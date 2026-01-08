# data/news_provider.py
import feedparser
from datetime import datetime
import time
from textblob import TextBlob # <--- 确保导入了 TextBlob

class NewsProvider:
    def get_company_news(self, symbol: str, limit=10):
        """
        使用 Google News RSS 获取最新财经新闻，并进行 AI 情绪分析
        """
        print(f"📡 正在连接 Google News RSS 获取 {symbol} 情报...")
        
        rss_url = f"https://news.google.com/rss/search?q={symbol}+stock&hl=en-US&gl=US&ceid=US:en"
        
        try:
            feed = feedparser.parse(rss_url)
            
            clean_news = []
            if not feed.entries:
                return []

            for entry in feed.entries[:limit]:
                # 1. 先定义 title (必须在 TextBlob 之前！)
                title = entry.get('title', 'No Title')
                link = entry.get('link', '#')
                pub_date = entry.get('published', 'Recent')
                
                # 2. AI 情绪分析 (Day 12)
                try:
                    blob = TextBlob(title)
                    sentiment_score = blob.sentiment.polarity # type: ignore
                    
                    # 给个简单的标签
                    if sentiment_score > 0.1:
                        sentiment_label = "Positive"
                    elif sentiment_score < -0.1:
                        sentiment_label = "Negative"
                    else:
                        sentiment_label = "Neutral"
                except Exception:
                    # 如果分析出错，给个默认值
                    sentiment_score = 0
                    sentiment_label = "Neutral"

                # 3. 安全获取来源
                source = 'Google News'
                if 'source' in entry:
                    s_data = entry['source']
                    if isinstance(s_data, dict):
                        source = s_data.get('title', 'Google News')
                
                # 4. 清洗时间格式
                try:
                    dt_struct = entry.get('published_parsed')
                    if dt_struct:
                        # type: ignore
                        date_str = time.strftime('%Y-%m-%d %H:%M', dt_struct) # type: ignore
                    else:
                        date_str = str(pub_date)[:16]
                except:
                    date_str = str(pub_date)

                news_item = {
                    'title': title,
                    'link': link,
                    'publisher': source,
                    'date': date_str,
                    'summary': '',
                    'sentiment': sentiment_score, # 存入分数
                    'label': sentiment_label      # 存入标签
                }
                clean_news.append(news_item)
                
            return clean_news
            
        except Exception as e:
            print(f"❌ RSS 获取失败: {e}")
            return []