# LangChain / LangGraph Middleware — Interview Mastery Notes

> Rebuilt from your uploaded Q1–15 notes and cross-checked against the current
> LangChain (`langchain.agents.middleware`) and LangGraph docs/reference as of
> **August 2026**. Your original notes were conceptually strong — the mental
> models mostly survive intact — but a few specifics were either invented,
> outdated, or hedged as "unverifiable." Those are now verified and corrected.

**Legend**
- ✅ Verified against current official docs/reference — safe to state confidently in an interview.
- ⚠️ **Correction** — this differs from what your original notes said.
- 🔧 Real, runnable-shape code (import paths and parameter names are accurate).
- 🧠 "Hard mode" — the kind of follow-up a strong interviewer asks *after* you give the textbook answer.

---

## ⚠️ Corrections to know before anything else

These are the four places your original notes will get you into trouble if quoted verbatim in an interview:

| # | Your notes said | Reality |
|---|---|---|
| 7 | HITL has **four** decisions: Approve / Reject / Edit / **Continue** | HITL has **three** decision types: `approve`, `edit`, `reject`. "Continue" isn't a decision — it's what you call resuming *any* interrupted graph (`Command(resume=...)`), HITL or otherwise. Don't list it as a fourth decision type. |
| 11 | `ToolErrorMiddleware` is a built-in class | **No such class exists** in `langchain.agents.middleware`. Tool-error handling is done via a custom `@wrap_tool_call` hook, or `ToolNode(handle_tool_errors=...)`, or `ToolRetryMiddleware`'s own `on_failure` param. |
| 9 | "Workflow/graph-level retry" is a third middleware type | It's not agent-middleware at all — it's LangGraph's node-native `RetryPolicy`, attached via `add_node(..., retry_policy=RetryPolicy(...))`. It lives one layer below the agent-middleware system entirely. |
| 12 | PII directions are "input / tool calls / output" | The actual `PIIMiddleware` params are `apply_to_input`, `apply_to_output`, `apply_to_tool_results` — it's tool **results**, not tool call arguments, that get the dedicated flag. `apply_to_input` defaults to `True`. |

Everything else in your notes was directionally correct; below is the fully-verified, interview-hardened version.

---

## Part 0 — LangGraph Foundations

### 0.1 `thread_id` vs `checkpointer` vs `context` — the precise relationship

Your mental model was right: `thread_id` identifies, `checkpointer` persists. Here's the API-accurate version plus the trap interviewers love.

```python
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(model="gpt-5.5", tools=[...], checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "rohan-trip-001"}}
agent.invoke({"messages": [...]}, config=config)
```

- `thread_id` is not a special runtime concept — it's just a well-known key inside `config["configurable"]` that the checkpointer looks for.
- **`context`** (LangGraph's `Runtime.context`) is a *separate*, newer mechanism (LangGraph ≥0.6) for static run dependencies — `user_id`, `db_conn`, feature flags. It answers "what does this run need to know," not "which conversation is this."
- ✅ `context` is explicitly documented as the long-term replacement for the old `configurable` dict — **except** for checkpoint-routing keys like `thread_id`, which still must go through `config={"configurable": {...}}` for the checkpointer to recognize them.

🧠 **Hard-mode trap:** *"Can I just put `thread_id` inside `context` since that's the modern pattern?"*
No — as of LangGraph 1.0, this is a known sharp edge: passing `context` and `config` together is disallowed in some entry points (e.g. `RemoteGraph`), and even where allowed, a `thread_id` placed only in `context` is **not picked up by the checkpointer** — you lose persistence silently. `thread_id` must go through `configurable`. This is one of the most commonly mis-answered "gotcha" questions right now because the docs are actively migrating.

### 0.2 `stream_mode` — there are seven, not three

Your notes covered the three most commonly demoed modes. The full, current list (`graph.stream(..., stream_mode=...)`):

| Mode | What you get |
|---|---|
| `values` | Full state after each node |
| `updates` | Only the diff each node returned |
| `messages` | Token-level LLM output (chat-UI streaming) |
| `custom` | Arbitrary data a node writes via `get_stream_writer()` |
| `checkpoints` | Checkpoint objects as they're written (requires a checkpointer) |
| `tasks` | Node start/finish events, including errors |
| `debug` | Everything — verbose trace-level detail |

You can pass a **list** of modes: `stream_mode=["updates", "custom"]`, and each chunk is tagged with its mode.

🧠 **Hard mode:** *"You need a progress bar showing % complete inside a single long-running node, not just node-to-node updates. Which mode?"*
Not `updates` (that only fires when a node **finishes**). Use `custom` with `get_stream_writer()` called from inside the node to emit interim progress — this is the documented pattern for sub-node granularity. As of LangGraph v1.2, there's also a **typed-projection "event streaming" API** that gives separate iterators per projection (messages/values/subgraphs/output) instead of branching on `stream_mode` — worth mentioning if asked about "the new way."

### 0.3 Agent naming (`name=`) — still conceptually correct

This one was fine as written: naming costs nothing at single-agent scale and becomes essential the moment you're in a supervisor/sub-agent topology (LangGraph supervisor patterns, deep agents' sub-agents) — for tracing, LangSmith run identification, and routing logs. No correction needed here; just don't over-claim it as a specific top-level `create_agent(name=...)` parameter unless the interviewer is asking about a specific sub-agent framework, since naming conventions differ slightly between `create_agent`, supervisor libraries, and deep-agents' `subagents` list.

