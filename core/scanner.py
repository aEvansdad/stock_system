# core/scanner.py
import pandas as pd
from data.yfinance_provider import YFinanceProvider
from core.strategies.ma_cross import MovingAverageCrossStrategy

class MarketScanner:
    def __init__(self):
        self.provider = YFinanceProvider()

    def scan_market(self, symbols: list, short_window=50, long_window=200) -> pd.DataFrame:
        """
        扫描列表中的所有股票，返回最新的信号状态
        """
        results = []
        
        # 实例化策略
        strategy = MovingAverageCrossStrategy(short_window, long_window)
        
        print(f"📡 开始扫描 {len(symbols)} 只股票...")
        
        for symbol in symbols:
            try:
                # 1. 获取数据 (只需要最近 2 年即可，为了算 200 日均线)
                df = self.provider.get_price_history(symbol, period="2y")
                
                if df.empty:
                    continue
                
                # 2. 运行策略
                signals = strategy.generate_signals(df)
                
                # 3. 提取最后一天的数据
                last_row = signals.iloc[-1]
                prev_row = signals.iloc[-2] # 前一天，用于判断趋势
                
                # 4. 判断当前状态
                status = "Wait"
                if last_row['Position'] == 1:
                    status = "🔺 BUY (Golden Cross)"
                elif last_row['Position'] == -1:
                    status = "🔻 SELL (Death Cross)"
                elif last_row['Signal'] == 1:
                    status = "✅ Holding (Bullish)"
                else:
                    status = "⚪ Empty (Bearish)"
                
                # 5. 收集结果
                results.append({
                    'Symbol': symbol,
                    'Close Price': round(last_row['Close'], 2),
                    'SMA_Short': round(last_row['SMA_Short'], 2),
                    'SMA_Long': round(last_row['SMA_Long'], 2),
                    'Status': status,
                    'Date': str(last_row.name)[:10]
                })
                
            except Exception as e:
                print(f"❌ 扫描 {symbol} 出错: {e}")
                continue
                
        # 转为 DataFrame 返回
        return pd.DataFrame(results)