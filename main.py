# main.py
from data.yfinance_provider import YFinanceProvider

def main():
    print("🎄 Stock Intelligence System - Day 1 Test")
    print("=========================================")
    
    # 1. 初始化数据提供者
    # 如果以后要换数据源，只需要改这里，比如换成 FMPProvider()
    provider = YFinanceProvider()
    
    # 2. 定义要测试的股票
    symbol = "AAPL"
    
    # 3. 获取数据
    df = provider.get_price_history(symbol, period="1mo")
    
    # 4. 展示结果
    if not df.empty:
        print(f"\n✅ 成功获取 {symbol} 最近 1 个月数据：")
        print(f"数据行数: {len(df)}")
        print("\n最新 5 行数据:")
        print(df.tail())
    else:
        print("❌ 获取数据失败")

if __name__ == "__main__":
    main()