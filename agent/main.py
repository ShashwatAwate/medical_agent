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
    "distances":pd.DataFrame(),
    "shortages":list,
    "surpluses":list,
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
                if st.button("Get Recommendation"):
                    st.session_state["state"] = graph.invoke(st.session_state["state"])
                    save_state(st.session_state["state"])

                state = st.session_state["state"]
                st.subheader("Recommendation")
                st.write(state.get("recommendation", "No recommendation available."))

                st.subheader("Justification")
                st.write(state.get("recommendation_justification", "No justification available."))

                res_meta = state.get("recommendation_meta", {})
                if not res_meta:
                    st.write("Nothing to change!")
                else:
                    from_hosp = res_meta.get("from", [])
                    to_hosp = res_meta.get("to", [])
                    resource = res_meta.get("resource", "").lower()
                    rec_qty = res_meta.get("quantity")

                    today_df = state.get("tracking_data", None)
                    if today_df is None or resource is None:
                        st.warning("Tracking data or resource not available.")
                    else:
                        # Convert to list if single hospital
                        if isinstance(from_hosp, str):
                            from_hosp = [from_hosp]
                        if isinstance(to_hosp, str):
                            to_hosp = [to_hosp]

                        st.markdown("### Resource Transfer Details")
                        st.write(f"**Resource:** {resource}")

                        from_data = []
                        for fh in from_hosp:
                            from_row = today_df[today_df["hospital"] == fh]
                            if not from_row.empty:
                                from_data.append({
                                    "Hospital": fh,
                                    "Stock": int(from_row[f"{resource}_stock"].iloc[0]),
                                    "Usage": int(from_row[f"{resource}_usage"].iloc[0])
                                })

                        # Prepare "To Hospitals" data
                        to_data = []
                        for th in to_hosp:
                            to_row = today_df[today_df["hospital"] == th]
                            if not to_row.empty:
                                to_data.append({
                                    "Hospital": th,
                                    "Stock": int(to_row[f"{resource}_stock"].iloc[0]),
                                    "Usage": int(to_row[f"{resource}_usage"].iloc[0])
                                })
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("From Hospitals")
                    if from_data:
                        st.dataframe(pd.DataFrame(from_data), width="stretch")
                    else:
                        st.info("No data for from hospitals")

                with col2:
                    st.subheader("To Hospitals")
                    if to_data:
                        st.dataframe(pd.DataFrame(to_data), width="stretch")
                    else:
                        st.info("No data for to hospitals")

                st.write(f"**Quantity to transfer** {rec_qty}")
                col1,col2 = st.columns(2)
                with col1:
                    accept_click = st.button("Accept")
                with col2:
                    reject_click = st.button("Reject")
                transfer_quantities = {}
                reason = ""
                approval = False
                if accept_click:
                    approval = True
                    st.subheader("Adjust Quantities")
                    transfer_quantities = {}
                    for fh in from_hosp:
                        for th in to_hosp:
                            default = res_meta.get("quantity",0)
                            val_str = st.text_input("Enter quantity", value=str(default))
                            qty = int(val_str)
                            transfer_quantities[(fh,th)] = qty
                elif reject_click:
                    reason = st.text_area("Specify reason for rejection")
                
                if accept_click or reject_click:
                    if st.button("Submit Feedback"):
                        st.session_state["state"] = get_feedback(st.session_state["state"],approval=approval,transfer_vals=transfer_quantities,reason=reason)
                        save_state(st.session_state["state"])
                        st.write("Updated Recommendation Weights:", st.session_state["state"]["recommendation_weights"])

    except Exception as e:
        print(f"ERROR: in main function {str(e)}")
        print(f"{type(e).__name__}")

    # print(final_state)