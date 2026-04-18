# 数据库表结构说明

## 一、核心业绩指标表
**表名：** `core_performance_indicators_sheet`

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| serial_number | 序号 | int | 数据排序标识 |
| stock_code | 股票代码 | varchar(20) | 唯一标识代码 |
| stock_abbr | 股票简称 | varchar(50) | 证券市场简称 |
| eps | 每股收益(元) | decimal(10,4) | 每股净利润 |
| total_operating_revenue | 营业总收入(万元) | decimal(20,2) | 日常经营收入总额 |
| operating_revenue_yoy_growth | 营业总收入-同比增长(%) | decimal(10,4) | 同比变动比例 |
| operating_revenue_qoq_growth | 营业总收入-季度环比增长(%) | decimal(10,4) | 环比变动比例 |
| net_profit_10k_yuan | 净利润(万元) | decimal(20,2) | 净利润 |
| net_profit_yoy_growth | 净利润-同比增长(%) | decimal(10,4) | 同比变动比例 |
| net_profit_qoq_growth | 净利润-季度环比增长(%) | decimal(10,4) | 环比变动比例 |
| net_asset_per_share | 每股净资产(元) | decimal(10,4) | 归属股东净资产 / 总股本 |
| roe | 净资产收益率(%) | decimal(10,4) | 净资产盈利能力 |
| operating_cf_per_share | 每股经营现金流量(元) | decimal(10,4) | 经营现金流 / 总股本 |
| net_profit_excl_non_recurring | 扣非净利润（万元） | decimal(20,2) | 剔除异常损益 |
| net_profit_excl_non_recurring_yoy | 扣非净利润同比增长（%） | decimal(10,4) | 同比变动比例 |
| gross_profit_margin | 销售毛利率(%) | decimal(10,4) | （收入-成本）/收入 |
| net_profit_margin | 销售净利率（%） | decimal(10,4) | 净利润 / 收入 |
| roe_weighted_excl_non_recurring | 加权平均净资产收益率（扣非）（%） | decimal(10,4) | 扣非后ROE |
| report_period | 报告期 | varchar(20) | FY/Q1/HY/Q3 |
| report_year | 报告期-年份 | int | 年份 |

## 二、资产负债表
**表名：** `balance_sheet`

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| serial_number | 序号 | int | 数据排序标识 |
| stock_code | 股票代码 | varchar(20) | 唯一标识代码 |
| stock_abbr | 股票简称 | varchar(50) | 证券市场简称 |
| asset_cash_and_cash_equivalents | 资产-货币资金(万元) | decimal(20,2) | 现金及存款 |
| asset_accounts_receivable | 资产-应收账款(万元) | decimal(20,2) | 应收款项 |
| asset_inventory | 资产-存货(万元) | decimal(20,2) | 存货 |
| asset_trading_financial_assets | 资产-交易性金融资产（万元） | decimal(20,2) | 短期金融资产 |
| asset_construction_in_progress | 资产-在建工程（万元） | decimal(20,2) | 在建工程 |
| asset_total_assets | 资产-总资产(万元) | decimal(20,2) | 总资产 |
| asset_total_assets_yoy_growth | 资产-总资产同比(%) | decimal(10,4) | 总资产同比 |
| liability_accounts_payable | 负债-应付账款(万元) | decimal(20,2) | 应付款项 |
| liability_advance_from_customers | 负债-预收账款(万元) | decimal(20,2) | 预收款项 |
| liability_total_liabilities | 负债-总负债(万元) | decimal(20,2) | 总负债 |
| liability_total_liabilities_yoy_growth | 负债-总负债同比(%) | decimal(10,4) | 总负债同比 |
| liability_contract_liabilities | 负债-合同负债（万元） | decimal(20,2) | 合同负债 |
| liability_short_term_loans | 负债-短期借款（万元） | decimal(20,2) | 短期借款 |
| asset_liability_ratio | 资产负债率(%) | decimal(10,4) | 总负债/总资产 |
| equity_unappropriated_profit | 股东权益-未分配利润（万元） | decimal(20,2) | 未分配利润 |
| equity_total_equity | 股东权益合计(万元) | decimal(20,2) | 所有者权益 |
| report_period | 报告期 | varchar(20) | FY/Q1/HY/Q3 |
| report_year | 报告期-年份 | int | 年份 |

## 三、现金流量表
**表名：** `cash_flow_sheet`

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| serial_number | 序号 | int | 数据排序标识 |
| stock_code | 股票代码 | varchar(20) | 唯一标识代码 |
| stock_abbr | 股票简称 | varchar(50) | 证券市场简称 |
| net_cash_flow | 净现金流(元) | decimal(20,2) | 现金及等价物净增加额 |
| net_cash_flow_yoy_growth | 净现金流-同比增长(%) | decimal(10,4) | 同比变动 |
| operating_cf_net_amount | 经营性现金流-现金流量净额(万元) | decimal(20,2) | 经营现金流净额 |
| operating_cf_ratio_of_net_cf | 经营性现金流-净现金流占比(%) | decimal(10,4) | 占净现金流比例 |
| operating_cf_cash_from_sales | 经营性现金流-销售商品收到的现金（万元） | decimal(20,2) | 销售回款 |
| investing_cf_net_amount | 投资性现金流-现金流量净额(万元) | decimal(20,2) | 投资现金流净额 |
| investing_cf_ratio_of_net_cf | 投资性现金流-净现金流占比(%) | decimal(10,4) | 占净现金流比例 |
| investing_cf_cash_for_investments | 投资性现金流-投资支付的现金（万元） | decimal(20,2) | 投资支付现金 |
| investing_cf_cash_from_investment_recovery | 投资性现金流-收回投资收到的现金（万元） | decimal(20,2) | 收回投资现金 |
| financing_cf_cash_from_borrowing | 融资性现金流-取得借款收到的现金（万元） | decimal(20,2) | 借款收到现金 |
| financing_cf_cash_for_debt_repayment | 融资性现金流-偿还债务支付的现金（万元） | decimal(20,2) | 偿还债务现金 |
| financing_cf_net_amount | 融资性现金流-现金流量净额(万元) | decimal(20,2) | 融资现金流净额 |
| financing_cf_ratio_of_net_cf | 融资性现金流-净现金流占比(%) | decimal(10,4) | 占净现金流比例 |
| report_period | 报告期 | varchar(20) | FY/Q1/HY/Q3 |
| report_year | 报告期-年份 | int | 年份 |

