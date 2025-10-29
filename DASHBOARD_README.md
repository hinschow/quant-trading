# 量化交易监控Dashboard使用指南

## 🎯 系统概述

这是一个完整的量化交易监控系统，集成了：
- **策略优化**：基于回测数据的参数调整
- **外部数据采集**：社交媒体、新闻、链上数据
- **实时可视化**：Web Dashboard监控面板

---

## 📦 安装步骤

### 1. 安装Dashboard依赖

```bash
# 安装额外依赖
pip install -r requirements-dashboard.txt

# 或者单独安装
pip install Flask Flask-CORS gunicorn
```

### 2. 配置外部数据源（可选）

编辑 `config/external_data_config.py`：

```python
# 启用/禁用各个数据源
SOCIAL_SENTIMENT_PARAMS = {
    "enabled": True,  # Twitter监控
    ...
}

NEWS_PARAMS = {
    "enabled": True,  # 新闻监控
    "cryptopanic": {
        "api_key": "your_api_key",  # 申请免费API: https://cryptopanic.com/developers/api/
    }
}
```

---

## 🚀 启动Dashboard

### 方式1：使用启动脚本（推荐）

```bash
python start_dashboard.py
```

### 方式2：直接运行

```bash
cd dashboard
python app.py
```

### 方式3：生产环境（使用Gunicorn）

```bash
gunicorn -w 4 -b 0.0.0.0:5000 dashboard.app:app
```

访问地址：**http://localhost:5000**

---

## 📊 Dashboard功能说明

### 1. **主要指标概览**

顶部4个关键指标卡片：
- **活跃信号**：当前满足条件的交易机会数量
- **监控币种**：启用的交易对总数
- **新闻事件**：最新的新闻数量
- **市场情绪**：综合情绪分数（正面/中性/负面）

### 2. **告警区域**

显示重要提醒：
- 🔴 **关键告警**：重大新闻、极端情绪、鲸鱼大额交易
- 🟡 **警告**：中等影响的事件
- 🟢 **信息**：一般性提示

### 3. **实时交易信号**

表格显示：
- 币种
- 信号类型（BULLISH/BEARISH/NEUTRAL）
- 信号强度（0-100分）
- 当前价格
- 资金费率
- 情绪得分
- 生成时间

**信号颜色说明**：
- 🟢 绿色：看涨信号
- 🔴 红色：看跌信号
- 🟡 黄色：中性信号

### 4. **市场概览表**

所有监控币种的实时数据：
- 价格
- 资金费率（正值=多头支付，负值=空头支付）
- 持仓量（OI）
- 数据来源（Hyperliquid/Binance）
- 交易状态（启用/禁用）

### 5. **鲸鱼动态**

监控大额交易：
- 鲸鱼买入/卖出
- 交易所大额转入/转出
- 影响分析

### 6. **最新资讯**

实时新闻流：
- 标题
- 发布时间
- 点击可跳转原文

**新闻来源**：
- CoinDesk
- Cointelegraph
- The Block
- Decrypt
等主流媒体

### 7. **情绪分析图表**

柱状图显示各币种的综合情绪得分：
- 🟢 正值：正面情绪
- 🔴 负值：负面情绪

**情绪来源**：
- Twitter/X 讨论热度
- 新闻事件影响
- 链上数据指标

---

## ⚙️ 配置说明

### 参数优化配置

**文件**: `config/strategy_params.py`

已优化的关键配置：

```python
# 时间框架权重（30m表现最佳）
SIGNAL_FUSION_PARAMS = {
    "timeframe_weights": {
        "15m": 0.2,
        "30m": 0.6,  # ⬆️ 提高权重
        "1h": 0.2,
    },
    "min_signal_strength": 55,  # 降低阈值增加机会
}

# 币种差异化参数
SYMBOL_SPECIFIC_PARAMS = {
    "1000RATS/USDT": {
        # 高收益币种(+84%)，降低门槛
        "min_signal_strength": 45,
        "stop_loss_pct": 0.04,
        "take_profit_pct": 0.08,
        "enabled": True,
    },
    "SOL/USDT": {
        # 稳定盈利(+8.4%)
        "min_signal_strength": 55,
        "timeframe_preference": "30m",
        "enabled": True,
    },
    "SNX/USDT": {
        # 表现差，暂时禁用
        "enabled": False,
    },
}
```

### 外部数据权重

**文件**: `config/external_data_config.py`

```python
EXTERNAL_DATA_WEIGHTS = {
    "technical_signals": 0.50,  # 技术指标 50%
    "social_sentiment": 0.15,   # 社交媒体 15%
    "news_impact": 0.15,        # 新闻事件 15%
    "market_data": 0.15,        # 资金费率+OI 15%
    "onchain_data": 0.05,       # 链上数据 5%
}
```

---

## 🔌 API端点说明

Dashboard提供以下API接口：

### 1. 市场概览
```
GET /api/market_overview
```
返回所有交易对的实时数据

