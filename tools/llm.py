"""
LLM integration via local vLLM (Qwen3.6-27B) using OpenAI-compatible API.
Graceful fallback when langchain-openai is not installed.
"""
import os

# Lazy import — gracefully handle missing langchain-openai
_import_error = None
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError as e:
    _import_error = str(e)
    ChatOpenAI = None  # type: ignore
    HumanMessage = None  # type: ignore
    SystemMessage = None  # type: ignore


def get_llm(model: str = None, base_url: str = None):
    """Get a configured vLLM LLM instance (OpenAI-compatible). Returns None if langchain_openai unavailable."""
    if ChatOpenAI is None:
        print(f"WARNING: langchain_openai not installed ({_import_error}). Running in dry-run mode.")
        return None

    if not model:
        model = os.getenv("LLM_MODEL", "Qwen3.6-27B")
    if not base_url:
        base_url = os.getenv("LLM_BASE_URL", "http://localhost:8080/v1")

    return ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=os.getenv("OPENAI_API_KEY", "not-needed"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
        max_tokens=32768,
    )


def invoke_skill(skill_content: str, task: str, context: str = "", llm=None):
    """
    Invoke a skill: combine its instructions with the task and context,
    send to the LLM, and return the response.
    Falls back to echo mode when LLM is unavailable.
    """
    if llm is None:
        llm = get_llm()

    if llm is None:
        # Dry-run: return summary of what would happen
        return f"[DRY-RUN] Skill({len(skill_content)} chars) → Task: {task}"

    system_prompt = (
        f"You are an expert following these instructions:\n\n"
        f"{skill_content}\n\n"
        f"Respond with actionable output. Be specific, include file paths, "
        f"code snippets, and verification steps."
    )

    user_prompt = f"Task: {task}\n\nContext: {context}"

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        return response.content
    except Exception as e:
        return f"[LLM ERROR] {e}"