---

## Part 1 — What middleware actually is, mechanically

Middleware is not a separate runtime — it's hooks that get compiled directly **into** the LangGraph graph that `create_agent()` returns. That's why you can drop a fully-middleware-equipped agent into a bigger `StateGraph` as a node/subgraph and every hook still fires.

```python
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, HumanInTheLoopMiddleware

agent = create_agent(
    model="gpt-5.5",
    tools=[...],
    middleware=[SummarizationMiddleware(...), HumanInTheLoopMiddleware(...)],
)
```

### 1.1 Three hook families

| Family | Hooks | Shape |
|---|---|---|
| **Node-style** ("before/after") | `before_agent`, `before_model`, `after_model`, `after_agent` | `(state, runtime) -> dict | None` — return a partial state update, or `None` to pass through |
| **Wrap-style** ("around") | `wrap_model_call`, `wrap_tool_call` | `(request, handler) -> response` — you control whether/how many times `handler` is called |
| **Convenience** | `dynamic_prompt`, decorator forms (`@before_model`, `@wrap_tool_call`, etc.) | Turns a plain function into middleware without a class |

### 1.2 Execution order — the part that trips people up

✅ Verified directly from LangChain's custom-middleware docs. For `middleware=[M1, M2, M3]`:

```
before_* (node-style):        M1 → M2 → M3 → [core step]
wrap_* (wrap-style):          M1.wrap( M2.wrap( M3.wrap( core ) ) )
    → on the way IN:          M1 → M2 → M3 → core
    → on the way OUT:         core → M3 → M2 → M1
after_* (node-style):         [core step] → M3 → M2 → M1   (reverse of before_*)
```

Rule of thumb, stated precisely: **`before_*` runs in list order. `after_*` runs in reverse list order. `wrap_*` nests with the first-declared middleware as the outermost layer** — meaning it's the *last* to touch the request going in, and the *first* to see the response coming back... no, precisely: outermost = first to see the request, last to see the response. (`M1` wraps `M2` wraps `M3` wraps core → `M1` is outermost.)

