#!/usr/bin/env python3
"""
外部API配置向导
帮助用户快速配置Twitter、Whale Alert等API
"""

import os
import sys

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_step(number, text):
    print(f"\n{number}. {text}")

def main():
    print("\n🚀 外部API配置向导")
    print_header("欢迎使用量化交易外部数据配置工具")

    print("\n本向导将帮助你配置以下数据源：")
    print("  1. Twitter/X 情绪分析（可选）")
    print("  2. Whale Alert 鲸鱼监控（推荐）")
    print("  3. CryptoPanic 新闻监控（推荐）")

    print("\n" + "="*70)
    choice = input("\n是否继续配置？(y/n): ").strip().lower()
    if choice != 'y':
        print("已取消配置")
        return

    # 检查.env文件
    env_file = '.env'
    env_exists = os.path.exists(env_file)

    if not env_exists:
        print(f"\n⚠️  未找到 {env_file} 文件")
        create = input("是否创建新的 .env 文件？(y/n): ").strip().lower()
        if create == 'y':
            if os.path.exists('.env.example'):
                import shutil
                shutil.copy('.env.example', '.env')
                print(f"✅ 已从 .env.example 创建 {env_file}")
            else:
                with open('.env', 'w') as f:
                    f.write("# 量化交易环境变量\n")
                    f.write("ENVIRONMENT=development\n\n")
                print(f"✅ 已创建新的 {env_file}")
        else:
            print("请先创建 .env 文件")
            return

    # 配置 Whale Alert
    print_header("1/3: Whale Alert API 配置（推荐）")
    print("\nWhale Alert 监控区块链大额交易（鲸鱼活动）")
    print("免费额度：10次/分钟，足够使用")

    print_step(1, "访问官网注册")
    print("   https://whale-alert.io/")

    print_step(2, "获取API Key")
    print("   登录后进入: Dashboard > API > Create API Key")

    whale_key = input("\n请输入你的 Whale Alert API Key（直接回车跳过）: ").strip()

    # 配置 CryptoPanic
    print_header("2/3: CryptoPanic API 配置（推荐）")
    print("\nCryptoPanic 提供加密货币新闻聚合")
    print("免费额度：足够日常使用")

    print_step(1, "访问官网注册")
    print("   https://cryptopanic.com/developers/api/")

    print_step(2, "获取API Key")
    print("   注册后直接显示 API key")

    crypto_key = input("\n请输入你的 CryptoPanic API Key（直接回车使用'free'）: ").strip()
    if not crypto_key:
        crypto_key = "free"

    # Twitter配置说明
    print_header("3/3: Twitter API 配置（可选）")
    print("\nTwitter API 申请较复杂，推荐使用免费的 Nitter 方案")

    print("\n方案选择：")
    print("  A. 使用 Nitter（推荐）")
    print("     - 完全免费，无需API key")
    print("     - 无请求限制")
    print("     - 已内置支持")
    print()
    print("  B. 使用官方 Twitter API")
    print("     - 需要申请开发者账号")
    print("     - 免费tier限制较多")
    print("     - 需要填写API key")

    twitter_choice = input("\n选择方案 (A/B)，直接回车选A: ").strip().upper()

    twitter_key = ""
    if twitter_choice == 'B':
        print("\n获取 Twitter API:")
        print_step(1, "访问 https://developer.twitter.com/")
        print_step(2, "Apply for Developer Account")
        print_step(3, "创建 Project 和 App")
        print_step(4, "复制 Bearer Token")

        twitter_key = input("\n请输入 Bearer Token（直接回车跳过）: ").strip()

    # 写入.env文件
    print("\n" + "="*70)
    print("正在保存配置...")

    with open('.env', 'r') as f:
        lines = f.readlines()

    # 更新或添加配置
    config_map = {
        'WHALE_ALERT_API_KEY': whale_key,
        'CRYPTOPANIC_API_KEY': crypto_key,
        'TWITTER_BEARER_TOKEN': twitter_key,
    }

    updated_lines = []
    added_keys = set()

    for line in lines:
        updated = False
        for key, value in config_map.items():
            if line.startswith(f"{key}=") and value:
                updated_lines.append(f"{key}={value}\n")
                added_keys.add(key)
                updated = True
                break
        if not updated:
            updated_lines.append(line)

    # 添加未存在的key
    if updated_lines and not updated_lines[-1].endswith('\n'):
        updated_lines.append('\n')

    if '# 外部数据源API' not in ''.join(updated_lines):
        updated_lines.append('\n# 外部数据源API\n')

    for key, value in config_map.items():
        if key not in added_keys and value:
            updated_lines.append(f"{key}={value}\n")

    with open('.env', 'w') as f:
        f.writelines(updated_lines)

    print("✅ 配置已保存到 .env 文件")

    # 测试API
    print_header("测试API连接")
    test = input("\n是否测试API连接？(y/n): ").strip().lower()

    if test == 'y':
        print("\n正在测试...")

        # 测试 Whale Alert
        if whale_key:
            print("\n🐋 测试 Whale Alert...")
            try:
                from utils.whale_alert_client import WhaleAlertClient
                client = WhaleAlertClient(whale_key)
                txs = client.get_transactions(min_value=1000000)
                if txs is not None:
                    print(f"   ✅ 成功！获取到 {len(txs)} 笔大额交易")
                else:
                    print("   ⚠️  API可能未激活或速率限制")
            except Exception as e:
                print(f"   ❌ 失败: {e}")

        # 测试 Nitter
        if twitter_choice != 'B':
            print("\n🐦 测试 Nitter (Twitter免费方案)...")
            try:
                from utils.twitter_nitter import NitterClient
                client = NitterClient()
                tweets = client.search_tweets("BTC OR Bitcoin", limit=5)
                if tweets:
                    print(f"   ✅ 成功！获取到 {len(tweets)} 条推文")
                else:
                    print("   ⚠️  可能网络问题或Nitter实例不可用")
            except Exception as e:
                print(f"   ❌ 失败: {e}")

    # 完成
    print_header("配置完成！")
    print("\n✅ 外部API配置成功！")
    print("\n下一步：")
    print("  1. 启动Dashboard查看效果:")
    print("     python start_dashboard.py")
    print()
    print("  2. 或者运行测试:")
    print("     python utils/whale_alert_client.py")
    print("     python utils/twitter_nitter.py")
    print()
    print("  3. 查看详细文档:")
    print("     DASHBOARD_README.md")
    print()

if __name__ == "__main__":
    main()
