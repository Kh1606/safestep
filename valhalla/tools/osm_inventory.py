import osmium
from collections import Counter
import json

PBF = "seoul_4km2.osm.pbf"
OUT = "inventory.json"

TOP_KEYS = 80
TOP_VALUES_PER_KEY = 40

class Inv(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.node_keys = Counter()
        self.way_keys = Counter()
        self.rel_keys = Counter()

        self.node_kv = {}  # key -> Counter(values)
        self.way_kv = {}
        self.rel_kv = {}

    def _add(self, kv_map, key_counter, tags):
        for t in tags:
            k, v = t.k, t.v
            key_counter[k] += 1
            if k not in kv_map:
                kv_map[k] = Counter()
            kv_map[k][v] += 1

    def node(self, n): self._add(self.node_kv, self.node_keys, n.tags)
    def way(self, w):  self._add(self.way_kv,  self.way_keys,  w.tags)
    def relation(self, r): self._add(self.rel_kv, self.rel_keys, r.tags)

def top_kv(kv, top_values=TOP_VALUES_PER_KEY):
    out = {}
    for k, c in kv.items():
        out[k] = c.most_common(top_values)
    return out

h = Inv()
h.apply_file(PBF, locations=False)

data = {
    "pbf": PBF,
    "top_node_keys": h.node_keys.most_common(TOP_KEYS),
    "top_way_keys": h.way_keys.most_common(TOP_KEYS),
    "top_relation_keys": h.rel_keys.most_common(TOP_KEYS),
    "top_node_kv": top_kv(h.node_kv),
    "top_way_kv": top_kv(h.way_kv),
    "top_relation_kv": top_kv(h.rel_kv),
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Wrote", OUT)
