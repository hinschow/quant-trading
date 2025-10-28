"""
测试多数据源切换功能
测试Hyperliquid -> Binance的自动回退
"""

import logging
from utils.hyperliquid_client import HyperliquidClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_multi_source():
    """测试多数据源支持"""

    print("\n" + "="*80)
    print("多数据源切换测试")
    print("="*80)

    # 初始化客户端（启用Binance备用数据源）
    client = HyperliquidClient(enable_persistence=False, enable_binance_fallback=True)

    # 测试1：Hyperliquid支持的交易对（BTC, ETH, SOL）
    print("\n测试1：Hyperliquid支持的交易对")
    print("-" * 80)

    for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        print(f"\n测试 {symbol}:")
        market_data = client.get_market_data(symbol)

        if market_data:
            print(f"  ✅ 数据获取成功")
            print(f"  📊 数据源: {market_data['source']}")
            print(f"  💰 资金费率: {market_data['funding_rate']:.4%}")
            print(f"  📈 持仓量: ${market_data['open_interest']:,.2f}")
            print(f"  💵 价格: ${market_data['price']:,.2f}")
        else:
            print(f"  ❌ 数据获取失败")

    # 测试2：Hyperliquid不支持的交易对（会回退到Binance）
    print("\n\n测试2：测试不常见交易对（可能只在Binance有）")
    print("-" * 80)

    # 注意：如果这些交易对在Hyperliquid也有，会优先使用Hyperliquid
    test_symbols = ['DOGE/USDT', 'XRP/USDT', 'ADA/USDT']

    for symbol in test_symbols:
        print(f"\n测试 {symbol}:")
        market_data = client.get_market_data(symbol)

        if market_data:
            print(f"  ✅ 数据获取成功")
            print(f"  📊 数据源: {market_data['source']}")
            print(f"  💰 资金费率: {market_data['funding_rate']:.4%}")
            print(f"  📈 持仓量: ${market_data['open_interest']:,.2f}")
            print(f"  💵 价格: ${market_data['price']:,.2f}")
        else:
            print(f"  ❌ 数据获取失败")

    # 测试3：显示数据源统计
    print("\n\n测试3：数据源使用统计")
    print("-" * 80)

    hyperliquid_count = sum(1 for source in client.data_source.values() if source == 'hyperliquid')
    binance_count = sum(1 for source in client.data_source.values() if source == 'binance')

    print(f"Hyperliquid数据源: {hyperliquid_count} 个交易对")
    print(f"Binance数据源: {binance_count} 个交易对")

    print("\n详细列表:")
    for symbol, source in client.data_source.items():
        emoji = "🟦" if source == "hyperliquid" else "🟨"
        print(f"  {emoji} {symbol:12} -> {source}")

    print("\n" + "="*80)
    print("测试完成")
    print("="*80)


if __name__ == "__main__":
    test_multi_source()
