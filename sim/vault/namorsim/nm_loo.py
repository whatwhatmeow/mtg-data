import json, sys
from nm_run import *
prof = sys.argv[1]; N = int(sys.argv[2])
base = load("deck.json")
names = sorted({c for c in base if c not in LANDS})
V = {"BASE": base}
for c in names:
    V["-" + c] = swap(base, [(c, "BLANK")])
rows = compare(V, prof, N=N, chunks=2)
json.dump(rows, open(f"loo_{prof}.json", "w"))
b = rows[0]
print(f"base by12 {b['by12']:.3f} avg {b['avg']:.2f}")
for r in sorted(rows[1:], key=lambda r: r["faster"]):
    print(f"{r['name']:38s} turns lost if cut {-r['faster']:+.3f}±{r['se']:.3f}  by12 {100*(r['by12']-b['by12']):+.1f}pts")
