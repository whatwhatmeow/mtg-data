"""Shared pieces every deck simulator needs, so a new sim only has to write the Game class.

    from common import PROFILES, CardDB, load_deck, compare, leave_one_out, show

A simulator supplies play(deck, profile, rng) -> turn the deck won on (or None).
compare() runs every variant on the SAME seeds (paired design), so small differences
between two lists show up with far fewer games.
"""
import csv, gzip, json, math, os, random
from multiprocessing import Pool

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# Opponent pressure per bracket: chance per opponent per turn of targeted removal, a board
# wipe, artifact/enchantment removal, adding a blocker; chance a combo attempt or a key
# spell gets answered. Same numbers the vault simulators used, so results line up.
PROFILES = {
    "goldfish": dict(removal=0.0, wipe=0.0, art=0.0, ench=0.0, creature_rate=0.0, disrupt=0.0, counter=0.0),
    "bracket2": dict(removal=0.05, wipe=0.02, art=0.03, ench=0.03, creature_rate=0.55, disrupt=0.10, counter=0.02),
    "bracket3": dict(removal=0.08, wipe=0.03, art=0.04, ench=0.05, creature_rate=0.60, disrupt=0.15, counter=0.03),
    "bracket4": dict(removal=0.15, wipe=0.05, art=0.07, ench=0.08, creature_rate=0.70, disrupt=0.30, counter=0.10),
}
MAX_TURN = 16


class CardDB:
    """Oracle data by card name from data/cards.csv.gz (first paper printing found)."""

    def __init__(self, path=None):
        csv.field_size_limit(10**9)
        self.cards = {}
        with gzip.open(path or os.path.join(ROOT, "data", "cards.csv.gz"), "rt", encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if r["digital"] == "1":
                    continue
                for n in {r["name"], r["name"].split(" // ")[0]}:
                    self.cards.setdefault(n, r)

    def __getitem__(self, name):
        return self.cards[name]

    def get(self, name):
        return self.cards.get(name)

    def is_land(self, name):
        return "Land" in self.cards[name]["type_line"].split(" // ")[0]

    def missing(self, names):
        return sorted({n for n in names if n not in self.cards})


def _names(items):
    out = []
    for c in items or []:
        if isinstance(c, str):
            out.append(c)
        else:
            out += [c["name"]] * int(c.get("qty", 1))
    return out


def load_deck(deck, variant=None):
    """deck = a vault id ('tom-bombadil') or a path. Returns (99-ish card names, commanders).
    variant = id or label of a saved version; its out/in lists are applied to the main list."""
    path = deck if os.path.exists(deck) else os.path.join(ROOT, "decks", deck + ".json")
    d = json.load(open(path, encoding="utf-8"))
    d = d.get("data", d)
    cards = _names(d["cards"])
    if variant:
        v = next(x for x in d.get("variants", []) if variant in (x.get("id"), x.get("label"), x.get("name")))
        for n in _names(v.get("out")):
            cards.remove(n)
        cards += _names(v.get("in"))
    return cards, list(d.get("commanders", []))


def swap(deck, pairs):
    x = list(deck)
    for out, inn in pairs:
        x[x.index(out)] = inn
    return x


def _job(a):
    play, name, deck, prof, n, seed = a
    return name, [play(deck, PROFILES[prof], random.Random(seed * (k + 1))) or 99 for k in range(n)]


def compare(play, variants, profile, n=3000, seed=1_000_003):
    """variants = {label: card list}; the first one is the baseline. play must be a top-level function."""
    names = list(variants)
    with Pool() as p:
        res = dict(p.map(_job, [(play, v, variants[v], profile, n, seed) for v in names], chunksize=1))
    base, cap, rows = res[names[0]], (lambda t: min(t, MAX_TURN + 1)), []
    for v in names:
        r = res[v]
        d = [cap(b) - cap(x) for x, b in zip(r, base)]
        m = sum(d) / n
        se = math.sqrt(sum((y - m) ** 2 for y in d) / max(1, n - 1) / n)
        rows.append(dict(name=v, faster=m, se=se, **{f"by{t}": sum(x <= t for x in r) / n for t in (6, 8, 10, 12, 16)}))
    return rows


def leave_one_out(play, deck, profile, n=3000, is_land=lambda c: False):
    """Blank each nonland card in turn; the cards whose loss costs the most turns matter most."""
    v = {"base": deck}
    for c in sorted({c for c in deck if not is_land(c)}):
        v["-" + c] = swap(deck, [(c, "BLANK")])
    rows = compare(play, v, profile, n)
    return [rows[0]] + sorted(rows[1:], key=lambda r: r["faster"])


def show(rows, title=""):
    print("==", title)
    for r in rows:
        print(f"  {r['name']:44s} by8 {100*r['by8']:5.1f}% by10 {100*r['by10']:5.1f}% by12 {100*r['by12']:5.1f}% "
              f"by16 {100*r['by16']:5.1f}%  turns faster than base {r['faster']:+.3f}±{r['se']:.3f}")
