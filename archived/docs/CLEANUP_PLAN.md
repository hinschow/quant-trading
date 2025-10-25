# 🧹 项目文件清理计划

## 📋 分析结果

### 1️⃣ 确定可以删除的文件

#### Python脚本
| 文件 | 原因 | 依赖情况 |
|------|------|---------|
| **config/risk_params.py** | 未被任何文件引用 | 无依赖 ✅ |
| **main.py** | 早期主程序入口，已被专门脚本取代 | 被settings.py依赖 |
| **utils/logger.py** | 只被main.py使用 | 仅main.py依赖 |
| **config/settings.py** | 只被main.py和logger.py使用 | 仅main.py依赖 |

#### 说明
- **main.py** 是早期设计的统一入口，但现在已有专门脚本：
  - `realtime_monitor_pro.py` - 实时监控
  - `multi_monitor.py` - 多币监控
  - `signal_analyzer.py` - 信号分析
- **删除main.py**后，相关的logger.py和settings.py也可以删除

---

### 2️⃣ 可能重复的文件

| 文件 | 状态 | 建议 |
|------|------|------|
| **realtime_monitor.py** | 早期版本 | 已被realtime_monitor_pro.py取代，可删除 ✅ |
| **REALTIME_MONITOR_GUIDE.md** | 早期文档 | 已被REALTIME_MONITOR_PRO_GUIDE.md取代，可删除 ✅ |

---

### 3️⃣ 需要保留的文件

#### 核心脚本（必须保留）
```
✅ data_collector.py          - 数据采集
✅ strategy_engine.py          - 策略引擎
✅ realtime_engine.py          - 实时信号引擎
✅ websocket_stream.py         - WebSocket流
✅ realtime_monitor_pro.py     - 实时监控（主要使用）
✅ multi_monitor.py            - 多币监控（主要使用）
✅ signal_analyzer.py          - 信号分析工具
```

#### 工具模块（必须保留）
```
✅ utils/data_buffer.py        - 数据缓冲
✅ utils/indicators.py         - 技术指标
✅ utils/signal_logger.py      - 信号记录
```

#### 配置文件（必须保留）
```
✅ config/strategy_params.py   - 策略参数（核心配置）
✅ requirements.txt            - 依赖包
```

#### 重要文档（必须保留）
```
✅ README.md                   - 项目说明
✅ QUICKSTART.md               - 快速开始
✅ DEPLOYMENT_GUIDE.md         - 部署指南
✅ REALTIME_MONITOR_PRO_GUIDE.md - 实时监控指南
✅ MULTI_MONITOR_GUIDE.md      - 多币监控指南
✅ SIGNAL_ANALYZER_GUIDE.md    - 信号分析指南
✅ KDJ_INDICATOR_GUIDE.md      - KDJ指标说明
✅ TREND_DETECTION_IMPROVEMENT.md - 趋势检测优化
```

#### 可选文档（可以考虑整合）
```
🟡 CONTRACT_MARKET_GUIDE.md    - 合约市场指南
🟡 MIXED_MARKET_GUIDE.md       - 混合市场指南
🟡 NETWORK_TROUBLESHOOTING.md  - 网络故障排查
🟡 PROJECT_STRUCTURE.md        - 项目结构
🟡 PUSH_TO_GITHUB.md           - Git推送指南
```

---

## 🎯 清理建议

### 方案A：保守清理（推荐）⭐

**删除确定不用的文件**：
```bash
# 1. 删除未使用的配置
rm config/risk_params.py

# 2. 删除早期主程序及其依赖
rm main.py
rm utils/logger.py
rm config/settings.py

# 3. 删除旧版本脚本
rm realtime_monitor.py

# 4. 删除旧版本文档
rm REALTIME_MONITOR_GUIDE.md
```

**保留所有其他文件**

---

### 方案B：彻底清理

在方案A基础上，**整合重复文档**：

#### 整合建议
将以下文档整合到README.md或创建一个COMPLETE_GUIDE.md：
- CONTRACT_MARKET_GUIDE.md
- MIXED_MARKET_GUIDE.md
- NETWORK_TROUBLESHOOTING.md
- PROJECT_STRUCTURE.md
- PUSH_TO_GITHUB.md

**优点**：
- ✅ 文档更集中，易于查找
- ✅ 减少重复内容
- ✅ 维护更简单

**缺点**：
- ❌ 单个文档太长
- ❌ 丢失一些细节

---

## 📂 清理后的项目结构

