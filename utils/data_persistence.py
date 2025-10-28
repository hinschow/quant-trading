"""
数据持久化模块
用于保存和加载历史数据（OI、资金费率等），避免每次重启都重新获取
"""

import json
import os
import time
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataPersistence:
    """数据持久化管理器"""

    def __init__(self, data_dir: str = "data/persistence"):
        """
        初始化数据持久化管理器

        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir

        # 确保目录存在
        os.makedirs(data_dir, exist_ok=True)

        # 文件路径
        self.oi_history_file = os.path.join(data_dir, "oi_history.json")
        self.funding_rate_file = os.path.join(data_dir, "funding_rate_history.json")

        logger.info(f"✅ 数据持久化初始化完成，目录: {data_dir}")

    def save_oi_history(self, oi_history: Dict[str, List[Dict]]) -> bool:
        """
        保存OI历史数据

        Args:
            oi_history: OI历史数据字典
                格式: {
                    'BTC/USDT': [
                        {'timestamp': 1234567890, 'oi': 29806.79, 'price': 114494.0},
                        ...
                    ],
                    ...
                }

        Returns:
            是否保存成功
        """
        try:
            # 添加保存时间戳
            data = {
                'saved_at': time.time(),
                'saved_at_readable': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data': oi_history
            }

            with open(self.oi_history_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"✅ OI历史数据已保存: {len(oi_history)} 个交易对")
            return True

        except Exception as e:
            logger.error(f"❌ 保存OI历史数据失败: {e}")
            return False

    def load_oi_history(self, max_age_hours: int = 24) -> Optional[Dict[str, List[Dict]]]:
        """
        加载OI历史数据

        Args:
            max_age_hours: 数据最大有效期（小时），超过此时间的数据将被忽略

        Returns:
            OI历史数据字典，如果文件不存在或数据过期则返回None
        """
        try:
            if not os.path.exists(self.oi_history_file):
                logger.info("📂 OI历史数据文件不存在，将从头开始")
                return None

            with open(self.oi_history_file, 'r') as f:
                data = json.load(f)

            saved_at = data.get('saved_at', 0)
            current_time = time.time()
            age_hours = (current_time - saved_at) / 3600

            # 检查数据是否过期
            if age_hours > max_age_hours:
                logger.warning(f"⚠️  OI历史数据已过期（{age_hours:.1f}小时），将重新获取")
                return None

            oi_history = data.get('data', {})

            # 清理过期的数据点（只保留最近的数据）
            cleaned_history = {}
            cutoff_time = current_time - (max_age_hours * 3600)

            for symbol, history in oi_history.items():
                # 过滤掉过期的数据点
                valid_data = [
                    point for point in history
                    if point.get('timestamp', 0) > cutoff_time
                ]
                if valid_data:
                    cleaned_history[symbol] = valid_data

            logger.info(f"✅ 已加载OI历史数据: {len(cleaned_history)} 个交易对，"
                       f"数据年龄 {age_hours:.1f}小时")
            return cleaned_history

        except Exception as e:
            logger.error(f"❌ 加载OI历史数据失败: {e}")
            return None

    def save_funding_rate_history(self, funding_history: Dict[str, List[Dict]]) -> bool:
        """
        保存资金费率历史数据

        Args:
            funding_history: 资金费率历史数据
                格式: {
                    'BTC/USDT': [
                        {'timestamp': 1234567890, 'funding_rate': 0.0001},
                        ...
                    ],
                    ...
                }

        Returns:
            是否保存成功
        """
        try:
            data = {
                'saved_at': time.time(),
                'saved_at_readable': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data': funding_history
            }

            with open(self.funding_rate_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"✅ 资金费率历史数据已保存: {len(funding_history)} 个交易对")
            return True

        except Exception as e:
            logger.error(f"❌ 保存资金费率历史数据失败: {e}")
            return False

    def load_funding_rate_history(self, max_age_hours: int = 24) -> Optional[Dict[str, List[Dict]]]:
        """
        加载资金费率历史数据

        Args:
            max_age_hours: 数据最大有效期（小时）

        Returns:
            资金费率历史数据字典
        """
        try:
            if not os.path.exists(self.funding_rate_file):
                logger.info("📂 资金费率历史数据文件不存在，将从头开始")
                return None

            with open(self.funding_rate_file, 'r') as f:
                data = json.load(f)

            saved_at = data.get('saved_at', 0)
            current_time = time.time()
            age_hours = (current_time - saved_at) / 3600

            if age_hours > max_age_hours:
                logger.warning(f"⚠️  资金费率历史数据已过期（{age_hours:.1f}小时），将重新获取")
                return None

            funding_history = data.get('data', {})

            # 清理过期数据
            cleaned_history = {}
            cutoff_time = current_time - (max_age_hours * 3600)

            for symbol, history in funding_history.items():
                valid_data = [
                    point for point in history
                    if point.get('timestamp', 0) > cutoff_time
                ]
                if valid_data:
                    cleaned_history[symbol] = valid_data

            logger.info(f"✅ 已加载资金费率历史数据: {len(cleaned_history)} 个交易对，"
                       f"数据年龄 {age_hours:.1f}小时")
            return cleaned_history

        except Exception as e:
            logger.error(f"❌ 加载资金费率历史数据失败: {e}")
            return None

    def get_data_info(self) -> Dict:
        """
        获取数据文件信息

        Returns:
            数据文件信息字典
        """
        info = {
            'oi_history': {
                'exists': os.path.exists(self.oi_history_file),
                'size': 0,
                'modified_at': None
            },
            'funding_rate': {
                'exists': os.path.exists(self.funding_rate_file),
                'size': 0,
                'modified_at': None
            }
        }

        # OI历史文件信息
        if info['oi_history']['exists']:
            stat = os.stat(self.oi_history_file)
            info['oi_history']['size'] = stat.st_size
            info['oi_history']['modified_at'] = datetime.fromtimestamp(
                stat.st_mtime
            ).strftime('%Y-%m-%d %H:%M:%S')

        # 资金费率文件信息
        if info['funding_rate']['exists']:
            stat = os.stat(self.funding_rate_file)
            info['funding_rate']['size'] = stat.st_size
            info['funding_rate']['modified_at'] = datetime.fromtimestamp(
                stat.st_mtime
            ).strftime('%Y-%m-%d %H:%M:%S')

        return info

    def clear_all_data(self) -> bool:
        """
        清除所有持久化数据（用于测试或重置）

        Returns:
            是否清除成功
        """
        try:
            files_removed = 0

            if os.path.exists(self.oi_history_file):
                os.remove(self.oi_history_file)
                files_removed += 1

            if os.path.exists(self.funding_rate_file):
                os.remove(self.funding_rate_file)
                files_removed += 1

            logger.info(f"✅ 已清除 {files_removed} 个数据文件")
            return True

        except Exception as e:
            logger.error(f"❌ 清除数据失败: {e}")
            return False


# 自动保存装饰器
def auto_save(data_key: str):
    """
    自动保存装饰器

    Args:
        data_key: 数据键名（'oi_history' 或 'funding_rate'）
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)

            # 如果有persistence实例，自动保存
            if hasattr(self, 'persistence') and self.persistence:
                try:
                    if data_key == 'oi_history' and hasattr(self, 'oi_history'):
                        self.persistence.save_oi_history(self.oi_history)
                    elif data_key == 'funding_rate' and hasattr(self, 'funding_history'):
                        self.persistence.save_funding_rate_history(self.funding_history)
                except Exception as e:
                    logger.warning(f"⚠️  自动保存失败: {e}")

            return result
        return wrapper
    return decorator


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("="*60)
    print("数据持久化模块测试")
    print("="*60)

    # 创建持久化管理器
    persistence = DataPersistence()

    # 测试OI数据保存和加载
    print("\n1. 测试OI历史数据保存")
    test_oi_data = {
        'BTC/USDT': [
            {'timestamp': time.time() - 3600, 'oi': 29806.79, 'price': 114494.0},
            {'timestamp': time.time() - 1800, 'oi': 29850.23, 'price': 114520.5},
            {'timestamp': time.time(), 'oi': 29900.45, 'price': 114550.0},
        ],
        'ETH/USDT': [
            {'timestamp': time.time() - 3600, 'oi': 15234.56, 'price': 4250.0},
            {'timestamp': time.time(), 'oi': 15300.78, 'price': 4260.0},
        ]
    }

    success = persistence.save_oi_history(test_oi_data)
    print(f"保存结果: {'成功' if success else '失败'}")

    print("\n2. 测试OI历史数据加载")
    loaded_data = persistence.load_oi_history(max_age_hours=24)
    if loaded_data:
        print(f"加载成功，交易对数: {len(loaded_data)}")
        for symbol, data in loaded_data.items():
            print(f"  {symbol}: {len(data)} 个数据点")
            if data:
                latest = data[-1]
                print(f"    最新: OI={latest['oi']}, 价格={latest['price']}")

    print("\n3. 测试资金费率数据保存和加载")
    test_funding_data = {
        'BTC/USDT': [
            {'timestamp': time.time() - 3600, 'funding_rate': 0.0001},
            {'timestamp': time.time(), 'funding_rate': 0.00012},
        ]
    }

    persistence.save_funding_rate_history(test_funding_data)
    loaded_funding = persistence.load_funding_rate_history(max_age_hours=24)
    if loaded_funding:
        print(f"加载资金费率数据成功: {len(loaded_funding)} 个交易对")

    print("\n4. 获取数据文件信息")
    info = persistence.get_data_info()
    print(f"OI历史文件:")
    print(f"  存在: {info['oi_history']['exists']}")
    print(f"  大小: {info['oi_history']['size']} 字节")
    print(f"  修改时间: {info['oi_history']['modified_at']}")
    print(f"资金费率文件:")
    print(f"  存在: {info['funding_rate']['exists']}")
    print(f"  大小: {info['funding_rate']['size']} 字节")
    print(f"  修改时间: {info['funding_rate']['modified_at']}")

    print("\n5. 测试数据过期清理")
    # 测试加载过期数据（设置很短的有效期）
    old_data = persistence.load_oi_history(max_age_hours=0.001)  # 约3.6秒
    if old_data is None:
        print("✅ 过期数据正确被清理")

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
