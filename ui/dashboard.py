# ui/dashboard.py
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data.yfinance_provider import YFinanceProvider
from core.strategies.ma_cross import MovingAverageCrossStrategy
from core.backtester import Backtester
from core.scanner import MarketScanner # <--- 新增导入

def render_dashboard():
    st.title("🎄 Stock Intelligence System")
    
    # 创建两个标签页
    tab1, tab2 = st.tabs(["📈 策略回测 (Backtest)", "🕵️ 市场扫描 (Scanner)"])
    
    # ==========================
    # TAB 1: 单只股票回测 (Day 4 的内容)
    # ==========================
    with tab1:
        # --- 侧边栏只在 Tab 1 生效不太好做，我们把参数放在页面内或者通用侧边栏
        # 为了简单，我们复用侧边栏，但逻辑分块
        st.sidebar.header("⚙️ 全局设置")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            symbol = st.text_input("回测代号", value="AAPL").upper()
            period = st.selectbox("数据周期", ["1y", "2y", "5y", "10y"], index=2)
            
        with col2:
            st.info("调整左侧侧边栏参数来改变策略敏感度")

        # 侧边栏参数
        short_window = st.sidebar.slider("短期均线 (Short)", 5, 100, 50)
        long_window = st.sidebar.slider("长期均线 (Long)", 20, 300, 200)
        initial_capital = st.sidebar.number_input("初始资金 ($)", value=10000)

        if st.button("🚀 开始回测", type="primary"):
            with st.spinner(f"正在分析 {symbol} ..."):
                provider = YFinanceProvider()
                df = provider.get_price_history(symbol, period)
                
                if not df.empty:
                    strategy = MovingAverageCrossStrategy(short_window, long_window)
                    signals_df = strategy.generate_signals(df)
                    backtester = Backtester(initial_capital)
                    results = backtester.run_backtest(signals_df)
                    
                    # 显示指标
                    metrics = results['metrics']
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("最终资产", metrics['Final Value'])
                    m2.metric("总收益率", metrics['Total Return'])
                    m3.metric("最大回撤", metrics['Max Drawdown'])
                    m4.metric("胜率", metrics['Win Rate (Daily)'])
                    
                    # 绘图
                    data = results['data']
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
                    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='K线'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=data.index, y=data['SMA_Short'], line=dict(color='orange'), name=f'MA{short_window}'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=data.index, y=data['SMA_Long'], line=dict(color='blue'), name=f'MA{long_window}'), row=1, col=1)
                    
                    # 标记买卖点
                    buys = data[data['Position'] == 1]
                    sells = data[data['Position'] == -1]
                    fig.add_trace(go.Scatter(x=buys.index, y=buys['Close'], mode='markers', marker=dict(color='green', size=10, symbol='triangle-up'), name='Buy'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=sells.index, y=sells['Close'], mode='markers', marker=dict(color='red', size=10, symbol='triangle-down'), name='Sell'), row=1, col=1)
                    
                    fig.add_trace(go.Scatter(x=data.index, y=data['Equity_Curve'], fill='tozeroy', line=dict(color='green'), name='净值'), row=2, col=1)
                    st.plotly_chart(fig, use_container_width=True)

    # ==========================
    # TAB 2: 市场扫描 (UI 优化版)
    # ==========================
    with tab2:
        st.subheader("🕵️ 批量扫描")
        
        # 默认股票池
        default_list = "AAPL, MSFT, NVDA, TSLA, GOOGL, AMZN, META, AMD, SPY, QQQ"
        user_input = st.text_area("输入股票代码 (用逗号分隔)", value=default_list, height=70)
        
        if st.button("📡 开始扫描", type="primary"):
            # 处理输入
            symbols = [s.strip().upper() for s in user_input.split(',') if s.strip()]
            
            scanner = MarketScanner()
            with st.spinner(f"正在扫描 {len(symbols)} 只股票..."):
                scan_results = scanner.scan_market(symbols, short_window, long_window)
                
            if not scan_results.empty:
                # --- 1. 数据分流 ---
                # 找出需要行动的 (Buy/Sell) 和 不需要行动的 (Holding/Empty)
                action_df = scan_results[scan_results['Status'].str.contains("BUY|SELL")]
                passive_df = scan_results[~scan_results['Status'].str.contains("BUY|SELL")]
                
                # --- 2. 顶部统计卡片 ---
                buy_count = len(scan_results[scan_results['Status'].str.contains("BUY")])
                sell_count = len(scan_results[scan_results['Status'].str.contains("SELL")])
                
                c1, c2, c3 = st.columns(3)
                c1.metric("🔍 扫描数量", len(scan_results))
                c2.metric("🔺 买入信号", buy_count, delta=buy_count if buy_count > 0 else None)
                c3.metric("🔻 卖出信号", sell_count, delta=-sell_count if sell_count > 0 else None)
                
                st.divider()

                # --- 3. 重点展示区 ---
                if not action_df.empty:
                    st.error("🚨 发现今日交易机会！")
                    st.dataframe(
                        action_df.style.map(
                            lambda x: 'background-color: #ffcccc' if 'SELL' in str(x) else 'background-color: #ccffcc', 
                            subset=['Status']
                        ),
                        use_container_width=True
                    )
                else:
                    st.success("🍵 今日无操作信号 (No Action Needed)")

                # --- 4. 详情列表 (折叠) ---
                with st.expander(f"查看其余 {len(passive_df)} 只股票状态 (Holding/Empty)", expanded=True):
                    # 对 Holding 和 Empty 做简单的颜色区分
                    st.dataframe(
                        passive_df.style.map(
                            lambda x: 'color: green' if 'Holding' in str(x) else 'color: gray',
                            subset=['Status']
                        ),
                        use_container_width=True
                    )
            else:
                st.warning("没有获取到数据。")