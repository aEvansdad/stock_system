# core/strategies/macd.py
import pandas as pd
import pandas_ta as ta
from .base_strategy import BaseStrategy

class MacdStrategy(BaseStrategy):
    def __init__(self, fast=12, slow=26, signal=9):
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        signals = df.copy()
        
        # 1. 计算 MACD
        # pandas_ta 的 macd 函数会返回三列: MACD, Histogram, Signal
        macd_df = ta.macd(signals['Close'], fast=self.fast, slow=self.slow, signal=self.signal)
        
        # 因为列名可能会变 (比如 MACD_12_26_9)，我们需要按位置或者重命名
        # 通常列顺序是: macd, histogram, signal
        macd_cols = macd_df.columns
        signals['MACD'] = macd_df[macd_cols[0]]
        signals['MACD_Signal'] = macd_df[macd_cols[2]]
        
        # 2. 初始化信号
        signals['Signal'] = 0
        
        # 3. 生成逻辑
        # 金叉: MACD > Signal
        condition = signals['MACD'] > signals['MACD_Signal']
        signals.loc[condition, 'Signal'] = 1
        
        # 4. 计算买卖动作
        signals['Position'] = signals['Signal'].diff()
        
        return signals