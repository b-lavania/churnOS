# MEMORY

Purpose
- A living log updated by the AI when it makes a mistake.
- The agent should read this file before starting new tasks and append entries when it discovers mistakes.

How to use
- Read before work: the agent (or a human reviewer) should open this file at the start of any new task to recall prior issues and patterns to avoid.
- Append entries: use the helper script `tools/memory.py` or edit manually.

Template for new entries
- Date (UTC)
- Mistake: short description of what went wrong
- Patterns to avoid: what led to the mistake
- Better approaches: actionable alternatives to use next time

## Mistakes

_(most recent first : add new entries at the top or use the helper script)_

### Example entry : 2026-03-28T00:00:00Z
**Mistake:** Assumed default cohort alignment was "signup_date" without checking data.

**Patterns to avoid:**
- Making assumptions about input schema or defaults that the code doesn't explicitly document.

**Better approaches:**
- Inspect the data or config files for defaults before using them; add explicit UI to surface the assumption to users.

## Patterns to avoid

- Assuming defaults without checking source code or data.
- Changing multiple unrelated files in one large commit.

## Better approaches

- Centralize UI inputs and defaults in a single module so assumptions are explicit.
- Persist user selections with `st.session_state` and provide preset/scenario save/load.

---

Notes
- Automated helper: `tools/memory.py` can read and append entries programmatically.
- Maintain brevity: entries should be concise and actionable.
# MEMORY

Purpose
- A living log updated by the AI when it makes a mistake.
- The agent should read this file before starting new tasks and append entries when it discovers mistakes.

How to use
- Read before work: the agent (or a human reviewer) should open this file at the start of any new task to recall prior issues and patterns to avoid.
- Append entries: use the helper script `tools/agent_learnings.py` or edit manually.

Template for new entries
- Date (UTC)
- Mistake: short description of what went wrong
- Patterns to avoid: what led to the mistake
- Better approaches: actionable alternatives to use next time

## Mistakes

_(most recent first : add new entries at the top or use the helper script)_

### Example entry : 2026-03-28T00:00:00Z
**Mistake:** Assumed default cohort alignment was "signup_date" without checking data.

**Patterns to avoid:**
- Making assumptions about input schema or defaults that the code doesn't explicitly document.

**Better approaches:**
- Inspect the data or config files for defaults before using them; add explicit UI to surface the assumption to users.

## Patterns to avoid

- Assuming defaults without checking source code or data.
- Changing multiple unrelated files in one large commit.

## Better approaches

- Centralize UI inputs and defaults in a single module so assumptions are explicit.
- Persist user selections with `st.session_state` and provide preset/scenario save/load.

---

Notes
- Automated helper: `tools/agent_learnings.py` can read and append entries programmatically.
- Maintain brevity: entries should be concise and actionable.
