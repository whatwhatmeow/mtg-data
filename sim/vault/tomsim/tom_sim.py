"""Monte Carlo simulator for Tom's Bombs (Tom Bombadil, five-color Sagas + combos).

Win routes modeled:
  * Infinite mana: Freed from the Real / Pemmin's Aura on Bloom Tender, Faeburrow Elder (non-blue),
    Sage of the Maze, Sanctum Weaver (blue too); Umbral Mantle / Staff of Domination / Isochron
    Scepter + Dramatic Reversal (candidates).
      -> Helix Pinnacle + All Will Be One (instant), Helix alone (next upkeep), infinite blue +
         Clockspinning + (All Will Be One | Narci + a Saga | Summon: Bahamut on board).
  * There and Back Again + Clockspinning (~12 mana): Smaug legend-rule loop = infinite Treasures,
    then any payoff above.
  * Summon: Bahamut chapter IV re-triggered with Clockspinning (8 mana per extra trigger).
  * Maze's End with 10 different Gates.
  * Fair damage: Saga tokens (Smaug, Avacyn, Kraken, Wraiths, Knights, Angels...), Summon creatures,
    Narci drains, Bahamut IV, One Ring to Rule Them All III, All Will Be One pings, Primal Odin.
Opponents: blockers, targeted removal (combo creature > Tom > threats), wipes, enchantment removal,
and a chance to disrupt each combo attempt.
"""
import random
TRANCE = True
from tom_cards import LANDS, SAGAS, OTHER, ANY

COLORS = "WUBRG"


class Won(Exception):
    def __init__(self, how):
        self.how = how


PROFILES = {
    "bracket3": dict(removal=0.08, wipe=0.03, ench=0.05, creature_rate=0.6, disrupt=0.15),
    "bracket4": dict(removal=0.15, wipe=0.05, ench=0.08, creature_rate=0.7, disrupt=0.30),
}


def pips(cost):
    return {c for c in COLORS if cost.get(c, 0)}


def card(c):
    if c in SAGAS:
        d = SAGAS[c]
        return dict(cost=d["cost"], type="saga", tags={"saga"})
    return OTHER.get(c)


def mv(c):
    d = card(c)
    if not d:
        return 0
    return sum(d["cost"].values())


