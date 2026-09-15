
````markdown
# 🤖 Kubernetes SRE Agent – A Simple Agentic AI Approach

## 📌 Overview

This project demonstrates a simple and practical implementation of **Agentic AI for Kubernetes troubleshooting**.

Instead of using an LLM only as a chatbot, this project gives the LLM access to real Kubernetes tools.

The agent can understand a natural-language question, decide which tool it needs, retrieve information from Kubernetes, analyze the results, and provide a troubleshooting response.

The current implementation is intentionally **read-only**.

The agent does not modify, restart, or delete Kubernetes resources.

---

## 🎯 Project Objective

The objective is to understand the fundamental building blocks of an Agentic AI system using a real DevOps use case.

The project demonstrates:

- LLM Tool Calling
- LangGraph
- Python Kubernetes Client
- Kubernetes API interaction
- Kubernetes RBAC
- Multi-step agentic reasoning
- Kubernetes troubleshooting
- Read-only SRE automation

---

# 🏗️ Architecture

```text
                    User
                     |
                     v
              +--------------+
              |   LangGraph  |
              |    Agent     |
              +------+-------+
                     |
                     v
                +--------+
                |  LLM   |
                +----+---+
                     |
              Tool Selection
                     |
                     v
              +-------------+
              |  ToolNode   |
              +------+------+
                     |
                     v
        Python Kubernetes Client
                     |
                     v
          Kubernetes API Server
                     |
                     v
               Kubernetes
                     |
                     v
              Tool Result
                     |
                     v
                   LLM
                     |
             +-------+-------+
             |               |
        Another Tool     Final Answer
````

The agent follows an iterative loop:

```text
Agent
  ↓
Tool
  ↓
Tool Result
  ↓
Agent
  ↓
Another Tool
  ↓
Tool Result
  ↓
Final Answer
```

---

# 🧠 Why is this Agentic AI?

A traditional LLM interaction looks like:

```text
User
  ↓
LLM
  ↓
Answer
```

The LLM simply generates an answer based on the information available in the conversation.

In this project, the LLM can decide that it needs information from Kubernetes.

For example:

```text
User:
Why are my demo-api pods not Ready?
```

The agent can reason that it needs Kubernetes information and select appropriate tools.

The flow becomes:

```text
User Question
      ↓
      LLM
      ↓
Tool Selection
      ↓
Kubernetes Tool
      ↓
Real Kubernetes Data
      ↓
      LLM
      ↓
Further Investigation
      ↓
Root Cause
      ↓
Final Response
```

The important concept is:

> The LLM decides which tool should be used, while the application executes the tool.

---

# 🛠️ Tools Available

The current agent has four Kubernetes tools.

## 1. Get Pods

```text
get_pods()
```

Lists pods in a Kubernetes namespace.

It provides:

* Pod name
* Pod status
* Container readiness

Example:

```text
Pod: demo-api-xxxxx
Status: Running
Ready: 0/1
```

---

## 2. Get Pod Logs

```text
get_pod_logs()
```

Retrieves logs from a Kubernetes pod.

This can help identify:

* Application errors
* Exceptions
* Startup problems
* Runtime failures

---

## 3. Describe Pod

```text
describe_pod()
```

Retrieves detailed pod information.

The tool checks:

* Pod conditions
* Container status
* Restart count
* Waiting state
* Terminated state
* Container image
* Readiness probe
* Liveness probe

---

## 4. Get Kubernetes Events

```text
get_events()
```

Retrieves Kubernetes events from a namespace.

This can help identify:

* Failed readiness probes
* Scheduling problems
* Container failures
* Lifecycle issues
* Other Kubernetes warnings

---

# 🔐 Kubernetes RBAC

The agent uses a dedicated Kubernetes ServiceAccount:

```text
k8s-agent
```

The ServiceAccount is bound to a namespace-scoped read-only Role.

Current permissions:

```yaml
verbs:
  - get
  - list
  - watch
