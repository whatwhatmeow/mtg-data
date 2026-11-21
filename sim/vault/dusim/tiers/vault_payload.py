import os
import sys, json, gzip, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_all import *
from collections import Counter
r = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json"))); F_ = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "final.json")))
TYPE = {}
for row in csv.DictReader(gzip.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..") + "/data/cards.csv.gz", "rt")):
    for n in {row["name"], row["name"].split(" // ")[0]}:
        TYPE.setdefault(n, row["type_line"])
known = {c["name"]: c["role"] for c in D["cards"]}
for v in D["variants"]:
    for c in v["in"]: known.setdefault(c["name"], c.get("role"))
def role(c):
    if c in LANDS: return "land"
    if c in known and known[c] not in (None, "other"): return known[c]
    t = CARDS.get(c, {}).get("tags", set())
    for rl, s in (("win", {"win", "leveler", "consult", "pact", "inverter", "doomsday", "exsang", "crawler"}), ("tutor", {"tutor", "tutor_top", "wishclaw", "transmute2"}),
                  ("ramp", {"rock", "ritual", "petal", "amber", "burst3", "chrome", "diamond", "medallion", "culling", "jlotus", "led"}), ("rem", {"interact", "removal"}),
                  ("prot", {"save", "haste", "hexproof", "shroud", "indestr", "grid", "discard", "drawbridge", "equip1"}),
                  ("draw", {"draw2", "bauble", "sacdraw", "peer", "stargaze", "arena", "horn", "mine", "necro", "citadel", "ring", "bmc", "dispute"}),
                  ("recur", {"reanimate", "entomb", "buried", "scythe"})):
        if t & s: return rl
    return "other"
def typ(c):
    tl = TYPE.get(c, "").split(" // ")[0]
    for k in ("Creature", "Land", "Artifact", "Enchantment", "Instant", "Sorcery", "Planeswalker"):
        if k in tl: return k
    return tl
def entries(cnt):
    return [{"name": n, "qty": q, "role": role(n), "type": typ(n)} for n, q in sorted(cnt.items())]
MAIN = Counter(r["ideal-3gc-v2"]["deck"])
def diff(deck):
    c = Counter(deck)
    return entries(c - MAIN), [{"name": n, "qty": q} for n, q in sorted((MAIN - c).items())]
def st(n, prof="bracket3"):
    x = F_[prof][n]; return f"by turn 6 {x['T6']:.0f}%, turn 8 {x['T8']:.0f}%, turn 10 {x['T10']:.0f}%, average win turn {x['avg']:.1f}"
B3 = "Bracket 3 table"
P1 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "path_budget_to_ideal.json"))); P2 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "path_today_to_budget.json")))
def pathnote(rows, k):
    rows = sorted([z for z in rows if z["turns"] > 2 * z["se"]], key=lambda z: -z["turns"])[:k]
    return "; ".join(f"{i+1}. {z['card']} (${z['price']:.2f}, {z['turns']:.2f} turns)" for i, z in enumerate(rows))
borg = [a["name"] for a in D["adds"] if a["status"] == "Borg (unopened)"]
V = {}
def mk(id_, label, key, bracket, goal, src, notes):
    i, o = diff(r[key]["deck"])
    V[id_] = {"id": id_, "label": label, "name": f"Doom Unrivaled ({label})", "bracket": bracket, "bracketGoal": goal, "source": src,
              "updated": "Nov 21, 2026", "in": i, "out": o, "notes": notes}
gcl = lambda k: ", ".join(sorted(set(gcs(r[k]["deck"])))) or "none"
mk("ideal-0gc", "Ideal, no Game Changers", "ideal-0gc", "Bracket 3", "0 Game Changers",
   "Nov 21 sim-driven build, no price limit",
   [f"Fastest list the sim found with no Game Changers and no budget. About ${r['ideal-0gc']['price']:.0f} at the cheapest printings.",
    f"Nov 21 sim, 10,000 games, {B3}: {st('ideal-0gc')}. The 3-Game-Changer Ideal is about 0.35 turns faster.",
    "Every card name appears once, so Tainted Pact works."])
