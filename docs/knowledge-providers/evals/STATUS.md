# Evaluation status

| Surface | State | Evidence boundary |
|---|---|---|
| evaluation schemas | IMPLEMENTED | JSON Schemas plus stdlib validators |
| paired fixture suite | IMPLEMENTED | Four cases and eight paired observations |
| mutation controls | IMPLEMENTED | Authority, subject, coverage, cleanup, and memory controls |
| exact-head GitHub Actions | NOT_EXERCISED | Final PR head has not been observed |
| Serena live execution | NOT_EXERCISED | No current adapter/index canary receipt |
| GrepAI live execution | NOT_EXERCISED | No current adapter/index canary receipt |
| Code-Graph-RAG | NOT_CONFIGURED | Read-only adapter and graph coverage receipt absent |
| Mem0 | NOT_CONFIGURED | Storage, retention, deletion, and writeback admission absent |
| provider winner | NOT_EXERCISED | Fixture evidence cannot elect a winner |
| production admission | NOT_PERFORMED | Requires Human Admit |

The checked-in configuration is fixture-only. Live evidence requires a separate reviewed contract change.
