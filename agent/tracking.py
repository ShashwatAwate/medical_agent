from .core import State,sd


def setup_tracking(state: State):
    """Track specific hospitalss"""
    all_hosp = []
    selected_hosp = state["tracking_hosps"]
    df = state["window_data"]
    all_hosp = list(df["hospital"].unique())

    for idx,hosp in enumerate(all_hosp):
        already_tracking = False
        if hosp in selected_hosp:
            already_tracking = True
        if already_tracking:
            print(f"{idx}. {hosp} (tracking)")
        else:
            print(f"{idx}. {hosp}")
    
    print("-1. select all")
    
    inputs = input("Select index of hospitals you want to track, remove hosps by adding their index ")
    inputs = [int(x) for x in inputs.split()]

    if inputs[0]==-1:
        selected_hosp = set(all_hosp)
    else:
        if len(inputs)>=len(all_hosp)-1:
            print("Leave atleast 2 hospitals for tracking..., now tracking all hospitals")
            selected_hosp = set(all_hosp)
        else:
            for inp in inputs:
                hosp = all_hosp[inp]
                if hosp in selected_hosp:
                    selected_hosp.remove(hosp)
                else:
                    selected_hosp.add(hosp)

    if selected_hosp:
            selected_df = df[df["hospital"].isin(selected_hosp)]

    state["tracking_hosps"] = selected_hosp
    state["tracking_data"] = selected_df
    
    print(selected_hosp)
    print("Hospitals present:", selected_df["hospital"].unique())
    return state

if __name__ == "__main__":
    # setup_tracking()
    pass

    
