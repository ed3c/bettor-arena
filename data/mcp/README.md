# MCP exposure snapshot

[`exposure.json`](exposure.json) is generated from the canonical `loopctl` contract plus `.arena/mcp-policy.json`.

Only tools with explicit external exposure appear. Missing policy means denied. The snapshot must not contain generic shell execution, server-host absolute paths, secrets or mutable release refs.

Regenerate with:

```sh
bun loopctl/mcp_tools.ts loopctl/contract.json \
  --policy .arena/mcp-policy.json
```
