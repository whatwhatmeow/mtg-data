"""Monte Carlo simulator for Namor the Sub-Mariner mono-blue Merfolk (v1, Oct 27 2026).

Same table model as the vault's Winter Soldier sim so numbers line up:
Win = all three opponents dead (40 life each, or 21 Namor commander damage).
Opponents add creatures (some with flying/reach) and fire targeted removal, wipes
and artifact removal at the bracket profile rates. They do not attack you or race.

Modeled: Namor's power and token triggers (blue pips of noncreature spells), lords,
islandwalk (blue opponents + Tideshaper), unblockable (Herald, Sovereign, Daughter, Pym),
flying (Mist Dancer, Scourge counters, Zephyr Boots), connive, second-draw payoffs,
draw engines (Bident, Attuma, Svyelun, Super Intelligence, Idol, Baxter, Looter),
bounce/freeze/stun on blockers, instant-speed play on opponents' turns, counterspells
protecting the board from removal and wipes, Kopala/Svyelun ward taxes.
"""
import random
from nm_cards import C, LANDS, COMMANDER

COLORS = ["W", "U", "B", "R", "G"]
PROFILES = {
    "bracket2": dict(removal=0.05, wipe=0.02, art=0.03, creature_rate=0.55),
    "bracket3": dict(removal=0.08, wipe=0.03, art=0.04, creature_rate=0.60),
    "bracket4": dict(removal=0.15, wipe=0.05, art=0.07, creature_rate=0.70),
}
LORD_BONUS = {"Lord of Atlantis", "Master of the Pearl Trident", "Merrow Reejerey",
              "Merfolk Sovereign", "Attuma, Atlantean Warlord"}
KEY = {"lord", "svyelun", "scourge", "dancer"}


class Won(Exception):
    pass


def info(name):
    return C.get(name)


