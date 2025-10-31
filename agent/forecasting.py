from .core import State,sd


def forecast_data(state: State):
    """Forecast resource use and potential shortages using a rolling average"""

    window_df = state["window_data"]
    forecasts = {}
    severity_score = {"mild":1.05,"moderate":1.2,"severe":1.4,"critical":1.6}
    current_severity = state["report_data"]["severity"]
    for hospital in sd.hospitals:
        hospital_df = window_df[window_df["hospital"]==hospital].sort_values("date")
        hospital_forecasts = {}
        for resource in sd.resources:
            
            rolling_avg = hospital_df[f"{resource}_usage"].rolling(window=7).mean()
            res_forecast = rolling_avg.iloc[-1]*severity_score[current_severity]
            hospital_forecasts[f"{resource}_forecast"] = res_forecast
        forecasts[hospital] = hospital_forecasts

    state["today_forecasts"] = forecasts
    return state

def draw_conclusions(state: State):
    """Draw conclusions based on the forecasts"""
    
    conclusions = []
    for hosp,preds in state["today_forecasts"].items():
        for res in sd.resources:
            #get latest stock for that resource
            stock = state["window_data"].query("hospital==@hosp")[f"{res}_stock"].iloc[-1]
            forecast = preds[f"{res}_forecast"]
            diff = stock - forecast

            if diff<0:
                conclusion = f"{hosp} might face a SHORTAGE for {res} by {diff} units"
            elif diff>100:
                conclusion = f"{hosp} might have a SURPLUS for {res} by {diff} units"
            else:
                conclusion = f"{hosp} might be stable for {res}"
            conclusions.append(conclusion)
        
    state["forecast_conclusions"] = conclusions
    return state


if __name__ == "__main__":
    
    # forecasts = forecast_data(df)
    # print(draw_conclusions(df,forecasts))
    pass



