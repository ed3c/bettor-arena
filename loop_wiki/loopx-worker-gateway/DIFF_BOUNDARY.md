# Diff boundary

The host-local gateway observes tracked, staged and untracked paths after execution. A path is accepted only when it equals an allowlisted root or is a descendant of that root. Symlink/path escape and physical filesystem enforcement remain runtime-fabric responsibilities; this leaf makes no kernel-level isolation claim.
