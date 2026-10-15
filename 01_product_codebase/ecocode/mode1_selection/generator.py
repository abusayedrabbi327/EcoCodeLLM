"""
generator.py — LLM API caller for stochastic code sampling.

Issues N requests to the configured LLM with high temperature to
produce diverse code candidate solutions for a given programming prompt.
Supports OpenRouter (free models) and OpenAI, with an extensible adapter pattern.
"""

import os
import re
import json
import sys
import requests
from typing import List, Optional

# Ensure project root directory is in sys.path for direct file execution
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from ecocode.utils.logger import get_logger
from ecocode.utils.config_loader import get_config_value

logger = get_logger(__name__)


def _strip_code_fences(code: Optional[str]) -> str:
    """
    Remove markdown code fences from LLM output.

    LLMs often wrap code in ```python ... ``` blocks even when
    instructed not to. This strips those wrappers safely.
    """
    if not code:
        return ""
    # Remove ```python or ``` fences
    code = re.sub(r'^```(?:python)?\s*\n', '', code, flags=re.MULTILINE)
    code = re.sub(r'\n```\s*$', '', code, flags=re.MULTILINE)
    return code.strip()


def generate_with_openrouter(prompt: str, num_candidates: int = None,
                              temperature: float = None,
                              model: str = None) -> List[str]:
    """
    Generate N code candidates using the OpenRouter API.

    OpenRouter provides access to many LLM models (including free tiers)
    through a unified OpenAI-compatible API endpoint. This function uses
    direct HTTP requests (no SDK dependency required).

    Args:
        prompt: Natural language programming problem description.
        num_candidates: Number of code variants to generate (N).
        temperature: Sampling temperature (higher = more diverse).
        model: OpenRouter model identifier (e.g., 'openai/gpt-oss-20b:free').

    Returns:
        List of raw Python code strings.
    """
    from dotenv import load_dotenv

    # Load environment and config
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY not found. Set it in your .env file. "
            "See .env.example for the template."
        )

    if num_candidates is None:
        num_candidates = get_config_value("llm", "num_candidates", 5)
    if temperature is None:
        temperature = get_config_value("llm", "temperature", 0.7)
    if model is None:
        model = get_config_value("llm", "model", "openai/gpt-oss-20b:free")

    max_tokens = get_config_value("llm", "max_tokens", 2048)
    system_prompt = get_config_value("llm", "system_prompt",
        "You are an expert Python programmer. Generate exactly one complete "
        "Python function definition, including its def line. Return clean, "
        "executable Python code only. Do not include explanations, markdown "
        "formatting, code fences, or a test harness."
    )

    reasoning_enabled = get_config_value("llm", "reasoning_enabled", True)
    api_url = get_config_value("llm", "api_url", "https://openrouter.ai/api/v1/chat/completions")
    fallback_models = get_config_value("llm", "fallback_models", ["openrouter/free"])
    candidates = []

    logger.info(
        f"Generating {num_candidates} candidates via OpenRouter "
        f"(model={model}, temp={temperature}, reasoning={reasoning_enabled})..."
    )

    for i in range(num_candidates):
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if reasoning_enabled:
                payload["reasoning"] = {"enabled": True}

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ecocode-llm.dev",
                "X-Title": "EcoCode-LLM",
            }

            import time
            max_retries = 2
            response = None
            for attempt in range(max_retries):
                response = requests.post(
                    url=api_url,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=60,
                )

                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "2.5")
                    try:
                        retry_delay = min(float(retry_after), 10.0)
                    except ValueError:
                        retry_delay = 2.5
                    logger.warning(
                        f"  OpenRouter rate limited (HTTP 429). Retrying in {retry_delay:g}s "
                        f"(attempt {attempt+1}/{max_retries})..."
                    )
                    time.sleep(retry_delay)
                    continue
                else:
                    break

            # Try configured fallbacks if the primary model is unavailable.
            if response is None or response.status_code != 200:
                for fallback_model in fallback_models:
                    logger.warning(
                        f"  Model '{model}' unavailable. Trying fallback '{fallback_model}'..."
                    )
                    fallback_payload = dict(payload)
                    fallback_payload["model"] = fallback_model
                    if "reasoning" in fallback_payload:
                        del fallback_payload["reasoning"]
                    try:
                        fallback_response = requests.post(
                            url=api_url,
                            headers=headers,
                            data=json.dumps(fallback_payload),
                            timeout=60,
                        )
                    except requests.exceptions.RequestException as ex:
                        logger.error(f"  Fallback '{fallback_model}' failed: {ex}")
                        continue
                    if fallback_response.status_code == 200:
                        response = fallback_response
                        break
                    logger.warning(
                        f"  Fallback '{fallback_model}' returned HTTP {fallback_response.status_code}"
                    )

            if response is None or response.status_code != 200:
                logger.error(
                    f"  OpenRouter API error (HTTP {response.status_code if response else 'None'}): "
                    f"{response.text[:300] if response else 'No response'}"
                )
                continue

            result = response.json()

            # Check for API-level errors
            if "error" in result:
                logger.error(f"  OpenRouter error: {result['error']}")
                continue

            message = result["choices"][0]["message"]
            raw_code = message.get("content") or ""

            # If reasoning details were included in the response, log/preserve them
            if "reasoning_details" in message and message["reasoning_details"]:
                logger.debug(f"  Reasoning details received for candidate {i+1}")

            clean_code = _strip_code_fences(raw_code)

            if not clean_code:
                logger.warning(f"  Candidate {i+1} returned empty code response")
                continue

            candidates.append(clean_code)

            logger.info(f"  Generated candidate {i+1}/{num_candidates} ({len(clean_code)} chars)")

        except requests.exceptions.Timeout:
            logger.error(f"  Request timed out for candidate {i+1}")
            continue
        except requests.exceptions.ConnectionError as e:
            logger.error(f"  Connection error for candidate {i+1}: {e}")
            continue
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"  Failed to parse response for candidate {i+1}: {e}")
            continue
        except Exception as e:
            logger.error(f"  Unexpected error for candidate {i+1}: {e}")
            continue

    logger.info(f"Successfully generated {len(candidates)}/{num_candidates} candidates")
    return candidates


