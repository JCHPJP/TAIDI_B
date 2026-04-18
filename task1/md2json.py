import json
import re
import os
import logging
from openai import OpenAI
import time
from pathlib import Path
from datetime import datetime
from config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import signal
import sys

# ==================== 全局配置 ====================
stats_lock = threading.Lock()
_client_instance = None
_client_lock = threading.Lock()
processed_files_lock = threading.Lock()

# ==================== 配置日志 ====================
def setup_logger(name=None, log_level=logging.INFO):
    """设置日志配置"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_filename = f"{log_dir}/financial_extract_{datetime.now().strftime('%Y%m%d')}.log"
    error_log_filename = f"{log_dir}/financial_extract_error_{datetime.now().strftime('%Y%m%d')}.log"
    
    logger = logging.getLogger(name) if name else logging.getLogger(__name__)
    logger.setLevel(log_level)
    
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    error_handler = logging.FileHandler(error_log_filename, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger('FinancialExtractor')

# ==================== 配置 ====================
PROMPT_FILE = Path().cwd() / "prompt-extract.md"
schema_path = Path().cwd() / 'financial_schema.json'
OUTPUT_DIR = Path("output")
PROGRESS_FILE = OUTPUT_DIR / "progress.json"
# ============================================

# 统计信息
stats = {
    "total": 0,
    "success": 0,
    "failed": 0,
    "start_time": None,
    "end_time": None
}

# 已处理文件集合（用于断点续传）
processed_files = set()

def load_progress():
    """加载已处理进度"""
    global processed_files
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                processed_files = set(data.get("processed", []))
                logger.info(f"加载进度: 已处理 {len(processed_files)} 个文件")
        except Exception as e:
            logger.warning(f"加载进度文件失败: {e}")

def save_progress():
    """保存处理进度"""
    try:
        with processed_files_lock:
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump({"processed": list(processed_files)}, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"保存进度失败: {e}")

def signal_handler(signum, frame):
    """优雅退出处理"""
    logger.info(f"\n收到信号 {signum}，正在保存进度...")
    save_progress()
    logger.info("进度已保存，程序退出")
    sys.exit(0)

# 注册信号处理
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def get_client(api_key=Config.API_KEY, base_url=Config.BASE_URL, timeout=None):
    """获取OpenAI客户端（单例模式）"""
    global _client_instance
    with _client_lock:
        if _client_instance is None:
            _client_instance = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout or Config.DeepSeek.TIMEOUT
            )
        return _client_instance

def getAllMarkdownFiles(path=Path(__file__).parent.parent / "processed" / "财务报告") -> list:
    """获取所有未处理的Markdown文件（自动跳过已生成JSON的文件）"""
    
    md_files_path = Path(path)
    print(f"正在扫描目录 {md_files_path} 下的所有 Markdown 文件...")
    
    if not md_files_path.exists():
        logger.error(f"目录不存在: {md_files_path}")
        return []
    
    all_md_files = list(md_files_path.rglob("*.md"))
    
    # 获取已处理的文件（已生成JSON的文件）
    output_dir = Path(__file__).parent / "output"
    already_processed = set()
    
    if output_dir.exists():
        already_processed = {
            file.stem for file in output_dir.rglob("*.json")
        }
        logger.info(f"已处理文件数: {len(already_processed)}")
    
    # 加载进度文件中的已处理文件
    load_progress()
    already_processed.update(processed_files)
    
    # 过滤：只保留未处理的文件
    unprocessed_files = [
        str(md_file) for md_file in all_md_files 
        if md_file.stem not in already_processed
    ]
    
    logger.info(f"扫描完成:")
    logger.info(f"  - 总Markdown文件: {len(all_md_files)}")
    logger.info(f"  - 已处理文件: {len(already_processed)}")
    logger.info(f"  - 待处理文件: {len(unprocessed_files)}")
    
    return unprocessed_files

def fix_json_with_llm(broken_json, max_retries=2):
    """使用大模型修复不完整的JSON"""
    if not broken_json:
        return None
    
    logger.info(f"尝试修复不完整的JSON，长度: {len(broken_json)}")
    
    fix_prompt = f"""以下是一个不完整的JSON字符串，请修复成完整、合法的JSON格式。

不完整的JSON:
{broken_json}

要求：
1. 只返回修复后的JSON，不要包含其他解释性文字
2. 保持原有的字段和值不变
3. 补充缺失的括号、引号等
4. 确保JSON格式正确

