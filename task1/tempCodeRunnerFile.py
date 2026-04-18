self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS core_performance_indicators_sheet (
                -- 主键：自增ID，用于唯一标识每条记录
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- 业务字段
                serial_number INTEGER,                    -- 序号：数据排序标识，用于区分不同记录
                stock_code VARCHAR(20) NOT NULL,          -- 股票代码：公司在证券市场的唯一标识代码
                stock_abbr VARCHAR(50),                   -- 股票简称：公司在证券市场的简称
                
                -- 盈利能力指标
                eps DECIMAL(10,4),                        -- 每股收益(元)：反映普通股股东每股享有的净利润
                total_operating_revenue DECIMAL(20,2),    -- 营业总收入(万元)：日常经营活动实现的全部收入
                operating_revenue_yoy_growth DECIMAL(10,4),   -- 营业总收入-同比增长(%)：较上年同期变动比例
                operating_revenue_qoq_growth DECIMAL(10,4),   -- 营业总收入-季度环比增长(%)：较上季度变动比例
                net_profit_10k_yuan DECIMAL(20,2),        -- 净利润(万元)：最终盈利或亏损总额
                net_profit_yoy_growth DECIMAL(10,4),      -- 净利润-同比增长(%)：较上年同期变动比例
                net_profit_qoq_growth DECIMAL(10,4),      -- 净利润-季度环比增长(%)：较上季度变动比例
                
                -- 资产与收益质量指标
                net_asset_per_share DECIMAL(10,4),        -- 每股净资产(元)：归属股东净资产/总股本
                roe DECIMAL(10,4),                        -- 净资产收益率(%)：衡量运用净资产盈利的能力
                operating_cf_per_share DECIMAL(10,4),     -- 每股经营现金流量(元)：经营现金流净额/总股本
                net_profit_excl_non_recurring DECIMAL(20,2),   -- 扣非净利润(万元)：剔除非经常性损益后的净利润
                net_profit_excl_non_recurring_yoy DECIMAL(10,4), -- 扣非净利润同比增长(%)：较上年同期变动比例
                
                -- 利润率指标
                gross_profit_margin DECIMAL(10,4),        -- 销售毛利率(%)：(营业总收入-营业成本)/营业总收入×100%
                net_profit_margin DECIMAL(10,4),          -- 销售净利率(%)：(净利润/营业总收入)×100%
                roe_weighted_excl_non_recurring DECIMAL(10,4),  -- 加权平均净资产收益率（扣非）(%)：基于扣非净利润计算
                
                -- 报告期信息
                report_period VARCHAR(20) NOT NULL CHECK (report_period IN ('FY', 'Q1', 'HY', 'Q3')),  
                -- 报告期：FY=年报，Q1=一季度，HY=半年度，Q3=三季度
                report_year INTEGER NOT NULL,             -- 报告期-年份：数据对应的年份
                
                -- 系统字段
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 创建时间：记录插入时间
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 更新时间：记录最后修改时间
                
                -- 约束：同一股票同一报告期只能有一条记录
                UNIQUE(stock_code, report_year, report_period)
            )
        ''')
        print("✓ 创建表: core_performance_indicators_sheet")
        
        # ==================== 2. 资产负债表 ====================
        # 说明：反映公司在特定日期的资产、负债和股东权益状况
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS balance_sheet (
                -- 主键：自增ID
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- 基础信息
                serial_number INTEGER,                    -- 序号：数据排序标识
                stock_code VARCHAR(20) NOT NULL,          -- 股票代码：唯一标识
                stock_abbr VARCHAR(50),                   -- 股票简称
                
                -- 资产类科目（流动资产）
                asset_cash_and_cash_equivalents DECIMAL(20,2),  -- 货币资金(万元)：现金及可随时支付的存款
                asset_accounts_receivable DECIMAL(20,2),       -- 应收账款(万元)：应收客户款项
                asset_inventory DECIMAL(20,2),                 -- 存货(万元)：库存商品、在产品等
                asset_trading_financial_assets DECIMAL(20,2),  -- 交易性金融资产(万元)：主要为银行理财产品
                asset_construction_in_progress DECIMAL(20,2),  -- 在建工程(万元)：正在建设的固定资产
                
                -- 资产总量指标
                asset_total_assets DECIMAL(20,2),              -- 总资产(万元)：全部资产总额
                asset_total_assets_yoy_growth DECIMAL(10,4),   -- 总资产同比(%)：较上年期末变动比例
                
                -- 负债类科目
                liability_accounts_payable DECIMAL(20,2),      -- 应付账款(万元)：应付供应商款项
                liability_advance_from_customers DECIMAL(20,2), -- 预收账款(万元)：预收客户款项
                liability_total_liabilities DECIMAL(20,2),     -- 总负债(万元)：全部负债总额
                liability_total_liabilities_yoy_growth DECIMAL(10,4), -- 总负债同比(%)：较上年期末变动比例
                liability_contract_liabilities DECIMAL(20,2),  -- 合同负债(万元)：预收合同对价
                liability_short_term_loans DECIMAL(20,2),      -- 短期借款(万元)：1年内到期的借款
                
                -- 偿债能力指标
                asset_liability_ratio DECIMAL(10,4),           -- 资产负债率(%)：总负债/总资产×100%
                
                -- 股东权益类科目
                equity_unappropriated_profit DECIMAL(20,2),    -- 未分配利润(万元)：累计未分配利润
                equity_total_equity DECIMAL(20,2),             -- 股东权益合计(万元)：所有者权益总额
                
                -- 报告期信息
                report_period VARCHAR(20) NOT NULL CHECK (report_period IN ('FY', 'Q1', 'HY', 'Q3')),
                report_year INTEGER NOT NULL,
                
                -- 系统字段
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- 唯一约束
                UNIQUE(stock_code, report_year, report_period)
            )
        ''')
        print("✓ 创建表: balance_sheet")
        
        # ==================== 3. 利润表 ====================
        # 说明：反映公司在一定会计期间的经营成果
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS income_sheet (
                -- 主键：自增ID
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- 基础信息
                serial_number INTEGER,                    -- 序号
                stock_code VARCHAR(20) NOT NULL,          -- 股票代码
                stock_abbr VARCHAR(50),                   -- 股票简称
                
                -- 盈利核心指标
                net_profit DECIMAL(20,2),                 -- 净利润(万元)：最终盈利或亏损
                net_profit_yoy_growth DECIMAL(10,4),      -- 净利润同比(%)：较上年同期变动比例
                other_income DECIMAL(20,2),               -- 其他收益(万元)：政府补助等非营业收入
                total_operating_revenue DECIMAL(20,2),    -- 营业总收入(万元)：全部营业收入
                operating_revenue_yoy_growth DECIMAL(10,4), -- 营业总收入同比(%)：较上年同期变动比例
                
                -- 营业支出明细（成本费用类）
                operating_expense_cost_of_sales DECIMAL(20,2),     -- 营业成本(万元)：销售商品、提供劳务的成本
                operating_expense_selling_expenses DECIMAL(20,2),  -- 销售费用(万元)：销售环节发生的费用
                operating_expense_administrative_expenses DECIMAL(20,2), -- 管理费用(万元)：管理环节发生的费用
                operating_expense_financial_expenses DECIMAL(20,2),      -- 财务费用(万元)：筹资活动发生的费用
                operating_expense_rnd_expenses DECIMAL(20,2),            -- 研发费用(万元)：研发活动发生的费用
                operating_expense_taxes_and_surcharges DECIMAL(20,2),    -- 税金及附加(万元)：应负担的税费
                
                -- 利润指标
                total_operating_expenses DECIMAL(20,2),   -- 营业总支出(万元)：全部经营支出总额
                operating_profit DECIMAL(20,2),           -- 营业利润(万元)：日常经营实现的利润
                total_profit DECIMAL(20,2),               -- 利润总额(万元)：税前利润总额
                
                -- 减值损失
                asset_impairment_loss DECIMAL(20,2),      -- 资产减值损失(万元)：各项资产减值准备
                credit_impairment_loss DECIMAL(20,2),     -- 信用减值损失(万元)：金融工具信用减值
                
                -- 报告期信息
                report_period VARCHAR(20) NOT NULL CHECK (report_period IN ('FY', 'Q1', 'HY', 'Q3')),
                report_year INTEGER NOT NULL,
                
                -- 系统字段
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- 唯一约束
                UNIQUE(stock_code, report_year, report_period)
            )
        ''')
        print("✓ 创建表: income_sheet")
        
        # ==================== 4. 现金流量表 ====================
        # 说明：反映公司在一定会计期间现金和现金等价物流入和流出的情况
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cash_flow_sheet (
                -- 主键：自增ID
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- 基础信息
                serial_number INTEGER,                    -- 序号
                stock_code VARCHAR(20) NOT NULL,          -- 股票代码
                stock_abbr VARCHAR(50),                   -- 股票简称
                
                -- 总体现金流
                net_cash_flow DECIMAL(20,2),              -- 净现金流(元)：现金及现金等价物净增加额
                net_cash_flow_yoy_growth DECIMAL(10,4),   -- 净现金流-同比增长(%)：较上年同期变动比例
                
                -- 经营活动现金流（核心造血能力）
                operating_cf_net_amount DECIMAL(20,2),    -- 经营性现金流-现金流量净额(万元)：经营流入-流出
                operating_cf_ratio_of_net_cf DECIMAL(10,4), -- 经营性现金流-净现金流占比(%)：占净现金流的比例
                operating_cf_cash_from_sales DECIMAL(20,2),  -- 经营性现金流-销售商品收到的现金(万元)
                
                -- 投资活动现金流（扩张与投资）
                investing_cf_net_amount DECIMAL(20,2),    -- 投资性现金流-现金流量净额(万元)：投资流入-流出
                investing_cf_ratio_of_net_cf DECIMAL(10,4), -- 投资性现金流-净现金流占比(%)：占净现金流的比例
                investing_cf_cash_for_investments DECIMAL(20,2),      -- 投资支付的现金(万元)
                investing_cf_cash_from_investment_recovery DECIMAL(20,2), -- 收回投资收到的现金(万元)
                
                -- 融资活动现金流（筹资与偿债）
                financing_cf_cash_from_borrowing DECIMAL(20,2),  -- 取得借款收到的现金(万元)
                financing_cf_cash_for_debt_repayment DECIMAL(20,2), -- 偿还债务支付的现金(万元)
                financing_cf_net_amount DECIMAL(20,2),           -- 融资性现金流-现金流量净额(万元)
                financing_cf_ratio_of_net_cf DECIMAL(10,4),      -- 融资性现金流-净现金流占比(%)：占净现金流的比例
                
                -- 报告期信息
                report_period VARCHAR(20) NOT NULL CHECK (report_period IN ('FY', 'Q1', 'HY', 'Q3')),
                report_year INTEGER NOT NULL,
                
                -- 系统字段
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- 唯一约束
                UNIQUE(stock_code, report_year, report_period)
            )
        ''')
        print("✓ 创建表: cash_flow_sheet")
        
        # 提交所有建表操作
        self.conn.commit()
        print("\n✓ 所有表创建完成！")
        
    def create_indexes(self):
        """
        创建索引以提升查询性能
        
        索引策略：
        - 单列索引：对常用的查询字段（stock_code, report_year）创建索引
        - 复合索引：对组合查询条件（stock_code + report_year）创建索引
        - 覆盖索引：尽可能包含查询所需的字段
        
        索引说明：
        - idx_core_stock_code: 支持按股票代码查询核心业绩
        - idx_core_report_year: 支持按年份筛选
        - idx_core_stock_year: 支持按股票+年份的组合查询
        - 其他表的索引类似
        """
        indexes = [
            # 核心业绩指标表索引
            "CREATE INDEX IF NOT EXISTS idx_core_stock_code ON core_performance_indicators_sheet(stock_code)",
            "CREATE INDEX IF NOT EXISTS idx_core_report_year ON core_performance_indicators_sheet(report_year)",
            "CREATE INDEX IF NOT EXISTS idx_core_stock_year ON core_performance_indicators_sheet(stock_code, report_year)",
            "CREATE INDEX IF NOT EXISTS idx_core_report_period ON core_performance_indicators_sheet(report_period)",
            
            # 资产负债表索引
            "CREATE INDEX IF NOT EXISTS idx_balance_stock_code ON balance_sheet(stock_code)",
            "CREATE INDEX IF NOT EXISTS idx_balance_report_year ON balance_sheet(report_year)",
            "CREATE INDEX IF NOT EXISTS idx_balance_stock_year ON balance_sheet(stock_code, report_year)",
            "CREATE INDEX IF NOT EXISTS idx_balance_report_period ON balance_sheet(report_period)",
            
            # 利润表索引
            "CREATE INDEX IF NOT EXISTS idx_income_stock_code ON income_sheet(stock_code)",
            "CREATE INDEX IF NOT EXISTS idx_income_report_year ON income_sheet(report_year)",
            "CREATE INDEX IF NOT EXISTS idx_income_stock_year ON income_sheet(stock_code, report_year)",
            "CREATE INDEX IF NOT EXISTS idx_income_report_period ON income_sheet(report_period)",
            
            # 现金流量表索引
            "CREATE INDEX IF NOT EXISTS idx_cashflow_stock_code ON cash_flow_sheet(stock_code)",
            "CREATE INDEX IF NOT EXISTS idx_cashflow_report_year ON cash_flow_sheet(report_year)",
            "CREATE INDEX IF NOT EXISTS idx_cashflow_stock_year ON cash_flow_sheet(stock_code, report_year)",
            "CREATE INDEX IF NOT EXISTS idx_cashflow_report_period ON cash_flow_sheet(report_period)"
        ]