#!/usr/bin/env python3
"""
数据源连接测试脚本
显示交易所原始精度的价格
"""

from utils.hyperliquid_client import HyperliquidClient
from config.strategy_params import TRADING_SYMBOLS


def get_price_precision(price):
    """
    根据价格大小返回合适的精度
    """
    if price >= 1000:
        return 2  # BTC: 115163.00
    elif price >= 100:
        return 2  # SOL: 199.62
    elif price >= 10:
        return 2  # ETH: 4119.30
    elif price >= 1:
        return 4  # BNB: 1136.3000
    elif price >= 0.1:
        return 4  # 0.1-1: 0.5234
    elif price >= 0.01:
        return 5  # 0.01-0.1: 0.05234
    elif price >= 0.001:
        return 6  # 0.001-0.01: 0.005234
    else:
        return 8  # < 0.001: 0.00005234


def format_number(value, is_price=False, is_percentage=False, is_oi=False):
    """
    格式化数字显示

    Args:
        value: 数值
        is_price: 是否是价格
        is_percentage: 是否是百分比
        is_oi: 是否是持仓量
    """
    if is_percentage:
        return f"{value:.4%}"
    elif is_oi:
        # 持仓量用千位分隔符
        return f"${value:,.2f}"
    elif is_price:
        # 价格根据大小自动调整精度
        precision = get_price_precision(value)
        return f"${value:.{precision}f}"
    else:
        return str(value)


def main():
    print("🔍 测试数据源连接...\n")

    client = HyperliquidClient()

    # 统计数据源使用情况
    hyperliquid_count = 0
    binance_count = 0

    for symbol in TRADING_SYMBOLS:
        market_data = client.get_market_data(symbol)

        if market_data:
            source = market_data['source']

            # 统计
            if source == 'hyperliquid':
                hyperliquid_count += 1
            else:
                binance_count += 1

            # 显示结果
            print(f"✅ {symbol:20}")
            print(f"   数据源: {source:12}")
            print(f"   资金费率: {format_number(market_data['funding_rate'], is_percentage=True)}")
            print(f"   持仓量: {format_number(market_data['open_interest'], is_oi=True)}")
            print(f"   价格: {format_number(market_data['price'], is_price=True)}")
            print()
        else:
            print(f"❌ {symbol} 数据获取失败\n")

    # 显示统计
    print("=" * 60)
    print("📊 数据源统计")
    print("=" * 60)
    print(f"Hyperliquid: {hyperliquid_count} 个交易对")
    print(f"Binance:     {binance_count} 个交易对")
    print(f"总计:        {hyperliquid_count + binance_count} 个交易对")
    print()


if __name__ == "__main__":
    main()
