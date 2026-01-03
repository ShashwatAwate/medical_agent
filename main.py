from langgraph.graph import StateGraph,START,END
import pandas as pd

from agent.core import State

from agent.data_ingestor import ingest_knowledge,ingest_daily_reports
from agent.forecasting import forecast_data,draw_conclusions
from agent.recommendations import llm_recommendation,get_feedback,show_recommendations
from agent.persistence import save_state,load_state
from agent.tracking import setup_tracking
from agent.data_insights import show_insights
# from agent.candidates import get_transfers
from agent.model.models import HospitalModel


import datetime
import os
import time

import streamlit as st

graph_builder = StateGraph(State)
model = HospitalModel()

def get_transfers(state: State):
    """Get the transfers from the model"""
    if(len(model.pending_transfers) > 0):
            state['transfer_candidates'] = model.pending_transfers.copy()

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
    "plans":{},
    "model_recommendation": [],
    "recommendation_weights": {"cost":0.5,"coverage":0.5,"fairness":0.5,"urgency":0.5},
}

if __name__ == "__main__":

    try:
        while(True):
            
            model.step()
            print("INFO: invoking graph")
            final_state = graph.invoke(initial_state)
            print("INFO: showing recommendations")
            show_recommendations(final_state)
            print("INFO: getting feedback")
            transfers = get_feedback(final_state)
            print("INFO: Applying transfers")
            model.apply_transfers(transfers)
            print("INFO: transfers applied")
            initial_state = final_state

            print("INFO: sleeping for 3 sec")
            time.sleep(3)
    except Exception as e:
        print(f"ERROR: in main function {str(e)}")
        print(f"{type(e).__name__}")

    # print(final_state)