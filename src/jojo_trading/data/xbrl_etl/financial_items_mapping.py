# 台灣上市櫃公司 XBRL 財報常用財務科目與 XBRL 標籤對應表（初版）
# 若需補充 DCF 相關細項，請直接於此擴充

FINANCIAL_ITEMS_MAPPING = {
    # 資產負債表
    "資產總計": ["Assets"],
    "流動資產合計": ["CurrentAssets"],
    "非流動資產合計": ["NoncurrentAssets"],
    "負債總計": ["Liabilities"],
    "流動負債合計": ["CurrentLiabilities"],
    "非流動負債合計": ["NoncurrentLiabilities"],
    "股東權益總計": ["Equity"],
    "普通股股本": ["OrdinaryShareCapital"],
    "保留盈餘": ["RetainedEarnings"],

    # 綜合損益表
    "營業收入": ["OperatingRevenue"],
    "營業成本": ["OperatingCosts"],
    "營業毛利": ["GrossProfitLoss"],
    "營業費用": ["OperatingExpenses"],
    "營業利益": ["OperatingIncomeLoss"],
    "營業外收入及支出合計": ["NonoperatingIncomeAndExpenses"],
    "稅前淨利": ["ProfitLossFromContinuingOperationsBeforeTax"],
    "所得稅費用": ["IncomeTaxExpenseBenefit"],
    "稅後淨利": ["ProfitLoss"],
    "基本每股盈餘": ["BasicEarningsPerShare"],

    # 現金流量表
    "營業活動之淨現金流入": ["NetCashFlowsFromOperatingActivities"],
    "投資活動之淨現金流入": ["NetCashFlowsFromInvestingActivities"],
    "籌資活動之淨現金流入": ["NetCashFlowsFromFinancingActivities"],
    "本期現金及約當現金增加數": ["IncreaseDecreaseInCashAndCashEquivalents"],

    # DCF 相關細項（可擴充）
    "折舊費用": ["DepreciationExpense"],
    "攤銷費用": ["AmortizationExpense"],
    "利息費用": ["InterestExpense"],
    "現金及約當現金": ["CashAndCashEquivalents"],
    "應收帳款": ["AccountsReceivableNet"],
    "存貨": ["InventoriesNet"],
    "應付帳款": ["AccountsPayable"],
    "短期借款": ["ShortTermBorrowings"],
    "長期借款": ["LongTermBorrowings"],
    "應付公司債": ["BondsPayable"],
    "資本支出": ["AcquisitionOfPropertyPlantAndEquipment"],

    # 其他可依需求補充
}
