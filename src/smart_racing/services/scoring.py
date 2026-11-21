from __future__ import annotations

from smart_racing.algorithms.sorting import heap_sort, merge_sort, quick_sort, top_k
from smart_racing.model.race import ChampionshipEntry, RaceResult

POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]


def points_for_position(position: int) -> int:
    return POINTS[position - 1] if 1 <= position <= len(POINTS) else 0


def championship_key(entry: ChampionshipEntry) -> tuple:
    return (
        -entry.total_points,
        -entry.wins,
        entry.sum_of_finish_positions,
        entry.best_fastest_lap if entry.best_fastest_lap is not None else float("inf"),
        entry.racer_id,
    )


def record_results(entries: dict[int, ChampionshipEntry], results: list[RaceResult]) -> None:
    for result in results:
        entry = entries[result.racer_id]
        entry.total_points += result.points_awarded
        if result.finish_position == 1 and not result.dnf:
            entry.wins += 1
        entry.sum_of_finish_positions += result.finish_position
        if result.fastest_lap is not None and (
            entry.best_fastest_lap is None or result.fastest_lap < entry.best_fastest_lap
        ):
            entry.best_fastest_lap = result.fastest_lap


def rank_entries(
    entries: list[ChampionshipEntry], method: str = "merge"
) -> list[ChampionshipEntry]:
    values = [e.__dict__.copy() for e in entries]
    if method == "merge":
        return [
            ChampionshipEntry(**x)
            for x in merge_sort(
                values,
                key=lambda x: (
                    -x["total_points"],
                    -x["wins"],
                    x["sum_of_finish_positions"],
                    x["best_fastest_lap"] if x["best_fastest_lap"] is not None else float("inf"),
                    x["racer_id"],
                ),
            )
        ]
    if method == "quick":
        return [
            ChampionshipEntry(**x)
            for x in quick_sort(
                values,
                key=lambda x: (
                    -x["total_points"],
                    -x["wins"],
                    x["sum_of_finish_positions"],
                    x["best_fastest_lap"] if x["best_fastest_lap"] is not None else float("inf"),
                    x["racer_id"],
                ),
            )
        ]
    if method == "heap":
        return [
            ChampionshipEntry(**x)
            for x in heap_sort(
                values,
                key=lambda x: (
                    -x["total_points"],
                    -x["wins"],
                    x["sum_of_finish_positions"],
                    x["best_fastest_lap"] if x["best_fastest_lap"] is not None else float("inf"),
                    x["racer_id"],
                ),
            )
        ]
    raise ValueError("method must be merge, quick, or heap")


def top_k_entries(entries: list[ChampionshipEntry], k: int) -> list[ChampionshipEntry]:
    return top_k(entries, k, key=championship_key)
