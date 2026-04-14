# chart_generator.py
# 图表生成器

import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime
from config import CHART_OUTPUT_DIR, CHART_DEFAULT_TYPE

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


class ChartGenerator:
    """图表生成器类"""
    
    def __init__(self):
        self.output_dir = CHART_OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate(self, data, chart_type=None, title="数据图表", x_label=None, y_label=None):
        """
        生成图表
        
        Args:
            data: 数据，可以是DataFrame、字典或列表
            chart_type: 图表类型 (bar, line, pie, scatter)
            title: 图表标题
            x_label: X轴标签
            y_label: Y轴标签
        
        Returns:
            str: 保存的图表文件路径
        """
        chart_type = chart_type or CHART_DEFAULT_TYPE
        
        # 转换数据格式
        df = self._prepare_data(data)
        
        if df is None or df.empty:
            return None
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if chart_type == "bar":
            self._draw_bar(df, ax)
        elif chart_type == "line":
            self._draw_line(df, ax)
        elif chart_type == "pie":
            self._draw_pie(df, ax)
        elif chart_type == "scatter":
            self._draw_scatter(df, ax)
        else:
            self._draw_bar(df, ax)
        
        # 设置标题和标签
        ax.set_title(title, fontsize=14, fontweight='bold')
        if x_label:
            ax.set_xlabel(x_label)
        if y_label:
            ax.set_ylabel(y_label)
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        filename = f"chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def _prepare_data(self, data):
        """准备数据格式"""
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict):
            return pd.DataFrame([data])
        elif isinstance(data, list) and len(data) > 0:
            return pd.DataFrame(data)
        elif isinstance(data, tuple) and len(data) == 2:
            # 假设是 (columns, data) 格式
            columns, rows = data
            if columns and rows:
                return pd.DataFrame(rows, columns=columns)
        return None
    
    def _draw_bar(self, df, ax):
        """绘制柱状图"""
        # 如果有多列，取第一列作为x轴，第二列作为y轴
        if len(df.columns) >= 2:
            x_col = df.columns[0]
            y_col = df.columns[1]
            ax.bar(df[x_col], df[y_col])
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
        else:
            df.plot(kind='bar', ax=ax, legend=False)
    
    def _draw_line(self, df, ax):
        """绘制折线图"""
        if len(df.columns) >= 2:
            x_col = df.columns[0]
            y_col = df.columns[1]
            ax.plot(df[x_col], df[y_col], marker='o')
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
        else:
            df.plot(kind='line', ax=ax, legend=False)
    
    def _draw_pie(self, df, ax):
        """绘制饼图"""
        if len(df.columns) >= 2:
            labels = df[df.columns[0]]
            sizes = df[df.columns[1]]
            ax.pie(sizes, labels=labels, autopct='%1.1f%%')
        else:
            # 如果没有足够列，使用索引作为标签
            ax.pie(df.iloc[:, 0], labels=df.index, autopct='%1.1f%%')
    
    def _draw_scatter(self, df, ax):
        """绘制散点图"""
        if len(df.columns) >= 2:
            x_col = df.columns[0]
            y_col = df.columns[1]
            ax.scatter(df[x_col], df[y_col])
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
        else:
            ax.scatter(df.index, df.iloc[:, 0])
    
    def suggest_chart_type(self, data):
        """
        根据数据建议合适的图表类型
        
        Args:
            data: 数据
        
        Returns:
            str: 建议的图表类型
        """
        df = self._prepare_data(data)
        
        if df is None or df.empty:
            return "bar"
        
        num_rows = len(df)
        num_cols = len(df.columns)
        
        # 如果只有2列且数据量少，适合饼图
        if num_cols == 2 and num_rows <= 10:
            return "pie"
        
        # 如果数据有趋势性，适合折线图
        if num_cols >= 2 and df[df.columns[0]].dtype in ['int64', 'float64']:
            # 第一列是数值，可能适合折线图
            return "line"
        
        # 默认柱状图
        return "bar"


# 全局图表生成器实例
chart_generator = ChartGenerator()