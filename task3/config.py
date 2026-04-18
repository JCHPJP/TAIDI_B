# config.py

class Config:
    # 数据库配置
    class DataBase:
        DB_PATH = "db/financial_data.db"
    API_KEY =  "sk-UMdV9qSg2-ZQymIRCYq5ew"
    BASE_URL = "https://llmapi.paratera.com/v1/"
    class DeepSeek:
        BASE_URL = "https://llmapi.paratera.com"  
        MODEL_NAME = "DeepSeek-V3.2"  # 或你的模型名
        TIMEOUT = 480 
    
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
        BASE_URL = "http://127.0.0.1:6007/v1"  # 私人公网IP
        MODEL_NAME= "DeepSeek-R1-Distill-Qwen-32B"  # 模型名
        TIMEOUT = 180
    class GLM_Embedding_3:  
        MODEL_NAME = "GLM-Embedding-3"
    class Doubao_Embedding_Large_Text:
        MODEL_NAME = 'Doubao-Embedding-Large-Text'
        

    tokens = {'32k': 32768, '64k': 65536, '128k': 131072 }
    
