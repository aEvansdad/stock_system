# ui/dashboard.py
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import itertools
import pandas as pd

from data.yfinance_provider import YFinanceProvider
from core.strategies.ma_cross import MovingAverageCrossStrategy
from core.backtester import Backtester
from core.scanner import MarketScanner # <--- 新增导入
from core.optimizer import StrategyOptimizer # <--- 新增
from core.strategies.rsi import RsiStrategy   # <--- 新增
from core.strategies.macd import MacdStrategy # <--- 新增
from data.news_provider import NewsProvider # <--- 新增
from core.strategies.supertrend import SuperTrendStrategy # <--- 新增
from core.portfolio import PortfolioBacktester # <--- 新增

def render_dashboard():
    st.title("🎄 Stock Intelligence System")

    # 创建五个标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 策略回测 (Backtest)", "🕵️ 市场扫描 (Scanner)", "🧪 参数优化 (Optimizer)", "📰 情报中心 (News)", "💼 组合回测 (Portfolio Backtest)"])

    # ==========================
    # TAB 1: 策略回测 (升级版)
    # ==========================
    with tab1:
        st.sidebar.header("⚙️ 策略设置")
        
        # 1. 选择策略
        strategy_type = st.sidebar.selectbox(
            "选择交易策略", 
            ["双均线 (MA Cross)", "RSI (超买超卖)", "MACD (趋势跟踪)", "SuperTrend (超级趋势)"]
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
        elif strategy_type == "SuperTrend (超级趋势)":
            st.sidebar.subheader("SuperTrend 参数")
            st_period = st.sidebar.slider("ATR 周期", 5, 30, 10)
            st_factor = st.sidebar.slider("倍数 (Multiplier)", 1.0, 5.0, 3.0, step=0.1)
            # 实例化
            strategy = SuperTrendStrategy(st_period, st_factor)    

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
                    elif strategy_type == "SuperTrend (超级趋势)":
                    # 根据方向变色：涨势用绿线，跌势用红线
                    # 这里我们简单画一条线，Plotly 会自动连起来，或者我们可以分段画
                    # 简单画法：直接画一条线，颜色固定，或者用 marker
                        fig.add_trace(go.Scatter(
                            x=data.index, 
                            y=data['SuperTrend'], 
                            line=dict(color='purple', width=2, dash='dash'), 
                            name='SuperTrend Line'
                        ), row=1, col=1)
                    
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
        st.subheader("🕵️ 全市场扫描器")
        
        # --- 修复：确保变量名是 scan_tickers ---
        default_list = "AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, AMD, INTC, NFLX"
        scan_tickers = st.text_area("输入扫描股票池 (逗号分隔)", value=default_list, height=70)
        # -------------------------------------

        col1, col2 = st.columns([1, 3])
        with col1:
            # 按钮逻辑
            start_scan = st.button("📡 开始全市场扫描", type="primary")

        # 确保这里不需要缩进到 col1 里面，或者是接着写
        if start_scan:
            # --- 修复：先定义 symbols_list ---
            # 把输入框里的字符串 (scan_tickers) 分割成列表
            symbols_list = [s.strip().upper() for s in scan_tickers.split(',') if s.strip()]
            # -------------------------------
            
            # 1. 实例化扫描器
            scanner = MarketScanner()
            
            # 2. 实例化一个默认策略用于扫描 (例如：标准双均线 50/200)
            # 你也可以换成 RsiStrategy() 或 SuperTrendStrategy()
            scan_strategy = MovingAverageCrossStrategy(short_window=50, long_window=200)
            
            # 3. 传入策略对象和股票列表 (修复报错：现在需要两个参数)
            with st.spinner(f"正在扫描 {len(symbols_list)} 只股票 (策略: MA 50/200)..."):
                scan_results = scanner.scan_market(scan_strategy, symbols_list)
                
            if not scan_results.empty:
                # ==========================
                # 🔍 过滤器逻辑 (Day 11)
                # ==========================
                # 注意：with 下面必须缩进！
                with st.expander("🌪️ 结果过滤器 (Filter Results)", expanded=True):
                    f_col1, f_col2, f_col3 = st.columns(3)
                    
                    with f_col1:
                        all_sectors = ["All"] + list(scan_results['Sector'].unique())
                        sel_sector = st.selectbox("行业 (Sector)", all_sectors)
                    
                    with f_col2:
                        max_pe = st.slider("最大市盈率 (Max PE)", 0, 100, 50)
                    
                    with f_col3:
                        min_cap = st.slider("最小市值 ($B)", 0, 500, 0)

                # --- 执行过滤 ---
                filtered_df = scan_results.copy()
                
                # 1. 行业
                if sel_sector != "All":
                    filtered_df = filtered_df[filtered_df['Sector'] == sel_sector]
                
                # 2. PE
                filtered_df = filtered_df[(filtered_df['PE'] > 0) & (filtered_df['PE'] <= max_pe)]
                
                # 3. 市值
                filtered_df = filtered_df[filtered_df['Mkt Cap (B)'] >= min_cap]
                
                # 更新用于显示的数据
                display_df = filtered_df
                
                st.caption(f"筛选后剩余: {len(display_df)} 只股票")
                st.divider()

                # ==========================
                # 📊 结果展示逻辑 (必须缩进在 if not scan_results.empty 里面)
                # ==========================
                
                # 1. 统计数据
                buy_count = len(display_df[display_df['Status'].str.contains("BUY")])
                sell_count = len(display_df[display_df['Status'].str.contains("SELL")])
                pattern_count = len(display_df[display_df['Pattern'] != "-"])
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("🔍 筛选数量", len(display_df))
                c2.metric("🔺 买点", buy_count)
                c3.metric("🔻 卖点", sell_count)
                c4.metric("🕯️ 形态", pattern_count)
                
                st.divider()

                # 2. 重点关注列表 (Buy/Sell 或 有形态)
                is_signal = display_df['Status'].str.contains("BUY|SELL")
                is_pattern = display_df['Pattern'] != "-"
                action_df = display_df[is_signal | is_pattern]
                
                if not action_df.empty:
                    st.error("🚨 重点关注 (信号/形态)")
                    
                    def highlight_row(row):
                        styles = [''] * len(row)
                        if 'BUY' in str(row['Status']):
                            status_idx = row.index.get_loc('Status')
                            styles[status_idx] = 'background-color: #90EE90; color: black'
                        elif 'SELL' in str(row['Status']):
                            status_idx = row.index.get_loc('Status')
                            styles[status_idx] = 'background-color: #FFB6C1; color: black'
                        
                        if row['Pattern'] != "-":
                            pat_idx = row.index.get_loc('Pattern')
                            styles[pat_idx] = 'background-color: #FFFACD; color: black; font-weight: bold'
                        return styles

                    st.dataframe(action_df.style.apply(highlight_row, axis=1), use_container_width=True)
                else:
                    st.info("筛选结果中无重点交易信号。")
                
                # 3. 其余列表
                passive_df = display_df[~(is_signal | is_pattern)]
                if not passive_df.empty:
                    with st.expander(f"查看其余 {len(passive_df)} 只股票"):
                        st.dataframe(passive_df)
                        
            else:
                st.warning("未扫描到任何结果，请检查代码或网络。")

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

    # ==========================
    # TAB 4: 情报中心 (Day 8 重制版)
    # ==========================
    with tab4:
        st.subheader("📰 全球市场情报")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            # 这里的输入框默认值可以是上面选过的 symbol，或者给个新默认值
            news_symbol = st.text_input("输入代码", value="AAPL", key="news_search_input").upper()
            search_btn = st.button("🔍 搜集情报", type="primary")
            
        st.divider()

        if search_btn or news_symbol:
            news_provider = NewsProvider()
            with st.spinner(f"正在从全网搜集关于 {news_symbol} 的线索..."):
                news_list = news_provider.get_company_news(news_symbol, limit=10)
            
            if news_list:
                # 遍历新闻列表，显示漂亮的布局
                for i, news in enumerate(news_list):
                    # 使用 expander 或者 container 美化
                    with st.container():
                        # 标题做成蓝色超链接
                        st.markdown(f"### [{news['title']}]({news['link']})")
                        
                        # 第一行：来源和时间 (用小字)
                        st.caption(f"📢 {news['publisher']}  |  🕒 {news['date']}")
                        
                        # 正文摘要
                        if news['summary']:
                            st.info(news['summary'])
                        
                        # 如果不是最后一条，加个分割线
                        if i < len(news_list) - 1:
                            st.divider()
            else:
                st.warning("未搜索到相关新闻，可能是网络问题或代码输入有误。")
    # ==========================
    # TAB 5: 组合回测 (Day 10)
    # ==========================
    with tab5:
        st.subheader("🧺 投资组合压力测试")
        st.write("假设我们将资金 **平分** 给多只股票，并同时执行相同的策略，结果会如何？")
        
        # 1. 输入股票池
        default_portfolio = "AAPL, MSFT, NVDA, TSLA, GOOGL, AMZN, META"
        pf_symbols = st.text_area("投资组合 (逗号分隔)", value=default_portfolio, height=70)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            pf_capital = st.number_input("总投入资金 ($)", value=100000, step=10000)
        with col2:
            pf_period = st.selectbox("回测周期", ["1y", "2y", "5y"], index=1, key="pf_period")
        with col3:
            # 选择策略 (为了简化，我们在组合回测里只提供一种最强的策略选择，或者复用 Tab 1 的逻辑)
            # 这里演示用 SuperTrend，因为它是你最新的武器
            pf_strategy_name = st.selectbox("统一应用策略", ["SuperTrend", "MACD", "MA Cross"])

        # 策略参数区 (根据选择显示)
        params = {}
        strategy_cls = None
        
        if pf_strategy_name == "SuperTrend":
            st.caption("参数: Period=10, Multiplier=3.0 (默认)")
            strategy_cls = SuperTrendStrategy
            params = {'period': 10, 'multiplier': 3.0}
        elif pf_strategy_name == "MACD":
            st.caption("参数: 12, 26, 9 (默认)")
            strategy_cls = MacdStrategy
            params = {'fast': 12, 'slow': 26, 'signal': 9}
        elif pf_strategy_name == "MA Cross":
            st.caption("参数: 50, 200 (默认)")
            strategy_cls = MovingAverageCrossStrategy
            params = {'short_window': 50, 'long_window': 200}

        if st.button("🔥 运行组合压力测试", type="primary"):
            symbols_list = [s.strip().upper() for s in pf_symbols.split(',') if s.strip()]
            
            pf_tester = PortfolioBacktester(initial_capital=pf_capital)
            
            with st.spinner(f"正在同时交易 {len(symbols_list)} 只股票..."):
                results = pf_tester.run_portfolio_backtest(symbols_list, strategy_cls, params, pf_period)
            
            total_equity = results['total_equity']
            if total_equity is not None:
                # 1. 核心指标
                start_val = pf_capital
                end_val = total_equity.iloc[-1]
                total_ret = (end_val - start_val) / start_val * 100
                
                m1, m2 = st.columns(2)
                m1.metric("组合最终资产", f"${end_val:,.2f}")
                m2.metric("组合总收益率", f"{total_ret:.2f}%", delta=f"${end_val-start_val:,.2f}")
                
                # 2. 绘制总资产曲线
                st.markdown("### 📈 组合总资产曲线")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=total_equity.index, y=total_equity, fill='tozeroy', line=dict(color='gold'), name='Total Portfolio'))
                st.plotly_chart(fig, use_container_width=True)
                
                # 3. 各股表现对比
                st.markdown("### 🏆 各股贡献排行榜")
                details = results['details']
                rows = []
                for sym, data in details.items():
                    metrics = data['metrics']
                    # 提取数值
                    ret_val = float(metrics['Total Return'].strip('%'))
                    rows.append({
                        'Symbol': sym,
                        'Return (%)': ret_val,
                        'Final Value': metrics['Final Value'],
                        'Win Rate': metrics['Win Rate (Daily)']
                    })
                
                df_rank = pd.DataFrame(rows).sort_values(by='Return (%)', ascending=False)
                st.dataframe(df_rank.style.background_gradient(subset=['Return (%)'], cmap='RdYlGn'), use_container_width=True)
                
            else:
                st.error("回测失败，请检查股票代码或网络。")                                