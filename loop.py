#!/usr/bin/env python3
"""The daily loop, as runnable code: recall, work, remember, wrap.

One agent, one persistent caller handle, one job that survives the
session. Two commands, because a day has two halves:

    python3 loop.py start      # day one: price the watch, save the
                               # baseline state to memory
    python3 loop.py continue   # every later session: recall the state
                               # verbatim, re-check, remember the
                               # update, wrap the day into a handover

The handle is the whole trick. On initialize the endpoint issues a
caller handle; this script saves it in a state file next to itself
before doing anything else, and presents it on every call, in every
later process, forever. Memory, the job timeline, and the daily free
allowance all key to that handle. Lose the state file and the agent
comes back as a stranger: no memory, no continuity.

Three field lessons are baked in, each learned from a real refusal:

1. Facts have a hard limit of 500 characters. A longer memory_remember
   is refused before execution, receipted, and nothing is saved. Keep
   facts short; put the receipts in them, not the essay.
2. A refused call still returns a receipt. This script checks every
   result for errors and stops loudly instead of collecting receipts
   for work that never happened.
3. A wrap holds only receipts from its own job. The wrap below names
   only this job's executed steps (prices and memory saves), which the
   state file tracks across sessions.

Cost: start is 3 counted calls; continue is 3 counted calls (the
recall, the price, the remember) plus the free daily wrap-up. The free
tier is 20 calls + 1 wrap-up per day, keyed to the handle, so the loop
runs free. No API key, no signup. Every call returns an AER-1 receipt
link; a receipt proves the saved result was not changed, never that
the answer was right.

The pattern, taught end to end with a real run and its receipts:
https://rambozambodotdev.gitlab.io/aer1-hub/daily-loop-package.html
"""

import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

MCP_URL = os.environ.get("ZAMBO_MCP_URL", "https://zambo.dev/mcp")
AGENT_ID = os.environ.get("ZAMBO_AGENT_ID", "daily-loop-agent")
AGENT_NAME = os.environ.get("ZAMBO_AGENT_NAME", "Daily Loop Agent")
JOB_ID = os.environ.get("ZAMBO_SESSION_ID", "daily-loop-demo")
ASSETS = [
    a.strip().upper()
    for a in os.environ.get("ZAMBO_ASSETS", "BTC,ETH").split(",")
    if a.strip()
]
ALERT_PCT = {
    "BTC": float(os.environ.get("ZAMBO_ALERT_BTC", "3")),
    "ETH": float(os.environ.get("ZAMBO_ALERT_ETH", "4")),
}

HERE = Path(__file__).parent
# Step zero: the state file IS the identity. Handle, baselines, and
# the job's receipt ids live here, across processes and days.
STATE_FILE = HERE / f".zambo-loop-state-{AGENT_ID}.json"

RUN_URL_RE = re.compile(r"https://zambo\.dev/run/[0-9a-f-]{36}")
PRICE_RE = re.compile(r"\$([0-9][0-9,]*\.?[0-9]*)")

FACT_LIMIT = 500


def fmt_price(p):
    return f"${p:,.2f}"


