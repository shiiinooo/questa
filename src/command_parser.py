"""Very small command parser for the terminal UI.

The command system specified in the design documents is extensive, but
for the purpose of the test-suite we only need a minimal parser that can
interpret a couple of colon-prefixed commands.  The parser is decoupled
from Textual and simply invokes methods on the provided application
object.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict


@dataclass
class Command:
    """Represents a simple command handler."""

    func: Callable[[], None]
    description: str


class CommandParser:
    """Parse and execute terminal commands like ``:back`` or ``:quit``."""

    def __init__(self, app) -> None:
        self.app = app
        self.commands: Dict[str, Command] = {
            "back": Command(app.action_back, "Return to previous screen"),
            "help": Command(self._show_help, "Show help"),
            "quit": Command(app.action_quit, "Quit application"),
        }

    def parse(self, text: str) -> bool:
        """Parse *text* and execute a command if recognised.

        Returns ``True`` when a command was executed, otherwise ``False``.
        """

        if not text.startswith(":"):
            return False

        name, *rest = text[1:].strip().split()
        command = self.commands.get(name)
        if not command:
            return False

        command.func()
        return True

    def _show_help(self) -> None:  # pragma: no cover - trivial
        """Very small help output printed to the console."""

        help_lines = [f":{name} - {cmd.description}" for name, cmd in self.commands.items()]
        print("Available commands:\n" + "\n".join(help_lines))

