"""
LLM integration via local vLLM (Qwen3.6-27B) using OpenAI-compatible API.
Uses distilled skill instructions (Purpose + Process only) for fast context windows.
"""
import os
from tools.distiller import distill_skill

_import_error = None
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError as e:
    _import_error = str(e)
    ChatOpenAI = None
    HumanMessage = None
    SystemMessage = None


def get_llm(model: str = None, base_url: str = None):
    """Get a configured LLM instance. Returns None if langchain_openai unavailable."""
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


def invoke_skill(skill_content: str, task: str, context: str = "", llm=None, max_prompt_chars: int = 2000):
    """
    Invoke a skill: distill its instructions, combine with task + context,
    send to the LLM, and return the response.

    Args:
        skill_content: Raw SKILL.md content (distilled automatically).
        task: What to accomplish.
        context: Additional project context.
        llm: Pre-created LLM instance (created if None).
        max_prompt_chars: Max chars for the distilled skill portion.
    """
    if llm is None:
        llm = get_llm()

    if llm is None:
        return f"[DRY-RUN] Skill({len(skill_content)} chars) → Task: {task}"

    # Distill skill to essential instructions
    distilled = distill_skill(skill_content, max_chars=max_prompt_chars)

    system_prompt = (
        f"You are an expert following these instructions:\n\n"
        f"{distilled}\n\n"
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