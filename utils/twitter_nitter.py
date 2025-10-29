"""
使用Nitter（Twitter免费镜像）获取推文
无需API key，完全免费
"""

import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)


class NitterClient:
    """
    Nitter客户端 - Twitter免费镜像
    官网：https://nitter.net/
    """

    def __init__(self):
        # Nitter公共实例列表（可能需要轮换）
        self.instances = [
            "https://nitter.net",
            "https://nitter.1d4.us",
            "https://nitter.kavin.rocks",
            "https://nitter.unixfox.eu",
            "https://nitter.eu",
        ]
        self.current_instance = self.instances[0]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def search_tweets(self, query: str, limit: int = 20) -> List[Dict]:
        """
        搜索推文

        Args:
            query: 搜索关键词，如 "BTC OR Bitcoin"
            limit: 返回数量

        Returns:
            [{
                'text': '推文内容',
                'author': '作者',
                'time': '时间',
                'likes': 点赞数,
                'retweets': 转发数,
            }]
        """
        try:
            url = f"{self.current_instance}/search"
            params = {
                'f': 'tweets',
                'q': query,
            }

            response = self.session.get(url, params=params, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Nitter请求失败: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            tweets = []

            # 解析推文
            timeline = soup.find_all('div', class_='timeline-item', limit=limit)

            for item in timeline:
                try:
                    # 提取推文内容
                    content_div = item.find('div', class_='tweet-content')
                    if not content_div:
                        continue

                    text = content_div.get_text(strip=True)

                    # 提取作者
                    username = item.find('a', class_='username')
                    author = username.get_text(strip=True) if username else 'Unknown'

                    # 提取时间
                    date_elem = item.find('span', class_='tweet-date')
                    tweet_time = date_elem.get_text(strip=True) if date_elem else ''

                    # 提取互动数据
                    stats = item.find('div', class_='tweet-stats')
                    likes = 0
                    retweets = 0

                    if stats:
                        like_elem = stats.find('span', class_='icon-heart')
                        if like_elem and like_elem.parent:
                            likes_text = like_elem.parent.get_text(strip=True)
                            likes = self._parse_number(likes_text)

                        rt_elem = stats.find('span', class_='icon-retweet')
                        if rt_elem and rt_elem.parent:
                            rt_text = rt_elem.parent.get_text(strip=True)
                            retweets = self._parse_number(rt_text)

                    tweets.append({
                        'text': text,
                        'author': author,
                        'time': tweet_time,
                        'likes': likes,
                        'retweets': retweets,
                        'score': likes + retweets * 2,  # 简单权重
                    })

                except Exception as e:
                    logger.debug(f"解析单条推文失败: {e}")
                    continue

            logger.info(f"✅ 获取到 {len(tweets)} 条推文（关键词: {query}）")
            return tweets

        except Exception as e:
            logger.error(f"Nitter搜索失败: {e}")
            return []

    def get_user_tweets(self, username: str, limit: int = 10) -> List[Dict]:
        """
        获取指定用户的最新推文

        Args:
            username: Twitter用户名（不含@）
            limit: 数量

        Returns:
            推文列表
        """
        try:
            url = f"{self.current_instance}/{username}"

            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                logger.warning(f"获取用户推文失败: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            tweets = []

            timeline = soup.find_all('div', class_='timeline-item', limit=limit)

            for item in timeline:
                try:
                    content_div = item.find('div', class_='tweet-content')
                    if not content_div:
                        continue

                    text = content_div.get_text(strip=True)

                    date_elem = item.find('span', class_='tweet-date')
                    tweet_time = date_elem.get_text(strip=True) if date_elem else ''

                    tweets.append({
                        'text': text,
                        'author': username,
                        'time': tweet_time,
                    })

                except Exception as e:
                    logger.debug(f"解析用户推文失败: {e}")
                    continue

            logger.info(f"✅ 获取 @{username} 的 {len(tweets)} 条推文")
            return tweets

        except Exception as e:
            logger.error(f"获取用户推文失败: {e}")
            return []

    def analyze_sentiment(self, tweets: List[Dict]) -> int:
        """
        简单情绪分析

        Returns:
            情绪得分（-100 到 +100）
        """
        if not tweets:
            return 0

        positive_words = ['bullish', 'moon', 'pump', 'buy', 'long', 'up', 'green',
                         'breakthrough', 'adoption', 'partnership', 'upgrade']
        negative_words = ['bearish', 'dump', 'crash', 'sell', 'short', 'down', 'red',
                         'scam', 'hack', 'ban', 'regulation', 'lawsuit']

        total_score = 0

        for tweet in tweets:
            text = tweet.get('text', '').lower()
            tweet_score = 0

            # 统计正负面词汇
            for word in positive_words:
                if word in text:
                    tweet_score += 1

            for word in negative_words:
                if word in text:
                    tweet_score -= 1

            # 根据互动量加权
            weight = 1 + (tweet.get('likes', 0) + tweet.get('retweets', 0)) / 1000
            total_score += tweet_score * weight

        # 归一化到 -100 到 100
        normalized = int(total_score / len(tweets) * 10)
        return max(-100, min(100, normalized))

    def _parse_number(self, text: str) -> int:
        """解析数字（支持K、M等单位）"""
        try:
            text = text.strip().upper()
            if 'K' in text:
                return int(float(text.replace('K', '')) * 1000)
            elif 'M' in text:
                return int(float(text.replace('M', '')) * 1000000)
            else:
                return int(text.replace(',', ''))
        except:
            return 0


def get_crypto_sentiment(symbol: str) -> Dict:
    """
    获取加密货币的Twitter情绪

    Args:
        symbol: 如 "BTC/USDT"

    Returns:
        {
            'score': 15,
            'tweets_count': 20,
            'signals': ['...'],
        }
    """
    client = NitterClient()

    # 构建搜索查询
    crypto_map = {
        'BTC': 'BTC OR Bitcoin',
        'ETH': 'ETH OR Ethereum',
        'SOL': 'SOL OR Solana',
        'BNB': 'BNB OR Binance',
    }

    base_symbol = symbol.split('/')[0]
    query = crypto_map.get(base_symbol, base_symbol)

    # 搜索推文
    tweets = client.search_tweets(query, limit=20)

    if not tweets:
        return {'score': 0, 'tweets_count': 0, 'signals': []}

    # 分析情绪
    sentiment_score = client.analyze_sentiment(tweets)

    # 提取关键信号
    signals = []
    for tweet in tweets[:5]:  # 前5条
        if tweet.get('likes', 0) > 100 or tweet.get('retweets', 0) > 50:
            signals.append(f"@{tweet['author']}: {tweet['text'][:100]}...")

    return {
        'score': sentiment_score,
        'tweets_count': len(tweets),
        'signals': signals,
        'top_tweets': tweets[:5],
    }


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*60)
    print("测试 Nitter Twitter 数据采集")
    print("="*60)

    for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        print(f"\n分析 {symbol}:")
        result = get_crypto_sentiment(symbol)
        print(f"  情绪得分: {result['score']:+d}")
        print(f"  推文数量: {result['tweets_count']}")
        if result['signals']:
            print(f"  关键信号:")
            for signal in result['signals']:
                print(f"    • {signal}")