class Game:
    def __init__(self, deck, prof, rng, log=False, combo_from=1):
        self.rng, self.p, self.logging, self.lines = rng, prof, log, []
        self.combo_from = combo_from
        self.lib = list(deck)
        rng.shuffle(self.lib)
        self.hand, self.gy = [], []
        self.lands = []
        self.perms = []            # nonland, non-saga permanents (names)
        self.entered = {}
        self.auras = {}            # aura name -> host creature name
        self.sagas = []            # dicts: name, lore, copy(bool)
        self.tokens = []           # dicts: power, kind, sick
        self.tom = "cz"
        self.tom_tax = 0
        self.treasures = 0
        self.life = 40
        self.opp = [40, 40, 40]
        self.board = [[], [], []]
        self.turn = 0
        self.on_play = rng.random() < 0.25
        self.helix = 0
        self.helix_pending = False
        self.terra_mana = 0
        self.no_block = 0
        self.ring = 0
        self.odin = False
        self.st = dict(win=None, how=None, combo_attempts=0, disrupted=0, sagas_done=0, tom_reveals=0,
                       smaug_treasures=0, awbo_dmg=0, narci_dmg=0, combat_dmg=0, first_combo=None)
        self.mulligan()

    # ---------------- utils ----------------
    def log(self, s):
        if self.logging:
            self.lines.append(f"T{self.turn}: {s}")

    def alive(self):
        return [i for i in range(3) if self.opp[i] > 0]

    def check(self, how="damage"):
        if not self.alive():
            raise Won(how)

    def has(self, tag):
        return any(tag in (card(c) or {}).get("tags", ()) for c in self.perms)

    def count_tag(self, tag):
        return sum(tag in (card(c) or {}).get("tags", ()) for c in self.perms)

    def on_bf(self, name):
        return name in self.perms or any(s["name"] == name for s in self.sagas)

    def ready(self, name):
        return name in self.perms and self.entered.get(name, 99) < self.turn

    def mulligan(self):
        for a in range(4):
            if a:
                self.lib += self.hand
                self.hand = []
                self.rng.shuffle(self.lib)
            self.hand = [self.lib.pop() for _ in range(7)]
            nl = sum(c in LANDS for c in self.hand)
            if 3 <= nl <= 5 or a == 3:
                for _ in range(max(0, a - 1)):
                    lands = [c for c in self.hand if c in LANDS]
                    sp = [c for c in self.hand if c not in LANDS]
                    pick = lands[-1] if len(lands) > 4 or not sp else sp[-1]
                    self.hand.remove(pick)
                    self.lib.insert(0, pick)
                return

    def draw(self, n=1):
        for _ in range(n):
            if self.lib:
                self.hand.append(self.lib.pop())

    def ping(self, n, src="awbo"):
        """Damage to the opponent closest to death."""
        if n <= 0:
            return
        al = self.alive()
        if not al:
            return
        i = min(al, key=lambda k: self.opp[k])
        self.opp[i] -= n
        if src == "awbo":
            self.st["awbo_dmg"] += n
        self.check()

    def lose_each(self, n, src="narci"):
        for i in self.alive():
            self.opp[i] -= n
        if src == "narci":
            self.st["narci_dmg"] += n
        self.check()

    # ---------------- counts ----------------
    def enchantments(self):
        n = len(self.sagas) + len(self.auras)
        n += sum(1 for c in self.perms if (card(c) or {}).get("type") == "enchantment" or (card(c) or {}).get("ench"))
        return n

    def colors_among(self):
        cols = set()
        for c in self.perms + [s["name"] for s in self.sagas] + list(self.auras):
            d = card(c)
            if d:
                cols |= pips(d["cost"])
        if self.tom == "bf":
            cols |= set(COLORS)
        return cols

    def gates(self):
        return [l["name"] for l in self.lands if l.get("gate")]

    def lore_total(self):
        return sum(s["lore"] for s in self.sagas)

    def tom_protected(self):
        return self.lore_total() >= 4

    # ---------------- counters / All Will Be One ----------------
    def counters_placed(self, events=1, amount=1):
        if self.has("awbo"):
            for _ in range(events):
                self.ping(amount)

    # ---------------- lands & mana ----------------
    def any_color_lands(self):
        return self.has("omen") or self.has("lantern") or (
            any(l.get("worldtree") for l in self.lands) and len(self.lands) >= 6)

    def land_enters(self, name, from_effect=False, force_tapped=None):
        cols, tapped, ex = LANDS[name]
        if force_tapped is not None:
            tapped = force_tapped
        if ex.get("thran"):
            tapped = len(self.lands) > 2
        if tapped and (self.has("amulet") or self.has("spelunking")):
            tapped = False
        if tapped and ex.get("gate") and any(l.get("gond") for l in self.lands):
            tapped = False
        entry = {"name": name, "colors": set(cols), "tapped": tapped, **ex}
        if ex.get("urza"):
            entry["lore"] = 0
        self.lands.append(entry)
        # landfall
        if self.has("moleman") and len(self.lib) > 25:
            for _ in range(2 * self.count_tag("moleman")):
                if self.lib:
                    self.gy.append(self.lib.pop())
        if self.has("evosage"):
            self.proliferate(self.count_tag("evosage"))
        return entry

    def play_land(self):
        hl = [c for c in self.hand if c in LANDS]
        if not hl:
            return
        def key(l):
            cols, tapped, ex = LANDS[l]
            return (tapped and not (self.has("amulet") or self.has("spelunking")), -len(cols))
        # Maze's End: prefer when we can activate soon
        pick = sorted(hl, key=key)[0]
        self.hand.remove(pick)
        self.land_enters(pick)

    def build_pool(self):
        pool = []
        anyc = self.any_color_lands()
        gates = bool(self.gates())
        for l in self.lands:
            if l["tapped"]:
                continue
            cols = set(ANY) if anyc else set(l["colors"])
            if l.get("plaza") and not gates and not anyc:
                cols = {"C"}
            pool.append({"cols": cols, "land": l["name"]})
        for c in self.perms:
            d = card(c)
            prod = d.get("prod") if d else None
            if prod == "CC":
                pool += [{"cols": {"C"}}, {"cols": {"C"}}]
            elif prod:
                pool.append({"cols": set(prod)})
            if c in self.perms and d and d.get("type") == "creature" and self.entered.get(c, 99) < self.turn:
                tags = d["tags"]
                if "bloom" in tags:
                    for col in self.colors_among():
                        pool.append({"cols": {col}, "dork": c})
                elif "sage" in tags:
                    pool += [{"cols": set(ANY), "dork": c}, {"cols": set(ANY), "dork": c}]
                elif "weaver" in tags:
                    n = self.enchantments()
                    pool += [{"cols": set(ANY), "dork": c, "weaver": True} for _ in range(n)]
                elif "dork1" in tags:
                    pool.append({"cols": set(ANY), "dork": c})
        pool += [{"cols": set(ANY), "treasure": True} for _ in range(self.treasures)]
        return pool

    def _alloc(self, cost, srcs):
        need = []
        for c in COLORS:
            need += [c] * cost.get(c, 0)
        used = []

        def bt(k):
            if k == len(need):
                return True
            cand = sorted((i for i in range(len(srcs)) if i not in used and need[k] in srcs[i]["cols"]),
                          key=lambda i: (srcs[i].get("treasure", False), len(srcs[i]["cols"])))
            for i in cand[:5]:
                used.append(i)
                if bt(k + 1):
                    return True
                used.pop()
            return False
        if not bt(0):
            return None
        rest = sorted((i for i in range(len(srcs)) if i not in used),
                      key=lambda i: (srcs[i].get("treasure", False), len(srcs[i]["cols"])))
        g = cost.get("g", 0)
        if len(rest) < g:
            return None
        return used + rest[:g]

    def can_pay(self, cost, reserve=None):
        a = self._alloc(cost, self.pool)
        if a is None:
            return False
        if reserve:
            rest = [s for i, s in enumerate(self.pool) if i not in a]
            return self._alloc(reserve, rest) is not None
        return True

    def pay(self, cost):
        a = self._alloc(cost, self.pool)
        if a is None:
            return False
        for i in sorted(a, reverse=True):
            if self.pool[i].get("treasure"):
                self.treasures -= 1
            self.pool.pop(i)
        return True

    def mana_count(self):
        return len(self.pool)

    def cost_of(self, c):
        d = card(c)
        cost = dict(d["cost"])
        is_ench = d["type"] in ("enchantment", "aura", "saga") or d.get("ench")
        if is_ench and self.has("jukai"):
            cost["g"] = max(0, cost["g"] - self.count_tag("jukai"))
        return cost

    # ---------------- permanents ----------------
    def enchantment_enters(self, name, cast=True):
        if self.has("eidolon"):
            self.draw(self.count_tag("eidolon"))
        if self.has("archon"):
            self.tokens.append({"power": 2, "kind": "fly", "sick": True})
        if self.has("boon"):
            self.tokens.append({"power": 1, "kind": "ground", "sick": True})

    def enter(self, c):
        d = card(c)
        t = d["type"]
        if t == "saga":
            self.add_saga(c)
            return
        self.perms.append(c)
        self.entered[c] = self.turn
        if t == "enchantment" or d.get("ench"):
            self.enchantment_enters(c)
        tags = d.get("tags", set())
        if "rock" in tags and d.get("prod"):
            self.pool += [{"cols": {"C"}}, {"cols": {"C"}}] if d["prod"] == "CC" else [{"cols": set(d["prod"])}]
        if "burst3" in tags:
            self.pool += [{"cols": {"C"}}] * 3
        if "vine" in tags:
            gates = [x for x in self.lib if LANDS.get(x, (0, 0, {}))[2].get("gate") and x not in self.gates()]
            if gates:
                g = gates[0]; self.lib.remove(g); self.hand.append(g)
        if "spelunking" in tags:
            self.draw(1)
            hl = [x for x in self.hand if x in LANDS]
            if hl:
                self.hand.remove(hl[0]); self.land_enters(hl[0])
        if "tom" in tags:
            self.tom = "bf"
        if "mirrormade" in tags:
            tgt = self.best_saga_to_copy()
            self.perms.remove(c)
            if tgt:
                self.st["mirrormade_saga"] = self.st.get("mirrormade_saga", 0) + 1
                self.log(f"  Mirrormade copies {tgt['name']}")
                tok = {"name": tgt["name"], "lore": 0, "copy": True}
                self.sagas.append(tok)
                self.add_lore(tok, 1)
            else:
                rock = next((x for x in ("Sol Ring", "Chromatic Lantern", "Arcane Signet", "Amulet of Vigor") if x in self.perms), None)
                if rock:
                    self.perms.append(rock); self.entered[rock] = self.turn
                else:
                    self.perms.append(c)
            return
        if "terra" in tags:
            for _ in range(5):
                if self.lib:
                    self.gy.append(self.lib.pop())
            en = [x for x in self.gy[-5:] if (card(x) or {}).get("type") in ("enchantment", "aura", "saga")]
            if en:
                self.gy.remove(en[0]); self.hand.append(en[0])

    def add_saga(self, name, copy=False):
        s = {"name": name, "lore": 0, "copy": copy}
        self.sagas.append(s)
        self.enchantment_enters(name)
        if self.has("ondu") and not self.ondu_used and not copy:
            self.ondu_used = True
            self.add_saga(name, copy=True)
        self.add_lore(s, 1)

    # ---------------- Sagas ----------------
    def add_lore(self, s, n=1, event=True):
        if event:
            self.counters_placed(1)
        for _ in range(n):
            if s not in self.sagas:
                return
            s["lore"] += 1
            ch = SAGAS[s["name"]]["ch"]
            k = s["lore"]
            if k <= len(ch):
                for eff in ch[k - 1]:
                    self.effect(eff, s)
                if k == len(ch):
                    self.final_chapter(s)

    def final_chapter(self, s):
        name = s["name"]
        if self.has("boon"):
            self.tokens.append({"power": 4, "kind": "fly", "sick": True})
        if self.has("narci"):
            self.lose_each(mv(name) * self.count_tag("narci"))
        if s in self.sagas:
            self.sagas.remove(s)
        self.st["sagas_done"] += 1
        if not s["copy"]:
            last = SAGAS[name]["ch"][-1][0][0]
            if last == "return_hand":
                self.hand.append(name)
            elif last == "terra_mana":
                self.enter("Terra, Magical Adept")
            elif last == "transform":
                self.tokens.append({"power": 6, "kind": "fly", "sick": False, "perm": True})
            else:
                self.gy.append(name)
        # Tom: reveal until a Saga, put it onto the battlefield (once per turn)
        if self.tom == "bf" and not self.tom_used:
            self.tom_used = True
            revealed = []
            while self.lib:
                c = self.lib.pop()
                if c in SAGAS or c == "Urza's Saga":
                    self.st["tom_reveals"] += 1
                    self.log(f"  Tom reveals {c}")
                    for r in revealed:
                        self.lib.insert(0, r)
                    if c == "Urza's Saga":
                        self.land_enters(c)
                    else:
                        self.add_saga(c)
                    return
                revealed.append(c)
            for r in revealed:
                self.lib.insert(0, r)

    def best_saga_to_copy(self, exclude=None):
        cands = [x for x in self.sagas if x is not exclude and x["name"] != "Esper Terra"]
        if not cands:
            return None
        # value a fresh full run: prefer sagas whose chapters are mostly still ahead, high MV
        return max(cands, key=lambda x: (mv(x["name"]) + 3 * (x["name"] in ("Summon: Bahamut", "There and Back Again", "Summon: Titan", "The World Spell")), x["name"]))

    def effect(self, eff, s):
        kind = eff[0]
        if kind == "lose2":
            self.lose_each(2, "yoh")
            self.life -= 2
            return
        if kind == "terra_copy":
            tgt = self.best_saga_to_copy(exclude=s)
            if tgt:
                self.st["terra_copies"] = self.st.get("terra_copies", 0) + 1
                self.log(f"  Esper Terra copies {tgt['name']}")
                tok = {"name": tgt["name"], "lore": 0, "copy": True}
                self.sagas.append(tok)
                self.enchantment_enters(tgt["name"])
                self.add_lore(tok, 1)
                self.add_lore(tok, 3)
                if tok in self.sagas:
                    self.sagas.remove(tok)
            return
        if kind == "terra_mana":
            self.terra_mana += 10
            return
        if kind == "terra_flip":
            return
        if kind == "token":
            pw, k = eff[1], eff[2]
            if k == "smaug":
                if any(t.get("smaug") for t in self.tokens):
                    self.treasures += 14
                    self.st["smaug_treasures"] += 14
                else:
                    self.tokens.append({"power": 6, "kind": "fly", "sick": False, "smaug": True})
            else:
                self.tokens.append({"power": pw, "kind": k, "sick": k != "haste"})
        elif kind == "remove":
            for _ in range(eff[1]):
                al = [i for i in self.alive() if self.board[i]]
                if not al:
                    break
                i = max(al, key=lambda k: max(self.board[k]))
                self.board[i].remove(max(self.board[i]))
        elif kind == "draw":
            self.draw(eff[1])
        elif kind == "mill":
            for _ in range(eff[1]):
                if self.lib:
                    self.gy.append(self.lib.pop())
        elif kind == "ramp":
            for b in ("Forest", "Mountain", "Island", "Swamp", "Plains"):
                if b in self.lib:
                    self.lib.remove(b)
                    self.land_enters(b, force_tapped=(b != "Mountain"))
                    break
        elif kind == "treasure":
            self.treasures += eff[1]
        elif kind == "copytoken":
            if self.tokens:
                best = max(self.tokens, key=lambda t: (t.get("smaug", False), t["power"]))
                if best.get("smaug"):
                    self.treasures += 14
                    self.st["smaug_treasures"] += 14
                else:
                    self.tokens.append(dict(best, sick=True, perm=False))
        elif kind == "gain":
            self.life += eff[1]
        elif kind == "dmg_mv":
            x = sum(mv(c) for c in self.perms) + sum(mv(x["name"]) for x in self.sagas if x is not s)
            self.lose_each(x, "bahamut")
            self.bahamut_x = x
        elif kind == "drain_gy":
            self.lose_each(2 + self.turn // 2, "ring")
        elif kind == "wipe_nonleg":
            self.board = [[], [], []]
            for c in list(self.perms):
                d = card(c)
                if d.get("type") == "creature" and c not in ("Tom Bombadil",) and not c.split(",")[0] in (
                        "Narci", "Satsuki", "Garnet", "Goldberry", "Xavier Sal", "Zur", "Terra", "Sythis", "O'aka"):
                    self.perms.remove(c)
                    self.gy.append(c)
                    for a, h in list(self.auras.items()):
                        if h == c:
                            del self.auras[a]
                            self.gy.append(a)
            self.tokens = [t for t in self.tokens if t.get("smaug")]
        elif kind == "tapall":
            self.no_block = 2
        elif kind == "tapall_one":
            al = [i for i in self.alive() if self.board[i]]
            if al:
                self.board[al[0]].remove(max(self.board[al[0]]))
        elif kind == "cheat2":
            perms = sorted([c for c in self.hand if c not in LANDS and c not in SAGAS and card(c)
                            and card(c)["type"] not in ("instant", "sorcery", "aura")], key=lambda c: -mv(c))[:2]
            for c in perms:
                if c in self.hand:
                    self.hand.remove(c)
                    self.enter(c)
        elif kind == "dig":
            top = self.lib[-7:]
            good = [c for c in top if c not in LANDS and c not in SAGAS and card(c) and card(c)["type"] not in ("instant", "sorcery")]
            if good:
                pick = max(good, key=self.tutor_score)
                self.lib.remove(pick)
                self.hand.append(pick)
        elif kind == "lands_back":
            for c in [x for x in self.gy if x in LANDS]:
                if c in self.gy:
                    self.gy.remove(c)
                    self.land_enters(c, force_tapped=True)
        elif kind == "odin":
            self.odin = True
        elif kind == "anthem":
            self.anthem += eff[1]

    def proliferate(self, n=1):
        for _ in range(n):
            events = len(self.sagas) + (1 if self.helix else 0)
            self.counters_placed(events)
            if self.helix:
                self.helix += 1
            for s in list(self.sagas):
                self.add_lore(s, 1, event=False)

    def advance_sagas(self):
        for s in list(self.sagas):
            self.add_lore(s, 1)
        for l in list(self.lands):
            if l.get("urza"):
                l["lore"] += 1
                self.counters_placed(1)
                if l["lore"] >= 3:
                    for c in ("Sol Ring", "Amulet of Vigor", "Hex Parasite"):
                        if c in self.lib:
                            self.lib.remove(c)
                            self.enter(c)
                            break
                    self.lands.remove(l)
                    self.gy.append(l["name"])
                    self.final_chapter_land()

    def final_chapter_land(self):
        if self.has("narci"):
            self.lose_each(0)
        if self.tom == "bf" and not self.tom_used:
            self.tom_used = True
            revealed = []
            while self.lib:
                c = self.lib.pop()
                if c in SAGAS or c == "Urza's Saga":
                    self.st["tom_reveals"] += 1
                    for r in revealed:
                        self.lib.insert(0, r)
                    if c == "Urza's Saga":
                        self.land_enters(c)
                    else:
                        self.add_saga(c)
                    return
                revealed.append(c)
            for r in revealed:
                self.lib.insert(0, r)

    # ---------------- combo detection ----------------
    def untap_combo(self):
        """Return (infinite?, infinite_blue?) from untap auras / equipment on mana creatures."""
        inf, blue = False, False
        for a, host in self.auras.items():
            if "untapaura" not in card(a)["tags"] or host not in self.perms or self.entered.get(host, 99) >= self.turn:
                continue
            tags = card(host)["tags"]
            if "sage" in tags:
                inf = blue = True
            elif "weaver" in tags and self.enchantments() >= 2:
                inf = blue = True
            elif "bloom" in tags and len(self.colors_among()) >= 2:
                inf = True
        dorks = [c for c in self.perms if "bloom" in card(c)["tags"] and self.entered.get(c, 99) < self.turn]
        if self.has("mantle") and any(len(self.colors_among()) >= 4 for _ in dorks):
            inf = True
            blue = blue or "U" in self.colors_among()
        if self.has("staff") and (dorks and len(self.colors_among()) >= 3 or any(
                "sage" in card(c)["tags"] for c in self.perms if self.entered.get(c, 99) < self.turn)):
            inf = True
            blue = blue or "U" in self.colors_among()
        if self.has("scepter_reversal"):
            producers = sum(1 for s in self.pool if not s.get("land") and not s.get("treasure"))
            if producers >= 3:
                inf = blue = True
        return inf, blue

    def payoff_now(self, blue):
        """With infinite mana (blue if flagged), can we win this turn?"""
        if self.on_bf("Helix Pinnacle") or "Helix Pinnacle" in self.hand:
            if self.has("awbo") or "All Will Be One" in self.hand:
                return "helix+awbo"
        if "Walking Ballista" in self.hand or self.on_bf("Walking Ballista"):
            return "ballista"
        if blue and "Clockspinning" in self.hand:
            if self.has("awbo") or "All Will Be One" in self.hand:
                return "clock+awbo"
            if self.sagas and (self.has("narci") or "Narci, Fable Singer" in self.hand):
                return "clock+narci"
            if any(s["name"] in ("Summon: Bahamut", "Battle at the Helvault", "The Kami War") for s in self.sagas):
                return "clock+saga"
            if any(s["name"] == "There and Back Again" for s in self.sagas) and (
                    self.has("boon") or "Historian's Boon" in self.hand):
                return "clock+smaug+boon"
        return None

    def disruption(self):
        p = self.p["disrupt"]
        if self.has("spinner"):
            p *= 0.7
        protect = [c for c in self.hand if "counter" in (card(c) or {}).get("tags", ())]
        if protect and self.mana_count() >= 2:
            p *= 0.55
        return self.rng.random() < p

    def try_combos(self):
        if self.turn < self.combo_from:
            return
        inf, blue = self.untap_combo()
        taba = next((s for s in self.sagas if s["name"] == "There and Back Again"), None)
        if not inf and taba and "Clockspinning" in self.hand:
            need = 8 if self.taba_ch3_now else 12
            if taba["lore"] >= 2 and self.mana_count() >= need:
                inf = blue = True
                self.via = "taba"
        if inf:
            how = self.payoff_now(blue)
            if how is None and (self.on_bf("Helix Pinnacle") or "Helix Pinnacle" in self.hand):
                how = "helix_pending"
            if how:
                self.st["combo_attempts"] += 1
                if self.st["first_combo"] is None:
                    self.st["first_combo"] = self.turn
                if self.disruption():
                    self.st["disrupted"] += 1
                    # lose a piece
                    if self.auras:
                        a = next(iter(self.auras))
                        del self.auras[a]
                        self.gy.append(a)
                    elif "Clockspinning" in self.hand:
                        self.hand.remove("Clockspinning"); self.gy.append("Clockspinning")
                    self.log("  combo disrupted")
                    return
                if how == "helix_pending":
                    if "Helix Pinnacle" in self.hand:
                        self.hand.remove("Helix Pinnacle"); self.perms.append("Helix Pinnacle")
                    self.helix = 100
                    self.helix_pending = True
                    self.log("  Helix Pinnacle to 100")
                    return
                raise Won("combo:" + how)
        # Bahamut chapter IV re-triggers
        if self.bahamut_x and "Clockspinning" in self.hand:
            extra = self.mana_count() // 8
            if extra and self.bahamut_x * extra >= max(self.opp[i] for i in self.alive()):
                self.st["combo_attempts"] += 1
                if not self.disruption():
                    raise Won("combo:bahamut")
                self.st["disrupted"] += 1
        # Maze's End
        if len(set(self.gates())) >= 10 and any(l.get("gate_mazes") for l in self.lands):
            raise Won("mazes_end")

    # ---------------- tutors ----------------
    def tutor_score(self, c):
        """How much a card helps right now (for tutors / digs)."""
        inf, blue = self.untap_combo()
        have = set(self.hand) | set(self.perms) | {s["name"] for s in self.sagas} | set(self.auras)
        dorks = [x for x in have if "dork" in (card(x) or {}).get("tags", ())]
        aura = any("untapaura" in (card(x) or {}).get("tags", ()) for x in have)
        score = {"Helix Pinnacle": 6, "All Will Be One": 5, "Clockspinning": 5, "Freed from the Real": 6,
                 "Pemmin's Aura": 5, "Sage of the Maze": 6, "Bloom Tender": 5, "Sanctum Weaver": 5,
                 "There and Back Again": 4, "Tom Bombadil": 3, "Narci, Fable Singer": 4}.get(c, 1)
        if c in ("Freed from the Real", "Pemmin's Aura") and dorks and not aura:
            score += 6
        if c in ("Sage of the Maze", "Bloom Tender", "Sanctum Weaver", "Faeburrow Elder") and aura and not dorks:
            score += 6
        if c == "Walking Ballista":
            score = 15 if inf else 3
        if c == "Helix Pinnacle" and inf:
            score += 10
        if c in ("All Will Be One",) and inf:
            score += 9
        if c == "Clockspinning" and any(s["name"] == "There and Back Again" for s in self.sagas):
            score += 8
        if c in have:
            score = 0
        return score

    def tutor(self, pool_filter=None, to_top=False, to_bf=False):
        cands = [c for c in set(self.lib) if c not in LANDS and (pool_filter is None or pool_filter(c))]
        if not cands:
            return
        pick = max(sorted(cands), key=self.tutor_score)
        self.lib.remove(pick)
        self.rng.shuffle(self.lib)
        if to_bf:
            self.enter(pick)
        elif to_top:
            self.lib.append(pick)
        else:
            self.hand.append(pick)

    # ---------------- casting ----------------
    def prio(self, c):
        d = card(c)
        if d is None:
            return -5
        tags = d.get("tags", set())
        t = d["type"]
        if tags & {"rock", "burst3", "dork", "dork1", "sprawl"}:
            return 95 if self.turn <= 6 else 40
        if "untapaura" in tags:
            host = self.best_host()
            return 92 if host else -1
        if "ballista" in tags:
            return -1
        if tags & {"helix"}:
            return -1 if not self.untap_combo()[0] else 99
        if tags & {"tutor", "trans3", "trans2", "enchtutor", "enchtutor2", "finale", "gsz", "creaturetutor",
                   "scroll", "ptutor", "etutor", "mtutor", "wtutor", "grove"}:
            return 85
        if "tom" in tags:
            return 80
        if tags & {"amulet", "omen", "spelunking", "jukai", "eidolon", "sythis", "presence", "narci", "evosage",
                   "awbo", "spinner", "ring", "remora", "boon", "archon", "satsuki", "vine", "ondu", "harmony",
                   "mantle", "staff", "scepter", "tithe", "rhystic", "doubling"}:
            return 75
        if t == "saga":
            return 70 + mv(c)
        if tags & {"counter", "clock", "croprot", "reversal"}:
            return -1
        if tags & {"landtutor", "explore", "eerie", "mirrormade", "moleman"}:
            return 50
        return 30

    def best_host(self):
        hosts = [c for c in self.perms if "dork" in card(c)["tags"] and not any(h == c for h in self.auras.values())]
        if not hosts:
            return None
        order = {"sage": 0, "weaver": 1, "bloom": 2}
        def k(c):
            tags = card(c)["tags"]
            for t, v in order.items():
                if t in tags:
                    return v
            return 9
        return min(hosts, key=k)

    def cast(self, c):
        d = card(c)
        self.hand.remove(c)
        self.log(f"cast {c}")
        t = d["type"]
        tags = d.get("tags", set())
        is_ench = t in ("enchantment", "aura", "saga") or d.get("ench")
        if is_ench:
            if self.has("sythis") or self.has("presence"):
                self.draw(self.count_tag("sythis") + self.count_tag("presence"))
        if t == "aura":
            if "untapaura" in tags:
                host = self.best_host()
                if host:
                    self.auras[c] = host
                    self.enchantment_enters(c)
                    return
            if "sprawl" in tags:
                self.perms.append(c)
                self.pool.append({"cols": set(ANY)})
                return
            self.gy.append(c)
            return
        if t in ("instant", "sorcery"):
            self.gy.append(c)
            self.resolve_spell(c, tags)
            return
        self.enter(c)

    def resolve_spell(self, c, tags):
        if "tutor" in tags:
            if c == "Grim Tutor":
                self.life -= 3
            self.tutor()
            if "gamble" in tags and self.hand:
                self.gy.append(self.hand.pop(self.rng.randrange(len(self.hand))))
        elif "trans3" in tags:
            self.tutor(lambda x: mv(x) == 3)
        elif "trans2" in tags:
            self.tutor(lambda x: mv(x) == 2)
        elif "enchtutor" in tags:
            self.tutor(lambda x: (card(x) or {}).get("type") in ("enchantment", "aura", "saga"))
        elif "enchtutor2" in tags:
            self.tutor(lambda x: (card(x) or {}).get("type") in ("enchantment", "aura", "saga"))
            self.tutor(lambda x: (card(x) or {}).get("type") in ("enchantment", "aura", "saga"))
        elif tags & {"finale", "gsz"}:
            self.tutor(lambda x: (card(x) or {}).get("type") == "creature" and mv(x) <= 3 and x != "Walking Ballista", to_bf=True)
        elif "creaturetutor" in tags:
            self.tutor(lambda x: (card(x) or {}).get("type") == "creature")
        elif "scroll" in tags:
            self.tutor(lambda x: x in ("Clockspinning", "Counterspell", "Muddle the Mixture", "Perplex", "Dramatic Reversal"))
        elif tags & {"ptutor", "mtutor"}:
            self.tutor(lambda x: (card(x) or {}).get("type") in ("instant", "sorcery"), to_top=True)
        elif "etutor" in tags:
            self.tutor(lambda x: (card(x) or {}).get("type") in ("enchantment", "aura", "saga", "artifact"), to_top=True)
        elif "wtutor" in tags:
            self.tutor(lambda x: (card(x) or {}).get("type") == "creature", to_top=True)
        elif "landtutor" in tags:
            self.land_tutor(to_hand=True)
        elif "explore" in tags:
            for _ in range(2):
                g = [x for x in self.lib if LANDS.get(x, (0, 0, {}))[2].get("gate") and x not in self.gates()]
                if g:
                    self.lib.remove(g[0]); self.land_enters(g[0], force_tapped=True)
        elif "eerie" in tags:
            back = []
            for x in list(self.gy):
                if x not in LANDS and card(x) and card(x)["type"] not in ("instant", "sorcery") and x not in back:
                    back.append(x)
            for x in back:
                if x not in self.gy:
                    continue
                self.gy.remove(x)
                if card(x)["type"] == "aura":
                    host = self.best_host()
                    if host and "untapaura" in card(x)["tags"]:
                        self.auras[x] = host
                    continue
                self.enter(x)

    def land_tutor(self, to_hand=True):
        want = []
        if any(l.get("gate_mazes") for l in self.lands) or len(set(self.gates())) >= 6:
            want = [x for x in self.lib if LANDS.get(x, (0, 0, {}))[2].get("gate") and x not in self.gates()]
        if not any(l.get("gate_mazes") for l in self.lands) and "Maze's End" in self.lib and len(set(self.gates())) >= 5:
            want = ["Maze's End"]
        for x in ("Gond Gate", "Urza's Saga", "Command Tower"):
            if not want and x in self.lib:
                want = [x]
        if want:
            self.lib.remove(want[0])
            if to_hand:
                self.hand.append(want[0])
            else:
                self.land_enters(want[0])

    def cast_tom(self):
        if self.tom != "cz":
            return False
        cost = {"g": self.tom_tax, "W": 1, "U": 1, "B": 1, "R": 1, "G": 1}
        if self.can_pay(cost):
            self.pay(cost)
            self.tom_tax += 2
            self.tom = "bf"
            self.entered["Tom Bombadil"] = self.turn
            self.log("cast Tom")
            return True
        return False

    def main_phase(self):
        for _ in range(40):
            self.try_combos()
            if self.cast_tom():
                continue
            cands = sorted({c for c in self.hand if c not in LANDS and self.prio(c) >= 0}, key=lambda c: -self.prio(c))
            res = None
            if any("counter" in (card(c) or {}).get("tags", ()) for c in self.hand) and self.untap_combo()[0]:
                res = {"g": 1, "U": 1}
            done = False
            for c in cands:
                cost = self.cost_of(c)
                if self.can_pay(cost, reserve=res):
                    self.pay(cost)
                    self.cast(c)
                    done = True
                    break
            if not done:
                break
        # Isochron Scepter + Dramatic Reversal
        if self.has("scepter") and "Dramatic Reversal" in self.hand and "Scepter+Reversal" not in self.perms:
            self.hand.remove("Dramatic Reversal")
            self.perms.append("Scepter+Reversal")
        self.try_combos()

    def activations(self):
        # Return of the Mole Man: {5}{G}, sacrifice: X 1/1 Moloids, X = permanent cards in graveyard (sorcery)
        if "Return of the Mole Man" in self.perms:
            x = sum(1 for c in self.gy if c in LANDS or (card(c) and card(c)["type"] not in ("instant", "sorcery")))
            if x >= 6 and self.can_pay({"g": 5, "G": 1}):
                self.pay({"g": 5, "G": 1})
                self.perms.remove("Return of the Mole Man"); self.gy.append("Return of the Mole Man")
                self.tokens += [{"power": 1, "kind": "ground", "sick": True} for _ in range(x)]
                self.st["moloids"] = self.st.get("moloids", 0) + x
                self.log(f"  Return of the Mole Man: {x} Moloids")
        # Terra's Trance: {4}{R}{G}, T: transform into Esper Terra (sorcery speed)
        if TRANCE and "Terra, Magical Adept" in self.perms and self.ready("Terra, Magical Adept") and \
                any(x["name"] != "Esper Terra" for x in self.sagas) and self.can_pay({"g": 4, "R": 1, "G": 1}):
            self.pay({"g": 4, "R": 1, "G": 1})
            self.perms.remove("Terra, Magical Adept")
            self.st["trances"] = self.st.get("trances", 0) + 1
            self.log("  Terra trances into Esper Terra")
            self.add_saga("Esper Terra")
        # Satsuki: lore counter on each Saga (sorcery speed)
        for c in list(self.perms):
            tags = card(c)["tags"] if card(c) else set()
            if "satsuki" in tags and self.ready(c) and self.sagas:
                for s in list(self.sagas):
                    self.add_lore(s, 1)
            if "xavier" in tags and self.ready(c) and self.tokens and self.sagas:
                self.tokens.remove(min(self.tokens, key=lambda t: t["power"]))
                self.proliferate(1)
        # Maze's End: fetch a Gate
        for l in list(self.lands):
            if l.get("gate_mazes") and not l["tapped"]:
                src = next((s for s in self.pool if s.get("land") == "Maze's End"), None)
                if src:
                    self.pool.remove(src)
                    if self.can_pay({"g": 3}):
                        self.pay({"g": 3})
                        self.lands.remove(l)
                        self.hand.append("Maze's End")
                        g = [x for x in self.lib if LANDS.get(x, (0, 0, {}))[2].get("gate") and x not in self.gates()]
                        if g:
                            self.lib.remove(g[0]); self.land_enters(g[0])
                        if len(set(self.gates())) >= 10:
                            raise Won("mazes_end")
                    else:
                        self.pool.append(src)
        # Crop Rotation: trade a basic for Maze's End / Gond Gate when useful
        if "Crop Rotation" in self.hand and self.can_pay({"G": 1}):
            basics = [l for l in self.lands if l.get("basic")]
            if basics and ("Maze's End" in self.lib and len(set(self.gates())) >= 6 or "Urza's Saga" in self.lib):
                self.pay({"G": 1})
                self.hand.remove("Crop Rotation"); self.gy.append("Crop Rotation")
                self.lands.remove(basics[0]); self.gy.append(basics[0]["name"])
                self.land_tutor(to_hand=False)
        # Destiny Spinner: animate a land with spare mana late
        # Sterling Grove: sac to put an enchantment on top
        if self.has("grove") and self.can_pay({"g": 1}):
            inf, _ = self.untap_combo()
            have = set(self.hand) | set(self.perms) | set(self.auras)
            need = [x for x in ("Freed from the Real", "Helix Pinnacle", "All Will Be One") if x not in have and x in self.lib]
            if need and (self.best_host() or inf):
                self.pay({"g": 1})
                self.perms.remove("Sterling Grove"); self.gy.append("Sterling Grove")
                self.tutor(lambda x: x == need[0], to_top=True)

    # ---------------- combat ----------------
    def combat(self):
        attackers = []
        for t in self.tokens:
            if not t.get("sick"):
                attackers.append((t["power"] + self.anthem, t["kind"]))
        for c in self.perms:
            d = card(c)
            if d and d.get("type") == "creature" and self.ready(c) and not (d["tags"] & {"dork", "dork1", "tom"}):
                kind = "fly" if d.get("fly") else "ground"
                attackers.append((d.get("power", 1) + self.anthem, kind))
        for s in self.sagas:
            cr = SAGAS[s["name"]].get("creature")
            if cr and s.get("ready", False):
                attackers.append((cr[0] + self.anthem, "fly" if cr[1] == "fly" else ("trample" if cr[1] == "trample" else "ground")))
                if s["name"] == "Summon: Primal Odin" and self.odin:
                    self.odin_attack = True
        if not attackers or not self.alive():
            return
        i = min(self.alive(), key=lambda k: self.opp[k])
        blockers = [] if self.no_block else sorted(self.board[i])
        dmg = 0
        for pw, kind in sorted(attackers, key=lambda a: -a[0]):
            if kind in ("fly", "hexfly"):
                blocked = blockers and self.rng.random() < 0.25
            elif kind == "menace":
                blocked = len(blockers) >= 2 and self.rng.random() < 0.6
            else:
                blocked = bool(blockers) and pw >= 2
            if blocked and blockers:
                b = blockers.pop(0)
                if kind == "trample":
                    dmg += max(0, pw - b[1])
                if pw >= b[1] and b in self.board[i]:
                    self.board[i].remove(b)
            else:
                dmg += pw
        if dmg:
            self.opp[i] -= dmg
            self.st["combat_dmg"] += dmg
            if getattr(self, "odin_attack", False):
                self.opp[i] = 0
            self.check()

    # ---------------- opponents ----------------
    def opponents(self):
        for i in range(3):
            if self.opp[i] <= 0:
                continue
            if self.turn >= 2 and self.rng.random() < self.p["creature_rate"]:
                pw = self.rng.choice([1, 1, 2, 2, 3, 3, 4, 5, 6])
                self.board[i].append((pw, max(1, pw + self.rng.choice([-1, 0, 0, 1]))))
            if self.has("remora") and self.rng.random() < 0.5:
                self.draw(1)
            if self.has("tithe") and self.rng.random() < 0.6:
                self.treasures += 1
            if self.has("rhystic") and self.rng.random() < 0.7:
                self.draw(1)
            if self.turn < 3:
                continue
            r = self.rng.random()
            p = self.p
            if r < p["wipe"] and self.turn >= 4:
                for c in list(self.perms):
                    d = card(c)
                    if d.get("type") == "creature":
                        if c == "Tom Bombadil" and self.tom_protected():
                            continue
                        self.perms.remove(c)
                        self.gy.append(c)
                        if c == "Tom Bombadil":
                            self.tom = "cz"
                if self.tom == "bf" and not self.tom_protected():
                    self.tom = "cz"
                for a, h in list(self.auras.items()):
                    if h not in self.perms:
                        del self.auras[a]; self.gy.append(a)
                self.tokens = []
                self.sagas = [s for s in self.sagas if not SAGAS[s["name"]].get("creature")]
            elif r < p["wipe"] + p["removal"]:
                # targeted removal: combo creature first, then Tom, then the best token
                hosts = [h for h in self.auras.values() if h in self.perms]
                dorks = [c for c in self.perms if "dork" in card(c)["tags"]]
                if hosts:
                    v = hosts[0]
                elif self.tom == "bf" and not self.tom_protected():
                    v = "Tom Bombadil"
                elif dorks:
                    v = dorks[0]
                elif self.tokens:
                    self.tokens.remove(max(self.tokens, key=lambda t: t["power"]))
                    continue
                else:
                    continue
                if v == "Tom Bombadil":
                    self.tom = "cz"
                else:
                    self.perms.remove(v)
                    self.gy.append(v)
                for a, h in list(self.auras.items()):
                    if h == v:
                        del self.auras[a]; self.gy.append(a)
            elif r < p["wipe"] + p["removal"] + p["ench"]:
                for target in ("Helix Pinnacle", "All Will Be One"):
                    if target in self.perms and target != "Helix Pinnacle":   # Helix has shroud
                        self.perms.remove(target); self.gy.append(target)
                        break
                else:
                    if self.auras:
                        a = next(iter(self.auras)); del self.auras[a]; self.gy.append(a)
                    elif self.sagas:
                        s = max(self.sagas, key=lambda s: mv(s["name"]))
                        self.sagas.remove(s); self.gy.append(s["name"])
        if self.helix_pending and self.rng.random() < self.p["ench"] * 0.5:
            # a board-wide enchantment answer gets around shroud
            self.helix_pending = False
            self.helix = 0
            if "Helix Pinnacle" in self.perms:
                self.perms.remove("Helix Pinnacle"); self.gy.append("Helix Pinnacle")

    # ---------------- turn ----------------
    def my_turn(self):
        self.turn += 1
        self.tom_used = False
        self.ondu_used = False
        self.anthem = 0
        self.bahamut_x = 0
        self.taba_ch3_now = False
        self.odin_attack = False
        for l in self.lands:
            l["tapped"] = False
        for t in self.tokens:
            t["sick"] = False
        for s in self.sagas:
            s["ready"] = True
        if self.helix_pending and self.helix >= 100:
            raise Won("helix")
        if not (self.turn == 1 and self.on_play):
            self.draw(1)
        if self.has("ring"):
            self.ring += 1
            self.draw(self.ring)
        self.pool = []
        played = False
        taba = next((s for s in self.sagas if s["name"] == "There and Back Again"), None)
        if taba and taba["lore"] == 2 and "Clockspinning" in self.hand:
            self.taba_ch3_now = True
            # hold the chapter III trigger: Clockspinning loop happens with this turn's mana
            self.play_land()
            played = True
            self.pool = self.build_pool()
            self.try_combos()
        self.advance_sagas()
        if not played:
            self.play_land()
        self.pool = self.build_pool()
        if self.terra_mana:
            for col in "WUBRG":
                self.pool += [{"cols": {col}}, {"cols": {col}}]
            self.terra_mana = 0
        self.main_phase()
        self.activations()
        self.combat()
        self.no_block = max(0, self.no_block - 1)
        self.main_phase()
        while len(self.hand) > 7:
            junk = sorted(self.hand, key=lambda c: (c not in LANDS, self.prio(c)))
            self.gy.append(junk[0]); self.hand.remove(junk[0])

    def run(self, max_turns=16):
        try:
            for _ in range(max_turns):
                self.my_turn()
                self.opponents()
        except Won as w:
            self.st["win"] = self.turn
            self.st["how"] = w.how
        return self.st
