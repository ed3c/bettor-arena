# Output boundary

Stdout and stderr are captured as bounded content-addressed artifacts. Exceeding the combined output budget terminates the process group and produces `OUTPUT_LIMIT`; truncated output cannot be labeled complete. Artifact content still requires downstream redaction/policy before any live-host admission.
