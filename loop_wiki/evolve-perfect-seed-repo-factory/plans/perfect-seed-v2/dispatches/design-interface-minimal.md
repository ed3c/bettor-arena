# Planning dispatch — minimal append-only event core

Status: completed planning evidence; no file mutation authorized.

## Exact task

針對 perfect-seed-repo-factory v2 的公開介面（plan-registry / Work-Item /
architecture graph / oracle registry / attestation refs / three local skills /
CQ-0）提出一個「最小方法數、append-only event core」方案。需求已由主對話
鎖定；讀取目標 repo 實際檔案以來源錨定。輸出：1) interface
signatures/schema shape；2) caller usage；3) hides；4) tradeoffs；5) 與 v1
migration 相容性；6) 可證偽風險。不要實作。

## Result consumption

The event core was rejected as ontology SSOT but retained as an internal async
lease/cancel/race implementation candidate. Its strongest falsifiers were
carried into Milestones 07 and 09.
