# 推送代码到 GitHub 指南

## ✅ Git 仓库已初始化完成

已完成的步骤：
- ✅ Git 仓库初始化
- ✅ 创建 .gitignore 文件
- ✅ 配置 Git 用户信息
- ✅ 添加所有文件到 Git
- ✅ 创建初始提交
- ✅ 添加远程仓库：https://github.com/hinschow/quant-trading.git

## 🔐 需要配置 GitHub 认证

由于服务器环境无法交互式输入密码，你需要在本地完成推送。

### 方案 1：在本地机器上推送（推荐）⭐⭐⭐⭐⭐

#### 步骤 1：克隆当前代码到本地

```bash
# 在本地机器上执行
# 如果服务器 IP 是 xxx.xxx.xxx.xxx
scp -r andre@服务器IP:/home/andre/.claude/code/market/quant_trading ~/Projects/

# 或者使用 rsync
rsync -avz -e ssh andre@服务器IP:/home/andre/.claude/code/market/quant_trading/ ~/Projects/quant_trading/
```

#### 步骤 2：在本地推送到 GitHub

```bash
# 进入项目目录
cd ~/Projects/quant_trading

# 查看 Git 状态
git status
git remote -v

# 推送到 GitHub（会提示输入 GitHub 用户名和密码/Token）
git push -u origin main

# 如果提示需要 Personal Access Token (PAT)：
# 1. 访问 https://github.com/settings/tokens
# 2. 点击 "Generate new token (classic)"
# 3. 勾选 "repo" 权限
# 4. 复制生成的 token
# 5. 推送时输入：
#    Username: hinschow
#    Password: 粘贴你的 token
```

### 方案 2：使用 SSH 密钥（更安全）⭐⭐⭐⭐⭐

#### 步骤 1：生成 SSH 密钥

```bash
# 在服务器上执行
ssh-keygen -t ed25519 -C "hinschow@gmail.com"

# 按 Enter 使用默认路径
# 可以设置密码或直接回车（不设密码）

# 查看公钥
cat ~/.ssh/id_ed25519.pub
```

#### 步骤 2：添加 SSH 公钥到 GitHub

1. 复制上面命令输出的公钥
2. 访问 https://github.com/settings/keys
3. 点击 "New SSH key"
4. 粘贴公钥，保存

#### 步骤 3：更改远程仓库 URL 为 SSH

```bash
cd /home/andre/.claude/code/market/quant_trading

# 更改远程仓库 URL
git remote set-url origin git@github.com:hinschow/quant-trading.git

# 推送
git push -u origin main
```

### 方案 3：使用 GitHub CLI（最简单）⭐⭐⭐⭐

```bash
# 安装 GitHub CLI（如果未安装）
# Ubuntu/Debian:
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# 登录 GitHub
gh auth login

# 推送代码
cd /home/andre/.claude/code/market/quant_trading
git push -u origin main
```

## 📋 推送成功后

推送成功后，你可以访问：
https://github.com/hinschow/quant-trading

查看代码是否上传成功。

## 🔄 日常开发流程

### 1. 在服务器上开发

```bash
cd /home/andre/.claude/code/market/quant_trading

# 修改代码后
git add .
git commit -m "描述你的修改"
git push
```

### 2. 在本地开发

```bash
cd ~/Projects/quant_trading

# 拉取最新代码
git pull

# 修改代码后
git add .
git commit -m "描述你的修改"
git push

# 同步回服务器（如果需要）
rsync -avz ~/Projects/quant_trading/ andre@服务器IP:/home/andre/.claude/code/market/quant_trading/
```

## 🚀 下一步

选择一种方案完成推送后，你可以：

1. ✅ 在本地克隆仓库
2. ✅ 开始开发核心模块
3. ✅ 定期推送代码到 GitHub

## 💡 提示

如果你不确定选哪个方案：
- **本地开发为主** → 选方案 1
- **服务器开发为主** → 选方案 2 或 3
- **团队协作** → 推荐方案 2（SSH）

---

**当前仓库**: https://github.com/hinschow/quant-trading
**本地路径**: /home/andre/.claude/code/market/quant_trading