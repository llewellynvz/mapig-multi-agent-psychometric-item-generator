import json, re, difflib, os, sys

ROOT = "/home/ldb/projects/mapig"


def normalize(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s']", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_published():
    with open(os.path.join(ROOT, "tier2_benchmark/instruments.json")) as f:
        data = json.load(f)
    out = {}
    for inst in data["instruments"]:
        out[inst["id"]] = {"name": inst["name"], "items": [it["text"] for it in inst["items"]]}
    return out


def load_generated(path, store):
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if "items" not in rec:
                continue
            store[rec["id"]] = [it["text"] for it in rec["items"]]


def main():
    published = load_published()
    generated = {}
    load_generated(os.path.join(ROOT, "tier2_benchmark/gen_results.jsonl"), generated)

    id_map = {"swls": "swls", "grit": "grit-s", "uwes": "uwes-9", "burnout": "cbi"}

    print("=" * 78)
    print("COPYRIGHT / VERBATIM CHECK — generated vs published items")
    print("Method: exact match on normalized text; near-match via difflib ratio (>=0.80).")
    print("=" * 78)

    totals = {"exact": 0, "near": 0, "gen": 0}
    for gid, pub_id in id_map.items():
        if gid not in generated or pub_id not in published:
            print(f"\n[skip] {gid} -> {pub_id}: missing generated or published items")
            continue
        gen_items = generated[gid]
        pub_items = published[pub_id]["items"]
        pub_norm = [normalize(x) for x in pub_items]
        print(f"\n--- {gid} (n={len(gen_items)}) vs {pub_id} '{published[pub_id]['name']}' (n={len(pub_items)}) ---")
        for gi in gen_items:
            totals["gen"] += 1
            gin = normalize(gi)
            best_ratio, best_pub = 0.0, None
            for pi, pn in zip(pub_items, pub_norm):
                if gin == pn:
                    best_ratio, best_pub = 1.0, pi
                    break
                r = difflib.SequenceMatcher(None, gin, pn).ratio()
                if r > best_ratio:
                    best_ratio, best_pub = r, pi
            if best_ratio == 1.0:
                totals["exact"] += 1
                print(f"  [EXACT]      \"{gi}\"\n               == published \"{best_pub}\"")
            elif best_ratio >= 0.80:
                totals["near"] += 1
                print(f"  [NEAR {best_ratio:.2f}] \"{gi}\"\n               ~  published \"{best_pub}\"")
            else:
                print(f"  [ok  {best_ratio:.2f}] \"{gi}\"")
    print("\n" + "=" * 78)
    print(f"TOTAL: {totals['gen']} generated items | {totals['exact']} exact (verbatim) | "
          f"{totals['near']} near-paraphrase (>=0.80)")
    print("=" * 78)


if __name__ == "__main__":
    main()
