from typing import Protocol

class MessageSource(Protocol):
    def next_message(self) -> str | None:...

class CLIMessageSource(MessageSource):
    def next_message(self) -> str | None:
        try:
            line = input("> ").strip()
            return None if line.lower() == "quit" else line
        except EOFError:
            return None