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
from threading import Lock

# ==================== 配置日志 ====================
def setup_logger(name=None, log_level=logging.INFO):
    """设置日志配置"""
    # 创建日志目录
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 生成日志文件名（按日期）
    log_filename = f"{log_dir}/financial_extract_{datetime.now().strftime('%Y%m%d')}.log"
    error_log_filename = f"{log_dir}/financial_extract_error_{datetime.now().strftime('%Y%m%d')}.log"
    
    # 创建logger
    logger = logging.getLogger(name) if name else logging.getLogger(__name__)
    logger.setLevel(log_level)
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器（记录所有日志）
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # 错误日志处理器（只记录错误）
    error_handler = logging.FileHandler(error_log_filename, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger

# 创建全局logger
logger = setup_logger('FinancialExtractor')

# ==================== 配置 ====================
DB_PATH = "financial_data.db"
PROMPT_FILE = "prompt-extract.md"
MAX_WORKERS = 10  # 线程数，可根据API限制和机器性能调整
OUTPUT_DIR = Path("output")  # 输出目录
# ============================================

# 线程锁，用于保护共享资源
file_lock = Lock()
stats_lock = Lock()

# 统计信息
stats = {
    "total": 0,
    "success": 0,
    "failed": 0,
    "start_time": None,
    "end_time": None
}

def get_client():
    """每个线程独立创建客户端"""
    try:
        logger.debug("正在创建OpenAI客户端")
        return OpenAI(
            api_key=Config.DeepSeek.API_KEY,
            base_url=Config.DeepSeek.BASE_URL,  
            timeout=Config.DeepSeek.TIMEOUT
        )
    except Exception as e:
        logger.error(f"创建OpenAI客户端失败: {e}", exc_info=True)
        raise

def getAllMarkdownFiles(path= Path.cwd().parent / "processed" /"财务报告" )->list:
    print(f"正在扫描目录 {path} 下的所有 Markdown 文件...")
    md_files = Path(path).rglob("*.md")
    return  [ str(file) for file in md_files]


def extract_json(text):
    """从大模型返回的文本中提取JSON（处理各种包装格式和不完整JSON）"""
    if not text:
        logger.warning("提取JSON时接收到空文本")
        return None
    
    logger.debug(f"开始提取JSON，文本长度: {len(text)}")
    
    # 先尝试提取代码块中的内容
    cleaned_text = text
    
    # 提取 ```json ... ``` 或 ``` ... ``` 中的内容
    code_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    match = re.search(code_pattern, text)
    if match:
        cleaned_text = match.group(1)
        logger.debug("提取到代码块内容")
    
    # 尝试找到完整的JSON对象
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
        logger.debug(f"提取到JSON字符串，长度: {len(json_str)}")
        
        # 尝试解析
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}，尝试修复")
            
            # 尝试修复不完整的JSON
            try:
                # 添加缺失的闭合括号
                open_braces = json_str.count('{')
                close_braces = json_str.count('}')
                if open_braces > close_braces:
                    json_str += '}' * (open_braces - close_braces)
                    logger.debug(f"添加 {open_braces - close_braces} 个闭合括号")
                
                open_brackets = json_str.count('[')
                close_brackets = json_str.count(']')
                if open_brackets > close_brackets:
                    json_str += ']' * (open_brackets - close_brackets)
                    logger.debug(f"添加 {open_brackets - close_brackets} 个闭合方括号")
                
                return json.loads(json_str)
            except:
                pass
    
    # 直接解析
    try:
        return json.loads(cleaned_text.strip())
    except:
        pass
    
    # 提取 { ... } 花括号内容
    brace_pattern = r'\{[\s\S]*\}'
    match = re.search(brace_pattern, cleaned_text)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass
    
    logger.error(f"所有JSON提取方法都失败")
    return None

