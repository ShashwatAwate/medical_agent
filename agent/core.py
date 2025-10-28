from typing_extensions import TypedDict
import pandas as pd
from typing import List,Dict

from datetime import datetime
import os

SAVE_PATH = "/sim_data"

try:
    sim_path = os.path.join(SAVE_PATH,"simulation.csv")
    report_path = os.path.join(SAVE_PATH,"reports.csv")

    sim_df = pd.read_csv(sim_path)
    report_df = pd.read_csv(report_path)

except Exception as e:
    print(f"ERROR: {str(e)}")
    exit()


class State(TypedDict):
    today_date: datetime
    window_data: pd.DataFrame
    today_data: dict
    report_data: str
    recommendation: str
    user_action: str
    recommendation_weights: Dict[str,float]