# Browser contract status

[`status.json`](status.json) is generated from `.arena/browser/contract.json`.

It records the configured actors, transports, sessions, workflows, routes and evidence expectations. It does not contain a signed-in profile or session token. A configured route remains `NOT_EXERCISED` until a current provider canary observes it.