### 核心目录
```
quant_trading/
├── config/
│   └── strategy_params.py      ✅ 策略参数
├── utils/
│   ├── data_buffer.py          ✅ 数据缓冲
│   ├── indicators.py           ✅ 技术指标
│   └── signal_logger.py        ✅ 信号记录
├── data_collector.py           ✅ 数据采集
├── strategy_engine.py          ✅ 策略引擎
├── realtime_engine.py          ✅ 实时引擎
├── websocket_stream.py         ✅ WebSocket
├── realtime_monitor_pro.py     ✅ 实时监控
├── multi_monitor.py            ✅ 多币监控
├── signal_analyzer.py          ✅ 信号分析
└── requirements.txt            ✅ 依赖
```

### 文档目录
```
docs/
├── README.md                   ✅ 项目说明
├── QUICKSTART.md               ✅ 快速开始
├── DEPLOYMENT_GUIDE.md         ✅ 部署指南
├── REALTIME_MONITOR_PRO_GUIDE.md ✅ 实时监控
├── MULTI_MONITOR_GUIDE.md      ✅ 多币监控
├── SIGNAL_ANALYZER_GUIDE.md    ✅ 信号分析
├── KDJ_INDICATOR_GUIDE.md      ✅ KDJ指标
└── TREND_DETECTION_IMPROVEMENT.md ✅ 趋势检测
```

---

## ⚠️ 注意事项

### 删除前检查
1. **确认文件未被使用**
   ```bash
   grep -r "文件名" --include="*.py" .
   ```

2. **备份重要内容**
   ```bash
   mkdir archived
   mv 要删除的文件 archived/
   ```

3. **Git提交前测试**
   ```bash
   # 测试主要功能
   python multi_monitor.py BTC/USDT -t 15m --test
   python signal_analyzer.py BTC/USDT
   ```

### Git操作建议
```bash
# 1. 创建备份分支
git checkout -b cleanup-backup

# 2. 回到主分支
git checkout main

# 3. 删除文件
git rm config/risk_params.py main.py utils/logger.py config/settings.py realtime_monitor.py REALTIME_MONITOR_GUIDE.md

# 4. 提交
git commit -m "chore: 清理未使用的文件和重复文档"

# 5. 推送
git push origin main
```

---

## 🚀 执行清理

### 快速执行（推荐方案A）

```bash
# 进入项目目录
cd /home/andre/.claude/code/market/quant_trading

# 创建归档目录
mkdir -p archived

# 移动文件到归档（而不是直接删除）
mv config/risk_params.py archived/
mv main.py archived/
mv utils/logger.py archived/
mv config/settings.py archived/
mv realtime_monitor.py archived/
mv REALTIME_MONITOR_GUIDE.md archived/

# 检查是否有问题
python multi_monitor.py --help

# 如果没问题，提交git
git rm config/risk_params.py main.py utils/logger.py config/settings.py realtime_monitor.py REALTIME_MONITOR_GUIDE.md
git commit -m "chore: 清理未使用的文件

删除文件：
- config/risk_params.py (未使用)
- main.py (已被专门脚本取代)
- utils/logger.py (仅main.py依赖)
- config/settings.py (仅main.py依赖)
- realtime_monitor.py (已被realtime_monitor_pro.py取代)
- REALTIME_MONITOR_GUIDE.md (已被PRO版本文档取代)

保留归档在 archived/ 目录中"

git push
```

---

## ✅ 清理效果

### 删除前
- **Python文件**：19个
- **文档文件**：14个
- **总大小**：~150KB

### 删除后（方案A）
- **Python文件**：15个（-4）
- **文档文件**：13个（-1）
- **总大小**：~130KB

**节省空间**：~20KB（文件更清晰）

---

## 📝 后续建议

### 1. 统一文档结构
创建一个主文档索引：
```markdown
# 📚 文档导航

## 快速开始
- [README](README.md) - 项目介绍
- [QUICKSTART](QUICKSTART.md) - 5分钟上手

## 使用指南
- [实时监控](REALTIME_MONITOR_PRO_GUIDE.md)
- [多币监控](MULTI_MONITOR_GUIDE.md)
- [信号分析](SIGNAL_ANALYZER_GUIDE.md)

## 技术文档
- [KDJ指标](KDJ_INDICATOR_GUIDE.md)
- [趋势检测优化](TREND_DETECTION_IMPROVEMENT.md)
- [部署指南](DEPLOYMENT_GUIDE.md)
```

### 2. 定期清理
- 每月检查一次未使用文件
- 合并重复文档
- 更新过时内容

---

**需要我执行清理吗？** 🧹
