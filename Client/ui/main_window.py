from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QGroupBox, QGridLayout, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QFileDialog, QProgressBar, QStatusBar,
    QTabWidget, QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QPalette, QColor
import logging
from core.logger import global_logger, Logger, system_logger, data_com_logger, ctrl_com_logger
from core.config_manager import global_config
from core.communication import TCPCommunication
from core.data_processor import DataProcessor
from core.file_handler import FileHandler
from core.protocol_handler import ProtocolHandler
import os
import json
import time
import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
import numpy as np



class MainWindow(QMainWindow):
    """
    主窗口类，负责UI交互和整体控制
    """
    
    def __init__(self):
        """
        初始化主窗口
        """
        super().__init__()
        
        # 初始化核心组件
        # 尝试获取控制端口，默认使用1023
        try:
            control_port = global_config.get_int('Communication', 'control_port', fallback=global_config.get_int('Communication', 'port', fallback=1023))
        except Exception as e:
            control_port = 1023
            system_logger.info(f"使用默认控制端口: {control_port}")
        
        # 尝试获取数据端口，默认使用1025
        try:
            data_port = global_config.get_int('Communication', 'data_port', fallback=1025)
        except Exception as e:
            data_port = 1025
            system_logger.info(f"使用默认数据端口: {data_port}")
        
        self.tcp_comm = TCPCommunication(control_port, comm_type='CTRL_COM')  # 控制参数通讯客户端
        self.tcp_data_comm = TCPCommunication(data_port, comm_type='DATA_COM')  # 整体数据读取客户端
        self.data_processor = DataProcessor()
        self.file_handler = FileHandler()
        self.protocol_handler = ProtocolHandler()  # 通讯协议处理器
        
        # 设置回调函数
        self.tcp_comm.set_callback(receive_callback=self.on_control_data_received, error_callback=self.on_comm_error)
        self.tcp_data_comm.set_callback(receive_callback=self.on_data_received, error_callback=self.on_comm_error)
        
        # 初始化变量
        self.is_running = False
        self.current_target_weight = None
        self.excel_sheet = None
        self.excel_max_row = 0
        self.excel_max_col = 0
        self.current_row = 1
        self.current_col = 1
        self.current_material = "Unknown"
        self.excel_filename = "Unknown"
        self.current_json_filename = "Unknown"  # 当前物料的JSON文件名
        
        # 曲线相关变量
        self.curve_data = []  # 存储曲线数据，格式：[(time, target_weight, current_weight), ...]
        self.curve_start_time = None  # 曲线开始时间
        self.time_window = 300  # 显示最近5分钟的数据
        
        # 曲线绘图变量
        self.time_axis = []
        self.target_weight_data = []
        self.current_weight_data = []
        
        # 设置窗口标题和大小
        self.setWindowTitle("机器人上位机软件")
        self.setGeometry(100, 100, 1200, 800)  # 增加窗口高度，更好地显示所有内容
        
        # 初始化UI
        self.init_ui()
        
        # 初始化定时器，用于更新UI
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(1000)  # 1秒更新一次
        self.update_timer.start()
    
    def init_ui(self):
        """
        初始化UI
        """
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 设置窗口为最大化状态，让空间填充完整整个界面
        self.showMaximized()
        
        # 主布局：三列水平布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)  # 设置主布局边距
        main_layout.setSpacing(15)  # 设置列间距
        
        # 1. 左列：连接设置、参数配置、数据监控（垂直布局）
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setSpacing(15)  # 设置组间距
        left_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(left_column, stretch=1)  # 设置列宽度比例
        
        # 2. 中列：文件操作（垂直排列）
        middle_column = QWidget()
        middle_layout = QVBoxLayout(middle_column)
        middle_layout.setSpacing(15)  # 设置组间距
        middle_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(middle_column, stretch=1)  # 设置列宽度比例
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # ========== 填充各列内容 ==========
        # 左列：连接设置、参数配置、数据监控（垂直排列）
        self.setup_connection_section()
        self.setup_parameters_section()
        self.setup_monitoring_section()
        
        left_layout.addWidget(self.connection_group, stretch=0)  # 连接设置，不拉伸
        left_layout.addWidget(self.parameters_group, stretch=0)  # 参数配置，不拉伸
        left_layout.addWidget(self.monitoring_group, stretch=1)  # 数据监控，适当拉伸
        
        # 中列：文件操作（垂直排列）
        self.setup_file_section()
        
        middle_layout.addWidget(self.file_group, stretch=1)  # 文件操作，适当拉伸
        
    
    def setup_connection_section(self):
        """
        设置连接设置区域
        """
        self.connection_group = QGroupBox("连接设置")
        conn_layout = QVBoxLayout(self.connection_group)
        conn_layout.setContentsMargins(15, 15, 15, 15)  # 设置组内边距
        conn_layout.setSpacing(15)  # 设置组内控件间距
        
        # 控制指令客户端配置
        control_label = QLabel("控制指令客户端:")
        control_label.setStyleSheet("font-weight: bold;")
        conn_layout.addWidget(control_label, alignment=Qt.AlignLeft)
        
        # 控制客户端IP地址（水平布局）
        control_ip_layout = QHBoxLayout()
        control_ip_layout.setSpacing(10)
        control_ip_label = QLabel("IP地址:")
        control_ip_label.setMinimumWidth(60)  # 固定标签宽度
        control_ip_layout.addWidget(control_ip_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        # 获取控制客户端IP地址
        try:
            control_host = global_config.get('Communication', 'control_host')
        except Exception:
            control_host = global_config.get('Communication', 'host')
        self.control_ip_edit = QLineEdit(control_host)
        self.control_ip_edit.setMinimumHeight(30)
        self.control_ip_edit.setMinimumWidth(120)  # 固定文本框宽度
        control_ip_layout.addWidget(self.control_ip_edit)
        conn_layout.addLayout(control_ip_layout)
        
        # 控制客户端端口（水平布局）
        control_port_layout = QHBoxLayout()
        control_port_layout.setSpacing(10)
        control_port_label = QLabel("端口:")
        control_port_label.setMinimumWidth(60)  # 固定标签宽度
        control_port_layout.addWidget(control_port_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.control_port_edit = QSpinBox()
        self.control_port_edit.setRange(1, 65535)
        # 获取控制客户端端口
        try:
            control_port = global_config.get_int('Communication', 'control_port')
        except Exception:
            control_port = global_config.get_int('Communication', 'port')
        self.control_port_edit.setValue(control_port)
        self.control_port_edit.setMinimumHeight(30)
        self.control_port_edit.setMinimumWidth(120)  # 固定文本框宽度
        control_port_layout.addWidget(self.control_port_edit)
        conn_layout.addLayout(control_port_layout)
        
        # 控制指令客户端连接按钮
        control_conn_layout = QHBoxLayout()
        control_conn_layout.setSpacing(10)
        self.control_connect_btn = QPushButton("连接控制指令客户端")
        self.control_connect_btn.clicked.connect(self.toggle_control_connection)
        self.control_connect_btn.setMinimumHeight(35)
        self.control_connect_btn.setMinimumWidth(150)  # 固定按钮宽度
        control_conn_layout.addWidget(self.control_connect_btn, alignment=Qt.AlignCenter)
        conn_layout.addLayout(control_conn_layout)
        
        # 控制指令客户端状态
        control_status_layout = QHBoxLayout()
        control_status_layout.setSpacing(10)
        control_status_layout.addWidget(QLabel("控制指令客户端状态:"), alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.control_status_label = QLabel("未连接")
        self.control_status_label.setStyleSheet("color: red")
        control_status_layout.addWidget(self.control_status_label)
        conn_layout.addLayout(control_status_layout)
        
        # 数据回传客户端配置
        data_label = QLabel("数据回传客户端:")
        data_label.setStyleSheet("font-weight: bold;")
        conn_layout.addWidget(data_label, alignment=Qt.AlignLeft)
        
        # 数据客户端IP地址（水平布局）
        data_ip_layout = QHBoxLayout()
        data_ip_layout.setSpacing(10)
        data_ip_label = QLabel("IP地址:")
        data_ip_label.setMinimumWidth(60)  # 固定标签宽度
        data_ip_layout.addWidget(data_ip_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        # 获取数据客户端IP地址
        try:
            data_host = global_config.get('Communication', 'data_host')
        except Exception:
            data_host = global_config.get('Communication', 'host')
        self.data_ip_edit = QLineEdit(data_host)
        self.data_ip_edit.setMinimumHeight(30)
        self.data_ip_edit.setMinimumWidth(120)  # 固定文本框宽度
        data_ip_layout.addWidget(self.data_ip_edit)
        conn_layout.addLayout(data_ip_layout)
        
        # 数据客户端端口（水平布局）
        data_port_layout = QHBoxLayout()
        data_port_layout.setSpacing(10)
        data_port_label = QLabel("端口:")
        data_port_label.setMinimumWidth(60)  # 固定标签宽度
        data_port_layout.addWidget(data_port_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.data_port_edit = QSpinBox()
        self.data_port_edit.setRange(1, 65535)
        # 获取数据客户端端口
        try:
            data_port = global_config.get_int('Communication', 'data_port')
        except Exception:
            data_port = 1025
        self.data_port_edit.setValue(data_port)
        self.data_port_edit.setMinimumHeight(30)
        self.data_port_edit.setMinimumWidth(120)  # 固定文本框宽度
        data_port_layout.addWidget(self.data_port_edit)
        conn_layout.addLayout(data_port_layout)
        
        # 数据回传客户端连接按钮
        data_conn_layout = QHBoxLayout()
        data_conn_layout.setSpacing(10)
        self.data_connect_btn = QPushButton("连接数据回传客户端")
        self.data_connect_btn.clicked.connect(self.toggle_data_connection)
        self.data_connect_btn.setMinimumHeight(35)
        self.data_connect_btn.setMinimumWidth(150)  # 固定按钮宽度
        data_conn_layout.addWidget(self.data_connect_btn, alignment=Qt.AlignCenter)
        conn_layout.addLayout(data_conn_layout)
        
        # 数据回传客户端状态
        data_status_layout = QHBoxLayout()
        data_status_layout.setSpacing(10)
        data_status_layout.addWidget(QLabel("数据回传客户端状态:"), alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.data_status_label = QLabel("未连接")
        self.data_status_label.setStyleSheet("color: red")
        data_status_layout.addWidget(self.data_status_label)
        conn_layout.addLayout(data_status_layout)
        
        # 全局连接状态
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        status_layout.addWidget(QLabel("全局连接状态:"), alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.status_label = QLabel("未连接")
        self.status_label.setStyleSheet("color: red")
        status_layout.addWidget(self.status_label)
        conn_layout.addLayout(status_layout)
    
    def setup_parameters_section(self):
        """
        设置参数配置区域
        """
        self.parameters_group = QGroupBox("参数配置")
        params_layout = QVBoxLayout(self.parameters_group)
        params_layout.setContentsMargins(15, 15, 15, 15)  # 设置组内边距
        params_layout.setSpacing(15)  # 设置组内控件间距
        
        # 密度
        density_layout = QHBoxLayout()
        density_layout.setSpacing(10)
        density_label = QLabel("密度:")
        density_label.setMinimumWidth(80)  # 固定标签宽度
        density_layout.addWidget(density_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.density_edit = QDoubleSpinBox()
        self.density_edit.setRange(0.1, 10.0)
        self.density_edit.setSingleStep(0.1)
        self.density_edit.setValue(global_config.get_float('Parameters', 'density'))
        self.density_edit.setMinimumHeight(30)
        self.density_edit.setMinimumWidth(120)  # 固定输入框宽度
        density_layout.addWidget(self.density_edit)
        density_unit = QLabel("g/cm³")
        density_unit.setMinimumWidth(50)
        density_layout.addWidget(density_unit, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        params_layout.addLayout(density_layout)
        
        # 颗粒大小
        particle_layout = QHBoxLayout()
        particle_layout.setSpacing(10)
        particle_label = QLabel("颗粒大小:")
        particle_label.setMinimumWidth(80)  # 固定标签宽度
        particle_layout.addWidget(particle_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.particle_edit = QDoubleSpinBox()
        self.particle_edit.setRange(0.1, 10.0)
        self.particle_edit.setSingleStep(0.1)
        self.particle_edit.setValue(global_config.get_float('Parameters', 'particle_size'))
        self.particle_edit.setMinimumHeight(30)
        self.particle_edit.setMinimumWidth(120)  # 固定输入框宽度
        particle_layout.addWidget(self.particle_edit)
        particle_unit = QLabel("mm")
        particle_unit.setMinimumWidth(50)
        particle_layout.addWidget(particle_unit, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        params_layout.addLayout(particle_layout)
        
        # 瓶重
        vial_layout = QHBoxLayout()
        vial_layout.setSpacing(10)
        vial_label = QLabel("瓶重:")
        vial_label.setMinimumWidth(80)  # 固定标签宽度
        vial_layout.addWidget(vial_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.vial_edit = QDoubleSpinBox()
        self.vial_edit.setRange(0.1, 100.0)
        self.vial_edit.setSingleStep(0.1)
        self.vial_edit.setValue(global_config.get_float('Parameters', 'vial_weight'))
        self.vial_edit.setMinimumHeight(30)
        self.vial_edit.setMinimumWidth(120)  # 固定输入框宽度
        vial_layout.addWidget(self.vial_edit)
        vial_unit = QLabel("g")
        vial_unit.setMinimumWidth(50)
        vial_layout.addWidget(vial_unit, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        params_layout.addLayout(vial_layout)
        
        # 模拟重量
        simulate_layout = QHBoxLayout()
        simulate_layout.setSpacing(10)
        simulate_label = QLabel("使用模拟重量:")
        simulate_label.setMinimumWidth(100)  # 固定标签宽度
        simulate_layout.addWidget(simulate_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.simulate_check = QCheckBox()
        self.simulate_check.setChecked(global_config.get_boolean('Parameters', 'simulate_weight'))
        simulate_layout.addWidget(self.simulate_check, alignment=Qt.AlignLeft)
        params_layout.addLayout(simulate_layout)
        
        # 保存按钮
        save_btn = QPushButton("保存参数")
        save_btn.clicked.connect(self.save_parameters)
        save_btn.setMinimumHeight(35)
        params_layout.addWidget(save_btn, alignment=Qt.AlignCenter)
    
    def setup_monitoring_section(self):
        """
        设置数据监控区域
        """
        self.monitoring_group = QGroupBox("数据监控")
        monitoring_layout = QVBoxLayout(self.monitoring_group)
        monitoring_layout.setContentsMargins(15, 15, 15, 15)  # 设置组内边距
        monitoring_layout.setSpacing(15)  # 设置组内控件间距
        
        # 目标重量
        target_layout = QHBoxLayout()
        target_layout.setSpacing(10)
        target_label = QLabel("目标重量:")
        target_label.setMinimumWidth(80)  # 固定标签宽度
        target_layout.addWidget(target_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.target_weight_label = QLineEdit("--")
        self.target_weight_label.setReadOnly(True)  # 设置为只读
        self.target_weight_label.setMinimumHeight(30)  # 设置与IP地址输入框相同的高度
        self.target_weight_label.setMinimumWidth(240)  # 固定显示区域宽度
        self.target_weight_label.setMaximumWidth(240)
        self.target_weight_label.setStyleSheet("border: 1px solid #ccc; padding: 5px; background-color: white;")
        target_layout.addWidget(self.target_weight_label)
        monitoring_layout.addLayout(target_layout)
        
        # 当前重量
        current_layout = QHBoxLayout()
        current_layout.setSpacing(10)
        current_label = QLabel("当前重量:")
        current_label.setMinimumWidth(80)  # 固定标签宽度
        current_layout.addWidget(current_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.current_weight_label = QLineEdit("--")
        self.current_weight_label.setReadOnly(True)  # 设置为只读
        self.current_weight_label.setMinimumHeight(30)  # 设置与IP地址输入框相同的高度
        self.current_weight_label.setMinimumWidth(240)  # 固定显示区域宽度
        self.current_weight_label.setMaximumWidth(240)
        self.current_weight_label.setStyleSheet("border: 1px solid #ccc; padding: 5px; background-color: white;")
        current_layout.addWidget(self.current_weight_label)
        monitoring_layout.addLayout(current_layout)
        
        # 抖动幅度
        shaking_layout = QHBoxLayout()
        shaking_layout.setSpacing(10)
        shaking_label = QLabel("抖动幅度:")
        shaking_label.setMinimumWidth(80)  # 固定标签宽度
        shaking_layout.addWidget(shaking_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.shaking_label = QLineEdit("--")
        self.shaking_label.setReadOnly(True)  # 设置为只读
        self.shaking_label.setMinimumHeight(30)  # 设置与IP地址输入框相同的高度
        self.shaking_label.setMinimumWidth(240)  # 固定显示区域宽度
        self.shaking_label.setMaximumWidth(240)
        self.shaking_label.setStyleSheet("border: 1px solid #ccc; padding: 5px; background-color: white;")
        shaking_layout.addWidget(self.shaking_label)
        monitoring_layout.addLayout(shaking_layout)
        
        # 抖动角度
        angle_layout = QHBoxLayout()
        angle_layout.setSpacing(10)
        angle_label = QLabel("抖动角度:")
        angle_label.setMinimumWidth(80)  # 固定标签宽度
        angle_layout.addWidget(angle_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.angle_label = QLineEdit("--")
        self.angle_label.setReadOnly(True)  # 设置为只读
        self.angle_label.setMinimumHeight(30)  # 设置与IP地址输入框相同的高度
        self.angle_label.setMinimumWidth(240)  # 固定显示区域宽度
        self.angle_label.setMaximumWidth(240)
        self.angle_label.setStyleSheet("border: 1px solid #ccc; padding: 5px; background-color: white;")
        angle_layout.addWidget(self.angle_label)
        monitoring_layout.addLayout(angle_layout)
        
        # 完成进度
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(10)
        progress_label = QLabel("完成进度:")
        progress_label.setMinimumWidth(80)  # 固定标签宽度
        progress_layout.addWidget(progress_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        monitoring_layout.addLayout(progress_layout)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        control_layout.setSpacing(20)
        control_layout.setAlignment(Qt.AlignCenter)
        
        self.start_btn = QPushButton("开始")
        self.start_btn.clicked.connect(self.start_process)
        self.start_btn.setMinimumWidth(150)
        self.start_btn.setMinimumHeight(40)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_process)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumWidth(150)
        self.stop_btn.setMinimumHeight(40)
        control_layout.addWidget(self.stop_btn)
        
        monitoring_layout.addLayout(control_layout)
    
    def setup_file_section(self):
        """
        设置文件操作区域
        """
        self.file_group = QGroupBox("文件操作")
        file_layout = QVBoxLayout(self.file_group)
        file_layout.setContentsMargins(15, 15, 15, 15)  # 设置组内边距
        file_layout.setSpacing(15)  # 设置组内控件间距
        
        # Excel文件选择
        file_row = QHBoxLayout()
        file_row.setSpacing(10)  # 设置水平布局间距
        file_label = QLabel("Excel文件:")
        file_label.setMinimumWidth(80)  # 固定标签宽度
        file_row.addWidget(file_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.excel_path_edit = QLineEdit()
        self.excel_path_edit.setText(global_config.get('File', 'excel_file'))
        self.excel_path_edit.setMinimumHeight(30)  # 设置输入框高度
        file_row.addWidget(self.excel_path_edit, stretch=1)  # 输入框占满剩余空间，自适应宽度
        
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_excel)
        browse_btn.setMinimumWidth(80)  # 设置按钮最小宽度
        browse_btn.setMinimumHeight(30)  # 设置按钮高度
        file_row.addWidget(browse_btn)
        
        file_layout.addLayout(file_row)
        
        # 文件预览表格
        self.excel_table = QTableWidget()
        self.excel_table.setColumnCount(5)
        self.excel_table.setHorizontalHeaderLabels(["物料名", "目标重量", "密度", "颗粒大小", "空瓶重"])
        self.excel_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # 列宽自适应
        self.excel_table.setRowCount(10)  # 设置默认行数
        self.excel_table.setMinimumHeight(300)  # 设置表格最小高度
        file_layout.addWidget(self.excel_table, stretch=1)  # 表格占满剩余空间，自适应高度
        
        # 加载文件按钮
        load_btn = QPushButton("加载文件")
        load_btn.clicked.connect(self.load_excel)
        load_btn.setMinimumWidth(120)  # 设置按钮最小宽度
        load_btn.setMinimumHeight(35)  # 设置按钮高度
        load_btn.setMaximumWidth(200)  # 设置按钮最大宽度
        file_layout.addWidget(load_btn, alignment=Qt.AlignCenter)
        
        # 添加分割线
        separator = QWidget()
        separator.setFixedHeight(2)
        separator.setStyleSheet("background-color: #cccccc;")
        file_layout.addWidget(separator)
        
        # JSON文件管理区域
        self.json_management_group = QGroupBox("实验结果管理")
        json_layout = QVBoxLayout(self.json_management_group)
        json_layout.setContentsMargins(15, 15, 15, 15)  # 设置组内边距
        json_layout.setSpacing(15)  # 设置组内控件间距
        
        # 筛选区域
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)  # 设置水平布局间距
        
        # 物料名称筛选
        material_label = QLabel("物料名称:")
        material_label.setMinimumWidth(80)  # 固定标签宽度
        filter_layout.addWidget(material_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.material_combo = QComboBox()
        self.material_combo.setMinimumHeight(30)  # 设置输入框高度
        self.material_combo.setMinimumWidth(150)  # 设置最小宽度
        self.material_combo.addItem("所有物料")  # 默认选项
        filter_layout.addWidget(self.material_combo)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_json_files)
        refresh_btn.setMinimumWidth(80)  # 设置按钮最小宽度
        refresh_btn.setMinimumHeight(30)  # 设置按钮高度
        filter_layout.addWidget(refresh_btn)
        
        # 清空按钮
        clear_btn = QPushButton("清空筛选")
        clear_btn.clicked.connect(self.clear_json_filters)
        clear_btn.setMinimumWidth(80)  # 设置按钮最小宽度
        clear_btn.setMinimumHeight(30)  # 设置按钮高度
        filter_layout.addWidget(clear_btn)
        
        filter_layout.addStretch(1)  # 添加伸缩项，将按钮推到右侧
        
        json_layout.addLayout(filter_layout)
        
        # JSON文件列表表格
        self.json_table = QTableWidget()
        self.json_table.setColumnCount(4)
        self.json_table.setHorizontalHeaderLabels(["文件名", "物料名", "创建时间", "大小"])
        self.json_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # 列宽自适应
        self.json_table.setRowCount(10)  # 设置默认行数
        self.json_table.setMinimumHeight(200)  # 设置表格最小高度
        json_layout.addWidget(self.json_table, stretch=1)  # 表格占满剩余空间，自适应高度
        
        # 操作按钮区域
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)  # 设置水平布局间距
        
        # 查看按钮
        view_btn = QPushButton("查看选中")
        view_btn.clicked.connect(self.view_selected_json)
        view_btn.setMinimumWidth(100)  # 设置按钮最小宽度
        view_btn.setMinimumHeight(35)  # 设置按钮高度
        actions_layout.addWidget(view_btn)
        
        # 导出按钮
        export_btn = QPushButton("导出选中")
        export_btn.clicked.connect(self.export_selected_json)
        export_btn.setMinimumWidth(100)  # 设置按钮最小宽度
        export_btn.setMinimumHeight(35)  # 设置按钮高度
        actions_layout.addWidget(export_btn)
               
        # 删除按钮
        delete_btn = QPushButton("删除选中")
        delete_btn.clicked.connect(self.delete_selected_json)
        delete_btn.setMinimumWidth(100)  # 设置按钮最小宽度
        delete_btn.setMinimumHeight(35)  # 设置按钮高度
        actions_layout.addWidget(delete_btn)
        
        actions_layout.addStretch(1)  # 添加伸缩项，将按钮推到左侧
        
        json_layout.addLayout(actions_layout)
        
        file_layout.addWidget(self.json_management_group, stretch=1)  # 添加JSON管理组到文件布局
        
        # 初始化JSON文件列表
        self.refresh_json_files()
    
    def save_connection_config(self):
        """
        保存连接配置到配置文件
        """
        control_host = self.control_ip_edit.text()
        control_port = self.control_port_edit.value()
        data_host = self.data_ip_edit.text()
        data_port = self.data_port_edit.value()
        
        # 更新配置
        global_config.set('Communication', 'control_host', control_host)
        global_config.set('Communication', 'control_port', str(control_port))
        global_config.set('Communication', 'data_host', data_host)
        global_config.set('Communication', 'data_port', str(data_port))
        
        system_logger.info("连接配置保存成功")
        self.status_bar.showMessage("连接配置保存成功")
    
    def update_connection_status(self):
        """
        更新连接状态显示
        """
        # 更新控制指令客户端状态
        control_connected = self.tcp_comm.get_connection_status()
        if control_connected:
            self.control_status_label.setText("已连接")
            self.control_status_label.setStyleSheet("color: green")
            self.control_connect_btn.setText("断开控制指令客户端")
        else:
            self.control_status_label.setText("未连接")
            self.control_status_label.setStyleSheet("color: red")
            self.control_connect_btn.setText("连接控制指令客户端")
        
        # 更新数据回传客户端状态
        data_connected = self.tcp_data_comm.get_connection_status()
        if data_connected:
            self.data_status_label.setText("已连接")
            self.data_status_label.setStyleSheet("color: green")
            self.data_connect_btn.setText("断开数据回传客户端")
        else:
            self.data_status_label.setText("未连接")
            self.data_status_label.setStyleSheet("color: red")
            self.data_connect_btn.setText("连接数据回传客户端")
        
        # 更新全局连接状态
        if control_connected and data_connected:
            self.status_label.setText("已连接")
            self.status_label.setStyleSheet("color: green")
        elif control_connected or data_connected:
            self.status_label.setText("部分连接")
            self.status_label.setStyleSheet("color: orange")
        else:
            self.status_label.setText("未连接")
            self.status_label.setStyleSheet("color: red")
    
    def toggle_control_connection(self):
        """
        切换控制指令客户端连接状态
        """
        if self.tcp_comm.get_connection_status():
            # 断开连接
            self.tcp_comm.disconnect()
            self.status_bar.showMessage("已断开控制指令客户端连接")
        else:
            # 保存连接配置
            self.save_connection_config()
            
            # 连接到服务器
            control_host = self.control_ip_edit.text()
            control_port = self.control_port_edit.value()
            
            # 设置控制参数客户端信息
            self.tcp_comm.set_server_info(control_host, control_port)
            
            # 连接控制指令客户端
            control_connected = self.tcp_comm.connect()
            
            if control_connected:
                self.status_bar.showMessage(f"已连接到控制端 {control_host}:{control_port}")
            else:
                self.status_bar.showMessage("控制指令客户端连接失败，请检查服务器状态")
        
        # 更新连接状态
        self.update_connection_status()
    
    def toggle_data_connection(self):
        """
        切换数据回传客户端连接状态
        """
        if self.tcp_data_comm.get_connection_status():
            # 断开连接
            self.tcp_data_comm.disconnect()
            self.status_bar.showMessage("已断开数据回传客户端连接")
        else:
            # 保存连接配置
            self.save_connection_config()
            
            # 连接到服务器
            data_host = self.data_ip_edit.text()
            data_port = self.data_port_edit.value()
            
            # 设置数据读取客户端信息
            self.tcp_data_comm.set_server_info(data_host, data_port)
            
            # 连接数据回传客户端
            data_connected = self.tcp_data_comm.connect()
            
            if data_connected:
                self.status_bar.showMessage(f"已连接到数据端 {data_host}:{data_port}")
            else:
                self.status_bar.showMessage("数据回传客户端连接失败，请检查服务器状态")
        
        # 更新连接状态
        self.update_connection_status()
    
    def toggle_connection(self):
        """
        切换全局连接状态
        """
        # 保存连接配置
        self.save_connection_config()
        
        control_connected = self.tcp_comm.get_connection_status()
        data_connected = self.tcp_data_comm.get_connection_status()
        
        if control_connected or data_connected:
            # 断开所有连接
            self.tcp_comm.disconnect()
            self.tcp_data_comm.disconnect()
            self.status_bar.showMessage("已断开所有连接")
        else:
            # 连接所有客户端
            control_host = self.control_ip_edit.text()
            control_port = self.control_port_edit.value()
            data_host = self.data_ip_edit.text()
            data_port = self.data_port_edit.value()
            
            # 设置客户端信息
            self.tcp_comm.set_server_info(control_host, control_port)
            self.tcp_data_comm.set_server_info(data_host, data_port)
            
            # 连接客户端
            control_connected = self.tcp_comm.connect()
            data_connected = self.tcp_data_comm.connect()
            
            if control_connected and data_connected:
                self.status_bar.showMessage(f"已连接到控制端 {control_host}:{control_port} 和数据端 {data_host}:{data_port}")
            else:
                self.status_bar.showMessage("部分连接失败，请检查服务器状态")
        
        # 更新连接状态
        self.update_connection_status()
    
    def save_parameters(self):
        """
        保存参数到配置文件
        """
        # 更新配置
        global_config.set('Parameters', 'density', str(self.density_edit.value()))
        global_config.set('Parameters', 'particle_size', str(self.particle_edit.value()))
        global_config.set('Parameters', 'vial_weight', str(self.vial_edit.value()))
        global_config.set('Parameters', 'simulate_weight', str(self.simulate_check.isChecked()))
        
        system_logger.info("参数保存成功")
        self.status_bar.showMessage("参数保存成功")
    
    def browse_excel(self):
        """
        浏览选择Excel文件
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.excel_path_edit.setText(file_path)
    
    def load_excel(self):
        """
        加载Excel文件并显示预览
        """
        file_path = self.excel_path_edit.text()
        if not file_path:
            self.status_bar.showMessage("请选择Excel文件")
            return
        
        # 更新配置
        global_config.set('File', 'excel_file', file_path)
        
        # 读取Excel文件
        sheet, max_row, max_col = self.file_handler.read_excel(file_path)
        if not sheet:
            self.status_bar.showMessage("Excel文件加载失败")
            return
        
        self.excel_sheet = sheet
        self.excel_max_row = max_row
        self.excel_max_col = max_col
        
        # 计算实际数据行数（跳过标题行）
        actual_data_rows = max_row - 1
        
        # 更新表格行数，只显示前20行数据
        self.excel_table.setRowCount(min(actual_data_rows, 20))
        
        # 从第2行开始读取数据（跳过标题行）
        for excel_row in range(2, min(max_row + 1, 22)):  # 处理Excel行2到行21（共20行数据）
            table_row = excel_row - 2  # 表格行从0开始
            
            for excel_col in range(1, min(max_col + 1, 6)):  # 处理前5列
                table_col = excel_col - 1  # 表格列从0开始
                cell_value = self.file_handler.get_cell_value(sheet, excel_row, excel_col)
                item = QTableWidgetItem(str(cell_value) if cell_value is not None else "")
                self.excel_table.setItem(table_row, table_col, item)
        
        # 保存Excel文件名（不包含路径和扩展名）
        self.excel_filename = os.path.splitext(os.path.basename(file_path))[0]
        
        self.status_bar.showMessage(f"Excel文件加载成功，共 {actual_data_rows} 行数据，{max_col} 列")
    
    def is_completed(self):
        """
        检查是否处理完所有数据
        
        返回:
            bool: 是否已处理完所有数据
        """
        if not self.excel_sheet:
            return True
        return self.current_col > self.excel_max_col
    
    def start_process(self):
        """
        开始处理
        """
        if not self.tcp_comm.get_connection_status():
            self.status_bar.showMessage("请先连接到服务器")
            return
        
        # 如果没有加载Excel文件，提示用户
        if not self.excel_sheet:
            self.status_bar.showMessage("请先加载Excel文件")
            return
        
        # 初始化当前行和列
        self.current_row = 1
        
        self.is_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_bar.showMessage("处理中...")

        self.process_timer = QTimer()
        self.process_timer.timeout.connect(self.handle_data)
        self.process_timer.start(1000)  # 每秒处理一次
    
    def stop_process(self):
        """
        停止处理
        """
        self.is_running = False
        
        # 检查是否处理完成所有数据
        if self.is_completed():
            # 遍历完所有数据，禁用开始按钮
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.status_bar.showMessage("所有物料已处理完成")
            system_logger.info("所有物料已处理完成")
        else:
            # 未遍历完所有数据，启用开始按钮，禁用停止按钮
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_bar.showMessage("已停止")
        
        if hasattr(self, 'process_timer'):
            self.process_timer.stop()
        
    def on_control_data_received(self, data_str):
        """
        控制指令客户端数据接收回调
        
        参数:
            data_str: 接收到的数据字符串
        """
        try:
            # 使用协议处理器解析响应
            parsed_response = self.protocol_handler.parse_response(data_str)
            
            if parsed_response:
                command = parsed_response['command']
                data = parsed_response['data']
                
                # 处理new_target指令
                if command == 'new_target':
                    self.protocol_handler.handle_new_target()
                    
                    # 获取新目标重量
                    if self.excel_sheet and not self.is_completed() and self.is_running:
                        # 移动到下一个目标
                        if self.current_row < self.excel_max_row:
                            self.current_row += 1
                        else:
                            self.status_bar.showMessage("所有目标已处理完成")
                            self.stop_process()
                            return
                        
                        # 从Excel获取物料参数（假设列结构：1-物料名，2-目标重量，3-密度，4-颗粒大小，5-空瓶重）
                        material_name = self.file_handler.get_cell_value(self.excel_sheet, self.current_row, 1)  # 第1列：物料名称
                        target_weight_cell = self.file_handler.get_cell_value(self.excel_sheet, self.current_row, 2)  # 第2列：目标重量
                        density_cell = self.file_handler.get_cell_value(self.excel_sheet, self.current_row, 3)  # 第3列：密度
                        particle_size_cell = self.file_handler.get_cell_value(self.excel_sheet, self.current_row, 4)  # 第4列：颗粒大小
                        vial_weight_cell = self.file_handler.get_cell_value(self.excel_sheet, self.current_row, 5)  # 第5列：空瓶重
                        
                        # 保存当前物料名称，用于JSON命名
                        self.current_material = material_name if material_name else "Unknown"
                        
                        # 处理目标重量
                        if target_weight_cell is None or not isinstance(target_weight_cell, (int, float)):
                            system_logger.warning(f"从Excel获取的目标重量无效: {target_weight_cell}，使用测试值 10.0 g")
                            target_weight = 10.0
                        else:
                            target_weight = float(target_weight_cell)
                            system_logger.info(f"获取到有效目标重量: {target_weight} g")
                        
                        # 生成当前物料的JSON文件名
                        timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
                        self.current_json_filename = f"{self.excel_filename}_{self.current_material}_{timestamp}.json"
                        
                        # 处理密度
                        density = None
                        if density_cell is not None and isinstance(density_cell, (int, float)):
                            density = float(density_cell)
                            system_logger.info(f"获取到有效密度: {density}")
                        
                        # 处理颗粒大小
                        particle_size = None
                        if particle_size_cell is not None and isinstance(particle_size_cell, (int, float)):
                            particle_size = float(particle_size_cell)
                            system_logger.info(f"获取到有效颗粒大小: {particle_size}")
                        
                        # 处理空瓶重
                        vial_weight = None
                        if vial_weight_cell is not None and isinstance(vial_weight_cell, (int, float)):
                            vial_weight = float(vial_weight_cell)
                            system_logger.info(f"获取到有效空瓶重: {vial_weight} g")
                        
                        # 更新数据处理器参数
                        self.data_processor.update_parameters(
                            density=density,
                            vial_weight=vial_weight,
                            particle_size=particle_size
                        )
                        
                        # 更新当前目标重量
                        self.current_target_weight = target_weight
                        self.target_weight_label.setText(f"{target_weight:.2f}")
                        
                        # 获取当前重量
                        current_weight = self.data_processor.get_weight()
                        
                        # 计算抖动参数
                        shaking_amplitude, shaking_angle = self.data_processor.calculate_shaking_parameters(
                            self.current_target_weight, current_weight
                        )
                        
                        # 更新UI参数
                        if density is not None and isinstance(density, (int, float)):
                            self.density_edit.setValue(float(density))
                        if particle_size is not None and isinstance(particle_size, (int, float)):
                            self.particle_edit.setValue(float(particle_size))
                        if vial_weight is not None and isinstance(vial_weight, (int, float)):
                            self.vial_edit.setValue(float(vial_weight))
                        
                        # 更新其他UI
                        self.current_weight_label.setText(f"{current_weight:.2f}")
                        self.shaking_label.setText(f"{shaking_amplitude:.2f}")
                        self.angle_label.setText(f"{shaking_angle:.2f}")

                        # 使用协议处理器格式化控制指令
                        send_str = self.protocol_handler.format_control_packet(
                            target_weight,
                            shaking_amplitude,
                            current_weight,
                            shaking_angle
                        )
                        
                        if send_str:
                            self.tcp_comm.send_data(send_str)
                
                # 处理executing指令
                elif command == 'executing':
                    self.protocol_handler.handle_executing(data)

                     # 获取当前重量
                    current_weight = self.data_processor.get_weight()
                    
                    # 如果有目标重量，计算抖动参数并发送
                    if self.current_target_weight and not self.is_completed() and self.is_running:
                        # 计算抖动参数
                        shaking_amplitude, shaking_angle = self.data_processor.calculate_shaking_parameters(
                            self.current_target_weight, current_weight
                        )
                        
                        # 更新UI
                        self.current_weight_label.setText(f"{current_weight:.2f}")
                        self.shaking_label.setText(f"{shaking_amplitude:.2f}")
                        self.angle_label.setText(f"{shaking_angle:.2f}")
                        
                        # 使用协议处理器格式化控制指令
                        send_str = self.protocol_handler.format_control_packet(
                            0,  # executing指令时target_weight为0
                            shaking_amplitude,
                            current_weight,
                            shaking_angle
                        )
                        
                        if send_str:
                            self.tcp_comm.send_data(send_str)
        
        except Exception as e:
            ctrl_com_logger.error(f"处理控制指令数据时发生错误: {e}")
    
    def on_data_received(self, data_str):
        """
        数据回传客户端数据接收回调
        
        参数:
            data_str: 接收到的数据字符串
        """
        try:
            # 处理数据回传客户端的数据
            if self.excel_sheet and not self.is_completed() and self.is_running:
                if data_str != "9 9 9":  # 有效的数据
                    # 解析数据
                    data_parts = data_str.split()
                    if len(data_parts) >= 4:
                        # 格式化数据为字典
                        result_dict = {
                            'accuracy': float(data_parts[0]),
                            'difference': float(data_parts[1]),
                            'target_weight': float(data_parts[2]),
                            'time': float(data_parts[3])
                        }
                        
                        # 保存数据到JSON文件
                        results_dir = global_config.get('File', 'results_dir', 'Experimental results')
                        if not os.path.exists(results_dir):
                            os.makedirs(results_dir)
                        
                        # 使用当前物料的JSON文件名
                        if self.current_json_filename != "Unknown":
                            json_file = os.path.join(results_dir, self.current_json_filename)
                            
                            # 保存新数据
                            with open(json_file, 'a') as f:
                                f.write(json.dumps(result_dict) + '\n')
                            system_logger.info(f"保存数据到JSON文件: {result_dict}")
                        else:
                            system_logger.info(f"不保存数据，当前文件名为Unknown: {result_dict}")
        except Exception as e:
            data_com_logger.error(f"处理数据回传客户端数据时发生错误: {e}")
    
    def on_comm_error(self, error_msg):
        """
        通讯错误回调
        
        参数:
            error_msg: 错误信息
        """
        system_logger.error(f"通讯错误: {error_msg}")
        self.status_bar.showMessage(f"通讯错误: {error_msg}")
  
    def refresh_json_files(self):
        """
        刷新JSON文件列表
        """
        try:
            # 获取结果目录
            results_dir = global_config.get('File', 'results_dir')
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
            
            # 获取所有JSON文件
            json_files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
            
            # 清空表格
            self.json_table.setRowCount(0)
            
            # 清空物料名称下拉框
            self.material_combo.clear()
            self.material_combo.addItem("所有物料")  # 默认选项
            
            # 物料名称集合
            materials = set()
            
            # 添加文件到表格
            for file_name in json_files:
                # 解析文件名，提取物料名称和创建时间
                # 文件名格式：excel_filename_material_timestamp.json
                parts = file_name.split('_')
                if len(parts) >= 3:
                    # 物料名称是倒数第二个部分
                    material = parts[-2]
                    # 时间戳是最后一个部分（去掉.json后缀）
                    timestamp_str = parts[-1].replace('.json', '')
                    try:
                        # 解析时间戳
                        timestamp = time.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        create_time = time.strftime('%Y-%m-%d %H:%M:%S', timestamp)
                    except ValueError:
                        create_time = "未知时间"
                else:
                    material = "Unknown"
                    create_time = "未知时间"
                
                # 获取文件大小
                file_path = os.path.join(results_dir, file_name)
                file_size = os.path.getsize(file_path)
                file_size_str = f"{file_size / 1024:.2f} KB"
                
                # 添加到表格
                row = self.json_table.rowCount()
                self.json_table.insertRow(row)
                
                # 添加文件名
                self.json_table.setItem(row, 0, QTableWidgetItem(file_name))
                # 添加物料名
                self.json_table.setItem(row, 1, QTableWidgetItem(material))
                # 添加创建时间
                self.json_table.setItem(row, 2, QTableWidgetItem(create_time))
                # 添加文件大小
                self.json_table.setItem(row, 3, QTableWidgetItem(file_size_str))
                
                # 添加到物料集合
                materials.add(material)
            
            # 添加物料到下拉框
            for material in sorted(materials):
                self.material_combo.addItem(material)
            
            self.status_bar.showMessage(f"刷新完成，共找到 {len(json_files)} 个JSON文件")
        except Exception as e:
            self.status_bar.showMessage(f"刷新JSON文件列表失败: {str(e)}")
            system_logger.error(f"刷新JSON文件列表失败: {e}")
    
    def clear_json_filters(self):
        """
        清空筛选条件
        """
        self.material_combo.setCurrentIndex(0)  # 选择"所有物料"
        self.refresh_json_files()  # 刷新列表
    
    def view_selected_json(self):
        """
        查看选中的JSON文件
        """
        # 获取选中的行
        selected_rows = set()
        for item in self.json_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            self.status_bar.showMessage("请先选择要查看的JSON文件")
            return
        
        # 只处理第一个选中的文件
        row = list(selected_rows)[0]
        file_name = self.json_table.item(row, 0).text()
        
        # 读取并显示文件内容
        results_dir = global_config.get('File', 'results_dir')
        file_path = os.path.join(results_dir, file_name)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 创建一个新的窗口显示文件内容
            from PyQt5.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QPushButton
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"查看JSON文件: {file_name}")
            dialog.setGeometry(200, 200, 800, 600)
            
            layout = QVBoxLayout(dialog)
            
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(content)
            layout.addWidget(text_edit)
            
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn, alignment=Qt.AlignCenter)
            
            dialog.exec_()
        except Exception as e:
            self.status_bar.showMessage(f"查看JSON文件失败: {str(e)}")
            system_logger.error(f"查看JSON文件失败: {e}")
    
    def export_selected_json(self):
        """
        导出选中的JSON文件
        """
        # 获取选中的行
        selected_rows = set()
        for item in self.json_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            self.status_bar.showMessage("请先选择要导出的JSON文件")
            return
        
        # 选择导出路径
        export_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not export_dir:
            return
        
        # 导出选中的文件
        results_dir = global_config.get('File', 'results_dir')
        exported_count = 0
        
        for row in selected_rows:
            file_name = self.json_table.item(row, 0).text()
            source_path = os.path.join(results_dir, file_name)
            target_path = os.path.join(export_dir, file_name)
            
            try:
                # 复制文件
                import shutil
                shutil.copy2(source_path, target_path)
                exported_count += 1
            except Exception as e:
                self.status_bar.showMessage(f"导出文件 {file_name} 失败: {str(e)}")
                system_logger.error(f"导出文件 {file_name} 失败: {e}")
        
        self.status_bar.showMessage(f"导出完成，共导出 {exported_count} 个文件")
    
    def delete_selected_json(self):
        """
        删除选中的JSON文件
        """
        # 获取选中的行
        selected_rows = set()
        for item in self.json_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            self.status_bar.showMessage("请先选择要删除的JSON文件")
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除选中的 {len(selected_rows)} 个JSON文件吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 删除选中的文件
        results_dir = global_config.get('File', 'results_dir')
        deleted_count = 0
        
        # 按行号从大到小删除，避免索引混乱
        for row in sorted(selected_rows, reverse=True):
            file_name = self.json_table.item(row, 0).text()
            file_path = os.path.join(results_dir, file_name)
            
            try:
                os.remove(file_path)
                self.json_table.removeRow(row)
                deleted_count += 1
            except Exception as e:
                self.status_bar.showMessage(f"删除文件 {file_name} 失败: {str(e)}")
                system_logger.error(f"删除文件 {file_name} 失败: {e}")
        
        self.status_bar.showMessage(f"删除完成，共删除 {deleted_count} 个文件")
        
        # 刷新物料下拉框
        self.refresh_json_files()
    
    def handle_data(self):
        """
        处理数据
        """
        if not self.is_running:
            return
        
        try:
            # 1. 数据回传客户端：发送 'request_data' 到数据服务器
            self.tcp_data_comm.send_data('request_weight')
            
        except Exception as e:
            system_logger.error(f"处理数据时发生错误: {e}")
    
    def closeEvent(self, event):
        """
        关闭窗口时的处理
        """
        # 断开TCP连接
        if self.tcp_comm.get_connection_status():
            self.tcp_comm.disconnect()
        
        if self.tcp_data_comm.get_connection_status():
            self.tcp_data_comm.disconnect()
        
        # 停止定时器
        if hasattr(self, 'process_timer'):
            self.process_timer.stop()
        
        event.accept()
