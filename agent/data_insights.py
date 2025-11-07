import streamlit as st

import pandas as pd
from agent.core import State



def show_insights(state: State):
    st.title("Data Insights")
    try:
        df = state.get("window_data").copy()
        df["date"] = pd.to_datetime(df["date"],errors="coerce").dt.date
        st.subheader("Overview")
        st.write(df.describe())

        
        hospitals = sorted(df["hospital"].unique())
        selected_hosp = st.sidebar.selectbox("Select Hospital",hospitals)

        resource_cols = [c for c in df.columns if c.endswith("_stock")]
        if not resource_cols:
            st.warning("No resource columns found in data")
            return
        
        selected_resource = st.sidebar.selectbox("Select Resource", resource_cols)

        
        hosp_df = df[df["hospital"] == selected_hosp]
    
        st.subheader(f"{selected_hosp} — {selected_resource} Trend")
    
        
        chart_data = hosp_df[["date", selected_resource]].set_index("date")
        st.line_chart(chart_data)
    
        
        avg_value = chart_data[selected_resource].mean()
        min_value = chart_data[selected_resource].min()
        max_value = chart_data[selected_resource].max()
    
        st.markdown(f"""
        **Summary for {selected_resource}:**
        - Average: {avg_value:.2f}  
        - Minimum: {min_value:.2f}  
        - Maximum: {max_value:.2f}
        """)
    
        
        st.subheader(f"{selected_hosp} — All Resources Comparison")
        st.line_chart(hosp_df.set_index("date")[resource_cols])
    
    except Exception as e:
        print(f"ERROR: during insight showing {str(e)}")
        print(type(e).__name__)