from  multiprocessing import Process,Pool
import os
import base64
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()
api_key = os.getenv("ALIYUN_API_KEY")
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
def get_Client(api_key=api_key,base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"):
    client = OpenAI(
        api_key=api_key,  # 你的 API Key
        base_url=base_url,
    )   
    return client
def img_to_markdown(image_path):
    base64_image = encode_image(image_path)
    client = get_Client()
    completion = client.chat.completions.create(
        model="qwen3-vl-flash",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    },
                    {"type": "text", "text": "请识别图片中的表格内容，并以 Markdown 格式返回。"}
                ]
            }
        ]
    )
    
    return completion.choices[0].message.content

def clear(file_dir,target_file):
    target_file.parent.mkdir(parents=True, exist_ok=True)
    if not target_file.exists():
        target_file.touch()  # 创建空文件
        print(f"文件已创建: {target_file}")
    else:
        print(f"文件已存在: {target_file}")
    with open(file_dir, "r", encoding="utf-8") as f:
        content = f.read()
    t = content.count('![]')
    print(f"文件 {file_dir} 中找到 {t} 张图片。")
    for _ in range(t):
        start = content.find('![]')
        end = content.find(')', start )
        replaced = content[start:end+1]
        images_dir = file_dir.parent / replaced[4:-1] # 提取图片路径
        translation = img_to_markdown(str(images_dir))
        translation = translation.replace("markdown", "")
        content = content.replace(replaced, translation)
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"文件已处理: {target_file}")
    


if __name__=='__main__':
    ttt = []
    folds = Path.cwd() / 'parsed_results' 
    for fold in os.listdir(folds):
        fold_path = folds / fold
        for file in os.listdir(fold_path):
            if file.endswith('.md'):
                file_dir  = fold_path / file
                target_file = Path.cwd() /'processed' / file_dir.parent.name / file_dir.name
                ttt.append((file_dir,target_file))
    pool = Pool(3) 
    for file_dir,target_file in ttt[9:][7:][3:]:
        # print(file_dir,target_file)
        pool.apply_async(func=clear, args=(file_dir,target_file))
    pool.close()
    pool.join()
    


