import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import base64
from openai import OpenAI
from pathlib import Path
from config import Config
from datetime import datetime

# 配置 logging
def setup_logging():
    """设置日志配置"""
    # 创建日志目录
    log_dir = Path.cwd() / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 日志文件名（按日期）
    log_file = log_dir / f'processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),  # 文件输出
            logging.StreamHandler()  # 控制台输出
        ]
    )
    return logging.getLogger(__name__)

# 初始化 logger
logger = setup_logging()

client = OpenAI(
    api_key=Config.DeepSeek.API_KEY,
    base_url=Config.DeepSeek.API_URL
)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
def img_to_markdown(image_path):
    try:
        base64_image = encode_image(image_path)
        
        completion = client.chat.completions.create(
            model=Config.GLM_4V_Flash.MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的OCR识别助手，擅长识别图片中的表格、文字和数据。请准确提取图片中的所有信息，并严格按照要求的格式返回。"
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        },
                        {
                            "type": "text", 
                            "text": """请识别并处理图片中的内容，要求如下：

1. 如果图片中有表格数据：
   - 以 Markdown 表格格式返回
   - 保持原有的行列结构和数据
   - 确保数据对齐和准确性

2. 如果图片中没有表格：
   - 用 Markdown 格式描述图片内容
   - 尽可能还原图片中的文字、数字等信息
   - 保持数据的完整性和准确性

3. 输出要求：
   - 只返回 Markdown 格式的内容
   - 不要添加任何额外的解释或说明
   - 不要包含"markdown"字样"""
                        }
                    ]
                }
            ],
            timeout=60,
            temperature=0.1  # 降低随机性，提高准确性
        )
        
        content = completion.choices[0].message.content
        # 移除可能出现的 markdown 标记
        content = content.replace("```markdown", "").replace("```", "").strip()
        logger.debug(f"成功识别图片: {image_path}")
        return content
        
    except Exception as e:
        logger.error(f"图片识别失败 {image_path}: {str(e)}")
        raise

def clear(file_dir, target_file):
    logger.info(f"开始处理文件: {file_dir.name}")
    
    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_dir, "r", encoding="utf-8") as f:
            content = f.read()
        
        image_count = content.count('![]')
        logger.info(f"{file_dir.name}: 发现 {image_count} 张图片")
        
        if image_count == 0:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"✅ {file_dir.name}: 无图片，已复制")
            return
        
        # 处理图片
        current_content = content
        processed = 0
        failed = 0
        
        for i in range(image_count):
            start = current_content.find('![]')
            end = current_content.find(')', start)
            replaced = current_content[start:end+1]
            images_dir = file_dir.parent / replaced[4:-1]
            
            logger.debug(f"  {file_dir.name}: 处理图片 {i+1}/{image_count} - {images_dir.name}")
            
            try:
                translation = img_to_markdown(str(images_dir))
                translation = translation.replace("markdown", "")
                current_content = current_content.replace(replaced, translation, 1)
                processed += 1
                logger.info(f"  ✅ {file_dir.name}: 图片 {i+1}/{image_count} 识别成功")
            except Exception as e:
                failed += 1
                logger.error(f"  ❌ {file_dir.name}: 图片 {i+1}/{image_count} 识别失败 - {e}")
                current_content = current_content.replace(replaced, f"[识别失败]{replaced}", 1)
        
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(current_content)
        
        logger.info(f"✅ {file_dir.name}: 完成处理 (成功: {processed}, 失败: {failed}, 总计: {image_count})")
        
    except Exception as e:
        logger.error(f"❌ {file_dir.name}: 文件处理失败 - {e}", exc_info=True)

def main():
    logger.info("=" * 60)
    logger.info("开始处理任务")
    logger.info("=" * 60)
    
    # 收集任务
    ttt = []
    folds = Path.cwd() / 'parsed_results' / '财务报告'
    
    if not folds.exists():
        logger.error(f"目录不存在: {folds}")
        return
    
    for fold in os.listdir(folds):
        fold_path = folds / fold
        if not fold_path.is_dir():
            continue
            
        for file in os.listdir(fold_path):
            if file.endswith('.md'):
                file_dir = fold_path / file
                target_file = Path.cwd() / 'processed' / '财务报告' / file_dir.parent.name / file_dir.name
                ttt.append((file_dir, target_file))
    
    logger.info(f"共找到 {len(ttt)} 个文件需要处理")
    
    if not ttt:
        logger.warning("没有找到需要处理的文件")
        return
    
    tasks_to_process = ttt 
    logger.info(f"本次处理 {len(tasks_to_process)} 个文件")
    logger.info("-" * 60)
    
    # 统计成功和失败的任务数
    success_count = 0
    fail_count = 0
    
    with ThreadPoolExecutor(max_workers=int(Config.GLM_4V_Flash.MAX_WORKERS * 0.8)) as executor:
        futures = {}
        for file_dir, target_file in tasks_to_process:
            logger.info(f"提交任务: {file_dir.name}")
            future = executor.submit(clear, file_dir, target_file)
            futures[future] = file_dir.name
        
        # 等待所有完成并处理异常
        for future in as_completed(futures):
            file_name = futures[future]
            try:
                future.result()
                success_count += 1
                logger.info(f"✅ 任务完成: {file_name}")
            except Exception as e:
                fail_count += 1
                logger.error(f"❌ 任务执行失败: {file_name} - {e}", exc_info=True)
    
    # 输出最终统计
    logger.info("=" * 60)
    logger.info(f"所有任务处理完成！")
    logger.info(f"成功: {success_count}, 失败: {fail_count}, 总计: {len(tasks_to_process)}")
    logger.info("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("用户中断程序")
    except Exception as e:
        logger.error(f"程序异常退出: {e}", exc_info=True)