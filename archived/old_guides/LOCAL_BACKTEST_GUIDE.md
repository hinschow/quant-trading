# 本地回测执行指南

## 环境准备

### 1. 确认 Python 环境
```bash
python3 --version  # 确认 Python 3.9 或更高版本
```

### 2. 安装依赖
在你的**本地 Mac** 上执行：

```bash
cd /path/to/quant-trading  # 替换为你本地的项目路径
pip3 install -r requirements.txt
```

如果遇到依赖冲突，可以使用：
```bash
pip3 install -r requirements-mac-py39.txt
```

## 执行回测

### 方法一：使用测试脚本（推荐）
```bash
chmod +x test_backtest.sh
./test_backtest.sh
```

### 方法二：直接执行 Python 脚本
```bash
python3 backtest_engine.py
```

### 方法三：使用配置管理器指定参数
```bash
python3 config_manager.py
```

## 回测参数说明

回测会使用 `config/backtest_config.json` 中的配置：
- **交易对**：BTC/USDT, ETH/USDT, SOL/USDT
- **时间周期**：1h (1小时K线)
- **初始资金**：10,000 USDT
- **手续费**：0.1%
- **回测时间范围**：最近 30 天

## 输出结果

回测完成后会生成以下文件：
- `backtest_trades_BTC_USDT_1h.csv` - BTC 交易记录
- `backtest_trades_ETH_USDT_1h.csv` - ETH 交易记录
- `backtest_trades_SOL_USDT_1h.csv` - SOL 交易记录

每个 CSV 文件包含：
- 交易时间
- 交易类型（买入/卖出）
- 价格
- 数量
- 盈亏
- 账户余额
- 等详细信息

## 提交结果到服务器

### 1. 将生成的 CSV 文件复制到服务器
在你的**本地 Mac** 上执行：

```bash
# 方法一：使用 scp（如果已配置 SSH）
scp backtest_trades_*.csv andre@your-server:/home/andre/code/quant-trading/

# 方法二：或者直接提交到 Git
git add backtest_trades_*.csv
git commit -m "Add backtest results from local execution"
git push
```

### 2. 在服务器上拉取结果
然后我可以在服务器上执行：
```bash
git pull
```

## 常见问题

### Q1: 提示缺少某个包
```bash
pip3 install 包名
```

### Q2: TA-Lib 安装失败
Mac 上需要先安装 TA-Lib 底层库：
```bash
brew install ta-lib
pip3 install TA-Lib
```

### Q3: 网络连接问题
回测引擎会自动从 Binance API 获取历史数据。确保：
- 网络连接正常
- 可以访问 api.binance.com
- 或者使用代理（如需要）

### Q4: 回测时间过长
如果数据量大，可以修改配置文件中的日期范围：
```bash
python3 config_manager.py
# 选择修改 backtest 配置
# 调整 lookback_days 参数
```

## 验证结果

回测完成后，检查生成的 CSV 文件：
```bash
ls -lh backtest_trades_*.csv
head -20 backtest_trades_BTC_USDT_1h.csv
```

## 下一步

将结果文件提交到服务器后，告诉我，我会：
1. 分析回测结果
2. 生成性能报告
3. 提供策略优化建议
