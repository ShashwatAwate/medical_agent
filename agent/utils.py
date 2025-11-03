from agent.core import State

import json
import re

from faiss import IndexFlatL2
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
dims = 384
index = IndexFlatL2(dims)

def parse_model_res(res_content: str):
    try:
        pattern = r"```json(.*?)```"
        matches = re.findall(pattern, res_content, re.DOTALL)
        if matches:
            json_str = matches[0].strip()
        else:
            # fallback: assume whole response is JSON
            json_str = res_content.strip()

        json_content = json.loads(json_str)
        
        return json_content
    
    except Exception as e:
        print(f"json parse error: {str(e)}")
        raise

def append_to_index(state: State,text):
    """Add recommendations to faiss index"""

    print("INFO: encoding recommendation")
    try:
        emb = model.encode([text])
        distance,_ = index.search(emb,1)
        if(distance[0,0] < 0.8):
            index.add(emb)
            state["prev_recommendations"][emb] = text
    except Exception as e:
        print(f"ERROR: during appending to faiss index {str(e)}")
        print(f"{type(e).__name__}")
    return state 


    