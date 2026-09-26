from langgraph.checkpoint.memory import MemorySaver


# Development short-term agent memory.
#
# Conversation state is retained by LangGraph for the lifetime
# of this application process and is isolated by thread_id.
agent_checkpointer = MemorySaver()