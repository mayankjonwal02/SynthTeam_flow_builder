# SynthTeam Product Documentation

SynthTeam is a visual, low-code workflow builder for creating backend APIs, AI agents, RAG pipelines, and database-driven applications. Users design workflows by connecting nodes on a drag-and-drop canvas, then deploy them as live API endpoints with a single click.

---

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Node Reference](#node-reference)
   - [Triggers](#1-triggers)
   - [Logic](#2-logic)
   - [Flow Control](#3-flow-control)
   - [Output](#4-output)
   - [Middleware](#5-middleware)
   - [Database Nodes](#6-database-nodes)
   - [AI Config Nodes](#7-ai-config-nodes)
   - [AI Tool Nodes](#8-ai-tool-nodes)
   - [AI / LLM Execution](#9-ai--llm-execution)
   - [RAG Pipeline](#10-rag-pipeline)
   - [Agents](#11-agents)
   - [Vision and Speech](#12-vision-and-speech)
3. [Connection Handles Reference](#connection-handles-reference)
4. [Example Workflows](#example-workflows)

---

## Core Concepts

### Workflows
A workflow is a directed graph of nodes connected by edges. Each workflow starts with a **trigger** node (HTTP Entry, Webhook, Cron, or Manual) and ends with a **Response** node. When deployed, the workflow becomes a live API endpoint.

### Nodes
Each node represents a unit of work: receiving input, transforming data, calling an LLM, querying a database, or returning a response. Nodes have **configuration fields** that define their behavior.

### Edges and Handles
Nodes connect through **handles** (connection points). There are two kinds:
- **Data handles** (`input` / `output`): Pass general data between nodes in the execution pipeline. Shown on the left (target) and right (source) of nodes.
- **Typed AI handles**: Specialized connections for AI components. They pass configuration (not data flow) and are named with an `ai_` prefix: `ai_model`, `ai_tool`, `ai_memory`, `ai_structure`, `ai_embedding`, `ai_vectorstore`, `ai_subagent`.

### Deploy
Deploying a workflow compiles the graph into an execution plan (topological sort), registers a FastAPI route, and makes the endpoint live. Supports Cron scheduling, rate limiting, and execution logging.

### Field Modes
Many fields support three input modes:
- **Static**: A literal value typed directly into the field.
- **Input**: References a key from upstream data (e.g., `query` reads the `query` field from the previous node's output).
- **Expression**: A Jinja-style template expression (e.g., `input.data.items[0].name`).

---

## Node Reference

### 1. Triggers

Trigger nodes are the entry points of every workflow. They define how the workflow is invoked.

#### HTTP Entry
The primary trigger. Defines an API endpoint with method, path, and request/response schemas.
- **Fields**: Method (GET/POST/PUT/DELETE/PATCH), Path, Request Schema (dynamic fields with types), Response Schema (dynamic fields with types)
- **Supported field types**: any, string, int, float, bool, list, dict, json, base64, bytes, image, audio, video, file, date, datetime, url, email, uuid
- **Handles**: Output (right, source)
- **Output**: The incoming request body as a dictionary, filtered by the request schema if defined.

#### Webhook Trigger
Receives external webhook payloads. Similar to HTTP Entry but designed for incoming webhook integrations.
- **Handles**: Output (right, source)

#### Cron Schedule
Time-based trigger that runs the workflow on a schedule using cron expressions.
- **Fields**: Cron Expression (e.g., `*/5 * * * *` for every 5 minutes)
- **Handles**: Output (right, source)

#### Manual Trigger
A test entry point for manual execution without a live API endpoint.
- **Handles**: Output (right, source)

---

### 2. Logic

Logic nodes control conditional branching and custom code execution.

#### If Condition
Branches execution into two paths based on a condition evaluation.
- **Fields**: Field (the value to check, supports Static/Input/Expression modes), Operator (==, !=, >, <, >=, <=), Compare Value (supports Static/Input/Expression modes)
- **Handles**: Input (left, target), Output (right, source) -- edges carry condition labels `"true"` / `"false"` to route downstream nodes
- **Output**: `{ __condition__: true/false, data: {...} }` -- downstream nodes on the matching branch receive the data.

#### Switch / Case
Multi-way branching based on a field's value matching defined cases.
- **Fields**: Field (supports modes), Cases (list of case values)
- **Handles**: Input (left, target), Output (right, source) -- edges carry case labels
- **Output**: `{ __case__: "value", data: {...} }` -- routes to the matching case branch.

#### Python Function
Execute custom Python code within the workflow. Has access to all upstream inputs.
- **Fields**: Code (Python editor)
- **Handles**: Input (left, target), Output (right, source)
- **Output**: Whatever the Python function returns (must be a dict).

---

### 3. Flow Control

#### Processor
A transform and relay node. In default mode, merges all upstream inputs and passes them through. When field mappings are configured, builds a new dictionary from the specified fields.
- **Fields**: Field Mappings (dynamic list of name + source mode + value)
- **Handles**: Input (left, target), Output (right, source)
- **Output**: The merged or transformed data dictionary.

#### Loop ForEach
Iterates over an array, executing a body of nodes for each element. Has 4 handles for controlling loop flow.
- **Fields**: Array Field (which key contains the array to iterate over)
- **Handles**:
  - Input `in` (left, target, top 30%) -- receives the array data
  - Loop Back `loop_back` (left, target, bottom 75%) -- receives output from the loop body to continue iteration
  - Loop Out `loop_out` (right, source, top 30%) -- sends each element to the loop body
  - Done `done` (right, source, bottom 75%) -- outputs accumulated results after all iterations complete
- **Output**: Accumulated array of results from each iteration.

#### Parallel Split
Runs all downstream children concurrently using asyncio.gather.
- **Handles**: Input (left, target), Output (right, source)
- **Output**: Same as input -- the downstream nodes run in parallel.

#### Merge / Join
Collects outputs from parallel branches and merges them into a single dictionary.
- **Handles**: Input (left, target), Output (right, source)
- **Output**: Merged dictionary from all upstream branches.

#### Delay
Pauses execution for a configurable number of seconds.
- **Fields**: Seconds (number)
- **Handles**: Input (left, target), Output (right, source)
- **Output**: Passes through the input unchanged after the delay.

---

### 4. Output

#### Response
The terminal node of API workflows. Builds the HTTP response by mapping upstream data to named output fields.
- **Fields**: Field Mappings (dynamic list with name, type, and Static/Input/Expression source mode)
- **Handles**: Input (left, target)
- **Output**: The constructed response dictionary, which becomes the API response body.

---

### 5. Middleware

#### Header Extractor
Extracts specific HTTP headers from the incoming request.
- **Fields**: Headers to extract (list of header names)
- **Handles**: Input (left, target), Output (right, source)
- **Output**: Dictionary of extracted header key-value pairs.

#### Auth Gate
Validates API keys or authentication tokens from request headers.
- **Fields**: Auth configuration
- **Handles**: Input (left, target), Output (right, source)
- **Output**: Passes through on success, blocks execution on failure.

---

### 6. Database Nodes

All database nodes follow a consistent pattern with Input (left) and Output (right) handles. They connect to databases using connection strings configured in each node.

#### PostgreSQL (8 nodes)
| Node | Description | Key Fields |
|------|-------------|------------|
| PG Find | Query rows with filters | Table, Filter, Columns, Limit |
| PG Insert | Insert rows | Table, Data |
| PG Update | Update rows | Table, Filter, Data |
| PG Delete | Delete rows | Table, Filter |
| PG Query | Execute raw SQL | SQL Query |
| PG Txn Start | Begin transaction | Connection |
| PG Txn Commit | Commit transaction | Connection |
| PG Txn Rollback | Rollback transaction | Connection |

#### MySQL (8 nodes)
Same operations as PostgreSQL: Find, Insert, Update, Delete, Raw Query, Txn Start, Txn Commit, Txn Rollback.

#### MongoDB (5 nodes)
| Node | Description | Key Fields |
|------|-------------|------------|
| Mongo Find | Find documents | Collection, Filter, Projection |
| Mongo Insert | Insert documents | Collection, Document |
| Mongo Update | Update documents | Collection, Filter, Update |
| Mongo Delete | Delete documents | Collection, Filter |
| Mongo Aggregate | Aggregation pipeline | Collection, Pipeline |

#### SQLite (5 nodes)
Find, Insert, Update, Delete, Raw Query -- operating on SQLite database files.

#### Supabase (5 nodes)
Find, Insert, Update, Delete, Raw Query -- operating on Supabase tables via the Supabase client.

---

### 7. AI Config Nodes

Config nodes provide configuration to AI execution nodes via **typed handles**. They do not process data; they supply credentials and settings. Each has an Input handle (left) and a typed source handle (right).

#### LLM Model
Configures the language model provider and credentials.
- **Fields**: Provider (openai, anthropic, gemini, ollama, groq, mistral), Model (e.g., gpt-4o-mini), API Key, Temperature, Base URL
- **Source Handle**: `ai_model` (connects to LLM Call, Agent, Vision, STT, TTS nodes)

#### Output Structure
Defines a JSON schema for structured LLM output.
- **Fields**: JSON Schema
- **Source Handle**: `ai_structure` (connects to LLM Call, Agent nodes)

#### Memory
Configures conversational memory for agents.
- **Fields**: Backend (in_memory, redis, vector), Session ID, Max Messages, Redis URL
- **Source Handle**: `ai_memory` (connects to Agent nodes)

#### Embedding Model
Configures the embedding provider for vector operations.
- **Fields**: Provider (openai, ollama, huggingface), Model (e.g., text-embedding-3-small), API Key
- **Source Handle**: `ai_embedding` (connects to Embedding Generate, RAG Retrieval, Agent nodes)

#### Vector Store
Configures the vector database connection.
- **Fields**: Provider (qdrant, pinecone, weaviate, chroma, supabase), Collection, URL, API Key
- **Source Handle**: `ai_vectorstore` (connects to Vector Upsert, Vector Search, Vector Delete, RAG Retrieval, Agent nodes)

---

### 8. AI Tool Nodes

Tool nodes give agents capabilities. Each tool node connects to an Agent's `ai_tool` handle. The agent decides when and how to use each tool during its reasoning loop.

All tool nodes have:
- **Input handle** (left, target) -- for data flow
- **Source handle** `ai_tool` (right) -- connects to Agent's `ai_tool` target handle

#### Web Search
Searches the internet using the Tavily API.
- **Fields**: Tavily API Key, Max Results

#### HTTP Request
Makes HTTP calls to external APIs.
- **Fields**: Allowed Methods, Timeout

#### Calculator
Evaluates mathematical expressions. No configuration needed.

#### DB Query
Executes database queries as an agent tool.
- **Fields**: Database Type (postgres, mysql, sqlite, mongo), Connection ID / URI

#### Code Executor
Runs sandboxed Python code.
- **Fields**: Timeout

#### File Ops
Reads or writes files on the server.
- **Fields**: Mode (read/write), Base Path

#### Email Sender
Sends emails via SMTP.
- **Fields**: SMTP Host, SMTP Port, Username, Password, From Email

#### Gmail
Sends emails via Gmail SMTP with simplified configuration.
- **Fields**: Gmail Address, App Password
- The agent chooses the recipient, subject, and body at runtime.

#### Slack Notifier
Sends messages to Slack via webhook.
- **Fields**: Webhook URL

#### Workflow Invoker
Calls another deployed SynthTeam workflow as a tool.
- **Fields**: Workflow URL, Method

#### Composio
Integrates with Composio for third-party actions (GitHub, Google Sheets, etc.).
- **Fields**: API Key, Action

#### Knowledge Base (RAG Tool)
Enables agents to search a vector store for relevant document chunks (Agentic RAG).
- **Fields**: Data Description (tells the agent what this knowledge base contains), Collection, Top K, Embedding Provider, Embedding Model, Embedding API Key, Vector Store Provider, Vector Store URL, Vector Store API Key
- The agent calls this tool with a natural-language query. The tool embeds the query, searches the vector store, and returns matching document chunks.
- Can inherit Embedding Model and Vector Store Config from the agent's `ai_embedding` / `ai_vectorstore` handles to avoid duplicating credentials.

---

### 9. AI / LLM Execution

#### LLM Call
Invokes a language model with a system prompt and user prompt. Supports structured output.
- **Fields**: System Prompt (Static/Input/Expression), Prompt Template (Static/Input/Expression)
- **Target Handles**: `ai_model` (Model), `ai_structure` (Schema)
- **Handles**: Input (left, target), Output (right, source)
- **Output**: `{ response: "...", model: "...", usage: {...} }`

---

### 10. RAG Pipeline

RAG (Retrieval-Augmented Generation) nodes form a pipeline for ingesting documents into a vector store and retrieving relevant chunks for context.

#### Document Loader
Loads text content from various sources.
- **Fields**: Source Type (text, url, file), Text/Content, URL, File Path
- **Handles**: Input (left, target), Output (right, source via `default` handle)
- **Output**: `{ documents: ["..."], source: "...", char_count: N }`

#### Text Splitter
Chunks documents into smaller pieces for embedding.
- **Fields**: Strategy (character, separator), Chunk Size, Overlap, Separator
- **Handles**: Input (left, target), Output (right, source via `default` handle)
- **Input**: Reads `documents` array from upstream.
- **Output**: `{ chunks: ["...", "..."], chunk_count: N, strategy: "..." }`

#### Generate Embedding
Converts text or chunks into vector embeddings.
- **Fields**: Text Template
- **Target Handles**: `ai_embedding` (Embed Model)
- **Handles**: Input (left, target), Output (right, source)
- **Input**: Reads `chunks` array (batch mode) or `text` (single mode) from upstream.
- **Output (batch)**: `{ embeddings: [[...], [...]], chunks: ["..."], dimensions: N, count: N }`
- **Output (single)**: `{ embedding: [...], dimensions: N, text: "..." }`

#### Vector Upsert
Inserts embeddings and their associated text chunks into a vector database.
- **Target Handles**: `ai_vectorstore` (VStore)
- **Handles**: Input (left, target), Output (right, source)
- **Input**: Reads `embeddings` + `chunks` (batch) or `embedding` + `text` (single) from upstream.
- **Output**: `{ status: "upserted", collection: "...", count: N }`

#### Vector Search
Performs similarity search on a vector database using a pre-computed query vector.
- **Fields**: Top K
- **Target Handles**: `ai_vectorstore` (VStore)
- **Handles**: Input (left, target), Output (right, source)
- **Input**: Reads `embedding` (query vector) and/or `query`/`text` from upstream.
- **Output**: `{ documents: ["..."], count: N }`

#### Vector Delete
Deletes vectors from a vector database.
- **Target Handles**: `ai_vectorstore` (VStore)
- **Handles**: Input (left, target), Output (right, source)

#### RAG Retrieval
An all-in-one retrieval node. Embeds the query, searches the vector store, and returns concatenated context. Combines Embedding Generate + Vector Search into a single step.
- **Fields**: Top K
- **Target Handles**: `ai_embedding` (Embed), `ai_vectorstore` (VStore)
- **Handles**: Input (left, target), Output (right, source)
- **Input**: Reads `query`, `text`, or `input` from upstream data.
- **Output**: `{ context: "...", documents: ["..."], query: "...", count: N }`

---

### 11. Agents

Agent nodes are intelligent execution units that reason, plan, and use tools to accomplish tasks.

#### Agent (ReAct)
A ReAct (Reasoning + Acting) agent that iteratively reasons about the task, selects tools, executes them, observes results, and continues until the goal is achieved.
- **Fields**: System Prompt (Static/Input/Expression), Prompt / Goal (Static/Input/Expression), Max Iterations
- **Target Handles**:
  - `ai_model` (Model) -- required, provides the LLM
  - `ai_tool` (Tools) -- optional, one or more tool nodes
  - `ai_memory` (Memory) -- optional, conversational memory backend
  - `ai_structure` (Schema) -- optional, structured output format
  - `ai_embedding` (Embed) -- optional, shared embedding config for Knowledge Base tools
  - `ai_vectorstore` (VStore) -- optional, shared vector store config for Knowledge Base tools
  - `ai_subagent` (Sub-Agents) -- optional, other agent nodes as sub-agents
- **Handles**: Input (left, target), Output (right, source)
- **Output**: `{ output: "...", iterations: N, tool_calls: [...] }` (full message history stripped)
- **Memory**: When a Memory node is connected, the agent loads previous conversation history before executing and saves new messages after execution, enabling multi-turn conversations keyed by `session_id`.

#### Autonomous Agent
A planning-based agent that first creates a step-by-step plan, then executes each step using tools, and finally summarizes the results.
- **Fields**: System Prompt (Static/Input/Expression), Goal (Static/Input/Expression), Max Steps
- **Target Handles**: Same as Agent (ReAct): `ai_model`, `ai_tool`, `ai_memory`, `ai_embedding`, `ai_vectorstore`, `ai_subagent`
- **Handles**: Input (left, target), Output (right, source)
- **Output**: Planning results and final summary.

---

### 12. Vision and Speech

#### Vision Analyze
Analyzes images using multimodal LLMs (e.g., GPT-4 Vision).
- **Fields**: Image URL / Base64, Prompt
- **Target Handles**: `ai_model` (Model)
- **Handles**: Input (left, target), Output (right, source)

#### Speech to Text
Transcribes audio files to text.
- **Fields**: Provider (e.g., openai_whisper), Audio Path, Language
- **Target Handles**: `ai_model` (Model)
- **Handles**: Input (left, target), Output (right, source)

#### Text to Speech
Converts text to audio.
- **Fields**: Provider, Voice, Text Template
- **Target Handles**: `ai_model` (Model)
- **Handles**: Input (left, target), Output (right, source)

---

## Connection Handles Reference

### Data Flow Handles
| Handle ID | Type | Description |
|-----------|------|-------------|
| `input` | target (left) | Receives data from upstream nodes |
| `output` | source (right) | Sends data to downstream nodes |
| `default` | source (right) | Used by Config nodes (Doc Loader, Text Splitter) for general data output |
| `in` | target (left) | Loop ForEach input |
| `loop_back` | target (left) | Loop ForEach body return |
| `loop_out` | source (right) | Loop ForEach body output |
| `done` | source (right) | Loop ForEach completion |

### Typed AI Handles
| Handle ID | Type | Color | What Connects | Connects To |
|-----------|------|-------|---------------|-------------|
| `ai_model` | target | Purple | LLM Model config node | LLM Call, Agents, Vision, STT, TTS |
| `ai_tool` | target | Amber | Tool nodes (Web Search, Calculator, etc.) | Agent (ReAct), Autonomous Agent |
| `ai_memory` | target | Cyan | Memory Config node | Agent (ReAct), Autonomous Agent |
| `ai_structure` | target | Emerald | Output Structure node | LLM Call, Agent (ReAct) |
| `ai_embedding` | target | Indigo | Embedding Model config node | Embedding Generate, RAG Retrieval, Agent (ReAct), Autonomous Agent |
| `ai_vectorstore` | target | Violet | Vector Store Config node | Vector Upsert, Vector Search, Vector Delete, RAG Retrieval, Agent (ReAct), Autonomous Agent |
| `ai_subagent` | target | Pink | Other Agent nodes | Agent (ReAct), Autonomous Agent |

---

## Example Workflows

### 1. Simple REST API
Build a CRUD API backed by a database.

```
HTTP Entry (POST /api/users) --> PG Insert --> Response
HTTP Entry (GET /api/users)  --> PG Find   --> Response
```

### 2. Conditional API with Auth
An authenticated API that branches on input.

```
HTTP Entry --> Header Extractor --> Auth Gate --> Processor --> If Condition
                                                                 |-> (true)  PG Find    --> Response
                                                                 |-> (false) PG Insert  --> Response
```

### 3. LLM-Powered Chatbot API
A simple LLM invocation endpoint.

```
HTTP Entry --> LLM Call --> Response
                 ^
                 |
              LLM Model (OpenAI, gpt-4o)
```

### 4. ReAct Agent with Tools
An AI agent that can search the web, do math, and query a database.

```
HTTP Entry --> Agent (ReAct) --> Response
                 ^   ^   ^
                 |   |   |
           LLM Model |   |
                      |   |
               Web Search |
                          |
                     Calculator
```

### 5. RAG Ingestion Pipeline
Upload documents via API, chunk them, embed them, and store in a vector database.

```
HTTP Entry (POST /ingest) --> Doc Loader --> Text Splitter --> Embedding Generate --> Vector Upsert --> Response
                                                                    ^                     ^
                                                                    |                     |
                                                              Embedding Model       Vector Store Config
                                                            (OpenAI embed)         (Qdrant, collection: "docs")
```

### 6. RAG Query Pipeline
Query the vector store for relevant chunks and return context.

```
HTTP Entry (POST /query) --> RAG Retrieval --> Response
                                ^        ^
                                |        |
                          Embedding    Vector Store
                           Model        Config
```

### 7. RAG + LLM (Question Answering)
Retrieve context from a knowledge base, then use an LLM to generate an answer.

```
HTTP Entry (POST /ask) --> RAG Retrieval --> LLM Call --> Response
                             ^        ^        ^
                             |        |        |
                       Embedding   Vector    LLM Model
                        Model     Store
                                  Config
```
The RAG Retrieval node outputs `{ context, documents, query }`. The LLM Call's prompt template uses `{{context}}` and `{{query}}` to formulate the answer.

### 8. Agentic RAG
An agent that autonomously decides when to search a knowledge base (alongside other tools).

```
HTTP Entry --> Agent (ReAct) --> Response
                 ^   ^   ^   ^        ^
                 |   |   |   |        |
           LLM Model |   |   |        |
                      |   |   |        |
            Knowledge Base|   |        |
              (Tool)      |   |        |
                    Web Search|        |
                              |        |
                         Embedding   Vector Store
                          Model       Config
```
The Embedding Model and Vector Store Config connect to both the Agent's `ai_embedding` / `ai_vectorstore` handles, automatically sharing credentials with the Knowledge Base tool.

### 9. Multi-Turn Conversational Agent
An agent with memory that maintains conversation history across requests.

```
HTTP Entry (POST /chat, body: {query, session_id}) --> Agent (ReAct) --> Response
                                                         ^   ^   ^
                                                         |   |   |
                                                   LLM Model |   |
                                                              |   |
                                                       Web Search |
                                                                  |
                                                            Memory Config
                                                          (Redis, session_id)
```
Each request includes a `session_id`. The Memory node stores conversation history in Redis, keyed by session. The agent loads previous messages before responding and saves new messages after.

### 10. Autonomous Agent with Sub-Agents
An autonomous planning agent that delegates sub-tasks.

```
HTTP Entry --> Autonomous Agent --> Response
                 ^   ^   ^   ^
                 |   |   |   |
           LLM Model |   |   |
                      |   |   |
              Web Search  |   |
                          |   |
                    Agent (ReAct)  <-- (connected as sub-agent)
                       ^   ^
                       |   |
                 LLM Model |
                            |
                      Calculator
```

### 11. Parallel Processing Pipeline
Process multiple tasks concurrently.

```
HTTP Entry --> Parallel Split --> PG Find     --> Merge / Join --> Response
                              --> Mongo Find  -->
                              --> LLM Call    -->
```

### 12. Batch Processing with Loop
Iterate over an array of items and process each one.

```
HTTP Entry --> Loop ForEach
                 | (loop_out)
                 v
              PG Insert --> (loop_back)
                 | (done)
                 v
              Response
```

### 13. Scheduled Data Pipeline
A cron-triggered workflow that runs every hour.

```
Cron Trigger (0 * * * *) --> PG Find --> Processor --> PG Insert
```

### 14. Vision Analysis API
Analyze images with GPT-4 Vision.

```
HTTP Entry (POST /analyze, body: {image_url, prompt}) --> Vision Analyze --> Response
                                                            ^
                                                            |
                                                       LLM Model (gpt-4o)
```

---

## Supported Providers

### LLM Providers
- OpenAI (GPT-4o, GPT-4o-mini, GPT-3.5, etc.)
- Anthropic (Claude 3.5, Claude 3, etc.)
- Google Gemini
- Ollama (local models)
- Groq
- Mistral

### Embedding Providers
- OpenAI (text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002)
- Ollama (local embedding models)
- HuggingFace

### Vector Store Providers
- Qdrant
- Pinecone
- Weaviate
- ChromaDB
- Supabase (pgvector)

### Database Connectors
- PostgreSQL
- MySQL
- MongoDB
- SQLite
- Supabase
