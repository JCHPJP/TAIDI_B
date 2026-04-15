import json
import re
import sqlite3
import os
import logging
from openai import OpenAI

import time
from pathlib import Path

import json 
from functools import partial
from datetime import datetime
from config import Config

# ==================== 配置日志 ====================
# 创建日志目录
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)



# ==================== 配置 ====================
maximum = Config.maximum
DB_PATH = "financial_data.db"
PROMPT_FILE = "prompt-extract.md"
MAX_PROCESSES = 25  # 进程数
# ============================================
def get_client():
    """每个进程独立创建客户端"""
    return OpenAI(
        api_key=Config.DeepSeek.API_KEY,
        base_url=Config.DeepSeek.BASE_URL,  
        timeout=Config.DeepSeek.TIMEOUT
    )
client = get_client()

def extract_json(text):
    # 从大模型返回的文本中提取JSON（处理各种包装格式）
        if not text:
            return None
    
    # 1. 直接解析（最简单情况）
        try:
            return json.loads(text.strip())
        except:
            pass
        
        # 2. 提取 ```json ... ``` 代码块
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        match = re.search(json_pattern, text)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        
        # 3. 提取 ``` ... ``` 代码块（无json标记）
        code_pattern = r'```\s*([\s\S]*?)\s*```'
        match = re.search(code_pattern, text)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        
        # 4. 提取 { ... } 花括号内容（最外层）
        brace_pattern = r'\{[\s\S]*\}'
        match = re.search(brace_pattern, text)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        
        # 5. 提取 [ ... ] 方括号内容（数组）
        bracket_pattern = r'\[[\s\S]*\]'
        match = re.search(bracket_pattern, text)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        
        # 6. 尝试修复常见问题
        try:
            # 替换单引号为双引号
            fixed = text.replace("'", '"')
            # 替换Python的None为null
            fixed = fixed.replace('None', 'null')
            # 替换True/False为true/false
            fixed = fixed.replace('True', 'true').replace('False', 'false')
            return json.loads(fixed)
        except:
            pass
        return None
def call_llm(prompt, file_name=""):
    """调用大模型"""
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=Config.GLM_4_Flash.MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是一个专业的财务数据提取专家。请严格按照JSON格式返回结果，不要包含其他解释性文字。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            stream=False,
            max_tokens= 8192 
        )
        content = response.choices[0].message.content.strip()
        
        result = extract_json(content)
        return {"success": True, "data": result, "file": file_name}
        
    except json.JSONDecodeError as e:
        error_msg = f"JSON解析失败: {e}"
        return {"success": False, "error": error_msg, "file": file_name}
    except Exception as e:
        error_msg = str(e)
        return {"success": False, "error": error_msg, "file": file_name}

def GetDefaultTableData():
    with open(Path().cwd() / 'financial_schema.json', 'r', encoding='utf-8') as f:
        return f.read()

def get_prompt():
    with open(Path().cwd() / PROMPT_FILE, 'r', encoding='utf-8') as f:
        prompt = f.read()
    return prompt

def split_and_merge(paragraphs):
    """将段落重新拼接，每段不超过max_len"""
    result = []
    current = ""
    
    for p in paragraphs:
        # 如果当前段加上新段落会超长，就保存当前段，重新开始
        if len(current) + len(p)  <= int( maximum*0.6 ):
            current += p + "\n"
        else:
            if current:
                result.append(current)
            current = p + "\n"
    # 最后一段
    if current:
        result.append(current)
    return result

def main():
    file = 'F:\\dddd\\财务报告\\reports-上交所\\600080_20230428_MMWM.md'
    with open( file, 'r', encoding='utf-8') as f:
        financial_data = f.read()#全文
    paragraphs = financial_data.split('#')  # 按换行分割段落
    new_segments = split_and_merge(paragraphs)

    prompt = get_prompt()
    
    prompt = prompt.replace("{new_text}", new_segments[0])
    last_data = GetDefaultTableData()
    for segment in new_segments:
        prompt = get_prompt()
        prompt = prompt.replace("{last_data}", last_data)  
        prompt = prompt.replace("{new_text}", segment)
        print(len(prompt) )
        response = call_llm(prompt)
    
        print(response)
        response_map_data = response.get("data")
        
        last_data = json.dumps(response_map_data, ensure_ascii=False, indent=2)
        print(last_data)
if __name__ == "__main__":
    print( call_llm("请提取以下文本中的财务数据：\n\n" + "这是一个测试文本，包含一些财务信息。") )