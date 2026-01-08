# core/scanner.py
import pandas as pd
import streamlit as st
from data.yfinance_provider import YFinanceProvider
from core.patterns import PatternRecognizer # 确保导入了这个

class MarketScanner:
    def __init__(self):
        self.provider = YFinanceProvider()
        # 修复：在这里定义默认扫描的股票列表
        self.default_list = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", # 七巨头
            "AMD", "INTC", "NFLX", "DIS", "PYPL", "COIN"           # 其他热门股
        ]

    def scan_market(self, strategy, symbols=None):
        if symbols is None:
            symbols = self.default_list
            
        results = []
        progress_bar = st.progress(0)
        
        print(f"🕵️ 开始扫描 {len(symbols)} 只股票...")
        
        for i, symbol in enumerate(symbols):
            # 更新进度条
            progress_bar.progress((i + 1) / len(symbols))
            
            try:
                # 1. 获取价格数据
                df = self.provider.get_price_history(symbol, period="2y")
                if df.empty: continue
                
                # 2. 获取基本面数据 (Day 11 新增)
                fund_data = self.provider.get_fundamentals(symbol) # <--- 调用刚才写的方法
                
                # 3. 识别形态
                recognizer = PatternRecognizer(df)
                patterns_df = recognizer.detect_patterns()
                last_pat = patterns_df.iloc[-1]
                
                pattern_tags = []
                if last_pat['Pattern_Hammer']: pattern_tags.append("🔨 Hammer")
                if last_pat['Pattern_Doji']: pattern_tags.append("➕ Doji")
                if last_pat['Pattern_Bullish_Engulfing']: pattern_tags.append("🐂 Bullish")
                pattern_str = ", ".join(pattern_tags) if pattern_tags else "-"

                # 4. 运行策略
                signals = strategy.generate_signals(df)
                last_row = signals.iloc[-1]
                
                # 5. 判断状态
                status = "Wait"
                if last_row['Position'] == 1: status = "🔺 BUY"
                elif last_row['Position'] == -1: status = "🔻 SELL"
                elif last_row['Signal'] == 1: status = "✅ Holding"
                else: status = "⚪ Empty"
                
                # 6. 收集结果 (合并基本面数据)
                # 我们把 fund_data 里的字段拆开存进去
                mc_billions = fund_data['MarketCap'] / 1e9 # 转换为十亿 (B)
                
                results.append({
                    'Symbol': symbol,
                    'Price': round(last_row['Close'], 2),
                    'Status': status,
                    'Pattern': pattern_str,
                    'Sector': fund_data['Sector'],       # <--- 新增
                    'PE': round(fund_data['PE_Ratio'], 2) if fund_data['PE_Ratio'] else 0, # <--- 新增
                    'Mkt Cap (B)': round(mc_billions, 2), # <--- 新增
                    'Date': str(last_row.name)[:10]
                })
                
            except Exception as e:
                print(f"❌ 扫描 {symbol} 出错: {e}")
                
        progress_bar.empty()
        return pd.DataFrame(results)