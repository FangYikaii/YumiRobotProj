import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.logger import global_logger, system_logger

def main():
    """
    主程序入口
    """
    try:
        system_logger.info("机器人上位机软件启动")
        
        # 创建Qt应用实例
        app = QApplication(sys.argv)
        
        # 设置应用风格
        app.setStyle("Fusion")
        
        # 创建主窗口
        window = MainWindow()
        
        # 显示主窗口
        window.show()
        
        # 启动应用的事件循环
        exit_code = app.exec_()
        
        system_logger.info(f"机器人上位机软件退出，退出码: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        system_logger.error(f"主程序启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
