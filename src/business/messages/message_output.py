from typing import Protocol

class MessageOutput(Protocol):
    def display(self, msg: str) -> None: ...

class CLIMessageOutput(MessageOutput):
    def display(self, msg):
        print(msg)