mk("budget-0gc", "Budget, no Game Changers", "budget-0gc", "Bracket 3", "0 Game Changers",
   "Nov 21 sim-driven build, capped at $150",
   [f"Fastest list the sim found at or under $150 (cheapest printings, Doom included): ${r['budget-0gc']['price']:.2f}. Prices move, so check before buying.",
    f"Nov 21 sim, 10,000 games, {B3}: {st('budget-0gc')}. That's the recommended budget build: about 1.7 turns faster than the Nov 20 Unique Pact list.",
    "Upgrade path toward Ideal, best gain first (each measured alone, in for Doom's Servo-Guards; it breaks the $150 cap): " + pathnote(P1, 12) + ".",
    "Big-ticket Ideal cards (Mox Amber, The Soul Stone, Lake of the Dead, Cavern of Souls, Urborg) each add under 0.1 turns on their own.",
    "Every card name appears once, so Tainted Pact works."])
mk("budget-3gc", "Budget, 3 Game Changers", "budget-3gc-forced", "Bracket 3", "3 Game Changers: " + gcl("budget-3gc-forced"),
   "Nov 21 sim-driven build, capped at $150, forced to keep 3 Game Changers",
   [f"The three cheapest Game Changers (Ad Nauseam, Bolas's Citadel, Opposition Agent, about $38 together) forced into a $150 list: ${r['budget-3gc-forced']['price']:.2f}.",
    f"Nov 21 sim, 10,000 games, {B3}: {st('budget-3gc-forced')}. That's about 2.9 turns slower than the no-Game-Changer budget list: paying for them costs the tutors. Not recommended; it exists for comparison.",
    "Every card name appears once, so Tainted Pact works."])
mk("today-3gc", "Build today, 3 Game Changers", "today-3gc", "Bracket 3", "3 Game Changers: " + gcl("today-3gc"),
   "Nov 21 sim-driven build from owned cards only",
   [f"Fastest list from cards you own (your sleeved deck, the Owned build, the vault's owned cards and your stated collection). Game Changers: Demonic Tutor, The One Ring, Orcish Bowmasters.",
    f"Nov 21 sim, 10,000 games, {B3}: {st('today-3gc')}. Orcish Bowmasters was added only to reach three; it tested about 0.05 turns slower than Murmuring Volume.",
    "28 Swamps: you don't own enough different lands yet, so Tainted Pact is out (it stops at the second Swamp). The land package in the Budget list turns it on.",
    "Buy order (measured from the no-Game-Changer Build-today list): " + pathnote(P2, 8) + "; then the Budget list's lands (about $15), which make Tainted Pact work."])
mk("today-0gc", "Build today, no Game Changers", "today-0gc", "Bracket 3", "0 Game Changers",
   "Nov 21 sim-driven build from owned cards only",
   ["Fastest list from cards you own, with no Game Changers. Replaces the Owned build.",
    f"Nov 21 sim, 10,000 games, {B3}: {st('today-0gc')} (the old Owned build: {st('Owned build (today)')}).",
    "28 Swamps, so Tainted Pact is out until you buy the Budget list's lands.",
    "Buy order, best gain first (each measured alone, in for Grim Reaper's Scythe): " + pathnote(P2, 12) + "; then the Budget list's lands (about $15), which make Tainted Pact work."])
mk("b4", "Bracket 4", "b4", "Bracket 4", "Any Game Changers: " + gcl("b4"),
   "Nov 21 sim-driven build, tuned against the Bracket 4 table profile, no limits",
   [f"No price or Game Changer limit, tuned against a Bracket 4 table. About ${r['b4']['price']:.0f}.",
    f"Nov 21 sim, 10,000 games, Bracket 4 table: {st('b4', 'bracket4')}. Bracket 3 table: {st('b4')}.",
    "It's barely faster than the 3-Game-Changer Ideal: past three, more Game Changers (Ancient Tomb, Grim Monolith) add little because the deck already finds its win on time.",
    "Every card name appears once, so Tainted Pact works."])
mk("b5", "Bracket 5 / cEDH", "b5", "Bracket 5", "Any Game Changers: " + gcl("b5"),
   "Nov 21 sim-driven build, tuned against the cEDH table profile, no limits",
   [f"No limits, tuned against a cEDH table (opponents interact a lot and can win from turn 3). About ${r['b5']['price']:.0f}.",
    f"Nov 21 sim, 10,000 games, cEDH table: {st('b5', 'cedh')}. The 3-Game-Changer Ideal at the same table: {st('ideal-3gc-v2', 'cedh')}.",
    "It trades Inverter of Truth and Psychosis Crawler for cheap interaction (Deadly Rollick, Dismember, Snuff Out, Fatal Push, Sheoldred's Edict) and Mox Diamond.",
    "Every card name appears once, so Tainted Pact works."])
