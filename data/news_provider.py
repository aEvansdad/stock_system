# data/news_provider.py
import feedparser
from datetime import datetime
import time

class NewsProvider:
    def get_company_news(self, symbol: str, limit=10):
        """
        使用 Google News RSS 获取最新财经新闻 (最稳定方案)
        """
        print(f"📡 正在连接 Google News RSS 获取 {symbol} 情报...")
        
        # Google News RSS 搜索接口
        # hl=en-US&gl=US&ceid=US:en 确保获取的是美股英文资讯
        rss_url = f"https://news.google.com/rss/search?q={symbol}+stock&hl=en-US&gl=US&ceid=US:en"
        
        try:
            feed = feedparser.parse(rss_url)
            
            clean_news = []
            if not feed.entries:
                return []

            for entry in feed.entries[:limit]:
                # RSS 返回的标准字段
                title = entry.get('title', 'No Title')
                link = entry.get('link', '#')
                pub_date = entry.get('published', 'Recent')
                # --- 修复 Pylance 报错：拆解 source 获取逻辑 ---
                source = 'Google News' # 默认值
                if 'source' in entry:
                    s_data = entry['source']
                    # 只有当它是字典时，才去取 title
                    if isinstance(s_data, dict):
                        source = s_data.get('title', 'Google News')
                    # 如果 feedparser 把它解析成了其他奇怪的对象，我们保持默认值
                # ---------------------------------------------
                
                # 尝试清洗时间格式 (Tue, 07 Jan 2025 10:00:00 GMT -> 2025-01-07)
                try:
                    dt_struct = entry.get('published_parsed')
                    if dt_struct:
                        date_str = time.strftime('%Y-%m-%d %H:%M', dt_struct) # type: ignore
                    else:
                        date_str = str(pub_date)[:16] # 截取前一部分
                except:
                    date_str = pub_date

                # Google RSS 的 summary 往往包含 HTML 标签，比较乱，我们只取标题和链接
                # 或者尝试简单清洗 summary (可选)
                
                news_item = {
                    'title': title,
                    'link': link,
                    'publisher': source,
                    'date': date_str,
                    'summary': '' # RSS 的摘要通常很难看，不如只看标题
                }
                clean_news.append(news_item)
                
            return clean_news
            
        except Exception as e:
            print(f"❌ RSS 获取失败: {e}")
            return []