```

Resources:

```text
pods
pods/log
events
```

The agent does NOT have permissions to:

```text
create
update
patch
delete
```

Kubernetes resources.

This follows the **principle of least privilege**.

---

# 🧪 Demo Scenario

The Kubernetes deployment intentionally contains a broken readiness probe.

```yaml
readinessProbe:
  httpGet:
    path: /wrong-path
    port: 80
```

The nginx container itself is running.

However, nginx does not serve:

```text
/wrong-path
```

Therefore the Kubernetes pod can be:

```text
STATUS: Running
READY: 0/1
```

This demonstrates an important Kubernetes concept:

> **Running does not necessarily mean Ready.**

---

# 📂 Kubernetes Resources

All Kubernetes resources are included in a single YAML file:

```text
k8s-agent-demo.yaml
```

The file creates:

```text
Namespace
ServiceAccount
Role
RoleBinding
Deployment
Service
```

Deploy everything using:

```bash
kubectl apply -f k8s-agent-demo.yaml
```

Check the pods:

```bash
kubectl get pods -n ai-devops
```

Expected output:

```text
NAME                         READY   STATUS
demo-api-xxxxxxxxxx         0/1     Running
demo-api-yyyyyyyyyy         0/1     Running
```

---

# 📁 Project Structure

```text
k8s-tool-agent/
│
├── agent.py
├── requirements.txt
├── Dockerfile
└── k8s-agent-demo.yaml
```

---

# ⚙️ Requirements

Recommended:

```text
Python 3.10+
Kubernetes cluster
kubectl
OpenAI API access
```

Python dependencies:

```text
langchain
langchain-openai
langgraph
kubernetes
typing-extensions
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key"
```

---

# ☸️ Kubernetes Connection

The Python application supports both local and in-cluster Kubernetes execution.

When running outside Kubernetes, it uses:

```python
config.load_kube_config()
```

This loads the Kubernetes configuration from kubeconfig.

When running inside Kubernetes, it can use:

```python
config.load_incluster_config()
```

This allows the application to authenticate using the Kubernetes ServiceAccount attached to its Pod.

---

# ▶️ Run the Agent

Deploy the Kubernetes resources:

```bash
kubectl apply -f k8s-agent-demo.yaml
```

Check the workload:

```bash
kubectl get pods -n ai-devops
```

Start the agent:

```bash
python agent.py
```

The application provides an interactive prompt:

```text
======================================================================
KUBERNETES SRE AGENT
======================================================================
Ask me anything about your Kubernetes cluster.
Type 'exit' to quit.

You:
```

---

# 💬 Example Questions

The agent accepts natural-language questions.

### Basic Kubernetes Questions

```text
Is there any pod running in default namespace?
```

```text
Show me all pods in ai-devops.
```

```text
Which pods are not ready?
```

### Troubleshooting Questions

```text
Why are the demo-api pods not ready?
```

```text
Investigate demo-api and determine the root cause.
```

```text
Check the Kubernetes events for demo-api.
```

```text
Check the logs of the demo-api pods.
```

### SRE Investigation

```text
Act as a Kubernetes SRE.

Investigate the demo-api workload in the ai-devops namespace.

Determine why the pods are not Ready.

Collect supporting evidence from Kubernetes,
identify the root cause, and recommend a fix.

Do not make any changes.
```

---

# 🔄 Example Agent Workflow

For the question:

```text
Why are the demo-api pods not ready?
```

the agent may perform:

```text
User
 |
 v
LLM
 |
 +----> get_pods
 |          |
 |          v
 |      Pod = 0/1 Ready
 |
 v
LLM
 |
 +----> describe_pod
 |          |
 |          v
 |      Readiness Probe
 |
 v
LLM
 |
 +----> get_events
 |          |
 |          v
 |      Probe failure / HTTP 404
 |
 v
LLM
 |
 v
Root Cause Analysis
 |
 v