🧠 **Hard mode:** *"You register `before_model` on M1 and it returns `{"jump_to": "__end__"}`. Does M2's `before_model` still run?"*
No. A `before_model` hook returning a jump/early-termination signal short-circuits the remaining `before_*` chain for that step — this is the documented mechanism for early termination (e.g., `ModelCallLimitMiddleware`'s `exit_behavior="end"` uses exactly this). Also worth knowing: **jumping to `"model"` from inside `before_model` itself is explicitly disallowed** to preserve ordering guarantees.

---

## Part 2 — `HumanInTheLoopMiddleware` (corrected)

```python
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model="gpt-5.5",
    tools=[transfer_funds, check_balance],
    checkpointer=InMemorySaver(),          # REQUIRED — interrupts need to survive the pause
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "transfer_funds": {"allowed_decisions": ["approve", "edit", "reject"]},
                "check_balance": False,     # no approval needed — safe, read-only
            },
            description_prefix="Approval required",
        ),
    ],
)
```

### The three real decisions

| Decision | Meaning | Resume payload |
|---|---|---|
| `approve` | Execute exactly as proposed | `{"type": "approve"}` |
| `edit` | Correct the args, then execute | `{"type": "edit", "editedAction": {...}}` |
| `reject` | Do not execute; optionally attach a message the model sees | `{"type": "reject", "message": "..."}` |

Resuming is done via `Command(resume=...)`, which is the "continue the workflow" step — but that's a *generic* LangGraph resume mechanism, not a fourth HITL decision.

🧠 **Hard mode:**
- *"Where in the hook lifecycle does HITL interrupt?"* — `after_model`, i.e. after the model proposes the tool call but before `ToolNode` executes it. That's the natural checkpoint: you have the proposed action, but nothing has run yet.
- *"What breaks if you forget the checkpointer?"* — `interrupt()` needs somewhere to persist the paused state while waiting (possibly minutes/hours) for a human. Without a checkpointer, LangGraph has nowhere to write that pause, and resume becomes impossible — you'd effectively be starting a brand-new run.
- *"NovaBank wants sub-agents to also pause for approval — does HITL propagate into subagents automatically?"* — Be careful here: there's a known real-world limitation (`deepagents` issue #554) where `edit`/`reject` resume can fail for tool calls originating inside **subagents**, even though `approve` works — worth flagging as "verify against your framework version" rather than assuming it just works.

---

## Part 3 — Context engineering: `SummarizationMiddleware` vs `ContextEditingMiddleware`

Your "long conversation → summarize; huge tool output → context-edit" heuristic is correct. Here's the accurate API for both.

### `SummarizationMiddleware` — implements `before_model`

```python
from langchain.agents.middleware import SummarizationMiddleware

SummarizationMiddleware(
    model="openai:gpt-4o-mini",       # can differ from the main agent model
    max_tokens_before_summary=3000,   # trigger threshold
    messages_to_keep=20,              # most recent messages preserved verbatim
)
```
Mechanically: when the token threshold is crossed, older messages are compressed into a summary message; the most recent N messages stay intact so recency/detail isn't lost.

### `ContextEditingMiddleware` + `ClearToolUsesEdit`

```python
from langchain.agents.middleware import ContextEditingMiddleware, ClearToolUsesEdit

ContextEditingMiddleware(
    edits=[
        ClearToolUsesEdit(
            trigger=100_000,        # token count that triggers the edit (or {"tokens":.., "messages":..})
            keep=3,                 # most recent tool results that are NEVER cleared
            clear_tool_inputs=False,# optionally also clear the AI message's tool-call args
            exclude_tools=[],       # tools whose results are exempt from clearing
            placeholder="[cleared]",
        ),
    ],
)
```
✅ This mirrors Anthropic's `clear_tool_uses_20250919` server-side behavior. Default trigger is 100,000 tokens if unset.

🧠 **Hard mode:**
- *"Can you use both together, and if so, what fires first?"* — Yes, and it matters: context editing should generally run **before** summarization in your production stack, because you want to discard dead tool-output weight first (cheap, mechanical) before spending an LLM call summarizing what's left (expensive). This isn't enforced by the framework — it's a design choice you make in how you order/trigger them.
- *"Why does `ClearToolUsesEdit` replace with a placeholder instead of deleting the message entirely?"* — Message-shape integrity: most providers require every `tool_use` block to have a matching `tool_result` block. Deleting the tool result outright would desync the message list; replacing its *content* with a placeholder keeps the structure valid while reclaiming the token cost.

---

## Part 4 — Retry, correctly separated into the actual three layers

Your "what failed?" framing is exactly right — but the names were partly invented. Here's what's real:

### Layer 1 — Model retry: `ModelRetryMiddleware`
```python
from langchain.agents.middleware import ModelRetryMiddleware
ModelRetryMiddleware(max_retries=3, backoff_factor=2.0, retry_on=(RateLimitError,))
```
Use when the **LLM API call itself** fails (503, rate limit, timeout).

### Layer 2 — Tool retry: `ToolRetryMiddleware`
```python
from langchain.agents.middleware import ToolRetryMiddleware
ToolRetryMiddleware(
    max_retries=3,
    backoff_factor=2.0,
    initial_delay=1.0,
    tools=["get_balance"],            # None = applies to all tools
    on_failure="continue",            # 'continue' (default) | 'error' | callable
)
```
Use when a **specific tool call** fails. `on_failure="continue"` returns a `ToolMessage` describing the failure so the LLM can react; `"error"` re-raises and halts the run.

### Layer 3 — Workflow/node retry: LangGraph's `RetryPolicy` ⚠️ *not agent-middleware*
```python
from langgraph.types import RetryPolicy

workflow.add_node(
    "charge_payment",
    charge_payment,
    retry_policy=RetryPolicy(max_attempts=3, retry_on=ConnectionError),
    error_handler=payment_error_handler,   # optional compensation routing
)
```
This lives at the **graph-construction level**, not inside `create_agent`'s middleware list — it's how you make a whole node (which might itself contain several tool calls, or non-LLM logic) resilient. Default policy retries transient errors (connection errors, 5xx) and explicitly does **not** retry `ValueError`/`TypeError`. Retries clear that node's partial writes between attempts, so failed side effects don't leak into state.

🧠 **Hard mode:**
- *"NovaBank's `transfer_funds` timed out — did the money move or not? Should you retry?"* — This is the trap question. Automatic retry (any layer) is dangerous on a non-idempotent mutation: if the first call actually succeeded and only the *response* was lost, a naive retry double-transfers. The correct production answer is: the tool itself needs an idempotency key (client-generated request ID the bank API dedupes on) **before** you're allowed to safely wrap it in `ToolRetryMiddleware`. Retry middleware is a reliability layer, not a substitute for idempotent API design.
- *"How do `ToolRetryMiddleware.on_failure` and a custom `wrap_tool_call` error formatter interact if both are in your middleware list?"* — This is the corrected version of your original Q11. `wrap_*` composes with **first-in-list = outermost**. So if you want "retry gets first crack at recovery, and only if it truly gives up does your custom formatter produce the final message," you need:
  ```python
  middleware=[my_custom_error_formatter, ToolRetryMiddleware(on_failure="error")]
  ```
  `ToolRetryMiddleware` here is *innermost* (closer to the actual tool call), so it sees the exception first and retries. Only when it exhausts retries and `on_failure="error"` re-raises does the exception propagate outward to your custom formatter. If you left `on_failure="continue"` (the default), `ToolRetryMiddleware` fully absorbs the failure itself and your outer formatter never even sees an exception — nothing to catch. This dependency between `on_failure` and list order is exactly the kind of thing that separates a "textbook" answer from a "actually shipped this" answer.

---

## Part 5 — `ToolCallLimitMiddleware` vs `ModelCallLimitMiddleware`

```python
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware

ModelCallLimitMiddleware(
    thread_limit=10,     # across ALL runs sharing a thread_id — needs a checkpointer
    run_limit=5,         # per single .invoke() call
    exit_behavior="end", # 'end' (graceful) | 'error' (raise)
)

ToolCallLimitMiddleware(
    tools=["transfer_funds"],  # None = global, across all tools
    run_limit=1,
)
```

Both intercept **before** the call happens (`ModelCallLimitMiddleware` checks in `wrap_model_call`-adjacent logic before sending the request) and both raise/exit rather than letting the call happen and cleaning up after.

🧠 **Hard mode:** *"`thread_limit` requires a checkpointer — why?"* Because "across all runs in a thread" is inherently a cross-invocation count; without persistence there's no thread-scoped counter to check against, only an in-memory per-run counter. This is the same dependency pattern as HITL needing a checkpointer, and it's a good instinct to flag any time a middleware promises "thread-scoped" behavior.

---

## Part 6 — `PIIMiddleware`, precisely

```python
from langchain.agents.middleware import PIIMiddleware

middleware = [
    PIIMiddleware("email", strategy="redact", apply_to_input=True),
    PIIMiddleware("credit_card", strategy="mask",
                   apply_to_input=True, apply_to_output=True, apply_to_tool_results=True),
    PIIMiddleware("account_number", detector=r"\d{12}", strategy="block", apply_to_input=True),
]
```

- **Strategies:** `block` (raise `PIIDetectionError`), `redact` (`[REDACTED_EMAIL]`), `mask` (partial, e.g. `****-****-****-1234`), `hash` (deterministic hash).
- **Directions:** `apply_to_input` (default `True`), `apply_to_output`, `apply_to_tool_results`. Note it's *results*, not call arguments — the middleware inspects what tools *return*, not what the model *sends* them, on that flag.
- Implements `before_model` **and** `after_model` hooks.
- Built-in types: email, credit card, IP, MAC address, URL — anything else (like a bank account number) needs a custom `detector` (regex string or callable returning `[{"text":..., "start":..., "end":...}]`).

For NovaBank account numbers specifically, all three directions enabled with `strategy="mask"` on output/tool-results (so support staff still see a partial number for verification) and `strategy="block"` or `"redact"` on input (don't even let a typed-in full number reach the model) is a defensible, explainable design — good interview framing.

🧠 **Hard mode:** *"With `apply_to_output=True`, does PII redaction apply to token-by-token streaming, or only the final message?"* As of `langchain>=1.3.2`, `apply_to_output=True` also redacts the **streamed wire output** — text deltas, tool-call args, tool outputs — via a registered stream transformer, not just the final settled message. This matters a lot if you're piping `stream_mode="messages"` straight to a UI: without this, redaction-on-the-final-object still lets raw PII flash across the wire mid-stream.

---

## Part 7 — Tool selection & emulation, disambiguated

Three easily-confused middleware live here. Keep them separate:

### `LLMToolEmulator` — for **testing**, not selection
```python
from langchain.agents.middleware import LLMToolEmulator
LLMToolEmulator(tools=["send_email"], model="anthropic:claude-haiku-4-5")
```
⚠️ This one is commonly misunderstood (your original Q13 hedged on it correctly). It does **not** select or route tools — it **fakes their execution**. Instead of actually calling `send_email`, a (typically cheap/fast) LLM generates a plausible fake tool response, so you can test agent reasoning/branching without hitting real APIs, sending real emails, or moving real money. `tools=None` (default) emulates *everything*; `tools=[]` emulates nothing.
- **Why the explicit `model=` matters:** if unset, you risk an ambiguous default that silently differs from your main agent's model — inconsistent fake-data "voice," unpredictable cost, harder debugging. Explicit `model=` is a professional-habit signal in an interview answer.

### `LLMToolSelectorMiddleware` — LLM-driven filtering
```python
from langchain.agents.middleware import LLMToolSelectorMiddleware
LLMToolSelectorMiddleware(model="openai:gpt-4o-mini", max_tools=3)
```
Runs a fast/cheap LLM inside `wrap_model_call` to pick the relevant subset of tools from a large registry (NovaBank's 15 tools → maybe 2 relevant ones for "what's my balance") before the *main* model ever sees the full list. Reduces context bloat and tool-selection confusion. Works with **any** provider — the intelligence is LangChain's own LLM call, not a provider feature.

### `ProviderToolSearchMiddleware` — provider-native, not LLM-driven
```python
from langchain.agents.middleware import ProviderToolSearchMiddleware
ProviderToolSearchMiddleware(searchable_tools=["lookup_order"])
```
Marks specific tools as **deferred** (`extras["defer_loading"]`) and hands discovery off to the *model provider's own* server-side tool-search capability — the full schema for a deferred tool is only fetched when the provider decides it's needed, keeping the request payload small.
⚠️ **Constraint, verified:** currently only Anthropic and OpenAI support server-side tool search. If a tool is deferred but the resolved provider doesn't support it, the call **raises `ValueError`** — this is not a silent fallback. That's the correct answer to "what happens if you use this with an unsupported model."

🧠 **Hard mode:** *"NovaBank is provider-agnostic (sometimes OpenAI, sometimes a local model) but wants tool-list bloat solved reliably. Which of the two selection middlewares do you pick, and why?"* `LLMToolSelectorMiddleware` — it's provider-independent because the selection logic is LangChain's own LLM call in `wrap_model_call`, not a provider capability. `ProviderToolSearchMiddleware` is strictly better *when* available (no extra LLM call, no extra cost/latency for the selection step itself) but it's an opt-in feature of a specific provider, so it's the wrong choice for a multi-provider or self-hosted-model setup — it would raise `ValueError` the moment you swap providers.

---

## Part 8 — A corrected, production-grade NovaBank middleware stack

```python
from langchain.agents import create_agent
from langchain.agents.middleware import (
    PIIMiddleware, ContextEditingMiddleware, ClearToolUsesEdit,
    SummarizationMiddleware, ModelCallLimitMiddleware, ToolCallLimitMiddleware,
    HumanInTheLoopMiddleware, ToolRetryMiddleware, ModelRetryMiddleware,
)
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import RetryPolicy

agent = create_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[check_balance, transfer_funds],
    checkpointer=InMemorySaver(),
    middleware=[
        # 1. Guardrails first — never let raw PII hit the model or leak back out
        PIIMiddleware("account_number", detector=r"\d{12}", strategy="mask",
                       apply_to_input=True, apply_to_output=True, apply_to_tool_results=True),

        # 2. Resource ceilings — cheap to check, catch runaway behavior before it costs money
        ModelCallLimitMiddleware(thread_limit=20, run_limit=8, exit_behavior="end"),
        ToolCallLimitMiddleware(tools=["transfer_funds"], run_limit=1),

        # 3. Context hygiene — cheap mechanical pruning before expensive summarization
        ContextEditingMiddleware(edits=[ClearToolUsesEdit(trigger=8000, keep=3)]),
        SummarizationMiddleware(model="anthropic:claude-haiku-4-5",
                                 max_tokens_before_summary=6000, messages_to_keep=15),

        # 4. Reliability — model & tool layers only; transfer_funds is excluded from blind retry
        ModelRetryMiddleware(max_retries=2),
        ToolRetryMiddleware(max_retries=3, tools=["check_balance"], on_failure="continue"),

        # 5. The real safety boundary — human approval on the consequential action
        HumanInTheLoopMiddleware(interrupt_on={
            "transfer_funds": {"allowed_decisions": ["approve", "edit", "reject"]},
        }),
    ],
)
```

Notice `transfer_funds` is **deliberately excluded** from `ToolRetryMiddleware` — this is the idempotency point from Part 4. A separate, node-level `RetryPolicy` with `retry_on=` scoped to genuinely-safe-to-retry exceptions (e.g. a pre-flight connectivity check node, not the mutation itself) would be the honest way to add resilience there without risking a double transfer.

---

## Part 9 — Rapid-fire hard-mode Q&A

**Q. You put `ModelCallLimitMiddleware` and `HumanInTheLoopMiddleware` in the same list. The call limit is hit while a HITL interrupt is pending resume. What happens?**
The call-limit check runs in the model-call path; a pending interrupt means execution is paused *before* re-entering that path, so the count doesn't advance while paused. But once resumed, the check resumes counting from where it left off (it's thread/run-scoped state, not wall-clock-scoped) — resuming after a long approval delay doesn't reset or bypass the limit.

**Q. Why does `SummarizationMiddleware` accept its own `model=` separate from the agent's main model, and is that a good default to change?**
Summarization is a cheap, mechanical task relative to the main reasoning loop — using a smaller/cheaper model (e.g. `gpt-4o-mini` while the agent runs `gpt-5.5`) is the documented common pattern, trading a little summary quality for meaningfully lower cost on every trigger, since summarization can fire many times in a long-running thread.

**Q. If `PIIMiddleware("email", strategy="block")` raises `PIIDetectionError`, does the agent see it as a normal tool failure it can react to?**
No — `block` is meant to be a hard stop, not a recoverable `ToolMessage`. It's an exception the *application* is expected to catch, not something the LLM gets a chance to route around (contrast with `ToolRetryMiddleware(on_failure="continue")`, which deliberately hands the failure back to the model). Confusing these two failure philosophies — "stop the world" vs "let the model try again" — is a common design mistake.

**Q. Two middleware both implement `before_model` and both try to modify the outgoing message list. Who wins?**
They run in list order, each receiving the state as mutated by the previous one's returned partial update (LangGraph merges partial state updates). So order is significant and "last-registered wins" only holds if they touch the exact same state key — otherwise both edits can coexist. This is why order in the `middleware=[]` list is a real design decision, not cosmetic.

**Q. Where does `dynamic_prompt` fit into the hook lifecycle, and why isn't it just another `before_model` implementation?**
It's a purpose-built convenience hook specifically for generating the system prompt based on current state/context at call time (e.g., inject the user's tier, current date, or retrieved memory into the prompt per-turn) — it exists separately because prompt construction is common enough to deserve its own decorator (`@dynamic_prompt`) rather than everyone hand-rolling the same `before_model` pattern.

**Q. Middleware A does `wrap_model_call` and calls `handler(request)` twice. Is that safe?**
Yes — this is the documented retry pattern (see `ToolRetryMiddleware`/`ModelRetryMiddleware` source). The docs explicitly note the handler can be invoked multiple times, and **each call is independent and stateless** — so retrying doesn't accumulate side effects from the prior attempt.

---

## Part 10 — Appendix: other built-ins worth recognizing by name

You likely won't need deep API knowledge of these for a mid-level interview, but recognizing them (and not confusing them with the ones above) signals breadth:

| Middleware | One-liner |
|---|---|
| `ModelFallbackMiddleware` | Falls back to an alternate model if the primary model call fails outright |
| `TodoListMiddleware` | Gives the agent a structured todo-list tool for multi-step task tracking (used heavily in "deep agent" patterns) |
| `AnthropicPromptCachingMiddleware` | Applies Anthropic prompt-caching breakpoints automatically to cut repeated-context cost |
| `ShellToolMiddleware` | Provides a sandboxed shell-execution tool |
| `PlanningMiddleware` | Structured planning step before execution, distinct from the todo-tracking of `TodoListMiddleware` |

---

## Final Cheat Sheet

| Topic | One-line answer that survives follow-ups |
|---|---|
| `thread_id` vs `context` | `thread_id` → `configurable`, routes to the checkpointer. `context` → static run dependencies, not persisted. Don't put `thread_id` inside `context`. |
| `stream_mode` | 7 modes exist: values, updates, messages, custom, checkpoints, tasks, debug. `custom` is for sub-node progress. |
| Hook ordering | `before_*` forward, `after_*` reverse, `wrap_*` nests (first-in-list = outermost). |
| HITL decisions | Exactly three: `approve`, `edit`, `reject`. Fires in `after_model`. Requires a checkpointer. |
| Summarization vs Context Editing | Summarization compresses conversation *history*; context editing prunes *tool output* weight. Run context editing before summarization when combined. |
| Retry, 3 real layers | `ModelRetryMiddleware` (LLM call failed) / `ToolRetryMiddleware` (tool call failed) / LangGraph `RetryPolicy` on a node (graph-level, not agent middleware). Never blind-retry non-idempotent mutations. |
| Tool limit vs Model limit | `ToolCallLimitMiddleware` = specific action budget. `ModelCallLimitMiddleware` = whole-loop budget; `thread_limit` needs a checkpointer. |
| PII directions | `apply_to_input` (default True) / `apply_to_output` / `apply_to_tool_results` — results, not call args. |
| Tool selection trio | `LLMToolEmulator` = fakes tool execution for testing. `LLMToolSelectorMiddleware` = LLM picks relevant tools, provider-agnostic. `ProviderToolSearchMiddleware` = provider-native, Anthropic/OpenAI only, raises `ValueError` elsewhere. |
| Production mindset | Guardrails → limits → context hygiene → reliability → human approval on the consequential action. Idempotency at the API layer is a prerequisite for safe retry, not something middleware gives you for free. |

---

*Sources: docs.langchain.com (middleware overview, built-in, custom, guardrails, streaming, thinking-in-langgraph pages), reference.langchain.com (agents.middleware.* API reference), and the langchain-ai/langchain and langchain-ai/langgraph GitHub repos/issue trackers, all retrieved August 2026. Given how actively this API is evolving (alpha → 1.0 migration), re-verify exact parameter names against your installed version before an interview if you can — pin your `langchain` version and skim its changelog.*
