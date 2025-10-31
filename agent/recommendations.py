from .core import State,llm_client,MODEL_NAME
from .utils import parse_model_res


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

    w_cost = state["recommendation_weights"]["cost"]
    w_coverage = state["recommendation_weights"]["coverage"]
    w_fairness = state["recommendation_weights"]["fairness"]
    w_urgency = state["recommendation_weights"]["urgency"]

    forecast_summary = state["forecast_conclusions"]
    recommendation = state["recommendation"]
    feedback = state["user_feedback"]
    llm_prompt = f"""
You are a healthcare resource allocation assistant tasked with optimizing resource distribution across hospitals.

Your job: decide how to reallocate resources between hospitals based on forecasted shortages or surpluses.

Current preference weights:
- Cost Efficiency: {w_cost}
- Coverage: {w_coverage}
- Fairness: {w_fairness}
- Urgency: {w_urgency}

Here are the forecasted resource utilizations:
{forecast_summary}
This is the previous given recommendation:
{recommendation}
And this is the user feedback for that recommendation:
{feedback}
---

**Your task:**
1. Identify hospitals facing *shortages* (high forecast values) and *surpluses* (low forecast values).
2. Suggest **specific transfers** between hospitals, in plain text. 
   Format each transfer like:
   - "Transfer 10 ventilators from CityCare Hospital to Metro Hospital"
3. Justify each recommendation using the 4 preference weights.

**Rules:**
1.Only give response in valid JSON format
2.Give only a single recommendation.
3.Do not include additional text, abbrevations or salutations.
4.Do not show weights in your justification
** JSON Format: **
{{
"recommendation":"",
"justification":"",
 "meta":{{
    "from":,
    "to":
    "resource_name":,
    "quantity":
    }}
}}
If there are no actionable imbalances, say so clearly.
Output should be a concise, readable report.
"""


    res = llm_client.models.generate_content(model=MODEL_NAME,contents=llm_prompt)
    res_dict = parse_model_res(res.text)
    print(res_dict)
    state["recommendation"] = res_dict["recommendation"]
    state["recommendation_meta"] = res_dict["meta"]
    return state


def get_feedback(state: State):
    """Adjusts weights based on feedback"""
    
    feedback = input("give your feedback ")

    if feedback=="quit":
        state["done"] = True
        return state
    
    """Adjust the recommendation weights based on user feedback"""

    llm_prompt = f"""
You are an expert feedback analyst. Based on the user feedback, assign required weight offset to following fields.
[[cost,coverage,fairness,urgency]].

**START OF FEEDBACK**
{feedback}
**END OF FEEDBACK**

**Rules**
1. The offset must be a float value between -0.5 and 0.5.
2. The absolute value of each offset should normally be at least 0.05 when a clear preference is detected.
3. Use 0 only if the feedback clearly implies no change.
4. Only respond in JSON format.
5. user_approval is either True or False based on whether user accepts or rejects recommendation.


** JSON format **
{{"weights":{{
    "cost":,
    "coverage":,
    "fairness":,
    "urgency":
    }},
    "user_approval":,
}}
"""
    res = llm_client.models.generate_content(model=MODEL_NAME,contents=llm_prompt)
    res_dict = parse_model_res(res.text)
    
    weights = state["recommendation_weights"]
    weights = apply_offsets(weights,res_dict["weights"])
    print(weights)
    state["recommendation_weights"] = weights
    state['user_feedback'] = feedback

    if res_dict["user_approval"]==True:
        resource = state["recommendation_meta"]["resource"]
        from_hos = state["recommendation_meta"]["from"]
        to_hos = state["recommendation_meta"]["to"]
        qty = state["recommendation_meta"]["quantity"]

        

    return state
    
