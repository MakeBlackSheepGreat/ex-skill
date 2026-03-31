# Codex CLI 适配说明

本仓库现在支持在 Codex CLI 中安装 `create-ex`，并把生成出来的前任 Skill 发布为 Codex 可直接调用的 skill。

官方文档参考：

- https://developers.openai.com/codex/skills/

## 1. 安装 create-ex

Codex CLI 会扫描 `~/.agents/skills/<skill-name>/SKILL.md`，也支持当前仓库下的 `.agents/skills/<skill-name>/SKILL.md`。

```bash
# macOS / Linux
git clone https://github.com/therealXiaomanChu/ex-skill ~/.agents/skills/create-ex

# Windows PowerShell
git clone https://github.com/therealXiaomanChu/ex-skill "$env:USERPROFILE/.agents/skills/create-ex"
```

安装完成后可以显式调用：

```text
$create-ex
```

如果描述足够明确，Codex 也可以根据技能描述自动选用它。

## 2. 生成前任 Skill

在 Codex CLI 中运行 `$create-ex`，按提示完成：

- 花名 / 代号
- 基本信息
- 性格画像
- 原材料导入

生成结果会先写到仓库内的 `exes/{slug}/`。

## 3. 发布到 Codex 技能目录

生成完成后，在仓库根目录执行：

```bash
# macOS / Linux
python3 tools/skill_writer.py --action publish --base-dir ./exes --slug <slug> --runtime codex

# Windows PowerShell
python3 tools/skill_writer.py --action publish --base-dir ./exes --slug <slug> --runtime codex
```

这条命令会生成并发布三个 skill：

- `$<slug>`
- `$<slug>-memory`
- `$<slug>-persona`

对应的中间产物会保存在：

```text
exes/{slug}/dist/
```

每个运行时目录下都会生成：

- `SKILL.md`
- `agents/openai.yaml`

其中 `agents/openai.yaml` 是给 Codex 使用的可选元数据。

## 4. 更新与重发

当你追加新聊天记录、照片或纠正人格设定后，再执行一次相同的 `publish` 命令即可覆盖 Codex 中已发布的版本。

## 5. 兼容策略

- 仓库根目录 `SKILL.md` 现在使用 `{SKILL_DIR}` 作为路径占位符
- Claude Code 中将其替换为 `${CLAUDE_SKILL_DIR}`
- OpenCode 中将其替换为 `${HOME}/.config/opencode/skills/create-ex`
- Codex CLI 中将其替换为 `${HOME}/.agents/skills/create-ex`
- `tools/skill_writer.py` 负责把本地 `exes/{slug}` 渲染成运行时可加载的 skill 包，并支持 `--runtime codex`
