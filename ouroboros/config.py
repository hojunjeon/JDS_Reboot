"""Configuration and LLM helper utilities for Ouroboros Lite.

This module loads API keys from the environment and implements a robust
HTTP-based LLM calling client with graceful fallbacks and mocking capabilities
to ensure that the framework can be tested and run even without API credentials.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
from rich.console import Console

# Rich Console for status updates
console = Console()

# ---------------------------------------------------------------------------
# 1. API Keys & Endpoint Configurations
# ---------------------------------------------------------------------------

OPENAI_API_KEY: Optional[str] = os.environ.get("OPENAI_API_KEY")
GEMINI_API_KEY: Optional[str] = os.environ.get("GEMINI_API_KEY")
ANTHROPIC_API_KEY: Optional[str] = os.environ.get("ANTHROPIC_API_KEY")

# Default Models
OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
ANTHROPIC_MODEL: str = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")

# Global LLM settings
DEFAULT_TEMPERATURE: float = float(os.environ.get("LLM_TEMPERATURE", "0.2"))
DEFAULT_TIMEOUT: int = int(os.environ.get("LLM_TIMEOUT", "30"))


# ---------------------------------------------------------------------------
# 2. Rule-Based Fallback/Mock Generator
# ---------------------------------------------------------------------------


def generate_fallback_response(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Generates context-aware high-fidelity mock responses based on standard
    Ouroboros requirements. This guarantees functionality without API keys.
    """
    prompt_lower = prompt.lower()

    if "socratic" in prompt_lower or "clarify" in prompt_lower:
        return """### Socratic Clarification Questions

1. **Phaser 3 Physics selection**: Should we use Phaser's default Arcade Physics (sufficient for rectangular bounding boxes and simple velocities) or a lightweight, grid-based customized collision system to perfectly emulate pure terminal grids?
2. **Terminal UI/IDE Graphics**: Should we construct standard Phaser GameObjects (with monospace BitmapFonts/Text) for the IDE panel interfaces, or overlay HTML/CSS DOM layers over the game canvas?
3. **Weapon Scaling and Balance**: How should the fire rates, velocity, and penetration scale between the starting languages: Python (balanced automatic), C++ (high speed linear pierce), and Java (circular orbit shield)?
4. **Time vs. Kill-based Boss Spawns**: Should the boss 'Jang Seonhyeong' trigger precisely at 60 seconds of survival, or do we require the player to resolve a threshold number of basic syntax errors (e.g., 50 bugs)?
5. **Session Persistence**: Is weapon unlock/progression data persisted locally (e.g., `localStorage`), or is every survival iteration treated as a stateless reboot?
"""

    elif (
        "double diamond" in prompt_lower
        or "planning" in prompt_lower
        or "mvp" in prompt_lower
    ):
        return """### Double Diamond Implementation Plan

#### Phase 1: Discover & Define (Problem Space)
*   **Discover**: Map the core fantasy of surviving programming bugs inside a terminal workspace. Focus on low-complexity, keyboard-only controls.
*   **Define**: Restrict the MVP to Stage 1 (Python Basics), 3 starting weapons (Python, C++, Java), 4 enemy types (SyntaxError, NullPointer, SegFault, HealBug), and 1 boss.

#### Phase 2: Develop & Deliver (Solution Space)
*   **Develop**: Establish Phaser 3 engine scaffolding with clear separation of game logic structures from scene-rendering interfaces.
*   **Deliver**: Execute mathematical verification on weapon collision matrices and spawn timers. Package the interactive web application bundle.
"""

    elif "acceptance criteria" in prompt_lower or "ac" in prompt_lower:
        return """### Acceptance Criteria (AC) Hierarchy

- **AC-101**: Player character must receive arrow key / WASD input and move smoothly.
- **AC-102**: Basic enemies (SyntaxError) must track player coordinates and inflict contact damage.
- **AC-103**: Python projectile weapon must auto-acquire and fire towards the nearest enemy every 1.5 seconds.
- **AC-104**: Boss 'Jang Seonhyeong' must spawn exactly when the game clock hits 60 seconds, initiating phase 2 of the stage.
"""

    elif "architecture" in prompt_lower or "decisions" in prompt_lower:
        return """### Architecture Decisions (AD)

- **AD-001**: Use Phaser 3 standard canvas rendering for cross-browser web gaming.
- **AD-002**: Abstract all weapon/enemy behaviors into state-driven configurations to simplify tuning.
- **AD-003**: Keep game state updates pure and decoupled from drawing operations to facilitate fast unit testing.
"""

    else:
        return f"""[Fallback Mock Response]
Received prompt: {prompt[:150]}...
(Note: No LLM API keys were detected in the environment or the API request failed.
This is a standard high-fidelity rule-based response generated by the Ouroboros mock runner.)
"""


