# main.py
from data.yfinance_provider import YFinanceProvider
from core.strategies.ma_cross import MovingAverageCrossStrategy
from core.backtester import Backtester  # <--- 新增导入

def main():
    print("💰 Stock Intelligence System - Day 3 Backtest")
    print("===========================================")
    
    # 1. 获取数据 (取过去 5 年，看长期表现)
    symbol = "AAPL"
    print(f"📥 [1/3] 获取 {symbol} 5年历史数据...")
    provider = YFinanceProvider()
    df = provider.get_price_history(symbol, period="5y") 
    
    if df.empty: return

    # 2. 运行策略
    print(f"⚙️ [2/3] 运行策略 (MA20 vs MA50)...")
    strategy = MovingAverageCrossStrategy(short_window=50, long_window=200)
    signals_df = strategy.generate_signals(df)
    
    # 3. 运行回测 (新增部分)
    print(f"💵 [3/3] 模拟交易 (初始资金 $10,000)...")
    backtester = Backtester(initial_capital=10000)
    results = backtester.run_backtest(signals_df)
    
    metrics = results['metrics']
    data = results['data']

    # 4. 打印最终报告
    print(f"\n📊 {symbol} 5年回测成绩单:")
    print(f"-----------------------------")
    print(f"最终资产: {metrics['Final Value']}")
    print(f"总收益率: {metrics['Total Return']}")
    print(f"最大回撤: {metrics['Max Drawdown']} (最惨时的跌幅)")
    print(f"日胜率  : {metrics['Win Rate (Daily)']}")
    
    # 对比一下：如果傻傻拿着不动 (Buy & Hold) 会赚多少？
    buy_and_hold_return = (df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1
    print(f"\n基准对比 (买入持有): {buy_and_hold_return:.2%}")

    if float(metrics['Total Return'].strip('%')) > buy_and_hold_return * 100:
        print("✅ 策略跑赢了死拿！牛逼！")
    else:
        print("⚠️ 策略没跑赢死拿，需要优化。")

if __name__ == "__main__":
    main()