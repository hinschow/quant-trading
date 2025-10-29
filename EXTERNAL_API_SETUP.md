# 外部API获取指南

快速获取免费API，增强量化交易系统的数据源。

---

## 🚀 快速开始（推荐）

### 方式1：使用配置向导（最简单）

```bash
python setup_external_apis.py
```

向导会引导你完成所有配置！

### 方式2：手动配置

按照下面的详细说明逐个申请API。

---

## 📋 API获取详细步骤

### 1. 🐋 Whale Alert API（推荐，5分钟完成）

**用途**：监控区块链大额交易（鲸鱼活动）

**免费额度**：
- ✅ 10次/分钟（足够使用）
- ✅ 支持主流币种
- ⚠️ 数据有~10分钟延迟

**获取步骤**：

#### 步骤1：注册账号
```
访问：https://whale-alert.io/
点击右上角 "Sign Up"
填写：
  - Email: 你的邮箱
  - Password: 设置密码
  - 用途: Personal research
```

#### 步骤2：获取API Key
```
1. 登录后进入 Dashboard
2. 点击左侧 "API"
3. 点击 "Create API Key"
   - Name: "Crypto Trading Monitor"
4. 复制显示的 API Key
   格式：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

#### 步骤3：配置到项目
```bash
# 编辑 .env 文件，添加：
WHALE_ALERT_API_KEY=你的API_Key
```

#### 测试：
```bash
python utils/whale_alert_client.py
```

---

### 2. 📰 CryptoPanic API（推荐，3分钟完成）

**用途**：加密货币新闻聚合

**免费额度**：
- ✅ 基础新闻访问
- ✅ 支持多个币种
- ✅ 每日足够使用

**获取步骤**：

#### 步骤1：注册
```
访问：https://cryptopanic.com/developers/api/
点击 "Get your free API key"
填写：
  - Email: 你的邮箱
  - Use case: Personal investment research
```

#### 步骤2：获取Key
```
注册确认后，会立即显示 API Key
格式：xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### 步骤3：配置
```bash
# .env 文件：
CRYPTOPANIC_API_KEY=你的API_Key

# 或者使用免费默认（有限制）：
CRYPTOPANIC_API_KEY=free
```

---

### 3. 🐦 Twitter/X API（可选）

**两种方案：**

---

#### 方案A：Nitter（推荐 - 无需API key）

**优点**：
- ✅ 完全免费
- ✅ 无需注册
- ✅ 无请求限制
- ✅ 已内置支持

**使用**：
```bash
# 无需任何配置，直接使用！
python utils/twitter_nitter.py

# 或在Dashboard中自动使用
```

**Nitter说明**：
- Nitter是Twitter的开源前端镜像
- 官网：https://nitter.net/
- 多个公共实例可用
- 代码已内置实例列表和自动切换

---

#### 方案B：官方Twitter API（复杂）

**仅当Nitter不可用时考虑**

**免费额度（2024年）**：
- ⚠️ Tweets/月：10,000条（较少）
- ✅ 搜索请求：100次/15分钟
- ⚠️ 需要申请审批

**获取步骤**：

##### 步骤1：申请开发者账号
```
访问：https://developer.twitter.com/
点击 "Sign up" 或 "Apply"
使用你的Twitter账号登录

选择账户类型：
  - "Hobbyist"（爱好者）
  - "Exploring the API"
```

##### 步骤2：填写申请表
```
App name: "Crypto Sentiment Analyzer"

Use case description（英文，至少200字）：
"I'm building a personal cryptocurrency sentiment analysis tool
to monitor discussions about Bitcoin, Ethereum and other
cryptocurrencies on Twitter. The data will be used for personal
investment research and educational purposes only.

I will search for specific keywords such as 'BTC', 'Bitcoin',
'ETH', 'Ethereum', 'crypto', analyze the sentiment of tweets,
and track mentions from well-known crypto influencers and experts.
The analysis will help me understand market sentiment trends.

I plan to make approximately 50-100 API requests per day,
primarily using the search/recent endpoint to find relevant tweets.
All data will be used privately for my own analysis and will not
be redistributed or published publicly."

Country: China
Email: 你的邮箱
```

##### 步骤3：等待审批
```
通常 1-24小时内会收到邮件通知
审批通过后，进入 Developer Portal
```

##### 步骤4：创建App
```
进入：https://developer.twitter.com/en/portal/dashboard

1. Create Project
   - Name: "Crypto Trading Monitor"
   - Use case: "Exploring the API"

2. Create App (within Project)
   - App name: "sentiment-tracker-2024"（必须唯一）
   - Environment: Development

3. 保存 API Credentials（重要！只显示一次）
   - API Key
   - API Secret Key
   - Bearer Token ⭐（最重要）
```

##### 步骤5：配置权限
```
Settings → User authentication settings
- App permissions: Read only
- Type of App: Web App, Automated App or Bot
```

