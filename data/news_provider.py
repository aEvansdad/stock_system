# data/news_provider.py
from duckduckgo_search import DDGS
from datetime import datetime

class NewsProvider:
    def get_company_news(self, symbol: str, limit=10):
        """
        使用 DuckDuckGo 搜索该股票的最新财经新闻
        """
        print(f"🕵️ 正在搜索 {symbol} 的新闻情报...")
        try:
            # 搜索关键词：股票代码 + stock + news
            keywords = f"{symbol} stock news"
            
            # 使用 DDGS 获取新闻
            # region="us-en" 确保搜到的是英文原版财经消息
            results = DDGS().news(keywords=keywords, region="us-en", safesearch="off", max_results=limit)
            
            clean_news = []
            if not results:
                return []

            for item in results:
                # DDGS 返回结构: {'date':..., 'title':..., 'body':..., 'url':..., 'source':...}
                news_item = {
                    'title': item.get('title', 'No Title'),
                    'link': item.get('url', '#'),
                    'publisher': item.get('source', 'Unknown'),
                    'date': item.get('date', 'Recent'), # 返回的是相对时间比如 "2 hours ago"
                    'summary': item.get('body', '')     # 新闻摘要
                }
                clean_news.append(news_item)
                
            return clean_news
            
        except Exception as e:
            print(f"❌ 新闻获取失败: {e}")
            return []