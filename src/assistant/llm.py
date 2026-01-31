from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from openai import OpenAI

from assistant.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

LOGGER = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, api_key: str, model: str, transcribe_model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._transcribe_model = transcribe_model

    def extract(self, message: str) -> Dict[str, Any]:
        prompt = USER_PROMPT_TEMPLATE.format(message=message)
        response = self._client.responses.create(
            model=self._model,
            response_format={"type": "json_object"},
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        text = _response_text(response)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            LOGGER.warning("Failed to parse LLM JSON output")
            return {"summary": "", "items": [], "questions": []}

    def transcribe(self, file_path: str) -> str:
        with open(file_path, "rb") as audio_file:
            transcript = self._client.audio.transcriptions.create(
                model=self._transcribe_model,
                file=audio_file,
            )
        return getattr(transcript, "text", "") or ""


def _response_text(response: Any) -> str:
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text
    try:
        return response.output[0].content[0].text
    except (AttributeError, IndexError, TypeError):
        return ""
