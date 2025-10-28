# Mac本地环境安装指南

您已经从GitHub克隆了项目到Mac，现在需要安装依赖。

## 🔧 步骤1：确认虚拟环境已激活

您已经激活了虚拟环境（看到 `(venv)` 前缀），很好！

如果没有激活，运行：
```bash
source venv/bin/activate
```

## 📦 步骤2：安装Python依赖

```bash
# 确保在项目目录
cd ~/quant-trading  # 或您的项目路径

# 安装依赖
pip install -r requirements.txt
```

## ⚠️ TA-Lib安装（Mac特殊处理）

TA-Lib需要先安装系统依赖：

### 方式1：使用Homebrew（推荐）

```bash
# 安装Homebrew（如果还没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装TA-Lib
brew install ta-lib

# 然后安装Python包
pip install ta-lib
```

### 方式2：如果Homebrew安装失败

可以临时跳过TA-Lib，使用纯Python实现：

```bash
# 安装除TA-Lib外的其他依赖
pip install pandas numpy ccxt python-dotenv pyyaml requests pytz python-dateutil
```

然后修改 `utils/indicators.py`，使用pandas-ta替代：

```bash
pip install pandas-ta
```

## 📋 步骤3：验证安装

```bash
# 测试Python导入
python3 << 'EOF'
try:
    import pandas
    import numpy
    import ccxt
    print("✅ 基础依赖安装成功")
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")

try:
    import talib
    print("✅ TA-Lib安装成功")
except ImportError:
    print("⚠️  TA-Lib未安装（可选，但推荐安装）")
EOF
```

## 🚀 步骤4：运行测试

```bash
# 快速测试
./test_backtest.sh

# 或直接运行回测
python3 backtest_engine.py BTC/USDT -t 1h --limit 500
```

## 🔍 常见问题

### Q1: `pip install ta-lib` 失败

**错误**: `error: command 'gcc' failed`

**解决方案**:
```bash
# 确保安装了Xcode命令行工具
xcode-select --install

# 然后重新安装ta-lib
brew install ta-lib
pip install ta-lib
```

### Q2: ccxt安装失败

**错误**: 版本冲突

**解决方案**:
```bash
# 安装特定版本
pip install 'ccxt>=4.0.0,<4.3.0'
```

### Q3: 没有Homebrew也不想装

**解决方案**: 使用pandas-ta替代

1. 安装pandas-ta:
   ```bash
   pip install pandas-ta
   ```

2. 创建 `utils/indicators_pandasta.py`:
   ```python
   import pandas as pd
   import pandas_ta as ta

   def calculate_ema(df, period):
       return ta.ema(df['close'], length=period)

   def calculate_rsi(df, period=14):
       return ta.rsi(df['close'], length=period)

   # ... 其他指标
   ```

3. 修改导入语句（在需要的文件中）:
   ```python
   # from utils.indicators import ...
   from utils.indicators_pandasta import ...
   ```

### Q4: 网络问题导致无法连接Binance

**Mac可能需要代理**:

```bash
# 在终端设置代理（临时）
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890

# 然后运行脚本
python3 backtest_engine.py BTC/USDT -t 1h
```

或在代码中指定代理（已支持）:
```bash
python3 backtest_engine.py BTC/USDT -t 1h --proxy http://127.0.0.1:7890
```

## 📝 完整安装命令（复制粘贴）

```bash
# 进入项目目录
cd ~/quant-trading

# 激活虚拟环境（如果还没有）
source venv/bin/activate

# 安装TA-Lib系统依赖
brew install ta-lib

# 安装Python依赖
pip install -r requirements.txt

# 验证安装
python3 -c "import pandas, numpy, ccxt, talib; print('✅ 所有依赖安装成功')"

# 运行测试
./test_backtest.sh
```

## 🎯 最简安装（跳过TA-Lib）

如果TA-Lib安装太麻烦，可以暂时跳过：

```bash
cd ~/quant-trading
source venv/bin/activate

# 只安装核心依赖
pip install pandas numpy ccxt python-dotenv pyyaml requests pytz python-dateutil

# 安装pandas-ta作为替代
pip install pandas-ta

# 修改indicators.py使用pandas-ta
# （需要手动修改代码）
```

## 💡 推荐配置

```bash
# ~/.zshrc 或 ~/.bash_profile
alias activate-quant='cd ~/quant-trading && source venv/bin/activate'
export QUANT_PROXY='http://127.0.0.1:7890'
```

然后：
```bash
source ~/.zshrc  # 或 source ~/.bash_profile
activate-quant
```

## 🔗 相关文档

- [QUICK_START_BACKTEST.md](QUICK_START_BACKTEST.md) - 回测快速开始
- [PARAMETER_GUIDE.md](PARAMETER_GUIDE.md) - 参数配置指南
- [requirements.txt](requirements.txt) - 依赖列表

---

**Mac版本**: macOS 支持
**Python版本**: 3.10+
**更新时间**: 2025-10-27
