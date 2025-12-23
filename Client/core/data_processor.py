import random
from .logger import global_logger
from .config_manager import global_config

class DataProcessor:
    """
    数据处理类，负责重量数据获取和抖动参数计算
    """
    
    def __init__(self):
        """
        初始化数据处理类
        """
        # 从配置文件读取参数
        self.density = global_config.get_float('Parameters', 'density')
        self.vial_weight = global_config.get_float('Parameters', 'vial_weight')
        self.particle_size = global_config.get_float('Parameters', 'particle_size')
        self.simulate_weight = global_config.get_boolean('Parameters', 'simulate_weight')
        
        # 串口配置（备用）
        self.serial_port = "COM3"
        self.baudrate = 9600
        self.ser = None
    
    def update_parameters(self, density=None, vial_weight=None, particle_size=None, simulate_weight=None):
        """
        更新参数
        
        参数:
            density: 物料密度
            vial_weight: 空瓶重量
            particle_size: 颗粒大小
            simulate_weight: 是否使用模拟重量数据
            
        返回:
            dict: 更新后的参数
        """
        if density is not None:
            self.density = density
            global_config.set('Parameters', 'density', density)
        
        if vial_weight is not None:
            self.vial_weight = vial_weight
            global_config.set('Parameters', 'vial_weight', vial_weight)
        
        if particle_size is not None:
            self.particle_size = particle_size
            global_config.set('Parameters', 'particle_size', particle_size)
        
        if simulate_weight is not None:
            self.simulate_weight = simulate_weight
            global_config.set('Parameters', 'simulate_weight', simulate_weight)
        
        global_logger.info(f"参数已更新 - 密度: {self.density}, 瓶重: {self.vial_weight} g, 颗粒大小: {self.particle_size}, 模拟重量: {self.simulate_weight}")
        
        # 返回更新后的参数
        return self.get_current_parameters()
    
    def get_weight(self):
        """
        获取重量数据
        
        返回:
            float: 重量数据（g）
        """
        try:
            if self.simulate_weight:
                # 使用模拟重量数据
                weight = self._get_simulate_weight()
            else:
                # 使用真实串口数据
                weight = self._get_serial_weight()
            
            global_logger.info(f"获取到重量数据: {weight} g")
            return weight
            
        except Exception as e:
            global_logger.error(f"获取重量数据失败: {e}")
            # 发生错误时返回模拟重量值
            weight = self._get_simulate_weight()
            global_logger.warning(f"使用模拟重量数据作为备份: {weight} g")
            return weight
    
    def _get_simulate_weight(self):
        """
        获取模拟重量数据
        
        返回:
            float: 模拟重量数据（g）
        """
        # 返回一个随机的模拟重量值，范围在5-15g之间
        weight = random.uniform(5.0, 15.0)
        global_logger.debug(f"生成模拟重量: {weight} g")
        return weight
    
    def _get_serial_weight(self):
        """
        从串口获取重量数据
        
        返回:
            float: 重量数据（g）
        """
        # 注意：这里的串口读取功能需要根据实际硬件进行调整
        # 当前实现为模拟数据，实际使用时需要取消注释并调整代码
        global_logger.warning("串口重量读取功能尚未实现，使用模拟数据")
        return self._get_simulate_weight()
    
    def calculate_shaking_parameters(self, target_weight, current_weight):
        """
        计算抖动参数
        
        参数:
            target_weight: 目标重量（g）
            current_weight: 当前重量（g）
            
        返回:
            tuple: (抖动幅度, 抖动角度)
        """
        try:
            # 基本参数验证
            if target_weight is None or current_weight is None:
                global_logger.warning("检测到None值输入，返回默认抖动参数")
                return (None, None)
            
            # 确保输入为数字类型
            target_weight = float(target_weight)
            current_weight = float(current_weight)
            
            global_logger.debug(f"开始计算抖动参数 - 目标重量: {target_weight} g, 当前重量: {current_weight} g, 密度: {self.density}, 颗粒大小: {self.particle_size}")
            
            # 计算差值和差值百分比
            weight_diff = abs(target_weight - current_weight)
            diff_percent = (weight_diff / target_weight) * 100 if target_weight > 0 else 0
            
            global_logger.debug(f"重量差值: {weight_diff} g, 差值百分比: {diff_percent}%")
            
            # 根据差值百分比计算抖动幅度（差值越大，抖动幅度越大）
            if diff_percent > 50:
                y_shaking = 100  # 大幅度抖动
            elif diff_percent > 20:
                y_shaking = 50   # 中等幅度抖动
            elif diff_percent > 5:
                y_shaking = 20   # 小幅度抖动
            else:
                y_shaking = 5    # 微调
            
            # 根据颗粒大小调整抖动角度（颗粒越大，角度越小）
            if self.particle_size > 5:
                y_angle = 5   # 小角度
            elif self.particle_size > 2:
                y_angle = 10  # 中等角度
            else:
                y_angle = 15  # 大角度
            
            # 根据密度调整参数（密度越大，抖动幅度和角度越小）
            density_factor = 1.0 / self.density
            y_shaking = y_shaking * density_factor
            y_angle = y_angle * density_factor
            
            # 确保参数在合理范围内
            y_shaking = max(1, min(100, y_shaking))
            y_angle = max(1, min(30, y_angle))
            
            global_logger.debug(f"计算完成 - 抖动幅度: {y_shaking}, 抖动角度: {y_angle}")
            return (y_shaking, y_angle)
            
        except Exception as e:
            global_logger.error(f"计算抖动参数时发生错误: {e}")
            return (None, None)
    
    def get_current_parameters(self):
        """
        获取当前参数
        
        返回:
            dict: 当前参数
        """
        return {
            'density': self.density,
            'vial_weight': self.vial_weight,
            'particle_size': self.particle_size,
            'simulate_weight': self.simulate_weight
        }
