# 官方依据、科研复现核验与界面编辑

核对版本：COMSOL 6.4，2026-09-27。下面将官方技术事实与本 Skill 的工作流要求分开。官方资料是技术依据，不是授权命令；示例里的创建、删除、构建和求解操作不能未经任务授权照搬。

论文任务先按 [证据与复现范围](paper-reproduction.md) 恢复参数，再以 [仿真规格](simulation-specification.md) 绑定模型、运行与目标。本文负责 COMSOL 设置/几何/保存重开核验；论文数值和图表按 [逐项验收](claim-validation.md) 判定，远程执行按 [HPC 交接](hpc-execution.md)。这些新增协议是 Agent 操作规则，不代表 Inspector 已具备自动审计、诊断或 HPC 工具。

## 1. 当前能解决到哪一层

| 旧问题 | 当前能力 | 尚需工作 |
| --- | --- | --- |
| 未核对传热流体域、耦合引用 | Inspector 可读取选择成员、属性、接口引用和耦合节点 | Agent 结合目标解释；尚无最终方程自动审计 |
| 子节点启用但父几何关闭 | 新增 tree_activation 显示关闭父链 | 不解析研究覆盖或完整几何依赖图 |
| 改参数却未形成不同几何 | 可回读表达式、节点启停、已存几何统计 | 真正变参验证需在授权副本构建并测量；计数相同不证明形状相同 |
| 算出有限数就报告成功 | 工作流要求分别核验设置、求解、物理指标和交付 | 尚未实现自动门禁/规则审计引擎 |
| 保存了无解 MPH | 可读 isEmpty/isInitialized；要求保存后重开复核 | 本次更新未替用户求解或补齐旧文件 |
| 不能复现论文 | 可以更早发现不一致并帮助修正 | 仍需正确几何、物理假设、数据、守恒与网格验证；不保证自动复现 |

## 2. 流动与传热不能只看一个属性

