import configparser
import os
from .logger import global_logger

class ConfigManager:
    """
    配置管理类，负责处理配置文件的读写操作
    """
    
    def __init__(self, config_file='resources/config.ini'):
        """
        初始化配置管理器
        
        参数:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        # 默认配置
        self.default_config = {
            'Communication': {
                'host': '127.0.0.1',
                'port': '1023',
                'control_host': '127.0.0.1',
                'control_port': '1023',
                'data_host': '127.0.0.1',
                'data_port': '1025',
                'timeout': '30',
                'buffer_size': '10240'
            },
            'File': {
                'excel_file': 'test_file.xlsx',
                'json_file': 'experimental_results.json',
                'results_dir': 'Experimental results'
            },
            'Parameters': {
                'density': '2.11',
                'vial_weight': '9.7',
                'particle_size': '3',
                'simulate_weight': 'True'
            },
            'Logging': {
                'level': 'DEBUG',
                'log_file': 'robot_client.log'
            }
        }
        
        # 加载配置文件，如果不存在则创建默认配置
        self.load_config()
    
    def load_config(self):
        """
        加载配置文件
        """
        try:
            # 检查配置文件是否存在
            if os.path.exists(self.config_file):
                self.config.read(self.config_file, encoding='utf-8')
                global_logger.info(f"配置文件加载成功: {self.config_file}")
            else:
                # 创建默认配置
                self.create_default_config()
        except Exception as e:
            global_logger.error(f"加载配置文件失败: {e}")
            # 创建默认配置
            self.create_default_config()
    
    def create_default_config(self):
        """
        创建默认配置文件
        """
        try:
            # 检查配置文件目录是否存在，不存在则创建
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            # 添加默认配置
            for section, options in self.default_config.items():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                for key, value in options.items():
                    self.config.set(section, key, value)
            
            # 保存配置文件
            self.save_config()
            global_logger.info(f"默认配置文件创建成功: {self.config_file}")
        except Exception as e:
            global_logger.error(f"创建默认配置文件失败: {e}")
    
    def save_config(self):
        """
        保存配置到文件
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            global_logger.info(f"配置文件保存成功: {self.config_file}")
        except Exception as e:
            global_logger.error(f"保存配置文件失败: {e}")
    
    def get(self, section, key, default=None):
        """
        获取配置值
        
        参数:
            section: 配置节名称
            key: 配置项名称
            default: 默认值
            
        返回:
            str: 配置值
        """
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if default is not None:
                return default
            # 尝试从默认配置中获取
            if section in self.default_config and key in self.default_config[section]:
                return self.default_config[section][key]
            global_logger.warning(f"配置项不存在: [{section}] {key}")
            return None
    
    def get_int(self, section, key, default=0):
        """
        获取整数类型的配置值
        
        参数:
            section: 配置节名称
            key: 配置项名称
            default: 默认值
            
        返回:
            int: 配置值
        """
        try:
            return self.config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            if section in self.default_config and key in self.default_config[section]:
                try:
                    return int(self.default_config[section][key])
                except ValueError:
                    pass
            global_logger.warning(f"无法获取整数配置项: [{section}] {key}")
            return default
    
    def get_float(self, section, key, default=0.0):
        """
        获取浮点数类型的配置值
        
        参数:
            section: 配置节名称
            key: 配置项名称
            default: 默认值
            
        返回:
            float: 配置值
        """
        try:
            return self.config.getfloat(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            if section in self.default_config and key in self.default_config[section]:
                try:
                    return float(self.default_config[section][key])
                except ValueError:
                    pass
            global_logger.warning(f"无法获取浮点数配置项: [{section}] {key}")
            return default
    
    def get_boolean(self, section, key, default=False):
        """
        获取布尔类型的配置值
        
        参数:
            section: 配置节名称
            key: 配置项名称
            default: 默认值
            
        返回:
            bool: 配置值
        """
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            if section in self.default_config and key in self.default_config[section]:
                try:
                    return self.default_config[section][key].lower() in ['true', '1', 'yes', 'y']
                except ValueError:
                    pass
            global_logger.warning(f"无法获取布尔配置项: [{section}] {key}")
            return default
    
    def set(self, section, key, value):
        """
        设置配置值
        
        参数:
            section: 配置节名称
            key: 配置项名称
            value: 配置值
        """
        try:
            if not self.config.has_section(section):
                self.config.add_section(section)
            self.config.set(section, key, str(value))
            self.save_config()
            global_logger.info(f"配置项更新成功: [{section}] {key} = {value}")
        except Exception as e:
            global_logger.error(f"设置配置项失败: [{section}] {key} = {value}, 错误: {e}")
    
    def get_all_config(self):
        """
        获取所有配置
        
        返回:
            dict: 所有配置
        """
        config_dict = {}
        for section in self.config.sections():
            config_dict[section] = {}
            for key, value in self.config.items(section):
                config_dict[section][key] = value
        return config_dict

# 创建全局配置实例
global_config = ConfigManager()
