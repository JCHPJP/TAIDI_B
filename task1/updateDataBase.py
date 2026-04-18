import logging
from datetime import datetime
from pathlib import Path 
from config import Config 
from openai import OpenAI 
import json 
from db_helper import DatabaseHelper
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 初始化数据库
path_file = Path(__file__).parent.parent / 'db' / 'financial_data.db'
db = DatabaseHelper(path_file)

SCHEMA_FILE = Path(__file__).parent / "table_information.md"

def get_schema() -> str:
    """读取数据库表结构"""
    if SCHEMA_FILE.exists():
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        print(f"警告: 表结构文件不存在 {SCHEMA_FILE}")
        return ""

client = OpenAI(
    api_key=Config.DeepSeek.API_KEY,
    base_url=Config.DeepSeek.BASE_URL
)

# 配置日志
def setup_logging(log_path: str = None):
    """配置日志系统 - 按天保存"""
    if log_path is None:
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        log_path = log_dir / f"process_log_{datetime.now().strftime('%Y%m%d')}.log"
    else:
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()


# ============ 功能1：获取历史数据 ============
def get_historical_data(stock_code: str, current_year: int):
    """获取当期和去年的数据"""
    logger.info(f"开始获取历史数据: 股票={stock_code}, 年份={current_year}")
    
    tables = ['core_performance_indicators_sheet', 'balance_sheet', 'income_sheet', 'cash_flow_sheet']
    result = {}
    
    for table in tables:
        try:
            sql = f"""
                SELECT * FROM {table}
                WHERE stock_code = '{stock_code}'
                AND report_year IN ({current_year}, {current_year - 1})
            """
            data = db.query(sql)
            
            if data:
                result[table] = {
                    'current': next((d for d in data if d['report_year'] == current_year), None),
                    'last': next((d for d in data if d['report_year'] == current_year - 1), None)
                }
                logger.info(f"✓ {table} 数据获取成功")
            else:
                result[table] = {'current': None, 'last': None}
                logger.info(f"⚠ {table} 无历史数据")
        except Exception as e:
            logger.error(f"✗ 查询{table}失败: {e}")
            result[table] = {'current': None, 'last': None}
    
    return result


# ============ 功能2：大模型补全缺失值 ============
def fill_missing_values(data: dict) -> dict:
    """使用大模型补全null字段"""
    logger.info("开始使用大模型补全缺失值")
    
    # 检查是否有null字段
    has_null = False
    def check_null(obj):
        nonlocal has_null
        if isinstance(obj, dict):
            for v in obj.values():
                if v is None:
                    has_null = True
                    return
                check_null(v)
        elif isinstance(obj, list):
            for item in obj:
                check_null(item)
    check_null(data)
    
    if not has_null:
        logger.info("没有null字段，跳过补全")
        return data
    
    try:
        prompt = f"""
        补全以下JSON中的null字段。
        
        计算公式：
        - 销售毛利率 = (营业收入-营业成本)/营业收入*100
        - 销售净利率 = 净利润/营业收入*100
        - 总资产收益率(ROA) = 净利润/总资产*100
        - 营业利润率 = 营业利润/营业收入*100
        - 期间费用率 = (销售费用+管理费用+研发费用+财务费用)/营业收入*100
        - 扣非净资产收益率 = 扣非净利润/归属于母公司所有者权益*100
        
        数据：{json.dumps(data, ensure_ascii=False, indent=2)}
        
        要求：
        1. 只将null改为计算值，保留2位小数
        2. 无法计算保持null
        3. 直接返回完整JSON，不要有其他文字
        """
        
        response = client.chat.completions.create(
            model=Config.DeepSeek.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        
        text = response.choices[0].message.content
        
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]
        
        result = json.loads(text)
        logger.info("✓ 缺失值补全完成")
        return result
        
    except Exception as e:
        logger.error(f"✗ 大模型补全失败: {e}")
        return data


