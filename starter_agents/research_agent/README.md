# 🔎 Research Agent

An AI-powered research agent built with **Google Gemini, Agno, WebSearchTools, and Streamlit**.

The goal of this project is to learn how to build and ship an agent that can understand a research question, decide when web search is useful, gather information through tools, and synthesize the results into a research response.

---

## 🚀 Current Architecture

```text
                         User
                          │
                          ▼
                    Streamlit UI
                          │
                          │ Research topic
                          ▼
                    Agno Agent
                          │
                          ▼
                     Gemini LLM
                          │
                    Tool decision
                          │
                          ▼
                  WebSearchTools
                          │
                          ▼
                    Web Search
                          │
                          ▼
                     Gemini
                          │
                          ▼
                  Research Report
                          │
                          ▼
                    Streamlit UI
```

---

## 🧠 What This Project Demonstrates

This project is being built incrementally to understand the engineering behind AI agents.

### 1. LLM

Google Gemini is used as the reasoning and generation model.

### 2. Tool Calling

The model can decide when it needs an external capability such as web search.

Conceptually:

```text
User Question
     ↓
Gemini
     ↓
Should I use a tool?
     ↓
Web Search
     ↓
Search Results
     ↓
Gemini
     ↓
Final Answer
```

### 3. Agent Orchestration

Agno manages the interaction between the model and its tools.

Instead of manually implementing:

```text
function_call
      ↓
execute function
      ↓
function_result
      ↓
call model again
```

Agno provides the agent abstraction that handles this orchestration.

### 4. Web Research

`WebSearchTools` provides the agent with web-search capabilities.

The agent can perform multiple searches when additional information is needed.

### 5. Streamlit Interface

Streamlit provides a simple UI where users can:

* Enter their Gemini API key
* Submit the API key
* Enter a research question
* Start the research process
* View the generated research report

---

## 📁 Project Structure

```text
agent-lab/
│
└── starter_agents/
    │
    └── research_agent/
        │
        ├── app.py
        ├── tools.py
        ├── streamlit_app.py
        └── README.md
```

### `app.py`

Responsible for creating the Agno Research Agent.

```text
Gemini
  +
WebSearchTools
  +
Research instructions
  ↓
Agno Agent
```

### `tools.py`

Contains custom tools that may be added to the Research Agent as the project evolves.

### `streamlit_app.py`

Contains the user interface and handles:

* API key input
* API key session state
* Research topic input
* Agent execution
* Research output rendering

---

## 🛠️ Tech Stack

| Technology     | Purpose                           |
| -------------- | --------------------------------- |
| Python         | Application development           |
| Google Gemini  | LLM / reasoning                   |
| Agno           | Agent framework and orchestration |
| WebSearchTools | Web research                      |
| Streamlit      | User interface                    |
| Pydantic       | Planned structured output layer   |

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd agent-lab
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -U agno google-genai streamlit
```

### 5. Start the application

From the project root:

```bash
streamlit run starter_agents/research_agent/streamlit_app.py
```

---

## 🔑 API Key

The current Streamlit interface follows a **Bring Your Own Key (BYOK)** approach.

The user enters their Gemini API key through the sidebar:

```text
┌─────────────────────────┐
│ Configuration           │
│                         │
│ Gemini API Key          │
│ [••••••••••••••••••]    │
│                         │
│       [ Submit ]        │
└─────────────────────────┘
```

After submitting the key, the research interface becomes available.

The API key should **never be committed to Git**.

---

## 🔬 Example

Input:

```text
Research the impact of climate change on polar bear populations.
```

The agent can decide to perform searches such as:

```text
impact of climate change on polar bear populations

IUCN polar bear subpopulations climate change

polar bear fasting climate change research
```

The search results are then provided to Gemini for synthesis.

---

## 🧩 Agent Flow

The underlying agent loop can be understood as:

```text
                  ┌───────────────┐
                  │     User      │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │    Gemini     │
                  └───────┬───────┘
                          │
                    Tool required?
                     /           \
                   Yes            No
                   │               │
                   ▼               ▼
             WebSearchTools     Final answer
                   │
                   ▼
             Search results
                   │
                   ▼
                 Gemini
                   │
                   ▼
             More research?
                /      \
              Yes       No
               │         │
               ▼         ▼
             Search    Final answer
               │
               └──────────► Gemini
```

This loop is the foundation of the Research Agent.

---

## 🗺️ Roadmap

### Phase 1 — Agent Fundamentals

* [x] Gemini integration
* [x] Understand function/tool calling
* [x] Build a mock research tool
* [x] Execute tool calls manually
* [x] Return tool results to Gemini
* [x] Move to Agno
* [x] Integrate web search
* [x] Build Streamlit interface

### Phase 2 — Better Research Output

* [ ] Define `ResearchReport` schema
* [ ] Add structured outputs
* [ ] Separate findings from evidence
* [ ] Add source metadata
* [ ] Improve citations
* [ ] Improve report rendering

### Phase 3 — Better Research Capabilities

* [ ] Web-page reading
* [ ] Web scraping/crawling
* [ ] Academic paper search
* [ ] PDF research
* [ ] Multiple specialized research tools

### Phase 4 — Agentic Research

* [ ] Multi-step research planning
* [ ] Iterative searching
* [ ] Evidence evaluation
* [ ] Source comparison
* [ ] Parallel research
* [ ] Research quality checks

### Phase 5 — Production

* [ ] Authentication
* [ ] Secure API-key handling
* [ ] Observability
* [ ] Agent evaluation
* [ ] Error handling
* [ ] Cost/latency tracking
* [ ] Deployment

---

## 🎯 Project Goal

The goal is **not simply to create a chatbot that searches the web**.

The goal is to understand and build the complete architecture behind a research agent:

```text
                Research Question
                       │
                       ▼
                     Agent
                       │
                 ┌─────┴─────┐
                 ▼           ▼
              Planning     Tools
                             │
                    ┌────────┼────────┐
                    ▼        ▼        ▼
                  Search    Read    Analyze
                    │        │        │
                    └────────┼────────┘
                             ▼
                          Evidence
                             │
                             ▼
                           Gemini
                             │
                             ▼
                      Research Report
```

The project will progressively evolve from a simple **LLM + web search** agent into a more capable, multi-step research system.

---

## 📚 Learning Philosophy

This project is being developed incrementally.

The approach is:

```text
Understand the primitive
        ↓
Build it manually
        ↓
Use an agent framework
        ↓
Understand what the framework abstracts
        ↓
Add real tools
        ↓
Add structure
        ↓
Add reliability
        ↓
Ship
```

The objective is to understand **what happens underneath the framework**, rather than simply learning framework syntax.
