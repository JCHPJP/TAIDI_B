son
# from pathlib import Path
# from config import Config

# # 创建测试文件
# def create_test_files():
#     # 创建目录
#     report_dir = Path("./test_data/processed/附件2：财务报告")
#     json_dir = Path("./test_data/task1/output")
#     report_dir.mkdir(parents=True, exist_ok=True)
#     json_dir.mkdir(parents=True, exist_ok=True)
    
#     # 创建测试财报
#     report_content = """# 公司概况

# 测试公司股份有限公司是一家高科技企业，主要从事人工智能和大数据技术研发。

# # 财务数据

# 2023年公司实现营业收入10.5亿元，同比增长25.3%。净利润2.1亿元，同比增长18.7%。

# # 业务板块

# 公司主营业务包括：AI平台服务、数据分析服务、云计算服务三大板块。
# """
    
#     report_file = report_dir / "test_report.md"
#     report_file.write_text(report_content, encoding='utf-8')
#     print(f"✅ 创建测试文件: {report_file}")
    
#     # 创建测试JSON
#     json_content = {
#         "报告信息": {
#             "股票代码": "000001",
#             "股票简称": "测试公司",
#             "报告年份": "2023",
#             "报告期": "年度报告"
#         }
#     }
    
#     json_file = json_dir / "test_report.json"
#     json_file.write_text(json.dumps(json_content, ensure_ascii=False, indent=2), encoding='utf-8')
#     print(f"✅ 创建测试文件: {json_file}")
    
#     return report_file, json_file

# # 运行测试
# if __name__ == "__main__":
#     create_test_files()
#     print("\n