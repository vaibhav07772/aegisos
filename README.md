# 🛡️ AegisOS — AI Operating System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge\&logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2-FF6B6B?style=for-the-badge)
![Groq](https://img.shields.io/badge/Groq-Llama_3-F55036?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge\&logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge\&logo=docker)
![Streamlit](https://img.shields.io/badge/Streamlit-1.39-FF4B4B?style=for-the-badge)

**An intent-driven AI orchestration layer that analyzes requests, selects an appropriate LLM, coordinates multi-agent execution, manages tool access, and produces transparent decision logs.**

[🚀 Quick Start](#-quick-start) ·
[🏗️ Architecture](#️-architecture) ·
[📡 API](#-api-endpoints) ·
[📊 Decision Logs](#-decision-logs) ·
[🔮 Roadmap](#-roadmap)

</div>

---

## 📌 What is AegisOS?

AegisOS is an **AI orchestration layer built on top of multiple LLM capabilities**.

Instead of sending every request directly to the same model, AegisOS analyzes the request and determines:

* 🧠 **What type of task is being requested**
* 📊 **How complex the task is**
* ⚠️ **What risk level is associated with the request**
* 🎯 **Which model tier is appropriate**
* 🔧 **Which tools are required**
* 🤖 **Which agents should execute the task**
* 🔄 **Whether verification or retry is required**
* 📈 **How the request affects token capacity**
* 💰 **What the projected cost would be under an alternative pricing model**

Every execution produces a **structured decision log**, making the orchestration process observable instead of treating the LLM as a black box.

---

# 🎯 Why AegisOS?

A typical LLM application looks like:

```text
User
  ↓
LLM
  ↓
Response
```

AegisOS introduces an engineering layer around the model:

```text
User Request
     ↓
Intent Analysis
     ↓
Decision Engine
     ↓
Model Selection
     ↓
Tool Selection
     ↓
Multi-Agent Execution
     ↓
Verification
     ↓
Retry / Correction
     ↓
Final Response
     +
Decision Log
```

This makes the system useful for exploring **AI routing, agent orchestration, tool execution, verification, rate-limit management, and AI observability** in one architecture.

---

# ✨ Key Features

| Feature                          | Description                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------------------- |
| 🧠 **Intent Analysis**           | Classifies task type, complexity, risk, and required tools                                  |
| 🎯 **Complexity-Aware Routing**  | Routes simpler tasks toward smaller models and complex tasks toward larger reasoning models |
| 📊 **Rate-Limit Management**     | Tracks estimated token usage and checks model capacity                                      |
| 🤖 **Multi-Agent Orchestration** | Planner → Executor → Verifier workflow using LangGraph                                      |
| 🔧 **Tool Execution**            | Sandboxed filesystem operations and GitHub API tools                                        |
| ✅ **Verification Loop**          | Verifier evaluates execution results and can trigger retries                                |
| 🔄 **Fallback Models**           | Provides an alternative model when the selected path cannot continue                        |
| 📋 **Decision Logs**             | Records intent, routing, token impact, verification, and execution metadata                 |
| 🎨 **Streamlit Dashboard**       | Visual interface for interacting with the orchestration system                              |
| ⚡ **FastAPI Backend**            | REST API for programmatic access                                                            |
| 🐳 **Docker Compose**            | Runs API and UI as separate services                                                        |

---

# 🏗️ Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                         USER QUERY                           │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    INTENT ANALYZER                            │
│                                                              │
│  • Task Type                                                 │
│  • Complexity                                                │
│  • Risk Level                                                │
│  • Required Tools                                            │
│  • Estimated Tokens                                          │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     DECISION ENGINE                          │
│                                                              │
│  • Model Selection                                           │
│  • Rate-Limit Check                                          │
│  • Fallback Identification                                   │
│  • Cost Projection                                           │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    LANGGRAPH WORKFLOW                         │
│                                                              │
│        ┌──────────┐      ┌──────────┐      ┌──────────┐     │
│        │ PLANNER  │ ───► │ EXECUTOR │ ───► │ VERIFIER │     │
│        └──────────┘      └──────────┘      └──────────┘     │
│                                                │             │
│                                                │             │
│                                      ┌─────────▼─────────┐   │
│                                      │   Retry Required? │   │
│                                      └─────────┬─────────┘   │
│                                                │             │
│                                      Yes ──────┘             │
└───────────────────────────────────────────────┬──────────────┘
                                                │
                                                ▼
┌──────────────────────────────────────────────────────────────┐
│                FINAL ANSWER + DECISION LOG                   │
└──────────────────────────────────────────────────────────────┘
```

---

# 🧠 Intent Analysis

The intent analyzer converts a natural-language request into structured information.

Example:

```json
{
  "task_type": "code_generation",
  "complexity": "high",
  "risk_level": "medium",
  "tools_needed": [
    "filesystem",
    "github"
  ],
  "estimated_tokens": 2000
}
```

This structured representation becomes the input to the decision engine.

---

# 🎯 Complexity-Aware Model Routing

AegisOS maintains multiple model tiers.

```text
                 USER REQUEST
                       │
                       ▼
                Intent Analysis
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
           LOW      MEDIUM      HIGH
             │         │         │
             ▼         ▼         ▼
          Small     Medium      Large
          Model     Model       Model
```

The routing decision considers factors such as:

* Task complexity
* Required tools
* Estimated token usage
* Model availability
* Rate-limit capacity
* Fallback options

The goal is to avoid treating every task as if it requires the largest available model.

---

# 🤖 Multi-Agent System

AegisOS uses **LangGraph** to coordinate multiple execution stages.

### 1. Planner

Breaks the request into executable steps.

```text
User Request
     ↓
Planner
     ↓
Execution Plan
```

### 2. Executor

Executes the planned steps and invokes available tools when required.

### 3. Verifier

Checks whether the execution result satisfies the expected outcome.

```text
Planner
   ↓
Executor
   ↓
Verifier
   │
   ├── Approved ──► Final Response
   │
   └── Retry ─────► Executor
```

The current workflow allows up to **2 retries** based on the configured execution path.

---

# 🔧 Tool System

AegisOS currently provides tools for filesystem and GitHub operations.

| Tool              |      Risk | Description                         |
| ----------------- | --------: | ----------------------------------- |
| `read_file`       |    🟢 Low | Read a sandboxed file               |
| `write_file`      | 🟡 Medium | Write a sandboxed file              |
| `list_files`      |    🟢 Low | List available files                |
| `delete_file`     |   🔴 High | Delete a sandboxed file             |
| `get_repo_info`   |    🟢 Low | Retrieve GitHub repository metadata |
| `list_repo_files` |    🟢 Low | List repository files               |
| `read_repo_file`  |    🟢 Low | Read a repository file              |
| `list_issues`     |    🟢 Low | Retrieve GitHub issues              |

---

# 🔐 Tool Security

Filesystem operations are intentionally restricted.

### Sandbox

```text
./sandbox/
```

Filesystem operations are restricted to the sandbox directory.

### Extension Filtering

Supported file types can be restricted through an extension allowlist such as:

```text
.py
.txt
.md
.json
```

### File Size Limit

Maximum configured file size:

```text
1 MB
```

### Path Traversal Protection

Paths attempting to escape the sandbox are rejected.

```text
./sandbox/project/file.py
        ✅

./sandbox/../../secret.txt
        ❌
```

These controls reduce the risk associated with LLM-generated tool calls.

---

# 📊 Rate-Limit Management

AegisOS tracks estimated token usage before executing model requests.

Example:

```text
Estimated Tokens: 2,000
Model TPM Limit:  8,000
Quota Impact:     25%
```

This allows the decision layer to consider model capacity before execution instead of relying only on reactive API failures.

---

# 💰 Cost Projection

The decision log can also include a **projected cost under an alternative pricing model**.

Example:

```text
Projected GPT-4 Cost: $0.0100
Actual Groq Cost:     $0.0000
```

The projection is intended for comparison and observability; it is not a billing statement.

---

# 🧠 Groq Models

The current configuration supports model entries such as:

| Model                          | Tier   | TPM Limit | Intended Use           |
| ------------------------------ | ------ | --------: | ---------------------- |
| `openai/gpt-oss-20b`           | Small  |     8,000 | Fast/simple tasks      |
| `qwen/qwen3.6-27b`             | Medium |     8,000 | Balanced reasoning     |
| `meta-llama/llama-4-scout-17b` | Medium |    30,000 | Long-context workloads |
| `openai/gpt-oss-120b`          | Large  |     8,000 | Complex reasoning      |
| `moonshotai/kimi-k2-instruct`  | Large  |    10,000 | Large-context tasks    |

> Model availability and provider limits can change over time. Treat the project's model configuration as the source of truth when running the system.

---

# 📡 API Endpoints

| Method | Endpoint  | Description                                    |
| ------ | --------- | ---------------------------------------------- |
| `GET`  | `/`       | Service information                            |
| `GET`  | `/health` | Health check                                   |
| `GET`  | `/models` | List configured models                         |
| `GET`  | `/tools`  | List available tools                           |
| `GET`  | `/usage`  | Rate-limit statistics                          |
| `POST` | `/run`    | Execute the complete AI orchestration pipeline |

---

# 🚀 Example API Request

```bash
curl -X POST "http://localhost:8000/run" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the capital of France?",
    "max_retries": 1,
    "max_steps": 5
  }'
```

---

# 📦 Example Response

```json
{
  "query": "What is the capital of France?",
  "decision_id": "a47a46e8",

  "intent": {
    "task_type": "simple_qa",
    "complexity": "low",
    "risk_level": "low",
    "tools_needed": [],
    "estimated_tokens": 10
  },

  "decision": {
    "selected_model_id": "groq-gpt-oss-20b",
    "selected_model_name": "openai/gpt-oss-20b",
    "selected_model_tier": "small",
    "selection_reason": "low complexity -> small model",
    "quota_impact_pct": 0.125,
    "projected_cost_usd": 0.00005
  },

  "verification_status": "approved",
  "retry_count": 0,

  "final_answer": "The capital of France is Paris.",
  "success": true,
  "elapsed_seconds": 5.31
}
```

---

# 📋 Decision Logs

One of AegisOS's core features is **transparent orchestration logging**.

Example:

```text
════════════════════════════════════════════════════════

DECISION LOG

INPUT
  Query: My GitHub project is not production-ready
  ID:    1e5b0293
  Time:  2026-09-26T14:12:14

────────────────────────────────────────────────────────

INTENT ANALYSIS
  Task Type:   code_generation
  Complexity:  high
  Risk Level:  medium
  Tools:       filesystem, github

────────────────────────────────────────────────────────

MODEL SELECTION
  Selected:    groq-gpt-oss-120b
  Fallback:    groq-qwen-27b
  Reason:      high complexity → large model | tool use required

────────────────────────────────────────────────────────

RATE LIMIT
  Estimated Tokens: 2,000 / 8,000 TPM
  Quota Impact:     25.0%

────────────────────────────────────────────────────────

COST PROJECTION
  Alternative Model: $0.0100
  Groq:              $0.0000

════════════════════════════════════════════════════════
```

This provides visibility into **why** a model and execution path were selected.

---

# 🎨 Streamlit Dashboard

AegisOS also provides a Streamlit interface for interacting with the orchestration system.

The dashboard is intended to expose:

* Query execution
* Intent classification
* Model selection
* Tool selection
* Execution plan
* Verification status
* Retry information
* Rate-limit information
* Decision logs

---

# 🛠️ Tech Stack

| Layer                | Technology     | Purpose                        |
| -------------------- | -------------- | ------------------------------ |
| **Language**         | Python 3.11    | Core implementation            |
| **LLM Provider**     | Groq           | LLM inference                  |
| **Orchestration**    | LangGraph      | Stateful multi-agent workflow  |
| **API**              | FastAPI        | REST service                   |
| **Validation**       | Pydantic V2    | Structured schemas             |
| **UI**               | Streamlit      | Interactive dashboard          |
| **Tools**            | Custom Tools   | Filesystem + GitHub operations |
| **CLI**              | Rich           | Terminal interface             |
| **Containerization** | Docker         | Packaging                      |
| **Deployment**       | Docker Compose | Multi-service orchestration    |

---

# 📁 Project Structure

```text
aegisos/
│
├── src/
│   │
│   ├── core/
│   │   ├── model_registry.py
│   │   ├── intent_analyzer.py
│   │   ├── decision_engine.py
│   │   ├── decision_log.py
│   │   ├── rate_limiter.py
│   │   └── executor.py
│   │
│   ├── agents/
│   │   ├── state.py
│   │   ├── planner.py
│   │   ├── executor_agent.py
│   │   ├── verifier.py
│   │   ├── graph.py
│   │   └── tool_agent.py
│   │
│   ├── tools/
│   │   ├── base.py
│   │   ├── filesystem.py
│   │   ├── github.py
│   │   └── registry.py
│   │
│   ├── serving/
│   │   ├── app.py
│   │   └── schemas.py
│   │
│   └── utils/
│       └── llm_client.py
│
├── configs/
│   └── models.yaml
│
├── main.py
├── streamlit_app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# 🚀 Quick Start

## 1. Clone Repository

```bash
git clone https://github.com/vaibhav07772/aegisos.git
cd aegisos
```

---

## 2. Create Environment

```bash
conda create -n aegisos python=3.11 -y
conda activate aegisos
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment

Create `.env`:

```env
GROQ_API_KEY=your_groq_api_key
```

Get your API key from the Groq console.

**Never commit `.env` to GitHub.**

---

# 💻 Run with CLI

```bash
python main.py "What is the capital of France?"
```

Try a coding task:

```bash
python main.py "Write a Python function to check if a number is prime"
```

Check usage:

```bash
python main.py usage
```

---

# 🌐 Run API + UI

### Terminal 1 — FastAPI

```bash
uvicorn src.serving.app:app --host 0.0.0.0 --port 8000
```

### Terminal 2 — Streamlit

```bash
streamlit run streamlit_app.py --server.port=8501
```

Open:

```text
API:
http://localhost:8000

Swagger:
http://localhost:8000/docs

Streamlit:
http://localhost:8501
```

---

# 🐳 Docker Compose

The easiest way to run the complete system:

```bash
docker-compose up -d
```

Services:

```text
API      → http://localhost:8000
Swagger  → http://localhost:8000/docs
UI       → http://localhost:8501
```

Stop services:

```bash
docker-compose down
```

---

# 🎯 Engineering Decisions

| Decision                          | Reason                                                      |
| --------------------------------- | ----------------------------------------------------------- |
| **Groq-first architecture**       | Fast inference and simple provider integration              |
| **Complexity-based routing**      | Allows model selection to consider task requirements        |
| **LangGraph**                     | Explicit state management, conditional routing, and retries |
| **Planner → Executor → Verifier** | Separates planning, execution, and validation               |
| **Sandboxed tools**               | Limits filesystem operations                                |
| **Rate limiter**                  | Tracks capacity before model execution                      |
| **Decision logs**                 | Makes routing decisions observable                          |
| **Docker Compose**                | Provides a simple multi-service local deployment            |

---

# 🔄 End-to-End Execution Flow

```text
                    USER QUERY
                         │
                         ▼
                ┌─────────────────┐
                │ Intent Analyzer │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Decision Engine │
                └────────┬────────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
            Model      Tools      Budget
            Route      Route      Check
              │          │          │
              └──────────┼──────────┘
                         ▼
                   ┌───────────┐
                   │  Planner  │
                   └─────┬─────┘
                         ▼
                   ┌───────────┐
                   │ Executor  │
                   └─────┬─────┘
                         ▼
                   ┌───────────┐
                   │ Verifier  │
                   └─────┬─────┘
                         │
                  ┌──────┴──────┐
                  │             │
               Approved       Retry
                  │             │
                  ▼             │
            Final Answer ◄──────┘
                  +
            Decision Log
```

---

# ⚠️ Known Limitations

Current limitations include:

* **No persistent memory** — conversation state resets between calls.
* **Provider rate limits** — Groq model capacity depends on the active provider limits.
* **English-focused intent analysis** — multilingual routing is not currently a primary target.
* **Tool execution constraints** — filesystem access is intentionally sandboxed.
* **Local/Docker deployment** — the current project does not include a production cloud deployment.
* **LLM-dependent intent analysis** — classification and routing quality depend partly on the selected model.
* **Cost projection is informational** — it does not represent actual provider billing.

---

# 🔮 Roadmap

### 🧠 Intelligence

* [ ] Persistent conversational memory
* [ ] Episodic agent memory
* [ ] Improved intent classification
* [ ] Fine-tuned lightweight routing classifier

### 🔧 Tools

* [ ] Browser tool
* [ ] Sandboxed shell tool
* [ ] Python execution sandbox
* [ ] Database tools
* [ ] Additional GitHub automation

### 🌐 Model Providers

* [ ] OpenAI fallback
* [ ] Anthropic fallback
* [ ] Additional open-source model providers
* [ ] Dynamic provider selection

### 📊 Observability

* [ ] LangSmith tracing
* [ ] Agent trajectory visualization
* [ ] Token-level analytics
* [ ] Advanced cost tracking
* [ ] Evaluation framework

### ☁️ Deployment

* [ ] Web deployment
* [ ] Railway / Hugging Face deployment
* [ ] Kubernetes deployment
* [ ] Production monitoring
* [ ] Authentication and authorization

---

# 🎓 What This Project Demonstrates

AegisOS brings together several important AI engineering concepts:

```text
LLM Applications
      +
Model Routing
      +
Agentic AI
      +
LangGraph
      +
Tool Calling
      +
Rate-Limit Management
      +
Verification
      +
Retry / Recovery
      +
API Engineering
      +
Containerization
      +
Observability
```

It is particularly useful for demonstrating how an AI application can be designed as an **orchestration system rather than a single LLM call**.

---

# 💼 Interview Explanation

### What is AegisOS?

> **AegisOS is an AI orchestration layer that analyzes user intent, selects an appropriate model and tools, executes the task through a LangGraph-based multi-agent workflow, verifies the result, and generates a transparent decision log.**

### Why did you build it?

> I wanted to move beyond a simple chatbot architecture and explore how an AI system can make engineering decisions around model selection, tool usage, rate limits, multi-agent execution, verification, and retries.

### Why LangGraph?

> LangGraph provides explicit state management and conditional workflow transitions, which makes it suitable for coordinating Planner, Executor, and Verifier agents and implementing retry-based execution paths.

### Why model routing?

> Different requests have different complexity requirements. A routing layer allows the system to consider task complexity, required tools, and available model capacity before selecting a model.

### What makes it different from a normal chatbot?

```text
Normal Chatbot:

User → LLM → Response


AegisOS:

User
 ↓
Intent
 ↓
Decision
 ↓
Model + Tools
 ↓
Planner
 ↓
Executor
 ↓
Verifier
 ↓
Retry if required
 ↓
Response + Decision Log
```

---

# 📈 Learning Outcomes

This project provides practical experience with:

* LLM application architecture
* Agentic AI
* LangGraph
* Multi-agent systems
* Model routing
* Tool calling
* Structured outputs
* FastAPI
* Streamlit
* Rate-limit management
* Retry workflows
* Verification agents
* Sandboxed tool execution
* Docker
* Docker Compose
* AI observability concepts

---

# 🤝 Contributing

Contributions and ideas are welcome.

```bash
git checkout -b feature/your-feature
git commit -m "Add your feature"
git push origin feature/your-feature
```

Then open a Pull Request.

---

# 📄 License

This project is licensed under the **MIT License**.

---

# 👨‍💻 Author

**Vaibhav Singh**

AI/ML Engineer · Generative AI · Agentic AI · RAG · MLOps

* GitHub: https://github.com/vaibhav07772
* LinkedIn: https://linkedin.com/in/vaibhav-singh-9a9b9434a

---

<div align="center">

### 🛡️ AegisOS

**Intent → Decision → Model → Tools → Agents → Verification → Response**

Built with ❤️ using **Python · LangGraph · Groq · FastAPI · Streamlit · Docker**

⭐ Star the repository if you find it useful!

</div>
