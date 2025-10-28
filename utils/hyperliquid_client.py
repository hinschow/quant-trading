"""
Hyperliquid API客户端
用于获取资金费率和聪明钱包数据
"""

import requests
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HyperliquidClient:
    """Hyperliquid数据采集客户端"""

    def __init__(self, base_url: str = "https://api.hyperliquid.xyz"):
        """
        初始化Hyperliquid客户端

        Args:
            base_url: Hyperliquid API基础URL
        """
        self.base_url = base_url
        self.info_url = f"{base_url}/info"

        # 交易对映射：将交易所格式转换为Hyperliquid格式
        self.symbol_map = {
            'BTC/USDT': 'BTC',
            'ETH/USDT': 'ETH',
            'SOL/USDT': 'SOL',
            'BTCUSDT': 'BTC',
            'ETHUSDT': 'ETH',
            'SOLUSDT': 'SOL',
        }

        logger.info("✅ Hyperliquid客户端初始化完成")

    def _convert_symbol(self, symbol: str) -> str:
        """
        将交易所符号转换为Hyperliquid格式

        Args:
            symbol: 交易所格式的交易对（如 'BTC/USDT'）

        Returns:
            Hyperliquid格式的交易对（如 'BTC'）
        """
        return self.symbol_map.get(symbol, symbol.replace('/USDT', '').replace('USDT', ''))

    def get_funding_rate(self, symbol: str) -> Optional[float]:
        """
        获取Hyperliquid资金费率

        资金费率说明：
        - 正费率：多头支付空头（市场看多）
        - 负费率：空头支付多头（市场看空）
        - 每8小时结算一次（0:00, 8:00, 16:00 UTC）
        - 费率单位：年化百分比的1/3（因为每天3次结算）

        Args:
            symbol: 交易对符号（如 'BTC/USDT'）

        Returns:
            资金费率（小数形式，如 0.0001 = 0.01%），获取失败返回None
        """
        hl_symbol = self._convert_symbol(symbol)

        try:
            payload = {
                "type": "metaAndAssetCtxs"
            }

            response = requests.post(self.info_url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Hyperliquid API返回格式：
            # [0]: metadata (universe, marginTables等)
            # [1]: 资产上下文数组，每个元素包含funding等字段

            if not isinstance(data, list) or len(data) < 2:
                logger.error(f"❌ Hyperliquid API返回格式异常")
                return None

            # 获取metadata和资产上下文
            metadata = data[0]
            asset_contexts = data[1]

            # 从metadata中找到币种的索引
            universe = metadata.get('universe', [])
            asset_index = None

            for idx, asset_info in enumerate(universe):
                if asset_info.get('name') == hl_symbol:
                    asset_index = idx
                    break

            if asset_index is None:
                logger.warning(f"⚠️  未找到 {symbol} 的交易对信息")
                return None

            # 从资产上下文中获取funding费率
            if isinstance(asset_contexts, list) and asset_index < len(asset_contexts):
                asset_ctx = asset_contexts[asset_index]
                if isinstance(asset_ctx, dict) and 'funding' in asset_ctx:
                    funding_rate = float(asset_ctx['funding'])
                    logger.info(f"📊 {symbol} 资金费率: {funding_rate:.4%}")
                    return funding_rate

            logger.warning(f"⚠️  未找到 {symbol} 的资金费率数据")
            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 获取Hyperliquid资金费率失败: {e}")
            return None
        except (ValueError, KeyError, IndexError) as e:
            logger.error(f"❌ 解析Hyperliquid数据失败: {e}")
            return None

    def get_all_funding_rates(self) -> Dict[str, float]:
        """
        获取所有交易对的资金费率

        Returns:
            交易对到资金费率的字典
        """
        funding_rates = {}

        try:
            payload = {
                "type": "metaAndAssetCtxs"
            }

            response = requests.post(self.info_url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, list) or len(data) < 2:
                logger.error(f"❌ Hyperliquid API返回格式异常")
                return {}

            # 获取metadata和资产上下文
            metadata = data[0]
            asset_contexts = data[1]
            universe = metadata.get('universe', [])

            # 遍历所有资产
            for idx, asset_info in enumerate(universe):
                symbol = asset_info.get('name')
                if symbol and idx < len(asset_contexts):
                    asset_ctx = asset_contexts[idx]
                    if isinstance(asset_ctx, dict) and 'funding' in asset_ctx:
                        funding_rate = float(asset_ctx['funding'])
                        funding_rates[symbol] = funding_rate

            logger.info(f"✅ 获取到 {len(funding_rates)} 个交易对的资金费率")
            return funding_rates

        except Exception as e:
            logger.error(f"❌ 获取所有资金费率失败: {e}")
            return {}

    def calculate_funding_adjustment(self, funding_rate: float) -> int:
        """
        根据资金费率计算信号强度调整值

        调整规则：
        - 资金费率 > 0.015 (1.5%)：极度贪婪，-15分
        - 资金费率 > 0.01 (1%)：贪婪，-10分
        - 资金费率 > 0.005 (0.5%)：偏热，-5分
        - 资金费率 -0.005 ~ 0.005：正常，0分
        - 资金费率 < -0.005：偏冷，+5分
        - 资金费率 < -0.01：恐慌，+10分
        - 资金费率 < -0.015：极度恐慌，+15分

        Args:
            funding_rate: 资金费率

        Returns:
            信号强度调整值（-15 ~ +15）
        """
        if funding_rate is None:
            return 0

        # 极度贪婪
        if funding_rate > 0.015:
            return -15
        # 贪婪
        elif funding_rate > 0.01:
            return -10
        # 偏热
        elif funding_rate > 0.005:
            return -5
        # 正常
        elif funding_rate >= -0.005:
            return 0
        # 偏冷
        elif funding_rate >= -0.01:
            return 5
        # 恐慌
        elif funding_rate >= -0.015:
            return 10
        # 极度恐慌
        else:
            return 15

    def get_funding_signal(self, symbol: str) -> tuple[int, str]:
        """
        获取资金费率信号

        Args:
            symbol: 交易对符号

        Returns:
            (调整值, 描述信息) 元组
        """
        funding_rate = self.get_funding_rate(symbol)

        if funding_rate is None:
            return (0, '')

        adjustment = self.calculate_funding_adjustment(funding_rate)

        # 生成描述信息
        if adjustment > 0:
            description = f'✅ 负费率反转机会(资金费率:{funding_rate:.3%})'
        elif adjustment < 0:
            if funding_rate > 0.015:
                description = f'⚠️⚠️ 资金费率极高(资金费率:{funding_rate:.3%})'
            elif funding_rate > 0.01:
                description = f'⚠️ 资金费率过高(资金费率:{funding_rate:.3%})'
            else:
                description = f'注意: 资金费率偏高(资金费率:{funding_rate:.3%})'
        else:
            description = f'资金费率正常(资金费率:{funding_rate:.3%})'

        return (adjustment, description)


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建客户端
    client = HyperliquidClient()

    # 测试获取单个资金费率
    print("\n" + "="*60)
    print("测试1：获取单个交易对资金费率")
    print("="*60)

    for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        funding_rate = client.get_funding_rate(symbol)
        if funding_rate is not None:
            adjustment = client.calculate_funding_adjustment(funding_rate)
            print(f"{symbol:12} 资金费率: {funding_rate:7.4%}  调整: {adjustment:+3}分")

    # 测试获取所有资金费率
    print("\n" + "="*60)
    print("测试2：获取所有交易对资金费率")
    print("="*60)

    all_rates = client.get_all_funding_rates()
    print(f"获取到 {len(all_rates)} 个交易对的资金费率")

    # 显示前10个
    for i, (symbol, rate) in enumerate(list(all_rates.items())[:10]):
        print(f"{symbol:12} {rate:7.4%}")

    # 测试获取资金费率信号
    print("\n" + "="*60)
    print("测试3：获取资金费率信号")
    print("="*60)

    for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        adjustment, description = client.get_funding_signal(symbol)
        print(f"{symbol:12} {adjustment:+3}分  {description}")
