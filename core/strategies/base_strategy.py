# core/strategies/base_strategy.py
from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    """
    所有交易策略的基类
    """
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        输入原始数据的 DataFrame
        输出带有 'Signal' 列的 DataFrame
        Signal 定义: 1 (买入), -1 (卖入), 0 (观望)
        """
        pass