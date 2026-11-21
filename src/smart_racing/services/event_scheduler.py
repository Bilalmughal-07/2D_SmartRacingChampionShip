from __future__ import annotations

import heapq

from smart_racing.model.events import Event


class EventScheduler:
    def __init__(self):
        self.heap: list[tuple[tuple[float, int, int], int]] = []
        self.events: dict[int, Event] = {}
        self.sequence = 0
        self.heap_operations = 0

    def schedule(self, event: Event) -> None:
        self.sequence = max(self.sequence, event.insertion_sequence + 1)
        self.events[event.event_id] = event
        heapq.heappush(self.heap, (event.key(), event.event_id))
        self.heap_operations += 1

    def cancel(self, event_id: int) -> None:
        if event_id in self.events:
            self.events[event_id].cancelled = True

    def pop_due(self, now: float) -> list[Event]:
        due = []
        while self.heap and self.heap[0][0][0] <= now + 1e-9:
            _, event_id = heapq.heappop(self.heap)
            self.heap_operations += 1
            event = self.events[event_id]
            if not event.cancelled:
                due.append(event)
        return due

    def next_time(self) -> float | None:
        return self.heap[0][0][0] if self.heap else None
