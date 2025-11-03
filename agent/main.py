from langgraph.graph import StateGraph,START,END
import pandas as pd

from agent.core import State,sd

from agent.data_ingestor import ingest_knowledge,ingest_daily_reports
from agent.forecasting import forecast_data,draw_conclusions
from agent.recommendations import build_recommendations,get_feedback
from agent.persistence import save_state,load_state
from agent.tracking import setup_tracking

import datetime
import os

import streamlit as st

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
graph_builder.add_edge("build_recommendations","save_state")
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
    "recommendation_justification":"",
    "recommendation_meta":{},
    "user_feedback":"",
    "recommendation_weights": {"cost":0.5,"coverage":0.5,"fairness":0.5,"urgency":0.5},
    "done":False
}

if __name__ == "__main__":

    try:
        action = st.sidebar.selectbox("Choose Action",["Home","Tracking","Recommend"])

        if action=="Home":
            st.header("Welcome to the hospital agent dashboard")

            st.write("Simulation")
            if os.path.exists("./sim_outputs/state.json"):
                sim_mode = st.radio(
                    "Select simulation mode:",
                    ["Start New Simulation", "Continue Previous Simulation"],
                    horizontal=True
                )
            else:
                sim_mode = "Start New Simulation"
            if st.button("Confirm Choice"):
                if sim_mode == "Start New Simulation":
                    state = initial_state
                    st.session_state["state"] = state
                    st.success("New simulation started")
                else:
                    state = load_state()
                    st.session_state["state"] = state
                    st.info("Continuing previous simulation")

                st.subheader(f"Current simulation date: {st.session_state['state']['sim_date'].strftime('%Y-%m-%d')}")

        elif action=="Tracking":
            if("state" not in st.session_state):
                st.error("Initialize a simulation first!")
            if(st.session_state["state"]["window_data"].empty or st.session_state["state"]["tracking_data"].empty):
                st.error("Cannot Update Tracking! Run a recommendation first")
            else:
                all_hospitals = list(st.session_state["state"]["window_data"]["hospital"].unique())
                selected_hospitals = st.multiselect(
                    "Select hosps to track",
                    options = all_hospitals,
                    default= list(st.session_state["state"]["tracking_hosps"])
                )
                if st.button("Update Tracking"):
                    st.session_state["state"] = setup_tracking(st.session_state["state"],selected_hospitals)
                    st.success("Tracking Updated")
        elif action=="Recommend":
            if("state" not in st.session_state):
                st.error("Initialize a simulation first!")
            else:
                st.session_state["state"] = graph.invoke(st.session_state["state"])
                st.subheader("Recommendation")
                st.write(st.session_state["state"]["recommendation"])
                st.subheader("Justification")

                st.write(st.session_state["state"]["recommendation_justification"])
                from_hosp = st.session_state["state"]["recommendation_meta"]["from"]
                to_hosp = st.session_state["state"]["recommendation_meta"]["to"]
                resource = st.session_state["state"]["recommendation_meta"]["resource"]

                today_df = st.session_state["state"]["tracking_data"]
                from_stock_val = int(today_df[f"{resource}_stock"][today_df["hospital"] == from_hosp].iloc[0])
                from_usage_val = int(today_df[f"{resource}_usage"][today_df["hospital"] == from_hosp].iloc[0])

                to_stock_val = int(today_df[f"{resource}_stock"][today_df["hospital"] == to_hosp].iloc[0])
                to_usage_val = int(today_df[f"{resource}_usage"][today_df["hospital"] == to_hosp].iloc[0])

                st.metric("From Stock",from_stock_val)
                st.metric("To stock",to_stock_val)

                feedback = st.text_area("Give feedback")
                if st.button("Submit Feedback"):
                    st.session_state["state"] = get_feedback(st.session_state["state"],feedback)
                    save_state(st.session_state["state"])
                    st.write("Updated Recommendation Weights:", st.session_state["state"]["recommendation_weights"])
    except Exception as e:
        print(f"ERROR: in main function {str(e)}")
        print(f"{type(e).__name__}")

    # print(final_state)