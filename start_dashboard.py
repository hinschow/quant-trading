#!/usr/bin/env python3
"""
量化交易Dashboard启动脚本
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dashboard.app import app, init_services

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 启动量化交易监控Dashboard")
    print("="*70)
    print()
    print("功能:")
    print("  ✓ 实时市场数据监控")
    print("  ✓ 交易信号提醒")
    print("  ✓ 新闻事件追踪")
    print("  ✓ 情绪分析可视化")
    print("  ✓ 鲸鱼动态告警")
    print()
    print("="*70)
    print()

    # 初始化服务
    init_services()

    print("\n📊 Dashboard地址:")
    print("   本地访问: http://localhost:5000")
    print("   局域网访问: http://0.0.0.0:5000")
    print()
    print("按 Ctrl+C 停止服务")
    print()

    # 启动Flask应用
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=False  # 避免重复初始化
    )
