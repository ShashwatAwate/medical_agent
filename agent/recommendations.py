from agent.core import State,llm_client,MODEL_NAME,PLAN_WEIGHT_MAP,NUM_PLANS,PLAN_CAPACITY
from agent.utils import parse_model_res,index,model
from agent.forecasting import prepare_candidates


from sklearn.metrics.pairwise import cosine_similarity

from collections import defaultdict
import pandas as pd
import numpy as np
import datetime
import random
import pprint

def plan_summary(plans:dict):
    """Summarize plans for the llm to recommend"""
    try:
        plan_summary = {}
        for plan_name in plans.keys():
            transfers = plans[plan_name]
            requesting_hospitals = set()
            responding_hospitals = set()
            dists = []
            resource_stats = defaultdict(lambda : {"total":0,"count":0})
            under_emergency = 0
            for transfer in transfers:
                dist = transfer.get('distance')
                req_hospital = transfer.get('req_hospital')
                res_hospital = transfer.get('res_hospital')
                resource = transfer.get('resource')
                amount = transfer.get('amount')
                emergency = transfer.get('emergency')

                requesting_hospitals.add(req_hospital)
                responding_hospitals.add(res_hospital)
                dists.append(dist)
                resource_stats[resource]["total"] += amount
                resource_stats[resource]["count"] += 1

                if emergency=='Yes':
                    under_emergency += 1

            avg_dist = np.mean(dists)
            avg_amt = {}
            for res,stats in resource_stats.items():
                avg = resource_stats[res]["total"]/resource_stats[res]["count"]
                avg_amt[res] = avg
            summary = {
                f"Requesting hospital ids : {list(requesting_hospitals)}",
                f"Responding hospital ids : {list(responding_hospitals)}",
                f"Resource distribution: {avg_amt}",
                f"Average Distance between hospitals: {avg_dist}",
                f"Hospitals under emergency: {under_emergency}"
            }
            plan_summary[plan_name] = summary

        return plan_summary
    except Exception as e:
        print(f"ERROR: during making summaries for plans : {str(e)}")

def rank_candidates(state: State):
    """From all transfers get top 3 potential transfers"""
    try:
        candidates = state['transfer_candidates']
        if len(candidates)==0:
            return {}
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
        nearby = nearby[:PLAN_CAPACITY]
        mid = mid[:PLAN_CAPACITY]
        far = far[:PLAN_CAPACITY]
        low_cap= low_cap[:PLAN_CAPACITY]
        high_cap = high_cap[:PLAN_CAPACITY]

        plans = {
            "nearest": nearby,
            "max_coverage":nearby+mid,
            "urgent": nearby+mid+far,
            "minimal_impact":low_cap,
            "high_impact":high_cap
        }
        state['plans'] = plans
        summary = plan_summary(plans)
        return summary
    
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
        
        if not plans:
            state['model_recommendations'] = {}
            return state

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
    2. RECOMMEND the plans MOST FITTING the priorites given. 
    3. JUSTIFY each recommendation based on the priorites.
    4. DO NOT DIVIDE TRANSFERS INSIDE THE PLANS, RECOMMEND ENTIRE PLANS

    **Rules:**
    1.ONLY give response in valid JSON format.
    2.DO NOT include additional text, abbreviations or salutations.
    3.DO NOT show weights in your justification.
    4.NEVER mention or invent hospitals that are not in the plan.
    5.Round quantities to INTEGERS.
    6.If there are no actionable imbalances between the tracked hospitals, clearly state that in the recommendation and justification fields.
    7.Base your response ONLY on user's priorities, DO NOT add your own thinking to rank a plan, ONLY rank BASED ON THE PRIORITIES.
    8.The JSON must exactly match this structure (no extra keys):

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
        # print(f"INFO:RAW RES DICT \n")
        # pprint.pprint(res_dict,indent=4)
        state['model_recommendations'] = res_dict
        return state
    
    except Exception as e:
        print(f"ERROR: during llm recommendation {str(e)}")
        print(f"type(e).__name__")
        return {}

def show_recommendations(state: State):
    """Show recommendations"""
    recommendations = state['model_recommendations']

    if not recommendations:
        print("Nothing to recommend")
        return
    
    sorted(recommendations,key=lambda x:x['rank'] )

    for rec in recommendations:

        rank = rec.get('rank')
        plan_name = rec.get('plan_name')
        justification = rec.get('justification')
        plans = state['plans']
        plan = plans.get(plan_name)

        print(rank)
        print(plan_name)
        print(justification)
        for transfer in plan:
            req_hosp = transfer.get('req_hospital')
            res_hosp = transfer.get('res_hospital')
            resource = transfer.get('resource')
            amount = transfer.get('amount')
            delay = transfer.get('delay')
            distance = transfer.get('distance')
            
            printStr = (
                f"Requesting Hospital: {req_hosp} "
                f"Responding Hospital: {res_hosp} "
                f"Resource: {resource} "
                f"Amount: {amount} "
                f"Estimated Delay: {delay}"
                f"Distance: {distance}"
            )
            print(printStr)

        print("\n")

def update_weights(state:State,reward:float):
    """Update preference weights"""
    lr = 0.05
    weights = state['recommendation_weights']

    for key,val in weights.items():
        weights[key] = weights[key] + lr*reward*PLAN_WEIGHT_MAP.get(key,0.0)
    
    state['recommendation_weights'] = weights



def get_feedback(state: State):
    """Get user feedback" and adjust weights"""
    recommendations = state["model_recommendations"]
    if not recommendations:
        print("Nothing to get feedback on")
        return []
    
    plans = state['plans']
    reward = 0
    
    for rec in recommendations:
        plan_name = rec.get('plan_name')
        rank = rec.get('rank')
        plan = plans.get(plan_name)

        accepted_transfers = [] #storing transfers to be applied to the Mesa Model

        print(f"Enter feedback for plan {plan_name}")
        isAccept = int(input('Accept(1)/Reject(0)\n'))
        if isAccept==1:
            reward = (NUM_PLANS-rank)/NUM_PLANS
            for transfer in plan:

                id = transfer.get('id')
                req_hosp = transfer.get('req_hospital')
                res_hosp = transfer.get('res_hospital')
                resource = transfer.get('resource')
                amount = transfer.get('amount')
                delay = transfer.get('delay')
                distance = transfer.get('distance')
                
                printStr = (
                    f"Requesting Hospital: {req_hosp} "
                    f"Responding Hospital: {res_hosp} "
                    f"Resource: {resource} "
                    f"Amount: {amount} "
                    f"Estimated Delay: {delay}"
                    f"Distance: {distance}"
                )

                print(printStr)

                choice = int(input("Accept(1)/Reject(0)\n"))
                if choice==1:
                    accepted_transfers.append(id)
                    pass
            break
        else:
            reward = -(NUM_PLANS - rank + 1)/NUM_PLANS
        
        update_weights(state,reward)
    return accepted_transfers
    
