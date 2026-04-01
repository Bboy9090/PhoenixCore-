# [TASK-004] Safety Engine: policy + force-mode + confirmation token

Cursor tags: type:feature, area:security, P0-blocker, M0-spine  
Status: Done

## Acceptance Criteria
- [ ] Default: all destructive ops denied
- [ ] Force mode requires explicit flag + confirmation token
- [ ] System disk always blocked unless forced
- [ ] Unit tests for policy decisions
