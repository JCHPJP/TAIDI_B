from build_company_extract_prompt import build_company_extract_prompt
from prompts.clarification_prompts import get_intent_clarification_prompt

from llm_client import DeepSeekClient

if __name__ == "__main__":
    prompt = get_intent_clarification_prompt()
    client = DeepSeekClient()
    inputtext = '分析中药行业的盈利能力'
    messages = [
        {"role": "system", "content": prompt.replace("{user_input}", inputtext)},  
        {"role": "user", "content": inputtext}   
    ]
    json_response = client.extract_json( client.chat(messages= messages) )
    print(json_response)