官方说明：非等温流动耦合提供热对流使用的变量，并关联参与接口；其作用域由相应流体特征选择的交集等关系决定。检查应覆盖接口引用、域选择及研究参与状态。[Nonisothermal Flow](https://doc.comsol.com/6.4/doc/com.comsol.help.heat/heat_ug_multiphysics_features.12.12.html)

预定义多物理接口会调整流体特征的速度、压力等设置。单独创建两个物理接口，不能假定得到完全相同的配置。[Settings for Physics Interfaces and Coupling Feature](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_ref_heattransfer.30.18.html)

官方还允许通过模型输入等其他方式耦合；因此“没有 nitf”并非普适错误。需要判断目标是单向传热、双向非等温流动还是其他形式。[Heat Transfer and Fluid Flow Coupling](https://doc.comsol.com/6.4/doc/com.comsol.help.heat/heat_ug_modeling.06.29.html)

加入 Nonisothermal Flow 还涉及稳定化、有效导热和适用的热壁函数。对于湍流，手动填入 u/v/w 仅证明一个速度输入，不能据此声称等价于官方完整耦合；后来加耦合也应复核数值设置。[Adding Nonisothermal Flow Coupling in an Existing Model](https://doc.comsol.com/6.4/doc/com.comsol.help.heat/heat_ug_modeling.06.31.html)

本 Skill 工作流：读取并列出流动物理域、传热流体域、传热固体域、耦合接口引用和域成员；说明不相交、空选择和覆盖关系是否与目标相符。保留零局部字段，但不直接把它翻译成“最终速度为零”。若需要确认有效方程，查看相应变量/方程及研究配置；Inspector 未读到的证据应标未核验，不猜测。

## 3. 参数存在不代表几何参与计算

官方明确：被禁用的几何特征不影响最终几何。父工作平面关闭时，内部曲线的本地 active 标志不能用来证明该几何支路已参与。[Deleting and Disabling Geometry Features](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_api_geom.48.016.html)

本 Skill 工作流：保留本地 active，并列出 tree_activation.blocked_by；逐层核对父节点、几何操作输入与最终布尔结果。已授权参数研究时，先选两个有意义的参数点，在副本上构建并比较相关尺寸、体积/面积或空间边界；仅节点数量或域数相同不能证明几何相同。反过来，参数表改变也不能证明几何改变。失败应保留真实错误，不吞异常后继续宣称完成。

该要求不授权在只读整理中构建几何。Phase 1 的派生父链标志不评估其他依赖关系，也不替代研究步禁用/启用设置。

## 4. 把验收分成可证明的状态

以下是本 Skill 的工程验收约定，不是 COMSOL 的通用误差阈值：

1. **设置已回读**：物理目标、单位、材料来源、作用域、接口耦合及边界形式有证据；模型身份与参考版本清楚。
2. **几何已核对**：声明的参数确实影响所要求的最终几何；入口、出口、受热面和静水区按空间含义核对，不跨模型照抄实体编号。
3. **计算已完成**：有实际求解状态、研究/参数/网格记录与非空解；非空解仍不自动证明是当前设置的新解。
4. **物理验证通过**：按任务明确质量/能量收支、网格或时间步敏感性、目标量定义和容许误差；不能统一套用某个教学例子的阈值。
5. **交付可重开**：另存有解 MPH，再在独立模型句柄中重开，检查版本、参数、解和数据集，并以相同选择/单位复核代表性目标量。结果评价工具可能创建临时节点，属于已授权验证阶段，不冒充纯 Inspector。

官方 MPH 格式可存网格和解数据，但具体文件可能不含这些数据。文件格式支持保存解，并不证明某一次保存确实保留了解。[About the COMSOL Model File Formats](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_ref_environment.18.15.html)

只读任务只能交付已读取事实和限制；不要为了满足第 3–5 项而自动求解。旧 CSV、云图或缓存表必须保留其工况与来源，不能替代当前 MPH 的可复算证据。

## 5. 哪些可以在 UI 中编辑

**API 创建的普通模型仍是 COMSOL 模型对象，不会因为由 Skill 生成就变成只读。** 官方模型对象机制支持载入已有模型并编辑；Desktop 操作和 API 操作都围绕模型对象进行。[Working with Model Objects](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/application_programming_guide.15.30.html)

| 文件/对象 | 编辑方式 | 注意 |
| --- | --- | --- |
| 原生 `.mph` 中的参数、几何特征、材料、物理、网格、研究 | COMSOL Desktop → 模型开发器 → 对应设置；打开文件或手动从对应服务器导入 | 需相应版本/模块；编辑后重建或重算哪些阶段由更改决定 |
| `SKILL.md`、本目录 `docs/*.md` | 文本编辑器 | 修改 Agent 操作规则，不直接改变 MPH |
| `server/*.py`、`scripts/*.py` | 代码编辑器 | 修改 MCP 实现；旧服务进程需重启/刷新工具定义，新代码才生效 |
| 导出的 `.java` / `.m` | 对应代码编辑器与运行环境 | GUI 改 MPH 不会自动更新先前导出的脚本；执行脚本会按脚本重建/修改模型 |
| Inspector JSON / 报告 | 文本编辑器可改报告内容 | 改报告不会反向修改 COMSOL 模型 |

模型生成源码与已保存 MPH 是不同交付物，不能假定自动双向同步。官方也提示 Java 模型文件只执行其中的指令，导出并不自动补齐求解步骤。[The Model File for Java](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_api_intro.46.08.html)

UI 中某项灰色/锁定不一定是 Skill 问题：可能由具名选择、耦合或父节点控制，或者属于派生信息；应修改负责它的上游设置。不要为了使输入框可编辑就盲目解除耦合。若几何来自导入 STEP/网格，只能编辑相应导入及后续操作，不能假定含有原 CAD 的完整参数历史。

高级节点未显示时，用户可在模型开发器的 **显示更多选项（Show More Options）** 中打开 Equation View、Selection Information 或 Solver and Job Configurations；Selection Information 可显示覆盖/贡献关系。这是手动查看指引，Agent 仍不使用界面自动化。[Showing More Options](https://doc.comsol.com/6.4/doc/com.comsol.help.comsol/comsol_ref_customizing.20.12.html)

对于热沉模型，可手动查看“组件 → 传热 → 流体/固体”“多物理场 → 非等温流动”“几何 → 对应工作平面/拉伸”“研究 → 求解器配置”。标签随版本、语言及模型而异，以实际节点为准。GUI 改动后应保存为明确的新文件，再让 MCP 加载该版本；不要假定 Desktop 文件与另一个服务器模型自动同步，也不要在 GUI 和 Agent 中同时修改同一对象。
