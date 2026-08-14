# Structured Output vs Tool Schema vs ToolStrategy

## Overview

When building LangChain/LangGraph agents, three concepts can look very similar:

1. `@tool(args_schema=...)`
2. `model.with_structured_output(...)`
3. `ToolStrategy(...)` while creating an agent

They all involve schemas, but they solve **different problems**.

The easiest mental model is:

> **Tool schema = what the tool needs to DO its job**  
> **Structured output = what a model invocation should SAY/return**  
> **ToolStrategy = what the AGENT should ultimately return after its tool loop**

---

# 1. Quick Comparison

| Mechanism | Schema describes | Used by | Main purpose |
|---|---|---|---|
| `@tool(args_schema=...)` | Tool input arguments | Tool / Agent | Tell the LLM how to call an action |
| `model.with_structured_output(Schema)` | Model output | Model | Make a model invocation return structured data |
| `ToolStrategy(Schema)` | Agent final response | Agent runtime | Make an agent return a structured final result |

---

# 2. `@tool(args_schema=...)`

Use this when the LLM needs to **perform an action**.

```python
class SeatBookingInput(BaseModel):
    movie_title: str
    seat_count: int = Field(ge=1, le=10)
    preferred_row: Literal["front", "middle", "back"] = "middle"


@tool(args_schema=SeatBookingInput)
def book_seats(
    movie_title: str,
    seat_count: int,
    preferred_row: str = "middle",
) -> str:
    return f"Booked {seat_count} seat(s) in the {preferred_row} row for {movie_title}."
```

The schema describes the **arguments that the tool accepts**.

Conceptually, the LLM can generate:

```json
{
  "name": "book_seats",
  "arguments": {
    "movie_title": "Avengers",
    "seat_count": 3,
    "preferred_row": "middle"
  }
}
```

The framework validates those arguments and executes the function.

## Important

`SeatBookingInput` does **not** describe the agent's final response.

It describes:

> "If you want to call `book_seats`, these are the arguments you must provide."

---

# 3. When Should You Use a Tool Schema?

Use `@tool(args_schema=...)` when the operation has a real side effect or needs to access something outside the LLM.

Typical examples:

### Database

- `search_customer(customer_id)`
- `get_transaction(transaction_id)`
- `update_customer(...)`

### APIs

- `get_weather(...)`
- `get_stock_price(...)`
- `create_payment(...)`

### Business operations

- `book_movie(...)`
- `cancel_booking(...)`
- `create_jira_ticket(...)`
- `send_email(...)`

### Files

- `read_file(...)`
- `write_file(...)`
- `delete_file(...)`

### Enterprise systems

- `search_salesforce(...)`
- `create_service_ticket(...)`
- `update_order(...)`

The LLM decides **whether and when to call the tool**.

---

# 4. `model.with_structured_output(Schema)`

Use this when you want the **model's response itself to have a predictable structure**.

```python
class CustomerDecision(BaseModel):
    category: Literal["refund", "replacement", "support"]
    priority: Literal["low", "medium", "high"]
    reason: str


structured_model = model.with_structured_output(CustomerDecision)

result = structured_model.invoke(
    "The customer's phone arrived damaged."
)
```

The result is conceptually:

```python
CustomerDecision(
    category="replacement",
    priority="high",
    reason="The product arrived damaged.",
)
```

There is no tool execution here.

You are asking:

> "LLM, analyze this input and return your answer in this exact structure."

---

# 5. Use Cases for `with_structured_output`

## Classification

```python
class TicketClassification(BaseModel):
    category: Literal["billing", "technical", "account"]
    priority: Literal["low", "medium", "high"]
```

Input:

```text
"My payment failed twice."
```

Output:

```python
TicketClassification(
    category="billing",
    priority="high",
)
```

## Information Extraction

For example, extracting information from an invoice:

```python
class Invoice(BaseModel):
    invoice_number: str
    vendor: str
    amount: float
    currency: str
```

The model converts unstructured text into structured application data.

## Entity Extraction

```python
class Person(BaseModel):
    name: str
    company: str
    role: str
```

Input:

```text
"John Smith is a Staff Engineer at ABC Corp."
```

Output:

