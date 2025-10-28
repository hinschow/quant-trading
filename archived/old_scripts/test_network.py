#!/usr/bin/env python3
"""网络连接诊断工具"""
import ccxt

exchanges_to_test = ['binance', 'okx', 'bybit']

print("🔍 测试各交易所连接状态...\n")

for exchange_name in exchanges_to_test:
    try:
        print(f"测试 {exchange_name}...", end=' ')
        exchange = getattr(ccxt, exchange_name)({
            'timeout': 10000,
            'enableRateLimit': True
        })
        markets = exchange.load_markets()
        ticker = exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        print(f"✅ 成功 (BTC价格: ${price:,.2f})")
    except Exception as e:
        print(f"❌ 失败: {str(e)[:80]}")

print("\n💡 建议:")
print("- 如果币安失败，使用 --proxy 参数或切换到其他交易所")
print("- 如果 OKX 成功，推荐使用: python signal_analyzer.py BTC/USDT -e okx")
