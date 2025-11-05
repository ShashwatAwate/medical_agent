from typing_extensions import TypedDict
import pandas as pd
from typing import List,Dict

from .data.generate_data import SyntheticData

from datetime import datetime


from google import genai
import os
from dotenv import load_dotenv
load_dotenv()

SAVE_PATH = "./sim_data"

MODEL_NAME = "gemini-2.5-flash-lite"
llm_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

sd = SyntheticData(save_path=SAVE_PATH)

try:
    sim_path = os.path.join(SAVE_PATH,"simulation.csv")
    

    sim_df = pd.read_csv(sim_path)
except Exception as e:
    print(f"ERROR: {str(e)}")
    exit()


class State(TypedDict):
    sim_date:datetime
    days_since_update: int
    window_data: pd.DataFrame
    today_data: pd.DataFrame
    tracking_data: pd.DataFrame
    distances: pd.DataFrame
    shortages: list
    surpluses: list
    tracking_hosps: set
    report_data: dict
    today_forecasts : dict
    forecast_conclusions: list
    recommendation: str
    recommendation_justification: str
    prev_recommendations: dict
    user_feedback:str
    recommendation_weights: Dict[str,float]
    recommendation_meta: dict
    done: bool