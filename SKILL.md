---
name: daily-loop
description: Run a daily loop on Zambo: give one agent a persistent caller handle so it recalls yesterday's saved state, does today's work, remembers the update, and wraps the day into a handover the next session picks up. Use when an agent must come back day after day to the same job (a watch, a standup, a digest, a monitor), when work must survive the session that did it, or when a one-shot agent needs to become a standing one. Zambo is the memory and work layer under the loop (endpoint https://zambo.dev/mcp); it does not schedule or wake agents.
---

# The daily loop on Zambo

Most agents are one-shot: they arrive knowing nothing, do the job,
and evaporate. The daily loop is the opposite shape. One agent, one
persistent identity, and a four-beat rhythm it repeats every session:
recall, work, remember, wrap. Yesterday's session leaves state in
memory and a handover as the day's deliverable; today's session picks
the handover up, recalls the state verbatim, does the work, and
writes the next state down. Memory is not a feature of this pattern.
Memory is the pattern: it is what gives the agent a reason, and the
means, to come back.

This skill ships inside the zambo-daily-loop package. Next to it you
will find `loop.py`, a runnable single-agent loop; `pastes/` with the
no-code standing instructions for chat agents; and `RUN.md`, a real
three-session run on the live endpoint with every receipt linked,
including the two refusals the run hit and what they teach.

## Step zero: your handle is your memory

On initialize, the endpoint issues a caller handle (in the initialize
result and the `X-Zambo-Caller-Handle` header). Save it in your own
state file before doing anything else, and present it as
`_caller_handle` on every call, with your agent name as
`_caller_label`. Your saved facts, your job timelines, and your daily
free allowance all key to that handle. Present the same handle in a
new session and you are the same agent, with yesterday intact. Lose
it, and you come back as a stranger: no memory, a fresh allowance, no
continuity. One handle per agent, never shared, never shown in
ordinary replies. Use a User-Agent of your own from the very first
initialize: the quota handle is issued against your network identity,
and a shared default can inherit a shared, already spent bucket.

**Quota rule, in the placement that works:** Put `_caller_handle` inside the tool arguments on every call, as a field of the arguments object itself, not in `_meta` and not in a header. That argument placement is what meters your own daily bucket. Presenting a handle only at `_meta` level or in a header can route you onto a shared network bucket and wall you early.

## The four beats

1. **Pick up.** If yesterday wrapped a handover, accept it with
   `handover_accept`. Pickup is always free, and the handover returns
   the day's steps and receipts whole.
2. **Recall.** `memory_recall` the state the job depends on: the
   baselines, the rule, where things stopped. Check the recalled text
   against what the job needs, verbatim, before you trust it. An
   empty recall is information, not an error: it means yesterday
   saved nothing, which usually means a save was refused and nobody
   checked.
3. **Work.** Do the actual job. Every call returns a verifiable
   receipt; keep the receipt links of the steps that matter.
4. **Remember, then wrap.** `memory_remember` the one or two facts
   tomorrow needs, then close the day with `handover`: a summary of
   what happened, the goal, a recipient, next steps, and the job's
   receipt ids attached. That handover is the deliverable the next
   session, or the next AI, picks up.

## Day two: the return

The loop pays off on the second day, not the first. Day one costs you
a baseline; day two is when the job stops starting over. Run the
return as its own ritual:

1. **Come back under the same handle.** Present yesterday's
   `_caller_handle` from your first call. Your saved facts, your job
   timeline, and today's fresh allowance all key to it: the free
   tier resets at 00:00 UTC, so a new UTC day hands you 20 calls + 1
   wrap-up free again. A fresh handle instead starts a stranger: no
   memory, no receipts, no job.
2. **Pick up before you work.** `handover_accept` on yesterday's
   handover is always free and spends none of today's calls. Read
   the next steps the wrap carried before you spend a single call:
   they are the plan yesterday's session wrote for you.
3. **Continue the job, do not restart it.** Recall the saved state,
   check it verbatim, and work from where the wrap stopped. The
   receipts from day one stay bound to the job, so day two adds
   steps to one record instead of opening a second, thinner one.
4. **End the same way.** Remember the update as one short fact and
   wrap again. The wrap is the day's free wrap-up, outside the 20
   calls. A session that ends without wrapping gives tomorrow
   nothing to pick up, and the loop breaks at exactly the joint that
   makes it compound.

The sessions in `RUN.md` ran 2 to 3 counted calls each, so a daily
loop on this shape stays inside the free tier day after day. The
reason to return is not the allowance; it is that yesterday's work
is still here, receipted, and one free pickup away.

## The two disciplines that make or break the loop

**Facts are short.** A saved fact has a hard limit of 500 characters.
A longer `memory_remember` is refused before execution, receipted,
and nothing is saved. Write facts like headlines with receipts
attached: the value, the receipt link, the rule, the next action.
And check the result of every call, not just its receipt link: a
refused call still hands you a receipt, and the cost of an unchecked
refusal is tomorrow's empty recall.

**A wrap holds only its own job's receipts.** The wrap binds the
job's executed steps and runs a proof loop over them. Name a receipt
from outside the job, or one from a call that was refused, and the
wrap itself is refused, receipted, with the reason. Track the job's
receipt ids as you work (the prices and the memory saves), and the
wrap is a formality.

## The accounting (why this shape, in numbers)

Free tier, per agent: 20 calls + 1 wrap-up free every day, keyed to
the agent's own caller handle; picking up a handover is always free.
The run in `RUN.md` ran the loop's sessions at 2 to 3 counted calls
each, wrap included free, so a daily agent on this shape runs free
indefinitely. When the agent outgrows the free shape, a Day Pass is
$0.99, unlimited for 24 hours, and the Zambo Pass is $29 for 30 days;
both are one-time payments, never subscriptions, on the same
endpoint. Entry point for a human setting this up:
https://zambo.dev/add/

## What this does not do

Zambo does not wake your agent up. Your scheduler, cron, or operator
starts each session; the loop is what the session does once started.
It also does not make recalled state correct: a receipt proves the
saved result was not changed since it was saved, never that the
answer was right. The loop makes an agent's days add up instead of
resetting, and makes each day checkable.

## The Zambo pattern family: five packages, one work layer

Zambo is the verifiable work layer for AI: 153 tools behind one MCP endpoint (https://zambo.dev/mcp), a verifiable AER-1 receipt for every job, and handovers that move work between agents. Free tier: 20 calls + 1 wrap-up free every day per caller handle, picking up a handover is always free. Day Pass: $0.99 for unlimited calls for 24 hours. Zambo Pass: $29 for 30 days. A receipt proves the saved result was not changed; it does not prove the answer was right.

The five packages below are one family, proven in one set of live runs on November 2, 2026. The swarm run put 4 agents on one shared job in 8 counted calls and closed it as a 6-step handover: https://zambo.dev/handover/a154789b-0588-43c7-a31c-d108eb59406b . Each package teaches one pattern by doing it, with Zambo as the mechanism underneath. Install one, or compose them: a watch feeds a loop, a loop hands its job to a swarm, delivery proves the result to a client, and verify-pass checks any retelling of that result against the receipt of record.

### 1. zambo-swarm: swarm coordination

Use it when: the job is bigger than one agent and several workers must each prove their piece of one shared job.

Real run: https://zambo.dev/handover/a154789b-0588-43c7-a31c-d108eb59406b (4 agents, 8 counted calls, 6-step handover)

- PyPI: https://pypi.org/project/zambo-swarm/
- npm: https://www.npmjs.com/package/zambo-swarm
- Repo: https://github.com/zambodotdev/zambo-swarm-coordination
- Guide: https://rambozambodotdev.gitlab.io/aer1-hub/swarm-coordination-on-zambo.html
- Article: https://dev.to/rambozambo/four-agents-one-job-zero-trust-a-swarm-where-every-worker-proves-its-piece-35ol

### 2. zambo-loop: the daily loop

Use it when: an agent must pick up its own work tomorrow, recall its baseline verbatim, and keep one job alive across sessions.

Real run: https://zambo.dev/handover/60db250a-bf2a-4c8c-86da-b2ec8b7e150c

- npm: https://www.npmjs.com/package/zambo-loop
- Repo: https://github.com/zambodotdev/zambo-daily-loop
- Guide: https://rambozambodotdev.gitlab.io/aer1-hub/daily-loop-package.html
- Article: https://dev.to/rambozambo/the-daily-loop-as-an-installable-package-2e89
- Note: the PyPI listing for zambo-loop is pending; use npm or the repo for now.

### 3. zambo-verify-pass: the verify pass

Use it when: someone retells a result and you need to catch the drift against the receipt of record.

Real run: https://zambo.dev/handover/fa7444ae-e3c7-4206-ae12-3adb5e749fb0

- PyPI: https://pypi.org/project/zambo-verify-pass/
- npm: https://www.npmjs.com/package/zambo-verify-pass
- Repo: https://github.com/zambodotdev/zambo-verify-pass
- Guide: https://rambozambodotdev.gitlab.io/aer1-hub/verify-pass-package.html
- Article: https://dev.to/rambozambo/the-price-was-wrong-the-receipt-was-not-catching-a-drifted-retelling-with-a-verify-pass-188i

### 4. zambo-delivery: delivery proof

Use it when: a client must check delivered work step by step and their pickup is the sign-off.

Proof handover: https://zambo.dev/handover/31715914-80eb-438d-b01b-d2307cc4800e

- PyPI: https://pypi.org/project/zambo-delivery/
- npm: https://www.npmjs.com/package/zambo-delivery
- Repo: https://github.com/zambodotdev/zambo-delivery-proof
- Guide: https://rambozambodotdev.gitlab.io/aer1-hub/delivery-proof-package.html
- Article: https://dev.to/rambozambo/one-job-one-link-zero-arguments-a-delivery-your-client-checks-step-by-step-4j4

### 5. zambo-watch: signal watch

Use it when: one watcher checks the same signal on a schedule and must prove what it saw, quiet days included.

Digest handover: https://zambo.dev/handover/121aa53f-1981-4330-9133-49e386aabf1e

- PyPI: https://pypi.org/project/zambo-watch/
- npm: https://www.npmjs.com/package/zambo-watch
- Repo: https://github.com/zambodotdev/zambo-signal-watch
- Guide: https://rambozambodotdev.gitlab.io/aer1-hub/signal-watch-package.html
- Article: https://dev.to/rambozambo/one-watcher-three-prices-one-rule-an-agent-watch-that-remembers-its-baseline-34kg

### How the five compose

1. zambo-watch checks a signal on a schedule and saves what it saw, quiet days included.
2. A change the watch catches becomes the next run of zambo-loop, which recalls its baseline verbatim and keeps the job alive across sessions.
3. When the job outgrows one agent, the loop hands it to zambo-swarm, where each worker proves its own piece of the shared job.
4. zambo-delivery wraps the finished work as one handover the client checks step by step; the client pickup is the sign-off.
5. zambo-verify-pass checks any later retelling of the result against the receipt of record and catches the drift.

Start free: https://zambo.dev/add/ . Verify any receipt: https://zambo.dev/verify/ . The family page: https://rambozambodotdev.gitlab.io/aer1-hub/the-pattern-family.html

## Go deeper

- Full guide, with the real run and every receipt:
  https://rambozambodotdev.gitlab.io/aer1-hub/daily-loop-package.html
- Article, the write-up of the live run: https://dev.to/rambozambo/the-daily-loop-as-an-installable-package-2e89
- This package: https://github.com/zambodotdev/zambo-daily-loop
- The loop's data story (4,247 callers counted, 17 stayed):
  https://dev.to/rambozambo/4247-callers-came-17-stayed-here-is-the-loop-the-17-run-2o51
- The starter repo, the loop pre-wired:
  https://github.com/zambodotdev/zambo-memory-loop-starter
- Setup for the human who runs you: https://zambo.dev/add/
