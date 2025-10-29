"""
简化版鲸鱼监控
使用公开API监控大额交易，无需Whale Alert API
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict

logger = logging.getLogger(__name__)


class SimpleWhaleMonitor:
    """
    简化版鲸鱼监控
    使用免费的区块链浏览器API
    """

    def __init__(self, etherscan_key: str = None):
        """
        初始化监控器

        Args:
            etherscan_key: Etherscan API key（可选，从.env读取）
        """
        self.session = requests.Session()

        # 从环境变量读取API keys
        if not etherscan_key:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            etherscan_key = os.getenv('ETHERSCAN_API_KEY')

        self.etherscan_key = etherscan_key

        if self.etherscan_key:
            logger.info("✅ Etherscan API已配置")
        else:
            logger.info("ℹ️  未配置Etherscan API，使用免费数据源")

    def get_etherscan_large_txs(self, min_value_eth: float = 100) -> List[Dict]:
        """
        从Etherscan获取大额ETH交易

        Args:
            min_value_eth: 最小ETH数量（默认100 ETH）

        Returns:
            大额交易列表
        """
        if not self.etherscan_key:
            logger.debug("未配置Etherscan API，跳过ETH监控")
            return []

        try:
            # 使用Etherscan API获取最近的区块
            url = "https://api.etherscan.io/api"

            # 先获取最新区块号
            params = {
                'module': 'proxy',
                'action': 'eth_blockNumber',
                'apikey': self.etherscan_key,
            }

            response = self.session.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return []

            data = response.json()
            if data.get('result'):
                latest_block = int(data['result'], 16)

                # 获取最近几个区块的交易
                # 注意：这只是示例，实际可能需要更复杂的逻辑
                logger.info(f"✅ 已连接Etherscan，最新区块: {latest_block}")

            return []  # 返回空，避免过多API调用

        except Exception as e:
            logger.debug(f"Etherscan API调用失败: {e}")
            return []

    def get_btc_large_txs(self, min_value_btc: float = 10) -> List[Dict]:
        """
        从Blockchain.com获取大额BTC交易

        Args:
            min_value_btc: 最小BTC数量

        Returns:
            交易列表
        """
        try:
            # Blockchain.com 无需API key
            url = "https://blockchain.info/unconfirmed-transactions?format=json"

            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return []

            data = response.json()
            txs = data.get('txs', [])

            large_txs = []
            for tx in txs:
                # 计算总输出（satoshi转BTC）
                total_out = sum(out.get('value', 0) for out in tx.get('out', []))
                btc_amount = total_out / 100000000  # satoshi to BTC

                if btc_amount >= min_value_btc:
                    large_txs.append({
                        'symbol': 'BTC',
                        'amount': btc_amount,
                        'hash': tx.get('hash', '')[:16] + '...',
                        'timestamp': datetime.fromtimestamp(tx.get('time', 0)).isoformat(),
                    })

            logger.info(f"✅ 获取到 {len(large_txs)} 笔BTC大额交易")
            return large_txs[:10]  # 返回前10笔

        except Exception as e:
            logger.error(f"获取BTC大额交易失败: {e}")
            return []

    def _get_mock_data(self) -> List[Dict]:
        """
        返回模拟数据（用于演示）
        实际使用时替换为真实API
        """
        now = datetime.now()

        mock_txs = [
            {
                'symbol': 'BTC',
                'amount': 150.5,
                'value_usd': 15000000,  # Dashboard API期望的字段名
                'from': 'Unknown Wallet',
                'to': 'Binance',
                'type': 'sell',  # 使用统一的类型：buy/sell/transfer
                'description': '150.50 BTC 转入交易所（看跌信号）',
                'impact': 'bearish',
                'score': -10,
                'timestamp': (now - timedelta(hours=1)).isoformat(),
            },
            {
                'symbol': 'ETH',
                'amount': 5000,
                'value_usd': 18000000,
                'from': 'Coinbase',
                'to': 'Unknown Wallet',
                'type': 'buy',  # 从交易所转出 = 买入信号
                'description': '5000 ETH 转出交易所（看涨信号）',
                'impact': 'bullish',
                'score': 10,
                'timestamp': (now - timedelta(hours=2)).isoformat(),
            },
            {
                'symbol': 'SOL',
                'amount': 50000,
                'value_usd': 8500000,
                'from': 'Unknown Wallet',
                'to': 'Unknown Wallet',
                'type': 'transfer',
                'description': '50000 SOL 钱包间转移',
                'impact': 'neutral',
                'score': 0,
                'timestamp': (now - timedelta(hours=3)).isoformat(),
            },
            {
                'symbol': 'SUI',
                'amount': 2000000,
                'value_usd': 6400000,
                'from': 'Unknown Wallet',
                'to': 'Binance',
                'type': 'sell',
                'description': '2M SUI 转入交易所',
                'impact': 'bearish',
                'score': -5,
                'timestamp': (now - timedelta(hours=4)).isoformat(),
            },
        ]

        return mock_txs

    def get_whale_score(self, symbol: str) -> Dict:
        """
        获取鲸鱼活动得分

        Args:
            symbol: 币种符号（如 "BTC"）

        Returns:
            {
                'score': -10,
                'transactions': [...],
                'signals': ['...'],
            }
        """
        if symbol == 'BTC':
            txs = self.get_btc_large_txs()
        else:
            txs = self._get_mock_data()

        # 过滤指定币种
        symbol_txs = [tx for tx in txs if tx.get('symbol', '').upper() == symbol.upper()]

        # 计算总分
        total_score = sum(tx.get('score', 0) for tx in symbol_txs)

        # 生成信号
        signals = []
        for tx in symbol_txs[:5]:
            signal = (
                f"{tx.get('amount', 0):.2f} {tx.get('symbol')} "
                f"from {tx.get('from', 'Unknown')} to {tx.get('to', 'Unknown')} "
                f"({tx.get('impact', 'neutral')})"
            )
            signals.append(signal)

        return {
            'score': total_score,
            'transactions': symbol_txs[:10],
            'signals': signals,
            'count': len(symbol_txs),
            'note': '使用简化版监控（模拟数据）',
        }


def test_simple_whale_monitor():
    """测试简化版鲸鱼监控"""
    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*70)
    print("🐋 简化版鲸鱼监控测试")
    print("="*70)

    monitor = SimpleWhaleMonitor()

    # 测试BTC监控
    print("\n尝试获取BTC大额交易（使用Blockchain.com免费API）...")
    btc_txs = monitor.get_btc_large_txs(min_value_btc=10)

    if btc_txs:
        print(f"\n✅ 获取到 {len(btc_txs)} 笔BTC大额交易\n")
        for i, tx in enumerate(btc_txs[:3], 1):
            print(f"{i}. {tx['amount']:.2f} BTC")
            print(f"   Hash: {tx['hash']}")
            print(f"   时间: {tx['timestamp']}\n")
    else:
        print("\n使用模拟数据演示...\n")

    # 测试获取鲸鱼得分
    print("="*70)
    for symbol in ['BTC', 'ETH']:
        print(f"\n分析 {symbol} 鲸鱼活动:")
        result = monitor.get_whale_score(symbol)
        print(f"  总得分: {result['score']:+d}")
        print(f"  交易数: {result['count']}")
        if result['signals']:
            print(f"  信号:")
            for signal in result['signals']:
                print(f"    • {signal}")

    print("\n" + "="*70)
    print("💡 提示:")
    print("   - 当前使用简化版监控（部分模拟数据）")
    print("   - 如需真实数据，可注册 Etherscan API（免费）")
    print("   - 或等待 Whale Alert 恢复免费tier")
    print("="*70)


if __name__ == "__main__":
    test_simple_whale_monitor()
