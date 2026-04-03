"""
workflow_executor.py
--------------------
Simple, synchronous workflow execution engine.

Supported step types:
    - "log"      → prints a message to stdout
    - "response" → stores a message as the final output

Template variables:
    Use {{input.key}} or {{input.nested.key}} in any string field of a step.
    They are resolved against `input_data` before the handler runs.

    Example:
        step       = {"type": "log", "message": "Hello {{input.name}}"}
        input_data = {"name": "World"}
        result     → message printed: "Hello World"

Future step types can be registered via WorkflowExecutor.register_handler().
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Template engine  (stdlib only — no external dependencies)
# ---------------------------------------------------------------------------

# Matches {{ any.key.path }} with optional surrounding spaces
_TEMPLATE_RE = re.compile(r"\{\{\s*([^}\s]+)\s*\}\}")


def render_template(text: str, context: dict) -> str:
    """Reusable function to render strings with variables from a dict context.

    Supports dot-notation for nested keys across any domain in the context:
    ``{{input.user.name}}`` or ``{{steps.category}}``.
    Unknown or missing keys are replaced with an empty string.
    """
    if not isinstance(text, str):
        return text

    def _replacer(match: re.Match) -> str:
        key_path = match.group(1).split(".")
        value: Any = context
        for key in key_path:
            if isinstance(value, dict):
                value = value.get(key, "")
            else:
                value = ""
                break
        return str(value) if value != "" else ""

    return _TEMPLATE_RE.sub(_replacer, text)


def _resolve_step(step: dict, context_data: dict) -> dict:
    """Return a shallow copy of *step* with every string value template-resolved.

    Non-string values (numbers, booleans, nested dicts, lists) are left unchanged.
    """
    resolved: dict = {}
    for key, val in step.items():
        resolved[key] = render_template(val, context_data) if isinstance(val, str) else val
    return resolved


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class StepResult:
    """Output produced by a single executed step."""

    step_index: int
    step_type: str
    success: bool
    output: Any = None
    error: str | None = None


@dataclass
class ExecutionResult:
    """Aggregated result of a full workflow execution."""

    workflow_id: Any  # uuid.UUID when coming from DB, or None in tests
    steps_total: int
    steps_executed: int
    success: bool = True
    error_message: str | None = None
    results: list[StepResult] = field(default_factory=list)
    response: str | None = None  # last "response" step wins


# ---------------------------------------------------------------------------
# Step handlers
# ---------------------------------------------------------------------------


def _handle_log(step: dict, index: int, input_data: dict | None = None) -> StepResult:
    """Prints `message` to stdout/logger and returns success.

    By the time this handler runs, ``step["message"]`` is already resolved —
    any ``{{input.*}}`` placeholders have been replaced by ``_execute_step``.
    """
    message = step.get("message", "")
    print(f"[workflow:log] {message}")
    logger.info("[workflow:log] step=%d message=%r", index, message)
    return StepResult(step_index=index, step_type="log", success=True, output=message)


def _handle_response(step: dict, index: int, input_data: dict | None = None) -> StepResult:
    """Captures `message` as the workflow output."""
    message = step.get("message", "")
    return StepResult(
        step_index=index, step_type="response", success=True, output=message
    )


def _handle_ai_classify(step: dict, index: int, input_data: dict | None = None) -> StepResult:
    """Uses AIService to classify an input text into discrete labels."""
    from app.services.ai_service import AIService

    text = step.get("input", "")
    labels = step.get("labels", [])

    if not isinstance(labels, list) or not labels:
        return StepResult(
            step_index=index,
            step_type="ai_classify",
            success=False,
            error="Invalid or missing 'labels' list in step definition.",
        )

    try:
        service = AIService()
        classification = service.classify(text, labels)
        logger.info("[workflow:ai_classify] step=%d result=%r", index, classification)
        return StepResult(
            step_index=index, step_type="ai_classify", success=True, output=classification
        )
    except Exception as e:
        logger.exception("AI Classification failed")
        return StepResult(
            step_index=index, step_type="ai_classify", success=False, error=str(e)
        )


def _handle_ai_generate(step: dict, index: int, input_data: dict | None = None) -> StepResult:
    """Uses AIService to generate text based on a prompt."""
    from app.services.ai_service import AIService

    prompt = step.get("prompt", "")

    if not prompt:
        return StepResult(
            step_index=index,
            step_type="ai_generate",
            success=False,
            error="Missing 'prompt' string in step definition.",
        )

    try:
        service = AIService()
        reply = service.generate(prompt)
        logger.info("[workflow:ai_generate] step=%d length=%d", index, len(reply))
        return StepResult(
            step_index=index, step_type="ai_generate", success=True, output=reply
        )
    except Exception as e:
        logger.exception("AI Generation failed")
        return StepResult(
            step_index=index, step_type="ai_generate", success=False, error=str(e)
        )


def _evaluate_expression(expression: str) -> bool:
    """Helper function to evaluate simple string expressions securely without eval()."""
    if " == " in expression:
        left, right = expression.split(" == ", 1)
        return left.strip().strip("'\"") == right.strip().strip("'\"")
    if " != " in expression:
        left, right = expression.split(" != ", 1)
        return left.strip().strip("'\"") != right.strip().strip("'\"")
    return False


def _handle_condition(step: dict, index: int, input_data: dict | None = None) -> StepResult:
    """Evaluates an expression and prepares recursive branch substeps mapping."""
    expression = step.get("expression", "")
    is_true = _evaluate_expression(expression)

    branch = "then" if is_true else "else"
    substeps = step.get(branch, [])

    output = {
        "expression": expression,
        "evaluated": is_true,
        "branch": branch,
        "substeps": substeps,
    }

    logger.info("[workflow:condition] step=%d eval=%s branch=%s", index, is_true, branch)
    return StepResult(step_index=index, step_type="condition", success=True, output=output)


def _handle_fail(step: dict, index: int, input_data: dict | None = None) -> StepResult:
    """Intentionally raises an exception to simulate fatal errors and test retries."""
    message = step.get("message", "Intentional failure triggered by 'fail' step")
    raise RuntimeError(message)


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------

# Maps step type → handler callable
_DEFAULT_HANDLERS: dict[str, Any] = {
    "log": _handle_log,
    "response": _handle_response,
    "ai_classify": _handle_ai_classify,
    "ai_generate": _handle_ai_generate,
    "condition": _handle_condition,
    "fail": _handle_fail,
}


class WorkflowExecutor:
    """
    Executes a workflow definition synchronously, step by step.

    Usage::

        executor = WorkflowExecutor()

        # Basic execution
        result = executor.run(definition=workflow.definition, workflow_id=workflow.id)

        # With external input — {{input.*}} variables become available in all steps
        result = executor.run(
            definition=workflow.definition,
            workflow_id=workflow.id,
            input_data={"message": "hi", "user": {"name": "Ana"}},
        )
    """

    def __init__(self) -> None:
        self._handlers: dict[str, Any] = dict(_DEFAULT_HANDLERS)

    def register_handler(self, step_type: str, handler: Any) -> None:
        """Register a custom step handler at runtime."""
        self._handlers[step_type] = handler

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        definition: dict,
        workflow_id: Any = None,
        input_data: dict | None = None,
    ) -> ExecutionResult:
        """
        Execute all steps defined in ``definition["steps"]`` sequentially.

        Args:
            definition:  The workflow's JSON definition dict.
            workflow_id: Optional identifier used only for traceability.
            input_data:  External data injected into steps. String fields in each
                         step may reference it via ``{{input.key}}`` placeholders.

        Returns:
            ExecutionResult with per-step results and the final response.
        """
        steps_queue: list[dict] = definition.get("steps", []).copy()
        result = ExecutionResult(
            workflow_id=workflow_id,
            steps_total=len(steps_queue),
            steps_executed=0,
        )

        steps_data: dict[str, Any] = {}
        context_data = {
            "input": input_data or {},
            "steps": steps_data,
        }

        try:
            while steps_queue:
                step = steps_queue.pop(0)
                index = result.steps_executed

                step_result = self._execute_step(step, index, context_data=context_data)
                result.results.append(step_result)
                result.steps_executed += 1

                if not step_result.success:
                    result.success = False
                    result.error_message = step_result.error
                    logger.warning(
                        "Workflow %s aborted at step %d: %s",
                        workflow_id,
                        index,
                        step_result.error,
                    )
                    break  # stop on first failure

                # Handling control flow injections (like condition flattening)
                if step_result.step_type == "condition":
                    substeps = step_result.output.get("substeps", [])
                    if substeps:
                        # Inject steps at the front of the queue to execute them immediately
                        steps_queue = substeps + steps_queue
                        result.steps_total += len(substeps)

                # Store step output if output_key is defined
                output_key = step.get("output_key")
                if output_key and isinstance(output_key, str):
                    steps_data[output_key] = step_result.output

                if step_result.step_type == "response":
                    result.response = step_result.output
        except Exception as e:
            logger.exception("Fatal error during execution of workflow %s", workflow_id)
            result.success = False
            result.error_message = str(e)

        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _execute_step(
        self, step: dict, index: int, context_data: dict | None = None
    ) -> StepResult:
        step_type = step.get("type", "")
        handler = self._handlers.get(step_type)

        if handler is None:
            error = f"Unknown step type: {step_type!r}"
            logger.error("step=%d %s", index, error)
            return StepResult(
                step_index=index,
                step_type=step_type,
                success=False,
                error=error,
            )

        # Resolve {{input.*}} and {{steps.*}} templates BEFORE passing step to the handler.
        # Handlers receive already-interpolated values — they need no template logic.
        resolved_step = _resolve_step(step, context_data or {"input": {}, "steps": {}})

        try:
            # We preserve backward compatibility: handlers expect native input_data
            input_dict = context_data.get("input", {}) if context_data else {}
            return handler(resolved_step, index, input_dict)
        except Exception as exc:  # noqa: BLE001
            error = f"Step {index} ({step_type!r}) raised: {exc}"
            logger.exception(error)
            return StepResult(
                step_index=index,
                step_type=step_type,
                success=False,
                error=error,
            )
