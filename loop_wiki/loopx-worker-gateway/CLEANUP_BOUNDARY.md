# Cleanup boundary

A receipt can report `cleanup.state = PASS` only after the detached worktree is removed, Git worktree metadata is pruned and the gateway-owned temporary root is absent. Cleanup failure prevents `OBSERVED_SUCCESS` from remaining successful. Cleanup of cloud/provider resources belongs to runtime-fabric.
