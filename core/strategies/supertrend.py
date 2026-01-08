# core/strategies/supertrend.py
import pandas as pd
import pandas_ta as ta
from .base_strategy import BaseStrategy

class SuperTrendStrategy(BaseStrategy):
    def __init__(self, period=10, multiplier=3.0):
        """
        :param period: ATR 周期 (默认 10)
        :param multiplier: ATR 倍数 (默认 3.0，倍数越大，止损越宽，越不容易被震出局)
        """
        self.period = period
        self.multiplier = multiplier

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        signals = df.copy()
        
        # 1. 计算 SuperTrend
        # pandas_ta 的 supertrend 会返回两列：
        # SUPERT_{period}_{multiplier}: 趋势线数值
        # SUPERTd_{period}_{multiplier}: 方向 (1 为涨, -1 为跌)
        st_data = ta.supertrend(signals['High'], signals['Low'], signals['Close'], 
                                length=self.period, multiplier=self.multiplier)
        
        # 把列名标准化，方便后面用
        # 列名通常比较长，比如 SUPERT_10_3.0，我们直接按位置取
        signals['SuperTrend'] = st_data.iloc[:, 0]       # 趋势线
        signals['SuperTrend_Dir'] = st_data.iloc[:, 1]   # 方向 (1 或 -1)
        
        # 2. 生成信号
        # 1 (绿线) -> 持有
        # -1 (红线) -> 空仓
        signals['Signal'] = 0
        signals.loc[signals['SuperTrend_Dir'] == 1, 'Signal'] = 1
        signals.loc[signals['SuperTrend_Dir'] == -1, 'Signal'] = 0
        
        # 3. 计算买卖动作
        signals['Position'] = signals['Signal'].diff()
        
        return signals