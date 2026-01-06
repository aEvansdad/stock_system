# data/provider_interface.py
from abc import ABC, abstractmethod
import pandas as pd

class DataProvider(ABC):
    """
    数据提供者抽象基类
    所有具体的数据源(Yahoo, FMP, Webull等)都必须继承此类
    """
    
    @abstractmethod
    def get_price_history(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """
        获取历史价格数据
        :param symbol: 股票代码 (e.g., "AAPL")
        :param period: 时间周期 (e.g., "1y", "1mo", "1d")
        :return: 标准化的 DataFrame [Open, High, Low, Close, Volume]
        """
        pass