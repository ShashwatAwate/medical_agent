from agent.core import State,sd


def setup_tracking(state: State, selected_hospitals: list = None):
    """Track specific hospitals, works for CLI or frontend-provided selection."""
    try:
        
        df = state["window_data"]
        all_hosp = list(df["hospital"].unique())
        current_selection = state["tracking_hosps"]


        if selected_hospitals is None:
            for idx, hosp in enumerate(all_hosp):
                marker = "(tracking)" if hosp in current_selection else ""
                print(f"{idx}. {hosp} {marker}")
            print("-1. select all")
            inputs = input("Select index of hospitals you want to track, remove hosps by adding their index ")
            inputs = [int(x) for x in inputs.split()]

            if inputs[0] == -1:
                selected_hospitals = all_hosp
            else:
                if len(inputs) >= len(all_hosp) - 1:
                    print("Leave at least 2 hospitals for tracking..., now tracking all hospitals")
                    selected_hospitals = all_hosp
                else:
                    for inp in inputs:
                        hosp = all_hosp[inp]
                        if hosp in current_selection:
                            current_selection.remove(hosp)
                        else:
                            current_selection.add(hosp)
                    selected_hospitals = list(current_selection)

        if len(selected_hospitals)<2:
            raise ValueError("Leave at least 2 hospitals for tracking")

        selected_df = df[df["hospital"].isin(selected_hospitals)]
        state["tracking_hosps"] = set(selected_hospitals)
        state["tracking_data"] = selected_df


        if selected_hospitals is None:
            print(state["tracking_hosps"])
            print("Hospitals present:", selected_df["hospital"].unique())
    except Exception as e:
        print(f"ERROR: during tracking {str(e)}")
        print(f"{type(e).__name__}")
    return state

if __name__ == "__main__":
    # setup_tracking()
    pass

    
