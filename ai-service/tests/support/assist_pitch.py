"""Driving the generation layer offline. Delivered by C30b.

**The fake goes in at the provider's door and not above it.** `scripted_client` builds the
real `LiteLlmAssistClient` with a scripted `complete`, so every test still exercises the real
parsing, the real timeout, the real usage extraction and the real accumulation — only the
socket is replaced. A stand-in for the whole client would have tested the test.

Lives in `support/` rather than in a `conftest.py` for the reason `support/settings.py` already
records: `conftest.py` is pytest's fixture mechanism and not an importable module, so anything
a test module needs at import time has to live here.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping, Sequence
from typing import Any

from jbg_ai.assist.llm import LiteLlmAssistClient, ProviderReply, TokenUsage
from jbg_ai.assist.prompt import QUERY_CLOSE, QUERY_OPEN
from jbg_ai.assist.schema import AssistPitch, UsedCitation

#: The usage one scripted call reports unless a test says otherwise. Of the order of the real
#: thing — ~1.500 tokens in, ~300 out — so a cost assertion reads like a cost.
DEFAULT_USAGE = TokenUsage(
    prompt_tokens=1500, completion_tokens=300, total_tokens=1800, calls=1
)


def pitch(text: str, *used: tuple[str, str]) -> AssistPitch:
    """An `AssistPitch` from prose plus `(citation_id, supported_claim)` pairs."""
    return AssistPitch(
        pitch=text,
        used=[
            UsedCitation(citation_id=identifier, supported_claim=claim)
            for identifier, claim in used
        ],
    )


class ScriptedProvider:
    """One scripted `complete`: it records what it was handed and answers in order.

    The last entry of the script repeats, so a test that only cares about the first reply does
    not have to state a second — and a test that asserts a **ceiling** on the number of calls
    is asserting something the fake would happily exceed.
    """

    def __init__(
        self,
        script: Sequence[AssistPitch | BaseException | str],
        *,
        usage: Sequence[TokenUsage] | None = None,
        delay: float = 0.0,
    ) -> None:
        self._script = list(script)
        self._usage = list(usage) if usage is not None else None
        self._delay = delay
        self.calls: list[list[dict[str, str]]] = []

    @property
    def call_count(self) -> int:
        return len(self.calls)

    def messages_of(self, index: int) -> list[dict[str, str]]:
        return self.calls[index]

    def system_of(self, index: int) -> str:
        return self.calls[index][0]["content"]

    def user_of(self, index: int) -> str:
        return self.calls[index][1]["content"]

    async def __call__(self, messages: Sequence[Mapping[str, str]]) -> ProviderReply:
        self.calls.append([dict(message) for message in messages])
        if self._delay:
            await asyncio.sleep(self._delay)
        index = min(len(self.calls) - 1, len(self._script) - 1)
        reply = self._script[index]
        if callable(reply) and not isinstance(reply, BaseException):
            # A reply that depends on what was offered. The mode with a question retrieves its
            # own fragments, so a test cannot know their identifiers in advance without
            # restating the retrieval — and restating it would be testing the test.
            reply = reply(self.calls[-1])
        if isinstance(reply, BaseException):
            raise reply
        usage = (
            self._usage[min(len(self.calls) - 1, len(self._usage) - 1)]
            if self._usage
            else DEFAULT_USAGE
        )
        content = reply if isinstance(reply, str) else reply.model_dump_json()
        return ProviderReply(content=content, usage=usage)


def scripted_client(
    *script: AssistPitch | BaseException | str,
    usage: Sequence[TokenUsage] | None = None,
    delay: float = 0.0,
    timeout: float | None = None,
) -> tuple[LiteLlmAssistClient, ScriptedProvider]:
    """The real client over a scripted provider. Returns both, so calls can be counted."""
    provider = ScriptedProvider(script, usage=usage, delay=delay)
    kwargs: dict[str, Any] = {
        "api_key": "sk-test",
        "model": "fake/pitch-model",
        "complete": provider,
    }
    if timeout is not None:
        kwargs["timeout"] = timeout
    return LiteLlmAssistClient(**kwargs), provider


class RefusingProvider:
    """A `complete` that fails the test if it is ever called. For the two cuts."""

    def __init__(self) -> None:
        self.calls = 0

    async def __call__(self, messages: Sequence[Mapping[str, str]]) -> ProviderReply:
        self.calls += 1
        raise AssertionError(
            "no language model provider call may be made on this path"
        )


def refusing_client() -> tuple[LiteLlmAssistClient, RefusingProvider]:
    provider = RefusingProvider()
    return (
        LiteLlmAssistClient(api_key="sk-test", model="fake/pitch-model", complete=provider),
        provider,
    )


def query_block(user_message: str) -> str:
    """What travelled inside the delimited data block of a user message, if anything."""
    if QUERY_OPEN not in user_message:
        return ""
    start = user_message.index(QUERY_OPEN) + len(QUERY_OPEN)
    return user_message[start : user_message.index(QUERY_CLOSE)].strip()


def data_block(user_message: str) -> dict[str, Any]:
    """The JSON object of a user message, parsed back. Used to read what was handed over.

    **The first `{` is not necessarily the one that opens it**, which was true by accident
    until `assist/v5`. The task sections of the free query now name the placeholders they
    forbid — «no escribas `{{price}}` ni `{{stock}}`» — and a task section is part of the user
    message, so a walk anchored on the first brace lands inside `{{price}}`, balances there and
    hands `json.loads` something that is not JSON.

    Each candidate opening is therefore tried in turn and the first one that parses wins. The
    production side never does this — it builds the message and never reads it back — so the
    fragility was only ever the helper's.
    """
    for opening, char in enumerate(user_message):
        if char != "{":
            continue
        depth = 0
        for offset, inner in enumerate(user_message[opening:], start=opening):
            depth += (inner == "{") - (inner == "}")
            if depth == 0:
                try:
                    return json.loads(user_message[opening : offset + 1])
                except json.JSONDecodeError:
                    break
    raise AssertionError("the user message carries no complete JSON object")


def citing_what_was_offered(text: str, span: str, *, count: int = 1):
    """A scripted reply that cites whatever the payload actually offered.

    The mode with a question retrieves its own fragments, so a test cannot name their
    identifiers in advance without restating the retrieval — and restating it would be testing
    the test. `span` must occur literally in `text`, which is what correspondence checks.
    """

    def build(messages: Sequence[Mapping[str, str]]) -> AssistPitch:
        offered = [item["cita"] for item in data_block(messages[1]["content"])["corpus"]]
        return pitch(text, *[(item, span) for item in offered[:count]])

    return build