## 四、利润表
**表名：** `income_sheet`

| 字段名 | 中文名 | 类型 | 说明 |
|--------|--------|------|------|
| serial_number | 序号 | int | 数据排序标识 |
| stock_code | 股票代码 | varchar(20) | 唯一标识代码 |
| stock_abbr | 股票简称 | varchar(50) | 证券市场简称 |
| net_profit | 净利润(万元) | decimal(20,2) | 最终盈利或亏损 |
| net_profit_yoy_growth | 净利润同比(%) | decimal(10,4) | 同比变动 |
| other_income | 其他收益（万元） | decimal(20,2) | 政府补助等 |
| total_operating_revenue | 营业总收入(万元) | decimal(20,2) | 日常经营收入 |
| operating_revenue_yoy_growth | 营业总收入同比(%) | decimal(10,4) | 同比变动 |
| operating_expense_cost_of_sales | 营业总支出-营业支出(万元) | decimal(20,2) | 营业成本 |
| operating_expense_selling_expenses | 营业总支出-销售费用(万元) | decimal(20,2) | 销售费用 |
| operating_expense_administrative_expenses | 营业总支出-管理费用(万元) | decimal(20,2) | 管理费用 |
| operating_expense_financial_expenses | 营业总支出-财务费用(万元) | decimal(20,2) | 财务费用 |
| operating_expense_rnd_expenses | 营业总支出-研发费用（万元） | decimal(20,2) | 研发费用 |
| operating_expense_taxes_and_surcharges | 营业总支出-税金及附加（万元） | decimal(20,2) | 税金及附加 |
| total_operating_expenses | 营业总支出(万元) | decimal(20,2) | 总经营支出 |
| operating_profit | 营业利润(万元) | decimal(20,2) | 经营利润 |
| total_profit | 利润总额(万元) | decimal(20,2) | 税前利润总额 |
| asset_impairment_loss | 资产减值损失（万元） | decimal(20,2) | 资产减值损失 |
| credit_impairment_loss | 信用减值损失（万元） | decimal(20,2) | 信用减值损失 |
| report_period | 报告期 | varchar(20) | FY/Q1/HY/Q3 |
| report_year | 报告期-年份 | int | 年份 |
## 股票代码,股票简称
{
    "600222": "太龙药业",
    "600252": "中恒集团",
    "603998": "方盛制药",
    "600518": "康美药业",
    "600085": "同仁堂",
    "600535": "天士力",
    "603896": "寿仙谷",
    "600080": "金花股份",
    "603139": "康惠制药",
    "600332": "白云山",
    "600351": "亚宝药业",
    "600572": "康恩贝",
    "600129": "太极集团",
    "600329": "达仁堂",
    "603439": "贵州三力",
    "600557": "康缘药业",
    "600566": "济川药业",
    "600613": "神奇制药",
    "600976": "健民集团",
    "600422": "昆药集团",
    "600771": "广誉远",
    "600436": "片仔癀",
    "600479": "千金药业",
    "600993": "龙津药业",
    "603567": "珍宝岛",
    "603858": "步长制药",
    "600671": "天目药业",
    "600750": "江中药业",
    "600285": "羚锐制药",
    "600594": "益佰制药",
    "002873": "新天药业",
    "300147": "香雪制药",
    "300391": "长药控股",
    "000790": "华神科技",
    "002603": "以岭药业",
    "000989": "九芝堂",
    "002219": "新里程",
    "300519": "新光药业",
    "000650": "仁和药业",
    "300869": "康泰医学",
    "002728": "特一药业",
    "002589": "瑞康医药",
    "002737": "葵花药业",
    "002898": "赛隆药业",
    "002864": "盘龙药业",
    "002287": "奇正藏药",
    "002752": "嘉应制药",
    "301334": "恩威医药",
    "002424": "贵州百灵",
    "301111": "粤万年青",
    "300026": "红日药业",
    "000766": "通化金马",
    "002082": "万邦德",
    "002317": "众生药业",
    "300534": "陇神戎发",
    "002390": "信邦制药",
    "002907": "华森制药",
    "300878": "维康药业",
    "002275": "桂林三金",
    "002566": "益盛药业",
    "000590": "启迪药业",
    "000423": "东阿阿胶",
    "300158": "振东制药",
    "002166": "莱茵生物",
    "000538": "云南白药",
    "002773": "康弘药业",
    "002107": "沃华医药",
    "300181": "佐力药业",
    "000999": "华润三九",
    "002349": "精华制药"
}