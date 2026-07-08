from collections import defaultdict
from threading import Lock


class MemoryService:
    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self._messages: dict[str, list[dict[str, str]]] = defaultdict(list)
        self._lock = Lock()

    def add_user_message(self, conversation_id: str, content: str):
        self._add_message(conversation_id, "user", content)

    def add_assistant_message(self, conversation_id: str, content: str) -> None:
        self._add_message(conversation_id, "assistant", content)

    def get_message(self, conversation_id: str) -> list[dict[str, str]]:
        with self._lock:
            return self._messages[conversation_id]

    def clear(self, conversation_id: str) -> None:
        with self._lock:
            self._messages.pop(conversation_id)

    def _add_message(self, conversation_id: str, role: str, content: str) -> None:
        with self._lock:
            self._messages[conversation_id].append({"role": role, "content": content})
            if len(self._messages[conversation_id]) > self.max_messages:
                self._messages[conversation_id] = self._messages[conversation_id][
                    -self.max_messages:
                ]


if __name__ == "__main__":
    mem = MemoryService()
    mem.add_user_message("1", "hello")
    print(mem.get_message("1"))
