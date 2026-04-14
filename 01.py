import subprocess  # 用于运行外部命令行程序
import shutil      # 用于高级文件操作（移动、删除目录等）
import time        # 用于时间相关操作（计时、休眠）
import logging     # 用于记录运行日志
from pathlib import Path  # 面向对象的文件系统路径处理
from datetime import datetime  # 用于获取当前时间格式化日志文件名

# ===== 配置 =====
# 存放待处理PDF文件的根目录
PDF_ROOT = Path("/root/TAIDIBEI_B/data/raw/示例数据/附件2：财务报告")
# 解析结果（Markdown/JSON/图片）的输出根目录
OUTPUT_ROOT = Path("/root/TAIDIBEI_B/parsed_results")
# 存放运行日志的目录
LOG_DIR = Path("/root/TAIDIBEI_B/logs")
# ================

# 创建输出目录和日志目录（如果不存在则创建，存在则忽略错误）
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 配置日志系统
# 日志文件名包含当前时间戳，避免覆盖
log_file = LOG_DIR / f"processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,  # 记录INFO及以上级别的日志
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式：时间-级别-消息
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),  # 输出到文件，使用UTF-8编码
        logging.StreamHandler()  # 同时输出到控制台
    ]
)

def process_pdf(pdf_path):
    """
    处理单个PDF文件：调用magic-pdf命令解析，并将结果移动到指定目录
    
    参数:
        pdf_path (Path): PDF文件的路径对象
        
    返回:
        bool: 处理成功返回True，失败返回False
    """
    
    # 提取公司类型（PDF所在文件夹的名称）
    # 例如：/.../reports-上交所/xxx.pdf -> company = "reports-上交所"
    company = pdf_path.parent.name
    
    # 提取不带后缀的文件名（用于查找临时目录）
    pdf_name = pdf_path.stem
    
    # 创建针对该公司的目标目录结构
    target_dir = OUTPUT_ROOT / company          # 公司级别的输出目录
    images_dir = target_dir / "images"          # 存放图片的子目录

    # 确保目标目录存在（parents=True会创建所有必需的父目录）
    target_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"处理: {pdf_path.name}")       # 记录正在处理的PDF文件名
    logging.info(f"目标: {target_dir}")          # 记录目标输出路径
    
    # 构建要执行的magic-pdf命令
    # 参数说明：
    #   pdf-command : magic-pdf的子命令，用于处理PDF
    #   --pdf       : 指定输入的PDF文件路径
    #   --method    : 解析方法，auto表示自动选择
    cmd = ["magic-pdf", "pdf-command", "--pdf", str(pdf_path), "--method", "auto"]
    
    try:
        # 执行命令，捕获标准输出和标准错误，设置超时时间为1800秒（30分钟）
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        
        if result.returncode == 0:  # 返回码0表示命令执行成功
            # magic-pdf默认的输出临时目录结构
            # 格式：/tmp/magic-pdf/{pdf文件名不带后缀}/auto
            tmp_dir = Path(f"/tmp/magic-pdf/{pdf_name}/auto")
            
            if tmp_dir.exists():  # 检查临时目录是否存在
                # 1. 移动Markdown文件
                md_files = list(tmp_dir.glob("*.md"))  # 查找所有.md文件
                for md in md_files:
                    shutil.move(str(md), str(target_dir / md.name))  # 移动到目标目录
                    logging.info(f"  📄 移动: {md.name}")
                
                # 2. 移动JSON文件
                json_files = list(tmp_dir.glob("*.json"))  # 查找所有.json文件
                for json in json_files:
                    shutil.move(str(json), str(target_dir / json.name))
                    logging.info(f"  📊 移动: {json.name}")
                
                # 3. 移动图片文件
                img_dir = tmp_dir / "images"  # 图片所在的子目录
                if img_dir.exists():
                    jpg_count = 0 
                    for img in img_dir.glob("*.jpg"):  # 查找所有.jpg文件
                        shutil.move(str(img), str(images_dir / img.name))
                        jpg_count += 1
                    logging.info(f"  🖼️  移动图片: {jpg_count}张")
                    img_dir.rmdir()  # 尝试删除空的图片目录（如果还有其他文件则不会删除）
                
                # 4. 清理整个临时目录树
                # tmp_dir.parent 是 /tmp/magic-pdf/{pdf_name}
                if tmp_dir.parent.exists():
                    shutil.rmtree(tmp_dir.parent)  # 递归删除整个临时目录
                    logging.info(f"  🗑️ 清理临时目录: {tmp_dir.parent}")
                
                logging.info(f"  ✅ 完成: {pdf_name}")
                return True
            else:
                # 临时目录不存在，可能是magic-pdf执行异常或输出位置变更
                logging.warning(f"  ⚠️ 未找到临时目录: {tmp_dir}")
                return False
        else:
            # 命令执行失败
            logging.error(f"  ❌ 处理失败: {pdf_path.name}")
            if result.stderr:
                logging.error(f"     错误: {result.stderr[:200]}")  # 只显示前200字符避免日志过长
            return False
            
    except subprocess.TimeoutExpired:
        # 命令执行超过30分钟
        logging.error(f"  ⏰ 超时: {pdf_path.name}")
        return False
    except Exception as e:
        # 其他未预期的异常（如文件权限、磁盘空间等）
        logging.error(f"  💥 异常: {pdf_path.name}, {str(e)}")
        return False

def main():
    """主函数：遍历所有PDF文件并依次处理，输出统计信息"""
    
    # 递归查找PDF_ROOT下所有后缀为.pdf的文件
    all_pdfs = list(PDF_ROOT.rglob("*.pdf"))
    
    # 记录开始处理的信息
    logging.info(f"="*60)  # 打印分隔线
    logging.info(f"🚀 开始处理，共 {len(all_pdfs)} 个PDF文件")
    logging.info(f"📁 输出目录: {OUTPUT_ROOT}")
    logging.info(f"📄 日志文件: {log_file}")
    logging.info(f"="*60)
    
    success = 0  # 成功计数
    failed = 0   # 失败计数
    start_time = time.time()  # 记录开始时间，用于计算总耗时
    
    # 枚举所有PDF文件，i从1开始编号便于显示进度
    for i, pdf in enumerate(all_pdfs, 1):
        logging.info(f"\n[{i}/{len(all_pdfs)}] 进度: {i/len(all_pdfs)*100:.1f}%")
        
        # 处理当前PDF，根据返回值更新计数
        if process_pdf(pdf):
            success += 1
        else:
            failed += 1
        
        # 每处理5个文件后短暂休息3秒，避免CPU/IO过载
        if i % 5 == 0 and i < len(all_pdfs):
            logging.info(f"⏸️  已处理 {i} 个，休息3秒...")
            time.sleep(3)
    
    # 计算总耗时（秒），并转换为时:分:秒格式
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)        # 小时数
    minutes = int((elapsed % 3600) // 60)  # 分钟数
    seconds = int(elapsed % 60)         # 秒数
    
    # 输出最终统计信息
    logging.info("\n" + "="*60)
    logging.info(f"✅ 全部处理完成！")
    logging.info(f"📊 统计:")
    logging.info(f"   总文件: {len(all_pdfs)}")
    logging.info(f"   成功: {success}")
    logging.info(f"   失败: {failed}")
    logging.info(f"   用时: {hours}小时{minutes}分钟{seconds}秒")
    logging.info(f"📁 结果目录: {OUTPUT_ROOT}")
    logging.info(f"📄 日志文件: {log_file}")
    logging.info("="*60)

# 程序入口：只有直接运行此脚本时才执行main()，被导入时不执行
if __name__ == "__main__":
    main()