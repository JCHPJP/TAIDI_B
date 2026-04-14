import pandas as pd

from prompts.map_table_prompts import get_table_user_prompt
from pathlib import Path
from llm_client import DeepSeekClient

def build_company_extract_prompt(user_input: str) -> str:
    prompt = get_table_user_prompt()
    path = Path(__file__).parent.parent / "infors" / "company_stockcode.json"
    with open(path, "r", encoding="utf-8") as f:
        company_list = f.read()
    prompt = prompt.replace("{{company_list}}", company_list)
    prompt = prompt.replace("{user_input}", user_input)
    client = DeepSeekClient()
    content = client.chat(
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0.3
    )
    content_json = client.extract_json(content)
    names = []
    if content_json['has_company']:
        for data in content_json['extracted_companies']:
            names.append(data['matched_standard_name'])
    information = Path(__file__).parent.parent / 'data' / '正式数据'/'附件1：中药上市公司基本信息（截至到2025年12月22日）.xlsx'
    df = pd.read_excel(information)
    df = df[df['A股简称'].isin(names)]
    if df.empty:
    # 空的时候给一个提示字符串，不让模型懵
        company_list_str = "无匹配的上市公司"
    else:
    # 有数据时转成清晰字符串
        company_list_str = df.to_string(index=False)
    return user_input  + "\n输入相关的公司信息\n" + company_list_str
if __name__ == "__main__":
    print( build_company_extract_prompt("查一下阿胶和片仔癀的注册资本") )