请直接返回修复后的JSON："""

    for attempt in range(max_retries):
        try:
            # 修复时使用更长的超时
            timeout = 120
            client = get_client(timeout=timeout)
            response = client.chat.completions.create(
                model=Config.DeepSeek.MODEL_NAME,
                messages=[
                    {"role": "system", "content": "你是一个JSON修复专家。只返回修复后的JSON，不要有其他内容。"},
                    {"role": "user", "content": fix_prompt}
                ],
                temperature=0.1,
                max_tokens=4000,
                stream=False,
                timeout=timeout
            )
            
            fixed_content = response.choices[0].message.content.strip()
            fixed_json = extract_json(fixed_content)
            
            if fixed_json:
                logger.info(f"✅ JSON修复成功")
                return fixed_json
            else:
                logger.warning(f"修复后仍无法解析，重试 {attempt + 1}/{max_retries}")
                
        except Exception as e:
            logger.error(f"修复JSON失败: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # 指数退避
    
    logger.error("JSON修复失败")
    return None

def extract_json(text) -> dict:
    """从文本中提取JSON"""
    if not text:
        return None
    
    cleaned_text = text
    code_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    match = re.search(code_pattern, text)
    if match:
        cleaned_text = match.group(1)
    
    brace_count = 0
    start_pos = -1
    end_pos = -1
    
    for i, char in enumerate(cleaned_text):
        if char == '{':
            if brace_count == 0:
                start_pos = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                end_pos = i + 1
                break
    
    if start_pos != -1 and end_pos != -1:
        json_str = cleaned_text[start_pos:end_pos]
        try:
            return json.loads(json_str)
        except:
            try:
                open_braces = json_str.count('{')
                close_braces = json_str.count('}')
                if open_braces > close_braces:
                    json_str += '}' * (open_braces - close_braces)
                open_brackets = json_str.count('[')
                close_brackets = json_str.count(']')
                if open_brackets > close_brackets:
                    json_str += ']' * (open_brackets - close_brackets)
                return json.loads(json_str)
            except:
                pass
    
    try:
        return json.loads(cleaned_text.strip())
    except:
        pass
    
    brace_pattern = r'\{[\s\S]*\}'
    match = re.search(brace_pattern, cleaned_text)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass
    
    return None

def call_llm(prompt, file_name="", max_retries=5):
    """调用大模型，增加重试机制和动态超时"""
    logger.info(f"调用大模型处理文件: {file_name}, prompt长度: {len(prompt)}")
    start_time = time.time()
    
    for attempt in range(max_retries):
        try:
            # 动态超时：根据重试次数增加超时时间
            timeout = Config.DeepSeek.TIMEOUT * (attempt + 1)
            client = get_client(timeout=timeout)
            
            response = client.chat.completions.create(
                model=Config.DeepSeek.MODEL_NAME,
                messages=[
                    {"role": "system", "content": "你是一个专业的财务数据提取专家。请严格按照JSON格式返回结果，不要包含其他解释性文字。确保JSON完整，不要截断。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                stream=False,
                max_tokens=4000,
                timeout=timeout
            )
            
            elapsed_time = time.time() - start_time
            content = response.choices[0].message.content
            
            if content.count('{') != content.count('}'):
                logger.warning(f"JSON括号不匹配，尝试修复...")
                
                fixed_result = fix_json_with_llm(content)
                
                if fixed_result:
                    logger.info(f"文件 {file_name} JSON修复成功")
                    return {"success": True, "data": fixed_result, "file": file_name}
                else:
                    if attempt < max_retries - 1:
                        wait_time = min(2 ** attempt, 30)
                        logger.info(f"JSON修复失败，等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"文件 {file_name} JSON修复失败，已达最大重试次数")
                        return {"success": False, "error": "JSON解析失败且无法修复", "file": file_name}
            
            result = extract_json(content)
            if result:
                logger.info(f"文件 {file_name} 数据提取成功，耗时: {elapsed_time:.2f}秒")
                return {"success": True, "data": result, "file": file_name}
            else:
                logger.error(f"文件 {file_name} JSON解析失败")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return {"success": False, "error": "JSON解析失败", "file": file_name}
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"文件 {file_name} - 调用失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
            
            if attempt < max_retries - 1:
                # 根据错误类型设置不同的等待时间
                if "timeout" in error_msg.lower():
                    wait_time = min(2 ** (attempt + 1), 60)  # 2,4,8,16,32秒，最大60秒
                elif "rate_limit" in error_msg.lower():
                    wait_time = 10  # 限流等待10秒
                else:
                    wait_time = 2
                
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                continue
            return {"success": False, "error": error_msg, "file": file_name}
    
    return {"success": False, "error": "超过最大重试次数", "file": file_name}

def GetDefaultTableData():
    """获取默认的表格数据结构"""
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取financial_schema.json失败: {e}")
        raise

def get_prompt():
    """获取prompt模板"""
    try:
        prompt_path = Path().cwd() / PROMPT_FILE
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.warning(f"读取prompt文件失败，使用默认模板: {e}")
        return """
