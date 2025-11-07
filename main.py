from langgraph.graph import StateGraph,START,END
import pandas as pd

from agent.core import State

from agent.data_ingestor import ingest_knowledge,ingest_daily_reports
from agent.forecasting import forecast_data,draw_conclusions
from agent.recommendations import build_recommendations,get_feedback
from agent.persistence import save_state,load_state
from agent.tracking import setup_tracking
from agent.data_insights import show_insights

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
    "num_hospitals":0,
    "resource_names":[],
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
        action = st.sidebar.selectbox("Choose Action",["Home","Tracking","Recommend","Insights"])

        if action == "Home":
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
                st.session_state["sim_mode_confirmed"] = sim_mode

            if st.session_state.get("sim_mode_confirmed") == "Start New Simulation":
                print("INFO: in start new simulation")
                num_hosp = st.number_input("Number of hospitals:", min_value=2, max_value=20, value=5)
                base_resources = ["oxygen", "ventilators", "medication_TB", "ppe_kits"]

                resources = st.multiselect(
                    "Select resources to include",
                    base_resources,
                    default=base_resources
                )

                custom_resources_inp = st.text_input(
                    "Add custom resource names (separate with commas)"
                )

                custom_resources = [r.strip() for r in custom_resources_inp.split(",") if r.strip()]

                final_resources = list(dict.fromkeys(resources + custom_resources))
                st.write("Final simulation resources:", final_resources)

                if st.button("Start Simulation"):
                    print("INFO: pressed start simulation")
                    state = initial_state
                    state["resource_names"] = final_resources
                    state["num_hospitals"] = num_hosp
                    state = ingest_knowledge(state)
                    st.session_state["state"] = state
                    st.success("New simulation started")

            elif st.session_state.get("sim_mode_confirmed") == "Continue Previous Simulation":
                state = load_state()
                if state is None:
                    st.error("Could not load saved state — the file is empty, corrupted, or incomplete.")
                    st.info("Please start a new simulation instead.")
                else:
                    st.session_state["state"] = state
                    st.info("Continuing previous simulation")

            
            if "state" in st.session_state:
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
        elif action == "Recommend":
            if "state" not in st.session_state:
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
                    resource = res_meta.get("resource", "")
                    rec_qty = res_meta.get("quantity")

                    today_df = state.get("tracking_data", None)
                    if today_df is None or resource is None:
                        st.warning("Tracking data or resource not available.")
                    else:
                        if isinstance(from_hosp, str):
                            from_hosp = [from_hosp]
                        if isinstance(to_hosp, str):
                            to_hosp = [to_hosp]

                        st.markdown("### Resource Transfer Details")
                        st.write(f"**Resource:** {resource}")

                        from_data, to_data = [], []
                        for fh in from_hosp:
                            row = today_df[today_df["hospital"] == fh]
                            if not row.empty:
                                from_data.append({
                                    "Hospital": fh,
                                    "Stock": int(row[f"{resource}_stock"].iloc[0]),
                                    "Usage": int(row[f"{resource}_usage"].iloc[0])
                                })

                        for th in to_hosp:
                            row = today_df[today_df["hospital"] == th]
                            if not row.empty:
                                to_data.append({
                                    "Hospital": th,
                                    "Stock": int(row[f"{resource}_stock"].iloc[0]),
                                    "Usage": int(row[f"{resource}_usage"].iloc[0])
                                })

                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("From Hospitals")
                            st.dataframe(pd.DataFrame(from_data), width="stretch")
                        with col2:
                            st.subheader("To Hospitals")
                            st.dataframe(pd.DataFrame(to_data), width="stretch")

                        st.write(f"**Quantity to transfer:** {rec_qty}")

                        # Maintain UI state properly across reruns
                        if "feedback_mode" not in st.session_state:
                            st.session_state["feedback_mode"] = None

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Accept"):
                                st.session_state["feedback_mode"] = "accept"
                        with col2:
                            if st.button("Reject"):
                                st.session_state["feedback_mode"] = "reject"

                        if st.session_state["feedback_mode"] == "accept":
                            st.subheader("Adjust Quantities")
                            transfer_quantities = {}
                            for fh in from_hosp:
                                for th in to_hosp:
                                    default = res_meta.get("quantity", 0)
                                    qty_str = st.text_input(f"{fh} → {th}", value=str(default), key=f"{fh}_{th}")
                                    try:
                                        hosp_df = today_df[today_df["hospital"]==fh]
                                        qty = int(qty_str)
                                        if qty<0 or qty>hosp_df[f"{resource}_stock"].iloc[0]:
                                            st.info("Invalid quantity entered! Defaulting to recommended value")
                                            qty = default
                                    except ValueError:
                                        print("ERROR: Encountered value error")
                                        qty = 0
                                    transfer_quantities[(fh, th)] = qty

                            if st.button("Submit Feedback"):
                                st.session_state["state"] = get_feedback(
                                    st.session_state["state"],
                                    approval=True,
                                    transfer_vals=transfer_quantities,
                                    reason=""
                                )
                                save_state(st.session_state["state"])
                                st.success("Feedback submitted successfully!")
                                st.session_state["feedback_mode"] = None

                        elif st.session_state["feedback_mode"] == "reject":
                            reason = st.text_area("Specify reason for rejection")
                            if st.button("Submit Rejection"):
                                st.session_state["state"] = get_feedback(
                                    st.session_state["state"],
                                    approval=False,
                                    transfer_vals={},
                                    reason=reason
                                )
                                save_state(st.session_state["state"])
                                st.info("Rejection submitted.")
                                st.session_state["feedback_mode"] = None
        elif action=="Insights":
            state = st.session_state.get("state")
            if state is None:
                st.info("Run a simulation first!")
            else:
                show_insights(state=state)
    except Exception as e:
        print(f"ERROR: in main function {str(e)}")
        print(f"{type(e).__name__}")

    # print(final_state)