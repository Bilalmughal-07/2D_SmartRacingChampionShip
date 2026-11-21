from __future__ import annotations

import heapq


class MinHeap:
    def __init__(self):
        self._heap = []
        self.operations = 0

    def push(self, item):
        heapq.heappush(self._heap, item)
        self.operations += 1

    def pop(self):
        self.operations += 1
        return heapq.heappop(self._heap)

    def peek(self):
        return self._heap[0]

    def __bool__(self):
        return bool(self._heap)

    def __len__(self):
        return len(self._heap)
