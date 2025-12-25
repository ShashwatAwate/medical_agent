from agent.core import State,llm_client,MODEL_NAME
from agent.utils import parse_model_res,index,model
from agent.forecasting import prepare_candidates


from sklearn.metrics.pairwise import cosine_similarity

import pandas as pd
import numpy as np
import datetime
import random
import pprint

def apply_offsets(weights,offsets,alpha=0.8):
    for key in weights.keys():
        wt = weights[key]
        offset = offsets[key]
        wt += alpha*offset
        wt = max(0,min(1,wt))
        weights[key] = wt
    
    return weights


def rank_candidates(state: State):
    """From all transfers get top 3 potential transfers"""
    try:
        candidates = state['transfer_candidates']
        # print(f"INFO: CANDIDATES \n\n {candidates}")
        print("INFO: Ranking Candidates")
        if candidates==[]:
            return []
        
        nearby = []
        mid = []
        far = []
        low_cap = []
        high_cap = []
        for candidate in candidates:
            dist = candidate.get('distance',999)
            capacity = candidate.get('amount',0)
            if dist <= 100:
                nearby.append(candidate)
            elif dist > 100 and dist <= 300:
                mid.append(candidate)
            else:
                far.append(candidate)

            if capacity < 10:
                low_cap.append(candidate)
            else:
                high_cap.append(candidate)
        # print(f"INFO: HIGH LEVEL GROUPS \n\n {nearby} \n\n {mid} \n\n {far} \n\n {low_cap} \n\n {high_cap}")
        plans = {
            "nearest": nearby,
            "max_coverage":nearby+mid,
            "urgent": nearby+mid+far,
            "minimal_impact":low_cap,
            "high_impact":high_cap
        }
        
        return {k:v for k,v in plans.items() if len(v)>0}
    
    except Exception as e:
        print(f"ERROR: during ranking candidates: {str(e)}")

def decide_preferences(state:State):
    """Just decide if a weight has high or low priority"""
    weights = state.get("recommendation_weights")
    if not isinstance(weights,dict):
        return {}
    prefs = {}
    for key,val in weights.items():
        if val>0.6:
            priority = "VERY HIGH"
        elif val<0.6 and val>=0.5:
            priority = "HIGH"
        elif val<0.5 and val>0.3:
            priority = "MEDIUM"
        else:
            priority = "LOW"
        prefs[key] = priority
    
    return priority
def llm_recommendation(state:State):
    print("INFO: LLM Recommendation started")
    try:
        plans = rank_candidates(state)
        priorities = decide_preferences(state)
        

        # print(f"INFO: PLANS \n\n {plans}")

        llm_prompt = f"""
    You are a healthcare resource allocation assistant tasked with optimizing resource distribution across hospitals.

    Your job: decide how to reallocate resources between hospitals based on the given set of plans and then rank them based on given priorities.

    ---PRIORITIES START---
    {priorities}
    ---PRIORITIES END---
   
    DO NOT give the same recommendation again.
    Do not invent or modify any resource names. The casing must match exactly.

    ---

    **Your task:**
    1. CAREFULLY go through the plans and their names.
    2. RECOMMEND the transfers MOST FITTING the priorites given. 
    3. JUSTIFY each recommendation based on the priorites.

    **Rules:**
    1.ONLY give response in valid JSON format.
    2.DO NOT include additional text, abbreviations or salutations.
    3.DO NOT show weights in your justification.
    4.NEVER mention or invent hospitals that are not in the plan.
    5.Round quantities to INTEGERS.
    6.If there are no actionable imbalances between the tracked hospitals, clearly state that in the recommendation and justification fields.
    7.The JSON must exactly match this structure (no extra keys):

    **JSON Format:**
    {{
      "rank": <rank_number(lowest is most important)>,
      "justification": "<reasoning in 2 to 3 sentences>",
      "plan_name": <key name of the plan>
    }}

    ---PLANS START---
    {plans}
    ---PLANS END---
    """
        
        res = llm_client.models.generate_content(model=MODEL_NAME,contents=llm_prompt)
        res_dict = parse_model_res(res.text)
        print(f"INFO:RAW RES DICT \n")
        pprint.pprint(res_dict,indent=4)

    except Exception as e:
        print(f"ERROR: during llm recommendation {str(e)}")
        print(f"type(e).__name__")
        return {}
    