##### 步骤6：配置到项目
```bash
# .env 文件：
TWITTER_BEARER_TOKEN=你的Bearer_Token
TWITTER_API_KEY=你的API_Key
TWITTER_API_SECRET=你的API_Secret
```

---

## ⚙️ 配置文件说明

### .env 文件配置示例

```bash
# ==================== 外部数据源API ====================

# Whale Alert（必须）
WHALE_ALERT_API_KEY=12345678-1234-5678-1234-567812345678

# CryptoPanic（必须）
CRYPTOPANIC_API_KEY=abcdefghijklmnopqrstuvwxyz123456

# Twitter（可选，推荐使用Nitter）
# 如果使用官方API，取消注释：
# TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAABearerToken
```

---

## 🧪 测试API

### 测试所有API
```bash
python setup_external_apis.py
# 在向导最后选择 "测试API连接"
```

### 单独测试

**测试 Whale Alert**：
```bash
python utils/whale_alert_client.py
```

**测试 Nitter (Twitter)**：
```bash
python utils/twitter_nitter.py
```

**测试 CryptoPanic**：
```bash
python -c "from utils.external_sentiment import NewsMonitor; m = NewsMonitor(); print(m.fetch_crypto_news())"
```

---

## 📊 API使用说明

### 在Dashboard中查看

启动Dashboard后自动集成所有配置的API：

```bash
python start_dashboard.py
```

访问：http://localhost:5000

你会看到：
- 🐋 **鲸鱼动态**：显示大额交易
- 📰 **最新资讯**：显示CryptoPanic新闻
- 😊 **情绪分析**：显示Twitter情绪得分

### 在代码中使用

```python
from utils.external_sentiment import get_sentiment_analyzer

analyzer = get_sentiment_analyzer()

# 获取BTC的综合情绪
sentiment = analyzer.get_comprehensive_sentiment("BTC/USDT")

print(f"总得分: {sentiment['total_score']}")
print(f"Twitter: {sentiment['breakdown']['twitter']}")
print(f"新闻: {sentiment['breakdown']['news']}")
print(f"鲸鱼: {sentiment['breakdown']['whale']}")
```

---

## 🔒 安全提醒

### API Key保护

1. **不要提交到Git**
```bash
# .env 已在 .gitignore 中，不会被提交
# 确保不要 git add .env
```

2. **定期更换**
```bash
# 每3个月更换一次API key（推荐）
```

3. **权限最小化**
```bash
# Twitter API 只需要 Read only 权限
# Whale Alert 只需要 Transactions 权限
```

---

## 🎯 推荐配置方案

### 方案1：完全免费（推荐新手）
- ✅ Whale Alert：注册免费API
- ✅ CryptoPanic：使用 `free` key
- ✅ Twitter：使用内置 Nitter（无需配置）

**优点**：5分钟搞定，完全免费
**缺点**：Twitter数据量稍少

### 方案2：完整功能（推荐进阶）
- ✅ Whale Alert：注册免费API
- ✅ CryptoPanic：注册获取专属key
- ✅ Twitter：申请官方API

**优点**：数据最全面
**缺点**：需要20-30分钟配置

### 方案3：最小配置（快速体验）
- ✅ Whale Alert：注册免费API
- ⚠️ 其他：暂不配置

**优点**：2分钟完成核心配置
**缺点**：缺少新闻和社交数据

---

## ❓ 常见问题

### Q1: Whale Alert API不工作？
```bash
# 检查：
1. API key 是否正确复制（完整UUID格式）
2. 是否超过速率限制（10次/分钟）
3. 网络是否能访问 api.whale-alert.io
```

### Q2: CryptoPanic返回空数据？
```bash
# 原因：
- 使用 "free" key 有更多限制
- 建议注册专属key

# 测试：
curl "https://cryptopanic.com/api/v1/posts/?auth_token=free&currencies=BTC"
```

### Q3: Nitter无法访问？
```bash
# 原因：公共实例可能暂时不可用

# 解决：
1. 代码会自动切换其他实例
2. 或手动修改 utils/twitter_nitter.py 中的 instances 列表
3. 找其他可用实例：https://github.com/zedeus/nitter/wiki/Instances
```

### Q4: Twitter官方API申请被拒？
```bash
# 常见原因：
1. 申请理由不够详细（需要200字+）
2. 没有描述具体使用场景
3. 账号是新注册的（建议使用老账号）

# 解决：
- 重新申请，详细描述教育/研究用途
- 或者直接使用 Nitter 方案
```

---

## 📞 获取帮助

遇到问题？

1. 查看详细文档：`DASHBOARD_README.md`
2. 运行测试命令找出具体错误
3. 查看日志：Dashboard启动时会显示初始化状态

---

## ✨ 下一步

配置完成后：

```bash
# 1. 启动Dashboard
python start_dashboard.py

# 2. 访问
http://localhost:5000

# 3. 查看效果
- 鲸鱼动态面板
- 新闻资讯流
- 情绪分析图表
```

**祝配置顺利！** 🚀