main_notes = [
 "Nov 21, 2026 rebuild. Main list = Ideal (3 Game Changers: Demonic Tutor, Vampiric Tutor, Chrome Mox). Versions: Ideal without Game Changers, Budget (under $150) with and without, Build today with and without, Bracket 4 and Bracket 5. Every list was built by the sim one swap at a time, fastest first.",
 f"Ideal, Nov 21 sim, 10,000 games, {B3}: {st('ideal-3gc-v2')}. About ${r['ideal-3gc-v2']['price']:.0f} at the cheapest printings.",
 "Plan: Doom + Tainted Pact or Demonic Consultation (exile the library, tap Doom), Doom + Leveler or Inverter of Truth, with a pile of tutors to find them. Every card name appears once, so Tainted Pact works. Tell the table about the two-card wins before the game.",
 "Line A: cast Doom off fast mana, give him haste (Lightning Greaves {2}, equip {0}; Lavaspur Boots {1}, equip {1}), then Demonic Consultation naming a card not in the deck, or Tainted Pact taking nothing, and tap Doom.",
 "Line B: cast Doom and pass. At the end step of the player before you, cast Pact or Consultation (opponents may still have mana up). Doom is summoning sick until your turn starts, so tap him in your upkeep, before your draw.",
 "Line C (when Doomsday is in the list): pile Street Wraith, Dark Ritual, Night's Whisper, Demonic Consultation, Spoils of the Vault; Doom must already be able to tap.",
 "Line D: Mirror of Fate (tap, sacrifice, choose zero cards) empties the library. Inverter of Truth only empties it when your graveyard is empty.",
 "Never cast Spoils of the Vault from a full library: you lose a life per exiled card and die before Doom can tap. Doom's 'win even at 0 life' only covers his own 1 life.",
 "Sim caveats: Mox Opal is modeled like Mox Amber; 0-drop creatures only as sacrifice fodder; Spoils of the Vault left out because the sim ignores its life loss. Prices are the Nov 12 card-data refresh.",
 "Land notes kept for later: Gemstone Mine, Cabal Pit and Hive of the Eye Tyrant are the cheap untapped black lands.",
 "Retired Nov 21: Owned build (became Build today), Unique Pact (became Budget), Turbo Pact, Turbo Pact + Game Changers and Turbo Pact (budget lands) (their tutors and fast mana are in Ideal, B4 and B5). The old lists are in the mtg-data repo's history (decks/doom-unrivaled.json).",
 "Earlier: Nov 8 merged build (Doom + Leveler, Ultron backup); Nov 10-18 Owned-build sim swaps; Nov 20 Unique Pact (singleton land base, 0.37 turns faster than the Owned build)."]
data = {"cards": entries(MAIN), "bracket": "Bracket 3", "bracketGoal": "3 Game Changers: Demonic Tutor, Vampiric Tutor, Chrome Mox",
        "baseLabel": "Ideal (3 Game Changers)", "source": "Nov 21, 2026 sim-driven rebuild (Ideal, 3 Game Changers)", "updated": "Nov 21, 2026",
        "themeLabel": "Empty the library", "notes": main_notes,
        "variants": [V[k] for k in ("ideal-0gc", "budget-0gc", "budget-3gc", "today-3gc", "today-0gc", "b4", "b5")]}
assert sum(c["qty"] for c in data["cards"]) == 99
for v in data["variants"]:
    m = Counter(MAIN)
    for c in v["out"]: m[c["name"]] -= c["qty"]
    for c in v["in"]: m[c["name"]] += c["qty"]
    assert sum((+m).values()) == 99, v["id"]
json.dump(data, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "vault_data.json"), "w"), ensure_ascii=False)
mirror = dict(D); mirror.update(data)
json.dump(mirror, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..") + "/decks/doom-unrivaled.json", "w"), indent=1, ensure_ascii=False)
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..") + "/decks/doom-unrivaled.json", "a").write("\n")
print(len(json.dumps(data)), [ (v["id"], len(v["in"]), len(v["out"])) for v in data["variants"]])
print("borg used:", {k: [c for c in r[k]["deck"] if c in borg] for k in ("today-0gc", "today-3gc")})
print(Counter(c["role"] for c in data["cards"]))
for v in data["variants"]: print(v["id"], v["notes"][-1][:200] if v["id"].startswith("today") else "")
