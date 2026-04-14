# config.py
import os

class Config:
    # 数据库配置
    class DataBase:
        DB_PATH = "db/financial_data.db"
    
    class DeepSeek:
        API_URL = "https://llmapi.paratera.com"  
        API_KEY = "sk-93Yty17YQKAputyE9Rap3g"
        MODEL_NAME = "DeepSeek-V3.2"  # 或你的模型名
    
    class GLM_4V_Flash:
        MODEL_NAME = "GLM-4V-Flash"  # 或你的模型名
        MAX_WORKERS = 30  # 最大并发


    # 输出配置
    RESULT_FOLDER = "result"
    OUTPUT_EXCEL = "result_2.xlsx"

    # 线程配置
    
    