# 命令建模经验（COMSOL 6.2 实测）

这些是特定版本上的已验证模式。所有 COMSOL / MPh / Java API 示例只能通过 MCP 工具执行，不得在外部脚本中绕过 MCP 控制 COMSOL。不同版本先查同版本 API，不能盲目照抄属性字符串。

## 会话和前台

`mph.Server(cores=4, version="6.2", multi=True)` 启动可连接服务器，`mph.Client(port=server.port, host="localhost", version="6.2")` 连接。Desktop 用同一端口连接。`mph.Client()` standalone 与 Desktop 不自动共享模型。所有 Java 操作进入一个专用线程；运行中不要另起线程同时求解/查询同一模型。

可用 `ModelUtil.setServerBusyHandler(ServerBusyHandler(JInt(120000)))` 等待另一客户端释放服务器。它不能替代应用层串行队列。停止 MCP 会话时不执行 `client.clear()`，不能清除其他用户模型；明确区分“断开连接”“退出自建服务器”和“删除某模型”。

MPh/COMSOL 的 `model.save(path)` 会把服务器中模型标签改为输出文件名。多个案例都保存 `final.mph` 时尤其容易冲突；在 `finally` 中恢复该模型原来的唯一 label，并通过实际 Java tag 追踪模型。断开/重连后旧 Java 代理可能失效，要按服务器上的 tag 获取新代理，不能拿旧代理继续查询。

## 几何和选择

几何单位设置 `lengthUnit("mm")` 后，仍给选择框坐标写明确的 `[mm]`。COMSOL 物理表达式按 SI 量纲计算。Java `.set(key, int)` 可能与布尔重载冲突，使用 `jpype.JInt`；实体数组用 `jpype.JArray(jpype.JInt)`。

块的 `selresult=true` 可产生域选择，但不要假设所有 `_bnd` 标签都存在。用 `Explicit` 全域选择再建 `Adjacent`：`entitydim=3`、`outputdim=2`、`input=["allsolid"]`、`interior=false`，得到外表面；用 Box 选择加位置容差锁定载荷面。材料域、载荷面必须检查实际实体和面积。

## 传热边界

### 版本与边界语义检查

新建特征前核查当前版本、具体物理接口支持的类型；创建后回读类型、设置、实体选择及警告。API 调用成功只说明类型可创建，兼容保留类型也可能已过时。对于 COMSOL 6.4 单相流，本地模型核查发现旧 `Inlet`/`Outlet` 与当前 `InletBoundary`/`OutletBoundary` 有区别；不要把此映射泛化到其他模块或版本，也不要全局替换任意同名字串。官方说明旧 Java 文件可能继续创建已退出菜单的旧入口类型：[CFD 兼容性说明，第 55 页](https://cdn.comsol.com/doc/5.4/COMSOL_ReleaseNotes.pdf)。

当前任务明确是新建模型时，不生成已知过时类型。维护旧模型时先保留原文件，在副本迁移，并核对速度/流量/压力形式、湍流输入、回流、选择集和实际方程；无法确认等价时记录差异，不能仅清除警告就宣称修复。只读任务仅报告，不迁移或求解。

`TemperatureBoundary` 的边界温度与 `Inflow` 的上游温度即使数值相同也不自动等价；检查物理意义与热通量表达式。[Inflow 理论](https://doc.comsol.com/6.4/doc/com.comsol.help.heat/heat_ug_theory.07.009.html)。详细验收见 [物性与模型一致性门槛](model-consistency.md)。

```python
ht = c.physics().create('ht', 'HeatTransfer', 'geom1')
hot = ht.create('heaterflux', 'HeatFluxBoundary', 2)
hot.selection().named('heater')
hot.set('q0', 'Pheat/Lheat^2')  # COMSOL inward flux: positive into the solid
conv = ht.create('convection', 'HeatFluxBoundary', 2)
conv.selection().named('cooling')
conv.set('HeatFluxType', 'ConvectiveHeatFlux')
conv.set('h', 'hconv')
conv.set('Text', 'Tamb')
```

`ConvectiveHeatFlux` 在此是 HeatFluxBoundary 的属性值，不能创建成独立物理特征。固体各连接域默认连续；外部对流面不要包含内部材料界面。

## 研究和温度

研究步骤 API 为 `Stationary`、`Transient` 等，不能假设 UI 文本 Time Dependent 就是接口类型。瞬态设置初值并查生成求解器。BDF 示例设置 `consistent="on"`，`initialstepbdfactive="on"`，`initialstepbdf="0.001[s]"`；它不保证任意刚性系统都适合，需要检查真正的初时刻解。

稳态结果与瞬态结果显式绑定各自 Solution dataset。新建耦合算子尽量在求解之前；若求解后添加，则对相应求解器运行 `updateSolution()`，否则已有解可能不认识新增算子。

直接 `MaxVolume` 的 T 设置 degC 可正常换算；COMSOL 6.2 上 `EvalGlobal` 中耦合算子的摄氏单位换算曾保留 Kelvin 数值。稳妥表达式：`comp1.maxtemp((T-273.15[K])/1[K])`，单位 `1`，表头显式写 `Tmax_degC`。不在本已为摄氏的值上再次减 273.15。始终检查环境温度和初始值的数量级。

## 绘图和导出

三维 Surface 的限定域/面需在绘图特征内创建 Selection 子节点：

```python
surface.create('sel1','Selection').selection().set(face_ids)
```

不要假设 `surface.selection()` 可用。CutPlane `quickplane='xz'` 与 Slice 属性不完全相同；按实际节点文档设置。

PNG 导出设置 Image2D/Image3D、plotgroup、pngfilename、`size='manualweb'`、像素宽高；还需 `options1d/options2d/options3d='on'` 才能应用图例等设置。通过 MCP 检查导出节点配置、返回状态与数据，由用户在 COMSOL 中查看最终图；禁止截图或屏幕识别来检查界面。

## 本机文档位置

从 `COMSOL_ROOT/doc/help/wtpwebapps/ROOT/doc/` 查询当前版本的 `com.comsol.help.comsol`、具体模块目录及 API 页面。只读取必要页面，不随本包分发。公开参考：[COMSOL 编程资料入口](https://www.comsol.com/documentation)、[MPh 文档](https://mph.readthedocs.io/en/stable/)。
