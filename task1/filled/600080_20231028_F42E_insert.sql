-- 股票代码: 600080
-- 报告年份: 2023年
-- 报告期: Q3
-- 生成时间: 2026-04-18 02:49:28
-- ============================================================

-- 表名: core_performance_indicators_sheet
REPLACE INTO core_performance_indicators_sheet (stock_code, stock_abbr, eps, total_operating_revenue, operating_revenue_yoy_growth, net_profit_10k_yuan, net_profit_yoy_growth, net_profit_excl_non_recurring, net_profit_excl_non_recurring_yoy, gross_profit_margin, net_profit_margin, roe_weighted_excl_non_recurring, report_period, report_year) VALUES ('600080', '金花股份', 0.0009, 40280.503175, -4.81, 339.02983, -89.35, 2001.616467, -36.94, 76.94, 0.84, 1.19, 'Q3', 2023);

------------------------------------------------------------------------------------------------------------------------

-- 表名: balance_sheet

REPLACE INTO balance_sheet (
    stock_code,
    stock_abbr,
    asset_cash_and_cash_equivalents,
    asset_accounts_receivable,
    asset_inventory,
    asset_trading_financial_assets,
    asset_construction_in_progress,
    asset_total_assets,
    asset_total_assets_yoy_growth,
    liability_accounts_payable,
    liability_advance_from_customers,
    liability_total_liabilities,
    liability_contract_liabilities,
    liability_short_term_loans,
    asset_liability_ratio,
    equity_unappropriated_profit,
    equity_total_equity,
    report_period,
    report_year
) VALUES (
    '600080',
    '金花股份',
    44058.095602,
    11331.779362,
    2843.854088,
    19387.463948,
    40614.62838,
    205883.10419,
    4.28,
    1466.457001,
    0.0,
    37167.507148,
    155.297614,
    7640.539044,
    18.05,
    48432.638338,
    168715.597042,
    'Q3',
    2023
);


------------------------------------------------------------------------------------------------------------------------

-- 表名: income_sheet
REPLACE INTO income_sheet (stock_code, stock_abbr, net_profit, other_income, total_operating_revenue, operating_revenue_yoy_growth, operating_expense_cost_of_sales, operating_expense_selling_expenses, operating_expense_administrative_expenses, operating_expense_financial_expenses, operating_expense_rnd_expenses, operating_expense_taxes_and_surcharges, total_operating_expenses, operating_profit, total_profit, credit_impairment_loss, report_period, report_year) VALUES ('600080', '金花股份', 339.02983, 22.235042, 40280.503175, -4.81, 9291.415305, 24088.989091, 5162.776233, -157.366254, 886.027209, 686.466077, 39958.307661, 2055.6716, 193.603353, 640.421178, 'Q3', 2023);

------------------------------------------------------------------------------------------------------------------------

-- 表名: cash_flow_sheet
REPLACE INTO cash_flow_sheet (stock_code, stock_abbr, report_period, report_year, net_cash_flow, operating_cf_net_amount, operating_cf_cash_from_sales, investing_cf_net_amount, investing_cf_cash_for_investments, financing_cf_net_amount, financing_cf_cash_from_borrowing, financing_cf_cash_for_debt_repayment) VALUES ('600080', '金花股份', 'Q3', 2023, 6902170.3, -1194.931466, 40935.379393, -4851.472524, 16600.0, 6736.62102, 17540.539044, 9900.0);

------------------------------------------------------------------------------------------------------------------------

