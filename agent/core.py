from typing_extensions import TypedDict

from typing import Dict

from google import genai
import os
from dotenv import load_dotenv
load_dotenv()

SAVE_PATH = "./sim_data"

MODEL_NAME = "gemini-2.5-flash-lite"
llm_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

NUM_PLANS = 5 # total number of different plans that can be there

PLAN_WEIGHT_MAP = {     # pre defined offsets for weights based on plan
    "urgent":{"urgency":1.0},
    "high_impact": {"cost":0.5,"coverage":0.2},
    "minimal_impact":{"fairness":0.5,"cost":0.3},
    "nearest":{"cost":1.0,"urgency":0.3},
    "max_coverage":{"coverage":1.0,"fairness":1.0}
}
PLAN_CAPACITY = 8 #maximum transfers that can be in one plan (for simplicity)

class State(TypedDict):
    transfer_candidates: list
    plans: dict
    model_recommendations:list
    recommendation_weights: Dict[str,float]