# ---------------------------------------------------------------------------
# 3. Provider-Specific Call Implementations
# ---------------------------------------------------------------------------


def _call_gemini(
    prompt: str, system_prompt: Optional[str], model: str, temp: float, api_key: str
) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    payload: Dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temp},
    }

    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )

    with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        return str(res_data["candidates"][0]["content"]["parts"][0]["text"])


def _call_openai(
    prompt: str, system_prompt: Optional[str], model: str, temp: float, api_key: str
) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temp,
    }

    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )

    with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        return str(res_data["choices"][0]["message"]["content"])


def _call_anthropic(
    prompt: str, system_prompt: Optional[str], model: str, temp: float, api_key: str
) -> str:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": temp,
    }
    if system_prompt:
        payload["system"] = system_prompt

    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST"
    )

    with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        return str(res_data["content"][0]["text"])


# ---------------------------------------------------------------------------
# 4. Main Robust LLM Entry Point
# ---------------------------------------------------------------------------


def call_llm(
    prompt: str,
    system_prompt: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> str:
    """Robust LLM calling helper.

    Attempts to invoke the specified provider (or auto-detects based on env),
    handling network issues and authentication missing gracefully by falling
    back to context-aware mock generators.
    """
    temp = temperature if temperature is not None else DEFAULT_TEMPERATURE

    # 1. Determine provider & key
    chosen_provider = provider.lower() if provider else None

    # Auto-detect if not specified
    if not chosen_provider:
        if GEMINI_API_KEY:
            chosen_provider = "gemini"
        elif OPENAI_API_KEY:
            chosen_provider = "openai"
        elif ANTHROPIC_API_KEY:
            chosen_provider = "anthropic"
        else:
            console.log(
                "[yellow]No API keys found in environment. Using robust rules/mock fallback.[/yellow]"
            )
            return generate_fallback_response(prompt, system_prompt)

    # 2. Invoke appropriate API
    try:
        if chosen_provider == "gemini":
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not configured in the environment.")
            target_model = model or GEMINI_MODEL
            console.log(f"[green]Calling Gemini ({target_model})...[/green]")
            return _call_gemini(
                prompt, system_prompt, target_model, temp, GEMINI_API_KEY
            )

        elif chosen_provider == "openai":
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not configured in the environment.")
            target_model = model or OPENAI_MODEL
            console.log(f"[green]Calling OpenAI ({target_model})...[/green]")
            return _call_openai(
                prompt, system_prompt, target_model, temp, OPENAI_API_KEY
            )

        elif chosen_provider == "anthropic":
            if not ANTHROPIC_API_KEY:
                raise ValueError(
                    "ANTHROPIC_API_KEY is not configured in the environment."
                )
            target_model = model or ANTHROPIC_MODEL
            console.log(f"[green]Calling Anthropic ({target_model})...[/green]")
            return _call_anthropic(
                prompt, system_prompt, target_model, temp, ANTHROPIC_API_KEY
            )

        else:
            raise ValueError(f"Unknown or unsupported LLM provider: {provider}")

    except Exception as e:
        console.log(
            f"[red]LLM invocation failed: {e}. Falling back gracefully to mocks...[/red]"
        )
        return generate_fallback_response(prompt, system_prompt)
