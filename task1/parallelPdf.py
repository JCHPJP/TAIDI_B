import os
import subprocess
import shutil
import logging
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
import threading

# ===== 设置环境变量 =====
cpu_cores = cpu_count()
omp_threads = min(2, cpu_cores)
os.environ['OMP_NUM_THREADS'] = str(omp_threads)
os.environ['MKL_NUM_THREADS'] = str(omp_threads)
os.environ['OPENBLAS_NUM_THREADS'] = str(omp_threads)
os.environ['VECLIB_MAXIMUM_THREADS'] = str(omp_threads)

# ===================== 【全局变量：全部放在这里】 =====================
PDF_ROOT = None
OUTPUT_ROOT = None
LOG_DIR = None
log_file = None
file_lock = None
# ======================================================================

MAX_WORKERS = 3

# ===================== 【核心：切换目录 + 重新初始化日志 + 锁】 =====================
def set_new_dir(new_folder_name):
    """
    切换目录，并自动重新生成日志、锁
    你要做的只有：set_new_dir("附件3：行业研报")
    """
    global PDF_ROOT, OUTPUT_ROOT, LOG_DIR, log_file, file_lock

    # 1. 切换路径
    PDF_ROOT = Path.cwd().parent / "data" / "正式数据" / new_folder_name
      # 只保留冒号后面的部分作为输出目录名
    OUTPUT_ROOT = Path.cwd().parent / "parsed_results"/ new_folder_name.split("：")[-1]
    LOG_DIR = Path.cwd().parent / "logs"

    # 2. 创建目录
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 3. 新日志文件名（每次切换都新生成！）
    log_file = LOG_DIR / f"processing_{new_folder_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # 4. 重置日志配置
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [%(threadName)s] - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # 5. 新锁（每次目录切换都是新的）
    file_lock = threading.Lock()

    logging.info(f"✅ 已切换到新目录：{new_folder_name}")
    logging.info(f"📁 源目录：{PDF_ROOT}")
    logging.info(f"📁 输出目录：{OUTPUT_ROOT}")
    logging.info(f"📄 新日志：{log_file.name}")
# ==================================================================================

def safe_log(level, message):
    with file_lock:
        getattr(logging, level)(message)

def process_pdf(pdf_path):
    thread_name = threading.current_thread().name
    try:
        company = pdf_path.parent.name
        pdf_name = pdf_path.stem

        target_dir = OUTPUT_ROOT / company
        images_dir = target_dir / "images"

        with file_lock:
            target_dir.mkdir(parents=True, exist_ok=True)
            images_dir.mkdir(parents=True, exist_ok=True)

        safe_log('info', f"[{thread_name}] 处理: {pdf_path.name}")

        env = os.environ.copy()
        env['OMP_NUM_THREADS'] = '1'
        env['MKL_NUM_THREADS'] = '1'
        env['OPENBLAS_NUM_THREADS'] = '1'

        cmd = ["magic-pdf", "pdf-command", "--pdf", str(pdf_path), "--method", "auto"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, env=env)

        if result.returncode == 0:
            tmp_dir = Path(f"/tmp/magic-pdf/{pdf_name}/auto")
            if tmp_dir.exists():
                for md in tmp_dir.glob("*.md"):
                    with file_lock:
                        shutil.move(str(md), target_dir / md.name)
                    safe_log('info', f"[{thread_name}]   📄 移动: {md.name}")

                for json in tmp_dir.glob("*.json"):
                    with file_lock:
                        shutil.move(str(json), target_dir / json.name)
                    safe_log('info', f"[{thread_name}]   📊 移动: {json.name}")

                img_dir = tmp_dir / "images"
                if img_dir.exists():
                    jpg_count = 0
                    for img in img_dir.glob("*.jpg"):
                        with file_lock:
                            shutil.move(str(img), images_dir / img.name)
                        jpg_count += 1
                    safe_log('info', f"[{thread_name}]   🖼️  移动图片: {jpg_count}张")

                with file_lock:
                    if tmp_dir.parent.exists():
                        try:
                            shutil.rmtree(tmp_dir.parent)
                        except OSError:
                            pass

                safe_log('info', f"[{thread_name}]   ✅ 完成: {pdf_name}")
                return True, pdf_path.name
            else:
                safe_log('warning', f"[{thread_name}]   ⚠️ 未找到临时目录")
                return False, pdf_path.name
        else:
            safe_log('error', f"[{thread_name}]   ❌ 处理失败")
            return False, pdf_path.name

    except Exception as e:
        safe_log('error', f"[{thread_name}]   💥 异常: {str(e)}")
        return False, pdf_path.name

def main():
    all_pdfs = list(PDF_ROOT.rglob("*.pdf"))
    total = len(all_pdfs)
    if total == 0:
        logging.warning(f"未找到PDF：{PDF_ROOT}")
        return

    logging.info("=" * 60)
    logging.info(f"🚀 开始处理，共 {total} 个文件")
    logging.info("=" * 60)
    success = 0
    failed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_pdf = {executor.submit(process_pdf, pdf): pdf for pdf in all_pdfs}

        for i, future in enumerate(as_completed(future_to_pdf), 1):
            ok, name = future.result()
            success += ok
            failed += not ok

            if i % 5 == 0 or i == total:
                logging.info(f"进度：{i}/{total} | 成功：{success} | 失败：{failed}")

    elapsed = time.time() - start_time
    logging.info("\n✅ 处理完成！")
    logging.info(f"总文件：{total} | 成功：{success} | 失败：{failed}")
    logging.info(f"输出目录：{OUTPUT_ROOT}")

# ------------------------------------------------------------------------------
# 【使用方法】
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # 1. 处理附件2
    set_new_dir("附件2：财务报告")
    main()

    # 2. 处理完自动切换 → 附件5
    set_new_dir("附件5：研报数据")
    main()