```python
Person(
    name="John Smith",
    company="ABC Corp",
    role="Staff Engineer",
)
```

## Decision Making

```python
class FraudDecision(BaseModel):
    decision: Literal["approve", "review", "reject"]
    confidence: float
    reason: str
```

## Planning

```python
class Plan(BaseModel):
    steps: list[str]
    estimated_complexity: Literal["low", "medium", "high"]
```

---

# 6. Why Not Just Put the Schema in the Prompt?

You could manually put JSON instructions into the prompt:

```text
Return JSON in this format:

{
  "movie_title": "string",
  "seat_count": 1,
  "preferred_row": "front | middle | back"
}
```

But this is weaker than using an actual schema.

The model might return:

```json
{
  "movie_title": "Avengers",
  "seat_count": "three",
  "preferred_row": "centre"
}
```

Problems:

- `seat_count` is a string instead of an integer
- `centre` isn't one of the allowed values
- The response may contain additional unexpected text
- Validation becomes your responsibility
- The model is only being instructed to follow the format

With Pydantic:

```python
seat_count: int = Field(ge=1, le=10)
preferred_row: Literal["front", "middle", "back"]
```

you have an explicit contract that can be validated.

---

# 7. `ToolStrategy`

Now consider an actual agent.

An agent can:

1. Receive a user request
2. Decide which tools are needed
3. Call one or more tools
4. Receive tool results
5. Continue the tool loop
6. Produce a final response

Conceptually:

```text
User
  ↓
Agent
  ↓
LLM
  ↓
Tool call
  ↓
Tool result
  ↓
LLM
  ↓
Another tool call
  ↓
Tool result
  ↓
LLM
  ↓
Final response
```

Sometimes you don't just want a text final response.

You want:

```python
class BookingResult(BaseModel):
    success: bool
    movie: str
    seats: int
    message: str
```

Then an agent can be configured with a structured response strategy such as:

```python
ToolStrategy(BookingResult)
```

The important idea is:

> **ToolStrategy defines the structured contract for the agent's final response.**

---

# 8. Tool Schema + ToolStrategy Together

You can have **two completely different schemas** in the same agent.

## Tool input schema

```python
class SeatBookingInput(BaseModel):
    movie_title: str
    seat_count: int
    preferred_row: Literal["front", "middle", "back"]
```

This describes:

> "What does `book_seats()` need?"

## Agent output schema

```python
class BookingResult(BaseModel):
    success: bool
    movie: str
    seats: int
    message: str
```

This describes:

> "What should the agent ultimately return?"

Flow:

```text
                    AGENT
                      │
                      ↓
                LLM decides
                      │
                      ↓
               book_seats tool
                      │
              SeatBookingInput
                      │
                      ↓
                Tool executes
                      │
                      ↓
                 Tool result
                      │
                      ↓
                    LLM
                      │
                      ↓
                BookingResult
                      │
                      ↓
              Your application
```

---

# 9. `with_structured_output()` vs `ToolStrategy`

These can appear to do the same thing because both produce structured responses.

The key difference is **where they operate**.

## `with_structured_output()`

Works at the **model invocation level**.

```python
structured_model = model.with_structured_output(MySchema)

result = structured_model.invoke(...)
```

You are saying:

> "For this model call, return `MySchema`."

There may be no agent or tool loop.

## `ToolStrategy()`

Works at the **agent level**.

```python
agent = create_agent(
    model=model,
    tools=[...],
    response_format=ToolStrategy(MySchema),
)
```

You are saying:

> "This agent may use tools and perform its agent loop, but its final response should conform to `MySchema`."

---

# 10. ProviderStrategy vs ToolStrategy

Conceptually:

```text
ToolStrategy
    ↓
Structured response implemented through a tool-based mechanism


ProviderStrategy
    ↓
Structured response implemented using
the model provider's native structured-output capability
```

Do not confuse either of these with your application's actual business tools.

For example:

```python
@tool(args_schema=SeatBookingInput)
def book_seats(...):
    ...
```

is your **business/action tool**.

Whereas:

```python
ToolStrategy(BookingResult)
```

is about the **agent's structured final response**.

---

# 11. Real-World Example: Customer Support Agent

