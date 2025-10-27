#!/bin/bash
# 快速回测测试脚本

echo "=================================================="
echo "🚀 量化交易系统 - 回测引擎测试"
echo "=================================================="
echo ""

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
python3 -c "import pandas, numpy, ccxt, talib" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ 缺少依赖，请先运行: pip install -r requirements.txt"
    exit 1
fi
echo "✅ 依赖检查通过"
echo ""

# 测试配置管理工具
echo "=================================================="
echo "📋 测试1: 配置管理工具"
echo "=================================================="
python3 config_manager.py --show-presets
echo ""

# 测试回测引擎（使用较小的数据量快速测试）
echo "=================================================="
echo "📊 测试2: 回测引擎（BTC/USDT 1小时）"
echo "=================================================="
echo "⏳ 正在运行回测，请稍候..."
echo ""

python3 backtest_engine.py BTC/USDT -t 1h --limit 500 --capital 10000

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 回测完成！"
else
    echo ""
    echo "❌ 回测失败"
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ 所有测试通过！"
echo "=================================================="
echo ""
echo "📝 接下来您可以："
echo "  1. 查看交易记录: cat backtest_trades_BTC_USDT_1h.csv"
echo "  2. 回测其他币种: python3 backtest_engine.py ETH/USDT -t 4h"
echo "  3. 调整参数配置: nano config/strategy_params.py"
echo "  4. 查看参数说明: cat PARAMETER_GUIDE.md"
echo ""
