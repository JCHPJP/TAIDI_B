# prompts/analysis_prompts.py
# 分析结论生成Prompt

ANALYSIS_SYSTEM_PROMPT = """你是一个专业的数据分析助手。根据查询结果数据，给出专业的分析结论。

分析要求：
1. 总结数据的主要特征和趋势
2. 指出异常值或突出表现
3. 提供有价值的洞察和建议
4. 语言简洁专业，使用中文
5. 如果数据量较大，重点关注Top和Bottom表现
6. 包含具体的数据支撑

分析输出格式：
- 核心发现：简要总结最重要的发现
- 详细分析：分点说明具体分析结果
- 建议：基于数据给出的建议（可选）"""


def get_analysis_user_prompt(user_question, query_result, sql):
    """获取分析结论生成的用户提示"""
    result_preview = query_result.head(10).to_string() if hasattr(query_result, 'head') else str(query_result)
    
    return f"""用户问题：{user_question}

执行的SQL：{sql}

查询结果数据（前10行）：
{result_preview}

请基于以上数据给出专业的分析结论。"""