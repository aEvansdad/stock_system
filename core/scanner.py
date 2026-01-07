# core/scanner.py
import pandas as pd
from data.yfinance_provider import YFinanceProvider
from core.strategies.ma_cross import MovingAverageCrossStrategy
from core.patterns import PatternRecognizer

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
                # 1. 获取数据
                df = self.provider.get_price_history(symbol, period="2y")
                if df.empty: continue
                
                # --- Day 9 新增: 识别形态 ---
                recognizer = PatternRecognizer(df)
                patterns_df = recognizer.detect_patterns()
                # 提取最后一天的形态
                last_pat = patterns_df.iloc[-1]
                
                # 生成形态标签字符串
                pattern_tags = []
                if last_pat['Pattern_Hammer']: pattern_tags.append("🔨 Hammer")
                if last_pat['Pattern_Doji']: pattern_tags.append("➕ Doji")
                if last_pat['Pattern_Bullish_Engulfing']: pattern_tags.append("🐂 Bullish Engulf")
                
                pattern_str = ", ".join(pattern_tags) if pattern_tags else "-"
                # ---------------------------
                
                # 2. 运行策略 (均线策略)
                signals = strategy.generate_signals(df)
                last_row = signals.iloc[-1]
                
                # 3. 判断状态
                status = "Wait"
                if last_row['Position'] == 1: status = "🔺 BUY (Golden Cross)"
                elif last_row['Position'] == -1: status = "🔻 SELL (Death Cross)"
                elif last_row['Signal'] == 1: status = "✅ Holding"
                else: status = "⚪ Empty"
                
                # 4. 收集结果 (增加了 'Pattern' 列)
                results.append({
                    'Symbol': symbol,
                    'Close': round(last_row['Close'], 2),
                    'Status': status,
                    'Pattern': pattern_str,  # <--- 新增这一列
                    'Date': str(last_row.name)[:10]
                })
                
            except Exception as e:
                print(f"❌ 扫描 {symbol} 出错: {e}")
                continue
                
        # 转为 DataFrame 返回
        return pd.DataFrame(results)