# core/optimizer.py
import pandas as pd
import itertools
from core.strategies.ma_cross import MovingAverageCrossStrategy
from core.backtester import Backtester

class StrategyOptimizer:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        
    def optimize(self, short_range: range, long_range: range) -> pd.DataFrame:
        """
        暴力搜索最优参数组合
        :param short_range: 短期均线尝试范围 (例如 range(10, 50, 5))
        :param long_range: 长期均线尝试范围 (例如 range(100, 200, 10))
        """
        results = []
        
        # 生成所有组合
        combinations = list(itertools.product(short_range, long_range))
        print(f"🧪 正在测试 {len(combinations)} 种参数组合...")
        
        for short_win, long_win in combinations:
            # 必须保证 短期 < 长期，否则没意义
            if short_win >= long_win:
                continue
                
            # 1. 运行策略
            strategy = MovingAverageCrossStrategy(short_win, long_win)
            signals = strategy.generate_signals(self.df)
            
            # 2. 运行回测
            backtester = Backtester() # 默认 10000 起始资金
            res = backtester.run_backtest(signals)
            metrics = res['metrics']
            
            # 3. 记录结果 (我们需要数字类型来排序，所以要把百分号去掉)
            total_return = float(metrics['Total Return'].strip('%'))
            max_drawdown = float(metrics['Max Drawdown'].strip('%'))
            
            results.append({
                'Short': short_win,
                'Long': long_win,
                'Return (%)': total_return,
                'Drawdown (%)': max_drawdown,
                'Win Rate': metrics['Win Rate (Daily)']
            })
            
        # 转为 DataFrame 并按收益率排序
        results_df = pd.DataFrame(results)
        if not results_df.empty:
            results_df = results_df.sort_values(by='Return (%)', ascending=False)
            
        return results_df