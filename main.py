# main.py
from data.yfinance_provider import YFinanceProvider
from core.strategies.ma_cross import MovingAverageCrossStrategy

def main():
    print("🧠 Stock Intelligence System - Day 2 Strategy Test")
    print("================================================")
    
    # 1. 获取数据 (Day 1 的工作)
    symbol = "AAPL"
    provider = YFinanceProvider()
    df = provider.get_price_history(symbol, period="1y") # 取1年数据看趋势
    
    if df.empty:
        print("❌ 数据获取失败")
        return

    # 2. 运行策略 (Day 2 的工作)
    print(f"\n⚙️ 正在运行双均线策略 (MA20 vs MA50)...")
    strategy = MovingAverageCrossStrategy(short_window=20, long_window=50)
    result_df = strategy.generate_signals(df)
    
    # 3. 找出所有买入/卖出信号
    buy_signals = result_df[result_df['Position'] == 1]
    sell_signals = result_df[result_df['Position'] == -1]
    
    # 4. 打印报告
    print(f"\n📊 {symbol} 策略分析报告:")
    print(f"-------------------------")
    print(f"检测到买入机会: {len(buy_signals)} 次")
    print(f"检测到卖出机会: {len(sell_signals)} 次")
    
    print(f"\n最近 3 次交易信号:")
    # 合并买卖信号并按时间排序
    all_signals = result_df[result_df['Position'] != 0].tail(3)
    
    for date, row in all_signals.iterrows():
        action = "🔺 买入 (GOLDEN CROSS)" if row['Position'] == 1 else "🔻 卖出 (DEATH CROSS)"
        price = row['Close']
        print(f"[{date.date()}] {action} @ ${price:.2f}")

if __name__ == "__main__":
    main()