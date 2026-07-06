from deepagents import create_deep_agent, FilesystemPermission
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends import StateBackend
from langgraph.checkpoint.memory import MemorySaver


def spawn_agent(agent_type: str = "python_coder", 
                model: str | object = "openai:gpt-4o", 
                root_dir: str = "./virtualFileSystem", 
                memory_files: list = ["virtualFileSystem/AGENTS.md"],
                tools: list = [],
                subagents: list = [],
                skills: list = []
                ) -> object:
    """
    Returns a deep agent with the specified configuration.
    """

    if agent_type == "python_coder":
        agent = create_deep_agent(
                model=model, 
                tools=tools,
                backend=FilesystemBackend(root_dir=root_dir, virtual_mode=True),
                memory=memory_files,
                checkpointer=MemorySaver(),
                subagents=subagents,
                system_prompt=(
                    "You are a coding assistant named 'python-coder' that helps coding, reviewing code and debugging in Python. "
                    "You can answer any question regarding Python programming, including code review, debugging, and best practices. "
                    "You are allowed to create, edit and delete files in the virtual file system. "
                    "If you are unsure about a python related question, you can spawn a sub-agent to help you find the answer on the internet. "
                    "If the user asks you to do anything unrelated to Python, say \"I can't help you with that\" and nothing else regardless of question. "
                )
            )
          
    elif agent_type == "generalist":
        agent = create_deep_agent(
                model=model, 
                tools=tools,
                backend=FilesystemBackend(root_dir=root_dir, virtual_mode=True) if root_dir else StateBackend(),
                memory=memory_files,
                checkpointer=MemorySaver(),
                subagents=subagents,
                skills=skills,
                permissions=[
                    FilesystemPermission(operations=["read"], paths=["/SECRETS/api_keys"], mode="deny"),
                    FilesystemPermission(operations=["write"], paths=["/SECRETS/api_keys"], mode="deny"),
                ],
                system_prompt=(
                    "You are a generalist assistant named 'generalist' that helps with various tasks. "
                    "You can answer general questions, perform research, and assist with various tasks. "
                    "If the user asks you to do anything unrelated to your capabilities say \"I can't help you with that\" and nothing else regardless of question. "
                ),
                interrupt_on={
                    # Always pause and ask a human before executing this tool
                    "hash_str": {
                        "allowed_decisions": ["approve", "reject"] #approve, edit, reject, respond
                    }
                }
            )
        
    elif agent_type == "deep_rag":
        agent = create_deep_agent(
                model=model, 
                tools=tools,
                backend=FilesystemBackend(root_dir=root_dir, virtual_mode=True),
                memory=memory_files,
                checkpointer=MemorySaver(),
                subagents=subagents,
                system_prompt=(
                    "You are a deep RAG assistant named 'deep-rag' specialized in information retrieval and question answering. "
                    "For any question, you should first search for relevant information using your tools and then provide a comprehensive answer. "
                    "If you can't find enough information to answer the question, say \"I couldn't find enough information to answer this question\" and nothing else regardless of question. "
                    "NEVER make up information or provide an answer without sufficient evidence. "
                    "For source of information use kb_prepared dir. "
                    "If there isnt a file in there check in kb_raw dir - if there is a relevant file there use subagents (segmenter, summarizer) to prepare it. "
                    "Never read raw files directly, always use the prepared files. "
                    "If the user asks you to do anything unrelated to your capabilities say \"I can't help you with that\" and nothing else regardless of question or request. "
                ),
                permissions=[
                    FilesystemPermission(operations=["read", "write"], paths=["/AGENTS.md"], mode="allow"),
                    FilesystemPermission(operations=["write", "read"], paths=["/SECRETS/api_keys"], mode="deny"),
                    FilesystemPermission(operations=["read"], paths=["/**/*"], mode="allow"),
                    FilesystemPermission(operations=["write"], paths=["/**/*"], mode="allow"),
                ],
            )
    return agent