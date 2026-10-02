# 仿真规格与运行身份

规格是论文到求解器的中间记录，不是可直接调用的 MCP API，也不自动创建模型。默认保存为 `simulation/specification.json`；使用 YAML 时保持同一字段与类型。字段名属于本 Skill 的版本化契约。

## 最小契约

| 字段 | 内容 |
| --- | --- |
| `schema_version`, `spec_id`, `revision` | 契约版本、稳定任务 ID、随语义改变递增的整数版本 |
| `scope` | 论文/示例、目标工况、复现级别、原工作流或独立重建、偏差 |
| `sources`, `parameters` | [证据契约](paper-reproduction.md) 的记录，或有哈希的外部文件引用 |
| `geometry`, `selections` | 维数、形状/输入几何、参数引用；域/边界的空间语义与预期测量 |
| `materials` | 本构形式、参数引用、适用条件、材料作用域 |
| `physics`, `couplings` | 方程/接口、作用域、变量传递、单向/双向关系 |
| `boundary_conditions`, `initial_conditions` | 类型、值/参数引用、作用域与工况；不适用用空列表并解释 |
| `mesh`, `study`, `solver` | 离散策略与检查、扫描/时间/频率范围、依赖研究、求解控制与来源 |
| `outputs` | output_id、数学定义、采样/积分/平均方式、选择、单位、工况 |
| `validation_targets` | claim_id、output_id、参考来源、比较规则、阈值依据、物理与离散门槛 |
| `execution`, `repair_budget`, `unresolved` | 实际后端能力引用、资源/迭代限额、阻塞事项 |

所有参数引用和 ID 必须解析。所有关键量有单位（无量纲用 `1`）。缺失值用 null；不得以 `0`、空字符串或 unknown 字符串作为可求解数值。关键缺失引用到受影响 claims，并阻塞那些 claims 的执行；非关键默认设置也记录来源。

## 合成记录示例：缺本构，不能求解

以下是契约示例而非论文数据或完整模型。它故意表示被阻塞的输入；sources 为空、假设材料数值没有被伪装成已查到的论文。空列表不表示物理上确实没有边界/耦合，原因列在 unresolved。

```json
{
  "schema_version": "1.0",
  "spec_id": "synthetic-material-gap",
  "revision": 1,
  "scope": {
    "reproduction_level": "Non-executable",
    "implementation": "undetermined",
    "target": "synthetic displacement claim",
    "deviations": []
  },
  "sources": [],
  "parameters": [
    {
      "parameter_id": "E",
      "meaning": "Young modulus for a synthetic record",
      "original_value": 2.1,
      "original_unit": "MPa",
      "value": 2100000,
      "unit": "Pa",
      "source_type": "assumed",
      "source_ids": [],
      "evidence_status": "unverified",
      "conditions": "synthetic example only",
      "critical": true,
      "affected_claim_ids": ["C1"],
      "assumption": {
        "reason": "illustrate unit conversion, not a material recommendation",
        "range": null,
        "sensitivity_plan": "not executable before constitutive law and geometry are known"
      }
    },
    {
      "parameter_id": "constitutive_law",
      "meaning": "hyperelastic strain-energy law and its parameterization",
      "original_value": null,
      "original_unit": "1",
      "value": null,
      "unit": "1",
      "source_type": "missing",
      "source_ids": [],
      "evidence_status": "missing",
      "conditions": "target deformation regime unresolved",
      "critical": true,
      "affected_claim_ids": ["C1"]
    }
  ],
  "geometry": {"dimension": 3, "definition": null},
  "selections": [],
  "materials": [{"material_id": "M1", "law_parameter_id": "constitutive_law", "parameter_ids": ["E"], "selection_id": null}],
  "physics": [{"physics_id": "P1", "formulation": "solid mechanics", "selection_id": null}],
  "couplings": [],
  "boundary_conditions": [],
  "initial_conditions": [],
  "mesh": {"strategy": null, "convergence_plan": null},
  "study": {"type": null, "conditions": null},
  "solver": {"settings": null, "source_ids": []},
  "outputs": [{"output_id": "O1", "definition": "maximum displacement magnitude", "selection_id": null, "unit": "m", "condition": null}],
  "validation_targets": [{"claim_id": "C1", "output_id": "O1", "reference_source_ids": [], "reference": null, "acceptance": null, "physical_gates": null}],
  "execution": {"backend": null, "capability_record": null},
  "repair_budget": {"max_additional_runs": 0, "reason": "blocked synthetic example"},
  "unresolved": [
    {"id": "U1", "critical": true, "affected_claim_ids": ["C1"], "reason": "constitutive law and its required parameters are missing"},
    {"id": "U2", "critical": true, "affected_claim_ids": ["C1"], "reason": "geometry, selections, boundary/initial conditions, study and coupling applicability are not established"},
    {"id": "U3", "critical": true, "affected_claim_ids": ["C1"], "reason": "mesh/solver plan, output condition, reference and acceptance gates are not established"}
  ]
}
```