上次提取的数据：
{last_data}
现在从以下新财报中提取数据，更新到上面的JSON中：
{new_text}
输出更新后的JSON,只需要**上次提取的数据**字段，禁止添加其他字段，防止输出的json格式错误。输出为json格式
        """

def split_and_merge(paper):
    """将段落分割成适合模型处理的块"""
    if not paper:
        return []
    
    import re
    # 只匹配行首的单个 # （不匹配 ## 或 ###）
    paragraphs = re.split(r'(?=^#\s)', paper, flags=re.MULTILINE)
    
    result = []
    current = ""
    max_len = int(Config.tokens['128k'] * 0.8)
    
    for p in paragraphs:
        if not p or not p.strip():
            continue
        
        if len(current) + len(p) <= max_len:
            current += p + "\n"
        else:
            if current:
                result.append(current)
            current = p + "\n"
    
    if current:
        result.append(current)
    
    return result

def process_single_file(file_path):
    """处理单个文件（不包含统计，只返回结果）"""
    file_name = Path(file_path).name
    output_file = OUTPUT_DIR / f"{Path(file_path).stem}.json"
    
    # 检查输出文件是否已存在
    if output_file.exists():
        logger.info(f"文件 {file_name} 已存在，跳过处理")
        return {
            "file": file_name,
            "success": True,
            "skipped": True,
            "output_file": str(output_file),
            "path": str(file_path)
        }
    
    logger.info(f"开始处理文件: {file_path}")
    start_time = time.time()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            financial_data = f.read()
        
        paragraphs = financial_data.split('#')
        new_segments = split_and_merge(paragraphs)

        scheme = GetDefaultTableData()
        prompt_template = get_prompt()

        for idx, segment in enumerate(new_segments, 1):
            logger.info(f"处理文件 {file_name} 的第 {idx}/{len(new_segments)} 个块")
            
            prompt = prompt_template.replace("{last_data}", scheme)
            prompt = prompt.replace("{new_text}", segment)
            
            response = call_llm(prompt, file_name)
            
            if response.get("success"):
                response_map_data = response.get("data")
                scheme = json.dumps(response_map_data, ensure_ascii=False, indent=2)
            else:
                return {
                    "file": file_name,
                    "success": False,
                    "error": response.get('error'),
                    "path": str(file_path)
                }
        
        elapsed_time = time.time() - start_time
        
        # 保存结果
        OUTPUT_DIR.mkdir(exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(scheme)
        
        logger.info(f"文件 {file_name} 处理完成，耗时: {elapsed_time:.2f}秒")
        
        # 记录到已处理集合
        with processed_files_lock:
            processed_files.add(Path(file_path).stem)
        
        return {
            "file": file_name,
            "success": True,
            "data": scheme,
            "output_file": str(output_file),
            "time": elapsed_time,
            "path": str(file_path)
        }
        
    except Exception as e:
        logger.error(f"处理文件 {file_path} 时发生错误: {e}", exc_info=True)
        return {
            "file": file_name,
            "success": False,
            "error": str(e),
            "path": str(file_path)
        }

def process_files_multithread(files, max_workers=10):
    """多线程处理文件"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    stats["total"] = len(files)
    stats["start_time"] = datetime.now()
    stats["success"] = 0
    stats["failed"] = 0
    
    logger.info("="*60)
    logger.info(f"开始多线程处理 {len(files)} 个文件，线程数: {max_workers}")
    logger.info("="*60)
    
    results = []
    failed_files = []
    completed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(process_single_file, file_path): file_path
            for file_path in files
        }
        
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            completed += 1
            
            try:
                result = future.result()
                
                if result.get("success"):
                    with stats_lock:
                        stats["success"] += 1
                    logger.info(f"✅ 进度: [{completed}/{len(files)}] 成功 - {Path(file_path).name}")
                else:
                    with stats_lock:
                        stats["failed"] += 1
                    failed_files.append(result)
                    logger.error(f"❌ 进度: [{completed}/{len(files)}] 失败 - {Path(file_path).name} - 错误: {result.get('error')}")
                
                results.append(result)
                
                # 每10个文件保存一次进度
                if completed % 10 == 0:
                    save_progress()
                    logger.info(f"📊 阶段性统计: 已完成 {completed}/{len(files)}, "
                              f"成功: {stats['success']}, 失败: {stats['failed']}")
                
            except Exception as e:
                logger.error(f"处理文件 {file_path} 时发生异常: {e}", exc_info=True)
                failed_result = {
                    "file": Path(file_path).name,
                    "success": False,
                    "error": str(e),
                    "path": str(file_path)
                }
                results.append(failed_result)
                failed_files.append(failed_result)
                with stats_lock:
                    stats["failed"] += 1
    
    stats["end_time"] = datetime.now()
    elapsed_time = (stats["end_time"] - stats["start_time"]).total_seconds()
    
    # 最终保存进度
    save_progress()
    
    # 最终统计
    logger.info("="*60)
    logger.info("多线程处理完成")
    logger.info(f"📊 最终统计:")
    logger.info(f"   总文件数: {stats['total']}")
    logger.info(f"   成功: {stats['success']}")
    logger.info(f"   失败: {stats['failed']}")
    if stats['total'] > 0:
        logger.info(f"   成功率: {stats['success']/stats['total']*100:.2f}%")
    logger.info(f"   总耗时: {elapsed_time:.2f}秒")
    if len(files) > 0:
        logger.info(f"   平均每个文件: {elapsed_time/len(files):.2f}秒")
    logger.info("="*60)
    
    # 保存处理报告
    report_file = OUTPUT_DIR / f"processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_data = {
        "start_time": stats["start_time"].isoformat(),
        "end_time": stats["end_time"].isoformat(),
        "total": stats["total"],
        "success": stats["success"],
        "failed": stats["failed"],
        "total_time_seconds": elapsed_time,
        "failed_files": [
            {"file": f.get("file"), "error": f.get("error")} 
            for f in failed_files
        ]
    }
    if stats['total'] > 0:
        report_data["success_rate"] = f"{stats['success']/stats['total']*100:.2f}%"
        report_data["avg_time_per_file"] = elapsed_time / len(files)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📄 处理报告已保存: {report_file}")
    
    return results

