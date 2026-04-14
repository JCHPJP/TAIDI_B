# 数据库表结构说明
## 一、数据库表名（共5张表）
| 中文名称 | 英文名称 |
|----------|-----------|
| 业绩指标表 | `core_performance_indicators_sheet` |
| 资产负债表 | `balance_sheet` |
| 利润表 | `income_sheet` |
| 现金流量表 | `cash_flow_sheet` |
---
## 二、核心业绩指标表（`core_performance_indicators_sheet`）
| 字段名称 | 中文名称 | 字段类型 | 字段说明 |
|----------|----------|----------|----------|
| serial_number | 序号 | int | 数据排序标识 |
| stock_code | 股票代码 | varchar(20) | 公司唯一标识代码 |
| stock_abbr | 股票简称 | varchar(50) | 公司简称 |
| eps | 每股收益(元) | decimal(10,4) | 每股享有的净利润或亏损 |
| total_operating_revenue | 营业总收入(万元) | decimal(20,2) | 日常经营收入总额 |
| operating_revenue_yoy_growth | 营业总收入-同比增长(%) | decimal(10,4) | 同比变动比例 |
| operating_revenue_qoq_growth | 营业总收入-季度环比增长(%) | decimal(10,4) | 环比变动比例 |
| net_profit_10k_yuan | 净利润(万元) | decimal(20,2) | 净利润（万元） |
| net_profit_yoy_growth | 净利润-同比增长(%) | decimal(10,4) | 同比变动比例 |
| net_profit_qoq_growth | 净利润-季度环比增长(%) | decimal(10,4) | 环比变动比例 |
| net_asset_per_share | 每股净资产(元) | decimal(10,4) | 净资产 / 总股本 |
| roe | 净资产收益率(%) | decimal(10,4) | 净利润 / 净资产 |
| operating_cf_per_share | 每股经营现金流量(元) | decimal(10,4) | 经营现金流 / 总股本 |
| net_profit_excl_non_recurring | 扣非净利润（万元） | decimal(20,2) | 扣除非经常性损益后的净利润 |
| net_profit_excl_non_recurring_yoy | 扣非净利润同比增长（%） | decimal(10,4) | 同比变动比例 |
| gross_profit_margin | 销售毛利率(%) | decimal(10,4) | (收入-成本)/收入 |
| net_profit_margin | 销售净利率（%） | decimal(10,4) | 净利润 / 收入 |
| roe_weighted_excl_non_recurring | 加权平均净资产收益率（扣非）（%） | decimal(10,4) | 基于扣非净利润的ROE |
| report_period | 报告期 | varchar(20) | FY/Q1/HY/Q3 |
| report_year | 报告期-年份 | INT | 数据对应年份 |
---
## 三、资产负债表（`balance_sheet`）
| 字段名称 | 中文名称 | 字段类型 | 字段说明 |
|----------|----------|----------|----------|
| serial_number | 序号 | int | 数据排序标识 |
| stock_code | 股票代码 | varchar(20) | 公司唯一标识 |
| stock_abbr | 股票简称 | varchar(50) | 公司简称 |
| asset_cash_and_cash_equivalents | 资产-货币资金(万元) | decimal(20,2) | 现金及可随时支付存款 |
| asset_accounts_receivable | 资产-应收账款(万元) | decimal(20,2) | 应收客户款项 |
| asset_inventory | 资产-存货(万元) | decimal(20,2) | 存货 |
| asset_trading_financial_assets | 资产-交易性金融资产（万元） | decimal(20,2) | 短期持有的金融资产 |
| asset_construction_in_progress | 资产-在建工程（万元） | decimal(20,2) | 在建工程 |
| asset_total_assets | 资产-总资产(万元) | decimal(20,2) | 全部资产总额 |
| asset_total_assets_yoy_growth | 资产-总资产同比(%) | decimal(10,4) | 总资产同比增速 |
| liability_accounts_payable | 负债-应付账款(万元) | decimal(20,2) | 应付供应商款项 |
| liability_advance_from_customers | 负债-预收账款(万元) | decimal(20,2) | 预收客户款项 |
| liability_total_liabilities | 负债-总负债(万元) | decimal(20,2) | 全部负债总额 |
| liability_total_liabilities_yoy_growth | 负债-总负债同比(%) | decimal(10,4) | 总负债同比增速 |
| liability_contract_liabilities | 负债-合同负债（万元） | decimal(20,2) | 合同负债 |
| liability_short_term_loans | 负债-短期借款（万元） | decimal(20,2) | 一年内需偿还借款 |
| asset_liability_ratio | 资产负债率(%) | decimal(10,4) | 总负债/总资产 |
| equity_unappropriated_profit | 股东权益-未分配利润（万元） | decimal(20,2) | 未分配利润 |
| equity_total_equity | 股东权益合计(万元) | decimal(20,2) | 所有者权益总额 |
| report_period | 报告期 | varchar(20) | FY/Q1/HY/Q3 |
| report_year | 报告期-年份 | INT | 数据对应年份 |
---
## 四、现金流量表（`cash_flow_sheet`）
| 字段名称 | 中文名称 | 字段类型 | 字段说明 |
|----------|----------|----------|----------|
| serial_number | 序号 | int | 数据排序标识 |
| stock_code | 股票代码 | varchar(20) | 公司唯一标识 |
| stock_abbr | 股票简称 | varchar(50) | 公司简称 |
| net_cash_flow | 净现金流(元) | decimal(20,2) | 现金及现金等价物净增加额 |
| net_cash_flow_yoy_growth | 净现金流-同比增长(%) | decimal(10,4) | 同比增速 |
| operating_cf_net_amount | 经营性现金流-现金流量净额(万元) | decimal(20,2) | 经营现金流净额 |
| operating_cf_ratio_of_net_cf | 经营性现金流-净现金流占比(%) | decimal(10,4) | 经营现金流 / 总净现金流 |
| operating_cf_cash_from_sales | 经营性现金流-销售商品收到的现金（万元） | decimal(20,2) | 销售商品收到现金 |
| investing_cf_net_amount | 投资性现金流-现金流量净额(万元) | decimal(20,2) | 投资现金流净额 |
| investing_cf_ratio_of_net_cf | 投资性现金流-净现金流占比(%) | decimal(10,4) | 投资现金流 / 总净现金流 |
| investing_cf_cash_for_investments | 投资性现金流-投资支付的现金（万元） | decimal(20,2) | 投资支付现金 |
| investing_cf_cash_from_investment_recovery | 投资性现金流-收回投资收到的现金（万元） | decimal(20,2) | 收回投资收到现金 |
| financing_cf_cash_from_borrowing | 融资性现金流-取得借款收到的现金（万元） | decimal(20,2) | 借款收到现金 |
| financing_cf_cash_for_debt_repayment | 融资性现金流-偿还债务支付的现金（万元） | decimal(20,2) | 偿还债务支付现金 |
| financing_cf_net_amount | 融资性现金流-现金流量净额(万元) | decimal(20,2) | 融资现金流净额 |
| financing_cf_ratio_of_net_cf | 融资性现金流-净现金流占比(%) | decimal(10,4) | 融资现金流 / 总净现金流 |
| report_period | 报告期 | varchar(20) | FY/Q1/HY/Q3 |
| report_year | 报告期-年份 | INT | 数据对应年份 |
---
## 五、利润表（`income_sheet`）
| 字段名称 | 中文名称 | 字段类型 | 字段说明 |
|----------|----------|----------|----------|
| serial_number | 序号 | int | 数据排序标识 |
| stock_code | 股票代码 | varchar(20) | 公司唯一标识 |
| stock_abbr | 股票简称 | varchar(50) | 公司简称 |
| net_profit | 净利润(万元) | decimal(20,2) | 最终盈利或亏损 |
| net_profit_yoy_growth | 净利润同比(%) | decimal(10,4) | 同比增速 |
| other_income | 其他收益（万元） | decimal(20,2) | 非经营性政府补助等 |
| total_operating_revenue | 营业总收入(万元) | decimal(20,2) | 日常经营收入 |
| operating_revenue_yoy_growth | 营业总收入同比(%) | decimal(10,4) | 同比增速 |
| operating_expense_cost_of_sales | 营业总支出-营业支出(万元) | decimal(20,2) | 营业成本 |
| operating_expense_selling_expenses | 营业总支出-销售费用(万元) | decimal(20,2) | 销售费用 |
| operating_expense_administrative_expenses | 营业总支出-管理费用(万元) | decimal(20,2) | 管理费用 |
| operating_expense_financial_expenses | 营业总支出-财务费用(万元) | decimal(20,2) | 财务费用 |
| operating_expense_rnd_expenses | 营业总支出-研发费用（万元） | decimal(20,2) | 研发费用 |
| operating_expense_taxes_and_surcharges | 营业总支出-税金及附加（万元） | decimal(20,2) | 税金及附加 |
| total_operating_expenses | 营业总支出(万元) | decimal(20,2) | 全部经营支出总额 |
| operating_profit | 营业利润(万元) | decimal(20,2) | 日常经营利润 |
| total_profit | 利润总额(万元) | decimal(20,2) | 税前利润总额 |
| asset_impairment_loss | 资产减值损失（万元） | decimal(20,2) | 资产减值损失 |
| credit_impairment_loss | 信用减值损失（万元） | decimal(20,2) | 信用减值损失 |
| report_period | 报告期 | varchar(20) | FY/Q1/HY/Q3 |
| report_year | 报告期-年份 | INT | 数据对应年份 |