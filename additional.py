from deepagents import create_deep_agent, FilesystemPermission
from langgraph.checkpoint.memory import MemorySaver
from langchain_quickjs import CodeInterpreterMiddleware
from custom_py import PiiRedactionMiddleware


agent = create_deep_agent(
    model="google_genai:gemini-2.5-flash",
    permissions=[
        # Safe Zone: Let the agent read and write freely here
        FilesystemPermission(operations=["read", "write"], paths=["/workspace/**"], mode="allow"),
        
        # Danger Zone: If it attempts to touch private keys/secrets, completely pause the agent
        FilesystemPermission(operations=["write", "read"], paths=["/secrets/**"], mode="interrupt"),
        
        # Catch-all: Deny all other read/write operations on the machine
        FilesystemPermission(operations=["read", "write"], paths=["/**"], mode="deny")
    ]
)


agent = create_deep_agent(
    model="google_genai:gemini-2.5-flash",
    # Extends the agent's capabilities with custom validation and runtime execution
    middleware=[
        CodeInterpreterMiddleware(), # Injects the in-process `eval` tool
        PiiRedactionMiddleware()      # Custom logic to clean data before sending to LLM
    ]
)



# A sensitive tool we built
def delete_user_account(user_id: str):
    ...

agent = create_deep_agent(
    model="google_genai:gemini-2.5-flash",
    tools=[delete_user_account],
    checkpointer=MemorySaver(), # REQUIRED for human-in-the-loop interrupts to work
    interrupt_on={
        # Always pause and ask a human before executing this tool
        "delete_user_account": {
            "allowed_decisions": ["approve", "edit", "reject"] #approve, edit, reject, respond
        }
    }
)