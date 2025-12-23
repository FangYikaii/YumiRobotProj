## 修复计划

### 问题分析
程序在处理'executing'指令时闪退，出现QPainter相关错误（递归重绘和未正确关闭的画家对象）。虽然未直接找到QPainter的使用，但推测是UI更新操作导致的递归重绘循环。

### 修复方案
1. **简化executing指令处理逻辑**：
   - 移除executing指令处理中的UI更新操作
   - 删除进度条设置逻辑
   - 移除发送到机器人的控制指令
   - 保留必要的重量数据获取和日志记录

2. **删除远程控制命令输出**：
   - 移除`ctrl_com_logger.info(f"发送到机器人的数据: {repr(send_str)}")`相关代码

3. **优化UI更新机制**：
   - 确保UI更新操作不会触发递归重绘
   - 简化update_curve方法，移除可能导致绘制问题的逻辑

### 具体修改点
1. 修改`on_control_data_received`方法中的executing指令处理逻辑
2. 删除executing指令中的控制指令发送代码
3. 简化executing指令中的UI更新操作
4. 移除控制命令输出日志

### 预期效果
- 解决executing指令导致的闪退问题
- 消除递归重绘和QPainter相关错误
- 保持必要的功能完整性