# 安装与豆包连接器

技能定义仿真流程，MCP 服务提供实际工具；两者都需要安装。解压完整发布包并保留 `SKILL.md`、`server/`、`vendor/`、`examples/` 和 `scripts/`。本包不安装 COMSOL，也不提供 COMSOL 或附加模块许可证。

以下 Windows 命令在**仓库根目录**的 PowerShell 中运行。需要 Python 3.10+（推荐 3.12）、本机 COMSOL 和相应模块。默认通过 MPh 发现 COMSOL；多版本环境用 `COMSOL_VERSION` 选择版本。可将 `COMSOL_ROOT` 设为对应的、包含 `applications` 的 `Multiphysics` 目录，但它不能替代 MPh 的安装发现，也不能指向另一版本。不要填写 `bin` 目录或某个 `.exe` 路径；doctor 报发现失败时先检查 COMSOL 安装/注册信息。

## 1. 安装并检查

解压完整发布包到自己的本地项目目录。下面的脚本安装 **MCP 运行环境**，不会将技能注册到豆包管理列表。豆包列表安装还需第 4 步的“上传技能”流程；不要用复制到 `.user_skills` 或 `.codex/skills` 代替。已有 MCP 服务的用户继续使用原服务，无须重复安装运行环境。完整说明见 [豆包技能列表安装](skill-discovery.md)。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
.\.venv\Scripts\python.exe -m server.main doctor
```

安装脚本创建本仓库的 `.venv`。检查 `doctor` 输出中的 `success`、`comsol_root`、`application_library`。`license_checked: false` 表示尚未检查模块许可证，不能据此判断所有案例都能运行。可编辑安装依赖仓库源码，安装后不要单独移动 `.venv` 或删除 `vendor`。

## 2. 启动本机 HTTP MCP

首次配置，在仓库根目录执行：

```powershell
# 要启用完整命令建模（受信任 Agent 的 Python/Java API 执行），在启动前设置：
# $env:COMSOL_ALLOW_CODE = "1"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\start-mcp.ps1" -Transport streamable-http -Port 8765 -CopyHeader
```

脚本首次生成随机 Token，保存到本机技能目录的 `.mcp-token`；以后启动自动读取同一个值，并传给服务进程。`-CopyHeader` 将完整的 `Bearer <Token>` 复制到剪贴板，下一步直接粘贴。它不会在终端打印 Token。服务默认监听 `127.0.0.1:8765`；保持窗口运行，按 `Ctrl+C` 停止。

**以后重启只用下面这条命令，连接器 Header 无需更改：**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\start-mcp.ps1" -Transport streamable-http -Port 8765
```

不要每次启动都执行 `secrets.token_urlsafe(...)`，也不要在重新复制 Header 时生成新 Token。旧流程反复改 Header 的原因正是每次生成了新值。`.mcp-token` 存在时，脚本不会自动替换它；若环境变量与文件不一致会报错，保留两者让用户核对。

如果只是剪贴板内容丢失，使用下面这条命令重新复制**已有** Header；它不启动第二个服务，也不轮换 Token：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\start-mcp.ps1" -Transport streamable-http -PrepareTokenOnly -CopyHeader
```

### 已配置成功的旧版如何保留 Header

继续使用当前可用连接器，无需重建。更新包内源码时保留自己的 `.mcp-token`、`.venv` 和 `runs/`。旧版没有 `.mcp-token` 的，停止旧 MCP 服务后，在**仍有原 `COMSOL_MCP_TOKEN` 的 PowerShell 窗口**运行新版启动命令：脚本会将原 Token 保存一次，以后重启继续复用。

若旧窗口已关闭且尚无 `.mcp-token`，在豆包连接器中复制当前 Header 值到本机剪贴板，然后在仓库根目录执行：

```powershell
$ExistingHeader = [string](Get-Clipboard -Raw)
if ($ExistingHeader.Trim() -cmatch '^Bearer ([^\s]{32,})$') {
    $env:COMSOL_MCP_TOKEN = $Matches[1]
    powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\start-mcp.ps1" -Transport streamable-http -PrepareTokenOnly
} else {
    throw "Clipboard must contain the existing complete Bearer header. Nothing was saved or started."
}
```

这里只保存现有值，不生成新凭据。不要将真实 Header 粘贴到对话、日志或仓库。若无法找回原值，才需要重新生成并更新连接器一次。若文件已存在且与环境变量冲突，确认要复用文件后，可在当前窗口执行 `Remove-Item Env:COMSOL_MCP_TOKEN -ErrorAction SilentlyContinue`，再运行启动命令；这不会删除 Token 文件。

`.mcp-token` 是本机明文凭据，应放在自己的用户目录中。它已被 Git 忽略，发布脚本也将其排除；更新保留本机文件，分享源码或发布 ZIP 时不带上它。只有明确需要撤销旧凭据时才停止服务、更换 Token 并同步修改连接器；日常重启、工具刷新、切换 HTTP/SSE 均不需要换 Token。

### PowerShell 提示“在此系统上禁止运行脚本”

这是用户在豆包安装时遇到并解决的 `PSSecurityException`。使用上文带 `-NoProfile -ExecutionPolicy Bypass -File` 的完整命令启动安装包中已检查的脚本；只对这次 PowerShell 进程生效，不需要永久修改系统执行策略。原窗口的环境变量会被该子进程继承。若设备管理策略仍阻止启动，保留错误并按本机管理要求处理。

本服务的地址为 `http://127.0.0.1:8765/mcp`。**8765 是 MCP 的 HTTP 端口；COMSOL 原生服务器另外使用一个 TCP 端口，不能把它填进豆包的 MCP URL。**

