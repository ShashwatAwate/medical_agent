from agent.core import State,sd
import pandas as pd

def forecast_data(state: State):
    """Forecast resource use and potential shortages using a rolling average"""
    try:
        print("INFO: Forecasting Data")
        window_df = state.get("tracking_data")
        if not isinstance(window_df,pd.DataFrame):
            raise Exception("Not found tracking data")
        forecasts = {}
        severity_score = {"mild":1.05,"moderate":1.2,"severe":1.4,"critical":1.6}
        report_data = state.get("report_data")
        if not isinstance(report_data,dict):
            raise Exception("Not found report data")
        
        current_severity = report_data.get("severity")
        for hospital in state["tracking_hosps"]:
            hospital_df = window_df[window_df["hospital"]==hospital].sort_values("date")
            hospital_forecasts = {}
            for resource in sd.resources:

                trend = hospital_df[f"{resource}_usage"].diff().rolling(window=7).mean().iloc[-1]
                base = hospital_df[f"{resource}_usage"].iloc[-1]
                res_forecast = base + trend * severity_score[current_severity]
                hospital_forecasts[f"{resource}_forecast"] = res_forecast
            forecasts[hospital] = hospital_forecasts

        # print(forecasts)
        state["today_forecasts"] = forecasts
    except Exception as e:
        print(f"ERROR: during forecasting data {str(e)}")
        print(f"{type(e).__name__}")
    return state

def draw_conclusions(state: State):
    """Draw conclusions based on the forecasts"""
    try:
        print("INFO: Drawing Conclusions")
        conclusions = []
        surpluses =  []
        shortages = []

        for hosp,preds in state["today_forecasts"].items():
            for res in sd.resources:
                #get latest stock for that resource
                stock = state["tracking_data"].query("hospital==@hosp")[f"{res}_stock"].iloc[-1]
                forecast = preds[f"{res}_forecast"]
                diff = stock - forecast

                if diff<0:
                    conclusion = f"{hosp} might face a SHORTAGE for {res} by {diff} units"
                    shortages.append({"hospital":hosp,"resource":res,"quantity":abs(diff)})
                elif diff>100:
                    conclusion = f"{hosp} might have a SURPLUS for {res} by {diff} units"
                    surpluses.append({"hospital":hosp,"resource":res,"quantity":diff})
                else:
                    conclusion = f"{hosp} might be stable for {res}"
                conclusions.append(conclusion)

        # print(conclusions)
        state["shortages"] = shortages
        state["surpluses"] = surpluses
        state["forecast_conclusions"] = conclusions
        # print(conclusions)
        # print(shortages)
        # print(surpluses)
    except Exception as e:
        print(f"ERROR: during drawing conclusions from forecasts {str(e)}")
        print(f"{type(e).__name__}")
    return state

def prepare_candidates(state: State):
    """Prepare potential candidates for recommendations"""
    print("INFO: Preparing Candidates")
    try:
        candidates = []
        distance_df = state["distances"]
        # print(distance_df.head())
        for short_entry in state["shortages"]:
            providers = []
            short_hosp = short_entry["hospital"]
            short_resource = short_entry["resource"]
            short_diff = short_entry["quantity"]

            surplus_candidates = [entry for entry in state["surpluses"] if entry["resource"]==short_resource]
            surplus_candidates = sorted(surplus_candidates, key=lambda x: distance_df.loc[short_hosp, x["hospital"]])
            remaining_need = short_diff
            for candidate in surplus_candidates:
                disposable_surplus = 0.6*candidate["quantity"]
                providers.append({"hospital":candidate["hospital"],"quantity":disposable_surplus})
                if remaining_need - disposable_surplus <=0:
                    break
                remaining_need -= disposable_surplus
            candidates.append({"short_hospital":short_hosp,"resource":short_resource,"shortage":short_diff,"providers":providers})
        return candidates
    except Exception as e:
        print(f"ERROR: during preparing candidates {str(e)}")
        print(f"{type(e).__name__}")
    

if __name__ == "__main__":
    
    # forecasts = forecast_data(df)
    # print(draw_conclusions(df,forecasts))
    pass