Imagine an enterprise support agent.

Tools:

```python
@tool(args_schema=SearchCustomerInput)
def search_customer(...):
    ...


@tool(args_schema=GetOrdersInput)
def get_orders(...):
    ...


@tool(args_schema=CreateTicketInput)
def create_ticket(...):
    ...
```

The agent's final response:

```python
class SupportResponse(BaseModel):
    issue_type: Literal[
        "billing",
        "technical",
        "account",
        "order",
    ]
    resolution: str
    ticket_created: bool
    ticket_id: str | None
```

Architecture:

```text
                       User
                         │
                         ↓
                  Support Agent
                         │
             ┌───────────┼───────────┐
             ↓           ↓           ↓
       search_customer  get_orders  create_ticket
             │           │           │
             └───────────┼───────────┘
                         ↓
                        LLM
                         │
                         ↓
                  SupportResponse
```

---

# 12. Real-World Example: Banking Agent

Suppose the agent can:

- `get_account_balance()`
- `get_transactions()`
- `transfer_money()`
- `block_card()`

Tool schema:

```python
class TransferMoneyInput(BaseModel):
    destination_account: str
    amount: float
```

Tool:

```python
@tool(args_schema=TransferMoneyInput)
def transfer_money(
    destination_account: str,
    amount: float,
):
    ...
```

Final response:

```python
class BankingResponse(BaseModel):
    action: Literal[
        "balance",
        "transactions",
        "transfer",
        "card_block",
    ]
    success: bool
    message: str
    transaction_id: str | None
```

The distinction is:

```text
TransferMoneyInput
    ↓
"What does transfer_money need?"

BankingResponse
    ↓
"What should my agent ultimately return?"
```

---

# 13. Why This Matters in Production

Separating these schemas gives you clean contracts between components.

Instead of:

```text
LLM → random JSON → application
```

you get:

```text
LLM
 │
 ├── Tool contract
 │       ↓
 │   Tool execution
 │
 └── Agent response contract
         ↓
     Application
```

Benefits:

- Better validation
- Easier debugging
- Clear interfaces
- Easier testing
- More reliable tool calls
- Easier downstream application integration
- Better separation of responsibilities
- Less dependence on prompt instructions

---

# 14. Common Mistake

A common mistake is thinking:

```python
class MySchema(BaseModel):
    ...
```

automatically means:

> "The LLM must return this."

Not necessarily.

Look at **where the schema is attached**.

### Attached to a tool

```python
@tool(args_schema=MySchema)
```

Means:

> Tool input contract.

### Attached to the model

```python
model.with_structured_output(MySchema)
```

Means:

> Model output contract.

### Attached to the agent

```python
ToolStrategy(MySchema)
```

Means:

> Agent final response contract.

---

# 15. Practical Decision Tree

## Does the LLM need to perform an action?

If yes:

```python
@tool(args_schema=...)
```

Examples:

- Call API
- Search database
- Send email
- Create ticket
- Book seats
- Update CRM

## Do I only need structured data from the model?

If yes:

```python
model.with_structured_output(MySchema)
```

Examples:

- Classification
- Extraction
- Entity extraction
- Decision
- Analysis
- Planning

## Am I building an agent and want its final result typed?

If yes:

```python
ToolStrategy(MySchema)
```

Examples:

- Customer support agent
- Booking agent
- Financial operations agent
- Enterprise workflow agent
- Research agent
- Multi-tool automation agent

---

# 16. Three-Layer Mental Model

```text
                    SCHEMA
                      │
       ┌──────────────┼──────────────┐
       │              │              │
       ↓              ↓              ↓
    Tool           Model           Agent
       │              │              │
       ↓              ↓              ↓
args_schema    structured_output  ToolStrategy
       │              │              │
       ↓              ↓              ↓
"How do I       "What should     "What should
call this       this model       this agent
function?"      return?"        finally return?"
```

At each layer:

### Tool layer

```python
SeatBookingInput
```

Question:

> "What arguments does this action require?"

### Model layer

```python
with_structured_output(...)
```

Question:

> "What structure should this model invocation return?"

### Agent layer

```python
ToolStrategy(...)
```

Question:

