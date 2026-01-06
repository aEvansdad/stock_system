# data/yfinance_provider.py
import yfinance as yf
import pandas as pd
from .provider_interface import DataProvider

class YFinanceProvider(DataProvider):
    def get_price_history(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        print(f"📥 [YFinance] 正在获取 {symbol} 数据 ({period})...")
        
        try:
            # auto_adjust=True 自动处理分红和拆股（复权）
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, auto_adjust=True)
            
            if df.empty:
                print(f"⚠️ 警告: {symbol} 返回数据为空")
                return pd.DataFrame()

            # 数据清洗：保留核心列，重置索引
            # yfinance 返回的列包含: Open, High, Low, Close, Volume, Dividends, Stock Splits
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            # 确保索引是 Datetime 类型
            df.index = pd.to_datetime(df.index)
            
            return df
            
        except Exception as e:
            print(f"❌ 错误: 获取 {symbol} 失败 - {e}")
            return pd.DataFrame()