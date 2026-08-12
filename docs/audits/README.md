# Audit handoffs

`docs/audits/` stores review packets bound to a named repository, branch, commit or release subject.

Every audit should state:

- exact subject and scope;
- evidence arrival method;
- findings and severity;
- `NOT_EXERCISED` or excluded paths;
- remediation owner;
- reproduction and rollback instructions.

Do not silently treat an older audit as current after the subject bytes change.
