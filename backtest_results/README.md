# 回测结果目录

此目录用于存放所有回测结果文件。

## 目录结构

```
backtest_results/
├── v3_original/          # 原始版本（v3.1）回测结果
├── v4_optimized/         # 优化版本（v4.0）回测结果
└── latest/               # 最新回测结果（符号链接）
```

## 文件命名规范

格式：`backtest_trades_{SYMBOL}_{TIMEFRAME}_{VERSION}.csv`

示例：
- `backtest_trades_BTC_USDT_1h_v3.csv`
- `backtest_trades_BTC_USDT_1h_v4.csv`

## 使用方法

### 1. 运行回测后移动结果
```bash
# 回测完成后
python3 run_backtest_all.py

# 移动到对应版本目录
mv backtest_trades_*.csv backtest_results/v4_optimized/
```

### 2. 分析特定版本
```bash
# 分析 v4 结果
cd backtest_results/v4_optimized
python3 ../../analyze_backtest.py
```

### 3. 对比不同版本
```bash
# 对比 v3 和 v4
python3 compare_results.py v3_original v4_optimized
```

## 版本说明

### v3_original (原始版本)
- 信号强度阈值：60%
- ADX 阈值：30
- 止损：2.5%
- 止盈：5%
- 表现：-5.42% 收益率，37.55% 胜率

### v4_optimized (优化版本)
- 信号强度阈值：BTC/ETH 65, SOL 55
- ADX 阈值：35
- 止损：BTC/ETH 4%, SOL 3.5%
- 止盈：BTC/ETH 8%, SOL 7%
- 预期：正收益，45%+ 胜率

## 注意事项

- 不要直接提交 CSV 文件到 Git（已在 .gitignore 中排除）
- 需要分享结果时，创建汇总报告
- 定期清理旧版本结果