Final Answer
```

The agent is therefore not following one hardcoded troubleshooting command.

It can select tools based on the question and the information already collected.

---

# 🧩 LangGraph Concepts Used

## `@tool`

Python functions are exposed as tools:

```python
@tool
def get_pods(namespace: str = "default"):
    ...
```

The LLM can request this tool when Kubernetes pod information is required.

---

## `bind_tools()`

The tools are bound to the LLM:

```python
llm_with_tools = llm.bind_tools(tools)
```

This allows the LLM to generate tool calls.

---

## `ToolNode`

LangGraph's `ToolNode` executes the tools:

```python
ToolNode(tools)
```

---

## `add_messages`

The state contains:

```python
messages: Annotated[list, add_messages]
```

`add_messages` tells LangGraph how to merge new messages into the existing message state.

It is important for maintaining the correct sequence:

```text
Human Message
      ↓
AI Tool Call
      ↓
Tool Result
      ↓
AI Response
```

### Important

`add_messages` itself is **not persistent memory**.

Persistent conversational memory will be added using a LangGraph checkpointer and `thread_id`.

---

# 🧠 Memory – Next Enhancement

The current version does not yet implement persistent conversational memory.

The next step is to add:

```text
MemorySaver
+
thread_id
```

This will allow multi-turn conversations such as:

```text
You:
Which pods are unhealthy?

Agent:
demo-api is not Ready.

You:
Why?

Agent:
The readiness probe is failing.

You:
How can I fix it?

Agent:
Change the readiness probe path...
```

This introduces the concept of **short-term conversational memory**.

---

# 🚧 Current Limitations

This project is intentionally a basic Agentic AI implementation.

It currently does not include:

* Persistent conversational memory
* Long-term memory
* RAG
* Kubernetes runbook retrieval
* MCP
* Multi-agent architecture
* Automatic remediation
* Human approval workflow
* Agent evaluation
* Production observability
* Persistent checkpoint storage

These can be added incrementally.

---

# 🚀 Future Evolution

The basic agent can evolve into a production-oriented AI SRE platform.

```text
LLM + Tool Calling
        ↓
LangGraph
        ↓
Conversational Memory
        ↓
RAG + Kubernetes Runbooks
        ↓
MCP
        ↓
Multi-Agent Architecture
        ↓
Human Approval
        ↓
Controlled Remediation
        ↓
Verification
        ↓
Production AI SRE Platform
```

A safer remediation workflow would be:

```text
Incident
   ↓
Investigate
   ↓
Collect Evidence
   ↓
Root Cause
   ↓
Propose Fix
   ↓
Human Approval
   ↓
Execute Change
   ↓
Verify
```

---

# 🎯 Key Learning

The main objective of this project is to demonstrate that **Agentic AI does not need to start with a complicated architecture**.

A useful agent can begin with:

```text
LLM
+
Tools
+
LangGraph
+
Decision Loop
```

In this project, those tools interact with Kubernetes.

The LLM can decide:

> "I need information from Kubernetes before I can answer this question."

It then selects the appropriate tool, receives the result, and continues the investigation.

This simple pattern provides the foundation for building more advanced **AI-powered DevOps and SRE systems**.

---

# 👨‍💻 Learning Journey

This project is part of a broader learning path:

```text
LangChain
   ↓
LangGraph
   ↓
LLM Fundamentals
   ↓
RAG
   ↓
Tool Calling
   ↓
Kubernetes SRE Agent  ← Current Project
   ↓
Memory
   ↓
MCP
   ↓
Multi-Agent Systems
   ↓
Evaluation
   ↓
LLMOps
   ↓
Production Agentic AI
```

---

## ⭐ Final Note

This project is intentionally simple.

The goal is to understand the **fundamentals of Agentic AI through a real DevOps use case**, rather than hiding the concepts behind a large framework.

From here, the same architecture can be extended toward:

**AI-powered Kubernetes troubleshooting → AI SRE → Autonomous DevOps with controlled human approval.**

```
```
