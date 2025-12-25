from langgraph.graph import StateGraph,START,END
import pandas as pd

from agent.core import State

from agent.data_ingestor import ingest_knowledge,ingest_daily_reports
from agent.forecasting import forecast_data,draw_conclusions
from agent.recommendations import build_recommendations,get_feedback,llm_recommendation
from agent.persistence import save_state,load_state
from agent.tracking import setup_tracking
from agent.data_insights import show_insights
# from agent.candidates import get_transfers
from agent.model.models import HospitalModel


import datetime
import os

import streamlit as st

graph_builder = StateGraph(State)
model = HospitalModel()

def get_transfers(state: State):
    """Get the transfers from the model"""
    for i in range(100):
        model.step()
        if(len(model.pending_transfers) > 0):
            # print(f"INFO: tranfers \n\n {model.pending_transfers}")
            state['transfer_candidates'] = model.pending_transfers
            break
        else:
            continue
    return state

#NODES

graph_builder.add_node(get_transfers)
graph_builder.add_node(llm_recommendation)
#EDGES
graph_builder.add_edge(START,"get_transfers")
graph_builder.add_edge("get_transfers","llm_recommendation")
graph_builder.add_edge("llm_recommendation",END)

graph = graph_builder.compile()
initial_state: State = {
    "transfer_candidates": [],
    "recommendation": "",
    "recommendation_justification":"",
    "recommendation_weights": {"cost":0.5,"coverage":0.5,"fairness":0.5,"urgency":0.5},
    "done":False
}

if __name__ == "__main__":

    try:
        print("INFO: invoking graph")
        final_state = graph.invoke(initial_state)
    except Exception as e:
        print(f"ERROR: in main function {str(e)}")
        print(f"{type(e).__name__}")

    # print(final_state)