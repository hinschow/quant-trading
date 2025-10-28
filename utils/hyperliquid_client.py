"""
Hyperliquid API客户端
用于获取资金费率和聪明钱包数据
支持自动回退到Binance（如果Hyperliquid没有该交易对）
"""

import requests
import logging
import time
from typing import Dict, Optional, List
from datetime import datetime

# 处理相对导入
try:
    from utils.data_persistence import DataPersistence
    from utils.binance_data_client import BinanceDataClient
except ImportError:
    from data_persistence import DataPersistence
    from binance_data_client import BinanceDataClient

logger = logging.getLogger(__name__)


class HyperliquidClient:
    """
    多数据源市场数据客户端
    优先使用Hyperliquid，如果不支持则自动回退到Binance
    """

    def __init__(self, base_url: str = "https://api.hyperliquid.xyz",
                 enable_persistence: bool = True,
                 enable_binance_fallback: bool = True):
        """
        初始化市场数据客户端

        Args:
            base_url: Hyperliquid API基础URL
            enable_persistence: 是否启用数据持久化
            enable_binance_fallback: 是否启用Binance备用数据源
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

        # 数据源标记（记录每个交易对使用的数据源）
        self.data_source = {}  # {symbol: 'hyperliquid' or 'binance'}

        # Binance备用数据源
        self.enable_binance_fallback = enable_binance_fallback
        if enable_binance_fallback:
            try:
                self.binance_client = BinanceDataClient()
                logger.info("✅ Binance备用数据源已启用")
            except Exception as e:
                logger.warning(f"⚠️  Binance客户端初始化失败: {e}")
                self.binance_client = None
                self.enable_binance_fallback = False
        else:
            self.binance_client = None

        # 数据持久化
        self.enable_persistence = enable_persistence
        if enable_persistence:
            self.persistence = DataPersistence()

            # 加载历史数据
            self.oi_history = self.persistence.load_oi_history(max_age_hours=24) or {}
            self.funding_history = self.persistence.load_funding_rate_history(max_age_hours=24) or {}

            logger.info(f"✅ 加载历史数据: OI={len(self.oi_history)}个交易对, "
                       f"资金费率={len(self.funding_history)}个交易对")
        else:
            self.persistence = None
            self.oi_history = {}
            self.funding_history = {}

        logger.info("✅ 市场数据客户端初始化完成")

    def _convert_symbol(self, symbol: str) -> str:
        """
        将交易所符号转换为Hyperliquid格式

        Args:
            symbol: 交易所格式的交易对（如 'BTC/USDT'）

        Returns:
            Hyperliquid格式的交易对（如 'BTC'）
        """
        return self.symbol_map.get(symbol, symbol.replace('/USDT', '').replace('USDT', ''))

    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """
        获取市场数据（资金费率 + OI + 价格）
        优先使用Hyperliquid，如果不支持则自动回退到Binance

        资金费率说明：
        - 正费率：多头支付空头（市场看多）
        - 负费率：空头支付多头（市场看空）
        - 每8小时结算一次（0:00, 8:00, 16:00 UTC）

        Args:
            symbol: 交易对符号（如 'BTC/USDT'）

        Returns:
            市场数据字典 {'funding_rate': float, 'open_interest': float, 'price': float, 'timestamp': float, 'source': str}
            获取失败返回None
        """
        # 第一步：尝试从Hyperliquid获取
        market_data = self._get_hyperliquid_data(symbol)

        if market_data is not None:
            market_data['source'] = 'hyperliquid'
            self.data_source[symbol] = 'hyperliquid'
            logger.debug(f"📊 {symbol} 使用Hyperliquid数据")
            return market_data

        # 第二步：如果Hyperliquid失败，回退到Binance
        if self.enable_binance_fallback and self.binance_client:
            logger.info(f"🔄 {symbol} 在Hyperliquid不可用，切换到Binance")
            market_data = self.binance_client.get_market_data(symbol)

            if market_data is not None:
                market_data['source'] = 'binance'
                self.data_source[symbol] = 'binance'
                logger.info(f"✅ {symbol} 使用Binance数据")
                return market_data

        # 第三步：两个数据源都失败
        logger.error(f"❌ {symbol} 无法从任何数据源获取市场数据")
        return None

    def _get_hyperliquid_data(self, symbol: str) -> Optional[Dict]:
        """
        从Hyperliquid获取市场数据（内部方法）

        Args:
            symbol: 交易对符号

        Returns:
            市场数据字典或None
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
            # [1]: 资产上下文数组，每个元素包含funding, openInterest等字段

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
                logger.debug(f"⚠️  Hyperliquid未找到 {symbol}")
                return None

            # 从资产上下文中获取数据
            if isinstance(asset_contexts, list) and asset_index < len(asset_contexts):
                asset_ctx = asset_contexts[asset_index]
                if isinstance(asset_ctx, dict):
                    funding_rate = float(asset_ctx.get('funding', 0))
                    open_interest = float(asset_ctx.get('openInterest', 0))
                    mark_price = float(asset_ctx.get('markPx', 0))

                    market_data = {
                        'funding_rate': funding_rate,
                        'open_interest': open_interest,
                        'price': mark_price,
                        'timestamp': time.time()
                    }

                    return market_data

            logger.debug(f"⚠️  Hyperliquid未找到 {symbol} 的市场数据")
            return None

        except requests.exceptions.RequestException as e:
            logger.debug(f"⚠️  Hyperliquid API调用失败: {e}")
            return None
        except (ValueError, KeyError, IndexError) as e:
            logger.debug(f"⚠️  Hyperliquid数据解析失败: {e}")
            return None

    def get_funding_rate(self, symbol: str) -> Optional[float]:
        """
        获取Hyperliquid资金费率（向后兼容）

        Args:
            symbol: 交易对符号（如 'BTC/USDT'）

        Returns:
            资金费率（小数形式，如 0.0001 = 0.01%），获取失败返回None
        """
        market_data = self.get_market_data(symbol)
        return market_data['funding_rate'] if market_data else None

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

    def _update_history(self, symbol: str, market_data: Dict) -> None:
        """
        更新历史数据并保存

        Args:
            symbol: 交易对符号
            market_data: 市场数据
        """
        # 更新OI历史
        if symbol not in self.oi_history:
            self.oi_history[symbol] = []

        self.oi_history[symbol].append({
            'timestamp': market_data['timestamp'],
            'oi': market_data['open_interest'],
            'price': market_data['price']
        })

        # 只保留最近24小时的数据
        cutoff_time = time.time() - 24 * 3600
        self.oi_history[symbol] = [
            point for point in self.oi_history[symbol]
            if point['timestamp'] > cutoff_time
        ]

        # 更新资金费率历史
        if symbol not in self.funding_history:
            self.funding_history[symbol] = []

        self.funding_history[symbol].append({
            'timestamp': market_data['timestamp'],
            'funding_rate': market_data['funding_rate']
        })

        # 只保留最近24小时的数据
        self.funding_history[symbol] = [
            point for point in self.funding_history[symbol]
            if point['timestamp'] > cutoff_time
        ]

        # 保存到磁盘
        if self.enable_persistence and self.persistence:
            try:
                self.persistence.save_oi_history(self.oi_history)
                self.persistence.save_funding_rate_history(self.funding_history)
            except Exception as e:
                logger.warning(f"⚠️  保存历史数据失败: {e}")

    def get_funding_signal(self, symbol: str) -> tuple[int, str]:
        """
        获取资金费率信号（并更新历史数据）

        Args:
            symbol: 交易对符号

        Returns:
            (调整值, 描述信息) 元组
        """
        # 获取完整市场数据（包含OI）
        market_data = self.get_market_data(symbol)

        if market_data is None:
            return (0, '')

        funding_rate = market_data['funding_rate']

        # 更新历史数据
        self._update_history(symbol, market_data)

        # 计算资金费率调整
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