### 2. 交易信号
```
GET /api/signals
```
返回当前活跃的交易信号

### 3. 情绪分析
```
GET /api/sentiment/<symbol>
```
返回指定币种的综合情绪分析

示例：
```bash
curl http://localhost:5000/api/sentiment/BTC/USDT
```

响应：
```json
{
  "success": true,
  "data": {
    "total_score": 15,
    "breakdown": {
      "twitter": 5,
      "news": 10,
      "whale": 0
    },
    "signals": ["Positive news about BTC ETF"],
    "alerts": []
  }
}
```

### 4. 新闻列表
```
GET /api/news
```
返回最新加密货币新闻

### 5. 鲸鱼告警
```
GET /api/whale_alerts
```
返回大额交易记录

---

## 🛠️ 自定义开发

### 添加新的数据源

1. 在 `utils/external_sentiment.py` 中创建Monitor类：

```python
class YourCustomMonitor:
    def __init__(self):
        self.enabled = True

    def get_sentiment_score(self, symbol: str) -> Dict:
        # 实现数据采集逻辑
        return {'score': 0, 'signals': []}
```

2. 在 `ExternalSentimentAnalyzer` 中集成：

```python
class ExternalSentimentAnalyzer:
    def __init__(self):
        self.custom_monitor = YourCustomMonitor()

    def get_comprehensive_sentiment(self, symbol: str) -> Dict:
        custom_data = self.custom_monitor.get_sentiment_score(symbol)
        # 整合到总分
```

### 添加新的Dashboard页面

1. 在 `dashboard/templates/` 创建新HTML
2. 在 `dashboard/app.py` 添加路由：

```python
@app.route('/custom_page')
def custom_page():
    return render_template('custom_page.html')
```

---

## 📈 使用最佳实践

### 1. 参数调整流程

```bash
# 1. 修改参数
编辑 config/strategy_params.py

# 2. 回测验证
python run_multi_timeframe_backtest.py

# 3. 分析结果
python analyze_multi_timeframe.py

# 4. 如果满意，应用到实盘配置
```

### 2. 监控建议

- **日常监控**：关注"告警区域"和"实时信号"
- **深度分析**：查看"情绪图表"和"新闻资讯"
- **风险控制**：注意资金费率极端值和鲸鱼异常活动

### 3. 信号过滤策略

Dashboard默认只显示达到最低强度的信号。调整过滤：

```python
# config/strategy_params.py
SIGNAL_FUSION_PARAMS = {
    "min_signal_strength": 55,  # 调高=更严格，调低=更多信号
}
```

---

## 🐛 常见问题

### Q: Dashboard启动失败？

**A**: 检查依赖是否安装：
```bash
pip list | grep Flask
```

确保端口5000未被占用：
```bash
# Linux/Mac
lsof -i :5000

# Windows
netstat -ano | findstr :5000
```

### Q: 新闻不显示？

**A**: 检查外部数据配置：
```python
# config/external_data_config.py
NEWS_PARAMS = {
    "enabled": True,  # 确保启用
    "cryptopanic": {
        "enabled": True,
    }
}
```

### Q: 情绪分析全为0？

**A**: 外部数据源可能未配置API key，或网络连接失败。查看日志：
```bash
python start_dashboard.py 2>&1 | grep ERROR
```

### Q: 如何在服务器上运行？

**A**: 使用Gunicorn + Nginx：
```bash
# 安装
pip install gunicorn

# 启动（4个worker进程）
gunicorn -w 4 -b 0.0.0.0:5000 dashboard.app:app --daemon

# 使用Nginx反向代理（可选）
```

---

## 🔐 安全建议

1. **API Key保护**：
   - 不要将API key提交到Git
   - 使用环境变量：`export CRYPTOPANIC_KEY=xxx`

2. **生产部署**：
   - 启用HTTPS
   - 添加身份验证
   - 限制访问IP

3. **数据保护**：
   - 定期备份配置
   - 加密敏感信息

---

## 📝 更新日志

### v2.0 (2024-10-29)
- ✅ 新增外部数据采集（Twitter、新闻、链上）
- ✅ 完整的Web Dashboard
- ✅ 基于回测的参数优化
- ✅ 实时情绪分析可视化

### v1.0 (之前)
- 基础策略引擎
- 回测功能
- Hyperliquid/Binance数据源

---

## 💡 下一步计划

### 短期（1周内）
- [ ] 集成真实Twitter API
- [ ] 添加Telegram通知
- [ ] 优化移动端显示

### 中期（1月内）
- [ ] 机器学习情绪分类
- [ ] 自动参数优化（网格搜索）
- [ ] 历史信号回放

### 长期
- [ ] 多账户管理
- [ ] 组合优化
- [ ] 风险归因分析

---

## 📞 支持

- 问题反馈：[GitHub Issues](https://github.com/hinschow/quant-trading/issues)
- 文档：项目根目录 `README.md`
- 示例：`docs/` 目录

---

**祝交易顺利！** 🚀
