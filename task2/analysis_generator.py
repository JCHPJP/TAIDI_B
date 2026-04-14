# analysis_generator.py
# 分析结论生成器

from llm_client import deepseek_client
from prompts.analysis_prompts import ANALYSIS_SYSTEM_PROMPT, get_analysis_user_prompt
from database import db
import pandas as pd


class AnalysisGenerator:
    """分析结论生成器类"""
    
    def __init__(self):
        pass
    
    def generate_analysis(self, user_question, query_result, sql):
        """
        生成分析结论
        
        Args:
            user_question: 用户原始问题
            query_result: 查询结果（DataFrame）
            sql: 执行的SQL语句
        
        Returns:
            str: 分析结论文本
        """
        if query_result is None or query_result.empty:
            return "没有足够的数据进行分析。"
        
        user_prompt = get_analysis_user_prompt(user_question, query_result, sql)
        
        response = deepseek_client.chat_with_system(
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.5
        )
        
        if response:
            return response
        
        # 如果AI分析失败，提供基础分析
        return self._basic_analysis(query_result)
    
    def _basic_analysis(self, df):
        """
        基础统计分析（当AI分析失败时的备选）
        
        Args:
            df: 数据DataFrame
        
        Returns:
            str: 基础分析结论
        """
        analysis = []
        analysis.append("【基础统计分析】\n")
        
        # 对数值列进行分析
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) > 0:
            for col in numeric_cols:
                mean_val = df[col].mean()
                max_val = df[col].max()
                min_val = df[col].min()
                sum_val = df[col].sum()
                
                analysis.append(f"【{col}】")
                analysis.append(f"  - 总计: {sum_val:,.2f}")
                analysis.append(f"  - 平均值: {mean_val:,.2f}")
                analysis.append(f"  - 最高值: {max_val:,.2f}")
                analysis.append(f"  - 最低值: {min_val:,.2f}")
                analysis.append("")
        
        # 如果有分类列，进行分组统计
        if len(df.columns) >= 2:
            first_col = df.columns[0]
            second_col = df.columns[1] if len(df.columns) > 1 else None
            
            if second_col and df[second_col].dtype in ['int64', 'float64']:
                analysis.append(f"【按{first_col}分组统计】")
                
                # 按第一列分组，对第二列求和
                grouped = df.groupby(first_col)[second_col].sum().sort_values(ascending=False)
                
                analysis.append(f"最高: {grouped.index[0]} - {grouped.iloc[0]:,.2f}")
                if len(grouped) > 1:
                    analysis.append(f"最低: {grouped.index[-1]} - {grouped.iloc[-1]:,.2f}")
                
                analysis.append("")
        
        return "\n".join(analysis)
    
    def analyze_trend(self, df, date_col=None, value_col=None):
        """
        分析数据趋势
        
        Args:
            df: 数据DataFrame
            date_col: 日期列名
            value_col: 数值列名
        
        Returns:
            str: 趋势分析结论
        """
        if df.empty:
            return "无数据可分析"
        
        # 自动识别日期列和数值列
        if date_col is None:
            for col in df.columns:
                if 'date' in col.lower() or '时间' in col:
                    date_col = col
                    break
        
        if value_col is None:
            for col in df.columns:
                if df[col].dtype in ['int64', 'float64'] and col != date_col:
                    value_col = col
                    break
        
        if date_col and value_col:
            # 确保日期格式正确
            df_sorted = df.sort_values(by=date_col)
            values = df_sorted[value_col].values
            
            if len(values) >= 2:
                trend = "上升" if values[-1] > values[0] else "下降"
                change_pct = ((values[-1] - values[0]) / values[0]) * 100
                
                analysis = f"趋势分析：\n"
                analysis += f"从开始到结束，{value_col}呈{trend}趋势，"
                analysis += f"变化幅度为 {abs(change_pct):.1f}%。"
                return analysis
        
        return "无法进行趋势分析，请确保数据包含日期列和数值列。"
    
    def compare_groups(self, df, group_col=None, value_col=None):
        """
        分组对比分析
        
        Args:
            df: 数据DataFrame
            group_col: 分组列名
            value_col: 数值列名
        
        Returns:
            str: 对比分析结论
        """
        if df.empty:
            return "无数据可分析"
        
        # 自动识别分组列和数值列
        if group_col is None:
            for col in df.columns:
                if df[col].dtype == 'object':
                    group_col = col
                    break
        
        if value_col is None:
            for col in df.columns:
                if df[col].dtype in ['int64', 'float64'] and col != group_col:
                    value_col = col
                    break
        
        if group_col and value_col:
            grouped = df.groupby(group_col)[value_col].sum().sort_values(ascending=False)
            
            analysis = f"对比分析（按{group_col}）：\n"
            analysis += f"最高的是 {grouped.index[0]}，{value_col}为 {grouped.iloc[0]:,.2f}\n"
            
            if len(grouped) > 1:
                analysis += f"最低的是 {grouped.index[-1]}，{value_col}为 {grouped.iloc[-1]:,.2f}\n"
                analysis += f"差距为 {(grouped.iloc[0] / grouped.iloc[-1]):.1f} 倍"
            
            return analysis
        
        return "无法进行对比分析，请确保数据包含分组列和数值列。"


# 全局分析生成器实例
analysis_generator = AnalysisGenerator()