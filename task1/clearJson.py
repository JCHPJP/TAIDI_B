from pathlib import Path
import json 
import akshare as ak
from config import  Config
import openai
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from pathlib import Path
import json
import re

from config import Config

# 线程锁
print_lock = Lock()
with open( Path(__file__).parent.parent / 'infors' / 'code2name.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
code2name = data
name2code = {v: k for k, v in code2name.items()}
def updateinfors():
    # 1. 获取数据
    full_list = ak.stock_info_a_code_name()
    code2name = dict(zip(full_list['code'], full_list['name']))

    # 2. 保存到文件（注意是 'w' 模式）
    file_path = Path.cwd().parent / 'infors' / 'code2name.json'
    # 确保目录存在
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(code2name, f, ensure_ascii=False, indent=2)

    print(f"已保存 {len(code2name)} 只股票到 {file_path}")
def getNameCode(file_name):
    if  '：' in file_name:
        return {"股票代码": name2code.get(file_name.split('：')[0].replace(" ", ""), "未知"),"股票简称": file_name.split('：')[0].replace(" ", "")}
    else:
         
        return {"股票简称": code2name.get(file_name.split('_')[0].replace(" ", ""), "未知"),"股票代码": file_name.split('_')[0].replace(" ", "")}


def clear_json(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 这里可以根据需要清洗数据，例如去除某些字段，或者修改某些值
    # 下面是一个示例，假设我们要去除所有的 "metadata" 字段
    data['报告信息']['股票代码'] = getNameCode(json_path.stem)['股票代码']
    data['报告信息']['股票简称'] = getNameCode(json_path.stem)['股票简称']
    
    print(data['报告信息'] , json_path.stem , getNameCode(json_path.stem))
    # 将清洗后的数据写回文件
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
def one():
    folds = Path(__file__).parent / 'output' 
    json_files = list(Path(folds).glob('*.json'))
    mp = {}
    for json_file in json_files:
        clear_json(json_file)

    




# 配置API
client = openai.OpenAI(
    api_key=Config.DeepSeek.API_KEY,
    base_url=Config.DeepSeek.BASE_URL
)

def get_report_period(filepath: str) -> str:
    """
    判断单个文件的报告期
    返回: Q1, HY, Q3, FY, UNKNOWN
    """
    filepath = Path(filepath)
    filename = filepath.stem
    with open(str(filepath) , encoding='utf-8') as f:
        data = f.read()[:3000]
    prompt = f"""
文件名: {filename}
文件的前3000个字符{data}
规则:
判断数据对应的会计期间。其中，FY=年报（FullYear），Q1=一季度，HY=半年度，Q3=三季度。
只返回Q1, HY, Q3, FY。
只返回JSON: {{"period": "Q1"}}
"""
    
    try:
        response = client.chat.completions.create(
            model=Config.DeepSeek.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=50
        )
        result = response.choices[0].message.content.strip()
        
        # 方法1: 尝试提取JSON
        match = re.search(r'\{[^}]*\}', result)
        if match:
            d = json.loads(match.group())
            d['name'] = filename
            with print_lock:
                print(f"{d.get('period')} -> {filename}")
            return d 
        return {"period": "UNKNOWN","name":filename}
    except:
        return {"period": "UNKNOWN" , 'name':filename}

def get_report_year(filepath: str):
    """
    判断单个文件的报告期
    返回: Q1, HY, Q3, FY, UNKNOWN
    """
    filepath = Path(filepath)
    filename = filepath.stem
    with open(str(filepath) , encoding='utf-8') as f:
        data = f.read()[:3000]
    prompt = f"""
通过规则reports-上交所：上海证券交易所挂牌交易的上市公司财报数据。财务报告命名规则
为【股票代码_报告日期_随机标识.pdf】。 reports-深交所：深圳证券交易所挂牌交易的上市公司财报数据。财务报告命名规则
为【A 股简称：年份+报告周期+报告类型（报告/报告摘要）.pdf】。
直接返回年份，json格式
只返回JSON: {{"period": "2024"}}
"""
    
    try:
        response = client.chat.completions.create(
            model=Config.DeepSeek.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=50
        )
        result = response.choices[0].message.content.strip()
        
        # 方法1: 尝试提取JSON
        match = re.search(r'\{[^}]*\}', result)
        if match:
            d = json.loads(match.group())
            d['name'] = filename
            with print_lock:
                print(f"{d.get('period')} -> {filename}")
            return d 
        return {"period": "UNKNOWN","name":filename}
    except:
        return {"period": "UNKNOWN" , 'name':filename}

def two():
    reports1 = Path.cwd().parent / 'processed' / '财务报告' / 'reports-上交所'
    reports2 = Path.cwd().parent / 'processed' / '财务报告' / 'reports-深交所'
    
    r1 = [str(i) for i in reports1.glob('*.md')]
    r2 = [str(i) for i in reports2.glob('*.md')]
    all_files = r1 + r2
    
    print(f"共 {len(all_files)} 个文件\n")
    
    results = []
    
    # 多线程处理
    with ThreadPoolExecutor(max_workers=200) as executor:
        futures = {executor.submit(get_report_period, f): f for f in all_files}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"错误: {e}")
    
    # 保存结果
    with open('period_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 统计
    stats = {}
    for r in results:
        p = r.get('period', 'UNKNOWN')
        stats[p] = stats.get(p, 0) + 1
    
    print(f"\n统计: {stats}")

def get_report_year(filename: str):
    """AI从文件名提取年份"""
    prompt = f"""
文件名: {filename}

任务: 从文件名中提取财报的报告年份

规则:
- 上交所格式包含 8位日期数字，如 20241231 → 年份是 2024
- 深交所格式包含 "2024年" → 年份是 2024

只返回JSON: {{"year": "2024"}}
"""
    
    try:
        response = client.chat.completions.create(
            model=Config.DeepSeek.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=50
        )
        result = response.choices[0].message.content.strip()
        match = re.search(r'\{[^}]*\}', result)
        if match:
            d = json.loads(match.group())
            d['name'] = filename
            return d
        return "UNKNOWN"
    except:
        return "UNKNOWN"


def main():
    with open('period_results.json', 'r', encoding='utf-8') as f:
        d = json.load(f)
    
    for i in d :
        with open(Path().cwd() / 'output'/(i['name']+'.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['报告信息']['报告期'] = i['period']
        data['报告信息'].pop('期', None)
        print(data['报告信息'])
        with open( Path().cwd() / 'output'/(i['name']+'.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    

if __name__ == "__main__":
    # updateinfors()
    # from collections import defaultdict
    # d1 = defaultdict(int)
    # folds = Path(__file__).parent / 'output' 
    # json_files = list(Path(folds).glob('*.json'))
    # total = 0 
    # for i in json_files:
    #     with open(i, 'r', encoding='utf-8') as f:
    #         data = json.load(f)
    #         d1[data['报告信息']['报告年份']] +=1
    #         total += 1 
    # print(d1 , total )
    main()

    # results = []
    # with ThreadPoolExecutor(max_workers=200) as executor:
    #     futures = {executor.submit(get_report_year, f.stem): f for f in json_files}
        
    #     for future in as_completed(futures):
    #         try:
    #             result = future.result()
    #             print(result)
    #             results.append(result)
    #         except Exception as e:
    #             print(f"错误: {e}")
    # with open('period_year_results.json', 'w', encoding='utf-8') as f:
    #     data = json.dump(results, f, ensure_ascii=False, indent=2)
    
    # from collections import defaultdict
    # mp = defaultdict(int)
    # with open('period_year_results.json',encoding='utf-8') as f :
    #     data = json.load(f)

    # for i in data:
    #     with open(Path().cwd() / 'output'/(i['name']+'.json'), 'r', encoding='utf-8') as f:
    #         data = json.load(f)
    #     data['报告信息']['报告年份'] = i['year']
    #     print(data['报告信息'])
    #     with open( Path().cwd() / 'output'/(i['name']+'.json'), 'w', encoding='utf-8') as f:
    #         json.dump(data, f, ensure_ascii=False, indent=4)

    

    

