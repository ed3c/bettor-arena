# Planning dispatch — capability packet and terminal envelope

Status: completed planning evidence; no file mutation authorized.

## Exact task

針對 perfect-seed-repo-factory v2 公開介面提出一個「capability packet /
terminal slice envelope」方案，以每個 terminal slice 的 self-contained
packet 為中心，刻意與全域 registry 或 event log 不同。需涵蓋 Work-Item、
architecture、oracle、CQ-0、candidate commit、attestations、Forgejo
projection、三 skills。讀實際檔案來源錨定。輸出 signature、usage、hides、
tradeoffs、migration、可證偽風險。不要實作。

## Result consumption

Selected as the terminal execution closure. The proposed attestation ref shape
was hardened with an additional `<attestation-sha>` component to make retries
create-only rather than overwriting a profile ref.