> "What structure should this agent ultimately return?"

---

# 17. Recommended Production Pattern

For a typical production agent, it is completely reasonable to use:

```python
# 1. Tools have input schemas

@tool(args_schema=SearchCustomerInput)
def search_customer(...):
    ...


@tool(args_schema=CreateTicketInput)
def create_ticket(...):
    ...


# 2. Agent has a final response schema

class AgentResponse(BaseModel):
    success: bool
    answer: str
    action_taken: str | None


# 3. Agent uses ToolStrategy

agent = create_agent(
    model=model,
    tools=[
        search_customer,
        create_ticket,
    ],
    response_format=ToolStrategy(AgentResponse),
)
```

This gives you a clean separation:

```text
                Agent
                  │
       ┌──────────┴──────────┐
       │                     │
       ↓                     ↓
   Tool schemas         Final response
       │                     │
       ↓                     ↓
  Tool arguments        ToolStrategy
       │
       ↓
   Real actions
```

---

# 18. Final Cheat Sheet

```text
@tool(args_schema=...)
        │
        └── "What arguments does my tool need?"

model.with_structured_output(...)
        │
        └── "What structured data should this model call return?"

ToolStrategy(...)
        │
        └── "What structured response should my agent ultimately return?"
```

## One-line rule

> **`@tool(args_schema=...)` = DO**  
> **`with_structured_output()` = SAY**  
> **`ToolStrategy()` = AGENT'S FINAL SAY**

## Most important distinction

The same Pydantic `BaseModel` can be used in different places, but its **meaning changes based on where you attach it**.

```text
                    Pydantic Schema
                          │
          ┌───────────────┼───────────────┐
          ↓               ↓               ↓
      Tool schema     Model schema     Agent schema
          │               │               │
      tool input       model output    final response
```

That is the core concept to remember when designing LangChain/LangGraph systems.


---

# 19. `.bind_tools()` — Give the Model Access to Tools

`.bind_tools()` makes the model aware of available tools and allows it to generate tool calls. It does **not** execute the tools.

```python
model_with_tools = model.bind_tools([get_weather])

response = model_with_tools.invoke(
    "What's the weather in Jaipur?"
)
```

The model may return a tool call conceptually:

```python
AIMessage(
    content="",
    tool_calls=[
        {
            "name": "get_weather",
            "args": {"city": "Jaipur"}
        }
    ]
)
```

The model has said:

> "I want you to call `get_weather(city='Jaipur')`."

It has not necessarily executed the Python function.

---

# 20. `.bind_tools()` vs `@tool`

These work together; they are not alternatives.

### `@tool`

```python
@tool
def get_weather(city: str) -> str:
    return f"Weather in {city}: Sunny"
```

Defines the action and its input contract.

### `.bind_tools()`

```python
model_with_tools = model.bind_tools([get_weather])
```

Exposes that tool to the model.

The relationship is:

```text
@tool
  ↓
Define tool
  ↓
bind_tools()
  ↓
Give tool definitions to model
  ↓
LLM can generate tool calls
```

So:

> **`@tool` defines the action. `.bind_tools()` makes the action available to the model.**

---

# 21. `.bind_tools()` Does Not Execute Tools

This:

```python
model_with_tools = model.bind_tools([
    search_customer,
    create_ticket,
    send_email,
])
```

does **not** mean those functions immediately run.

Instead:

```text
User
  ↓
LLM + bound tools
  ↓
Tool call?
  ├── No  → Final response
  └── Yes
        ↓
   Your application / ToolNode
        ↓
   Execute tool
        ↓
   Tool result
        ↓
   Send result to LLM
        ↓
       LLM
```

When using `.bind_tools()` directly, you are responsible for the execution/orchestration loop unless another framework component handles it.

This is the critical distinction:

> **Binding a tool ≠ running a tool.**

---

# 22. Why Use `.bind_tools()`?

The biggest reason is **control**.

It lets you build your own orchestration logic around tool calls.

You can control:

- Whether a tool call is allowed
- Which tool actually executes
- Human approval
- Authorization
- Retry behavior
- Tool errors
- Maximum iterations
- State management
- Routing
- Which tools are available at each workflow stage

