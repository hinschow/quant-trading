# 🚀 完整部署指南

## 📦 一、代码已准备完毕

### 当前状态
✅ Git 仓库已初始化
✅ 代码已提交到本地 Git
✅ 远程仓库已配置：https://github.com/hinschow/quant-trading
⏳ 需要推送到 GitHub（需要认证）

---

## 🔐 二、推送到 GitHub（3种方案）

### 方案 A：使用 SSH 密钥（推荐）⭐⭐⭐⭐⭐

```bash
# 1. 生成 SSH 密钥
ssh-keygen -t ed25519 -C "hinschow@gmail.com"
# 按 Enter 使用默认路径，密码可留空

# 2. 查看并复制公钥
cat ~/.ssh/id_ed25519.pub

# 3. 添加公钥到 GitHub
# 访问：https://github.com/settings/keys
# 点击 "New SSH key"，粘贴公钥

# 4. 更改远程 URL 为 SSH
cd /home/andre/.claude/code/market/quant_trading
git remote set-url origin git@github.com:hinschow/quant-trading.git

# 5. 推送
git push -u origin main
```

### 方案 B：使用 Personal Access Token

```bash
# 1. 生成 Token
# 访问：https://github.com/settings/tokens
# 点击 "Generate new token (classic)"
# 勾选 "repo" 权限，生成并复制 token

# 2. 推送时使用 token
cd /home/andre/.claude/code/market/quant_trading
git push -u origin main
# Username: hinschow
# Password: 粘贴你的 token

# 3. 保存凭证（可选）
git config --global credential.helper store
# 下次推送不需要再输入
```

### 方案 C：在本地机器推送

```bash
# 1. 从服务器复制代码到本地
scp -r andre@你的服务器IP:/home/andre/.claude/code/market/quant_trading ~/Projects/

# 2. 在本地推送
cd ~/Projects/quant_trading
git push -u origin main
```

---

## 💻 三、本地部署步骤

### 1. 克隆代码到本地

```bash
# 方案 A：从 GitHub 克隆（推送成功后）
git clone https://github.com/hinschow/quant-trading.git
cd quant-trading

# 方案 B：从服务器直接复制
scp -r andre@服务器IP:/home/andre/.claude/code/market/quant_trading ~/Projects/
cd ~/Projects/quant_trading
```

### 2. 安装 Python 依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

### 3. 安装 TA-Lib（重要！）

#### macOS
```bash
brew install ta-lib
pip install ta-lib
```

#### Ubuntu/Debian
```bash
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
sudo ldconfig
cd ..
pip install ta-lib
```

#### Windows
```bash
# 下载预编译的 wheel 文件
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
# 选择对应 Python 版本，例如：
pip install TA_Lib-0.4.28-cp310-cp310-win_amd64.whl
```

### 4. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env
# macOS/Linux:
nano .env

# Windows:
notepad .env

# 至少配置以下内容：
# ENVIRONMENT=development
# BINANCE_API_KEY=你的API密钥
# BINANCE_API_SECRET=你的API密钥密码
# POSTGRES_PASSWORD=设置一个数据库密码
```

### 5. 启动 Docker 服务

```bash
# 确保 Docker 已安装并运行
docker --version
docker-compose --version

# 启动数据库和缓存
docker-compose up -d postgres redis

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f postgres

# 等待看到：database system is ready to accept connections
```

### 6. 初始化数据库

```bash
# 方式 1：自动初始化（Docker Compose 会自动执行 init_db.sql）
# 已在 docker-compose.yml 中配置

# 方式 2：手动初始化
docker exec -i quant_trading_postgres psql -U trader -d quant_trading < scripts/init_db.sql

# 验证表是否创建
docker exec -it quant_trading_postgres psql -U trader -d quant_trading -c "\dt"

# 应该看到 10+ 张表：
# klines, orders, trades, positions, performance_metrics, 等
```

### 7. 测试运行

```bash
# 激活虚拟环境
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 查看帮助
python main.py --help

# 测试导入
python -c "from utils.indicators import calculate_ema; print('导入成功')"
```

---

## 🎯 四、验证安装

### 创建测试脚本

```bash
# 创建测试文件
cat > test_setup.py << 'EOF'
"""
测试系统安装是否正确
"""
import sys

print("="*60)
print("测试量化交易系统安装")
print("="*60)

# 1. 测试 Python 版本
print(f"\n✓ Python 版本: {sys.version}")

# 2. 测试依赖包
try:
    import pandas as pd
    print(f"✓ Pandas 版本: {pd.__version__}")
except ImportError as e:
    print(f"✗ Pandas 导入失败: {e}")

try:
    import numpy as np
    print(f"✓ NumPy 版本: {np.__version__}")
except ImportError as e:
    print(f"✗ NumPy 导入失败: {e}")

