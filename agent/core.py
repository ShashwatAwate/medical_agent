from typing_extensions import TypedDict
import pandas as pd
from typing import List,Dict


from datetime import datetime
from .model.models import HospitalModel

from google import genai
import os
from dotenv import load_dotenv
load_dotenv()

SAVE_PATH = "./sim_data"

MODEL_NAME = "gemini-2.5-flash-lite"
llm_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class State(TypedDict):
    transfer_candidates: List
    recommendation: str
    recommendation_justification: str
    prev_recommendations: dict
    user_feedback:str
    recommendation_weights: Dict[str,float]
    recommendation_meta: dict
    done: bool