def retry_failed_files(failed_files, max_workers=5, max_retries=2):
    """重试失败的文件"""
    if not failed_files:
        logger.info("没有失败的文件需要重试")
        return []
    
    logger.info("="*60)
    logger.info(f"开始重试 {len(failed_files)} 个失败文件")
    logger.info("="*60)
    
    # 等待一段时间后再重试
    time.sleep(10)
    
    # 提取文件路径
    file_paths = [f.get("path") for f in failed_files if f.get("path")]
    
    # 降低并发数重试
    retry_results = process_files_multithread(file_paths, max_workers=max_workers)
    
    return retry_results

def main():
    """主函数"""
    logger.info("="*60)
    logger.info("程序启动")
    logger.info("="*60)
    
    try:
        reports_path = Path.cwd().parent / "processed" / "财务报告"
        logger.info(f"扫描目录: {reports_path}")
        all_files = getAllMarkdownFiles(reports_path) 
        logger.info(f"找到 {len(all_files)} 个markdown文件")
        
        if not all_files:
            logger.warning("没有找到markdown文件")
            return
        
        # 第一轮处理
        results = process_files_multithread(all_files, max_workers=10)
        
        # 收集失败的文件
        failed_files = [r for r in results if not r.get("success")]
        
        # 如果有失败的文件，进行重试
        if failed_files:
            logger.info(f"发现 {len(failed_files)} 个失败文件，准备重试...")
            retry_results = retry_failed_files(failed_files, max_workers=5)
            
            # 更新最终统计
            final_success = len([r for r in results if r.get("success")]) + \
                           len([r for r in retry_results if r.get("success")])
            final_failed = len([r for r in results if not r.get("success")]) - \
                          len([r for r in retry_results if r.get("success")])
            
            logger.info("="*60)
            logger.info("最终统计（含重试）:")
            logger.info(f"   总文件数: {len(all_files)}")
            logger.info(f"   成功: {final_success}")
            logger.info(f"   失败: {final_failed}")
            logger.info(f"   成功率: {final_success/len(all_files)*100:.2f}%")
            logger.info("="*60)
        
        logger.info("所有文件处理完成！")
        
    except Exception as e:
        logger.error(f"程序运行出错: {e}", exc_info=True)
    
    logger.info("="*60)
    logger.info("程序结束")
    logger.info("="*60)

def quick_test():
    """快速测试单个文件"""
    logger.setLevel(logging.DEBUG)
    
    test_file = Path().cwd().parent / 'processed' / '财务报告' / 'reports-上交所' / '600080_20230428_FQ2V.md'
    
    logger.info("快速测试开始")
    logger.info(f"测试文件: {test_file}")
    
    if not os.path.exists(test_file):
        logger.error(f"文件不存在: {test_file}")
        return
    
    try:
        result = process_single_file(test_file)
        
        if result and result.get("success"):
            logger.info("✅ 测试成功!")
            logger.info(f"输出文件: {result.get('output_file')}")
            
            if result.get('output_file') and os.path.exists(result['output_file']):
                with open(result['output_file'], 'r', encoding='utf-8') as f:
                    output_data = json.load(f)
                    logger.info(f"JSON验证成功，包含 {len(output_data)} 个顶级字段")
        else:
            logger.error(f"❌ 测试失败! 错误: {result.get('error') if result else '未知错误'}")
    except Exception as e:
        logger.error(f"测试异常: {e}", exc_info=True)

if __name__ == "__main__":
    main()