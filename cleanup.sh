#!/bin/bash
# 清理和整理项目文件

set -e

echo "========================================================================"
echo "项目清理和整理工具"
echo "========================================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 显示当前状态
echo "当前文件状态:"
echo "----------------------------------------"
echo "Python 缓存:"
find . -type d -name "__pycache__" | wc -l
echo ""
echo "备份文件:"
find config -name "*backup*.py" 2>/dev/null | wc -l || echo "0"
echo ""
echo "根目录 CSV 文件:"
find . -maxdepth 1 -name "*.csv" | wc -l
echo ""

# 询问确认
echo "========================================================================"
echo "将执行以下操作:"
echo "========================================================================"
echo ""
echo "1. 删除 Python 缓存 (__pycache__, *.pyc)"
echo "2. 删除配置备份文件 (config/*backup*.py)"
echo "3. 删除临时文件 (.last_backup)"
echo "4. 移动根目录 CSV 到 backtest_results/"
echo "5. 清理旧的无效结果 (v4_invalid)"
echo ""
echo -n "是否继续？(y/n): "
read -r response

if [ "$response" != "y" ]; then
    echo "取消清理"
    exit 0
fi

echo ""
echo "========================================================================"
echo "开始清理..."
echo "========================================================================"
echo ""

# 1. 清理 Python 缓存
echo "1. 清理 Python 缓存..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo -e "${GREEN}✓${NC} Python 缓存已清理"
echo ""

# 2. 清理配置备份
echo "2. 清理配置备份..."
rm -f config/*backup*.py 2>/dev/null || true
rm -f .last_backup 2>/dev/null || true
echo -e "${GREEN}✓${NC} 配置备份已清理"
echo ""

# 3. 移动 CSV 文件
echo "3. 整理回测结果..."
mkdir -p backtest_results/misc
csv_count=0
for file in backtest_trades_*.csv; do
    if [ -f "$file" ]; then
        mv "$file" backtest_results/misc/
        csv_count=$((csv_count + 1))
        echo "  移动: $file"
    fi
done
if [ $csv_count -gt 0 ]; then
    echo -e "${GREEN}✓${NC} 已移动 $csv_count 个 CSV 文件到 backtest_results/misc/"
else
    echo -e "${YELLOW}○${NC} 根目录没有 CSV 文件"
fi
echo ""

# 4. 清理无效结果
echo "4. 清理无效回测结果..."
if [ -d "backtest_results/v4_invalid" ]; then
    rm -rf backtest_results/v4_invalid
    echo -e "${GREEN}✓${NC} 已删除 v4_invalid 目录"
else
    echo -e "${YELLOW}○${NC} v4_invalid 目录不存在"
fi
echo ""

# 5. 显示清理后状态
echo "========================================================================"
echo "清理完成！"
echo "========================================================================"
echo ""
echo "当前目录结构:"
echo "----------------------------------------"
tree -L 2 -I '__pycache__|*.pyc|venv|env' backtest_results 2>/dev/null || ls -la backtest_results/
echo ""

echo "下一步建议:"
echo "  1. 提交清理后的结构: git add .gitignore backtest_results/"
echo "  2. 运行回测: python3 run_backtest_all.py"
echo "  3. 分析结果: python3 analyze_backtest_v2.py"
echo ""
