# core/patterns.py
import pandas as pd
import numpy as np

class PatternRecognizer:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        
    def detect_patterns(self) -> pd.DataFrame:
        """
        识别经典K线形态
        返回的 DataFrame 会增加几列 pattern 的布尔值
        """
        df = self.df
        
        # 预计算一些实体和影线的长度
        # 实体 (Body) = |收 - 开|
        realbody = abs(df['Close'] - df['Open'])
        
        # 上影线 (Upper Shadow) = 高 - max(开, 收)
        upper_shadow = df['High'] - df[['Open', 'Close']].max(axis=1)
        
        # 下影线 (Lower Shadow) = min(开, 收) - 低
        lower_shadow = df[['Open', 'Close']].min(axis=1) - df['Low']
        
        # 蜡烛总长度 (Range)
        candle_range = df['High'] - df['Low']
        
        # --- 1. 识别十字星 (Doji) ---
        # 定义：实体非常小 (比如小于总长度的 10%)
        df['Pattern_Doji'] = realbody <= (candle_range * 0.1)
        
        # --- 2. 识别锤子线 (Hammer) ---
        # 定义：
        # a. 实体较小 (在 K 线顶端)
        # b. 下影线很长 (至少是实体的 2 倍)
        # c. 上影线很短 (甚至没有)
        # d. 必须是阴跌之后的反转信号 (简单的判断：收盘价 < 50日均线，或者单纯看形态)
        
        # 这里我们只看“形态本身”，不看趋势位置，趋势由人判断
        is_small_body = realbody <= (candle_range * 0.3)
        long_lower_shadow = lower_shadow >= (realbody * 2.0)
        short_upper_shadow = upper_shadow <= (realbody * 0.5)
        
        df['Pattern_Hammer'] = is_small_body & long_lower_shadow & short_upper_shadow
        
        # --- 3. 识别吞没形态 (Engulfing) ---
        # 阳包阴 (Bullish Engulfing): 昨天跌，今天涨，且今天把昨天整个包住了
        # 阴包阳 (Bearish Engulfing): 昨天涨，今天跌，且今天把昨天整个包住了
        
        prev_open = df['Open'].shift(1)
        prev_close = df['Close'].shift(1)
        
        # 昨天是跌的 (Close < Open)
        prev_is_red = prev_close < prev_open
        # 今天是涨的 (Close > Open)
        curr_is_green = df['Close'] > df['Open']
        
        # 包住逻辑：今天开盘 < 昨天收盘 AND 今天收盘 > 昨天开盘
        bullish_engulf = (
            prev_is_red & curr_is_green & 
            (df['Open'] <= prev_close) & 
            (df['Close'] >= prev_open)
        )
        
        df['Pattern_Bullish_Engulfing'] = bullish_engulf
        
        return df[['Pattern_Doji', 'Pattern_Hammer', 'Pattern_Bullish_Engulfing']]