class Game:
    def __init__(self, deck, prof, rng, log=False, b2b_effect=0.10):
        self.rng, self.p, self.logging, self.lines = rng, prof, log, []
        self.b2b_effect = b2b_effect
        self.lib = list(deck)
        rng.shuffle(self.lib)
        self.hand, self.gy = [], []
        self.lands = []            # dicts: name, tapped, island, colorless
        self.arts = []             # dicts: name, tapped
        self.ench = []             # names
        self.cr = []               # creature dicts
        self.namor_cz, self.tax = True, 0
        self.opp = [40, 40, 40]
        self.cmd = [0, 0, 0]
        self.board = [[], [], []]
        self.bounced = [[], [], []]
        self.blue = [rng.random() < 0.40 for _ in range(3)]
        self.turn = 0
        self.clock = 0.0           # entry stamp; my turn T = T, opp turns T+0.25..
        self.on_play = rng.random() < 0.25
        self.U = self.Cl = 0
        self.draws_now = 0
        self.token_made = False
        self.idol_ready = False
        self.uid = 0
        self.super_on = None
        self.tide_on = None
        self.boots_on = None
        self.swift_on = None
        self.incub = []            # Incubator tokens waiting for {2} (Chrome Host Seedshark): counters on each
        self.st = dict(win=None, namor_cast=0, namor_removed=0, countered=0, wiped=0,
                       tokens=0, drawn=0, max_namor=0, first_hit=None)
        self.mulligan()

    # ---------------- utils ----------------
    def log(self, s):
        if self.logging:
            self.lines.append(f"T{self.turn}: {s}")

    def alive(self):
        return [i for i in range(3) if self.opp[i] > 0 and self.cmd[i] < 21]

    def check(self):
        if not self.alive():
            raise Won()

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
                    pick = lands[-1] if len(lands) > 4 or not sp else min(sp, key=self.prio)
                    self.hand.remove(pick)
                    self.lib.insert(0, pick)
                return

    def on_board(self, name):
        return any(c["name"] == name for c in self.cr)

    def tag_on(self, tag):
        return [c for c in self.cr if tag in c["tags"]]

    def namors(self):
        return [c for c in self.cr if c.get("namor")]

    def merfolk(self):
        return [c for c in self.cr if c["merfolk"]]

    # ---------------- draws ----------------
    def draw(self, n=1):
        for _ in range(n):
            if not self.lib:
                return
            self.hand.append(self.lib.pop())
            self.st["drawn"] += 1
            self.draws_now += 1
            for c in self.tag_on("skulker"):
                c["ctr"] += 1
            if self.draws_now == 2:
                for c in self.tag_on("daughter"):
                    self.token("Merfolk", 1, 1)
                for c in self.tag_on("second_counter"):
                    c["ctr"] += 1

    def best_spells_from(self, cards, k):
        lands_bf = len(self.lands)
        def val(c):
            if c in LANDS:
                return 5 if lands_bf + sum(x in LANDS for x in self.hand) < 6 else -5
            return self.prio(c)
        s = sorted(cards, key=val, reverse=True)
        return s[:k], s[k:]

    def look_take(self, n, k):
        top = [self.lib.pop() for _ in range(min(n, len(self.lib)))]
        take, rest = self.best_spells_from(top, k)
        for c in take:
            self.lib.append(c)
        self.draw(len(take))
        for c in rest:
            self.lib.insert(0, c)

    def discard_worst(self, n=1):
        for _ in range(n):
            if not self.hand:
                return None
            lands_total = len(self.lands) + sum(c in LANDS for c in self.hand)
            if lands_total >= 7 and any(c in LANDS for c in self.hand):
                pick = next(c for c in self.hand if c in LANDS)
            else:
                pick = min(self.hand, key=lambda c: (self.prio(c) if c not in LANDS else 3))
            self.hand.remove(pick)
            self.gy.append(pick)
            return pick

    def connive(self, c):
        self.draw(1)
        d = self.discard_worst(1)
        if d and d not in LANDS:
            c["ctr"] += 1

    # ---------------- creatures ----------------
    def new_creature(self, name, p, t, merfolk, tags, token=False, namor=False):
        self.uid += 1
        c = dict(id=self.uid, name=name, bp=p, bt=t, merfolk=merfolk, tags=set(tags), ctr=0,
                 token=token, namor=namor, entered=self.clock, tapped=False, ub=False)
        self.cr.append(c)
        if merfolk and "Kindred Discovery" in self.ench:
            self.draw(self.ench.count("Kindred Discovery"))
        return c

    def token(self, kind, p, t, merfolk=True, tags=()):
        self.st["tokens"] += 1
        self.token_made = True
        return self.new_creature(kind, p, t, merfolk, tags, token=True)

    def power(self, c):
        p = c["bp"] + c["ctr"]
        if c.get("namor"):
            p = len(self.merfolk()) + c["ctr"]
        if c["merfolk"]:
            for o in self.cr:
                if o is not c and o["name"] in LORD_BONUS and not o["token"] or (o is not c and o.get("copyof") in LORD_BONUS):
                    p += 1
                if o is not c and "dancer" in o["tags"]:
                    p += 1
            p += sum(1 for a in self.arts if a["name"] == "Patchwork Banner")
        return p

    def tough(self, c):
        t = c["bt"] + c["ctr"]
        if c["merfolk"]:
            for o in self.cr:
                if o is not c and (o["name"] in LORD_BONUS and not o["token"] or o.get("copyof") in LORD_BONUS):
                    t += 1
            t += sum(1 for a in self.arts if a["name"] == "Patchwork Banner")
        return t

    def flying(self, c):
        if "flying" in c["tags"] or c.get("namor"):
            return True
        if self.boots_on == c["id"]:
            return True
        if c["merfolk"]:
            if any("dancer" in o["tags"] and o is not c for o in self.cr):
                return True
            if c["ctr"] > 0 and any("scourge" in o["tags"] and o is not c for o in self.cr):
                return True
        return False

    def walk(self, c, i):
        if not (self.blue[i] or self.tide_on == i):
            return False
        if "islandwalk" in c["tags"]:
            return True
        if not c["merfolk"]:
            return False
        return any("walk" in o["tags"] and o is not c for o in self.cr)

    def evasive(self, c, i):
        if c["ub"] or "unblockable" in c["tags"] or self.walk(c, i):
            return "ub"
        if self.flying(c):
            return "fly"
        return None

    def indestructible(self, c):
        return "svyelun" in c["tags"] and len([m for m in self.merfolk() if m is not c]) >= 2

    def leave(self, c, how="destroy"):
        if c not in self.cr:
            return
        self.cr.remove(c)
        if self.super_on == c["id"]:
            self.super_on = None
            self.ench.remove("Super Intelligence")
            self.gy.append("Super Intelligence")
        if self.boots_on == c["id"]:
            self.boots_on = None
        if self.swift_on == c["id"]:
            self.swift_on = None
        if c.get("namor") and not c["token"]:
            self.namor_cz = True
            self.tax += 2
        elif not c["token"]:
            self.gy.append(c["name"])
        if "skulker" in c["tags"] and c["ctr"]:
            for _ in range(c["ctr"]):
                self.token("Squid", 1, 1, merfolk=False, tags=("islandwalk",))

    # ---------------- mana ----------------
    def build_pool(self, high_tide=False):
        U = Cl = 0
        for l in self.lands:
            if l["tapped"]:
                continue
            if l.get("colorless"):
                Cl += 1
            else:
                U += 1
        for a in self.arts:
            if a["tapped"] or C[a["name"]]["kind"] not in ("rock", "horn"):
                continue
            if a["name"] == "Herald's Horn":
                continue
            if "sol" in C[a["name"]]["tags"]:
                Cl += 2
            elif "cless" in C[a["name"]]["tags"]:
                Cl += 1
            else:
                U += 1
        self.U, self.Cl = U, Cl

    def cost_of(self, name):
        d = C[name]
        g, u = d["cost"], d["u"]
        if name == COMMANDER:
            g += self.tax
        if d["type"] == "creature" and d["merfolk"]:
            g -= len(self.tag_on("banneret"))
            g -= sum(1 for a in self.arts if a["name"] == "Herald's Horn")
        return max(0, g), u

    def can_pay(self, g, u, reserve=(0, 0)):
        rg, ru = reserve
        U, Cl = self.U - ru, self.Cl
        if U < u:
            return False
        free_c = Cl - 0
        need = g + rg
        return (U - u) + free_c >= need

    def pay(self, g, u):
        self.U -= u
        use_c = min(self.Cl, g)
        self.Cl -= use_c
        self.U -= g - use_c

    def total(self):
        return self.U + self.Cl

    # ---------------- priorities ----------------
    def prio(self, name):
        if name in LANDS:
            return 0
        d = C.get(name)
        if d is None:
            return 0
        if name == "BLANK":
            return -9
        if d["type"] == "creature":
            base = 6 if d["merfolk"] else 3
            if d["tags"] & {"lord", "svyelun", "scourge", "dancer"}:
                base = 9
            if d["tags"] & {"noattack"}:
                base = 4
            return base
        k = d["kind"]
        table = dict(rock=7, counter=6, kindred=8, bident=8, horn=7, piracy=7, superint=6, incursion=7,
                     leviathan=6, newhero=6, stockup=5, dig=5, fof=5, brainstorm=4, crescendo=7,
                     hightide=3, whoosh=4, peel=4, bounce=3, bounce_draw=4, crashing=5, freeze=4,
                     shrink=2, pym=4, unstable=4, draw1=3, manifest=3, extract=5, cabinet=4, idol=4,
                     boots=3, swiftfoot=5, kill=5, melody=6, b2b=4, aetherize=1, blank=-9,
                     cruise=5, inquiry=5, thirst=4, gauntlet=6)
        return table.get(k, 3)

    # ---------------- land ----------------
    def islands(self):
        return sum(1 for l in self.lands if l.get("island"))

    def play_land(self):
        lands = [c for c in self.hand if c in LANDS]
        if not lands:
            return
        def score(n):
            L = LANDS[n]
            if n == "Island":
                return 10
            if n == "Mystic Sanctuary":
                return 11 if self.islands() >= 3 and any(C.get(g, {}).get("type") in ("instant", "sorcery") for g in self.gy) else 6
            if n == "Fabled Passage":
                return 9 if len(self.lands) >= 3 else 7
            if L.get("colorless"):
                return 8
            return 5
        n = max(lands, key=score)
        self.hand.remove(n)
        L = LANDS[n]
        if L.get("fetch"):
            if "Island" in self.lib:
                self.lib.remove("Island")
                self.rng.shuffle(self.lib)
                untap = n == "Fabled Passage" and len(self.lands) + 1 >= 4
                self.lands.append(dict(name="Island", tapped=not untap, island=True))
            self.gy.append(n)
            return
        tapped = False
        if L.get("cond_tapped") == "islands3":
            tapped = self.islands() < 3
            if not tapped:
                spells = [g for g in self.gy if C.get(g, {}).get("type") in ("instant", "sorcery")]
                if spells:
                    best = max(spells, key=self.prio)
                    self.gy.remove(best)
                    self.lib.append(best)
        self.lands.append(dict(name=n, tapped=tapped, island=L.get("island", False),
                               colorless=L.get("colorless", False)))

    # ---------------- casting ----------------
    def namor_trigger(self, name):
        d = C[name]
        if d["type"] == "creature":
            return
        pips = d.get("pips", 0)
        mv = d["cost"] + d["u"]
        if mv > 0:
            for _ in self.tag_on("seedshark"):
                self.incub.append(mv)
        for _ in self.namors():
            for _ in range(pips):
                self.token("Merfolk", 1, 1)
        if self.clock != int(self.clock):           # opponent's turn
            for c in self.tag_on("brineborn"):
                c["ctr"] += 1

    def cast_namor(self, reserve=(0, 0)):
        if not self.namor_cz:
            return False
        g, u = self.cost_of(COMMANDER)
        if not self.can_pay(g, u, reserve):
            return False
        self.pay(g, u)
        self.namor_cz = False
        self.st["namor_cast"] += 1
        self.new_creature(COMMANDER, 0, 4, True, {"flying"}, namor=True)
        self.log(f"cast Namor (tax {self.tax})")
        return True

    def target_opp(self):
        a = self.alive()
        return min(a, key=lambda i: self.opp[i]) if a else 0

    def best_blocker(self, i, flying_only=False):
        bl = [b for b in self.board[i] if not b.get("frozen") and b.get("stun", -1) < self.turn
              and not b.get("tapped_turn") == self.turn]
        if flying_only:
            bl = [b for b in bl if b["fly"]] or bl
        return max(bl, key=lambda b: (b["fly"], b["p"] + b["t"])) if bl else None

    def bounce_blocker(self, i, recast=0.8):
        b = self.best_blocker(i, flying_only=True)
        if b:
            self.board[i].remove(b)
            if self.rng.random() < recast:
                self.bounced[i].append(b)
            return True
        return False

    def cast(self, name, reserve=(0, 0), free=False, phase="main"):
        d = C[name]
        g, u = self.cost_of(name)
        if d["type"] != "creature" and d["kind"] in ("dig", "cruise") and not free:
            dl = min(g, max(0, len(self.gy) - 2))
            g -= dl
            del self.gy[:dl]
        if not free:
            if not self.can_pay(g, u, reserve):
                return False
            self.pay(g, u)
        self.hand.remove(name)
        self.log(f"cast {name}")
        if d["type"] == "creature":
            c = self.new_creature(name, d["p"], d["t"], d["merfolk"], d["tags"])
            if "reejerey" not in d["tags"]:
                for _ in self.tag_on("reejerey"):
                    if phase == "main1":
                        b = self.best_blocker(self.target_opp())
                        if b:
                            b["tapped_turn"] = self.turn
            if "wayfinder" in d["tags"]:
                top = [self.lib.pop() for _ in range(min(3, len(self.lib)))]
                for x in top:
                    if x == "Island" or x == "Mystic Sanctuary":
                        self.hand.append(x)
                    else:
                        self.gy.append(x)
            if "stun" in d["tags"]:
                b = self.best_blocker(self.target_opp())
                if b:
                    b["stun"] = self.turn + 1
            if "harbinger" in d["tags"] and self.rng.random() < 0.5:
                self.bounce_blocker(self.target_opp(), recast=0.6 if phase == "endstep" else 0.8)
            if "namora" in d["tags"] and self.can_pay(2, 1):
                self.pay(2, 1)
                c["ctr"] += 1
                self.token("Merfolk", 1, 1); self.token("Merfolk", 1, 1)
                c["powered"] = True
            if "cantrip_etb" in d["tags"]:
                self.draw(1)
            return True
        self.namor_trigger(name)
        k = d["kind"]
        to_gy = d["type"] in ("instant", "sorcery")
        i = self.target_opp()
        if k == "rock" or k in ("cabinet", "idol", "boots", "horn", "swiftfoot", "gauntlet"):
            self.arts.append(dict(name=name, tapped="tapped" in d["tags"] or k in ("rock",) and False))
            if k == "cabinet":
                tg = sorted(self.merfolk(), key=lambda c: -self.power(c))[:4]
                for c in tg:
                    c["ctr"] += 1
            if "tapped" in d["tags"]:
                self.arts[-1]["tapped"] = True
            if k == "rock" and not self.arts[-1]["tapped"]:
                # fresh rock taps right away
                if "sol" in d["tags"]:
                    self.Cl += 2
                elif "cless" in d["tags"]:
                    self.Cl += 1
                else:
                    self.U += 1
                self.arts[-1]["tapped"] = True
            if k == "idol":
                self.idol_ready = True
            if k == "gauntlet":
                for b in self.board[i]:
                    b["tapped_turn"] = self.turn
                tg = max(self.cr, key=lambda c: (c.get("namor", False), self.power(c)), default=None)
                if tg:                       # stays on that creature; re-equipping ({2}) is not modeled
                    tg["ctr"] += 1
                    tg["tags"].add("hitloot")
        elif d["type"] == "enchantment":
            self.ench.append(name)
            if k == "superint":
                tg = max(self.cr, key=lambda c: (c.get("namor", False), self.tough(c)), default=None)
                if tg:
                    self.super_on = tg["id"]
                else:
                    self.ench.remove(name); self.gy.append(name)
            elif k == "freeze":
                b = self.best_blocker(i)
                if b:
                    b["frozen"] = True
            elif k == "shrink":
                b = self.best_blocker(i)
                if b:
                    b["p"] = 0
        elif k == "brainstorm":
            self.draw(3)
            for _ in range(2):
                w = min(self.hand, key=lambda c: self.prio(c) if c not in LANDS else (3 if len(self.lands) < 6 else -1))
                self.hand.remove(w)
                self.lib.append(w)
            if any(c in ("Fabled Passage", "Terramorphic Expanse", "Vibrant Cityscape") for c in self.hand) and len(self.lib) > 2:
                pass  # shuffle happens when the fetch is used
        elif k == "fof":
            top = [self.lib.pop() for _ in range(min(5, len(self.lib)))]
            take, rest = self.best_spells_from(top, 2)
            # opponent splits 2/3 vs 3/2: take the pile with the best two, average ~2.4 cards
            extra = 1 if self.rng.random() < 0.4 else 0
            take2 = take + rest[:extra]
            for c in take2:
                self.lib.append(c)
            self.draw(len(take2))
            self.gy += rest[extra:]
        elif k == "dig":
            self.look_take(7, 2)
        elif k == "cruise":
            self.draw(3)
        elif k == "inquiry":
            self.draw(3)
            if sum(self.power(c) for c in self.cr if not c["tapped"]) < 2:
                self.discard_worst(1)
        elif k == "thirst":
            self.draw(3)
            art = [c for c in self.hand if C.get(c, {}).get("type") == "artifact" and (self.prio(c) <= 5 or self.turn > 5)]
            if art:
                pick = min(art, key=self.prio)
                self.hand.remove(pick); self.gy.append(pick)
            else:
                self.discard_worst(1); self.discard_worst(1)
        elif k == "stockup":
            self.look_take(5, 2)
        elif k == "draw1":
            self.draw(1)
        elif k == "unstable":
            self.draw(1)
            m = self.connive_target()
            if m:
                self.connive(m)
        elif k == "pym":
            att = [c for c in self.attackers_ready() if not self.evasive(c, i)]
            if att:
                max(att, key=self.power)["ub"] = True
            self.draw(1)
        elif k == "crescendo":
            self.draw(len(self.merfolk()))
        elif k == "melody":
            self.draw(len(self.merfolk()))
        elif k in ("whoosh", "peel", "bounce", "crashing", "bounce_draw"):
            recast = 0.6 if phase == "endstep" else 0.8
            self.bounce_blocker(i, recast)
            if k in ("whoosh", "crashing", "bounce_draw"):
                self.draw(1)
            if k in ("peel", "bounce"):
                toks = [c for c in self.cr if c["token"]]
                if toks:
                    self.cr.remove(toks[0])
        elif k == "kill":
            b = self.best_blocker(i, flying_only=True)
            if b:
                self.board[i].remove(b)
                self.board[i].append(dict(p=3, t=3, fly=False))
        elif k == "leviathan":
            self.token("Leviathan", 6, 5, merfolk=False, tags=("hexproof",))
        elif k == "newhero":
            X = self.total()  # all remaining after paying base
            X = min(X, 6)
            self.pay(X, 0)
            self.draw(X)
            cands = [c for c in self.cr if not c["token"] and not c.get("namor")
                     and C.get(c["name"], {}).get("type") == "creature"
                     and C[c["name"]]["cost"] + C[c["name"]]["u"] <= X and c["name"] not in
                     ("Attuma, Atlantean Warlord", "Svyelun of Sea and Sky", "Namor, Scourge of the Seas",
                      "Namora, the Sea Queen", "Kopala, Warden of Waves")]
            if cands:
                b = max(cands, key=lambda c: self.prio(c["name"]))
                t = self.token(b["name"], b["bp"], b["bt"], b["merfolk"], b["tags"])
                t["copyof"] = b["name"]
        elif k == "incursion":
            for c in [c for c in self.cr if not c["token"]]:
                t = self.token(c["name"], c["bp"], c["bt"], c["merfolk"], c["tags"])
                t["copyof"] = c["name"]
                if c.get("namor"):
                    t["namor"] = True
        elif k == "manifest":
            if self.lib:
                self.lib.pop()
            self.token("Manifest", 2, 2, merfolk=False)
        elif k == "extract":
            if self.lib:
                top = self.lib.pop()
                if top in LANDS:
                    self.hand.append(top)
                else:
                    self.hand.append(top)
                    self.cast(top, free=True)
            for _ in range(len(self.alive())):
                r = self.rng.random()
                if r < 0.4:
                    self.token("Stolen", 3, 3, merfolk=False)
                elif r < 0.7:
                    self.bounce_blocker(i, recast=0.0)
        elif k == "counter":
            if "charm" in d["tags"]:
                self.draw(2)          # cast as Archmage's Charm draw mode
            if "fracture" in d["tags"]:
                self.draw(1)
        elif k == "hightide":
            self.U += sum(1 for l in self.lands if l.get("island"))
            self.draw(0)
        if to_gy:
            self.gy.append(name)
        return True

    def connive_target(self):
        ms = self.merfolk()
        if not ms:
            return None
        return max(ms, key=lambda c: (not self.flying(c), self.power(c)))

    def attackers_ready(self):
        return [c for c in self.cr if c["entered"] < self.turn and not c["tapped"]
                and "noattack" not in c["tags"] and self.power(c) > 0]

    # ---------------- main phases ----------------
    def counters_in_hand(self):
        return [c for c in self.hand if C.get(c, {}).get("kind") == "counter"]

    def reserve(self):
        cs = self.counters_in_hand()
        if not cs or self.turn < 3:
            return (0, 0)
        cheap = min(cs, key=lambda c: sum(self.cost_of(c)))
        g, u = self.cost_of(cheap)
        return (g, u)

    def main_phase(self, phase):
        progress = True
        while progress:
            progress = False
            if self.cast_namor():
                progress = True
                continue
            res = self.reserve()
            hand = sorted([c for c in self.hand if c not in LANDS and c != "BLANK"],
                          key=self.prio, reverse=True)
            for name in hand:
                d = C[name]
                k = d.get("kind")
                if d["type"] == "instant" and k not in ("hightide",) and not (k == "crashing"):
                    continue
                if d["type"] == "creature" and d.get("flash") and phase == "main1" and "harbinger" in d["tags"]:
                    continue
                if k == "hightide":
                    big = [c for c in self.hand if c not in LANDS and c != name and sum(self.cost_of(c)) > self.total()]
                    if not big or self.islands() < 4:
                        continue
                if k in ("freeze", "shrink", "pym", "kill", "whoosh", "bounce_draw", "crashing") and phase != "main1":
                    continue
                if k == "gauntlet" and (phase != "main1" or not self.attackers_ready()):
                    continue
                if k in ("freeze", "kill", "bounce_draw", "crashing") and not self.best_blocker(self.target_opp()):
                    continue
                if k == "pym" and not self.attackers_ready():
                    continue
                if k == "superint" and not self.cr:
                    continue
                if k == "newhero" and self.total() < sum(self.cost_of(name)) + 2:
                    continue
                keyish = d["type"] == "creature" and (d["tags"] & {"lord", "svyelun", "scourge", "dancer"}) or (k == "rock" and self.turn <= 4)
                r = (0, 0) if keyish else res
                if self.cast(name, reserve=r, phase=phase):
                    progress = True
                    break
        self.activations(phase)

    def activations(self, phase):
        if phase != "main2":
            return
        # Zephyr Boots / Swiftfoot equips
        for a in self.arts:
            if a["name"] == "Zephyr Boots" and self.boots_on is None:
                cands = [c for c in self.cr if not self.flying(c) and not c["token"]]
                if cands and self.can_pay(2, 0, self.reserve()):
                    self.pay(2, 0)
                    self.boots_on = max(cands, key=self.power)["id"]
            if a["name"] == "Swiftfoot Boots" and self.swift_on is None:
                n = self.namors()
                if n and self.can_pay(1, 0):
                    self.pay(1, 0)
                    self.swift_on = n[0]["id"]
        # Mind Stone crack late
        for a in list(self.arts):
            if a["name"] == "Mind Stone" and len(self.lands) >= 7 and self.can_pay(1, 0, self.reserve()):
                self.pay(1, 0); self.arts.remove(a); self.gy.append(a["name"]); self.draw(1)
        # Baxter Building draw
        for l in self.lands:
            if l["name"] == "Baxter Building" and not l["tapped"] and any(self.tough(c) >= 4 for c in self.cr):
                # Baxter's own C is in the pool; using it costs that mana plus 4 more
                if self.total() - 1 >= 4 + sum(self.reserve()):
                    self.Cl -= 1
                    self.pay(4, 0)
                    l["tapped"] = True
                    self.draw(1)
        # Looter: loot if it didn't attack
        for c in self.tag_on("looter"):
            if not c["tapped"] and c["entered"] < self.turn:
                c["tapped"] = True
                self.draw(1); self.discard_worst(1)
        self.hatch(self.reserve())
        # Idol
        self.use_idol()

    def hatch(self, reserve=(0, 0)):
        """Pay {2} to turn Incubator tokens into X/X Phyrexians, biggest first."""
        for x in sorted(self.incub, reverse=True):
            if not self.can_pay(2, 0, reserve):
                break
            self.pay(2, 0)
            self.incub.remove(x)
            self.token("Phyrexian", x, x, merfolk=False)

    def use_idol(self):
        if self.token_made and self.idol_ready and any(a["name"] == "Idol of Oblivion" for a in self.arts):
            self.idol_ready = False
            self.draw(1)

    # ---------------- combat ----------------
    def combat(self):
        self.tide_on = None
        i0 = self.target_opp()
        # beginning of combat: Scourge connive
        for s in self.tag_on("scourge"):
            tg = self.connive_target()
            if tg:
                self.connive(tg)
        att = self.attackers_ready()
        if not att or not self.alive():
            return
        # Tideshaper makes the target's land an Island
        ts = [c for c in self.tag_on("tideshaper") if c in att]
        if ts and not self.blue[i0] and any("walk" in o["tags"] for o in self.cr):
            ts[0]["tapped"] = True
            att.remove(ts[0])
            self.tide_on = i0
        # Sovereign / Daughter make the best blockable attacker unblockable
        for c in list(self.tag_on("sovereign")) + list(self.tag_on("daughter")):
            if c not in att:
                continue
            blockable = [x for x in att if x is not c and x["merfolk"] and not self.evasive(x, i0)]
            if not blockable:
                continue
            if "daughter" in c["tags"]:
                if not self.can_pay(0, 1):
                    continue
                self.pay(0, 1)
            best = max(blockable, key=self.power)
            if self.power(best) <= self.power(c) and "daughter" not in c["tags"]:
                continue
            best["ub"] = True
            c["tapped"] = True
            att.remove(c)
        # Looter stays home to loot
        att = [c for c in att if "looter" not in c["tags"]]
        # assign attackers to opponents: focus the lowest life total, spill over once
        # the predicted (post-block) damage is lethal, then keep valuable creatures home
        # when they would just die in a block.
        order = sorted(self.alive(), key=lambda i: self.opp[i])
        assign = {i: [] for i in order}
        remaining = sorted(att, key=self.power, reverse=True)
        for idx, i in enumerate(order):
            for c in list(remaining):
                if idx < len(order) - 1 and self.predict(i, assign[i])[0] >= self.opp[i]:
                    break
                assign[i].append(c)
                remaining.remove(c)
        for i, group in assign.items():
            for _ in range(6):
                dmg, blocked, losses = self.predict(i, group)
                keep_home = [c for c in losses if not c["token"]]
                if not keep_home:
                    break
                c = min(keep_home, key=lambda x: (bool(x["tags"] & KEY) or x.get("namor", False), -self.power(x)))
                trial = [x for x in group if x is not c]
                if self.predict(i, trial)[0] >= dmg - 1:
                    group.remove(c)
                else:
                    break
        merfolk_attacked = False
        for i, group in assign.items():
            if not group:
                continue
            for c in group:
                if "vigilance" not in c["tags"]:
                    c["tapped"] = True
                if c["merfolk"]:
                    merfolk_attacked = True
                if "attack_connive" in c["tags"]:
                    self.connive(c)
                if "svyelun" in c["tags"]:
                    self.draw(1)
                if c["merfolk"] and "Kindred Discovery" in self.ench:
                    self.draw(1)
            self.resolve(i, group)
        if merfolk_attacked:
            for _ in self.tag_on("attuma"):
                self.draw(1)
        for c in self.cr:
            c["ub"] = False

    def blocks(self, i, group):
        blockers = [b for b in self.board[i] if not b.get("frozen") and b.get("stun", -1) < self.turn
                    and b.get("tapped_turn") != self.turn]
        blockers.sort(key=lambda b: -b["p"] - b["t"])
        blocked = {}
        free = sorted(group, key=self.power, reverse=True)
        for b in blockers:
            elig = [c for c in free if c["id"] not in blocked and
                    (self.evasive(c, i) is None or (self.evasive(c, i) == "fly" and b["fly"]))]
            if elig:
                blocked[elig[0]["id"]] = b
        return blocked

    def predict(self, i, group):
        blocked = self.blocks(i, group)
        dmg = sum(self.power(c) for c in group if c["id"] not in blocked)
        losses = [c for c in group if c["id"] in blocked and blocked[c["id"]]["p"] >= self.tough(c)
                  and not self.indestructible(c)]
        return dmg, blocked, losses

    def resolve(self, i, group):
        if self.opp[i] <= 0:
            return
        blocked = self.blocks(i, group)
        dmg = 0
        hits = []
        dead_b = []
        for c in group:
            P = self.power(c)
            if c["id"] in blocked:
                b = blocked[c["id"]]
                if P >= b["t"]:
                    dead_b.append(b)
                if b["p"] >= self.tough(c) and not self.indestructible(c):
                    self.leave(c)
                continue
            dmg += P
            hits.append(c)
            if c.get("namor") and not c["token"]:
                self.cmd[i] += P
        for b in dead_b:
            if b in self.board[i]:
                self.board[i].remove(b)
        self.opp[i] -= dmg
        if hits and self.st["first_hit"] is None:
            self.st["first_hit"] = self.turn
        bident = sum(1 for e in self.ench if e == "Bident of Thassa")
        piracy = sum(1 for e in self.ench if C[e]["kind"] == "piracy")
        for c in hits:
            if c["merfolk"]:
                self.draw(bident)
            self.draw(piracy)
            if "hitdraw" in c["tags"]:
                self.draw(1)
            if "hitloot" in c["tags"]:
                self.draw(1); self.discard_worst(1)
            if self.boots_on == c["id"]:
                self.draw(1); self.discard_worst(1)
        if self.opp[i] <= 0 or self.cmd[i] >= 21:
            self.log(f"opponent {i} dies")
            self.board[i] = []
        self.check()

    # ---------------- opponents ----------------
    def try_counter(self, threat):
        cs = sorted(self.counters_in_hand(), key=lambda c: sum(self.cost_of(c)))
        for c in cs:
            g, u = self.cost_of(c)
            if self.can_pay(g, u):
                self.pay(g, u)
                self.hand.remove(c)
                self.gy.append(c)
                self.namor_trigger(c)
                if "fracture" in C[c]["tags"]:
                    self.draw(1)
                if "soft" in C[c]["tags"] and self.rng.random() < 0.5:
                    self.log(f"{c} paid through vs {threat}")
                    return False
                self.st["countered"] += 1
                self.log(f"{c} counters {threat}")
                return True
        return False

    def removal_target(self):
        if not self.cr:
            return None
        def val(c):
            v = self.power(c)
            if c.get("namor") and not c["token"]:
                v += 100
            if c["tags"] & KEY:
                v += 30
            return v
        return max(self.cr, key=val)

    def opponents(self):
        b2b = "Back to Basics" in self.ench
        mult = (1 - self.b2b_effect) if b2b else 1.0
        for i in range(3):
            self.clock = self.turn + 0.25 * (i + 1)
            self.draws_now = 0
            if i not in self.alive():
                continue
            for b in self.bounced[i]:
                self.board[i].append(b)
            self.bounced[i] = []
            if self.turn >= 2 and self.rng.random() < self.p["creature_rate"] * mult:
                pw = self.rng.choice([1, 1, 2, 2, 3, 3, 4, 5, 6])
                self.board[i].append(dict(p=pw, t=max(1, pw + self.rng.choice([-1, 0, 0, 1])),
                                          fly=self.rng.random() < 0.20))
            if self.turn < 3:
                continue
            r = self.rng.random()
            if r < self.p["wipe"] * mult and self.turn >= 4:
                important = len(self.cr) >= 3 or self.namors()
                if important and self.try_counter("wipe"):
                    continue
                self.st["wiped"] += 1
                self.log("board wipe")
                for c in list(self.cr):
                    if not self.indestructible(c):
                        self.leave(c)
            elif r < (self.p["wipe"] + self.p["removal"]) * mult:
                c = self.removal_target()
                if c is None:
                    continue
                if "hexproof" in c["tags"] or self.swift_on == c["id"]:
                    continue
                kind = self.rng.choices(["destroy", "exile", "edict"], [0.55, 0.35, 0.10])[0]
                if kind == "edict":
                    worst = min(self.cr, key=self.power)
                    self.leave(worst)
                    continue
                if c["merfolk"] and self.tag_on("kopala") and self.rng.random() < 0.4:
                    continue
                if c["merfolk"] and any(o is not c for o in self.tag_on("svyelun")) and self.rng.random() < 0.25:
                    continue
                if (c.get("namor") or c["tags"] & KEY) and self.try_counter("removal on " + c["name"]):
                    continue
                if kind == "destroy" and self.indestructible(c):
                    continue
                if c.get("namor") and not c["token"]:
                    self.st["namor_removed"] += 1
                self.log(f"removal hits {c['name']}")
                self.leave(c, kind)
            elif r < (self.p["wipe"] + self.p["removal"] + self.p["art"]) * mult:
                arts = [a for a in self.arts] + [dict(name=e) for e in self.ench if e == "Bident of Thassa"]
                if arts:
                    best = max(arts, key=lambda a: self.prio(a["name"]))
                    if best in self.arts:
                        self.arts.remove(best)
                    else:
                        self.ench.remove(best["name"])
                    self.gy.append(best["name"])
        if self.alive():
            self.end_step()

    def end_step(self):
        """End of the last opponent's turn: spend held mana at instant speed."""
        progress = True
        while progress:
            progress = False
            inst = sorted([c for c in self.hand if C.get(c) and (C[c]["type"] == "instant"
                           or C[c].get("flash") or C[c]["kind"] == "crashing")], key=self.prio, reverse=True)
            for name in inst:
                d = C[name]
                k = d["kind"]
                if k in ("hightide", "aetherize"):
                    continue
                if k == "counter" and "charm" not in d["tags"]:
                    continue
                if k == "crescendo":
                    g, u = self.cost_of(name)
                    untapped = [c for c in self.cr if not c["tapped"]]
                    conv = min(len(untapped), g + u)
                    gg = max(0, g - conv)
                    uu = max(0, u - max(0, conv - g))
                    if self.can_pay(gg, uu):
                        self.pay(gg, uu)
                        self.U += 0
                        if self.cast(name, free=True, phase="endstep"):
                            progress = True
                            break
                    continue
                if k in ("whoosh",):
                    g, u = self.cost_of(name)
                    if self.can_pay(g + 1, u + 1):
                        self.pay(1, 1)
                if self.cast(name, phase="endstep"):
                    progress = True
                    break
        self.hatch()
        self.use_idol()

    # ---------------- turn ----------------
    def my_turn(self):
        self.turn += 1
        self.clock = float(self.turn)
        self.draws_now = 0
        self.token_made = False
        self.idol_ready = True
        for l in self.lands:
            l["tapped"] = False
        for a in self.arts:
            a["tapped"] = False
        for c in self.cr:
            c["tapped"] = False
        if self.super_on is not None:
            self.draw(1)
        for a in self.arts:
            if a["name"] == "Herald's Horn" and self.lib:
                top = self.lib[-1]
                if C.get(top, {}).get("type") == "creature" and C[top]["merfolk"]:
                    self.draw(1)
        if not (self.turn == 1 and self.on_play):
            self.draw(1)
        self.play_land()
        self.build_pool()
        self.main_phase("main1")
        self.combat()
        self.main_phase("main2")
        n = self.namors()
        if n:
            self.st["max_namor"] = max(self.st["max_namor"], self.power(n[0]))
        while len(self.hand) > 7:
            self.discard_worst(1)

    def run(self, max_turns=16):
        try:
            for _ in range(max_turns):
                self.my_turn()
                self.opponents()
        except Won:
            self.st["win"] = self.turn
        return self.st
