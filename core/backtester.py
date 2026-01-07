# core/backtester.py
import pandas as pd
import numpy as np

class Backtester:
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital

    def run_backtest(self, df: pd.DataFrame) -> dict:
        """
        运行回测
        :param df: 必须包含 'Close' 和 'Signal' 列
        :return: 包含回测结果和性能指标的字典
        """
        # 1. 准备数据
        data = df.copy()
        
        # 计算股票的每日涨跌幅 (Pct Change)
        data['Market_Return'] = data['Close'].pct_change()
        
        # 2. 计算策略收益
        # 核心逻辑：今天的策略收益 = 今天的股票涨跌 * 昨天收盘时的持仓状态
        # shift(1) 非常重要！防止“未来函数”作弊
        data['Strategy_Return'] = data['Market_Return'] * data['Signal'].shift(1)
        
        # 3. 计算资金曲线 (累计收益)
        # cumprod() 是累乘，计算复利
        data['Equity_Curve'] = self.initial_capital * (1 + data['Strategy_Return']).cumprod()
        
        # 4. 计算最大回撤 (Max Drawdown) - 评估风险的关键
        # rolling_max: 截止到当天的历史最高净值
        data['Peak'] = data['Equity_Curve'].cummax()
        # drawdown: 当前净值相对于历史最高点的跌幅
        data['Drawdown'] = (data['Equity_Curve'] - data['Peak']) / data['Peak']
        
        # 5. 汇总性能指标
        metrics = self._calculate_metrics(data)
        
        return {
            'data': data,       # 详细的每日数据 (用于画图)
            'metrics': metrics  # 汇总的指标 (用于报告)
        }

    def _calculate_metrics(self, data: pd.DataFrame) -> dict:
        """计算核心评价指标"""
        total_return = (data['Equity_Curve'].iloc[-1] / self.initial_capital) - 1
        max_drawdown = data['Drawdown'].min() # 这是一个负数
        
        # 计算胜率 (基于日收益)
        winning_days = len(data[data['Strategy_Return'] > 0])
        total_days = len(data[data['Strategy_Return'] != 0])
        win_rate = winning_days / total_days if total_days > 0 else 0
        
        return {
            'Total Return': f"{total_return:.2%}",
            'Max Drawdown': f"{max_drawdown:.2%}",
            'Win Rate (Daily)': f"{win_rate:.2%}",
            'Final Value': f"${data['Equity_Curve'].iloc[-1]:,.2f}"
        }