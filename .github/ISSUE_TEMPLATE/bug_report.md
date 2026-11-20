---
name: Shipment state violation
about: Report an invalid shipment state transition
---
## Problem
A shipped shipment can be cancelled, violating the dispatch invariant.
## Required behavior
After SHIPPED, prohibit CANCELLED; preserve DELIVERED and RETURN_TO_SENDER.
## Acceptance criteria
- [ ] Cancellation after shipping raises ValueError.
- [ ] All 14 supplied unit tests pass.
- [ ] PR contains current-SHA CI evidence.
- [ ] Changes stay within the approved paths.
## Out of scope
Deployment, permissions, infrastructure, governance policy changes.
