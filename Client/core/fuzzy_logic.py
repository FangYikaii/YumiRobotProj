from fuzzylogic.classes import Domain, Set, Rule
from fuzzylogic.functions import S, R, trapezoid
from .logger import global_logger

class FuzzyLogicEngine:
    """
    模糊逻辑引擎，负责模糊推理和抖动参数计算
    """
    
    def __init__(self):
        """
        初始化模糊逻辑引擎
        """
        self.rules = None
        self.D = None  # 差值模糊域
        self.density = None  # 密度模糊域
        self.Sa = None  # 抖动幅度模糊域
        self.A = None  # 角度模糊域
        
        # 创建模糊系统
        self.create_fuzzy_system()
    
    def create_fuzzy_system(self):
        """
        创建模糊逻辑系统
        """
        try:
            # 定义模糊域
            self.D = Domain("Difference", -0.1, 2, res=0.02)  # 差值范围
            self.density = Domain("density", 0, 4, res=0.02)  # 密度范围
            self.Sa = Domain("shaking", 0, 20, res=0.1)  # 抖动幅度范围
            self.A = Domain('angle', 10, 40, res=0.1)  # 角度范围
            
            # 定义模糊集合 - 差值
            self.D.small = S(0.2, 0.4)  # 小差值
            self.D.medium = trapezoid(0.2, 0.5, 0.6, 0.8, c_m=1)  # 中等差值
            self.D.large = R(0.6, 0.8)  # 大差值
            
            # 定义模糊集合 - 密度
            self.density.small = S(1.0, 2.5)  # 低密度
            self.density.medium = trapezoid(2, 2.4, 2.8, 3.2, c_m=1)  # 中等密度
            self.density.large = R(3, 3.2)  # 高密度
            
            # 定义模糊集合 - 抖动幅度
            self.Sa.small = S(2, 4)  # 小幅度抖动
            self.Sa.medium = trapezoid(2, 6, 10, 12, c_m=1)  # 中等幅度抖动
            self.Sa.large = R(10, 15)  # 大幅度抖动
            
            # 定义模糊规则
            rules = [
                Rule({(self.D.small, self.density.medium): self.Sa.small}),
                Rule({(self.D.small, self.density.small): self.Sa.small}),
                Rule({(self.D.small, self.density.large): self.Sa.small}),
                Rule({(self.D.medium, self.density.small): self.Sa.medium}),
                Rule({(self.D.medium, self.density.medium): self.Sa.medium}),
                Rule({(self.D.medium, self.density.large): self.Sa.medium}),
                Rule({(self.D.large, self.density.small): self.Sa.large}),
                Rule({(self.D.large, self.density.medium): self.Sa.large}),
                Rule({(self.D.large, self.density.large): self.Sa.large})
            ]
            
            # 合并规则
            self.rules = sum(rules)
            
            global_logger.info("模糊逻辑系统创建成功")
            
        except Exception as e:
            global_logger.error(f"创建模糊逻辑系统失败: {e}")
    
    def fuzzy_inference(self, difference, density_val):
        """
        执行模糊推理
        
        参数:
            difference: 重量差值
            density_val: 物料密度
            
        返回:
            float: 推理得到的抖动幅度
        """
        try:
            if not self.rules:
                global_logger.error("模糊规则未初始化")
                return None
            
            # 输入值必须在模糊域范围内
            difference = max(self.D.min, min(self.D.max, difference))
            density_val = max(self.density.min, min(self.density.max, density_val))
            
            # 构建输入字典
            X = {self.D: difference, self.density: density_val}
            
            # 执行模糊推理
            result = self.rules(X)
            
            global_logger.debug(f"模糊推理 - 差值: {difference}, 密度: {density_val}, 结果: {result}")
            return result
            
        except Exception as e:
            global_logger.error(f"执行模糊推理时发生错误: {e}")
            return None
    
    def calculate_shaking(self, difference, density_val):
        """
        计算抖动参数
        
        参数:
            difference: 重量差值
            density_val: 物料密度
            
        返回:
            tuple: (抖动幅度, 抖动角度)
        """
        try:
            # 使用模糊逻辑计算抖动幅度
            shaking_amplitude = self.fuzzy_inference(difference, density_val)
            
            # 如果模糊推理失败，使用默认值
            if shaking_amplitude is None:
                shaking_amplitude = 10.0
                global_logger.warning("模糊推理失败，使用默认抖动幅度")
            
            # 根据抖动幅度计算抖动角度（简化计算）
            if shaking_amplitude < 5:
                shaking_angle = 15.0  # 小幅度抖动对应大角度
            elif shaking_amplitude < 10:
                shaking_angle = 10.0  # 中等幅度抖动对应中等角度
            else:
                shaking_angle = 5.0   # 大幅度抖动对应小角度
            
            # 确保参数在合理范围内
            shaking_amplitude = max(1, min(20, shaking_amplitude))
            shaking_angle = max(5, min(30, shaking_angle))
            
            global_logger.debug(f"模糊计算 - 抖动幅度: {shaking_amplitude}, 抖动角度: {shaking_angle}")
            return (shaking_amplitude, shaking_angle)
            
        except Exception as e:
            global_logger.error(f"计算抖动参数时发生错误: {e}")
            return (10.0, 10.0)  # 默认值
