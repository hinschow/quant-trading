#!/bin/bash
# 快速优化配置切换脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================================"
echo "量化交易策略优化工具 v4.0"
echo "========================================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查文件
check_files() {
    if [ ! -f "config/strategy_params.py" ]; then
        echo -e "${RED}❌ 错误: config/strategy_params.py 不存在${NC}"
        exit 1
    fi

    if [ ! -f "config/strategy_params_optimized.py" ]; then
        echo -e "${RED}❌ 错误: config/strategy_params_optimized.py 不存在${NC}"
        exit 1
    fi
}

# 备份当前配置
backup_config() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="config/strategy_params_backup_${TIMESTAMP}.py"

    cp config/strategy_params.py "$BACKUP_FILE"
    echo -e "${GREEN}✅ 当前配置已备份至: $BACKUP_FILE${NC}"
    echo "$BACKUP_FILE" > .last_backup
}

# 应用优化配置
apply_optimized() {
    echo ""
    echo -e "${BLUE}正在应用优化配置...${NC}"
    cp config/strategy_params_optimized.py config/strategy_params.py
    echo -e "${GREEN}✅ 优化配置已应用${NC}"
}

# 恢复原配置
restore_config() {
    if [ -f ".last_backup" ]; then
        BACKUP_FILE=$(cat .last_backup)
        if [ -f "$BACKUP_FILE" ]; then
            cp "$BACKUP_FILE" config/strategy_params.py
            echo -e "${GREEN}✅ 已恢复到原配置${NC}"
        else
            echo -e "${RED}❌ 备份文件不存在: $BACKUP_FILE${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  未找到备份记录${NC}"
    fi
}

# 显示变更摘要
show_changes() {
    echo ""
    echo "========================================================================"
    echo "主要优化点："
    echo "========================================================================"
    echo ""
    echo -e "${YELLOW}1. 入场质量${NC}"
    echo "   • 信号强度阈值: 60% → 60+ (BTC/ETH: 65, SOL: 55)"
    echo "   • ADX 阈值: 30 → 35"
    echo "   • 成交量确认: 1.3x → 1.5x"
    echo ""
    echo -e "${YELLOW}2. 止损策略${NC}"
    echo "   • 趋势策略: 2.5% → 3.5%"
    echo "   • BTC/ETH: 4%"
    echo "   • SOL: 3.5%"
    echo ""
    echo -e "${YELLOW}3. 止盈策略${NC}"
    echo "   • 趋势策略: 5% → 7%"
    echo "   • BTC/ETH: 8%"
    echo "   • SOL: 7%"
    echo ""
    echo -e "${YELLOW}4. 持仓管理${NC}"
    echo "   • 最长持仓: 72h → 96h"
    echo "   • 趋势市仓位: 80% → 70%"
    echo ""
    echo -e "${YELLOW}5. 品种差异化${NC}"
    echo "   • BTC/ETH: 更严格入场 + 更宽止损"
    echo "   • SOL: 保持最佳配置"
    echo ""
}

# 显示菜单
show_menu() {
    echo ""
    echo "========================================================================"
    echo "请选择操作："
    echo "========================================================================"
    echo ""
    echo "  1) 查看优化说明"
    echo "  2) 应用优化配置（推荐）"
    echo "  3) 恢复原配置"
    echo "  4) 运行回测"
    echo "  5) 分析回测结果"
    echo "  0) 退出"
    echo ""
    echo -n "请输入选项 [0-5]: "
}

# 运行回测
run_backtest() {
    echo ""
    echo -e "${BLUE}正在运行回测...${NC}"
    echo ""

    if [ -f "backtest_engine.py" ]; then
        python3 backtest_engine.py
        echo ""
        echo -e "${GREEN}✅ 回测完成${NC}"
    else
        echo -e "${RED}❌ 找不到 backtest_engine.py${NC}"
    fi
}

# 分析结果
analyze_results() {
    echo ""
    echo -e "${BLUE}正在分析回测结果...${NC}"
    echo ""

    if [ -f "analyze_backtest.py" ]; then
        python3 analyze_backtest.py
    else
        echo -e "${RED}❌ 找不到 analyze_backtest.py${NC}"
    fi
}

# 主程序
main() {
    check_files

    while true; do
        show_menu
        read -r choice

        case $choice in
            1)
                if [ -f "OPTIMIZATION_GUIDE.md" ]; then
                    show_changes
                    echo ""
                    echo -e "${BLUE}详细说明请查看: OPTIMIZATION_GUIDE.md${NC}"
                else
                    echo -e "${RED}❌ 找不到 OPTIMIZATION_GUIDE.md${NC}"
                fi
                ;;
            2)
                backup_config
                apply_optimized
                show_changes
                echo ""
                echo -e "${GREEN}✅ 优化配置已应用！${NC}"
                echo ""
                echo "下一步："
                echo "  • 运行回测: ./quick_optimize.sh 然后选择 4"
                echo "  • 或者: python3 backtest_engine.py"
                ;;
            3)
                restore_config
                ;;
            4)
                run_backtest
                ;;
            5)
                analyze_results
                ;;
            0)
                echo ""
                echo "退出"
                exit 0
                ;;
            *)
                echo -e "${RED}无效选项${NC}"
                ;;
        esac
    done
}

main
