import socket
import threading
from .logger import data_com_logger, ctrl_com_logger, system_logger, global_logger
from .config_manager import global_config

class TCPCommunication:
    """
    TCP通信类，负责与机器人服务器进行通信
    """
    
    def __init__(self, port=None, comm_type='CTRL_COM'):
        """
        初始化TCP通信类
        
        参数:
            port: 指定端口号，None则使用配置文件中的默认端口
            comm_type: 通讯类型，'CTRL_COM'表示控制通讯，'DATA_COM'表示数据通讯
        """
        self.socket = None
        self.is_connected = False
        self.comm_type = comm_type
        
        # 根据通讯类型选择日志记录器
        if comm_type == 'DATA_COM':
            self.logger = data_com_logger
            self.host = global_config.get('Communication', 'data_host')
            if port is None:
                self.port = global_config.get_int('Communication', 'data_port')
            else:
                self.port = port
        else:  # 默认使用控制通讯
            self.logger = ctrl_com_logger
            self.host = global_config.get('Communication', 'control_host')
            if port is None:
                self.port = global_config.get_int('Communication', 'control_port')
            else:
                self.port = port
        
        self.timeout = global_config.get_float('Communication', 'timeout')
        self.buffer_size = global_config.get_int('Communication', 'buffer_size')
        self.receive_callback = None
        self.error_callback = None
        self.receive_thread = None
        self.stop_event = threading.Event()
    
    def set_callback(self, receive_callback=None, error_callback=None):
        """
        设置回调函数
        
        参数:
            receive_callback: 接收数据回调函数
            error_callback: 错误回调函数
        """
        self.receive_callback = receive_callback
        self.error_callback = error_callback
    
    def connect(self):
        """
        连接到机器人服务器
        
        返回:
            bool: 连接是否成功
        """
        try:
            self.logger.info(f"正在连接到机器人服务器: {self.host}:{self.port}")
            
            # 创建socket对象
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # 设置超时时间
            self.socket.settimeout(self.timeout)
            
            # 连接服务器
            self.socket.connect((self.host, self.port))
            
            self.is_connected = True
            self.logger.info(f"成功连接到机器人服务器: {self.host}:{self.port}")
            
            # 启动接收线程
            self.start_receive_thread()
            
            return True
            
        except socket.timeout:
            self.logger.error(f"连接机器人服务器超时: {self.host}:{self.port}")
            if self.error_callback:
                self.error_callback("连接超时")
            return False
        except ConnectionRefusedError:
            self.logger.error(f"机器人服务器拒绝连接: {self.host}:{self.port}")
            if self.error_callback:
                self.error_callback("连接被拒绝")
            return False
        except Exception as e:
            self.logger.error(f"连接机器人服务器失败: {e}")
            if self.error_callback:
                self.error_callback(f"连接失败: {str(e)}")
            return False
    
    def disconnect(self):
        """
        断开与机器人服务器的连接
        """
        try:
            self.stop_event.set()
            
            if self.socket:
                self.socket.close()
                self.socket = None
            
            self.is_connected = False
            self.logger.info(f"已断开与机器人服务器的连接: {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"断开连接时发生错误: {e}")
    
    def start_receive_thread(self):
        """
        启动接收数据的线程
        """
        self.stop_event.clear()
        self.receive_thread = threading.Thread(target=self._receive_data_loop, daemon=True)
        self.receive_thread.start()
    
    def _receive_data_loop(self):
        """
        接收数据的循环
        """
        while not self.stop_event.is_set() and self.is_connected:
            try:
                # 接收数据
                data = self.socket.recv(self.buffer_size)
                
                if data:
                    # 解码数据
                    data_str = data.decode('ascii')
                    self.logger.info(f"收到机器人服务器数据: {repr(data_str)}")
                    
                    # 调用回调函数处理数据
                    if self.receive_callback:
                        self.receive_callback(data_str)
                else:
                    # 连接已关闭
                    self.logger.warning(f"机器人服务器连接已关闭")
                    self.is_connected = False
                    if self.error_callback:
                        self.error_callback("连接已关闭")
                    break
                    
            except socket.timeout:
                # 超时不处理，继续等待
                continue
            except socket.error as e:
                self.logger.error(f"接收数据时发生socket错误: {e}")
                self.is_connected = False
                if self.error_callback:
                    self.error_callback(f"接收错误: {str(e)}")
                break
            except Exception as e:
                self.logger.error(f"接收数据时发生错误: {e}")
                self.is_connected = False
                if self.error_callback:
                    self.error_callback(f"接收错误: {str(e)}")
                break
    
    def send_data(self, data):
        """
        发送数据到机器人服务器
        
        参数:
            data: 要发送的数据
            
        返回:
            bool: 发送是否成功
        """
        try:
            if not self.is_connected or not self.socket:
                self.logger.error("发送数据失败: 未连接到机器人服务器")
                return False
            
            # 确保数据是字符串类型
            if not isinstance(data, str):
                data = str(data)
            
            # 发送数据
            self.socket.send(data.encode('ascii'))
            self.logger.info(f"成功发送数据到机器人服务器: {repr(data)}")
            return True
            
        except socket.error as e:
            self.logger.error(f"发送数据时发生socket错误: {e}")
            self.is_connected = False
            if self.error_callback:
                self.error_callback(f"发送错误: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"发送数据时发生错误: {e}")
            if self.error_callback:
                self.error_callback(f"发送错误: {str(e)}")
            return False
    
    def get_connection_status(self):
        """
        获取连接状态
        
        返回:
            bool: 连接是否成功
        """
        return self.is_connected
    
    def set_server_info(self, host, port):
        """
        设置服务器信息
        
        参数:
            host: 服务器IP地址
            port: 服务器端口
        """
        self.host = host
        self.port = port
        
        # 更新配置文件
        global_config.set('Communication', 'host', host)
        global_config.set('Communication', 'port', port)
    
    def get_server_info(self):
        """
        获取服务器信息
        
        返回:
            tuple: (host, port)
        """
        return (self.host, self.port)
