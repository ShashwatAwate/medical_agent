from langgraph.graph import StateGraph,START,END
import pandas as pd

from .core import State,sd

from .data_ingestor import ingest_knowledge,ingest_daily_reports
from .forecasting import forecast_data,draw_conclusions
from .recommendations import build_recommendations,get_feedback



graph_builder = StateGraph(State)

#NODES

graph_builder.add_node(ingest_knowledge)
graph_builder.add_node(ingest_daily_reports)
graph_builder.add_node(forecast_data)
graph_builder.add_node(draw_conclusions)
graph_builder.add_node(build_recommendations)
graph_builder.add_node(get_feedback)

#EDGES
graph_builder.add_edge(START,"ingest_knowledge")
graph_builder.add_edge("ingest_knowledge","ingest_daily_reports")
graph_builder.add_edge("ingest_daily_reports","forecast_data")
graph_builder.add_edge("forecast_data","draw_conclusions")
graph_builder.add_edge("draw_conclusions","build_recommendations")
graph_builder.add_edge("build_recommendations","get_feedback")
graph_builder.add_edge("get_feedback","ingest_daily_reports")

graph = graph_builder.compile()
initial_state: State = {
    "today_date": None,
    "window_data": pd.DataFrame(),
    "today_data": pd.DataFrame(),
    "report_data": {},
    "today_forecasts": {},
    "forecast_conclusions": [],
    "recommendation": "",
    "user_feedback":"",
    "recommendation_weights": {"cost":0.2,"coverage":0.2,"fairness":0.2,"urgency":0.2},
    "done":False
}

if __name__=="__main__":
    state = initial_state
    while(True):
        state = graph.invoke(state)
        if state["done"] == True:
            break
    # print(final_state)