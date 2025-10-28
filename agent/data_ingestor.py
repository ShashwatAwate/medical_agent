import pandas as pd

from core import State,report_df,sim_df
import datetime

def ingest_data(state:State):
    today_df = sim_df[sim_df["date"]==state["today_date"]]

    if state["today_date"] in report_df:
        today_report = report_df.loc[[state["today_date"]]]
        report_text =  today_report["report"]
    else:
        report_text = ""

    #updating window
    if state["window_data"].empty:
        state["window_data"] = today_df
    else:
        state["window_data"] = pd.concat((state["window_data"],state["today_data"]))
        recent_dates = sorted(state["window_data"]["date"].unique())[-7:]
        state["window_data"] = state["window_data"][state["window_data"]["date"].isin(recent_dates)]
    #updating todays data
    state["today_data"] = today_df.iloc[0].to_dict()
    #updating todays reports if any
    state["report_data"] = report_text
    
    return state