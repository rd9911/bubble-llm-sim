from __future__ import annotations

import json
import time
from typing import Any

# ---------------------------------------------------------------------------
# Tool definitions – Responses API format (flat: name/description/parameters
# at the top level, NOT nested inside a "function" key).
# ---------------------------------------------------------------------------

SUBMIT_DECISION_TOOL = {
    "type": "function",
    "name": "submit_decision",
    "description": "Submit your final decision to buy or not buy.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "Your choice: either 'buy' or 'no_buy'.",
                "enum": ["buy", "no_buy"],
            },
            "confidence": {
                "type": "number",
                "description": "Your confidence level between 0.0 and 1.0.",
            },
            "belief_success_resale": {
                "type": "number",
                "description": "Your estimated probability between 0.0 and 1.0 that the next participant will buy if you do.",
            },
            "reasoning": {
                "type": "string",
                "description": "Your full chain-of-thought explanation.",
            },
            "rationale_short": {
                "type": "string",
                "description": "A very brief explanation.",
            },
        },
        "required": ["action", "confidence", "belief_success_resale", "reasoning", "rationale_short"],
        "additionalProperties": False,
    },
}

SUBMIT_QUIZ_ANSWERS_TOOL = {
    "type": "function",
    "name": "submit_quiz_answers",
    "description": "Submit your answers to all comprehension quiz questions at once.",
    "parameters": {
        "type": "object",
        "properties": {
            "reasoning": {
                "type": "string",
                "description": "Think step-by-step through the rules for all questions to arrive at the correct answers."
            },
            "answers": {
                "type": "array",
                "description": "Your answers for each question.",
                "items": {
                    "type": "object",
                    "properties": {
                        "question_id": {
                            "type": "string",
                            "description": "The ID of the question (e.g., 'q1')."
                        },
                        "rationale": {
                            "type": "string",
                            "description": "Your step-by-step reasoning for this specific question."
                        },
                        "answer": {
                            "type": "string",
                            "description": "Your chosen answer string."
                        }
                    },
                    "required": ["question_id", "rationale", "answer"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["reasoning", "answers"],
        "additionalProperties": False,
    },
}


class LabSubjectAgent:
    """
    Wrapper around the OpenAI Responses API with a persistent Conversation
    for rigorous lab replication.

    Replaces the deprecated Assistants API (beta.assistants / beta.threads /
    threads.runs). The public interface (get_decision, get_quiz_answer,
    add_message, teardown) is unchanged so the rest of the codebase requires
    no modifications.

    Concept mapping:
        Assistant object  →  inline `instructions` on every responses.create()
        Thread            →  Conversation  (client.conversations.create/delete)
        Run + poll loop   →  client.responses.create()  (synchronous)
        Run Step          →  item in response.output
    """

    def __init__(
        self,
        client: Any,
        conversation_id: str,
        instructions: str,
        model: str,
        response_kwargs: dict[str, Any],
        archetype_id: str | None = None,
    ) -> None:
        self.client = client
        self.conversation_id = conversation_id
        self.instructions = instructions
        self.model = model
        self.response_kwargs = response_kwargs
        self.archetype_id = archetype_id

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        client: Any,
        model: str,
        name: str = "LabSubject",
        instructions: str = "",
        archetype_id: str | None = None,
        **kwargs,
    ) -> LabSubjectAgent:
        """
        Create a new Conversation (persistent context store) and configure
        response-level parameters.
        """
        # Server-side conversation holds all turns for this agent
        conversation = client.conversations.create()

        response_kwargs: dict[str, Any] = {
            "temperature": kwargs.get("temperature", 1.0),
        }
        if "top_p" in kwargs:
            response_kwargs["top_p"] = kwargs["top_p"]
        if "max_completion_tokens" in kwargs:
            # Responses API uses max_output_tokens
            response_kwargs["max_output_tokens"] = kwargs["max_completion_tokens"]
        if "reasoning_effort" in kwargs:
            # Responses API surfaces reasoning control via the `reasoning` dict
            response_kwargs["reasoning"] = {"effort": kwargs["reasoning_effort"]}

        return cls(
            client=client,
            conversation_id=conversation.id,
            instructions=instructions,
            model=model,
            response_kwargs=response_kwargs,
            archetype_id=archetype_id,
        )

    # ------------------------------------------------------------------
    # Core communication
    # ------------------------------------------------------------------

    def send_message_and_get_tool_call(
        self, content: str, tool_name: str, max_retries: int = 2
    ) -> dict[str, Any] | None:
        """
        Send a user message inside the persistent Conversation and force the
        model to respond with a specific tool call. Returns the parsed JSON
        arguments or None on failure.

        The Responses API is fully synchronous — no polling loop needed.
        Conversation history is managed server-side via conversation_id.
        """
        for attempt in range(max_retries):
            try:
                response = self.client.responses.create(
                    model=self.model,
                    instructions=self.instructions,
                    input=[{"role": "user", "content": content}],
                    tools=[SUBMIT_DECISION_TOOL, SUBMIT_QUIZ_ANSWERS_TOOL],
                    # Responses API tool_choice: {"type": "function", "name": "..."}
                    tool_choice={
                        "type": "function",
                        "name": tool_name,
                    },
                    conversation=self.conversation_id,
                    **self.response_kwargs,
                )
            except Exception as e:
                print(f"[LabSubjectAgent] API error on attempt {attempt+1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                continue

            # Walk output items to find the forced tool call
            for item in response.output:
                if getattr(item, "type", None) == "function_call" and getattr(item, "name", None) == tool_name:
                    try:
                        args = json.loads(item.arguments)
                    except (json.JSONDecodeError, AttributeError):
                        break  # retry

                    # Extract reasoning tokens from usage metadata
                    usage = getattr(response, "usage", None)
                    if usage is not None:
                        details = getattr(usage, "output_tokens_details", None)
                        args["_reasoning_tokens"] = getattr(details, "reasoning_tokens", 0)
                    else:
                        args["_reasoning_tokens"] = 0

                    # Submit tool output back to the conversation so it's
                    # in a clean state for the next call. Without this, any
                    # subsequent responses.create() on the same conversation
                    # will fail with "No tool output found for function call".
                    try:
                        call_id = getattr(item, "call_id", None)
                        if call_id:
                            for cleanup_attempt in range(3):
                                try:
                                    self.client.conversations.items.create(
                                        self.conversation_id,
                                        items=[
                                            {
                                                "type": "function_call_output",
                                                "call_id": call_id,
                                                "output": json.dumps({"status": "recorded"}),
                                            }
                                        ],
                                    )
                                    break
                                except Exception as cleanup_err:
                                    if "conversation_locked" in str(cleanup_err) and cleanup_attempt < 2:
                                        time.sleep(2)
                                        continue
                                    raise cleanup_err
                    except Exception:
                        pass  # non-fatal; best-effort cleanup

                    return args

        return None

    def get_decision(self, prompt: str, max_retries: int = 2) -> dict[str, Any] | None:
        """Elicits a buy/no_buy decision."""
        return self.send_message_and_get_tool_call(prompt, "submit_decision", max_retries)

    def get_quiz_answers(self, prompt: str, max_retries: int = 2) -> dict[str, Any] | None:
        """Elicits quiz answers."""
        return self.send_message_and_get_tool_call(prompt, "submit_quiz_answers", max_retries)

    def add_message(self, content: str, max_retries: int = 3) -> None:
        """
        Appends a user message to the Conversation without expecting a tool
        call back (used for feedback or preparatory prompts between periods).
        """
        for attempt in range(max_retries):
            try:
                self.client.conversations.items.create(
                    self.conversation_id,
                    items=[
                        {
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": content}],
                        }
                    ],
                )
                return
            except Exception as e:
                if "conversation_locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                print(f"[LabSubjectAgent] Failed to add message: {e}")
                raise

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def teardown(self) -> None:
        """Delete the server-side Conversation to free resources."""
        try:
            self.client.conversations.delete(self.conversation_id)
        except Exception:
            pass
