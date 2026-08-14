# Official Agent Skills profile

本模組分開三種不能混稱為「官方共同格式」的事實：Agent Skills portable core、Codex host projection、Claude Code extension。最後查證日期為 2026-08-13；規格若更新，先重跑 `external-verify`，再修改本模組與 conformance checker。

## Portable core

官方 Agent Skills specification 定義一個目錄，唯一必需檔案是 `SKILL.md`；`scripts/`、`references/`、`assets/` 是建議的可選目錄，其他檔案也可存在。`SKILL.md` 必須是 YAML frontmatter 加 Markdown body。

Portable frontmatter 的共同面如下：

| 欄位 | portable 狀態 | 約束 |
|---|---|---|
| `name` | required | 1–64 字元；小寫英數與單一 `-`；不可首尾 `-` 或連續 `--`；等於父目錄名 |
| `description` | required | 1–1024 字元；同時說明做什麼與何時使用 |
| `license` | optional | 授權名稱或指向 bundled license 的文字 |
| `compatibility` | optional | 最多 500 字元；只有環境需求值得說明時才加 |
| `metadata` | optional | string-to-string map |
| `allowed-tools` | optional / experimental | 空白分隔工具；各 host 支援可能不同，不能視為 portable security boundary |

Body 沒有官方硬性格式或行數上限。官方 authoring guidance 建議控制在 500 行內，這在 Bettor 是家規 hard gate，不可寫成 Agent Skills validity rule。

來源：

- [Agent Skills specification](https://agentskills.io/specification)
- [Agent Skills authoring guidance](https://agentskills.io/skill-creation/best-practices)

## Codex projection

Codex repository scope 從 `.agents/skills/<name>/SKILL.md` 往 repository root discovery；user scope 是 `~/.agents/skills`，admin scope 是 `/etc/codex/skills`。Codex 支援 symlink。明確 invocation 是 `/skills` 選擇器或 prompt 中的 `$skill-name`；不要把 Claude 的 `/skill-name` 寫成 Codex 共同介面。

Codex 可選 sidecar 是 `agents/openai.yaml`。它承載 OpenAI/Codex 特有 metadata，不應把 host-only 欄位塞回 portable `SKILL.md`。

來源：[Codex Skills documentation](https://developers.openai.com/codex/skills)。

## Claude Code projection

Claude Code project scope 使用 `.claude/skills/<name>/SKILL.md`，並支援 `/skill-name`。Bettor 不複製第二份 package；`.claude/skills/<name>` 必須是指向 `.agents/skills/<name>` 的 thin symlink。

Claude Code 接受 `argument-hint`、invocation、model/subagent 等 extension，但它們是 Claude projection，不是 portable core。`allowed-tools` 只影響 skill 被 invocation 時的 tool approval，不能限制模型所有其他工具；host permission policy 才是權限邊界。

來源：[Claude Code Skills documentation](https://code.claude.com/docs/en/skills)。

## Bettor profile

```text
.agents/skills/<id>/SKILL.md       canonical portable package
.claude/skills/<id>                Claude thin symlink
.agents/skills/<id>/agents/openai.yaml  optional Codex/OpenAI sidecar
```

Bettor 另外採用以下家規：body 不超過 500 行、description 必須明示 what/when、canonical core 禁 host-only `argument-hint`。這些是跨 host 穩定性與 context budget 的本 repo policy，不冒充官方 parser 限制。
