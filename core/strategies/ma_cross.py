# core/strategies/ma_cross.py
import pandas as pd
import pandas_ta as ta
from .base_strategy import BaseStrategy

class MovingAverageCrossStrategy(BaseStrategy):
    def __init__(self, short_window=20, long_window=50):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        # 1. 创建副本，避免修改原始数据
        signals = df.copy()

        # 2. 使用 pandas_ta 计算均线
        # SMA: Simple Moving Average
        signals['SMA_Short'] = ta.sma(signals['Close'], length=self.short_window)
        signals['SMA_Long'] = ta.sma(signals['Close'], length=self.long_window)

        # 3. 初始化信号列
        signals['Signal'] = 0

        # 4. 生成信号逻辑
        # 当 短期均线 > 长期均线 时，标记为 1 (持仓状态)
        # 注意：iloc[self.long_window:] 是为了跳过开头数据不足算不出均线的行
        condition = signals['SMA_Short'] > signals['SMA_Long']
        signals.loc[condition, 'Signal'] = 1

        # 5. 计算买卖点 (Positions)
        # diff() 用于计算变化：
        # 0 -> 1 : diff = 1 (买入信号 🔺)
        # 1 -> 0 : diff = -1 (卖出信号 🔻)
        signals['Position'] = signals['Signal'].diff()

        return signals