This makes `.bind_tools()` particularly useful with **LangGraph and custom agent loops**.

---

# 23. `.bind_tools()` with LangGraph

A common LangGraph pattern is:

```python
model_with_tools = model.bind_tools(tools)
```

Then the graph can implement:

```text
                 ┌─────────────┐
                 │     LLM     │
                 └──────┬──────┘
                        │
                   tool_calls?
                   /          \
                 YES           NO
                  │             │
                  ↓             ↓
             ToolNode         END
                  │
                  ↓
            Tool results
                  │
                  └────────────→ LLM
```

The LLM decides whether it wants a tool.

The graph decides what happens with that tool call.

This gives you explicit control over execution and routing.

---

# 24. `.bind_tools()` vs an Agent

## Using `.bind_tools()`

```python
model_with_tools = model.bind_tools(tools)
```

You are working closer to the model level:

```text
LLM
 ↓
Tool call
 ↓
YOU / YOUR GRAPH
 ↓
Execute tool
 ↓
Tool result
 ↓
LLM
```

You control the loop.

## Using an Agent

```python
agent = create_agent(
    model=model,
    tools=tools,
)
```

The agent abstraction manages the tool-calling loop for you:

```text
User
 ↓
Agent
 ↓
LLM
 ↓
Tool call
 ↓
Tool execution
 ↓
Tool result
 ↓
LLM
 ↓
Final response
```

So:

> **`.bind_tools()` is a lower-level building block; an agent is a higher-level orchestration abstraction.**

Use `.bind_tools()` when you want to own the workflow. Use an agent when you want a higher-level runtime to manage the tool loop.

---

# 25. When Should You Use `.bind_tools()`?

Use it when you want **explicit control over orchestration**.

### 1. LangGraph workflows

```text
START
 ↓
LLM
 ↓
Tool?
 ├── YES → ToolNode → LLM
 └── NO  → END
```

### 2. Deterministic workflows

For example:

```text
Get customer
    ↓
Get orders
    ↓
Analyze orders
    ↓
Generate response
```

You don't need a fully autonomous agent deciding every step.

### 3. Human approval

For sensitive operations:

```text
LLM
 ↓
"Transfer ₹50,000"
 ↓
Human approval
 ↓
Execute tool
```

### 4. Custom authorization

```text
LLM requests delete_customer
        ↓
Authorization check
        ↓
Allowed?
   ├── YES → Execute
   └── NO  → Reject
```

### 5. Custom retry/error handling

```text
Tool call
   ↓
Failure
   ↓
Custom retry policy
   ↓
Retry / alternate tool / notify user
```

### 6. Dynamic tool availability

Different workflow stages can expose different tools:

```text
Customer lookup node
    ↓
Only customer tools available

Payment node
    ↓
Only payment tools available
```

---

# 26. `.bind_tools()` + Tool Schema

These pieces fit together directly:

```python
class SearchCustomerInput(BaseModel):
    customer_id: str


@tool(args_schema=SearchCustomerInput)
def search_customer(customer_id: str):
    ...
```

Then:

```python
model_with_tools = model.bind_tools([
    search_customer
])
```

The flow is:

```text
SearchCustomerInput
        ↓
Defines tool argument contract
        ↓
@tool
        ↓
Defines actual action
        ↓
bind_tools()
        ↓
Makes tool available to model
        ↓
LLM can generate tool call
```

So:

> **`args_schema` describes the tool. `.bind_tools()` exposes the tool to the model.**

---

# 27. The Four Concepts Together

At this point there are four related concepts:

| Mechanism | Purpose |
|---|---|
| `@tool(args_schema=...)` | Define the tool and its input contract |
| `.bind_tools()` | Give tools to a model so it can generate tool calls |
| `with_structured_output()` | Make a model return structured data |
| `ToolStrategy()` | Make an agent return structured final data |

A useful mental model:

```text
                    @tool
                      │
                      ↓
              Define tool + schema
                      │
                      ↓
                 bind_tools()
                      │
                      ↓
                     LLM
                      │
               generates call
                      │
                      ↓
             Tool execution
           (YOU / ToolNode / Agent)
                      │
                      ↓
                 Tool result
                      │
                      ↓
                     LLM
                      │
                      ↓
             Final structured result
                 /            \
                /              \
with_structured_output      ToolStrategy
       (model)                 (agent)
```