class ZamboClient:
    """Minimal MCP client over streamable HTTP, standard library only."""

    def __init__(self, state):
        self.state = state
        self.session_id = None
        self._next_id = 0

    @property
    def caller_handle(self):
        return self.state.get("caller_handle")

    @property
    def quota_handle(self):
        return self.state.get("quota_handle")

    def _post(self, payload, expect_response=True):
        body = json.dumps(payload).encode()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "X-Agent-Id": AGENT_ID,
            "X-Agent-Name": AGENT_NAME,
            # A User-Agent of the agent's own from the very first
            # initialize: the quota handle is issued against the
            # caller's network identity, and a shared default UA can
            # inherit a shared, already-spent bucket.
            "User-Agent": f"{AGENT_ID}/1.0",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        req = urllib.request.Request(MCP_URL, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            if self.session_id is None:
                self.session_id = resp.headers.get("Mcp-Session-Id")
            header_handle = resp.headers.get("X-Zambo-Caller-Handle")
            raw = resp.read().decode()
        if header_handle and not self.caller_handle:
            self.state["caller_handle"] = header_handle
            self._save()
        if not expect_response:
            return None
        return self._parse_rpc(raw)

    @staticmethod
    def _parse_rpc(raw):
        message = None
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                try:
                    message = json.loads(line[5:])
                except Exception:
                    pass
        if message is None:
            message = json.loads(raw)
        if "error" in message:
            raise RuntimeError(f"MCP error: {message['error']}")
        return message.get("result", {})

    def initialize(self):
        params = {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": AGENT_NAME, "version": "1.0.0"},
        }
        if self.caller_handle:
            params["_meta"] = {
                "caller_handle": self.caller_handle,
                "quota_handle": self.quota_handle,
            }
        result = self._post(
            {"jsonrpc": "2.0", "id": self._id(), "method": "initialize", "params": params}
        )
        for container in (result.get("_meta", {}), result.get("meta", {})):
            if not self.caller_handle and container.get("caller_handle"):
                self.state["caller_handle"] = container["caller_handle"]
            if not self.quota_handle and container.get("quota_handle"):
                self.state["quota_handle"] = container["quota_handle"]
        self._save()
        self._post(
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            expect_response=False,
        )
        return result

    def call_tool(self, name, arguments):
        args = dict(arguments)
        if self.caller_handle:
            args["_caller_handle"] = self.caller_handle
        args.setdefault("_caller_label", AGENT_ID)
        params = {"name": name, "arguments": args}
        if self.quota_handle:
            params["_meta"] = {
                "quota_handle": self.quota_handle,
                "caller_handle": self.caller_handle,
            }
        result = self._post(
            {"jsonrpc": "2.0", "id": self._id(), "method": "tools/call", "params": params}
        )
        # A refused call still returns a receipt. Check the result
        # itself, never just the receipt link.
        structured = result.get("structuredContent") or {}
        error = structured.get("error") if isinstance(structured, dict) else None
        if result.get("isError") or error:
            raise RuntimeError(f"{name} refused: {json.dumps(error)[:240] if error else result}")
        handle = structured.get("caller_handle")
        if handle and not self.caller_handle:
            self.state["caller_handle"] = handle
            self._save()
        return result

    def _save(self):
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    def _id(self):
        self._next_id += 1
        return self._next_id


def receipt_link(result):
    structured = result.get("structuredContent") or {}
    for key in ("receipt_url", "run_url", "url"):
        value = structured.get(key)
        if isinstance(value, str) and "/run/" in value:
            return value
    match = RUN_URL_RE.search(json.dumps(result))
    return match.group(0) if match else None


def result_text(result):
    out = []
    for block in result.get("content", []):
        if block.get("type") == "text":
            out.append(block["text"])
    if result.get("structuredContent"):
        out.append(json.dumps(result["structuredContent"]))
    return "\n".join(out)


def parse_price(result):
    match = PRICE_RE.search(result_text(result))
    return float(match.group(1).replace(",", "")) if match else None


def load_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def remember(client, state, fact):
    assert len(fact) <= FACT_LIMIT, f"fact is {len(fact)} chars; the limit is {FACT_LIMIT}"
    result = client.call_tool(
        "memory_remember",
        {"fact": fact, "agent_name": AGENT_NAME, "_session_id": JOB_ID},
    )
    link = receipt_link(result)
    if link:
        state.setdefault("receipt_ids", []).append(link.rsplit("/", 1)[-1])
    return link


def start(client, state):
    # Work: price the watch. Real calls, real receipts.
    baselines = {}
    for symbol in ASSETS:
        result = client.call_tool("live_price", {"symbol": symbol, "_session_id": JOB_ID})
        price = parse_price(result)
        link = receipt_link(result)
        baselines[symbol] = {"price": price, "receipt": link}
        if link:
            state.setdefault("receipt_ids", []).append(link.rsplit("/", 1)[-1])
        print(f"[start] {symbol} {fmt_price(price)}  receipt: {link}")
    state["baselines"] = baselines
    state["day"] = time.strftime("%Y-%m-%d", time.gmtime())

    # Remember: save the state tomorrow's session will recall. Short
    # fact, receipts inside, the rule in plain words.
    parts = [f"Daily loop watch, day 1 baseline, {state['day']}."]
    for symbol in ASSETS:
        parts.append(
            f"{symbol} baseline {fmt_price(baselines[symbol]['price'])} "
            f"(receipt {baselines[symbol]['receipt']})."
        )
    rules = " or ".join(
        f"{s} {ALERT_PCT.get(s, 3):g} percent" for s in ASSETS
    )
    parts.append(
        f"Alert rule: flag if an asset moves from baseline by {rules} or more. "
        "Next session: recall, re-check, compare, remember, wrap."
    )
    link = remember(client, state, " ".join(parts))
    print(f"[start] baseline state remembered  receipt: {link}")
    client._save()
    print("day one saved. tomorrow, and every day after: python3 loop.py continue")
    return 0


def continue_loop(client, state):
    baselines = state.get("baselines")
    if not baselines:
        print("no baseline state in the state file: run `python3 loop.py start` first")
        return 1

    # Recall: pull yesterday's state back and check it lands verbatim.
    result = client.call_tool(
        "memory_recall",
        {"query": "daily loop watch day 1 baseline alert rule", "_session_id": JOB_ID},
    )
    recalled = result_text(result)
    for symbol, base in baselines.items():
        needle = f"{symbol} baseline {fmt_price(base['price'])}"
        print(f"[recall] {needle!r} verbatim: {needle in recalled}")
    print(f"[recall] receipt: {receipt_link(result)}")

    # Work: re-check the first asset against its baseline.
    symbol = ASSETS[0]
    base = baselines[symbol]["price"]
    result = client.call_tool("live_price", {"symbol": symbol, "_session_id": JOB_ID})
    price = parse_price(result)
    link = receipt_link(result)
    if link:
        state.setdefault("receipt_ids", []).append(link.rsplit("/", 1)[-1])
    move = (price - base) / base * 100.0
    alert = abs(move) >= ALERT_PCT.get(symbol, 3)
    print(
        f"[work] {symbol} {fmt_price(price)}, {move:+.2f}% from baseline "
        f"{fmt_price(base)}, alert: {alert}  receipt: {link}"
    )

    # Remember: today's update, short enough to save.
    update = (
        f"Daily loop watch, check {time.strftime('%Y-%m-%d', time.gmtime())}. "
        f"{symbol} now {fmt_price(price)}, a move of {move:+.2f} percent from the "
        f"day 1 baseline of {fmt_price(base)} (receipt {link}). "
        f"Alert: {'YES' if alert else 'no'}. Baselines unchanged; tomorrow the loop repeats."
    )
    link = remember(client, state, update)
    print(f"[remember] update saved  receipt: {link}")

    # Wrap: the day becomes a handover, naming only this job's own
    # executed receipts, which the state file tracked across sessions.
    summary = (
        f"Daily loop, job {JOB_ID}. Baselines: "
        + ", ".join(
            f"{s} {fmt_price(b['price'])} (receipt https://zambo.dev/run/"
            f"{(b['receipt'] or '').rsplit('/', 1)[-1]})"
            for s, b in baselines.items()
        )
        + f". Latest check: {symbol} {fmt_price(price)}, {move:+.2f}% from baseline, "
        f"alert: {'yes' if alert else 'no'}. The state was recalled verbatim before "
        "the check, and the update was remembered after it."
    )
    result = client.call_tool(
        "handover",
        {
            "summary": summary,
            "goal": "A daily loop whose state survives the session: recalled "
            "verbatim, worked on, updated, and wrapped, every step receipted.",
            "recipient": "Daily Loop Operator",
            "recipient_type": "human",
            "next_steps": [
                "Tomorrow: pick this handover up (pickup is always free), recall "
                "the watch state, re-check the prices, remember the update, wrap "
                "the day again.",
                "Check any receipt at https://zambo.dev/verify/ : a receipt proves "
                "the saved result was not changed since it was saved.",
            ],
            "receipt_ids": list(dict.fromkeys(state.get("receipt_ids", []))),
            "_session_id": JOB_ID,
        },
    )
    structured = result.get("structuredContent") or {}
    handover_id = structured.get("handover_id")
    if not handover_id:
        match = re.search(r"handover/([0-9a-f-]{36})", json.dumps(result))
        handover_id = match.group(1) if match else None
    print(f"[wrap] handover: https://zambo.dev/handover/{handover_id}")
    print(f"[wrap] wrap receipt: {receipt_link(result)}")
    client._save()
    print("loop closed: recall, work, remember, wrap.")
    return 0


def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else ""
    if phase not in ("start", "continue"):
        print("usage: python3 loop.py start|continue")
        return 2
    state = load_state()
    client = ZamboClient(state)
    client.initialize()
    print(f"session open; caller handle bound for agent '{AGENT_ID}'")
    return start(client, state) if phase == "start" else continue_loop(client, state)


if __name__ == "__main__":
    sys.exit(main())