# ============ 功能3：生成四个表的SQL ============
def generate_all_sql(filled_data: dict, stock_code: str, year: int, period: str) -> dict:
    """为四个表分别生成SQL语句"""
    
    schema = get_schema()
    
    # 获取历史数据
    historical_data = filled_data.get('historical_data', {})
    
    table_map = {
        '核心业绩指标': 'core_performance_indicators_sheet',
        '资产负债表': 'balance_sheet',
        '利润表': 'income_sheet',
        '现金流量表': 'cash_flow_sheet'
    }
    
    all_sql = {}
    
    for json_key, table_name in table_map.items():
        table_data = filled_data.get(json_key, {})
        
        if not table_data:
            logger.warning(f"⚠ {json_key} 数据为空，跳过")
            continue
        
        # 获取历史数据
        history = historical_data.get(table_name, {})
        current_history = history.get('current', {})
        last_history = history.get('last', {})
        
        try:
            prompt = f"""
            根据以下数据库表结构，将JSON数据生成SQLite的REPLACE INTO语句。
            
            ## 数据库表结构（字段名必须严格匹配）：
            {schema}
            
            ## 目标表名：{table_name}
            
            ## 当期JSON数据（需要插入的数据）：
            {json.dumps(table_data, ensure_ascii=False, indent=2)}
            
            ## 数据库中已有的数据（仅供参考，用于计算同比）：
            ### 今年已存在的数据：
            {json.dumps(current_history, ensure_ascii=False, indent=2) if current_history else '无'}
            
            ### 去年已存在的数据：
            {json.dumps(last_history, ensure_ascii=False, indent=2) if last_history else '无'}
            
            ## 公共字段（必须添加）：
            - stock_code: '{stock_code}'
            - report_year: {year}
            - report_period: '{period}'
            -
            
            ## 要求：
            1. 不要包含 serial_number 字段（自增主键）
            2. 字段名必须使用数据库表中的英文字段名
            3. 只插入数据库表中存在的字段
            4. 过滤掉值为null的字段
            5. 如果JSON中的null可以从历史数据或计算得出，请补全
            6. 金额单位统一为万元
            7. 只返回SQL语句，不要其他文字
            
            只返回SQL语句，不要其他文字。
            """
            
            response = client.chat.completions.create(
                model=Config.DeepSeek.MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            sql = response.choices[0].message.content.strip()
            if '```sql' in sql:
                sql = sql.split('```sql')[1].split('```')[0]
            elif '```' in sql:
                sql = sql.split('```')[1].split('```')[0]
            
            all_sql[table_name] = sql
            logger.info(f"✓ {table_name} SQL生成完成")
            
        except Exception as e:
            logger.error(f"✗ {table_name} SQL生成失败: {e}")
            all_sql[table_name] = f"-- 生成失败: {str(e)}"
    
    return all_sql


# ============ 保存SQL到文件 ============
def save_sql_to_file(sql_path: Path, stock_code: str, year: int, period: str, all_sql: dict):
    """将生成的SQL保存到文件"""
    try:
        with open(sql_path, 'w', encoding='utf-8') as f:
            f.write(f"-- 股票代码: {stock_code}\n")
            f.write(f"-- 报告年份: {year}年\n")
            f.write(f"-- 报告期: {period}\n")
            f.write(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-- " + "="*60 + "\n\n")
            
            for table_name, sql in all_sql.items():
                if sql and not sql.startswith("-- 生成失败"):
                    f.write(f"-- 表名: {table_name}\n")
                    f.write(sql)
                    if not sql.rstrip().endswith(';'):
                        f.write(';')
                    f.write("\n\n" + "--"*60 + "\n\n")
        
        logger.info(f"✓ SQL文件已保存: {sql_path}")
    except Exception as e:
        logger.error(f"✗ 保存SQL文件失败: {e}")


# ============ 执行SQL ============
def execute_sql(sql: str) -> tuple:
    """执行单条SQL语句"""
    try:
        # 分割多条SQL
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        
        for statement in statements:
            if statement:
                logger.debug(f"执行: {statement[:100]}...")
                db.execute(statement)
        
        return True, None
    except Exception as e:
        return False, str(e)


# ============ 处理单个文件 ============
def process_one_file(file_path: str) -> tuple:
    """处理单个文件（供多线程调用）"""
    try:
        logger.info(f"开始处理: {file_path}")
        
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 获取基本信息
        info = data.get('报告信息', {})
        stock_code = info.get('股票代码')
        year_str = info.get('报告年份')
        period = info.get('报告期')
        
        # 转换年份
        try:
            year = int(year_str) if year_str else None
        except:
            year = None
        
        if not all([stock_code, year, period]):
            logger.warning(f"跳过 {file_path}: 缺少必要字段")
            return file_path, False, "缺少必要字段"
        
        logger.info(f"股票代码: {stock_code}, 年份: {year}, 报告期: {period}")
        
        # 获取历史数据
        history = get_historical_data(stock_code, year)
        data['historical_data'] = history
        
        # 补全缺失值
        filled_data = fill_missing_values(data)
        
        # 保存补全后的文件
        output_dir = Path('filled')
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{Path(file_path).stem}_filled.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filled_data, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ 已保存: {output_path}")
        
        # 生成SQL
        all_sql = generate_all_sql(filled_data, stock_code, year, period)
        
        # 保存SQL到文件
        sql_path = output_dir / f"{Path(file_path).stem}_insert.sql"
        save_sql_to_file(sql_path, stock_code, year, period, all_sql)
        
        # 执行SQL
        logger.info("开始执行SQL...")
        success_count = 0
        fail_count = 0
        
        for table_name, sql in all_sql.items():
            if sql and not sql.startswith("-- 生成失败"):
                success, error = execute_sql(sql)
                if success:
                    success_count += 1
                    logger.info(f"✓ 执行成功: {table_name}")
                else:
                    fail_count += 1
                    logger.error(f"✗ 执行失败: {table_name}, 错误: {error}")
        
        logger.info(f"SQL执行完成: 成功 {success_count}, 失败 {fail_count}")
        logger.info(f"✓ 完成: {file_path}")
        
        return file_path, True, f"成功 (SQL: {success_count}/{success_count+fail_count})"
        
    except Exception as e:
        logger.error(f"✗ 失败: {file_path}, 错误: {e}")
        return file_path, False, str(e)


# ============ 多线程批量处理 ============
def batch_process(file_list: list, max_workers: int = 3):
    """批量处理多个文件"""
    print(f"\n{'='*60}")
    print(f"开始批量处理 {len(file_list)} 个文件，并发数: {max_workers}")
    print(f"{'='*60}\n")
    
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_one_file, f): f for f in file_list}
        
        for i, future in enumerate(as_completed(futures), 1):
            file_path, success, message = future.result()
            results.append((file_path, success, message))
            print(f"进度: {i}/{len(file_list)} - {'✓' if success else '✗'} {Path(file_path).name}")
    
    success_count = sum(1 for _, s, _ in results if s)
    print(f"\n{'='*60}")
    print(f"批量处理完成: 成功 {success_count}/{len(results)}")
    print(f"{'='*60}")
    
    # 打印失败的文件
    failed = [(p, m) for p, s, m in results if not s]
    if failed:
        print("\n失败的文件:")
        for f, m in failed:
            print(f"  - {Path(f).name}: {m}")
    
    return results