---

# 28. `.bind_tools()` vs `ToolStrategy()`

These are especially easy to confuse.

### `.bind_tools()`

```python
model_with_tools = model.bind_tools(tools)
```

Means:

> **"Give this model access to these tools so it can request tool calls."**

It concerns **tool availability to the model**.

### `ToolStrategy()`

```python
ToolStrategy(MyResponse)
```

Means:

> **"I want this agent to ultimately return a structured response matching `MyResponse`."**

It concerns the **agent's final response contract**.

So:

```text
.bind_tools()
    ↓
Model can REQUEST tools

ToolStrategy()
    ↓
Agent has a structured FINAL RESPONSE
```

---

# 29. `.bind_tools()` vs `with_structured_output()`

Another useful comparison:

### `.bind_tools()`

```python
model.bind_tools(tools)
```

The model can produce:

```text
tool_call(...)
```

It is requesting that an action be performed.

### `with_structured_output()`

```python
model.with_structured_output(MySchema)
```

The model produces structured information:

```text
MySchema(...)
```

So:

```text
bind_tools()
    ↓
"Let me REQUEST AN ACTION."

with_structured_output()
    ↓
"Let me RETURN STRUCTURED DATA."
```

---

# 30. Complete Example

Consider a customer support system:

```python
@tool(args_schema=SearchCustomerInput)
def search_customer(customer_id: str):
    ...


@tool(args_schema=CreateTicketInput)
def create_ticket(customer_id: str, issue: str):
    ...
```

Bind them:

```python
model_with_tools = model.bind_tools([
    search_customer,
    create_ticket,
])
```

Now the model can generate:

```python
AIMessage(
    tool_calls=[
        {
            "name": "search_customer",
            "args": {"customer_id": "123"}
        }
    ]
)
```

Your LangGraph `ToolNode` or application code executes the tool.

The result goes back to the model.

Eventually the flow can be:

```text
User
 ↓
LLM
 ↓
search_customer
 ↓
Tool result
 ↓
LLM
 ↓
create_ticket
 ↓
Tool result
 ↓
LLM
 ↓
Final response
```

---

# 31. Complete Mental Model

```text
                         YOUR SYSTEM
                              │
                              ↓
                         ┌─────────┐
                         │  Agent  │
                         └────┬────┘
                              │
                              ↓
                    ┌──────────────────┐
                    │       LLM        │
                    │                  │
                    │  bind_tools()    │
                    └────────┬─────────┘
                             │
                     Can request tools
                             │
                ┌────────────┴────────────┐
                ↓                         ↓
           tool_call                  no tool_call
                │                         │
                ↓                         ↓
         ToolNode / Your code          Final response
                │
                ↓
          Execute actual tool
                │
                ↓
           Tool result
                │
                └─────────────→ LLM
                                  │
                                  ↓
                           Final response
```

The critical separation is:

```text
@tool
   = DEFINE

bind_tools()
   = EXPOSE

LLM tool_call
   = REQUEST

ToolNode / application
   = EXECUTE

ToolStrategy
   = STRUCTURE AGENT FINAL RESPONSE
```

---

# 32. Final Cheat Sheet

```text
@tool(args_schema=Schema)
        ↓
"What action exists and what inputs does it need?"

.bind_tools([tools])
        ↓
"What tools can this model request?"

model.invoke(...)
        ↓
"Which tool, if any, does the model want to call?"

ToolNode / application code
        ↓
"Actually execute the requested tool."

model.with_structured_output(Schema)
        ↓
"What structured data should this model call return?"

ToolStrategy(Schema)
        ↓
"What structured response should this agent ultimately return?"
```

## One-line rule

> **`@tool` = DEFINE the action**  
> **`.bind_tools()` = EXPOSE the action to the model**  
> **LLM tool call = REQUEST the action**  
> **ToolNode / application = EXECUTE the action**  
> **`with_structured_output()` = STRUCTURE a model response**  
> **`ToolStrategy()` = STRUCTURE an agent's final response**
