# 题目文件
***
docs\B题-上市公司财报“智能问数”助手.pdf
***

# 任务一：构建结构化财报数据库 
***
## 步骤1：PDF财报 → MD格式

**目标 :**将上市公司发布的PDF格式财报转换为Markdown格式<br>
**输入 :**PDF财报文件（如：金花股份_2024年报.pdf）<br>
**输出 :**MD格式文件（如：600080_20250425_P7ID.md）<br>
**方法:**
|方式|	工具	|说明|
|-------|---------|--------|
|在线转换|[MinerU官网](https://mineru.net/) |API调用|
|命令行	|	magic-pdf pdf-command --pdf "你的pdf路径" --method auto|解析单个文件|
|代码|	parallel.py|同时解析文件|

**文件命名规范：**

|公司|	格式|	示例|
|----|-----|-------|
|金花股份|{股票代码}\_{日期}\_{标识}.md|600080_20250425_P7ID.md|
|华润三九|{公司简称}：{年份}{报告期}.md|华润三九：2023年年度报告.md|


**报告期代码对照 :**
| 代码 | 含义 | 文件命名示例 |
| ---- | ---- | ---- |
| FY | 年报（全年） | 华润三九：2023年年度报告.md |
| Q1 | 一季度报告 | 华润三九：2023年一季度报告.md |
| HY | 半年度报告 | 华润三九：2023年半年度报告.md |
| Q3 | 三季度报告 | 华润三九：2023年三季度报告.md |
![数据入库](images\image.png)

![数据处理流程](images\d11339684dd1457ae425d035424a644.png)
## 📁 数据文件
| 文件 | 说明 |
|------|------|
| `data\raw\示例数据\附件2：财务报告` | 原始PDF文件 |
| `financial_data.db` | SQLite数据库文件 |
| `parsed_results` | PDF->Markdown的PDF数据解析存放地|
| `processed` | 对parsed_results的图片进行提取表格后的存放地|

## 📓 代码文件
| 文件 | 说明 | 数据流动 |
|------|------|--------|
| `01_财报解析探索.ipynb` | 测试第一问的代码 | 无 |
| `并行处理.py` | 使用MinerU镜像解析PDF（PDF→Markdown） |data\raw\示例数据\附件2：财务报告 -> parsed_results |
| `clearn_data.py` | 把图片数据转为表格（img->table)  | parsed_results-> processed|
| `create_table.py` | 创建四个表格数据 | 无 |
|  `Agent.py`| 从每个文件中获取四个表格数据 | processed-> financial_data.db|





***
task1/<br>
├── AllMd.py # 获取需要处理的全部财报数据的文件目录<br>
├── config.py # 配置文件<br>
├── extracted_all_data.py # 获取全部的财报（markdown格式）文件目录<br>
├── financial_schema.json # 股票代码和A股简称<br>
├── prompt-extract.md # Prompt提取数据<br>
├── logs/ # 日志目录<br>
└──
***

***


# 任务二：搭建“智能问数”助手 
***
task2/<br>
├── config.py                 # 配置文件<br>
├── llm_client.py             # 本地DeepSeek模型客户端<br>
├── database.py               # 数据库操作层<br>
├── prompts/                  # Prompt模板文件夹<br>
│   ├── __init__.py          # Prompt模块导出<br>
│   ├── intent_prompts.py    # 意图识别相关Prompt<br>
│   ├── sql_prompts.py       # SQL生成相关Prompt<br>
│   ├── entity_prompts.py    # 实体提取相关Prompt<br>
│   ├── analysis_prompts.py  # 分析结论生成Prompt<br>
│   └── conversation_prompts.py # 多轮对话相关Prompt<br>
├── intent_recognizer.py     # 意图识别器<br>
├── entity_extractor.py      # 实体提取器<br>
├── sql_generator.py         # SQL生成器<br>
├── conversation.py          # 多轮对话管理器<br>
├── chart_generator.py       # 图表生成器<br>
├── output_formatter.py      # 输出格式化器<br>
├── analysis_generator.py    # 分析结论生成器<br>
├── main.py                  # 主程序入口<br>
└── result/                  # 图表输出目录<br>

## DataBase
![](images\\20260410_86c948.png)



***





# 任务三：增强“智能问数”助手的可靠性
***
![](images\deepseek_mermaid_20260410_8ca174.png)
## RAG （财报数据 ， 研报数据（行业，个股））

## 知识图谱


## 网络搜索

***
# 建议的待办事项
