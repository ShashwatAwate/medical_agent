import pandas as pd


from .core import State,llm_client,sd,MODEL_NAME
from .utils import parse_model_res
from google.genai import types
import datetime


def ingest_knowledge(state:State):
    """Ingests structured data which has been assumed to arrive every 2 weeks"""

    if state["days_since_update"]>=3 or state["window_data"].empty:

        print("INFO: Recieved new data!")
        
        sim_df = sd.generate_data()
        today_df = sim_df
    
        #updating window
        if state["window_data"].empty:
            state["window_data"] = today_df
        else:
            # window_data: will have data from last 14 entries

            state["window_data"] = pd.concat((state["window_data"],state["today_data"]))
            recent_dates = sorted(state["window_data"]["date"].unique())[-14:]
            state["window_data"] = state["window_data"][state["window_data"]["date"].isin(recent_dates)]

        #updating todays data
        state["today_date"] = state["sim_date"]
        state["today_data"] = sim_df[sim_df["date"]==state["today_date"]]
        state["days_since_update"] = 0

    
    return state
    


def ingest_daily_reports(state: State):
    """Ingest and parse daily unstructured reports"""
    daily_report = sd.generate_reports()

    llm_prompt = f"""
You are an assistant that extracts structured information from healthcare text reports.
Your job is to analyze each report and produce a JSON object summarizing the event, even if details are partially missing.

INPUT TEXT: {daily_report}

For input text, output only a valid JSON object with these fields:

hospital: the hospital mentioned, or null if unknown
region: the geographic region or city, or null if not stated
resource: what is affected (oxygen, ventilators, beds, staff, etc.)
event: one of [shortage, restock, maintenance, surge, stable, unknown]
change_estimate_pct: estimated percentage increase or decrease in resource use (integer, may be approximate)
reason: the event or cause described (e.g., “flood”, “heat wave”, “festival crowd”)
severity: serverity of the reason. choose one of [mild,moderate,severe,critical] mild is lowest severity, critical is highest severity.
confidence: a number from 0 to 1 showing how certain you are about your extraction, based on text clarity and specificity.

1.0 = completely certain
0.5 = partially inferred
0.2 = mostly guessing
**JSON format**
{{
"hospital":,
"region":,
"resource":,
"event":,
"change_estimate_pct",
"reason":,
"severity":,
"confidence":,
}}

If you cannot identify something, return null or unknown, but always include all fields.
Output JSON only, with no extra text.
"""
    res = llm_client.models.generate_content(model = MODEL_NAME,contents=llm_prompt,config=types.GenerateContentConfig(max_output_tokens=2000))
    res_dict = parse_model_res(res.text)

    if(res_dict["hospital"]==None or res_dict["region"]==None):
        res_dict["confidence"] -= 0.1
    if((res_dict.get("severity","")).lower() in ['mild','moderate']):
        res_dict["confidence"] -= 0.2

    state["report_data"] = res_dict
    state["today_date"] = state["sim_date"]
    return state


if __name__ == "__main__":
    ingest_daily_reports()