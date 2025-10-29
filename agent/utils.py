import json
import re

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