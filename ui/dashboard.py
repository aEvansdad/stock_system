# ui/dashboard.py
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import itertools

from data.yfinance_provider import YFinanceProvider
from core.strategies.ma_cross import MovingAverageCrossStrategy
from core.backtester import Backtester
from core.scanner import MarketScanner # <--- 新增导入
from core.optimizer import StrategyOptimizer # <--- 新增
from core.strategies.rsi import RsiStrategy   # <--- 新增
from core.strategies.macd import MacdStrategy # <--- 新增

def render_dashboard():
    st.title("🎄 Stock Intelligence System")

    # 创建三个标签页
    tab1, tab2, tab3 = st.tabs(["📈 策略回测 (Backtest)", "🕵️ 市场扫描 (Scanner)", "🧪 参数优化 (Optimizer)"])

    # ==========================
    # TAB 1: 策略回测 (升级版)
    # ==========================
    with tab1:
        st.sidebar.header("⚙️ 策略设置")
        
        # 1. 选择策略
        strategy_type = st.sidebar.selectbox(
            "选择交易策略", 
            ["双均线 (MA Cross)", "RSI (超买超卖)", "MACD (趋势跟踪)"]
        )
        
        st.sidebar.divider()
        
        # 2. 根据选择显示不同的参数
        strategy = None # 初始化
        
        if strategy_type == "双均线 (MA Cross)":
            st.sidebar.subheader("均线参数")
            short_window = st.sidebar.slider("短期均线", 5, 100, 50)
            long_window = st.sidebar.slider("长期均线", 20, 300, 200)
            # 实例化策略
            strategy = MovingAverageCrossStrategy(short_window, long_window)
            
        elif strategy_type == "RSI (超买超卖)":
            st.sidebar.subheader("RSI 参数")
            rsi_period = st.sidebar.slider("RSI 周期", 5, 30, 14)
            rsi_buy = st.sidebar.slider("买入阈值 (超卖)", 10, 40, 30)
            rsi_sell = st.sidebar.slider("卖出阈值 (超买)", 60, 90, 70)
            # 实例化策略
            strategy = RsiStrategy(rsi_period, rsi_buy, rsi_sell)
            
        elif strategy_type == "MACD (趋势跟踪)":
            st.sidebar.subheader("MACD 参数")
            macd_fast = st.sidebar.slider("快线 (Fast)", 5, 50, 12)
            macd_slow = st.sidebar.slider("慢线 (Slow)", 20, 100, 26)
            macd_signal = st.sidebar.slider("信号线 (Signal)", 5, 50, 9)
            # 实例化策略
            strategy = MacdStrategy(macd_fast, macd_slow, macd_signal)

        # 3. 通用设置 (股票代码等)
        # 把之前的代码稍微挪个位置，放在主页面更清晰
        col1, col2 = st.columns([1, 3])
        with col1:
            symbol = st.text_input("回测代号", value="AAPL").upper()
            period = st.selectbox("数据周期", ["1y", "2y", "5y", "10y"], index=2)
            initial_capital = st.number_input("初始资金 ($)", value=10000)
            
        with col2:
            st.info(f"当前使用的策略: **{strategy_type}**")
            run_backtest = st.button("🚀 开始回测", type="primary")

        # 4. 运行逻辑
        if run_backtest:
            with st.spinner(f"正在使用 {strategy_type} 分析 {symbol} ..."):
                provider = YFinanceProvider()
                df = provider.get_price_history(symbol, period)
                
                if not df.empty and strategy:
                    # 运行多态策略 (不管选的是谁，都有 generate_signals 方法)
                    signals_df = strategy.generate_signals(df)
                    
                    backtester = Backtester(initial_capital)
                    results = backtester.run_backtest(signals_df)
                    
                    # --- 下面的绘图代码基本不用变，或者稍微适配一下指标线 ---
                    metrics = results['metrics']
                    data = results['data']
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("最终资产", metrics['Final Value'])
                    m2.metric("总收益率", metrics['Total Return'])
                    m3.metric("最大回撤", metrics['Max Drawdown'])
                    m4.metric("胜率", metrics['Win Rate (Daily)'])
                    
                    # 绘图区
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3])
                    fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name='K线'), row=1, col=1)
                    
                    # 动态画指标线
                    if strategy_type == "双均线 (MA Cross)":
                        fig.add_trace(go.Scatter(x=data.index, y=data['SMA_Short'], line=dict(color='orange'), name='Short'), row=1, col=1)
                        fig.add_trace(go.Scatter(x=data.index, y=data['SMA_Long'], line=dict(color='blue'), name='Long'), row=1, col=1)
                    elif strategy_type == "RSI (超买超卖)":
                        # RSI 可以在下面画个小图，或者直接不管，只看买卖点。这里简单处理，只画买卖点。
                        pass 
                    
                    # 画买卖点 (所有策略通用)
                    buys = data[data['Position'] == 1]
                    sells = data[data['Position'] == -1]
                    fig.add_trace(go.Scatter(x=buys.index, y=buys['Close'], mode='markers', marker=dict(color='green', size=12, symbol='triangle-up'), name='Buy'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=sells.index, y=sells['Close'], mode='markers', marker=dict(color='red', size=12, symbol='triangle-down'), name='Sell'), row=1, col=1)
                    
                    # 资金曲线
                    fig.add_trace(go.Scatter(x=data.index, y=data['Equity_Curve'], fill='tozeroy', line=dict(color='green'), name='净值'), row=2, col=1)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("无法获取数据")

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
                        width="stretch"
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
                        width="stretch"
                    )
            else:
                st.warning("没有获取到数据。")

    # ==========================
    # TAB 3: 参数优化 (Day 6)
    # ==========================
    with tab3:
        st.subheader("🧪 寻找最优策略参数")
        st.write("暴力测试不同的均线组合，寻找该股票的历史最佳参数。")
        
        col1, col2 = st.columns(2)
        with col1:
            opt_symbol = st.text_input("股票代码", value="AAPL", key="opt_symbol").upper()
            
        with col2:
            opt_period = st.selectbox("数据周期", ["2y", "5y", "10y"], index=1, key="opt_period")

        st.divider()
        
        # 参数范围选择
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**短期均线范围 (Short)**")
            s_start = st.number_input("开始", 10, 50, 10)
            s_end = st.number_input("结束", 20, 100, 50)
            s_step = st.number_input("步长", 1, 10, 5) # 步长越大跑得越快，越不精细
        
        with c2:
            st.markdown("**长期均线范围 (Long)**")
            l_start = st.number_input("开始", 50, 100, 100)
            l_end = st.number_input("结束", 100, 300, 200)
            l_step = st.number_input("步长", 1, 20, 10)

        if st.button("🧪 开始挖掘", type="primary"):
            provider = YFinanceProvider()
            df = provider.get_price_history(opt_symbol, opt_period)
            
            if df.empty:
                st.error("无法获取数据")
            else:
                optimizer = StrategyOptimizer(df)
                
                # 创建 range 对象
                # range(start, end + 1, step) 确保包含 end
                s_range = range(s_start, s_end + 1, s_step)
                l_range = range(l_start, l_end + 1, l_step)
                
                total_combos = len(list(itertools.product(s_range, l_range)))
                st.info(f"即将进行 {total_combos} 次回测模拟，请稍候...")
                
                # 运行
                with st.spinner("正在疯狂计算中..."):
                    res_df = optimizer.optimize(s_range, l_range)
                
                # 显示结果
                st.success("优化完成！已按收益率从高到低排序：")
                
                # 冠军参数
                best = res_df.iloc[0]
                st.metric("🏆 最佳回报组合", f"Short {int(best['Short'])} / Long {int(best['Long'])}", f"{best['Return (%)']:.2f}%")
                
                # 详细表格
                st.dataframe(res_df.style.background_gradient(subset=['Return (%)'], cmap='RdYlGn'), width="stretch")
                
                # 散点图可视化 (可选)
                import plotly.express as px
                
                # 修复：计算绝对值用来控制气泡大小 (防止因负收益报错)
                res_df['Size'] = res_df['Return (%)'].abs()
                
                fig = px.scatter(res_df, x='Short', y='Long', 
                                 size='Size',           # 大小用绝对值
                                 color='Return (%)',    # 颜色看真本事 (红亏绿赚)
                                 hover_data=['Return (%)', 'Win Rate'], # 鼠标放上去显示真实数据
                                 title="参数热力分布 (颜色越绿越赚)", 
                                 color_continuous_scale='RdYlGn')
                st.plotly_chart(fig)            