# ============ 测试单个文件 ============
def test_single_file(file_path: str):
    """测试单个文件"""
    print(f"\n{'='*60}")
    print(f"测试模式: 处理单个文件")
    print(f"{'='*60}\n")
    
    result, success, message = process_one_file(file_path)
    
    if success:
        print(f"\n✓ 测试成功: {result}")
        print(f"  结果: {message}")
    else:
        print(f"\n✗ 测试失败: {message}")
    
    return result, success, message


# ============ 检查数据库数据 ============
def check_db_data():
    """检查数据库中的数据"""
    print("\n" + "="*60)
    print("数据库当前数据统计")
    print("="*60)
    
    tables = ['core_performance_indicators_sheet', 'balance_sheet', 'income_sheet', 'cash_flow_sheet']
    
    for table in tables:
        try:
            sql = f"SELECT COUNT(*) as count FROM {table}"
            result = db.query(sql)
            count = result[0]['count'] if result else 0
            print(f"{table}: {count} 条记录")
            
            # 显示前几条股票代码
            if count > 0:
                sql = f"SELECT DISTINCT stock_code, report_year FROM {table} LIMIT 5"
                samples = db.query(sql)
                codes = [f"{s['stock_code']}({s['report_year']})" for s in samples]
                print(f"  示例: {', '.join(codes)}")
        except Exception as e:
            print(f"{table}: 查询失败 - {e}")
    
    print("="*60)


# ============ 主函数 ============
if __name__ == "__main__":
    # 设置日志
    log_file = Path(__file__).parent / 'logs' / f"run_log_{datetime.now().strftime('%Y%m%d')}.log"
    logger = setup_logging(log_file)
    
    # 先检查数据库当前数据
    check_db_data()
    
    # ========== 选择模式 ==========
    
    # 模式1：测试单个文件
    # test_file = "output/以岭药业：2025年半年度报告.json"
    # if Path(test_file).exists():
    #     print("\n【模式1】测试单个文件")
    #     result, success, message = test_single_file(test_file)
    # else:
    #     print(f"测试文件不存在: {test_file}")
    #     print("请修改 test_file 路径")
    
    # ========== 模式2：多线程批量处理（取消注释启用） ==========
    
    # json_files = list(Path("output").glob("*.json"))
    # json_files = [f for f in json_files if not f.stem.endswith('_filled')]
    # 
    # if json_files:
    #     print(f"\n【模式2】多线程批量处理")
    #     print(f"找到 {len(json_files)} 个文件待处理")
    #     results = batch_process(json_files, max_workers=3)
    # else:
    #     print("没有找到待处理的文件")
    
    print(f"\n日志文件: {log_file}")
    print(f"输出目录: filled/")
    
    # 再次检查数据库数据
    check_db_data()
    db.close()