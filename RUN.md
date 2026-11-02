# Daily loop run: the proof record

Executed live against https://zambo.dev/mcp on November 2, 2026.
Job id (_session_id): `daily-loop-demo-2026-11-02`. One identity,
`daily-loop-agent`, issued a fresh caller handle at initialize and
persisted in a state file; three sessions ran under that same handle
as separate processes. Pattern: recall, work, remember, wrap. This
record includes the two refusals the run hit on the way, because they
are the two lessons the package exists to teach.

## Session 1: set the watch (20:46 UTC)

- `live_price` BTC: $76,786.70, down 1.29% (24h), 20:46:29 UTC.
  Receipt: https://zambo.dev/run/3ab3edf9-68c1-4419-b444-49853ddc7fca
- `live_price` ETH: $2,247.14, down 0.69% (24h), 20:46:32 UTC.
  Receipt: https://zambo.dev/run/326f0be5-f1fe-432c-a67d-01e56105531b
- `memory_remember` the baseline state: REFUSED before execution.
  The fact ran over the 500 character limit for a saved fact; the
  endpoint rejected it with `invalid_tool_arguments` and issued the
  refusal its own receipt:
  https://zambo.dev/run/c7d11d3b-64da-4625-b246-42243674bf7c
  Nothing was saved. A receipt link is not proof a call succeeded;
  the result said so plainly, and the next session proved it.

## Session 2: the honest empty recall (20:46 UTC)

- `memory_recall` for the watch state returned status `empty`,
  count 0, because session 1's save had never landed.
  Receipt: https://zambo.dev/run/4adc6ece-9458-4e19-af64-6e4587b1dbbc
- `live_price` BTC again: $76,848.93, 20:46:52 UTC.
  Receipt: https://zambo.dev/run/dc2f54b4-aaa0-460d-b823-f951724bb102
- `memory_remember` the session 2 update (inside the limit): saved.
  Receipt: https://zambo.dev/run/43a95682-e2dc-4833-8dbe-cc43bd605670
- `handover` wrap attempt: REFUSED with `receipt_access_denied`.
  The wrap's receipt selection named the refused remember's receipt,
  which is not an executed step of this job; a wrap holds only
  receipts from its own job, and nothing was published.
  Receipt: https://zambo.dev/run/5dad54f0-073d-4f1a-aecd-0d736d0d60c8

## Repair: save the baseline, short (20:49 UTC)

The same baseline state, written at 378 characters, saved cleanly:
BTC baseline $76,786.70 and ETH baseline $2,247.14 with their price
receipts inside the fact, and the alert rule in plain words (flag if
BTC moves 3 percent or more from baseline, or ETH 4 percent or more).
Receipt: https://zambo.dev/run/ba4a4143-d6db-4a4f-9834-af5056abd08f

## Session 3: the loop closes (20:49 to 20:50 UTC)

A third session, a new MCP session under the same saved handle:

- `memory_recall` returned the baseline fact, and the check was
  mechanical: the strings "BTC baseline $76,786.70", "ETH baseline
  $2,247.14", and the alert rule all appear in the recalled text
  verbatim, exactly as saved.
  Receipt: https://zambo.dev/run/fd2d6820-cc7d-4474-995f-2b04ef707140
- `live_price` BTC: $76,875.00, 20:49:54 UTC, a move of +0.115%
  from the $76,786.70 baseline. Inside the 3 percent band: no alert.
  Receipt: https://zambo.dev/run/e42b60ed-1dee-4360-bc4c-9b07ccb08250
- `memory_remember` the session 3 update: saved.
  Receipt: https://zambo.dev/run/1630f1f9-991e-40c1-a358-431c82dacae6
- `handover` wrap, its receipt selection naming only this job's
  executed steps (the two session 1 prices, the saved baseline
  remember, the session 3 price, the session 3 remember):
  https://zambo.dev/handover/60db250a-bf2a-4c8c-86da-b2ec8b7e150c
  JSON twin: https://zambo.dev/handover/60db250a-bf2a-4c8c-86da-b2ec8b7e150c.json
  Wrap receipt: https://zambo.dev/run/307d76af-cd16-4c2a-bd06-3206f6821c3c
  The handover lists exactly those 5 steps, in order.

## Accounting

The loop's shape, per session: work and memory calls only. Session 1
spent 2 counted calls (the prices; the refused remember executed
nothing). The repair remember spent 1. Session 3 spent 3 (recall,
price, remember) and its wrap was the free daily wrap-up. The whole
proof, refusals and diagnostics included, stayed inside one identity's
single day of free tier: 20 calls + 1 wrap-up free every day, keyed to
the caller handle, and picking up a handover is always free.

## The two lessons, which are the package

1. A saved fact has a hard limit of 500 characters. Write facts like
   headlines with receipts attached, not essays. And check the result
   of every call: a refused call still hands you a receipt link, and
   the next session's empty recall is what an unchecked refusal costs.
2. A wrap is a job's own record. It binds the job's executed steps and
   refuses a selection that names anything else. Keep the job's
   receipt ids as you go, and the wrap is a formality; improvise the
   selection, and the wrap refuses, receipted, with the reason.

## Verification

Every link above was fetched on 2026-11-02 after the run: all returned
HTTP 200 (14 of 14, including both refusal receipts, the final
handover page, and its JSON twin). One identity note, recorded for
honesty: the first identity minted for this run was issued under this
machine's shared default User-Agent and inherited a shared, already
spent quota bucket (0 of 20 free calls before its first call), so it
was replaced before any work was saved; the run above is the second
identity, minted with the agent's own User-Agent from its first
initialize, which is the discipline `loop.py` ships with.
