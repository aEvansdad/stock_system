# core/portfolio.py
import pandas as pd
import plotly.graph_objects as go
from data.yfinance_provider import YFinanceProvider
from core.backtester import Backtester

class PortfolioBacktester:
    def __init__(self, initial_capital=10000.0):
        self.initial_capital = initial_capital
        self.provider = YFinanceProvider()

    def run_portfolio_backtest(self, symbols: list, strategy_class, strategy_params: dict, period="2y"):
        """
        运行组合回测
        :param symbols: 股票列表 ['AAPL', 'MSFT']
        :param strategy_class: 策略类 (例如 SuperTrendStrategy)
        :param strategy_params: 策略参数字典 (例如 {'period':10, 'multiplier':3.0})
        """
        portfolio_results = {}
        combined_equity = None
        
        # 分配资金：假设平分
        capital_per_stock = self.initial_capital / len(symbols)
        
        print(f"🧺 开始组合回测: {len(symbols)} 只股票, 每只分配 ${capital_per_stock:.2f}")

        for symbol in symbols:
            try:
                # 1. 获取数据
                df = self.provider.get_price_history(symbol, period)
                if df.empty: continue
                
                # 2. 实例化策略
                # 这里的 **strategy_params 是把字典解包传进去
                strategy = strategy_class(**strategy_params)
                signals = strategy.generate_signals(df)
                
                # 3. 运行回测 (使用分配到的资金)
                backtester = Backtester(initial_capital=int(capital_per_stock))
                res = backtester.run_backtest(signals)
                
                # 4. 记录数据
                equity_curve = res['data']['Equity_Curve']
                portfolio_results[symbol] = {
                    'metrics': res['metrics'],
                    'equity': equity_curve
                }
                
                # 5. 叠加资金曲线
                if combined_equity is None:
                    combined_equity = equity_curve.copy()
                else:
                    # 按照日期对齐相加 (fill_value=0 处理停牌等情况)
                    combined_equity = combined_equity.add(equity_curve, fill_value=0)
                    
            except Exception as e:
                print(f"❌ {symbol} 回测失败: {e}")

        return {
            'details': portfolio_results,   # 每只股票的详细战报
            'total_equity': combined_equity # 总资产曲线
        }