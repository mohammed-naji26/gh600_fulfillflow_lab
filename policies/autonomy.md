# Risk-based autonomy policy (training example)
| Risk | Example | Allowed agent action | Enforced decision |
| --- | --- | --- | --- |
| Low | Documentation typo | Propose or edit on task branch | CI; ordinary PR process |
| Medium | Shipment transition logic | Branch, implementation, tests, PR | Required CI + human review |
| High | Secrets, workflows, CODEOWNERS, MCP access, deployment | Read, report, propose only | Security owner + human approval; no autonomous merge |

Actual enforcement must be configured using GitHub repository settings, rulesets,
protected environments, and credentials. A text policy alone is not enforcement.
