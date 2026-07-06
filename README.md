# Deep Agent Testing Project (Virtual Workspace)

This repository contains a small playground for **deep agents** with:
- a **virtual filesystem backend** (so the agent reads/writes only inside a workspace)
- optional **sub-agents** for segmentation/summarization/research
- a **Streamlit UI** that supports **human-in-the-loop interrupts** (approve/reject/edit)

## Core files

### `chat.py`
Streamlit app for chatting with the agent.
- Creates the agent via `spawn_agent(...)` (from `deep_agent_blueprints.py`).
- Keeps chat history in `st.session_state`.
- Detects LangGraph interrupts (`agent.get_state(config).next`) and renders:
  - **Approve / Reject** buttons
  - **Respond** (send feedback as a message)
  - **Edit** (inject JSON-parsed tool arguments)
- Invokes the agent with `agent.invoke(...)` and renders the final answer.

Run it to interactively test agent behavior and interrupts.

### `deep_agent_blueprints.py`
Factory for creating different deep-agent “personalities” using `create_deep_agent`.
- `spawn_agent(agent_type, model, root_dir, memory_files, tools, subagents)`:
  - `python_coder`: coding-focused agent; allowed to create/edit/delete inside the virtual FS.
  - `generalist`: general assistant; sets permissions to prevent access to secrets and can require approval for `hash_str`.
  - `deep_rag`: RAG-style agent that reads from `kb_prepared/` and can use segment/summarize subagents when needed. (DOESN'T WORK WELL)

### `subagent_blueprints.py`
Definitions for sub-agents (as config dictionaries):
- `researcher`: uses `internet_search` + `fetch_website_content`.
- `code_reviewer`: reviews code (no tools; reports findings only).
- `commenter`: provides code comments (no tools; comments only).
- `segmenter`: calls `extract_exact_pages` and outputs page ranges per segment.
- `summarizer`: reads segments and writes a summary file.

### `tools.py`
Tool functions exposed to the agent via `@tool`:
- `internet_search(query, max_results=3)`: DuckDuckGo text search (DDGS).
- `fetch_website_content(url)`: fetches a webpage and extracts readable text (BeautifulSoup).
- `hash_str(text)`: returns Python `hash(text)`.
- `extract_exact_pages(pdf_path, start_page, end_page)`:
  - restricts access to the `virtualFileSystem/` directory
  - extracts text from a PDF page range using `pypdf`
  - clamps page bounds to avoid crashes.

### `additional.py`
Examples of deep-agent configuration patterns:
- Shows how to use `FilesystemPermission` allow/deny/interrupt rules.
- Shows how to attach middleware:
  - `CodeInterpreterMiddleware()`
  - `PiiRedactionMiddleware()`
- Demonstrates `interrupt_on` for a sensitive tool (`delete_user_account`).

### `virtualFileSystem/` (workspace)
The directory used by the virtual filesystem backend.
Relevant subfolders:
- `AGENTS.md`: agent “memory” content loaded into agents.
- `SECRETS/`: intended to be protected/denied by permissions.
- `kb_raw/`, `kb_prepared/`: knowledge base staging.
- `simpleCNN/`: example ML workspace (if present for testing).
- `skills/`: additional skill files.

### `test_prompt/`
(Directory exists in repo root; used for testing prompts—details not inspected here.)

## How to run (While in project root directory)

### 1) Install dependencies 
python -m venv venv
venv\Scripts\activate (on windows)
python -m pip install -r requirements.txt

### 2) Configure environment
create a `.env` file. Provide any required API keys for the configured model provider(s) (e.g. `openai`, `google_genai`, etc.).

### 3) Start the Streamlit UI
streamlit run chat.py

Then open the displayed local URL.

## How to test

### Test 1: Basic chat + tools
In the Streamlit UI, ask something that triggers the configured tools (in `chat.py`, the agent is created with):
- `internet_search`, `fetch_website_content`, `hash_str`, `extract_exact_pages`

Example prompts:
- “Find and summarize the latest info about X.” (tests web tools)
- “Compute a hash of this string: ...” (tests `hash_str` and its interrupt policy)
- “Extract pages from a PDF at ...” (tests `extract_exact_pages`)

### Test 2: Human-in-the-loop interrupts
Ask the agent to call `hash_str` (or any other `interrupt_on` tool configured in `deep_agent_blueprints.py`).
- The UI should pause and ask you to **Approve / Reject / Respond / Edit**.

### Test 3: Virtual filesystem safety
Instruct the agent to read/write outside the allowed virtual workspace (e.g., attempt `/secrets` or `/etc/passwd`).
- Permissions in `deep_agent_blueprints.py` should deny secrets access.

## Notes / conventions
- The project uses a **virtual filesystem backend** (`FilesystemBackend(..., virtual_mode=True)`) so file operations are constrained.
- Subagents are optional and injected via the `subagents=[...]` argument.

