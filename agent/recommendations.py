from agent.core import State,llm_client,MODEL_NAME
from agent.utils import parse_model_res,index,model

from sklearn.metrics.pairwise import cosine_similarity

import pandas as pd
import datetime

def apply_offsets(weights,offsets,alpha=0.8):
    for key in weights.keys():
        wt = weights[key]
        offset = offsets[key]
        wt += alpha*offset
        wt = max(0,min(1,wt))
        weights[key] = wt
    
    return weights



def build_recommendations(state: State):
    """Based on the current data and forecasts and previous user interactions, build the recommendations"""
    try:
    
        w_cost = state["recommendation_weights"]["cost"]
        w_coverage = state["recommendation_weights"]["coverage"]
        w_fairness = state["recommendation_weights"]["fairness"]
        w_urgency = state["recommendation_weights"]["urgency"]

        forecast_summary = state["forecast_conclusions"]
        recommendation = state["recommendation"]
        feedback = state["user_feedback"]

        tracked_hospitals = list(state["tracking_hosps"])  

        llm_prompt = f"""
    You are a healthcare resource allocation assistant tasked with optimizing resource distribution across hospitals.

    Your job: decide how to reallocate resources between hospitals based on forecasted shortages or surpluses.

    Current preference weights (higher = more preferred):
    - Cost Efficiency: {w_cost}
    - Coverage: {w_coverage}
    - Fairness: {w_fairness}
    - Urgency: {w_urgency}

    Here are the forecasted resource utilizations:
    {forecast_summary}

    Hospitals currently being tracked:
    {tracked_hospitals}

    This is the previous given recommendation:
    {recommendation}

    And this is the user feedback for that recommendation:
    {feedback}

    DO NOT give the same recommendation again.

    ---

    **Your task:**
    1. Identify hospitals facing *shortages* (high forecast values) and *surpluses* (low forecast values) **only among the tracked hospitals**.
    2. Suggest **specific transfers** between tracked hospitals in plain text. 
    3. Justify each recommendation using the 4 preference weights.

    **Rules:**
    1.Only give response in valid JSON format.
    2.Give only a single recommendation.
    3.Do not include additional text, abbreviations or salutations.
    4.Do not show weights in your justification.
    5.**You must only reference hospitals from this list: {tracked_hospitals}.**
    6.**Never mention or invent hospitals that are not in the list.**
    7.NEVER recommend transfer to the same hospital.
    8.Round quantities to INTEGERS.
    9.If there are no actionable imbalances between the tracked hospitals, clearly state that in the recommendation and justification fields.
    10.**Do NOT provide multiple transfers or a list of transfers. Only ONE transfer should be included.**
    11.**The "meta" field MUST be a single object, NOT a list or array.**
    12.The JSON must exactly match this structure (no extra keys):

    **JSON Format:**
    {{
      "recommendation": "<short plain sentence describing ONE transfer>",
      "justification": "<reasoning in 2 to 3 sentences>",
      "meta": {{
          "from": "<hospital name>",
          "to": "<hospital name>",
          "resource": "<resource name>",
          "quantity": <integer>
      }}
    }}
    """



        res = llm_client.models.generate_content(model=MODEL_NAME,contents=llm_prompt)
        res_dict = parse_model_res(res.text)

        print(res.text)
        today_df = state["today_data"]
        res_meta = res_dict["meta"]
        resource = res_meta["resource"]
        from_hosp = res_meta["from"]
        to_hosp = res_meta["to"]

        from_stock_val = today_df[f"{resource}_stock"][today_df["hospital"] == from_hosp].values
        from_usage_val = today_df[f"{resource}_usage"][today_df["hospital"] == from_hosp].values

        to_stock_val = today_df[f"{resource}_stock"][today_df["hospital"] == to_hosp].values
        to_usage_val = today_df[f"{resource}_usage"][today_df["hospital"] == to_hosp].values

        print(f"from usage: {from_usage_val} | stock: {from_stock_val}")
        print(f"to usage: {to_usage_val} | stock: {to_stock_val}")

        state["recommendation"] = res_dict["recommendation"]
        state["recommendation_justification"] = res_dict["justification"]
        state["recommendation_meta"] = res_dict["meta"]
    except Exception as e:
        print(f"ERROR: during recommending things {str(e)}")
        print(f"{type(e).__name__}")
    return state


def get_feedback(state: State,feedback_str: str):
    """Adjusts weights based on feedback"""

    try:
        feedback = feedback_str

        feedback = feedback.lower()
        feedback_words = feedback.split()

        user_approval = False
        approval_words = ["yes","yes transfer","definitely transfer","ok"]
        print(f"Before update: {state["recommendation_weights"]}")
        for word in feedback_words:
            if word in approval_words:
                print("INFO: User approved the change")
                user_approval = True
                for weight in state["recommendation_weights"].keys():
                    state["recommendation_weights"][weight] += 0.02
                break

        concepts = {
        "cost": "concerns about expenses, distance, or transportation costs",
        "coverage": "ensuring enough resources are available across all hospitals or regions",
        "fairness": "equal distribution, fairness, or resource equity among hospitals",
        "urgency": "emergency, immediate need, or life-critical situations"
        }

        concept_embs = {k: model.encode(v,normalize_embeddings=True) for k,v in concepts.items()}
        feedback_emb = model.encode(feedback,normalize_embeddings=True).reshape(1,-1)
        justification_emb = model.encode(state["recommendation_justification"],normalize_embeddings=True).reshape(1,-1)


        delta_max = 0.05
        for concept,emb in concept_embs.items():
            feedback_sim = cosine_similarity(feedback_emb,emb.reshape(1,-1))[0][0]
            justification_sim = cosine_similarity(justification_emb, emb.reshape(1,-1))[0][0]
            print(f"INFO: feedback_sim: {feedback_sim}, justification_sim:{justification_sim}")
            sim = 0.4*feedback_sim + 0.6*justification_sim
            print(f"INFO: overall sim: {sim}")

            offset = 0
            offset = (max(sim,0.08) - 0.08)/(0.6)*delta_max
            print(f"INFO: offset: {offset}")
            if(user_approval):
                state["recommendation_weights"][concept] += float(offset)
            else:
                state["recommendation_weights"][concept] -= float(offset)

        print(f"After update: {state["recommendation_weights"]}")

        if user_approval==True:

            resource = state["recommendation_meta"]["resource"]
            from_hos = state["recommendation_meta"]["from"]
            to_hos = state["recommendation_meta"]["to"]
            qty = state["recommendation_meta"]["quantity"]

            today_df = state["today_data"]

            today_df.loc[today_df["hospital"]==from_hos,f"{resource}_stock"] -= qty
            today_df.loc[today_df["hospital"]==to_hos,f"{resource}_stock"] += qty

            state["tracking_data"] = pd.concat([state["tracking_data"],today_df])
            recent_dates = sorted(state["tracking_data"]["date"].unique())[-14:]
            state["tracking_data"] = state["tracking_data"][state["tracking_data"]["date"].isin(recent_dates)]

            state["today_data"] = today_df

        state["sim_date"] += datetime.timedelta(days=1)
        state["days_since_update"]+=1

        print(state["tracking_data"]["hospital"].unique())
    except Exception as e:
        print(f"ERROR: during feedback func {str(e)}")
        print(f"{type(e).__name__}")

    return state
    
