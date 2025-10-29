"""
Whale Alert API 客户端
监控区块链大额交易（鲸鱼活动）
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)


class WhaleAlertClient:
    """
    Whale Alert API客户端
    官网：https://whale-alert.io/
    文档：https://docs.whale-alert.io/
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端

        Args:
            api_key: Whale Alert API key（免费申请）
                    如果为None，从环境变量读取 WHALE_ALERT_API_KEY
        """
        self.api_key = api_key or self._get_api_key_from_env()
        self.base_url = "https://api.whale-alert.io/v1"
        self.session = requests.Session()

        # 免费限制：10次/分钟
        self.rate_limit = 10
        self.rate_window = 60  # 秒
        self.request_times = []

    def _get_api_key_from_env(self) -> Optional[str]:
        """从环境变量或配置读取API key"""
        import os
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.getenv('WHALE_ALERT_API_KEY')

        if not api_key:
            logger.warning("⚠️  未配置 Whale Alert API key")
            logger.info("请访问 https://whale-alert.io/ 申请免费API")

        return api_key

    def _check_rate_limit(self):
        """检查速率限制（10次/分钟）"""
        now = time.time()

        # 清理60秒前的记录
        self.request_times = [t for t in self.request_times if now - t < self.rate_window]

        # 检查是否超限
        if len(self.request_times) >= self.rate_limit:
            sleep_time = self.rate_window - (now - self.request_times[0]) + 1
            if sleep_time > 0:
                logger.info(f"速率限制，等待 {sleep_time:.1f} 秒...")
                time.sleep(sleep_time)
                self.request_times = []

        self.request_times.append(now)

    def get_transactions(self,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        min_value: int = 500000,
                        currency: str = 'usd') -> List[Dict]:
        """
        获取大额交易记录

        Args:
            start_time: 开始时间（默认1小时前）
            end_time: 结束时间（默认现在）
            min_value: 最小金额（默认50万美元）
            currency: 计价货币（usd/btc/eth）

        Returns:
            交易列表
        """
        if not self.api_key:
            logger.error("❌ 缺少 Whale Alert API key")
            return []

        # 默认查询最近1小时
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(hours=1)

        # 转换为时间戳
        start_ts = int(start_time.timestamp())
        end_ts = int(end_time.timestamp())

        # 检查速率限制
        self._check_rate_limit()

        try:
            url = f"{self.base_url}/transactions"
            params = {
                'api_key': self.api_key,
                'start': start_ts,
                'end': end_ts,
                'min_value': min_value,
                'currency': currency,
            }

            response = self.session.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                transactions = data.get('transactions', [])
                logger.info(f"✅ 获取到 {len(transactions)} 笔大额交易")
                return transactions

            elif response.status_code == 429:
                logger.warning("⚠️  API速率限制")
                return []

            else:
                logger.error(f"API请求失败: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"获取交易失败: {e}")
            return []

    def analyze_transaction(self, tx: Dict) -> Dict:
        """
        分析单笔交易的影响

        Returns:
            {
                'symbol': 'BTC',
                'amount': 150.5,
                'amount_usd': 10000000,
                'type': 'exchange_inflow',  # 或 exchange_outflow, transfer
                'impact': 'bearish',  # bearish/bullish/neutral
                'score': -15,
                'from': 'unknown wallet',
                'to': 'Binance',
                'timestamp': '2024-...',
            }
        """
        symbol = tx.get('symbol', 'UNKNOWN')
        amount = float(tx.get('amount', 0))
        amount_usd = float(tx.get('amount_usd', 0))

        from_owner = tx.get('from', {}).get('owner', 'unknown')
        to_owner = tx.get('to', {}).get('owner', 'unknown')

        # 判断交易类型
        tx_type = 'transfer'
        impact = 'neutral'
        score = 0

        # 转入交易所 = 卖压（bearish）
        if 'exchange' in to_owner.lower() or 'binance' in to_owner.lower():
            tx_type = 'exchange_inflow'
            impact = 'bearish'
            score = -10 if amount_usd > 1000000 else -5  # 100万美元以上 -10分

        # 转出交易所 = 囤币（bullish）
        elif 'exchange' in from_owner.lower() or 'binance' in from_owner.lower():
            tx_type = 'exchange_outflow'
            impact = 'bullish'
            score = 10 if amount_usd > 1000000 else 5

        # 鲸鱼间转账
        elif 'unknown' in from_owner.lower() and 'unknown' in to_owner.lower():
            if amount_usd > 5000000:  # 500万美元以上才关注
                tx_type = 'whale_transfer'
                impact = 'neutral'
                score = 0

        return {
            'symbol': symbol,
            'amount': amount,
            'amount_usd': amount_usd,
            'type': tx_type,
            'impact': impact,
            'score': score,
            'from': from_owner,
            'to': to_owner,
            'timestamp': datetime.fromtimestamp(tx.get('timestamp', 0)).isoformat(),
            'hash': tx.get('hash', '')[:16] + '...',  # 简化哈希
        }

    def get_crypto_whale_score(self, symbol: str) -> Dict:
        """
        获取指定加密货币的鲸鱼活动得分

        Args:
            symbol: 如 "BTC", "ETH"

        Returns:
            {
                'score': -15,
                'transactions': [...],
                'signals': ['150 BTC transferred to Binance (bearish)'],
            }
        """
        # 获取最近1小时的交易
        transactions = self.get_transactions()

        if not transactions:
            return {'score': 0, 'transactions': [], 'signals': []}

        # 过滤指定币种
        symbol_txs = [tx for tx in transactions if tx.get('symbol', '').upper() == symbol.upper()]

        # 分析每笔交易
        total_score = 0
        signals = []

        for tx in symbol_txs:
            analysis = self.analyze_transaction(tx)
            total_score += analysis['score']

            if abs(analysis['score']) >= 5:  # 重要交易
                signal = (
                    f"{analysis['amount']:.2f} {analysis['symbol']} "
                    f"from {analysis['from']} to {analysis['to']} "
                    f"({analysis['impact']}, {analysis['score']:+d})"
                )
                signals.append(signal)

        return {
            'score': total_score,
            'transactions': [self.analyze_transaction(tx) for tx in symbol_txs[:10]],
            'signals': signals[:5],  # 最多5条
            'count': len(symbol_txs),
        }


def test_whale_alert():
    """测试 Whale Alert API"""
    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*70)
    print("🐋 Whale Alert API 测试")
    print("="*70)

    client = WhaleAlertClient()

    if not client.api_key:
        print("\n⚠️  未配置API key")
        print("\n请按以下步骤获取：")
        print("1. 访问: https://whale-alert.io/")
        print("2. 注册账号")
        print("3. 进入 Dashboard > API")
        print("4. 创建新的 API key")
        print("5. 配置到 .env 文件:")
        print("   WHALE_ALERT_API_KEY=your_api_key_here")
        return

    # 测试获取交易
    print("\n获取最近1小时的大额交易...")
    transactions = client.get_transactions(min_value=1000000)  # 100万美元以上

    if transactions:
        print(f"\n✅ 找到 {len(transactions)} 笔大额交易\n")

        for i, tx in enumerate(transactions[:5], 1):
            analysis = client.analyze_transaction(tx)
            print(f"{i}. {analysis['symbol']}: {analysis['amount']:.2f} "
                  f"(${analysis['amount_usd']:,.0f})")
            print(f"   {analysis['from']} → {analysis['to']}")
            print(f"   类型: {analysis['type']}, 影响: {analysis['impact']} "
                  f"({analysis['score']:+d}分)\n")
    else:
        print("\n暂无大额交易")

    # 测试单个币种
    print("\n" + "="*70)
    for symbol in ['BTC', 'ETH']:
        print(f"\n分析 {symbol} 鲸鱼活动:")
        result = client.get_crypto_whale_score(symbol)
        print(f"  总得分: {result['score']:+d}")
        print(f"  交易数: {result['count']}")
        if result['signals']:
            print(f"  关键信号:")
            for signal in result['signals']:
                print(f"    • {signal}")


if __name__ == "__main__":
    test_whale_alert()