def call_llm(prompt, file_name="", max_retries=3):
    """调用大模型，支持重试"""
    logger.info(f"调用大模型处理文件: {file_name}, prompt长度: {len(prompt)}")
    start_time = time.time()
    
    for attempt in range(max_retries):
        try:
            client = get_client()
            response = client.chat.completions.create(
                model=Config.GLM_4_Flash.MODEL_NAME,
                messages=[
                    {"role": "system", "content": "你是一个专业的财务数据提取专家。请严格按照JSON格式返回结果，不要包含其他解释性文字。确保JSON完整，不要截断。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                stream=False,
                max_tokens=4000  # 增加到4000
            )
            
            elapsed_time = time.time() - start_time
            content = response.choices[0].message.content.strip()
            logger.debug(f"大模型响应成功，耗时: {elapsed_time:.2f}秒，响应长度: {len(content)}")
            
            # 检查响应是否完整
            if content.count('{') != content.count('}'):
                logger.warning(f"JSON括号不匹配，可能被截断。{{ count: {content.count('{')}, }} count: {content.count('}')}")
                if attempt < max_retries - 1:
                    logger.info(f"重试第 {attempt + 2} 次...")
                    time.sleep(2)
                    continue
            
            result = extract_json(content)
            if result:
                logger.info(f"文件 {file_name} 数据提取成功")
                return {"success": True, "data": result, "file": file_name}
            else:
                logger.error(f"文件 {file_name} JSON解析失败")
                if attempt < max_retries - 1:
                    logger.info(f"重试第 {attempt + 2} 次...")
                    time.sleep(2)
                    continue
                return {"success": False, "error": "JSON解析失败", "file": file_name}
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"文件 {file_name} - 调用失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
                continue
            return {"success": False, "error": error_msg, "file": file_name}
    
    return {"success": False, "error": "超过最大重试次数", "file": file_name}

def GetDefaultTableData():
    """获取默认表数据"""
    try:
        schema_path = Path().cwd() / 'financial_schema.json'
        logger.debug(f"读取默认表数据: {schema_path}")
        with open(schema_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"找不到financial_schema.json文件: {schema_path}")
        raise
    except Exception as e:
        logger.error(f"读取financial_schema.json失败: {e}", exc_info=True)
        raise

def get_prompt():
    """获取提示词模板"""
    try:
        prompt_path = Path().cwd() / PROMPT_FILE
        logger.debug(f"读取提示词模板: {prompt_path}")
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()
        return prompt
    except FileNotFoundError:
        logger.error(f"找不到{prompt_path}文件")
        raise
    except Exception as e:
        logger.error(f"读取提示词模板失败: {e}", exc_info=True)
        raise

def split_and_merge(paragraphs):
    """将段落重新拼接，每段不超过max_len"""
    logger.info(f"开始分割和合并段落，原始段落数: {len(paragraphs)}")
    result = []
    current = ""
    max_len = int(Config.tokens['32k'] * 0.5)  # 降低到0.5避免输出截断
    
    for i, p in enumerate(paragraphs):
        # 如果当前段加上新段落会超长，就保存当前段，重新开始
        if len(current) + len(p) <= max_len:
            current += p + "\n"
        else:
            if current:
                result.append(current)
                logger.debug(f"段落 {i} 创建新块，当前块数量: {len(result)}")
            current = p + "\n"
    
    # 最后一段
    if current:
        result.append(current)
    
    logger.info(f"段落分割完成，生成 {len(result)} 个块")
    return result

def process_single_file(file_path, prompt_template, default_data):
    """处理单个文件（用于多线程）"""
    file_name = Path(file_path).name
    logger.info(f"开始处理文件: {file_path}")
    start_time = time.time()
    
    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            financial_data = f.read()
        
        logger.info(f"文件读取成功，内容长度: {len(financial_data)} 字符")
        
        # 分割段落
        paragraphs = financial_data.split('#')
        
        # 合并段落
        new_segments = split_and_merge(paragraphs)
        
        last_data = default_data
        
        # 处理每个段落块
        for idx, segment in enumerate(new_segments, 1):
            logger.info(f"处理文件 {file_name} 的第 {idx}/{len(new_segments)} 个块")
            
            prompt = prompt_template.replace("{last_data}", last_data)
            prompt = prompt.replace("{new_text}", segment)
            
            response = call_llm(prompt, file_name)
            
            if response.get("success"):
                response_map_data = response.get("data")
                last_data = json.dumps(response_map_data, ensure_ascii=False, indent=2)
                logger.debug(f"第 {idx} 个块处理成功")
            else:
                logger.error(f"第 {idx} 个块处理失败: {response.get('error')}")
                # 如果处理失败，返回失败
                return {
                    "file": file_name,
                    "success": False,
                    "error": response.get('error'),
                    "path": str(file_path)
                }
        
        elapsed_time = time.time() - start_time
        
        # 保存结果到文件
        output_file = OUTPUT_DIR / f"{Path(file_path).stem}_extracted.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(last_data)
        
        logger.info(f"文件 {file_name} 处理完成，耗时: {elapsed_time:.2f}秒，结果保存到: {output_file}")
        
        # 更新成功统计
        with stats_lock:
            stats["success"] += 1
            logger.info(f"进度: {stats['success'] + stats['failed']}/{stats['total']} - 成功: {stats['success']}, 失败: {stats['failed']}")
        
        return {
            "file": file_name,
            "success": True,
            "data": last_data,
            "output_file": str(output_file),
            "time": elapsed_time,
            "path": str(file_path)
        }
        
    except Exception as e:
        logger.error(f"处理文件 {file_path} 时发生错误: {e}", exc_info=True)
        
        # 更新失败统计
        with stats_lock:
            stats["failed"] += 1
            logger.info(f"进度: {stats['success'] + stats['failed']}/{stats['total']} - 成功: {stats['success']}, 失败: {stats['failed']}")
        
        return {
            "file": file_name,
            "success": False,
            "error": str(e),
            "path": str(file_path)
        }

def process_files_multithread(files, max_workers=MAX_WORKERS):
    """多线程处理文件"""
    # 创建输出目录
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # 准备模板和默认数据
    prompt_template = get_prompt()
    default_data = GetDefaultTableData()
    
    # 更新统计信息
    with stats_lock:
        stats["total"] = len(files)
        stats["start_time"] = datetime.now()
    
    logger.info(f"开始处理 {len(files)} 个文件，使用 {max_workers} 个线程")
    
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_file = {
            executor.submit(process_single_file, file_path, prompt_template, default_data): file_path
            for file_path in files
        }
        
        # 处理完成的任务
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                results.append(result)
                
            except Exception as e:
                logger.error(f"处理文件 {file_path} 时发生异常: {e}", exc_info=True)
                results.append({
                    "file": Path(file_path).name,
                    "success": False,
                    "error": str(e),
                    "path": str(file_path)
                })
                with stats_lock:
                    stats["failed"] += 1
                    logger.info(f"进度: {stats['success'] + stats['failed']}/{stats['total']} - 成功: {stats['success']}, 失败: {stats['failed']}")
    
    with stats_lock:
        stats["end_time"] = datetime.now()
    
    return results

def save_summary_report(results):
    """保存处理总结报告"""
    summary_file = OUTPUT_DIR / f"processing_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    summary = {
        "statistics": {
            "total": stats["total"],
            "success": stats["success"],
            "failed": stats["failed"],
            "start_time": stats["start_time"].isoformat() if stats["start_time"] else None,
            "end_time": stats["end_time"].isoformat() if stats["end_time"] else None
        },
        "total_time": str(stats["end_time"] - stats["start_time"]) if stats["start_time"] and stats["end_time"] else "N/A",
        "success_files": [r for r in results if r["success"]],
        "failed_files": [{"file": r["file"], "error": r.get("error", "未知错误")} for r in results if not r["success"]]
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    logger.info(f"处理总结报告已保存到: {summary_file}")
    
    # 打印统计信息
    logger.info("="*60)
    logger.info("处理完成统计:")
    logger.info(f"总文件数: {stats['total']}")
    logger.info(f"成功: {stats['success']}")
    logger.info(f"失败: {stats['failed']}")
    logger.info(f"成功率: {stats['success']/stats['total']*100:.2f}%")
    logger.info(f"开始时间: {stats['start_time']}")
    logger.info(f"结束时间: {stats['end_time']}")
    logger.info(f"总耗时: {summary['total_time']}")
    logger.info("="*60)
    
    # 打印失败的文件
    if summary["failed_files"]:
        logger.warning("失败的文件列表:")
        for failed in summary["failed_files"]:
            logger.warning(f"  - {failed['file']}: {failed['error']}")

def test_single_file(file_path=None):
    """测试单个文件处理"""
    logger.info("="*60)
    logger.info("测试模式 - 处理单个文件")
    logger.info("="*60)
    
    try:
        # 如果没有指定文件，使用默认测试文件
        if file_path is None:
            file_path = 'E:\\github\\TAIDI_B\\processed\\财务报告\\reports-上交所\\600080_20230428_MMWM.md'
        
        logger.info(f"测试文件: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"测试文件不存在: {file_path}")
            return None
        
        # 准备模板和默认数据
        prompt_template = get_prompt() ## 缺两个参数
        default_data = GetDefaultTableData() ## 填充表格数据
        
        # 处理单个文件
        result = process_single_file(file_path, prompt_template, default_data)
        
        # 打印测试结果
        logger.info("="*60)
        logger.info("测试结果:")
        if result["success"]:
            logger.info(f"✅ 文件处理成功: {result['file']}")
            logger.info(f"📁 输出文件: {result['output_file']}")
            logger.info(f"⏱️  耗时: {result['time']:.2f}秒")
            logger.info(f"📊 数据长度: {len(result['data'])} 字符")
            
            # 可选：打印提取的数据摘要
            try:
                data_preview = json.loads(result['data'])
                logger.info(f"📋 数据摘要: {json.dumps(data_preview, ensure_ascii=False, indent=2)[:500]}...")
            except:
                pass
        else:
            logger.error(f"❌ 文件处理失败: {result['file']}")
            logger.error(f"错误信息: {result.get('error', '未知错误')}")
        
        logger.info("="*60)
        return result
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)
        return None

def test_with_custom_file():
    """使用自定义文件进行测试"""
    logger.info("="*60)
    logger.info("自定义文件测试")
    logger.info("="*60)
    
    # 可以在这里指定要测试的文件
    test_files = [
        'E:\\github\\TAIDI_B\\processed\\财务报告\\reports-上交所\\600080_20230428_MMWM.md',
        # 可以添加更多测试文件
        # 'E:\\github\\TAIDI_B\\processed\\财务报告\\reports-上交所\\600123_20230428_XXXX.md',
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            logger.info(f"\n测试文件: {os.path.basename(test_file)}")
            result = test_single_file(test_file)
            if result and result["success"]:
                logger.info(f"✅ {os.path.basename(test_file)} 测试通过")
            else:
                logger.error(f"❌ {os.path.basename(test_file)} 测试失败")
        else:
            logger.warning(f"测试文件不存在: {test_file}")

def main():
    """主函数 - 可选择运行模式"""
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "test":
            # 测试单个文件
            if len(sys.argv) > 2:
                # 使用指定的文件
                test_single_file(sys.argv[2])
            else:
                # 使用默认测试文件
                test_single_file()
        elif mode == "test-custom":
            # 测试自定义文件列表
            test_with_custom_file()
        elif mode == "batch":
            # 批量处理所有文件
            logger.info("批量处理模式")
            run_batch_processing()
        else:
            logger.error(f"未知模式: {mode}")
            print("使用方法:")
            print("  python script.py test           # 测试默认文件")
            print("  python script.py test <file>    # 测试指定文件")
            print("  python script.py test-custom    # 测试自定义文件列表")
            print("  python script.py batch          # 批量处理所有文件")
            print("  python script.py                # 默认批量处理")
    else:
        # 默认运行批量处理
        run_batch_processing()

def run_batch_processing():
    """批量处理所有文件"""
    logger.info("="*60)
    logger.info("批量处理模式启动")
    logger.info("="*60)
    
    try:
        # 获取所有markdown文件
        reports_path = Path.cwd().parent / "processed" / "财务报告"
        logger.info(f"扫描目录: {reports_path}")
        
        all_files = getAllMarkdownFiles(reports_path)
        logger.info(f"找到 {len(all_files)} 个markdown文件")
        
        if not all_files:
            logger.warning("没有找到markdown文件")
            return
        
        # 可以选择处理所有文件或只处理一部分进行测试
        # 处理所有文件
        files_to_process = all_files
        
        # 或者只处理前N个文件进行测试
        # test_count = 5
        # files_to_process = all_files[:test_count]
        # logger.info(f"测试模式：只处理前 {test_count} 个文件")
        
        logger.info(f"开始多线程处理，线程数: {MAX_WORKERS}")
        
        # 多线程处理
        results = process_files_multithread(files_to_process, max_workers=MAX_WORKERS)
        
        # 保存总结报告
        save_summary_report(results)
        
        logger.info("所有文件处理完成！")
        
    except Exception as e:
        logger.error(f"程序运行出错: {e}", exc_info=True)
    
    logger.info("="*60)
    logger.info("程序结束")
    logger.info("="*60)

# 快速测试函数 - 可以直接调用
def quick_test():
    """快速测试 - 直接运行这个函数来测试单个文件"""
    # 设置日志级别为DEBUG以获取更详细的信息
    logger.setLevel(logging.DEBUG)
    
    test_file = 'E:\\github\\TAIDI_B\\processed\\财务报告\\reports-上交所\\600080_20230428_MMWM.md'
    
    logger.info("快速测试开始")
    logger.info(f"测试文件: {test_file}")
    
    if not os.path.exists(test_file):
        logger.error(f"文件不存在: {test_file}")
        return
    
    try:
        # 准备模板和默认数据
        prompt_template = get_prompt()
        default_data = GetDefaultTableData()
        
        # 处理单个文件
        result = process_single_file(test_file, prompt_template, default_data)
        
        if result and result["success"]:
            logger.info("✅ 测试成功!")
            logger.info(f"输出文件: {result['output_file']}")
            
            # 验证输出文件
            with open(result['output_file'], 'r', encoding='utf-8') as f:
                output_data = json.load(f)
                logger.info(f"JSON验证成功，包含 {len(output_data)} 个顶级字段")
        else:
            logger.error("❌ 测试失败!")
            
    except Exception as e:
        logger.error(f"测试异常: {e}", exc_info=True)

def main():
    logger.info("="*60)
    logger.info("程序启动")
    logger.info("="*60)
    
    try:
        # 获取所有markdown文件
        reports_path = Path.cwd().parent / "processed" / "财务报告"
        logger.info(f"扫描目录: {reports_path}")
        
        all_files = getAllMarkdownFiles(reports_path)
        logger.info(f"找到 {len(all_files)} 个markdown文件")
        
        if not all_files:
            logger.warning("没有找到markdown文件")
            exit(0)
        
        # 可以选择处理所有文件或只处理一部分进行测试
        # 处理所有文件
        files_to_process = all_files
        
        # 或者只处理前N个文件进行测试
        # test_count = 5
        # files_to_process = all_files[:test_count]
        # logger.info(f"测试模式：只处理前 {test_count} 个文件")
        
        logger.info(f"开始多线程处理，线程数: {MAX_WORKERS}")
        
        # 多线程处理
        results = process_files_multithread(files_to_process, max_workers=MAX_WORKERS)
        
        # 保存总结报告
        save_summary_report(results)
        
        logger.info("所有文件处理完成！")
        
    except Exception as e:
        logger.error(f"程序运行出错: {e}", exc_info=True)
    
    logger.info("="*60)
    logger.info("程序结束")
    logger.info("="*60)
if __name__ == "__main__":
    quick_test()
    # main()