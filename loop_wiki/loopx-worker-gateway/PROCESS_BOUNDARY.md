# Process boundary

Each fixture/local subprocess starts in its own process group. Timeout, cancellation and output-limit paths terminate the whole group before cleanup. This proves process-group control in the host environment only; it does not prove container/VM isolation or safe behavior of a real model provider.
