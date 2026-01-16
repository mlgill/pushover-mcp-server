# Pushover Notification Setup

At the start of each session:

1. **Check for Pushover MCP**: Verify the Pushover MCP tool is available
2. **Run health check**: If the MCP is available, call `pushover_health` to confirm the service is working
3. **Store status**: Remember whether Pushover is working for this session

If the MCP is not found or `pushover_health` fails, proceed normally without notifications for the rest of the session.

---

## Notification Rules When Awaiting Approval

When you need user approval to run a command and are waiting for a response:

### Initial notification (after 2 minutes idle)
If no response after **2 minutes**, send:
```
pushover_send(
  title="Claude: Approval Needed",
  message="Waiting for approval: <brief command description>",
  priority=0
)
```

### Escalation notification (after 8 minutes idle)
If still no response after **8 minutes total**, send a high-priority follow-up:
```
pushover_send(
  title="Claude: Still Waiting",
  message="Agent may timeout soon. Awaiting approval: <brief command description>",
  priority=1
)
```

### Do not send additional notifications after the escalation.

---

## Timing Rationale

- **2 min**: Long enough to avoid buzzing for quick approvals, short enough to catch genuine AFK moments
- **8 min**: Claude Code contexts can timeout around 10-15 minutes of inactivity; this gives buffer to respond before losing session state
