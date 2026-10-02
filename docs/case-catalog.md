# 经典算例目录

本目录精选 46 个 COMSOL Application Library 教学/验证模型，覆盖全部主要物理场类别、常见耦合及专业模块。它们用于引导 Agent 找到用户已安装且已授权的官方案例，不把官方模型文件打包进仓库。原创示例另列于 `examples/original/`。

另有原创完整案例 **`heat_sink_3d`**：三维铝翅片散热器，10 W 热源、稳态温度场和 0–3600 s 升温过程，附网格细化与能量检查。它由本包 Python 源码直接建模，无需官方模型资源；与下列 46 个条目合计 47 个案例入口。实测范围见 [验证记录](../examples/validation/README.md)。

## 第一次怎么试

1. 完成连接器设置并运行诊断，确认 COMSOL 版本、服务器连接和可用模块。
2. 从下表选择 ID，让 Agent 列出该案例的信息并加载到独立模型；首次先检查几何、材料、物理场、网格和研究树。
3. 只通过 MCP 按案例原有研究顺序求解、更新和验证结果，并另存到专用输出目录。禁止屏幕识别、OCR、截图定位和界面自动化。
4. 最后让用户在连接同一服务器的 COMSOL Desktop 中手动点击 **文件 → COMSOL Multiphysics Server → 从服务器导入 App**，选择本次模型名称，查看模型树与结果。

可直接说：“用 `simple_resistor` 带我做一次三维电流仿真，只通过 MCP 检查模型树、求解并核对电流守恒；禁止屏幕识别，最后提示我手动从服务器导入 App 查看。” 或：“只通过 MCP 加载 `heat_slab`，说明初始条件，运行瞬态传热并比较解析解，最后提示我手动导入查看。”

## 覆盖和验证边界

所有下列路径已在 COMSOL 6.2 安装库核验。状态均为 `catalogued_not_run`：未在发布流程中逐个重新求解，不能把官方教程的结果当作本次 MCP 运行结果。`modules` 是案例所属产品族，不等于完整许可证需求；实际授权在加载模型时确认。文件存在也不代表模块已授权。

“全部主要类别”表示提供可扩展的工作流和各类别入口，不保证所有 COMSOL 版本、全部专业功能或任意耦合都能无需适配地运行。案例保留自身合适的维度，部分入门模型是 1D/2D；不会把低维模型说成三维。目录中的维度来自官方教程 Model Wizard，缺失项在运行时查询。

安装目录下的 CAD、LiveLink、网格与导入工具是辅助能力，不作为新的物理场重复计数。需要这些功能时先检查其插件、外部软件和许可证。