class SmartMoneyTracker:
    """
    聪明钱包追踪器
    通过OI变化识别大户行为
    """

    def __init__(self, hyperliquid_client: HyperliquidClient):
        """
        初始化聪明钱包追踪器

        Args:
            hyperliquid_client: Hyperliquid客户端实例
        """
        self.client = hyperliquid_client
        logger.info("✅ 聪明钱包追踪器初始化完成")

    def get_oi_change(self, symbol: str, window_hours: float = 1.0) -> Optional[Dict]:
        """
        获取OI变化情况

        Args:
            symbol: 交易对符号
            window_hours: 时间窗口（小时）

        Returns:
            OI变化数据字典 {'oi_change_pct': float, 'price_change_pct': float, 'direction': str}
        """
        # 获取历史数据
        oi_history = self.client.oi_history.get(symbol, [])

        if len(oi_history) < 2:
            logger.debug(f"📊 {symbol} OI历史数据不足（需要至少2个数据点）")
            return None

        # 获取时间窗口内的数据
        current_time = time.time()
        cutoff_time = current_time - (window_hours * 3600)

        # 找到窗口开始时的数据点（最接近cutoff_time的数据点）
        old_data = None
        for point in oi_history:
            if point['timestamp'] >= cutoff_time:
                old_data = point
                break

        if old_data is None:
            # 如果没有窗口内的数据，使用最老的数据点
            old_data = oi_history[0]

        # 最新数据
        new_data = oi_history[-1]

        # 计算变化率
        oi_change_pct = ((new_data['oi'] - old_data['oi']) / old_data['oi'] * 100) if old_data['oi'] > 0 else 0
        price_change_pct = ((new_data['price'] - old_data['price']) / old_data['price'] * 100) if old_data['price'] > 0 else 0

        # 判断方向
        if oi_change_pct > 0 and price_change_pct > 0:
            direction = 'long'  # 大户做多
        elif oi_change_pct > 0 and price_change_pct < 0:
            direction = 'short'  # 大户做空
        elif oi_change_pct < 0 and price_change_pct > 0:
            direction = 'profit_taking'  # 获利了结
        elif oi_change_pct < 0 and price_change_pct < 0:
            direction = 'stop_loss'  # 止损离场
        else:
            direction = 'neutral'  # 无明显方向

        return {
            'oi_change_pct': oi_change_pct,
            'price_change_pct': price_change_pct,
            'direction': direction,
            'old_oi': old_data['oi'],
            'new_oi': new_data['oi'],
            'old_price': old_data['price'],
            'new_price': new_data['price'],
            'time_span_hours': (new_data['timestamp'] - old_data['timestamp']) / 3600
        }

    def calculate_smart_money_adjustment(self, oi_change: Dict) -> int:
        """
        根据OI变化计算信号强度调整值

        调整规则：
        - OI↑ + 价格↑（大户做多）：+20分（阈值：OI增长>5%，价格上涨>2%）
        - OI↑ + 价格↓（大户做空）：-20分（阈值：OI增长>5%，价格下跌>2%）
        - OI↓ + 价格↑（获利了结）：-10分（阈值：OI减少>3%，价格上涨>2%）
        - OI↓ + 价格↓（止损离场）：+5分（阈值：OI减少>3%，价格下跌>2%）
        - 其他情况：0分

        Args:
            oi_change: OI变化数据

        Returns:
            信号强度调整值（-20 ~ +20）
        """
        oi_pct = oi_change['oi_change_pct']
        price_pct = oi_change['price_change_pct']
        direction = oi_change['direction']

        # 大户做多：OI增长>5%，价格上涨>2%
        if direction == 'long' and abs(oi_pct) > 5 and abs(price_pct) > 2:
            return 20

        # 大户做空：OI增长>5%，价格下跌>2%
        elif direction == 'short' and abs(oi_pct) > 5 and abs(price_pct) > 2:
            return -20

        # 获利了结：OI减少>3%，价格上涨>2%
        elif direction == 'profit_taking' and abs(oi_pct) > 3 and abs(price_pct) > 2:
            return -10

        # 止损离场：OI减少>3%，价格下跌>2%
        elif direction == 'stop_loss' and abs(oi_pct) > 3 and abs(price_pct) > 2:
            return 5

        # 其他情况
        else:
            return 0

    def get_smart_money_signal(self, symbol: str, window_hours: float = 1.0) -> tuple[int, str]:
        """
        获取聪明钱包信号

        Args:
            symbol: 交易对符号
            window_hours: 时间窗口（小时）

        Returns:
            (调整值, 描述信息) 元组
        """
        try:
            # 获取OI变化
            oi_change = self.get_oi_change(symbol, window_hours)

            if oi_change is None:
                return (0, '')

            # 计算调整值
            adjustment = self.calculate_smart_money_adjustment(oi_change)

            # 生成描述信息
            oi_pct = oi_change['oi_change_pct']
            price_pct = oi_change['price_change_pct']
            direction = oi_change['direction']

            if adjustment == 20:
                description = f'💰 大户做多(OI↑{abs(oi_pct):.1f}%, 价格↑{abs(price_pct):.1f}%)'
            elif adjustment == -20:
                description = f'⚠️ 大户做空(OI↑{abs(oi_pct):.1f}%, 价格↓{abs(price_pct):.1f}%)'
            elif adjustment == -10:
                description = f'📉 获利了结(OI↓{abs(oi_pct):.1f}%, 价格↑{abs(price_pct):.1f}%)'
            elif adjustment == 5:
                description = f'🔄 止损离场(OI↓{abs(oi_pct):.1f}%, 价格↓{abs(price_pct):.1f}%)'
            else:
                description = f'OI变化不明显(OI{oi_pct:+.1f}%, 价格{price_pct:+.1f}%)'

            return (adjustment, description)

        except Exception as e:
            logger.warning(f"⚠️  获取聪明钱包信号失败: {e}")
            return (0, '')


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