def build_recommendations(state: State):
    """Based on the current data and forecasts and previous user interactions, build the recommendations"""
    try:
        print("INFO: Building recommendations")
        res_dict = llm_recommendation(state)
        # print("INFO:", type(res_dict), res_dict)

        today_df = state["today_data"]
        res_meta = res_dict.get("meta", None)

        if not res_meta:
            print("WARN: No meta found in recommendations")
            state["recommendation"] = res_dict.get("recommendation", None)
            state["recommendation_justification"] = res_dict.get("justification", None)
            
            return state

        # Ensure these are lists (even if only one hospital)
        from_hosp = res_meta.get("from", [])
        to_hosp = res_meta.get("to", [])
        resource = res_meta.get("resource", "")

        if isinstance(from_hosp, str):
            from_hosp = [from_hosp]
        if isinstance(to_hosp, str):
            to_hosp = [to_hosp]

        # Filter using isin()
        from_df = today_df[today_df["hospital"].isin(from_hosp)]
        to_df = today_df[today_df["hospital"].isin(to_hosp)]

        from_stock_val = from_df[f"{resource}_stock"].values
        from_usage_val = from_df[f"{resource}_usage"].values

        to_stock_val = to_df[f"{resource}_stock"].values
        to_usage_val = to_df[f"{resource}_usage"].values

        print(f"FROM hospitals: {from_hosp}")
        print(f"TO hospitals: {to_hosp}")
        print(f"from usage: {from_usage_val} | stock: {from_stock_val}")
        print(f"to usage: {to_usage_val} | stock: {to_stock_val}")

        state["recommendation"] = res_dict.get("recommendation", "")
        state["recommendation_justification"] = res_dict.get("justification", "")
        state["recommendation_meta"] = res_meta

    except Exception as e:
        print(f"ERROR: during recommending things {str(e)}")
        print(f"{type(e).__name__}")

    return state


def get_feedback(state: State,approval:bool,transfer_vals:dict = {},reason:str = ""):
    """Adjusts weights based on feedback"""

    try:

        print(f"Before update: {state["recommendation_weights"]}")
        if approval:
            for weight in state["recommendation_weights"].keys():
                state["recommendation_weights"][weight] += 0.02
            meta = state.get("recommendation_meta")
            if isinstance(meta,dict) and meta.get("resource"):
                resource = meta.get("resource","")
                from_hos = meta.get("from", [])
                to_hos = meta.get("to", [])
                for fh in from_hos:
                    qty = transfer_vals.get((fh,to_hos),meta.get("quantity",0))
                    print(f"INFO: for {resource} qty is {qty}")
                    today_df = state["today_data"]

                    today_df.loc[today_df["hospital"]== fh,f"{resource}_stock"] -= qty
                    today_df.loc[today_df["hospital"]==to_hos,f"{resource}_stock"] += qty

                state["tracking_data"] = pd.concat([state["tracking_data"],today_df])
                recent_dates = sorted(state["tracking_data"]["date"].unique())[-14:]
                state["tracking_data"] = state["tracking_data"][state["tracking_data"]["date"].isin(recent_dates)]

                state["today_data"] = today_df
        else:
            concepts = {
            "cost": "concerns about expenses, distance, or transportation costs",
            "coverage": "ensuring enough resources are available across all hospitals or regions",
            "fairness": "equal distribution, fairness, or resource equity among hospitals",
            "urgency": "emergency, immediate need, or life-critical situations"
            }

            concept_embs = {k: model.encode(v,normalize_embeddings=True) for k,v in concepts.items()}
            feedback_emb = model.encode(reason,normalize_embeddings=True).reshape(1,-1)
            justification_emb = model.encode(state["recommendation_justification"],normalize_embeddings=True).reshape(1,-1)


            delta_max = 0.1
            for concept,emb in concept_embs.items():
                feedback_sim = cosine_similarity(feedback_emb,emb.reshape(1,-1))[0][0]
                justification_sim = cosine_similarity(justification_emb, emb.reshape(1,-1))[0][0]
                print(f"INFO: feedback_sim: {feedback_sim}, justification_sim:{justification_sim}")
                sim = 0.4*feedback_sim + 0.6*justification_sim
                print(f"INFO: overall sim: {sim}")

                offset = 0
                offset = (max(sim,0.08) - 0.08)/(0.6)*delta_max
                print(f"INFO: offset: {offset}")
                state["recommendation_weights"][concept] -= float(offset)


        print(f"After update: {state["recommendation_weights"]}")
        print(f"INFO: days since last update(feedback): {state["days_since_update"]}")
        state["sim_date"] += datetime.timedelta(days=1)
        state["days_since_update"]+=1
        print(state["tracking_data"]["hospital"].unique())

    except Exception as e:
        print(f"ERROR: during feedback func {str(e)}")
        print(f"{type(e).__name__}")

    return state
    
