# test_api.py
from config import Config
import openai

client = openai.OpenAI(
    api_key=Config.DeepSeek.API_KEY,
    base_url=Config.DeepSeek.BASE_URL
)

try:
    response = client.embeddings.create(
        model=Config.GLM_Embedding_3.MODEL_NAME,
        input=["测试文本"],
        dimensions=2048 
    )
    print("✓ 向量API可用")
    print(f"向量维度: {len(response.data[0].embedding)}")
except Exception as e:
    print(f"✗ 向量API不可用: {e}")