| ID | 方向 | 经典案例 | 向导维度 | 难度 |
|---|---|---|---|---|
| `simple_resistor` | 电流 | [三维电阻器](https://doc.comsol.com/6.2/doc/com.comsol.help.models.acdc.simple_resistor/simple_resistor.html) | 3D | 入门 |
| `capacitor_dc` | AC/DC：静电 | [三维直流电容器](https://doc.comsol.com/6.2/doc/com.comsol.help.models.acdc.capacitor_dc/capacitor_dc.html) | 3D | 入门 |
| `magnetic_wire` | AC/DC：磁场 | [无限长同轴导体磁场](https://doc.comsol.com/6.2/doc/com.comsol.help.models.acdc.magnetic_field_infinite_conductor/magnetic_field_infinite_conductor.html) | 2D | 入门 |
| `eddy_currents` | AC/DC：涡流 | [涡流与集肤效应](https://doc.comsol.com/6.2/doc/com.comsol.help.models.acdc.eddy_currents/eddy_currents.html) | 3D | 进阶 |
| `acoustic_resonator` | 声学 | [亥姆霍兹共振器](https://doc.comsol.com/6.2/doc/com.comsol.help.models.aco.helmholtz_resonator_solvers/helmholtz_resonator_solvers.html) | 2D Axisymmetric | 入门 |
| `species_diffusion` | 化学物质传递 | [多孔微结构有效扩散率](https://doc.comsol.com/6.2/doc/com.comsol.help.models.mph.effective_diffusivity/effective_diffusivity.html) | 2D | 入门 |
| `reaction_kinetics` | 化学物质传递：反应工程 | [Arrhenius 动力学参数估计](https://doc.comsol.com/6.2/doc/com.comsol.help.models.chem.activation_energy/activation_energy.html) | 0D | 入门 |
| `cyclic_voltammetry` | 电化学 | [一维循环伏安](https://doc.comsol.com/6.2/doc/com.comsol.help.models.echem.cyclic_voltammetry_1d/cyclic_voltammetry_1d.html) | 1D | 入门 |
| `flow_cylinder` | 流体流动 | [圆柱绕流](https://doc.comsol.com/6.2/doc/com.comsol.help.models.mph.cylinder_flow/cylinder_flow.html) | 2D | 入门 |
| `heat_slab` | 传热 | [平板瞬态导热](https://doc.comsol.com/6.2/doc/com.comsol.help.models.heat.heat_conduction_in_slab/heat_conduction_in_slab.html) | 1D | 入门 |
| `wave_fresnel` | 光学：波动光学 | [菲涅耳反射与折射](https://doc.comsol.com/6.2/doc/com.comsol.help.models.woptics.fresnel_equations/fresnel_equations.html) | 3D | 入门 |
| `ray_retroreflector` | 光学：射线光学 | [角锥回射器](https://doc.comsol.com/6.2/doc/com.comsol.help.models.roptics.corner_cube_retroreflector/corner_cube_retroreflector.html) | 3D | 入门 |
| `plasma_column` | 等离子体 | [一维正柱放电](https://doc.comsol.com/6.2/doc/com.comsol.help.models.plasma.positive_column_1d/positive_column_1d.html) | 1D | 进阶 |
| `rf_cavity` | 射频 | [电磁谐振腔](https://doc.comsol.com/6.2/doc/com.comsol.help.models.rf.cavity_resonators/cavity_resonators.html) | 3D | 入门 |
| `semiconductor_pn` | 半导体 | [一维 PN 结](https://doc.comsol.com/6.2/doc/com.comsol.help.models.semicond.pn_junction_1d/pn_junction_1d.html) | 1D | 入门 |
| `solid_cantilever` | 结构力学 | [渐变截面悬臂梁](https://doc.comsol.com/6.2/doc/com.comsol.help.models.mph.tapered_cantilever/tapered_cantilever.html) | 2D | 入门 |
| `math_point_source` | 数学：PDE | [点源的偏微分方程模型](https://doc.comsol.com/6.2/doc/com.comsol.help.models.mph.point_source/point_source.html) | 2D | 入门 |
| `math_lorenz` | 数学：ODE | [Lorenz 吸引子](https://doc.comsol.com/6.2/doc/com.comsol.help.models.mph.lorenz_attractor/lorenz_attractor.html) | 3D | 入门 |
| `joule_busbar` | 多物理场：电热 | [母线焦耳热](https://doc.comsol.com/6.2/doc/com.comsol.help.models.mph.busbar/busbar.html) | 运行时确认 | 入门 |
| `thermal_actuator` | 多物理场：电热结构 | [热致动器](https://doc.comsol.com/6.2/doc/com.comsol.help.models.sme.thermal_actuator_tem/thermal_actuator_tem.html) | 3D | 进阶 |
| `conjugate_heat_sink` | 多物理场：流热 | [空气冷却散热器](https://doc.comsol.com/6.2/doc/com.comsol.help.models.heat.heat_sink/heat_sink.html) | 3D | 进阶 |
| `fluid_structure` | 多物理场：流固 | [柔性障碍物的流固耦合](https://doc.comsol.com/6.2/doc/com.comsol.help.models.mems.fluid_structure_interaction/fluid_structure_interaction.html) | 2D | 进阶 |
| `piezoacoustic` | 多物理场：压电声学 | [压电声学换能器](https://doc.comsol.com/6.2/doc/com.comsol.help.models.aco.piezoacoustic_transducer/piezoacoustic_transducer.html) | 2D Axisymmetric | 进阶 |
| `electrostatic_cantilever` | 多物理场：机电/MEMS | [静电驱动悬臂梁](https://doc.comsol.com/6.2/doc/com.comsol.help.models.mems.electrostatically_actuated_cantilever/electrostatically_actuated_cantilever.html) | 3D | 进阶 |
| `battery_1d` | 电化学：电池 | [一维锂离子电池](https://doc.comsol.com/6.2/doc/com.comsol.help.models.battery.li_battery_1d/li_battery_1d.html) | 1D | 进阶 |
| `fuel_cell_mea` | 电化学：燃料电池 | [一维 PEM 膜电极组件](https://doc.comsol.com/6.2/doc/com.comsol.help.models.fce.pem_mea_1d/pem_mea_1d.html) | 1D | 进阶 |
| `corrosion_nail` | 电化学：腐蚀 | [镀锌钉的电偶腐蚀](https://doc.comsol.com/6.2/doc/com.comsol.help.models.corr.galvanized_nail/galvanized_nail.html) | 运行时确认 | 入门 |
| `electrodeposition_trench` | 电化学：电沉积 | [铜沟槽电沉积](https://doc.comsol.com/6.2/doc/com.comsol.help.models.edecm.cu_trench_deposition/cu_trench_deposition.html) | 2D | 进阶 |
| `microfluidic_separator` | 流体流动：微流控 | [受控扩散分离器](https://doc.comsol.com/6.2/doc/com.comsol.help.models.mfl.controlled_diffusion_separator/controlled_diffusion_separator.html) | 3D | 入门 |
| `mixer_power_law` | 流体流动：搅拌 | [幂律流体搅拌](https://doc.comsol.com/6.2/doc/com.comsol.help.models.mixer.power_law_mixer/power_law_mixer.html) | 3D | 进阶 |
| `porous_forchheimer` | 流体流动：多孔介质 | [Forchheimer 多孔流](https://doc.comsol.com/6.2/doc/com.comsol.help.models.porous.forchheimer_flow/forchheimer_flow.html) | 2D | 入门 |
| `subsurface_lens` | 流体流动：地下水 | [低渗透透镜体中的两相流](https://doc.comsol.com/6.2/doc/com.comsol.help.models.ssf.low_permeable_lens/low_permeable_lens.html) | 2D Axisymmetric | 进阶 |
| `pipe_tank` | 流体流动：管流 | [储水罐排放管路](https://doc.comsol.com/6.2/doc/com.comsol.help.models.pipe.discharging_tank/discharging_tank.html) | 2D | 入门 |
| `molecular_capillary` | 流体流动：分子流 | [真空毛细管](https://doc.comsol.com/6.2/doc/com.comsol.help.models.molec.vacuum_capillary/vacuum_capillary.html) | 2D Axisymmetric | 入门 |
| `polymer_cylinder` | 流体流动：聚合物流 | [黏弹性流体绕圆柱](https://doc.comsol.com/6.2/doc/com.comsol.help.models.polymer.cylinder_flow_viscoelastic/cylinder_flow_viscoelastic.html) | 2D | 进阶 |
| `particle_brownian` | 粒子追踪 | [布朗运动](https://doc.comsol.com/6.2/doc/com.comsol.help.models.particle.brownian_motion/brownian_motion.html) | 2D | 入门 |
| `composite_laminate` | 结构力学：复合材料 | [简支复合层合板](https://doc.comsol.com/6.2/doc/com.comsol.help.models.compmat.simply_supported_composite_laminate/simply_supported_composite_laminate.html) | 3D | 进阶 |
| `fatigue_cycles` | 结构力学：疲劳 | [循环计数基准](https://doc.comsol.com/6.2/doc/com.comsol.help.models.fatigue.cycle_counting_benchmark/cycle_counting_benchmark.html) | 2D | 入门 |
| `soil_compression` | 结构力学：岩土 | [土体等向压缩](https://doc.comsol.com/6.2/doc/com.comsol.help.models.geomech.isotropic_compression/isotropic_compression.html) | 2D Axisymmetric | 进阶 |
| `multibody_pendulum` | 结构力学：多体动力学 | [双摆](https://doc.comsol.com/6.2/doc/com.comsol.help.models.mbd.double_pendulum/double_pendulum.html) | 3D | 入门 |
| `nonlinear_stretch` | 结构力学：非线性材料 | [矩形薄片拉伸与起皱](https://doc.comsol.com/6.2/doc/com.comsol.help.models.nsm.sheet_uniaxial_stretching/sheet_uniaxial_stretching.html) | 3D | 进阶 |
| `rotor_beam` | 结构力学：转子动力学 | [简支梁转子](https://doc.comsol.com/6.2/doc/com.comsol.help.models.rotor.simply_supported_beam_rotor/simply_supported_beam_rotor.html) | 3D | 入门 |
| `metal_round_bar` | 材料加工：相变 | [圆棒中的相变](https://doc.comsol.com/6.2/doc/com.comsol.help.models.metproc.phase_transformations_in_a_round_bar/phase_transformations_in_a_round_bar.html) | 2D | 进阶 |
| `thermo_properties` | 物性：液体和气体 | [相包络线](https://doc.comsol.com/6.2/doc/com.comsol.help.models.lgp.phase_envelope/phase_envelope.html) | 运行时确认 | 入门 |
| `optimization_knee` | 数学：优化 | [L 形支架拓扑优化](https://doc.comsol.com/6.2/doc/com.comsol.help.models.opt.loaded_knee/loaded_knee.html) | 2D | 进阶 |
| `uq_ishigami` | 数学：不确定性量化 | [Ishigami 函数敏感性](https://doc.comsol.com/6.2/doc/com.comsol.help.models.uq.ishigami_function_uncertainty_quantification/ishigami_function_uncertainty_quantification.html) | 运行时确认 | 入门 |

## 每个案例的学习目标和验算

### 三维电阻器 · `simple_resistor`

应用库：`ACDC_Module/Introductory_Electric_Currents/simple_resistor.mph`。所属产品族：AC/DC Module。

学习：电势边界与电流守恒；端子电流和等效电阻。

验证：检查端子输入与输出电流一致；将数值电阻与几何和材料参数的解析估算比较。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### 三维直流电容器 · `capacitor_dc`

应用库：`ACDC_Module/Introductory_Electrostatics/capacitor_dc.mph`。所属产品族：AC/DC Module。

学习：电介质、静电场和电容提取。

验证：比较电荷法与电场能量法电容；检查空气域大小和网格敏感性。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### 无限长同轴导体磁场 · `magnetic_wire`

应用库：`ACDC_Module/Introductory_Magnetostatics/magnetic_field_infinite_conductor.mph`。所属产品族：AC/DC Module。

学习：电流激励、同轴几何与磁通密度。

验证：分区域使用安培环路定律对照解析磁场；检查内外导体总电流和网格误差。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### 涡流与集肤效应 · `eddy_currents`

应用库：`ACDC_Module/Introductory_Electromagnetics/eddy_currents.mph`。所属产品族：AC/DC Module。

学习：频域磁场、感应电流与导体损耗。

验证：以集肤深度控制导体网格；检查频率变化与焦耳损耗趋势。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Frequency Domain 

### 亥姆霍兹共振器 · `acoustic_resonator`

应用库：`Acoustics_Module/Tutorials,_Pressure_Acoustics/helmholtz_resonator_solvers.mph`。所属产品族：Acoustics Module。

学习：声压频率响应；不同声学求解策略。

验证：对照低频集中参数共振频率；峰值附近加密频率与网格。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Frequency Domain ；Preset Studies for Selected Physics Interfaces>Adaptive Frequency Sweep ；Preset Studies for Selected Physics Interfaces>Frequency Domain, Modal 

### 多孔微结构有效扩散率 · `species_diffusion`

应用库：`COMSOL_Multiphysics/Diffusion/effective_diffusivity.mph`。所属产品族：COMSOL Multiphysics。

学习：浓度边界、扩散通量与均匀化。

验证：核对入口与出口总通量；比较自由扩散和有效扩散率。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Time Dependent 

### Arrhenius 动力学参数估计 · `reaction_kinetics`

应用库：`Chemical_Reaction_Engineering_Module/Tutorials/activation_energy.mph`。所属产品族：Chemical Reaction Engineering Module。

学习：温度依赖反应速率与参数估计。

验证：比较模型浓度与案例内实验数据；检查 Arrhenius 参数尺度和拟合残差。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Time Dependent 

### 一维循环伏安 · `cyclic_voltammetry`

应用库：`Electrochemistry_Module/Tutorials/cyclic_voltammetry_1d.mph`。所属产品族：Electrochemistry Module。

学习：电位扫描、电极反应与扩散层。

验证：比较正反扫描电流峰；加密电极附近网格和时间步。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：Preset Studies for Selected Physics Interfaces>Cyclic Voltammetry 

### 圆柱绕流 · `flow_cylinder`

应用库：`COMSOL_Multiphysics/Fluid_Dynamics/cylinder_flow.mph`。所属产品族：COMSOL Multiphysics。

学习：层流边界、压降、尾涡和升阻力。

验证：检查流入流出质量守恒；与教程给出的阻力和脱涡量比较。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Time Dependent 

### 平板瞬态导热 · `heat_slab`

应用库：`Heat_Transfer_Module/Tutorials,_Conduction/heat_conduction_in_slab.mph`。所属产品族：Heat Transfer Module。

学习：导热方程、初始温度与时间尺度。

验证：对照教程中的解析温度解；检查空间和时间收敛。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Time Dependent 

### 菲涅耳反射与折射 · `wave_fresnel`

应用库：`Wave_Optics_Module/Verification_Examples/fresnel_equations.mph`。所属产品族：Wave Optics Module。

学习：平面波入射、偏振、反射率和透射率。

验证：对照菲涅耳公式；无损设置检查反射与透射功率之和。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：Preset Studies for Selected Physics Interfaces>Wavelength Domain ；Empty Study 

### 角锥回射器 · `ray_retroreflector`

应用库：`Ray_Optics_Module/Verification_Examples/corner_cube_retroreflector.mph`。所属产品族：Ray Optics Module。

学习：几何光线、反射与方向变化。

验证：检查出射与入射方向反平行；改变入射位置检验几何行为。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：Preset Studies for Selected Physics Interfaces>Ray Tracing 

### 一维正柱放电 · `plasma_column`

应用库：`Plasma_Module/Direct_Current_Discharges/positive_column_1d.mph`。所属产品族：Plasma Module。

学习：带电粒子输运、电子能量和放电平衡。

验证：检查粒子密度非负；检查反应源项与壁面通量平衡和稳态收敛。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Time Dependent 

### 电磁谐振腔 · `rf_cavity`

应用库：`RF_Module/Verification_Examples/cavity_resonators.mph`。所属产品族：RF Module。

学习：电磁本征频率、腔体模态和品质因数。

验证：将本征频率与教程解析值比较；识别简并和高阶模态。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Eigenfrequency ；Empty Study 

### 一维 PN 结 · `semiconductor_pn`

应用库：`Semiconductor_Module/Verification_Examples/pn_junction_1d.mph`。所属产品族：Semiconductor Module。

学习：掺杂、载流子、势垒与结区。

验证：对照耗尽层近似；检查接触电流守恒和偏置连续性。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### 渐变截面悬臂梁 · `solid_cantilever`

应用库：`COMSOL_Multiphysics/Structural_Mechanics/tapered_cantilever.mph`。所属产品族：COMSOL Multiphysics。

学习：固定约束、边界载荷与位移应力。

验证：比较教程梁理论参考值；检查支反力平衡和位移网格收敛。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### 点源的偏微分方程模型 · `math_point_source`

应用库：`COMSOL_Multiphysics/Equation_Based/point_source.mph`。所属产品族：COMSOL Multiphysics。

学习：系数/方程建模、点源与边界条件。

验证：对照教程解析或参考解；避免把点源奇异点最大值作为收敛指标。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### Lorenz 吸引子 · `math_lorenz`

应用库：`COMSOL_Multiphysics/Equation_Based/lorenz_attractor.mph`。所属产品族：COMSOL Multiphysics。

学习：常微分方程、初值敏感性与相图。

验证：缩小时间步比较短时轨迹；长期混沌轨迹不逐点要求重合。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Time Dependent 

教程使用 3D 组件组织模型和相空间曲线；Lorenz 系统本身是三个随时间变化的 ODE，不是三维空间 PDE。

### 母线焦耳热 · `joule_busbar`

应用库：`COMSOL_Multiphysics/Multiphysics/busbar.mph`。所属产品族：COMSOL Multiphysics。

学习：电流产生体热源与温度场。

验证：比较端子电功率和体焦耳热积分；核查热量流出平衡。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。

### 热致动器 · `thermal_actuator`

应用库：`Structural_Mechanics_Module/Thermal-Structure_Interaction/thermal_actuator_tem.mph`。所属产品族：Structural Mechanics Module。

学习：电阻发热、热膨胀与结构位移。

验证：检查电功率和热平衡；比较位移方向及低激励响应趋势。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### 空气冷却散热器 · `conjugate_heat_sink`

应用库：`Heat_Transfer_Module/Tutorials,_Forced_and_Natural_Convection/heat_sink.mph`。所属产品族：Heat Transfer Module。

学习：固体传热与流体带热；真实空气域。

验证：核查固体-流体界面热连续与质量守恒；检查热输入和出口焓流。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### 柔性障碍物的流固耦合 · `fluid_structure`

应用库：`MEMS_Module/Fluid-Structure_Interaction/fluid_structure_interaction.mph`。所属产品族：MEMS Module。

学习：流体压力与黏性载荷、弹性变形和 ALE 移动网格。

验证：检查流固界面速度与力的连续；监测移动网格质量、质量守恒与时间步收敛。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Time Dependent 

### 压电声学换能器 · `piezoacoustic`

应用库：`Acoustics_Module/Piezoelectric_Devices/piezoacoustic_transducer.mph`。所属产品族：Acoustics Module。

学习：电场-结构-声场耦合与辐射。

验证：检查电声耦合方向和共振；比较声辐射功率与输入功率和损耗。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Frequency Domain 

### 静电驱动悬臂梁 · `electrostatic_cantilever`

应用库：`MEMS_Module/Actuators/electrostatically_actuated_cantilever.mph`。所属产品族：MEMS Module。

学习：静电力、弹性变形和变形几何。

验证：低电压下比较力随电压平方变化；逐步增压检查拉入与非线性收敛。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### 一维锂离子电池 · `battery_1d`

应用库：`Battery_Design_Module/Batteries,_Lithium-Ion/li_battery_1d.mph`。所属产品族：Battery Design Module。

学习：多孔电极、颗粒扩散与放电电压。

验证：检查锂守恒、端子电流与荷电状态；不得越过模型定义的电压截止条件。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：Preset Studies for Selected Physics Interfaces>Time Dependent with Initialization 

### 一维 PEM 膜电极组件 · `fuel_cell_mea`

应用库：`Fuel_Cell_and_Electrolyzer_Module/Fuel_Cells/pem_mea_1d.mph`。所属产品族：Fuel Cell & Electrolyzer Module。

学习：膜电极内电流和反应传质。

验证：检查电流连续和反应消耗的法拉第计量；核对极化曲线趋势。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：Preset Studies for Selected Physics Interfaces>Hydrogen Fuel Cell>Stationary with Initialization 

### 镀锌钉的电偶腐蚀 · `corrosion_nail`

应用库：`Corrosion_Module/Galvanic_Corrosion/galvanized_nail.mph`。所属产品族：Corrosion Module。

学习：异种金属电偶、电极反应与电流分布。

验证：检查阳极与阴极总电流平衡；比较保护区与腐蚀区分布。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### 铜沟槽电沉积 · `electrodeposition_trench`

应用库：`Electrodeposition_Module/Tutorials/cu_trench_deposition.mph`。所属产品族：Electrodeposition Module。

学习：电流分布、电沉积速率和形状演化。

验证：用法拉第定律核对沉积质量；监测移动网格质量。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：Preset Studies for Selected Physics Interfaces>Time Dependent with Initialization 

### 受控扩散分离器 · `microfluidic_separator`

应用库：`Microfluidics_Module/Micromixers/controlled_diffusion_separator.mph`。所属产品族：Microfluidics Module。

学习：微通道流动与扩散分离。

验证：检查流量守恒和组分守恒；比较停留时间与扩散时间。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### 幂律流体搅拌 · `mixer_power_law`

应用库：`Mixer_Module/Benchmarks/power_law_mixer.mph`。所属产品族：Mixer Module。

学习：非牛顿黏度与旋转搅拌。

验证：核查扭矩、耗散和输入机械功；加密叶片附近网格。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：Preset Studies for Selected Physics Interfaces>Frozen Rotor 

### Forchheimer 多孔流 · `porous_forchheimer`

应用库：`Porous_Media_Flow_Module/Fluid_Flow/forchheimer_flow.mph`。所属产品族：Porous Media Flow Module。

学习：多孔阻力与非线性压降。

验证：比较低速 Darcy 极限和高速惯性修正；检查流量守恒。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### 低渗透透镜体中的两相流 · `subsurface_lens`

应用库：`Subsurface_Flow_Module/Fluid_Flow/low_permeable_lens.mph`。所属产品族：Subsurface Flow Module。

学习：渗透率分区、两相饱和度与界面不连续。

验证：检查各相体积守恒和饱和度范围；核查透镜界面条件。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Time Dependent 

### 储水罐排放管路 · `pipe_tank`

应用库：`Pipe_Flow_Module/Tutorials/discharging_tank.mph`。所属产品族：Pipe Flow Module。

学习：液位压头、管路压降与初始排放流量。

验证：将管路压降与可用水头比较；核对弯头、阀门和摩擦损失。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### 真空毛细管 · `molecular_capillary`

应用库：`Molecular_Flow_Module/Benchmarks/vacuum_capillary.mph`。所属产品族：Molecular Flow Module。

学习：稀薄气体、壁面作用与真空输运。

验证：与教程基准导流能力比较；检查分子通量平衡及离散收敛。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### 黏弹性流体绕圆柱 · `polymer_cylinder`

应用库：`Polymer_Flow_Module/Verification_Examples/cylinder_flow_viscoelastic.mph`。所属产品族：Polymer Flow Module。

学习：黏弹性本构与流动阻力。

验证：检查低弹性参数下的黏性极限；加密应力梯度区域。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### 布朗运动 · `particle_brownian`

应用库：`Particle_Tracing_Module/Verification_Examples/brownian_motion.mph`。所属产品族：Particle Tracing Module。

学习：随机力与粒子统计。

验证：将均方位移与扩散规律比较；报告粒子数和随机统计误差。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Time Dependent 

### 简支复合层合板 · `composite_laminate`

应用库：`Composite_Materials_Module/Verification_Examples/simply_supported_composite_laminate.mph`。所属产品族：Composite Materials Module。

学习：铺层、各向异性与层合板位移应力。

验证：与教程层合板理论/基准值比较；检查铺层坐标和厚度方向。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### 循环计数基准 · `fatigue_cycles`

应用库：`Fatigue_Module/Verification_Examples/cycle_counting_benchmark.mph`。所属产品族：Fatigue Module。

学习：载荷历程、循环统计与疲劳输入。

验证：与已知序列的循环数量及幅值比较；说明计数规则。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary ；Preset Studies for Selected Physics Interfaces>Fatigue 

### 土体等向压缩 · `soil_compression`

应用库：`Geomechanics_Module/Verification_Examples/isotropic_compression.mph`。所属产品族：Geomechanics Module。

学习：岩土本构、压缩与加载路径。

验证：核对模型定义的压缩曲线；检查单位、初始应力与收敛。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。

### 双摆 · `multibody_pendulum`

应用库：`Multibody_Dynamics_Module/Tutorials/double_pendulum.mph`。所属产品族：Multibody Dynamics Module。

学习：关节约束、重力与刚体动力学。

验证：检查约束误差；在无耗散设置下核对机械能。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Time Dependent 

### 矩形薄片拉伸与起皱 · `nonlinear_stretch`

应用库：`Nonlinear_Structural_Materials_Module/Hyperelasticity/sheet_uniaxial_stretching.mph`。所属产品族：Nonlinear Structural Materials Module。

学习：薄膜/壳建模、大变形与起皱。

验证：比较教程的两种建模策略；检查皱纹对网格和初始缺陷的敏感性。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary ；Preset Studies for Selected Physics Interfaces>Linear Buckling 

### 简支梁转子 · `rotor_beam`

应用库：`Rotordynamics_Module/Tutorials/simply_supported_beam_rotor.mph`。所属产品族：Rotordynamics Module。

学习：转子固有频率与转速相关行为。

验证：与简支梁解析频率/教程基准比较；跟踪模态随转速变化。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Eigenfrequency ；Preset Studies for Selected Physics Interfaces>Time Dependent with FFT 

### 圆棒中的相变 · `metal_round_bar`

应用库：`Metal_Processing_Module/Tutorial_Examples/phase_transformations_in_a_round_bar.mph`。所属产品族：Metal Processing Module。

学习：热历程与相变动力学。

验证：检查各相分数非负且总和合理；核对热量和相变时间尺度。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Time Dependent 

### 相包络线 · `thermo_properties`

应用库：`Liquid_and_Gas_Properties_Module/Tutorials/phase_envelope.mph`。所属产品族：Liquid & Gas Properties Module。

学习：热力学物性包与汽液相平衡。

验证：核对组成归一化、单位和共沸点行为；与教程参考包络比较。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：Preset Studies for Selected Physics Interfaces>Stationary ；General Studies>Stationary 

### L 形支架拓扑优化 · `optimization_knee`

应用库：`Optimization_Module/Topology_Optimization/loaded_knee.mph`。所属产品族：Optimization Module。

学习：设计变量、重量目标与刚度约束。

验证：核对优化前后目标和约束；检查滤波尺度、网格依赖和最终可制造性。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：General Studies>Stationary 

### Ishigami 函数敏感性 · `uq_ishigami`

应用库：`Uncertainty_Quantification_Module/Tutorials/ishigami_function_uncertainty_quantification.mph`。所属产品族：Uncertainty Quantification Module。

学习：输入分布、代理模型与全局敏感性。

验证：与 Ishigami 标准函数的统计/敏感性参考比较；检查采样和代理误差。

先枚举模型研究及其依赖，按原教程顺序运行；不要凭名称猜研究标签。 向导文档出现：Preset Studies for Selected Physics Interfaces>Stationary 

## 缺文件、缺模块或算不完时

先区分“库文件缺失”“缺许可证”“外部资源未找到”“求解失败”。缺文件时在本机应用库按精确文件名查找，并让用户通过 COMSOL 案例库下载或安装对应示例。跨版本改名必须核对教程，不按相似名称静默换模型。缺许可证时给出同方向已授权案例；不能以另一种方程伪装成该专业接口。

复杂模型可以先加载和解释结果树，再缩小参数扫描或降低网格进行教学试跑；所有改动要记录。不得跳过中间研究、删除耦合或改变物理机制后仍声称复现原案例。路径、研究标签、数据集标签和结果变量均以加载后的模型为准。

许可和来源：官方模型及教程属于 COMSOL 的应用库内容，使用者须遵循其 COMSOL 安装许可。本项目只提供原创的案例索引、运行工作流和验证提示。上表链接按已核验的本地帮助路径组成官方 COMSOL 6.2 地址，未逐条验证公网可达性；若版本文档归档地址不同或机器离线，可用 `documentation_relative_path` 在本机帮助文档中定位。
