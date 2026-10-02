# 发布到 GitHub

发布的是本目录的代码与技能，不是电脑上的 COMSOL 安装目录，也不是全部仿真输出文件夹。不要把 `.venv`、本地 Token、运行时模型、日志、官方模型/帮助、私人研究资料加入 Git。

## 生成可分发技能包

在仓库根目录执行：

```powershell
python scripts/release.py --output ..\Comsol-Automatic-v0.1.0.zip
```

脚本使用明确的文件类型和目录清单，校验上游快照哈希，扫描个人路径、凭据和禁止分发文件，输出顶层为 `comsol-automatic/` 的 ZIP。这个目录包含根 SKILL.md 及 MCP 代码，安装时一起解压。`RELEASE_MANIFEST.json` 记录每个文件的 SHA-256。

审计只检查可自动识别的问题，不能替代维护者审阅新增文件内容。新增私人案例应保存在包外运行目录，只有获得明确公开授权的教学资源才能加入发布清单。

启动脚本会在安装电脑生成 `.mcp-token`；此文件只属于该用户。它已被 `.gitignore` 忽略，并被发布脚本的根目录文件清单排除。更新本机源码时保留它，向 GitHub 或其他人分发时不包含它；不能用“固定公共 Token”解决 Header 重填问题。发布测试会检查本地 Token 文件和内容均未进入 ZIP。

## 建仓与上传

先阅读根 README、NOTICE、案例状态和验证记录；确认仓库名称与账号后在 GitHub 新建目标仓库。可以用 GitHub 网页上传发布清单中的文件，或在本目录初始化 Git 并提交。不要在上一级混有科研输出的目录执行 `git add .`。

以下步骤在确切仓库根目录执行，`<YOUR-REPO-URL>` 必须替换为自己的实际目标：

```powershell
git init
git add SKILL.md README.md LICENSE NOTICE.md .gitignore pyproject.toml server vendor examples docs scripts tests
git status --short
git commit -m "Add Comsol-Automatic skill (adapted from Comsol-Automatic-wwj) and bundled MCP runtime"
git branch -M main
git remote add origin <YOUR-REPO-URL>
git push -u origin main
```

发布 Release 时附上 ZIP 与 SHA-256，并写清实际测试版本、原创案例结果、官方库案例的未测试状态和豆包端验收情况。分别记录工具发现、模型创建、求解、前台导入及其证据来源；用户反馈的求解成功不能写成所有客户端版本或前台导入已验证。
