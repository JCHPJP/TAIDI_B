# llm_client.py - 保持原样，OpenAI客户端本身就是线程安全的
from openai import OpenAI
from config import Config
import json
import re
class DeepSeekClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=Config.DeepSeek.API_KEY,
            base_url=Config.DeepSeek.API_URL
        )
        self.model = Config.DeepSeek.MODEL_NAME
    
    def chat(self, messages, temperature=0.7):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content
    
    def extract_json(self, text):
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

# 全局单例，多线程直接共享使用
deepseek_client = DeepSeekClient()