try:
    import talib
    print(f"✓ TA-Lib 已安装")
except ImportError as e:
    print(f"✗ TA-Lib 导入失败: {e}")
    print("  请安装 TA-Lib: 参考 DEPLOYMENT_GUIDE.md")

try:
    import ccxt
    print(f"✓ CCXT 版本: {ccxt.__version__}")
except ImportError as e:
    print(f"✗ CCXT 导入失败: {e}")

# 3. 测试项目模块
try:
    from utils.logger import logger
    print("✓ 日志模块导入成功")
except ImportError as e:
    print(f"✗ 日志模块导入失败: {e}")

try:
    from utils.indicators import calculate_ema, calculate_rsi
    print("✓ 技术指标模块导入成功")
except ImportError as e:
    print(f"✗ 技术指标模块导入失败: {e}")

try:
    from config.settings import PROJECT_NAME, VERSION
    print(f"✓ 配置模块导入成功: {PROJECT_NAME} {VERSION}")
except ImportError as e:
    print(f"✗ 配置模块导入失败: {e}")

# 4. 测试数据库连接
try:
    import psycopg2
    from config.settings import DATABASE

    conn = psycopg2.connect(
        host=DATABASE['postgres']['host'],
        port=DATABASE['postgres']['port'],
        database=DATABASE['postgres']['database'],
        user=DATABASE['postgres']['user'],
        password=DATABASE['postgres']['password']
    )
    print("✓ PostgreSQL 连接成功")
    conn.close()
except Exception as e:
    print(f"✗ PostgreSQL 连接失败: {e}")
    print("  请确保 Docker 服务已启动: docker-compose up -d")

# 5. 测试 Redis 连接
try:
    import redis
    from config.settings import DATABASE

    r = redis.Redis(
        host=DATABASE['redis']['host'],
        port=DATABASE['redis']['port'],
        db=DATABASE['redis']['db']
    )
    r.ping()
    print("✓ Redis 连接成功")
except Exception as e:
    print(f"✗ Redis 连接失败: {e}")
    print("  请确保 Docker 服务已启动: docker-compose up -d")

print("\n" + "="*60)
print("测试完成！")
print("="*60)
EOF

# 运行测试
python test_setup.py
```

---

## 🔄 五、日常开发流程

### 在本地开发

```bash
# 1. 拉取最新代码
git pull

# 2. 创建新分支（开发新功能）
git checkout -b feature/market-regime-detector

# 3. 开发代码...

# 4. 提交更改
git add .
git commit -m "实现市场状态识别模块"

# 5. 推送到 GitHub
git push origin feature/market-regime-detector

# 6. 在 GitHub 创建 Pull Request
```

### 在服务器开发

```bash
# 1. 拉取最新代码
cd /home/andre/.claude/code/market/quant_trading
git pull

# 2. 开发代码...

# 3. 提交并推送
git add .
git commit -m "实现数据采集模块"
git push
```

---

## 📚 六、下一步开发

现在你已经完成基础设置，可以开始开发核心模块：

### 推荐开发顺序

1. **市场状态识别模块** (`strategies/market_regime.py`)
   - ADX + BBW 融合识别
   - 5 种市场状态判断

2. **数据采集模块** (`data/collectors/binance_collector.py`)
   - WebSocket 实时数据
   - 历史 K 线下载

3. **回测系统** (`backtest/engine.py`)
   - 历史数据回测
   - 性能指标计算

4. **策略引擎** (`strategies/`)
   - 趋势跟踪策略
   - 均值回归策略

5. **风险管理** (`risk/risk_manager.py`)
   - 仓位计算
   - 熔断机制

6. **交易执行** (`execution/order_manager.py`)
   - 订单管理
   - 智能路由

---

## 🆘 常见问题

### Q1: TA-Lib 安装失败
```bash
# 确保安装了编译工具
# Ubuntu:
sudo apt-get install build-essential

# macOS:
xcode-select --install
```

### Q2: Docker 无法启动
```bash
# 检查 Docker 服务
sudo systemctl status docker

# 启动 Docker
sudo systemctl start docker
```

### Q3: 数据库连接失败
```bash
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs postgres

# 重启容器
docker-compose restart postgres
```

### Q4: Git 推送失败
```bash
# 检查远程仓库
git remote -v

# 重新配置
git remote set-url origin git@github.com:hinschow/quant-trading.git
```

---

## 📞 需要帮助？

如果遇到任何问题，请告诉我：
1. 具体的错误信息
2. 你正在执行的步骤
3. 你的操作系统

我会立即帮你解决！

---

**项目地址**: https://github.com/hinschow/quant-trading
**本地路径**: /home/andre/.claude/code/market/quant_trading
**文档版本**: v1.0
**更新时间**: 2025-10-23
