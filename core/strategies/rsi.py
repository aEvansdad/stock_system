# core/strategies/rsi.py
import pandas as pd
import pandas_ta as ta
from .base_strategy import BaseStrategy
import numpy as np

class RsiStrategy(BaseStrategy):
    def __init__(self, period=14, buy_threshold=30, sell_threshold=70):
        self.period = period
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        signals = df.copy()
        
        # 1. 计算 RSI
        signals['RSI'] = ta.rsi(signals['Close'], length=self.period)
        
        # 2. 初始化信号
        signals['Signal'] = 0
        
        # 3. 生成逻辑 (状态机模式)
        # 我们创建一个 'Stance' (持仓态度) 列
        # 1 = 持有, 0 = 空仓, NaN = 保持现状
        
        signals['Stance'] = np.nan
        
        # 触发买入：RSI < 30 (超卖) -> 设为 1
        signals.loc[signals['RSI'] < self.buy_threshold, 'Stance'] = 1
        
        # 触发卖出：RSI > 70 (超买) -> 设为 0
        signals.loc[signals['RSI'] > self.sell_threshold, 'Stance'] = 0
        
        # 4. 填充中间状态 (关键步骤)
        # ffill() 会把最近一次的 1 或 0 延续下去
        # 如果一开始就是 NaN (还没到买卖点)，填为 0
        signals['Signal'] = signals['Stance'].ffill().fillna(0)
        
        # 5. 计算买卖动作 (Position = 1 买入, -1 卖出)
        signals['Position'] = signals['Signal'].diff()
        
        return signals