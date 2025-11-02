from langgraph.graph import StateGraph,START,END
import pandas as pd

from .core import State,sd

from .data_ingestor import ingest_knowledge,ingest_daily_reports
from .forecasting import forecast_data,draw_conclusions
from .recommendations import build_recommendations,get_feedback
from .persistence import save_state,load_state
from .tracking import setup_tracking

import datetime
import os

graph_builder = StateGraph(State)

#NODES

graph_builder.add_node(ingest_knowledge)
graph_builder.add_node(ingest_daily_reports)
graph_builder.add_node(forecast_data)
graph_builder.add_node(draw_conclusions)
graph_builder.add_node(build_recommendations)
graph_builder.add_node(get_feedback)
graph_builder.add_node(save_state)

#EDGES
graph_builder.add_edge(START,"ingest_knowledge")
graph_builder.add_edge("ingest_knowledge","ingest_daily_reports")
graph_builder.add_edge("ingest_daily_reports","forecast_data")
graph_builder.add_edge("forecast_data","draw_conclusions")
graph_builder.add_edge("draw_conclusions","build_recommendations")
graph_builder.add_edge("build_recommendations","get_feedback")
graph_builder.add_edge("get_feedback","save_state")
graph_builder.add_edge("save_state",END)

graph = graph_builder.compile()
initial_state: State = {
    "sim_date": datetime.datetime(2025,1,1),
    "days_since_update":0,
    "window_data": pd.DataFrame(),
    "today_data": pd.DataFrame(),
    "tracking_data":pd.DataFrame(),
    "report_data": {},
    "today_forecasts": {},
    "forecast_conclusions": [],
    "tracking_hosps": set(),
    "recommendation": "",
    "user_feedback":"",
    "recommendation_weights": {"cost":0.2,"coverage":0.2,"fairness":0.2,"urgency":0.2},
    "done":False
}

if __name__ == "__main__":

    if os.path.exists("./sim_outputs/state_snapshot.json"):
        state = load_state()
        print("Loaded saved simulation state.")
    else:
        state = initial_state
        print("Starting new simulation.")

    while True:
        choice = int(input("1. Recommend 2. Tracking"))
        if choice==1:
            state = graph.invoke(state)

            if state.get("done"):
                break
        elif choice==2:
            state = setup_tracking(state)
        pass
    # print(final_state)