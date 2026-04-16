from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import base64
from openai import OpenAI
from pathlib import Path
from config import Config
client = OpenAI(
        api_key=Config.DeepSeek.API_KEY,
        base_url=Config.DeepSeek.API_URL
    )
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
def img_to_markdown(image_path):
    base64_image = encode_image(image_path)
    
    completion = client.chat.completions.create(
        model=Config.GLM_4V_Flash.MODEL_NAME,
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
    content = completion.choices[0].message.content.replace("markdown", "")
    return content 

def clear(file_dir, target_file):
    try:
        print(f"开始处理: {file_dir.name}")
        
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_dir, "r", encoding="utf-8") as f:
            content = f.read()
        
        image_count = content.count('![]')
        print(f"{file_dir.name}: 发现 {image_count} 张图片")
        
        if image_count == 0:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ {file_dir.name}: 无图片，已复制")
            return
        
        # 处理图片
        current_content = content
        processed = 0
        
        for i in range(image_count):
            start = current_content.find('![]')
            end = current_content.find(')', start)
            replaced = current_content[start:end+1]
            images_dir = file_dir.parent / replaced[4:-1]
            
            print(f"  {file_dir.name}: 处理图片 {i+1}/{image_count} - {images_dir.name}")
            
            try:
                translation = img_to_markdown(str(images_dir))
                translation = translation.replace("markdown", "")
                current_content = current_content.replace(replaced, translation, 1)
                processed += 1
            except Exception as e:
                print(f"  ❌ {file_dir.name}: 图片识别失败 - {e}")
                current_content = current_content.replace(replaced, f"[识别失败]{replaced}", 1)
        
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(current_content)
        
        print(f"✅ {file_dir.name}: 完成处理 {processed}/{image_count} 张图片")
        
    except Exception as e:
        print(f"❌ {file_dir.name}: 处理失败 - {e}")



def main():
    print("=" * 60)
    print("开始处理")
    print("=" * 60)
    
    # 收集任务
    ttt = []
    folds = Path.cwd() / 'parsed_results' 
    
    for fold in os.listdir(folds):
        fold_path = folds / fold
        for file in os.listdir(fold_path):
            if file.endswith('.md'):
                file_dir = fold_path / file
                target_file = Path.cwd() / 'processed' / file_dir.parent.name / file_dir.name
                ttt.append((file_dir, target_file))
    
    print(f"共找到 {len(ttt)} 个文件")


    tasks_to_process = ttt # 从第10个文件开始
    print(f"本次处理 {len(tasks_to_process)} 个文件")
    print("-" * 60)
    
    with ThreadPoolExecutor(max_workers=int( Config.GLM_4V_Flash.MAX_WORKERS * 0.8) ) as executor:
        futures = []
        for file_dir, target_file in tasks_to_process:
            print(f"提交任务: {file_dir.name}")
            future = executor.submit(clear, file_dir, target_file)
            futures.append(future)
        
        # 可选：等待所有完成并处理异常
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"任务执行失败: {e}")
    
    print("=" * 60)
    print("所有任务处理完成！")
    return 
if __name__ == '__main__':
    p = r"F:\dddd\财务报告\reports-上交所\images\00fffac8941521f96848af6fb6b9ea8cc5ced519f0ac00f5563d79b706bc02ba.jpg"
    print(img_to_markdown(p))
