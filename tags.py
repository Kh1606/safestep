import os
import json
from collections import Counter
import osmium

PBF = r"Seoul.osm.pbf"   # <-- put file in same folder OR set full path
OUT_DIR = "tag_stats_out"
TOP_KV_TO_KEEP_IN_MEMORY = 2_000_000  # adjust if RAM is limited

os.makedirs(OUT_DIR, exist_ok=True)

# counts of tag KEYS (e.g., "highway", "name")
key_counts_all = Counter()
key_counts_by_type = {"node": Counter(), "way": Counter(), "relation": Counter()}

# counts of key=value pairs (e.g., "highway=steps", "amenity=cafe")
# This can explode in size, so we keep it capped in memory and spill later.
kv_counts_all = Counter()
kv_counts_by_type = {"node": Counter(), "way": Counter(), "relation": Counter()}

total_objects = {"node": 0, "way": 0, "relation": 0}
total_tags = {"node": 0, "way": 0, "relation": 0}

def add_tags(obj_type: str, tags):
    global kv_counts_all, kv_counts_by_type

    total_objects[obj_type] += 1
    # Count keys and key=value
    for k, v in tags:
        key_counts_all[k] += 1
        key_counts_by_type[obj_type][k] += 1

        kv = f"{k}={v}"
        # kv can be huge; try to cap in-memory growth
        if len(kv_counts_all) < TOP_KV_TO_KEEP_IN_MEMORY or kv in kv_counts_all:
            kv_counts_all[kv] += 1
        if len(kv_counts_by_type[obj_type]) < TOP_KV_TO_KEEP_IN_MEMORY or kv in kv_counts_by_type[obj_type]:
            kv_counts_by_type[obj_type][kv] += 1

        total_tags[obj_type] += 1

class TagStats(osmium.SimpleHandler):
    def node(self, n):
        add_tags("node", n.tags)

    def way(self, w):
        add_tags("way", w.tags)

    def relation(self, r):
        add_tags("relation", r.tags)

def write_counter(counter: Counter, path: str, top_n: int | None = None):
    # sorted list of (item, count)
    items = counter.most_common(top_n) if top_n else counter.most_common()
    with open(path, "w", encoding="utf-8") as f:
        for item, c in items:
            f.write(f"{c}\t{item}\n")

def write_summary():
    summary = {
        "pbf": os.path.abspath(PBF),
        "total_objects": total_objects,
        "total_tags": total_tags,
        "unique_tag_keys": len(key_counts_all),
        "unique_key_value_pairs_in_memory": len(kv_counts_all),
        "note": (
            "key=value counts were capped in memory to avoid RAM blow-up. "
            "If unique_key_value_pairs_in_memory hit the cap, rare pairs may be missing."
        ),
    }
    with open(os.path.join(OUT_DIR, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    if not os.path.exists(PBF):
        raise FileNotFoundError(f"Cannot find PBF: {PBF}")

    print("Reading:", PBF)
    TagStats().apply_file(PBF, locations=False)

    # Write outputs
    write_summary()

    # Tag keys
    write_counter(key_counts_all, os.path.join(OUT_DIR, "tag_keys_all.tsv"))
    write_counter(key_counts_by_type["node"], os.path.join(OUT_DIR, "tag_keys_nodes.tsv"))
    write_counter(key_counts_by_type["way"], os.path.join(OUT_DIR, "tag_keys_ways.tsv"))
    write_counter(key_counts_by_type["relation"], os.path.join(OUT_DIR, "tag_keys_relations.tsv"))

    # Key=Value (Top only for easy viewing) + full as captured in memory
    write_counter(kv_counts_all, os.path.join(OUT_DIR, "tag_kv_all_top2000.tsv"), top_n=2000)
    write_counter(kv_counts_by_type["node"], os.path.join(OUT_DIR, "tag_kv_nodes_top2000.tsv"), top_n=2000)
    write_counter(kv_counts_by_type["way"], os.path.join(OUT_DIR, "tag_kv_ways_top2000.tsv"), top_n=2000)
    write_counter(kv_counts_by_type["relation"], os.path.join(OUT_DIR, "tag_kv_relations_top2000.tsv"), top_n=2000)

    # Full captured-in-memory kv counts (may be huge but still limited by cap)
    write_counter(kv_counts_all, os.path.join(OUT_DIR, "tag_kv_all.tsv"))
    print("Done. Output folder:", OUT_DIR)
