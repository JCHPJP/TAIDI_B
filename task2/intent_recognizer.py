# intent_recognizer.py
# 意图识别器
from prompts.intent_prompts import INTENT_SYSTEM_PROMPT, get_intent_user_prompt
from llm_client import DeepSeekClient

class IntentRecognizer:
    """意图识别器类"""
    def __init__(self):
        self.intent_types = ["query", "analysis", "visualize", "conversation", "unknown"]
        self.client = DeepSeekClient()  # 使用DeepSeekClient进行对话交互
    def recognize(self, user_input):
        """
        识别用户意图
        Args:
            user_input: 用户输入文本
        Returns:
            dict: 包含intent、confidence、reason的字典
        """
        user_prompt = get_intent_user_prompt(user_input)
        messages = [
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        response = self.client.chat(
            messages=messages,
            temperature=0.3  # 低温度保证稳定性
        )
        
        if response:
            intent_result = self.client.extract_json(response)
            if intent_result and "intent" in intent_result:
                # 验证意图类型是否有效
                if intent_result["intent"] not in self.intent_types:
                    intent_result["intent"] = "unknown"
                    intent_result["confidence"] = 0.0
                return intent_result
        
        # 默认返回
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "reason": "意图识别失败"
        }
    
    def is_confident(self, intent_result):
        """
        判断识别结果是否可信
        
        Args:
            intent_result: 意图识别结果
        
        Returns:
            bool: 是否可信
        """
        return intent_result.get("confidence", 0) >= CONFIDENCE_THRESHOLD
    
    def get_intent_description(self, intent):
        """获取意图的中文描述"""
        descriptions = {
            "query": "数据查询",
            "analysis": "数据分析",
            "visualize": "数据可视化",
            "conversation": "日常对话",
            "unknown": "无法识别"
        }
        return descriptions.get(intent, "未知意图")


# 全局意图识别器实例
intent_recognizer = IntentRecognizer()

if __name__ == "__main__":
    print( intent_recognizer.recognize("金花股份近几年的利润总额变化趋势是什么样的") )
