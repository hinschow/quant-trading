#!/usr/bin/env python3
"""
数据源连接测试脚本（精确版）
显示交易所返回的原始精度
"""

from utils.hyperliquid_client import HyperliquidClient
from config.strategy_params import TRADING_SYMBOLS


def main():
    print("🔍 测试数据源连接（精确价格显示）...\n")

    client = HyperliquidClient()

    # 统计数据源使用情况
    hyperliquid_count = 0
    binance_count = 0

    for symbol in TRADING_SYMBOLS:
        market_data = client.get_market_data(symbol)

        if market_data:
            source = market_data['source']
            price = market_data['price']
            funding_rate = market_data['funding_rate']
            oi = market_data['open_interest']

            # 统计
            if source == 'hyperliquid':
                hyperliquid_count += 1
            else:
                binance_count += 1

            # 自动检测价格精度（保留所有有效数字）
            price_str = str(price)

            # 显示结果
            print(f"✅ {symbol:20}")
            print(f"   数据源:   {source:12}")
            print(f"   资金费率: {funding_rate:.6%}")  # 6位精度
            print(f"   持仓量:   ${oi:,.8f}".rstrip('0').rstrip('.'))  # 去除尾部零
            print(f"   价格:     ${price_str}")  # 显示原始价格字符串
            print()
        else:
            print(f"❌ {symbol} 数据获取失败\n")

    # 显示统计
    print("=" * 80)
    print("📊 数据源统计")
    print("=" * 80)
    print(f"🟦 Hyperliquid: {hyperliquid_count} 个交易对")
    print(f"🟨 Binance:     {binance_count} 个交易对")
    print(f"📈 总计:        {hyperliquid_count + binance_count} 个交易对")
    print()

    # 显示数据源分布
    if hyperliquid_count > 0 or binance_count > 0:
        print("💡 说明:")
        print("  - Hyperliquid优先: 去中心化交易所，支持聪明钱包追踪")
        print("  - Binance备用: Hyperliquid不支持时自动切换")
        print()


if __name__ == "__main__":
    main()