不能仅因为 JSON 能解析就说模型可执行。求解前需全部解析受影响的关键字段，并核验单位、量纲、本构参数、材料覆盖、选择与研究依赖。没有公开代码但上述信息完整时，可进入有据可查的独立重建分支。

## 选择语义与 COMSOL 映射

为选择记录 `selection_id`, `entity_dimension`, `predicate`, `expected_count`, `expected_measure`（含单位与容差）。例如用“最终几何 x=0 的端面，向外法向 -x，面积与横截面相符”定义固定端，随后在构建后的本模型绑定实体 ID；参数改变后重新检查，不能沿用另一模型的 boundary_1。

适配阶段记录 `backend_mapping`：spec 的 selection/material/physics/output ID → 真实模型名称、组件/节点 tag、实体成员、表达式、数据集和评价方式。实际工具/类型以 MCP 发现及同版本 API 为准，不根据人类名称猜类型。MPh/Java 仅通过 MCP；规格中的字符串不是自动执行代码。

先执行 [现有设置与几何核验](research-workflow.md)，再检查以下门槛：

- 预期几何参数确实改变最终测量，且选择语义仍成立。
- 材料和边界覆盖目标域；无意外空选择或冲突覆盖。
- 耦合变量、接口引用与研究参与状态有回读证据。
- 输出数学定义已映射到同工况、同单位、同平均/积分方法。
- 物理与离散验证计划适用于目标量；未知默认值标记来源与影响。

这些是 Agent 检查要求；Inspector 读取不等于自动证明方程完整。

## 运行清单与变更

每次运行使用唯一 `run_id`，在 `runs/<run_id>/manifest.json` 保存：

- `spec_id`, `spec_revision`, `spec_sha256`, `parent_run_id`。
- `inputs`：路径、角色、SHA256；包括规格、模型、参数、数据、代码/提交及环境记录。哈希对实际保存的文件字节计算，不能填示例哈希。
- `environment`：求解器版本、模块、平台、依赖/随机种子（适用时）、许可证检查状态，不保存密钥。
- `execution_state`, `reason`, `backend`, `job_id`, `submitted_at`, `started_at`, `finished_at`, `exit_code`；没有观察到的值为 null。执行历史未知用 execution_state=null 加 reason，不能填 not_run；发生已知提交但结果不明用 submission_unknown。
- `solution_identity`：模型/研究/解/数据集、参数/时间/频率、网格标识以及生成时间；记录证据而非仅声称“新解”。
- `artifacts`：路径、SHA256、对应 output_id 和 run_id；`checks`：设置、几何、物理、离散、重开核验的状态与证据。

参数、几何、本构、求解工况或验收定义变化均创建新 revision，并记录理由。新的执行生成新 run_id；未变的历史结果可以作为带身份的缓存引用，但不能改标签冒充本次重算。断线恢复继续查询原 run，不创建重复提交。文件哈希只能证明文件身份，仍需模型回读和解身份检查。
