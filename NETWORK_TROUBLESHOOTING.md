# 🌐 网络问题排查和解决方案

## 问题症状

如果你看到这样的错误：
```
TimeoutError: timed out
Connection to api.binance.com timed out
ccxt.base.errors.RequestTimeout
```

这说明无法连接到币安 API。

---

## 🔧 解决方案

### 方案 1：使用代理（推荐）

如果你有代理服务器（如 V2Ray, Clash, Shadowsocks），可以配置代理访问：

```bash
# 使用代理连接币安
python signal_analyzer.py BTC/USDT --proxy http://127.0.0.1:7890

# 不同代理软件的常用端口：
# Clash: http://127.0.0.1:7890
# V2Ray: http://127.0.0.1:10809
# Shadowsocks: http://127.0.0.1:1087
```

#### 如何找到你的代理端口？

**Clash:**
- 打开 Clash，查看 "端口设置" 或 "Port"
- 通常是 7890（HTTP）或 7891（SOCKS5）

**V2Ray/V2RayX:**
- 查看设置中的 HTTP 代理端口
- 通常是 10809

**Shadowsocks:**
- 查看 "高级设置" - "本地 Socks5 监听端口"
- 通常是 1080 或 1087

---

### 方案 2：切换到其他交易所

如果币安无法访问，可以使用其他交易所（它们也提供免费的公开 API）：

#### OKX (推荐)

```bash
# OKX 在国内访问通常较好
python signal_analyzer.py BTC/USDT -e okx

# 扫描 OKX 的 USDT 交易对
python signal_analyzer.py --scan USDT -e okx --min-strength 60
```

#### Bybit

```bash
# Bybit 也是可选项
python signal_analyzer.py BTC/USDT -e bybit
```

#### Gate.io

```bash
# Gate.io
python signal_analyzer.py BTC/USDT -e gateio
```

---

### 方案 3：测试网络连接

先测试能否访问币安 API：

```bash
# 测试1：检查 DNS 解析
ping api.binance.com

# 测试2：测试 HTTPS 连接
curl -I https://api.binance.com/api/v3/time

# 测试3：使用代理测试
curl -I https://api.binance.com/api/v3/time -x http://127.0.0.1:7890
```

如果 curl 成功返回数据，说明网络可达，可以用代理模式运行程序。

---

### 方案 4：修改 DNS（进阶）

有时币安 API 被 DNS 污染，可以尝试：

```bash
# 编辑 hosts 文件
sudo nano /etc/hosts

# 添加以下行（币安备用 IP）
54.186.118.55   api.binance.com
54.186.118.55   api1.binance.com
54.186.118.55   api2.binance.com
```

---

## 📊 推荐方案对比

| 方案 | 优点 | 缺点 | 推荐指数 |
|------|------|------|----------|
| 使用代理 | 最稳定，访问币安数据最全 | 需要代理软件 | ⭐⭐⭐⭐⭐ |
| 切换 OKX | 不需要代理，国内可访问 | 币种可能略少 | ⭐⭐⭐⭐ |
| 切换 Bybit | 访问稳定 | 需要测试 | ⭐⭐⭐ |
| 修改 hosts | 免费不需代理 | 可能不稳定，IP 会变 | ⭐⭐ |

---

## 🚀 快速开始示例

### 场景 1：有代理软件

```bash
# 1. 启动你的代理软件（Clash/V2Ray/Shadowsocks）

# 2. 查看代理端口（通常是 7890 或 10809）

# 3. 运行分析工具
python signal_analyzer.py BTC/USDT --proxy http://127.0.0.1:7890

# 4. 批量扫描
python signal_analyzer.py --scan USDT --proxy http://127.0.0.1:7890 --min-strength 60
```

### 场景 2：没有代理软件

```bash
# 直接使用 OKX
python signal_analyzer.py BTC/USDT -e okx

# OKX 扫描
python signal_analyzer.py --scan USDT -e okx --min-strength 60

# 多个币种
python signal_analyzer.py BTC/USDT ETH/USDT SOL/USDT -e okx -t 4h
```

---

## 🔍 诊断脚本

创建一个网络诊断脚本：

```bash
cat > test_network.py << 'EOF'
#!/usr/bin/env python3
"""网络连接诊断工具"""
import ccxt

exchanges_to_test = ['binance', 'okx', 'bybit', 'gateio']

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
        print(f"❌ 失败: {str(e)[:50]}")

print("\n💡 建议:")
print("- 如果币安失败，使用 --proxy 参数或切换到其他交易所")
print("- 如果所有都失败，检查网络连接")
EOF

# 运行诊断
python test_network.py
```

---

## ⚙️ 系统代理配置（可选）

如果想让所有程序都走代理：

### macOS / Linux

```bash
# 临时设置（当前终端有效）
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890

# 测试
python signal_analyzer.py BTC/USDT

# 取消代理
unset http_proxy
unset https_proxy
```

### 永久设置（添加到 ~/.zshrc 或 ~/.bashrc）

```bash
echo 'export http_proxy=http://127.0.0.1:7890' >> ~/.zshrc
echo 'export https_proxy=http://127.0.0.1:7890' >> ~/.zshrc
source ~/.zshrc
```

---

## 📞 常见问题

### Q: 我不知道代理端口怎么办？

A:
1. 打开你的代理软件（Clash/V2Ray）
2. 查找 "端口设置" 或 "Port Settings"
3. 记下 HTTP 端口号
4. 使用 `http://127.0.0.1:端口号` 作为代理地址

### Q: 使用 OKX 和币安有什么区别？

A:
- 数据基本相同，价格略有差异（套利空间）
- 币安交易量更大，数据更全
- OKX 在国内访问更稳定
- 建议：多个交易所对比分析

### Q: 代理会影响速度吗？

A:
- 优质代理几乎无影响
- 数据获取主要受限于交易所 API 速率
- 建议使用低延迟的代理节点

### Q: 能否直接在程序中硬编码代理？

A: 可以修改 `data_collector.py`：

```python
def __init__(self, exchange_name: str = 'binance', proxy: Optional[str] = None):
    # 硬编码代理
    if proxy is None:
        proxy = 'http://127.0.0.1:7890'  # 修改为你的代理
    ...
```

但不推荐，因为：
- 代理可能会变化
- 代码分享时会暴露你的配置
- 灵活性降低

---

## ✅ 验证成功

如果看到类似输出，说明网络已配置成功：

```
INFO:data_collector:✅ 初始化 binance 数据采集器 (域名: api.binance.com)
INFO:data_collector:📥 获取 BTC/USDT 1h 数据，共 500 条
INFO:data_collector:✅ 成功获取 500 条数据

📊 BTC/USDT - 1h 交易信号分析
================================================================================
【基本信息】
  当前价格: $67,234.50
  ...
```

祝交易顺利！ 📈
