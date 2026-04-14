# prompts/conversation_prompts.py
# 多轮对话相关Prompt

CONVERSATION_SYSTEM_PROMPT = """你是一个友好的数据分析助手。你可以帮助用户查询数据、分析趋势、生成图表。

你的特点：
1. 理解用户的多轮对话上下文
2. 能够回答关于数据的问题
3. 可以记住之前的对话内容
4. 用友好、专业的语气回复
5. 如果不清楚用户意图，可以引导用户提供更多信息

当用户询问数据相关问题时，你会调用相应的工具来查询和分析数据。
对于闲聊或问候，直接友好回复。"""


def get_conversation_user_prompt(user_input, history):
    """获取多轮对话的用户提示"""
    history_text = ""
    if history:
        history_text = "对话历史：\n"
        for item in history[-5:]:  # 只取最近5轮
            history_text += f"用户：{item.get('user', '')}\n助手：{item.get('assistant', '')}\n"
        history_text += "\n"
    
    return f"""{history_text}当前用户输入：{user_input}

请根据对话历史和当前输入，给出合适的回复。"""