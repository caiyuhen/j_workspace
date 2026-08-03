class EventBroker:
    def __init__(self) -> None:
        self._events: list[dict] = []

    def publish(self, event_type: str, payload: dict) -> None:
        self._events.append({"event_type": event_type, "payload": payload})

    def drain(self) -> list[dict]:
        events = list(self._events)
        self._events.clear()
        return events


broker = EventBroker()
