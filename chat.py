import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from deepagents.backends.utils import create_file_data

# Your custom library imports
from deep_agent_blueprints import spawn_agent
from subagent_blueprints import researcher, code_reviewer, commenter, segmenter, summarizer
from tools import internet_search, fetch_website_content, hash_str, extract_exact_pages

load_dotenv()

@st.cache_resource
def get_agent():
    return spawn_agent(
        agent_type="generalist", 
        model="openai:gpt-5.4-nano", 
        tools=[internet_search, fetch_website_content, hash_str, extract_exact_pages], 
        root_dir="./virtualFileSystem",
        skills=["/skills/"],
        subagents=[segmenter, summarizer],
    )
agent = get_agent()



st.set_page_config(page_title="Deep Agent Chat", page_icon="🤖", layout="wide")
st.title("🤖 Deep Agent Workspace")

config = {"configurable": {"thread_id": "streamlit_session_1"}}

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("thought_process"):
            with st.expander("🔍 View Detailed Thinking Process"):
                st.code(msg["thought_process"], language="text")

# -------------------------------------------------------------
# Change 2: Check for interrupt, show descriptive metadata, and allow all choices
# -------------------------------------------------------------
current_state = agent.get_state(config)
is_interrupted = bool(current_state.next)

prompt_payload = None

if is_interrupted:
    # 1. Dynamically extract exactly what the agent is asking permission for
    tool_name = "Unknown Action"
    try:
        if current_state.tasks:
            # Look at the tool calls inside the pending graph tasks
            last_task = current_state.tasks[-1]
            if last_task.interrupts:
                # Extracts information from the framework's serialization layer
                tool_name = str(last_task.interrupts[0].value)
    except Exception:
        pass

    # Display the clear notice 
    st.info(f"**Permission Required for**: `{tool_name}`")
    
    # 2. Render smaller, layout-friendly buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        # Using type="primary" and keeping text short shrinks button visual weight
        if st.button("Approve", use_container_width=True, type="primary"):
            prompt_payload = Command(resume={"decisions": [{"type": "approve"}]})
    with col2:
        if st.button("Reject", use_container_width=True):
            prompt_payload = Command(resume={"decisions": [{"type": "reject"}]})
            
    # 3. Text pipeline supporting 'respond' (feedback) and 'edit' (argument modification)
    feedback_msg = st.text_input("💬 Change course or suggest corrections (All Options):", 
                                 placeholder="Type feedback to 'respond' instead, or paste corrected arguments here...")
    
    if feedback_msg:
        col3, col4 = st.columns(2)
        with col3:
            if st.button("💬 Send as Feedback (Respond)", use_container_width=True):
                prompt_payload = Command(resume={"decisions": [{"type": "respond", "message": feedback_msg}]})
        with col4:
            if st.button("✏️ Inject as Argument (Edit)", use_container_width=True):
                import json
                try:
                    # Expects valid JSON string arguments to patch into the tool edit block
                    parsed_args = json.loads(feedback_msg)
                    prompt_payload = Command(resume={"decisions": [{"type": "edit", "args": parsed_args}]})
                except Exception:
                    st.error("To use 'Edit', please enter a valid JSON string of arguments (e.g., {'path': '/workspace/file.txt'})")
else:
    if user_query := st.chat_input("Ask your agent something..."):
        with st.chat_message("user"):
            st.markdown(user_query)
        st.session_state.messages.append({"role": "user", "content": user_query})
        prompt_payload = {"messages": [{"role": "user", "content": user_query}]}

# -------------------------------------------------------------
# 3. Handle Execution (Runs for both user queries AND button decisions)
# -------------------------------------------------------------
if prompt_payload is not None:
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            
            # This seamlessly accepts either the standard text prompt dict OR the LangGraph Command object
            response = agent.invoke(prompt_payload, config=config)
            
            # --- Extracting Responses ---
            final_message_obj = response['messages'][-1]
            
            if isinstance(final_message_obj.content, list):
                final_answer = final_message_obj.content[0].get('text', '')
            else:
                final_answer = final_message_obj.content
                
            all_steps = []
            for m in response['messages'][:-1]:  
                if hasattr(m, 'tool_calls') and m.tool_calls:
                    all_steps.append(f"[Tool Call]: {m.tool_calls}")
                elif m.content:
                    all_steps.append(f"[{m.type.upper()}]: {m.content}")
            
            thought_log = "\n\n".join(all_steps) if all_steps else "Direct response. No intermediate tool steps used."

        st.markdown(final_answer)
        
        with st.expander("🔍 View Detailed Thinking Process"):
            st.code(thought_log, language="text")
            
        st.session_state.messages.append({
            "role": "assistant", 
            "content": final_answer,
            "thought_process": thought_log
        })
        
        st.rerun() # Refresh layout to clean up buttons if the agent finished the action