def generate_with_openai(prompt: str, num_candidates: int = None,
                          temperature: float = None,
                          model: str = None) -> List[str]:
    """
    Generate N code candidates using the OpenAI API directly.

    Each call uses the same prompt but with stochastic sampling (high
    temperature) to produce diverse solutions.

    Args:
        prompt: Natural language programming problem description.
        num_candidates: Number of code variants to generate (N).
        temperature: Sampling temperature (higher = more diverse).
        model: OpenAI model identifier.

    Returns:
        List of raw Python code strings.
    """
    try:
        from openai import OpenAI
        from dotenv import load_dotenv
    except ImportError as e:
        logger.error(f"Missing dependency: {e}. Run: pip install openai python-dotenv")
        raise

    # Load environment and config
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Set it in your .env file. "
            "See .env.example for the template."
        )

    if num_candidates is None:
        num_candidates = get_config_value("llm", "num_candidates", 5)
    if temperature is None:
        temperature = get_config_value("llm", "temperature", 0.7)
    if model is None:
        model = get_config_value("llm", "model", "gpt-4o-mini")

    max_tokens = get_config_value("llm", "max_tokens", 2048)
    system_prompt = get_config_value("llm", "system_prompt",
        "You are an expert Python programmer. Generate only the function "
        "implementation as clean, executable Python code. Do not include "
        "explanations, markdown formatting, or code fences. Only output "
        "the raw Python code."
    )

    client = OpenAI(api_key=api_key)
    candidates = []

    logger.info(
        f"Generating {num_candidates} candidates "
        f"(model={model}, temp={temperature})...."
    )

    for i in range(num_candidates):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            raw_code = response.choices[0].message.content or ""
            clean_code = _strip_code_fences(raw_code)

            if not clean_code:
                logger.warning(f"  Candidate {i+1} returned empty code response")
                continue

            candidates.append(clean_code)

            logger.info(f"  Generated candidate {i+1}/{num_candidates} ({len(clean_code)} chars)")

        except Exception as e:
            logger.error(f"  Failed to generate candidate {i+1}: {e}")
            continue

    logger.info(f"Successfully generated {len(candidates)}/{num_candidates} candidates")
    return candidates


def generate_candidates(prompt: str, num_candidates: int = None) -> List[str]:
    """
    Main entry point for code generation.

    Routes to the appropriate provider based on config.
    Supported providers: 'openrouter' (default), 'openai'.

    Args:
        prompt: The programming problem prompt.
        num_candidates: Number of candidates to generate.

    Returns:
        List of Python code strings.
    """
    provider = get_config_value("llm", "provider", "openrouter")

    if provider == "openrouter":
        return generate_with_openrouter(prompt, num_candidates=num_candidates)
    elif provider == "openai":
        return generate_with_openai(prompt, num_candidates=num_candidates)
    else:
        raise ValueError(
            f"Unsupported LLM provider: '{provider}'. "
            f"Currently supported: 'openrouter', 'openai'. "
            f"Set llm.provider in config.yaml."
        )
