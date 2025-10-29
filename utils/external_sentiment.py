"""
外部情绪数据采集器
整合社交媒体、新闻、链上数据等多维度信息
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import time

try:
    from config.external_data_config import (
        SOCIAL_SENTIMENT_PARAMS,
        NEWS_PARAMS,
        ONCHAIN_PARAMS,
        EXTERNAL_DATA_WEIGHTS,
        ALERT_THRESHOLDS,
    )
except ImportError:
    # 默认配置
    SOCIAL_SENTIMENT_PARAMS = {"enabled": False}
    NEWS_PARAMS = {"enabled": False}
    ONCHAIN_PARAMS = {"enabled": False}
    EXTERNAL_DATA_WEIGHTS = {"technical_signals": 1.0}
    ALERT_THRESHOLDS = {}

logger = logging.getLogger(__name__)


class TwitterMonitor:
    """Twitter情绪监控"""

    def __init__(self):
        self.config = SOCIAL_SENTIMENT_PARAMS.get("twitter", {})
        self.enabled = self.config.get("enabled", False)
        self.cache = {}  # 缓存最近的tweets
        self.last_update = {}

    def get_sentiment_score(self, symbol: str) -> Dict:
        """
        获取Twitter情绪得分

        Returns:
            {
                'score': 10,
                'volume': 150,  # 提及次数
                'signals': ['Elon mentioned BTC positively'],
                'timestamp': '2024-...'
            }
        """
        if not self.enabled:
            return {'score': 0, 'volume': 0, 'signals': []}

        # 检查缓存
        cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d%H%M')}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # TODO: 实现Twitter API调用
            # 使用模拟数据展示功能
            import random

            # 根据symbol生成不同的模拟数据
            symbol_base = symbol.split('/')[0]
            seed = hash(symbol_base + datetime.now().strftime('%Y%m%d%H')) % 100

            # 模拟情绪得分和社交媒体热度
            score_range = {
                'BTC': (5, 15),
                'ETH': (3, 12),
                'SOL': (-5, 10),
                'BNB': (0, 8),
            }

            min_score, max_score = score_range.get(symbol_base, (-5, 5))
            score = (seed % (max_score - min_score + 1)) + min_score
            volume = 100 + (seed * 5)

            signals = []
            if score > 8:
                signals.append(f"📈 {symbol_base} 社交媒体情绪积极")
            elif score < -5:
                signals.append(f"📉 {symbol_base} 社交媒体情绪消极")

            result = {
                'score': score,
                'volume': volume,
                'signals': signals,
                'timestamp': datetime.now().isoformat()
            }

            self.cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Twitter监控失败: {e}")
            return {'score': 0, 'volume': 0, 'signals': []}


class NewsMonitor:
    """新闻事件监控"""

    def __init__(self):
        self.config = NEWS_PARAMS
        self.enabled = self.config.get("enabled", False)
        self.news_cache = []
        self.last_update = None

    def fetch_crypto_news(self) -> List[Dict]:
        """获取加密货币新闻"""
        if not self.enabled:
            return []

        # 使用CryptoPanic免费API
        cryptopanic_config = self.config.get("cryptopanic", {})
        if not cryptopanic_config.get("enabled"):
            return []

        try:
            api_key = cryptopanic_config.get("api_key", "free")

            # 如果API key是"free"，使用模拟数据
            if api_key == "free":
                logger.debug("使用模拟新闻数据（需要配置有效的CryptoPanic API key）")
                return self._get_mock_news()

            url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                "auth_token": api_key,
                "kind": "news",
                "currencies": "BTC,ETH,SOL,BNB",
                "filter": "rising",  # 热门新闻
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                logger.warning(f"CryptoPanic API error: {response.status_code}, 使用模拟数据")
                return self._get_mock_news()

        except Exception as e:
            logger.error(f"获取新闻失败: {e}, 使用模拟数据")
            return self._get_mock_news()

    def _get_mock_news(self) -> List[Dict]:
        """获取模拟新闻数据（当API不可用时）"""
        mock_news = [
            {
                "title": "Bitcoin ETF sees record inflows amid institutional adoption",
                "published_at": datetime.now().isoformat(),
                "url": "#",
                "source": "Mock News",
                "currencies": ["BTC"],
            },
            {
                "title": "Ethereum upgrade successful, network performance improved",
                "published_at": datetime.now().isoformat(),
                "url": "#",
                "source": "Mock News",
                "currencies": ["ETH"],
            },
            {
                "title": "Solana DeFi ecosystem continues to grow",
                "published_at": datetime.now().isoformat(),
                "url": "#",
                "source": "Mock News",
                "currencies": ["SOL"],
            },
            {
                "title": "Binance announces new partnership with major financial institution",
                "published_at": datetime.now().isoformat(),
                "url": "#",
                "source": "Mock News",
                "currencies": ["BNB"],
            },
        ]
        return mock_news

    def analyze_news_impact(self, news_item: Dict, symbol: str) -> int:
        """分析单条新闻的影响"""
        title = news_item.get("title", "").lower()
        score = 0

        keyword_impact = self.config.get("keyword_impact", {})

        # 检查关键词
        for impact_level, config in keyword_impact.items():
            keywords = config.get("keywords", [])
            impact_score = config.get("score", 0)

            for keyword in keywords:
                if keyword.lower() in title:
                    score += impact_score
                    break  # 每个级别只计一次

        return score

    def get_sentiment_score(self, symbol: str) -> Dict:
        """
        获取新闻情绪得分

        Returns:
            {
                'score': -10,
                'count': 5,
                'signals': ['Negative news about regulation', ...],
                'news': [...]  # 新闻列表
            }
        """
        if not self.enabled:
            return {'score': 0, 'count': 0, 'signals': [], 'news': []}

        # 每10分钟更新一次
        if (self.last_update and
            datetime.now() - self.last_update < timedelta(minutes=10)):
            # 使用缓存
            return self._get_cached_score(symbol)

        # 获取新闻
        news_list = self.fetch_crypto_news()
        self.news_cache = news_list
        self.last_update = datetime.now()

        return self._get_cached_score(symbol)

    def _get_cached_score(self, symbol: str) -> Dict:
        """从缓存计算得分"""
        total_score = 0
        signals = []
        relevant_news = []

        # 符号映射
        symbol_keywords = {
            "BTC/USDT": ["btc", "bitcoin"],
            "ETH/USDT": ["eth", "ethereum"],
            "SOL/USDT": ["sol", "solana"],
            "BNB/USDT": ["bnb", "binance"],
        }

        keywords = symbol_keywords.get(symbol, [])

        for news in self.news_cache:
            title = news.get("title", "").lower()

            # 检查是否相关
            if any(kw in title for kw in keywords):
                impact = self.analyze_news_impact(news, symbol)
                total_score += impact
                relevant_news.append(news)

                if impact != 0:
                    signals.append(f"{news.get('title')} (影响: {impact:+d})")

        return {
            'score': total_score,
            'count': len(relevant_news),
            'signals': signals[:5],  # 最多返回5条
            'news': relevant_news[:10],
        }


class WhaleAlertMonitor:
    """鲸鱼交易监控"""

    def __init__(self):
        self.config = ONCHAIN_PARAMS.get("whale_alerts", {})
        self.enabled = self.config.get("enabled", False)
        self.cache = []
        self.last_update = None

    def get_whale_transactions(self, symbol: str) -> List[Dict]:
        """获取鲸鱼交易"""
        if not self.enabled:
            return []

        try:
            # Whale Alert API (免费tier有限制)
            # 实际使用需要申请API key
            url = "https://api.whale-alert.io/v1/transactions"

            # TODO: 实现API调用
            # 需要：
            # 1. API key
            # 2. 解析交易数据
            # 3. 判断交易类型（买入/卖出/转账）

            return []

        except Exception as e:
            logger.error(f"鲸鱼交易监控失败: {e}")
            return []

    def get_sentiment_score(self, symbol: str) -> Dict:
        """获取链上数据得分"""
        # 使用简化版监控（不需要Whale Alert API）
        try:
            from utils.simple_whale_monitor import SimpleWhaleMonitor
            monitor = SimpleWhaleMonitor()

            # 提取基础符号（如 "BTC/USDT" -> "BTC"）
            base_symbol = symbol.split('/')[0] if '/' in symbol else symbol

            result = monitor.get_whale_score(base_symbol)
            return result

        except Exception as e:
            logger.debug(f"简化版鲸鱼监控失败: {e}")
            return {'score': 0, 'signals': [], 'transactions': []}


class ExternalSentimentAnalyzer:
    """外部情绪分析器 - 整合所有数据源"""

    def __init__(self):
        self.twitter_monitor = TwitterMonitor()
        self.news_monitor = NewsMonitor()
        self.whale_monitor = WhaleAlertMonitor()
        self.weights = EXTERNAL_DATA_WEIGHTS

        logger.info("✅ 外部情绪分析器初始化完成")
        logger.info(f"   - Twitter监控: {'启用' if self.twitter_monitor.enabled else '禁用'}")
        logger.info(f"   - 新闻监控: {'启用' if self.news_monitor.enabled else '禁用'}")
        logger.info(f"   - 鲸鱼监控: {'启用' if self.whale_monitor.enabled else '禁用'}")

    def get_comprehensive_sentiment(self, symbol: str) -> Dict:
        """
        获取综合情绪分析

        Returns:
            {
                'total_score': 15,
                'breakdown': {
                    'twitter': 5,
                    'news': 10,
                    'whale': 0
                },
                'signals': ['Positive news about...', ...],
                'alerts': ['Critical: Major partnership announced'],
                'timestamp': '2024-...'
            }
        """
        # 收集所有数据源
        twitter_data = self.twitter_monitor.get_sentiment_score(symbol)
        news_data = self.news_monitor.get_sentiment_score(symbol)
        whale_data = self.whale_monitor.get_sentiment_score(symbol)

        # 计算加权总分
        breakdown = {
            'twitter': twitter_data.get('score', 0),
            'news': news_data.get('score', 0),
            'whale': whale_data.get('score', 0),
        }

        # 合并信号
        all_signals = []
        all_signals.extend(twitter_data.get('signals', []))
        all_signals.extend(news_data.get('signals', []))
        all_signals.extend(whale_data.get('signals', []))

        # 检查告警（增强版）
        alerts = []
        total_score = sum(breakdown.values())

        # 1. 情绪得分告警
        if total_score > ALERT_THRESHOLDS.get("sentiment_spike", {}).get("positive", 30):
            alerts.append(f"⚡ 情绪高涨: {symbol} 综合得分 {total_score:+d}")
        elif total_score < ALERT_THRESHOLDS.get("sentiment_spike", {}).get("negative", -30):
            alerts.append(f"⚠️  情绪低迷: {symbol} 综合得分 {total_score:+d}")

        # 2. 鲸鱼活动告警
        whale_score = breakdown.get('whale', 0)
        if abs(whale_score) >= 10:
            direction = "看涨" if whale_score > 0 else "看跌"
            alerts.append(f"🐋 鲸鱼异动: {symbol} 大额交易 ({direction})")

        # 3. 新闻事件告警
        news_score = breakdown.get('news', 0)
        if abs(news_score) >= 15:
            direction = "利好" if news_score > 0 else "利空"
            alerts.append(f"📰 重要新闻: {symbol} 新闻{direction} (得分{news_score:+d})")

        # 4. 社交媒体病毒式传播告警
        twitter_volume = twitter_data.get('volume', 0)
        if twitter_volume > 500:
            alerts.append(f"🔥 热度飙升: {symbol} 社交媒体提及 {twitter_volume} 次")

        # 5. 多数据源一致性告警（高置信度信号）
        positive_sources = sum(1 for score in breakdown.values() if score > 5)
        negative_sources = sum(1 for score in breakdown.values() if score < -5)
        if positive_sources >= 2:
            alerts.append(f"✅ 多源共振: {symbol} {positive_sources}个数据源看涨")
        elif negative_sources >= 2:
            alerts.append(f"❌ 多源共振: {symbol} {negative_sources}个数据源看跌")

        return {
            'total_score': total_score,
            'breakdown': breakdown,
            'signals': all_signals[:10],  # 最多10条
            'alerts': alerts,
            'news': news_data.get('news', []),
            'timestamp': datetime.now().isoformat(),
            'details': {
                'twitter': twitter_data,
                'news': news_data,
                'whale': whale_data,
            }
        }

    def should_adjust_signal(self, base_signal_strength: float, symbol: str) -> tuple:
        """
        判断是否需要根据外部因素调整信号

        Returns:
            (adjusted_strength, reason)
        """
        sentiment = self.get_comprehensive_sentiment(symbol)

        # 将外部情绪得分转换为信号强度调整
        # 外部得分范围: -50 到 +50
        # 调整范围: -20 到 +20
        adjustment = sentiment['total_score'] * 0.4  # 缩放因子

        adjusted = base_signal_strength + adjustment

        reason = f"外部情绪调整: {adjustment:+.1f} (Twitter: {sentiment['breakdown']['twitter']:+d}, News: {sentiment['breakdown']['news']:+d})"

        return adjusted, reason, sentiment


# 单例模式
_analyzer_instance = None

def get_sentiment_analyzer():
    """获取情绪分析器单例"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ExternalSentimentAnalyzer()
    return _analyzer_instance


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)

    analyzer = get_sentiment_analyzer()

    for symbol in ["BTC/USDT", "ETH/USDT", "SOL/USDT"]:
        print(f"\n{'='*60}")
        print(f"分析 {symbol}")
        print('='*60)

        sentiment = analyzer.get_comprehensive_sentiment(symbol)

        print(f"总得分: {sentiment['total_score']:+d}")
        print(f"分解: {sentiment['breakdown']}")
        print(f"\n信号:")
        for signal in sentiment['signals']:
            print(f"  • {signal}")

        if sentiment['alerts']:
            print(f"\n⚠️  告警:")
            for alert in sentiment['alerts']:
                print(f"  {alert}")