## 3. 配置豆包

使用豆包桌面端或豆包工作，打开 **技能 · 连接器 · 伙伴 → 新建 → 新建自定义连接器**。填写下表。这些入口、HTTP 类型和自定义 Header 字段有连接器供应商的一手官方说明；名称可能随客户端更新变化。[flomo 官方接入说明](https://help.flomoapp.com/advance/mcp/token.html)

| 字段 | 本包填写值 |
| --- | --- |
| 服务器名称 | `COMSOL` |
| 传输类型 | `HTTP` |
| 服务器 URL | `http://127.0.0.1:8765/mcp` |
| 自定义 Header 名称 | `Authorization` |
| 自定义 Header 值 | 粘贴上一步复制的 `Bearer <Token>` |

保存后，在本地工作任务输入框下选择 COMSOL 连接器。flomo 官方说明指出，豆包工作的自定义连接器只在添加它的本地电脑使用，不自动同步到其他设备。[设备范围说明](https://help.flomoapp.com/advance/mcp/token.html)

**兼容性边界：**用户在 2026-09-05 提供的运行记录报告：已在其豆包环境通过本机 HTTP + Header 连接，完成工具发现、COMSOL 6.2 会话创建和 `heat_sink_3d` 求解，七项检查通过。这是用户反馈的成功案例；本次 Token 持久化更新另有本机脚本测试，尚未由用户在豆包重新验收。没有据此验证所有豆包版本、技能上传入口或前台导入全过程。若客户端拒绝本机地址，保留具体错误并核对运行环境；不要立即公开电脑端口，也不要把火山方舟或扣子的云插件规则当成豆包桌面规则。

如果客户端明确要求旧版 SSE，可停止现有服务后改用；仍复用本机 Token：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\start-mcp.ps1" -Transport sse -Port 8765
```

旧版 SSE 的 URL 是 `http://127.0.0.1:8765/sse`，服务器同时使用 `/messages/` 接收消息；客户端必须在这些请求中都携带认证 Header。只有确认客户端支持该传输时才选择它。旧版 HTTP+SSE 与 Streamable HTTP 是不同传输，不是把 `/mcp` 任意改名即可互换。[MCP 官方传输规范](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)

## 4. 导入技能并验收

进入豆包技能管理页，使用当前客户端的 **新建／创建 → 上传技能 → 选择文件**，上传经过发布审计的 `Comsol-Automatic-v0.1.0.zip`。本机客户端资源已确认“上传技能”入口及相关文案；具体位置以当前界面为准。不要把服务器子目录另当一个技能，也不要仅上传 `SKILL.md` 后删除其他必需文件。

本项目没有验证豆包各版本或“从 GitHub 导入”功能。若当前版本没有导入入口或 Agent 无法接入豆包管理页，说明这一具体限制，保留完整 ZIP 供用户按正式入口安装；不要改装到其他 Agent 的目录后声称完成。直接按路径读取 `SKILL.md` 可以临时使用，但不能据此声称已安装到技能列表。见 [豆包技能列表安装](skill-discovery.md)。

**列表安装单独验收：**提交后确认上传结果与安全检测通过，重新打开“我的技能”或管理列表并搜索名称，确认条目可见且可用。未完成这一项时报告“安装包已准备，豆包列表安装尚未完成”，不能用本地扫描、MCP 调用或案例求解成功替代。

第一次发送：

> 使用 comsol-automatic，先调用 comsol_doctor 和 comsol_list_cases，检查 COMSOL、工具和案例库；先不要创建模型。报告连接是否成功，不要把发现安装目录当成许可证验证。

检查通过后发送：

> 一定不要使用屏幕识别，只使用 MCP 操作 COMSOL。通过连接器运行 heat_sink_3d，并通过 MCP 打开同一服务器的 COMSOL Desktop。跟踪 job 状态直到完成，报告温度、热量平衡和输出文件。最后告诉我本次模型名称，提示我手动点击“文件 → COMSOL Multiphysics Server → 从服务器导入 App”查看模型及结果。

`comsol_run_case` 先返回 `job_id`，使用 `comsol_job_status` 读取真实进度。**全过程禁止屏幕识别、截图定位、OCR、鼠标键盘自动化；不能绕过 MCP 运行外部建模脚本。** 安装及连接器配置按本指南由用户完成。

如果工具调用报 `Function not found`，先刷新连接器工具定义、重新选择连接器，并使用当前返回的工具命名空间；用户在豆包中用此方法恢复了工具。不要因此重装 COMSOL、生成新 Token 或重复提交同一求解任务。状态查询超时也不等于求解失败或完成；本包的 `comsol_job_status` 不会排在求解线程后等待，不能仅凭超时认定“求解占满线程”。恢复 MCP 后查询原 `job_id`，仍只依据 MCP 返回确认进度。

仿真完成后，最后由用户在 COMSOL 中手动点击 **文件 → COMSOL Multiphysics Server → 从服务器导入 App**，选择 MCP 返回的新模型名称；普通模型也可能在此称为 App。Agent 给出实际服务器端口和模型名称，不自动点击菜单。完成导入后，Desktop 才能显示该服务器模型的几何、材料、物理场、网格、研究和结果。

## 其他 Agent：stdio

支持本地进程型 MCP 的 Agent 可以采用 stdio，不需要 HTTP Token。将下面绝对路径占位符替换为实际解压目录，按客户端配置格式设置：

```json
{
  "mcpServers": {
    "comsol": {
      "command": "C:/path/to/comsol-automatic/.venv/Scripts/python.exe",
      "args": ["-m", "server.main", "serve", "--transport", "stdio"],
      "cwd": "C:/path/to/comsol-automatic"
    }
  }
}
```

此处是通用示例，不是豆包配置文件格式。客户端不支持 `cwd` 时，用该客户端提供的工作目录设置，或让其启动 `scripts/start-mcp.ps1 -Transport stdio`。stdio 的标准输出属于 MCP 协议，调试信息应写到标准错误。[MCP 官方 stdio 说明](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)

本包在 stdio 开始读取输入前准备 COMSOL 客户端 JVM，以避免 Windows 输入读取与 Java 初始化相互等待；这一步不创建模型或求解。多版本环境须在启动前设置 `COMSOL_VERSION`，更换版本需重启 MCP。HTTP 模式保持按需启动。

## 高级 API 与常见故障

高层工具无法覆盖的 COMSOL 接口可通过 `comsol_model_code` 调用 Java API。它默认关闭；受信任的单用户环境若需要启用，在**启动服务前**设置：

```powershell
$env:COMSOL_ALLOW_CODE = "1"
```

这是任意 Python 代码执行权限，不是受限表达式求值。详见 [安全边界](security.md)。`COMSOL_OUTPUT_ROOT` 可指定输出目录，默认使用仓库内 `runs/`；`COMSOL_CORES` 默认 4。

| 现象 | 检查与处理 |
| --- | --- |
| 401 | Header 是否为 `Authorization`；`Bearer` 后有且只有一个空格；用 `-PrepareTokenOnly -CopyHeader` 重复制本机现有值；不生成新 Token。未携带 Header 的探测返回 401 只说明鉴权拒绝了请求，不是完整 MCP 验收 |
| 每次重启都要改 Header | 使用新版启动脚本复用 `.mcp-token`，按旧版迁移步骤保留当前 Token；删除启动命令中每次随机生成 Token 的步骤 |
| Token 文件与环境变量不同 | 不覆盖文件；核对要使用哪一个，复用文件时只清除当前窗口的旧环境变量 |
| PSSecurityException / 禁止运行脚本 | 使用上文 `powershell -NoProfile -ExecutionPolicy Bypass -File ...` 命令 |
| Function not found | 刷新工具定义并重新选择连接器，使用新的命名空间；不改 Header |
| 404 / 405 或传输协商失败 | HTTP 模式用 `/mcp`；旧版 SSE 用 `/sse`；确认客户端传输类型 |
| Host / Origin 被拒绝 | 确认 URL 使用本机回环地址；不要关闭防护来掩盖代理配置错误 |
| 连接本机却返回代理 502 或超时 | 让连接器对 `127.0.0.1` / `localhost` 绕过代理；Python 客户端可用 `NO_PROXY` 设置本机例外 |
| 找不到 COMSOL | 运行 doctor；检查 COMSOL 安装、`COMSOL_ROOT` 和可选 `COMSOL_VERSION` |
| 案例库存在但加载失败 | 读取准确的模块／许可证／版本错误；文件存在不代表许可证可用 |
| 前台是空白模型 | 按返回的 COMSOL TCP 端口连接同一服务器，并导入本次新模型 |
| 返回 queued/running | 继续读取 job 状态；这不是计算结果 |
| 只有工作流文字，没有工具 | 技能已读取但 MCP 尚未接通，返回第 2、3 步 |
| MCP 能用，但技能列表没有 COMSOL | 按 [豆包技能列表安装](skill-discovery.md) 从“上传技能”入口导入发布 ZIP，并确认检测通过和条目出现；不重建连接器、不改 Header |
