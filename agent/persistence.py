import os,json

import pandas as pd

from agent.core import State
import datetime


def save_state(state: State):   
    """Save current state to disk so that we dont get recursion errors"""
    path = "./sim_outputs/state.json"
    try:
        os.makedirs(os.path.dirname(path),exist_ok=True)

        with open(path,'w') as f:
            json.dump({
                "sim_date": str(state["sim_date"]),
                "recommendation":state["recommendation"],
                "days_since_update": state["days_since_update"],
                "recommendation_weights": state["recommendation_weights"],
                "tracking_hosps": list(state["tracking_hosps"]),
                "resource_names": list(state["resource_names"]),
                "num_hospitals": state["num_hospitals"]
            },f,indent=4)
        state["window_data"].to_csv("./sim_outputs/window_data.csv", index=False)
        state["today_data"].to_csv("./sim_outputs/today_data.csv", index=False)
        state["tracking_data"].to_csv("./sim_outputs/tracking_data.csv",index=False)
        state["distances"].to_csv("./sim_outputs/distances.csv",index=False)
    except Exception as e:
        print(f"ERROR: during writing state to disk {str(e)}")
        state = None
    return state

def load_state():
    path = "./sim_outputs/state.json"
    try:
        with open(path,'r') as f:
            saved = json.load(f)
        state = {
        "sim_date": datetime.datetime.fromisoformat(saved["sim_date"]),
        "days_since_update": saved["days_since_update"],
        "recommendation_weights": saved["recommendation_weights"],
        "tracking_hosps": set(saved["tracking_hosps"]),
        "window_data": pd.read_csv("./sim_outputs/window_data.csv",parse_dates=["date"]),
        "today_data": pd.read_csv("./sim_outputs/today_data.csv",parse_dates=["date"]),
        "tracking_data":pd.read_csv("./sim_outputs/tracking_data.csv",parse_dates=["date"]),
        "distances":pd.read_csv("./sim_outputs/distances.csv"),
        "num_hospitals":saved["num_hospitals"],
        "resource_names":saved["resource_names"],
        "recommendation": saved["recommendation"],
        "done": False,
    }
    except Exception as e:
        print(f"ERROR: during loading state from disc {str(e)}")
        state = None
    
    return state