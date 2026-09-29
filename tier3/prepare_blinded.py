#!/usr/bin/env python3
"""Build blinded Tier 3 rating forms from published + MAPIG-generated items.

Outputs:
  pilot/forms/<construct>.md   — readable rating form (definitions + grid)
  pilot/forms/<construct>.csv  — rating grid for data collection
  pilot/key.csv                — SECRET source key (never shown to raters)
"""
import json, csv, os, random

BASE = "/home/ldb/projects/mapig"
TIER2 = f"{BASE}/tier2_benchmark"
TIER3 = f"{BASE}/tier3"
FORMS = f"{TIER3}/pilot/forms"

CONSTRUCTS = {
    "swls": {
        "name": "Satisfaction with Life",
        "definition": "A global cognitive judgment of one's life as a whole, reflecting the degree to which a person evaluates their overall quality of life favorably.",
        "facets": {"Satisfaction with Life": "Global cognitive evaluation of one's life as a whole."},
    },
    "grit": {
        "name": "Grit",
        "definition": "Perseverance and passion for long-term goals.",
        "facets": {
            "Consistency of Interests": "Maintaining sustained interest in the same goals and projects over long periods.",
            "Perseverance of Effort": "Sustaining diligent effort and hard work despite setbacks and adversity.",
        },
    },
    "uwes": {
        "name": "Work Engagement",
        "definition": "A positive, fulfilling, work-related state of mind.",
        "facets": {
            "Vigor": "High energy and mental resilience while working.",
            "Dedication": "Significance, enthusiasm, inspiration, and pride in one's work.",
            "Absorption": "Full concentration and immersion in one's work.",
        },
    },
    "burnout": {
        "name": "Burnout",
        "definition": "Prolonged physical and psychological exhaustion experienced in relation to work.",
        "facets": {
            "Personal Burnout": "Generalized fatigue and exhaustion of the person.",
            "Work-Related Burnout": "Fatigue and exhaustion attributed to one's work.",
            "Client-Related Burnout": "Fatigue and exhaustion attributed to working with clients or service recipients.",
        },
    },
}

# published instrument id -> generated construct id
PUB2GEN = {"swls": "swls", "grit-s": "grit", "uwes-9": "uwes", "cbi": "burnout"}


def norm(t):
    t = t.strip()
    t = t.rstrip(".")
    return " ".join(t.split())


def canon(f):
    """Canonical facet name — strips source-specific capitalization/separator differences."""
    return f.strip().lower()


def load_published():
    insts = json.load(open(f"{TIER2}/instruments.json"))["instruments"]
    out = {}
    for inst in insts:
        items = [{"text": norm(it["text"]), "facet": canon(inst["factors"][it["factor"]]), "source": "published"}
                 for it in inst["items"]]
        out[PUB2GEN[inst["id"]]] = items
    return out


def load_generated():
    out = {}
    for line in open(f"{TIER2}/gen_results.jsonl"):
        rec = json.loads(line)
        if "error" in rec or "name" not in rec:
            continue
        items = [{"text": norm(it["text"]), "facet": canon(it["facet"]), "source": "generated"}
                 for it in rec["items"]]
        out[rec["id"]] = items
    return out


def main():
    os.makedirs(FORMS, exist_ok=True)
    pub, gen = load_published(), load_generated()
    key_rows = []

    for cid, cdef in CONSTRUCTS.items():
        pool = pub.get(cid, []) + gen.get(cid, [])
        random.Random(42).shuffle(pool)  # seeded for reproducibility
        rows = []
        for i, it in enumerate(pool):
            iid = f"{cid.upper()}-{i+1:02d}"
            key_rows.append({"id": iid, "construct": cdef["name"], "source": it["source"],
                             "facet": it["facet"], "text": it["text"]})
            rows.append({"id": iid, "text": it["text"], "facet": it["facet"]})

        md = [f"# {cdef['name']} — Item Rating Form (blinded)", "",
              f"**Construct definition:** {cdef['definition']}", "",
              "**Facets:**"]
        for fn, fd in cdef["facets"].items():
            md.append(f"- **{fn}**: {fd}")
        md += ["", "Rate each item on D1–D6 and Overall (1–5). Source guess: **H**=human, **A**=AI, **C**=cannot tell.",
               "", "| ID | Item | Facet | D1 | D2 | D3 | D4 | D5 | D6 | Overall | H/A/C | Notes |",
               "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            md.append(f"| {r['id']} | {r['text']} | {r['facet']} |  |  |  |  |  |  |  |  |  |")
        open(f"{FORMS}/{cid}.md", "w").write("\n".join(md))

        with open(f"{FORMS}/{cid}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "item_text", "facet", "D1_clarity", "D2_relevance", "D3_facet",
                        "D4_distinct", "D5_behavioral", "D6_bias", "overall", "source_guess_HAC", "notes"])
            for r in rows:
                w.writerow([r["id"], r["text"], r["facet"], "", "", "", "", "", "", "", "", ""])

    with open(f"{TIER3}/pilot/key.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "construct", "source", "facet", "text"])
        for r in key_rows:
            w.writerow([r["id"], r["construct"], r["source"], r["facet"], r["text"]])

    print(f"wrote {len(key_rows)} items across {len(CONSTRUCTS)} constructs")
    print("forms dir:", FORMS)
    print("key:", f"{TIER3}/pilot/key.csv")


if __name__ == "__main__":
    main()
