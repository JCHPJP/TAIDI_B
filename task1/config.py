# config.py
import os

class Config:
    # 数据库配置
    class DataBase:
        DB_PATH = "db/financial_data.db"
    
    class DeepSeek:
        BASE_URL = "https://llmapi.paratera.com"  
        API_KEY = "sk-PX3OOQz6HMYmJ6BsFf4lIw"
        MODEL_NAME = "DeepSeek-V3.2"  # 或你的模型名
        TIMEOUT = 120  
    
    class GLM_4V_Flash:
        MODEL_NAME = "GLM-4V-Flash"  # 或你的模型名
        MAX_WORKERS = 30  # 最大并发
    class GLM_4_Flash:
        MODEL_NAME = "GLM-4-Flash"  # 或你的模型名
        MAX_WORKERS = 1000  # 最大并发
        content = "128K"
    class GLM_4_5_Flash:
        MODEL_NAME = "GLM-4.5-Flash"  # 或你的模型名
        MAX_WORKERS = 30  # 最大并发
    class DeepSeek_R1_Distill_Qwen_32B:
        API_KEY = "fGnug0e7b8iHDACBIYCfwEVGJI4NCULAFihmTfJSfh4="
        BASE_URL = "http://127.0.0.1:6007/v1"  # 服务器公网IP
        MODEL_NAME= "DeepSeek-R1-Distill-Qwen-32B"  # 或你的模型名
        TIMEOUT = 180

    # 输出配置
    RESULT_FOLDER = "result"
    OUTPUT_EXCEL = "result_2.xlsx"
    maximum = 128000
    # 线程配置
    
