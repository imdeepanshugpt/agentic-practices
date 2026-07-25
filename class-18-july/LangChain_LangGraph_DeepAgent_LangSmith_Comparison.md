# LangChain vs LangGraph vs DeepAgent vs LangSmith

| Tool | What it is | Main Purpose |
|--------|------------|--------------|
| LangChain | Framework | Build LLM applications with tools, RAG, memory, prompts |
| LangGraph | Agent orchestration framework | Build stateful multi-step agents and workflows |
| DeepAgent | Agent architecture/template | Create autonomous agents that can plan and execute complex tasks |
| LangSmith | Observability platform | Debug, trace, evaluate, and monitor LLM applications |

## LangChain

Think of it as the foundation for LLM applications.

### Features
- Prompt templates
- LLM wrappers
- RAG pipelines
- Tool calling
- Memory
- Chains

### Use Cases
- Chatbots
- PDF Q&A
- Customer support assistants
- SQL database assistants

### When to Use
Use LangChain when:
- You need simple workflows
- Sequential steps are enough
- No complex state management is required

---

## LangGraph

LangGraph is built on top of LangChain and is designed for stateful agent workflows.

### Features
- State management
- Checkpointing
- Human-in-the-loop approvals
- Loops and branching
- Multi-agent systems

### Use Cases
- Research agents
- Coding agents
- Customer support workflows
- Approval pipelines
- Multi-step reasoning systems

### Example Flow
Question → Planner → Search → Analyze → Generate Report

---

## DeepAgent

DeepAgent is a pre-built agent architecture created by the LangChain team.

### Features
- Planning
- Tool usage
- Reflection
- Re-planning
- Long-running task execution

### Use Cases
- Deep research assistants
- Autonomous coding agents
- Competitive analysis
- Business research

### Key Idea
LangGraph lets you build the engine yourself.
DeepAgent provides a ready-made engine built using LangGraph.

---

## LangSmith

LangSmith is an observability and evaluation platform.

### Features
- Execution traces
- Prompt debugging
- Token usage tracking
- Latency monitoring
- Automated evaluations
- Production monitoring

### Use Cases
- Debugging agent failures
- Monitoring production systems
- Cost optimization
- Prompt evaluation

---

## How They Work Together

User
→ LangGraph
→ Tools

LangChain provides the building blocks.
LangGraph orchestrates workflows.
DeepAgent provides a ready-made autonomous agent.
LangSmith monitors and debugs everything.

---

## Interview One-Liners

- LangChain → Building blocks for LLM applications.
- LangGraph → Workflow engine for stateful agents.
- DeepAgent → Pre-built autonomous agent architecture.
- LangSmith → Monitoring, debugging, and evaluation platform.

## Recommended Modern Stack

LangChain + LangGraph + LangSmith

Use DeepAgent when you want autonomous research or coding agents instead of designing the workflow yourself.
