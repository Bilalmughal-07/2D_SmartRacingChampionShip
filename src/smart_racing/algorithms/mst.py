from __future__ import annotations


class UnionFind:
    def __init__(self, values):
        self.parent = {v: v for v in values}
        self.rank = {v: 0 for v in values}

    def find(self, value):
        if self.parent[value] != value:
            self.parent[value] = self.find(self.parent[value])
        return self.parent[value]

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def kruskal_mst(vertices: list[int], edges: list[tuple[int, int, float]]) -> dict:
    uf = UnionFind(vertices)
    chosen = []
    total = 0.0
    for source, target, weight in sorted(edges, key=lambda e: (e[2], e[0], e[1])):
        if uf.union(source, target):
            chosen.append((source, target, weight))
            total += weight
    return {
        "edges": chosen,
        "total_weight": total,
        "is_tree": len(chosen) == max(0, len(vertices) - 1),
        "components": len({uf.find(v) for v in vertices}),
    }
