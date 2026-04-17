from db_helper import DatabaseHelper
from pathlib import Path
import json
path_file = Path(__file__).parent.parent / 'db' / 'financial_data.db'
db = DatabaseHelper(path_file)

def getTwoyear(stock_code,period,current_year):
    sql = f"""
        SELECT 
            *
        FROM core_performance_indicators_sheet
        WHERE stock_code = '{stock_code}'
        AND report_period = '{period}'
        AND report_year IN ({current_year}, {current_year - 1})
        ORDER BY report_year DESC
    """
    return db.query(sql) 

def singel(file_name):
    with open(file_name , encoding='utf-8') as f :
        data = json.load(f)
    stock_code  =data['报告信息']['股票代码']
    period = data['报告信息']['报告期']
    current_year = data['报告信息']['报告年份']
    two_year_data = getTwoyear(stock_code=stock_code,period=period, current_year=current_year)



def main():
    pass 

    
    

    
if __name__ ==   "__main__":
    main()