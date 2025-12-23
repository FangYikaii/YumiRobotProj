import logging
import os
import time
from logging.handlers import RotatingFileHandler

class Logger:
    """
    日志管理类，负责配置和管理日志记录
    """
    
    def __init__(self, logger_name='RobotClient', log_file='log/robot_client.log', level=logging.DEBUG):
        """
        初始化日志记录器
        
        参数:
            logger_name: 日志记录器名称
            log_file: 日志文件路径
            level: 日志级别
        """
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(level)
        self.logger.propagate = False  # 防止日志重复输出
        
        # 设置日志目录为Client文件夹内的log文件夹
        log_dir = 'log'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 生成带时间戳的日志文件名
        timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
        base_name, ext = os.path.splitext(os.path.basename(log_file))
        log_file = os.path.join(log_dir, f'{base_name}_{timestamp}{ext}')
        
        # 定义日志格式
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 文件处理器 - 支持日志文件轮转
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,           # 保留5个备份文件
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(self.formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # 控制台只输出INFO及以上级别的日志
        console_handler.setFormatter(self.formatter)
        
        # 添加处理器到日志记录器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def get_logger(self):
        """
        获取配置好的日志记录器
        
        返回:
            logging.Logger: 配置好的日志记录器
        """
        return self.logger
    
    def add_custom_handler(self, handler):
        """
        添加自定义日志处理器
        
        参数:
            handler: 自定义日志处理器
        """
        handler.setFormatter(self.formatter)
        self.logger.addHandler(handler)

# 创建三个层级的日志记录器
# 系统日志记录器
system_logger = Logger(logger_name='SYSTEM', log_file='log/system.log').get_logger()

# 数据通讯日志记录器
data_com_logger = Logger(logger_name='DATA_COM', log_file='log/data_com.log').get_logger()

# 控制通讯日志记录器
ctrl_com_logger = Logger(logger_name='CTRL_COM', log_file='log/ctrl_com.log').get_logger()

# 兼容旧代码的全局日志实例
global_logger = Logger().get_logger()
