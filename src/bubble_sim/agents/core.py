from __future__ import annotations

import json
from typing import Any

SUBMIT_DECISION_TOOL = {
    "type": "function",
    "function": {
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
                "rationale_short": {
                    "type": "string",
                    "description": "A very brief explanation.",
                },
            },
            "required": ["action"],
            "additionalProperties": False,
        },
    },
}

SUBMIT_QUIZ_ANSWER_TOOL = {
    "type": "function",
    "function": {
        "name": "submit_quiz_answer",
        "description": "Submit your answer to the comprehension quiz question.",
        "parameters": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "Your answer to the question (e.g., 'Yes', 'No', '10', '0', etc.)."
                }
            },
            "required": ["answer"],
            "additionalProperties": False,
        },
    },
}

class LabSubjectAgent:
    """Wrapper around an OpenAI Assistant and its Thread for the rigorous lab replication."""

    def __init__(self, client: Any, assistant_id: str, thread_id: str) -> None:
        self.client = client
        self.assistant_id = assistant_id
        self.thread_id = thread_id

    @classmethod
    def create(cls, client: Any, model: str, name: str = "LabSubject") -> LabSubjectAgent:
        """Create a new Assistant and Thread via the OpenAI API (no system instructions)."""
        assistant = client.beta.assistants.create(
            name=name,
            instructions="",  # Instructions are delivered entirely via thread message
            model=model,
            tools=[SUBMIT_DECISION_TOOL, SUBMIT_QUIZ_ANSWER_TOOL],
        )
        thread = client.beta.threads.create()
        return cls(client=client, assistant_id=assistant.id, thread_id=thread.id)

    def send_message_and_get_tool_call(
        self, content: str, tool_name: str, max_retries: int = 2
    ) -> dict[str, Any] | None:
        """
        Sends a message to the thread and expects a specific tool call back.
        Returns the parsed JSON arguments or None on failure.
        """
        self.client.beta.threads.messages.create(
            thread_id=self.thread_id, role="user", content=content
        )

        for attempt in range(max_retries):
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id,
                tool_choice={"type": "function", "function": {"name": tool_name}},
            )

            if run.status == "requires_action":
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                for tool_call in tool_calls:
                    if tool_call.function.name == tool_name:
                        try:
                            args = json.loads(tool_call.function.arguments)
                            
                            # Clean up the run so the thread is unlocked for the next message
                            self.client.beta.threads.runs.cancel(
                                thread_id=self.thread_id, run_id=run.id
                            )
                            # Wait briefly for cancellation to take effect
                            import time
                            time.sleep(1)
                            return args
                        except json.JSONDecodeError:
                            # Cancel incomplete run on format failure to try again
                            self.client.beta.threads.runs.cancel(
                                thread_id=self.thread_id, run_id=run.id
                            )
                            break
            elif run.status in ["failed", "expired", "cancelled"]:
                break

        return None

    def get_decision(self, prompt: str, max_retries: int = 2) -> dict[str, Any] | None:
        """Elicits a buy/no_buy decision."""
        return self.send_message_and_get_tool_call(prompt, "submit_decision", max_retries)

    def get_quiz_answer(self, prompt: str, max_retries: int = 2) -> str | None:
        """Elicits a quiz answer string."""
        args = self.send_message_and_get_tool_call(prompt, "submit_quiz_answer", max_retries)
        if args and "answer" in args:
            return args["answer"]
        return None

    def add_message(self, content: str) -> None:
        """Appends a message without anticipating a tool call (e.g., feedback or prep)."""
        self.client.beta.threads.messages.create(
            thread_id=self.thread_id, role="user", content=content
        )

    def teardown(self) -> None:
        """Clean up resources on OpenAI servers."""
        try:
            self.client.beta.assistants.delete(self.assistant_id)
            self.client.beta.threads.delete(self.thread_id)
        except Exception:
            pass
