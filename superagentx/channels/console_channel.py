import asyncio
import json
import logging
import sys
from typing import Callable, Any

from superagentx.channels.base import HumanApprovalChannel

logger = logging.getLogger(__name__)


def _logger_is_configured(log: logging.Logger) -> bool:
    """
    Returns True if logging is configured with at least one handler.
    """
    if log.handlers:
        return True

    root = logging.getLogger()
    return bool(root.handlers)


def _print_colored_console(message: str, *, color: str = "cyan") -> None:
    COLORS = {
        "cyan": "\033[96m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "reset": "\033[0m",
    }

    color_code = COLORS.get(color, "")
    reset = COLORS["reset"]

    sys.stdout.write(f"{color_code}{message}{reset}\n")
    sys.stdout.flush()

def safe_format_result(result: Any) -> Any:
    try:
        return json.loads(result) if isinstance(result, str) else result
    except Exception as e:
        return str(result)

class ConsoleApprovalChannel(HumanApprovalChannel):

    async def request_approval(
        self,
        *,
        agent_id: str,
        agent_name: str,
        query: str,
        pre_result,
        pipe_id=None,
        conversation_id=None
    ) -> bool:
        loop = asyncio.get_running_loop()

        header = "=" * 60
        content = (
            f"{header}\n"
            f" HUMAN APPROVAL REQUIRED\n"
            f" Agent : {agent_name} ({agent_id})\n"
            f" Query : {query}\n"
            f" Result: {safe_format_result(pre_result)}\n"
            f"{header}"
        )

        if _logger_is_configured(logger):
            logger.info("\n%s", content)
        else:
            _print_colored_console(content, color="yellow")

        ask: Callable[[], str] = lambda: input(
            "\033[92mApprove this execution? (y/n): \033[0m"
        ).strip().lower()

        try:
            answer = await asyncio.wait_for(
                loop.run_in_executor(None, ask),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            if _logger_is_configured(logger):
                logger.warning("Human approval timed out")
            else:
                _print_colored_console(
                    "Human approval timed out",
                    color="red"
                )
            return False

        return answer == "y"
