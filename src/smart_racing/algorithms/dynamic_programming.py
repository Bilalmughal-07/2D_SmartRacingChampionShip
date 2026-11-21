from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DPResult:
    value: float
    selected: list
    feasible: bool = True
    states: int = 0
    details: dict = None


def knapsack_01(items: list[dict], budget: int) -> DPResult:
    if budget < 0:
        raise ValueError("budget must be non-negative")
    dp = [[0.0] * (budget + 1) for _ in range(len(items) + 1)]
    for i, item in enumerate(items, 1):
        cost, benefit = int(item["cost"]), float(item["benefit"])
        for b in range(budget + 1):
            dp[i][b] = dp[i - 1][b]
            if cost <= b:
                dp[i][b] = max(dp[i][b], dp[i - 1][b - cost] + benefit)
    selected = []
    b = budget
    for i in range(len(items), 0, -1):
        if dp[i][b] != dp[i - 1][b]:
            selected.append(items[i - 1])
            b -= int(items[i - 1]["cost"])
    selected.reverse()
    return DPResult(
        dp[-1][-1], selected, states=(len(items) + 1) * (budget + 1), details={"budget": budget}
    )


def refuel_dp(
    stops: list[dict],
    demands: list[int],
    capacity: int,
    starting_fuel: int,
    purchase_cap: int = 40,
    stop_time: float = 3.0,
) -> DPResult:
    if len(demands) != len(stops):
        raise ValueError("stops must contain one record for each route leg")
    inf = float("inf")
    dp = [[inf] * (capacity + 1) for _ in range(len(demands) + 1)]
    choices: dict[tuple[int, int], tuple[int, int]] = {}
    dp[0][min(capacity, starting_fuel)] = 0.0
    for j, demand in enumerate(demands):
        for fuel in range(capacity + 1):
            if dp[j][fuel] == inf:
                continue
            max_buy = min(capacity - fuel, purchase_cap) if stops[j].get("available", False) else 0
            for buy in range(max_buy + 1):
                if fuel + buy < demand:
                    continue
                next_fuel = fuel + buy - demand
                candidate = dp[j][fuel] + (stop_time if buy > 0 else 0.0)
                if candidate < dp[j + 1][next_fuel]:
                    dp[j + 1][next_fuel] = candidate
                    choices[(j + 1, next_fuel)] = (fuel, buy)
    best_fuel, best = min(enumerate(dp[-1]), key=lambda pair: pair[1])
    if best == inf:
        return DPResult(inf, [], feasible=False, states=(len(demands) + 1) * (capacity + 1))
    plan = []
    state = (len(demands), best_fuel)
    while state[0] > 0:
        previous_fuel, buy = choices[state]
        plan.append({"stop_index": state[0] - 1, "buy": buy, "arrival_fuel": previous_fuel})
        state = (state[0] - 1, previous_fuel)
    plan.reverse()
    return DPResult(
        best,
        plan,
        states=(len(demands) + 1) * (capacity + 1),
        details={"destination_fuel": best_fuel},
    )
