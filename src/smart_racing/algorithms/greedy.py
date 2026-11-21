from __future__ import annotations

from smart_racing.algorithms.dynamic_programming import DPResult


def greedy_knapsack(items: list[dict], budget: int) -> DPResult:
    selected = []
    remaining = budget
    zero_positive = [i for i in items if int(i["cost"]) == 0 and float(i["benefit"]) > 0]
    for item in sorted(zero_positive, key=lambda x: int(x.get("id", 0))):
        selected.append(item)
    candidates = [i for i in items if i not in zero_positive and int(i["cost"]) > 0]
    candidates.sort(key=lambda x: (-float(x["benefit"]) / int(x["cost"]), int(x.get("id", 0))))
    value = sum(float(i["benefit"]) for i in selected)
    for item in candidates:
        cost = int(item["cost"])
        if cost <= remaining:
            selected.append(item)
            remaining -= cost
            value += float(item["benefit"])
    return DPResult(
        value,
        selected,
        states=len(items),
        details={"remaining_budget": remaining, "heuristic": True},
    )
