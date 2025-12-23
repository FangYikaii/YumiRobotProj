from .logger import global_logger, system_logger

class ProtocolHandler:
    """
    通讯协议处理类，负责处理与机器人的通讯协议
    """
    
    def __init__(self):
        """
        初始化协议处理器
        """
        pass
    
    def format_data_packet(self, target_weight, shaking_amplitude, current_weight, shaking_angle):
        """
        格式化数据数据包
        
        Args:
            target_weight: 目标重量(g)
            shaking_amplitude: 抖动幅度
            current_weight: 当前重量(g)
            shaking_angle: 抖动角度
            
        Returns:
            str: 格式化后的数据包字符串
        """
        try:
            # 按照协议格式组装数据
            packet = f"{target_weight} {shaking_amplitude} {current_weight} {shaking_angle} #"
            return packet
        except Exception as e:
            system_logger.error(f"格式化数据包失败: {e}")
            return None
    
    def format_control_packet(self, target_weight, shaking_amplitude, current_weight, shaking_angle):
        """
        格式化控制指令数据包
        
        Args:
            target_weight: 目标重量(g)
            shaking_amplitude: 抖动幅度
            current_weight: 当前重量(g)
            shaking_angle: 抖动角度
            
        Returns:
            str: 格式化后的控制指令字符串
        """
        try:
            # 控制指令格式："target_weight shaking_amplitude current_weight shaking_angle #"
            packet = f"{target_weight} {shaking_amplitude} {current_weight} {shaking_angle} #"
            # 验证数据包格式
            if self.validate_packet(packet):
                return packet
            else:
                system_logger.warning(f"格式化的控制指令包格式无效: {repr(packet)}")
                return None
        except Exception as e:
            system_logger.error(f"格式化控制指令包失败: {e}")
            return None
    
    def format_data_packet(self, target_weight, shaking_amplitude, current_weight, shaking_angle):
        """
        格式化数据数据包
        
        Args:
            target_weight: 目标重量(g)
            shaking_amplitude: 抖动幅度
            current_weight: 当前重量(g)
            shaking_angle: 抖动角度
            
        Returns:
            str: 格式化后的数据包字符串
        """
        try:
            # 按照协议格式组装数据
            packet = f"{target_weight} {shaking_amplitude} {current_weight} {shaking_angle} #"
            # 验证数据包格式
            if self.validate_packet(packet):
                return packet
            else:
                system_logger.warning(f"格式化的数据包格式无效: {repr(packet)}")
                return None
        except Exception as e:
            global_logger.error(f"格式化数据包失败: {e}")
            return None
    
    def parse_response(self, response):
        """
        解析机器人响应
        
        Args:
            response: 机器人返回的原始响应字符串
            
        Returns:
            dict: 解析后的响应数据，包含指令类型和相关数据
        """
        try:
            response = response.strip()
            
            # 处理new_target指令
            if response == 'new_target':
                return {
                    'command': 'new_target',
                    'data': None
                }
            
            # 处理target指令
            elif response == 'target':
                return {
                    'command': 'target',
                    'data': None
                }
            
            # 处理executing指令
            elif 'executing' in response:
                return {
                    'command': 'executing',
                    'data': response
                }
            
            # 处理其他指令，尝试解析为数据格式
            elif response.endswith('#'):
                # 移除末尾的分隔符
                response = response[:-1]
                
                # 分割数据
                data_parts = response.split()
                
                if len(data_parts) >= 4:
                    return {
                        'command': 'data',
                        'data': {
                            'target_weight': float(data_parts[0]),
                            'shaking_amplitude': float(data_parts[1]),
                            'current_weight': float(data_parts[2]),
                            'shaking_angle': float(data_parts[3])
                        }
                    }
                else:
                    return {
                        'command': 'unknown',
                        'data': response
                    }
            
        except Exception as e:
            system_logger.error(f"解析响应失败: {e}")
            return {
                'command': 'error',
                'data': str(e)
            }
    
    def validate_packet(self, packet):
        """
        验证数据包格式是否正确
        
        Args:
            packet: 要验证的数据包
            
        Returns:
            bool: 格式是否正确
        """
        if not packet or not isinstance(packet, str):
            return False
        
        if not packet.endswith('#'):
            return False
        
        try:
            parts = packet[:-1].split()
            if len(parts) != 4:
                return False
            
            # 验证每个部分是否为数字
            for part in parts:
                float(part)
            
            return True
        except ValueError:
            return False
        except Exception as e:
            system_logger.error(f"验证数据包失败: {e}")
            return False
    
    def handle_new_target(self):
        """
        处理new_target指令
        
        Returns:
            str: 指令处理结果
        """
        try:
            global_logger.info("收到'new_target'指令，准备获取新目标重量")
            return "new_target_ack"
        except Exception as e:
            global_logger.error(f"处理new_target指令失败: {e}")
            return "error"
    
    def handle_executing(self, response):
        """
        处理executing指令
        
        Args:
            response: 完整的executing响应字符串
            
        Returns:
            str: 指令处理结果
        """
        try:
            global_logger.info(f"收到'executing'指令: {repr(response)}")
            return "executing_ack"
        except Exception as e:
            global_logger.error(f"处理executing指令失败: {e}")
            return "error"