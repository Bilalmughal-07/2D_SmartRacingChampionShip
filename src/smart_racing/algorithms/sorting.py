from __future__ import annotations

import heapq


def default_comparator(record: dict) -> tuple:
    lap = record.get("best_fastest_lap")
    return (
        -record.get("total_points", 0),
        -record.get("wins", 0),
        record.get("sum_of_finish_positions", 10**9),
        lap if lap is not None else float("inf"),
        record.get("racer_id", 10**9),
    )


def merge_sort(values: list, key=default_comparator, counter=None) -> list:
    if len(values) <= 1:
        return values.copy()
    mid = len(values) // 2
    left, right = merge_sort(values[:mid], key, counter), merge_sort(values[mid:], key, counter)
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if counter is not None:
            counter[0] += 1
        if key(left[i]) <= key(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    return result + left[i:] + right[j:]


def quick_sort(values: list, key=default_comparator, counter=None) -> list:
    arr = values.copy()

    def partition(lo, hi):
        pivot = key(arr[hi])
        i = lo
        for j in range(lo, hi):
            if counter is not None:
                counter[0] += 1
            if key(arr[j]) <= pivot:
                arr[i], arr[j] = arr[j], arr[i]
                i += 1
        arr[i], arr[hi] = arr[hi], arr[i]
        return i

    def sort(lo, hi):
        if lo < hi:
            p = partition(lo, hi)
            sort(lo, p - 1)
            sort(p + 1, hi)

    sort(0, len(arr) - 1)
    return arr


def heap_sort(values: list, key=default_comparator, counter=None) -> list:
    decorated = [(key(v), i, v) for i, v in enumerate(values)]
    heapq.heapify(decorated)
    result = []
    while decorated:
        result.append(heapq.heappop(decorated)[2])
        if counter is not None:
            counter[0] += 1
    return result


def top_k(values: list, k: int, key=default_comparator) -> list:
    if k <= 0:
        return []
    return heapq.nsmallest(k, values, key=key)
