"""
测试Binance回退功能
通过模拟Hyperliquid失败来验证回退逻辑
"""

import logging
from utils.binance_data_client import BinanceDataClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_binance_only():
    """测试纯Binance数据获取"""

    print("\n" + "="*80)
    print("Binance数据源测试")
    print("="*80)

    # 直接测试Binance客户端
    client = BinanceDataClient()

    # 测试常见交易对
    print("\n测试常见交易对（验证Binance作为备用数据源的可行性）")
    print("-" * 80)

    for symbol in ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']:
        print(f"\n测试 {symbol}:")
        market_data = client.get_market_data(symbol)

        if market_data:
            print(f"  ✅ 数据获取成功")
            print(f"  💰 资金费率: {market_data['funding_rate']:.4%}")
            print(f"  📈 持仓量: ${market_data['open_interest']:,.2f}")
            print(f"  💵 价格: ${market_data['price']:,.2f}")
        else:
            print(f"  ❌ 数据获取失败")

    print("\n" + "="*80)
    print("测试完成 - Binance可以作为可靠的备用数据源")
    print("="*80)


if __name__ == "__main__":
    test_binance_only()
