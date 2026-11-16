import sys, json
from ws_swap import *
deckf, prof, slot = sys.argv[1], sys.argv[2], sys.argv[3]
cands = sys.argv[4].split("|")
base = load(deckf)
V = {"base": base}
for c in cands:
    V[c] = swap(base, [(slot, c)])
rows = compare(V, prof, int(sys.argv[5]) if len(sys.argv) > 5 else 3000)
rows = [rows[0]] + sorted(rows[1:], key=lambda r: -r["faster"])
show(rows, f"{deckf} {prof}: each candidate replaces {slot}")
json.dump(rows, open(f"cand_{deckf.replace('.json','')}_{prof}.json", "w"))
