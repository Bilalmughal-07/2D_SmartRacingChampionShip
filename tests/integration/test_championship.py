from smart_racing.model.race import ChampionshipEntry
from smart_racing.services.scoring import rank_entries, top_k_entries


def test_common_comparator_and_final_id_tie_break():
    entries = [ChampionshipEntry(2, "B", 25, 1, 1, 50.0), ChampionshipEntry(1, "A", 25, 1, 1, 50.0)]
    assert [x.racer_id for x in rank_entries(entries, "merge")] == [1, 2]
    assert [x.racer_id for x in rank_entries(entries, "quick")] == [1, 2]
    assert [x.racer_id for x in rank_entries(entries, "heap")] == [1, 2]
    assert [x.racer_id for x in top_k_entries(entries, 1)] == [1]
