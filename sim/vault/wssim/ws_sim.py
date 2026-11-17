"""Monte Carlo simulator for Winter Soldier, Icy Assassin voltron (v2).

Win = all three opponents dead (21 commander damage, life, or Vorpal Sword).
Opponents build colored boards of blockers, double-block when it matters, and fire
colored targeted removal, edicts, wipes and artifact removal at profile rates.
Combat models menace, protection from colors, trample, deathtouch, first strike,
double strike, indestructible, unblockable and Wrecking Ball Arm evasion.
"""
import random
EQUIP_FIRST = True
SMART = True
from ws_cards import LANDS, EQUIP, AURAS, OTHER, COMMANDER

WB = {"W", "B"}
COLORS = ["W", "U", "B", "R", "G"]


class Won(Exception):
    pass


PROFILES = {
    "bracket2": dict(removal=0.05, wipe=0.02, art=0.03, creature_rate=0.55),
    "bracket3": dict(removal=0.08, wipe=0.03, art=0.04, creature_rate=0.60),
    "bracket4": dict(removal=0.15, wipe=0.05, art=0.07, creature_rate=0.70),
}
REMOVAL_COLORS = (["W", "B", "U", "R", "G", "C"], [0.30, 0.28, 0.15, 0.14, 0.08, 0.05])


def info(c):
    if c in EQUIP:
        return "equip", EQUIP[c]
    if c in AURAS:
        return "aura", AURAS[c]
    if c in OTHER:
        return OTHER[c]["type"], OTHER[c]
    return "land", None


class Game:
    def __init__(self, deck, prof, rng, log=False):
        self.rng, self.p, self.logging, self.lines = rng, prof, log, []
        self.lib = list(deck)
        rng.shuffle(self.lib)
        self.hand, self.gy = [], []
        self.lands, self.perms = [], []
        self.entered = {}
        self.equips, self.auras = [], []
        self.ws, self.ws_tax, self.ws_sick, self.ws_final = "cz", 0, False, False
        self.final_used = False
        self.ws_counters = self.jitte = 0
        self.life = 40
        self.opp, self.cmd = [40, 40, 40], [0, 0, 0]
        self.board = [[], [], []]           # (power, toughness, color)
        self.treasures = 0
        self.turn = 0
        self.on_play = rng.random() < 0.25
        self.held, self.pool = [], []
        self.squire_used = self.sfm_used = False
        self.ring = 0
        self.st = dict(win=None, ws_casts=0, ws_removed=0, ws_saved=0, ws_died_combat=0, recursions=0,
                       blocked=0, connects=0, chumps=0, max_power=0, wiped=0, vorpal=0, mother_saves=0,
                       pro_saves=0, hexproof_saves=0, indestr_saves=0, first_hit=None)
        self.mulligan()

    # ---------- utils ----------
    def log(self, s):
        if self.logging:
            self.lines.append(f"T{self.turn}: {s}")

    def alive(self):
        return [i for i in range(3) if self.opp[i] > 0 and self.cmd[i] < 21]

    def check(self):
        if not self.alive():
            raise Won()

    def has(self, tag):
        return any(tag in OTHER.get(c, {}).get("tags", ()) for c in self.perms)

    def ready(self, tag):
        """A creature with this tag that's been under my control since my last turn began."""
        return any(tag in OTHER.get(c, {}).get("tags", ()) and self.entered.get(c, 99) < self.turn
                   for c in self.perms)

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

    # ---------- counts ----------
    def artifacts(self):
        n = len(self.equips) + sum(1 for l in self.lands if l.get("artifact"))
        n += sum(1 for c in self.perms if OTHER.get(c, {}).get("type") == "artifact" or OTHER.get(c, {}).get("artifact"))
        return n

    def enchantments(self):
        return len(self.auras) + sum(1 for c in self.perms if OTHER.get(c, {}).get("type") == "enchantment")

    def swamps(self):
        return sum(1 for l in self.lands if "Swamp" in l.get("types", ()))

    def attached(self):
        return [e for e in self.equips if e["on_ws"]]

    def kw(self):
        k = {"menace", "vigilance"}
        for e in self.attached():
            k |= EQUIP[e["name"]].get("kw", set())
        for a in self.auras:
            k |= AURAS[a].get("kw", set())
        if self.has("enforcer") or self.has("bastion"):
            k.add("indestr")
        return k

    def pro(self):
        s = set()
        for e in self.attached():
            s |= EQUIP[e["name"]].get("pro", set())
        return s

    def stats(self):
        att = self.attached()
        names = [e["name"] for e in att]
        p = t = 7 if "Wrecking Ball Arm" in names else 2
        p += 2 * len(att)
        for e in att:
            d = EQUIP[e["name"]]
            p += d.get("p", 0)
            t += d.get("t", 0)
            dyn = d.get("dyn")
            if dyn == "lands":
                p += len(self.lands); t += len(self.lands)
            elif dyn == "artifacts_p":
                p += self.artifacts()
            elif dyn == "swamps":
                p += self.swamps(); t += self.swamps()
            elif dyn == "art_ench":
                n = self.artifacts() + self.enchantments(); p += n; t += n
            elif dyn == "steel":
                p += 2 * len(self.equips); t += 2 * len(self.equips)
            elif dyn == "omnitool":
                p += self.artifacts(); t += self.artifacts()
        for a in self.auras:
            d = AURAS[a]
            p += d.get("p", 0); t += d.get("t", 0)
            if d.get("dyn") == "wgp":
                n = len(att) + len(self.auras); p += 2 * n; t += 2 * n
            elif d.get("dyn") == "glitters":
                n = self.artifacts() + self.enchantments(); p += n; t += n
        if self.has("bastion"):
            p += 2; t += 2
        p += self.ws_counters; t += self.ws_counters
        return p, max(t, 1)

    # ---------- lands & mana ----------
    def tapped_cond(self, name):
        cols, tapped, ex = LANDS[name]
        cond = ex.get("cond")
        types = set()
        for l in self.lands:
            types.update(l.get("types", ()))
        if cond == "reveal":
            return not any("types" in LANDS.get(c, (0, 0, {}))[2] for c in self.hand)
        if cond:
            return not (set(cond) & types)
        return tapped

    def play_land(self):
        hl = [c for c in self.hand if c in LANDS]
        if not hl:
            return
        pick = sorted(hl, key=lambda l: (self.tapped_cond(l), LANDS[l][2].get("saga", False), -len(LANDS[l][0])))[0]
        self.hand.remove(pick)
        cols, _, ex = LANDS[pick]
        tapped = self.tapped_cond(pick)
        if ex.get("shock"):
            self.life -= 2
        if ex.get("cityscape"):
            basic = "Swamp" if self.swamps() <= sum(1 for l in self.lands if "W" in l["colors"]) else "Plains"
            if basic in self.lib:
                self.lib.remove(basic)
                self.gy.append(pick)
                c2, _, e2 = LANDS[basic]
                self.lands.append({"name": basic, "colors": set(c2), "tapped": True, **e2})
                return
        entry = {"name": pick, "colors": set(cols), "tapped": tapped, **ex}
        if ex.get("saga"):
            entry["lore"] = 0
        self.lands.append(entry)

    def advance_sagas(self):
        for l in list(self.lands):
            if l.get("saga"):
                l["lore"] += 1
                if l["lore"] >= 3:
                    want = ["Colossus Hammer", "Shadowspear", "Commander's Plate", "Sol Ring", "Bonesplitter",
                            "Bloodforged Battle-Axe", "O-Naginata", "Sai of the Shinobi", "Skullclamp"]
                    for c in want:
                        if c in self.lib:
                            self.lib.remove(c)
                            self.enter_permanent(c)
                            break
                    self.lands.remove(l)
                    self.gy.append(l["name"])

    def build_pool(self):
        pool = []
        swamp = self.swamps() > 0
        others = sum(1 for l in self.lands if not l["tapped"] and not l.get("filter"))
        for l in self.lands:
            if l["tapped"]:
                continue
            cols = set(l["colors"])
            if l.get("tainted") and not swamp:
                cols = {"C"}
            if l.get("filter") and others == 0:
                continue
            src = {"cols": cols, "land": l["name"]}
            if l.get("villain"):
                src["villain"] = True
            pool.append(src)
            if l.get("tomb"):
                pool.append({"cols": {"C"}, "land": l["name"]})
        for c in self.perms:
            prod = OTHER.get(c, {}).get("prod")
            if prod == "CC":
                pool += [{"cols": {"C"}}, {"cols": {"C"}}]
            elif prod:
                pool.append({"cols": set(prod)})
        pool += [{"cols": set(WB), "treasure": True} for _ in range(self.treasures)]
        if self.has("ronin"):
            pool += [{"cols": set(WB), "equip_only": True}, {"cols": set(WB), "equip_only": True}]
        return pool

    def _alloc(self, cost, srcs, equip=False, villain=False):
        pips = ["W"] * cost.get("W", 0) + ["B"] * cost.get("B", 0)
        usable = [i for i, s in enumerate(srcs) if equip or not s.get("equip_only")]

        def cols(i):
            s = srcs[i]
            if s.get("villain") and villain:
                return WB
            return s["cols"]
        used = []

        def bt(k):
            if k == len(pips):
                return True
            cand = sorted((i for i in usable if i not in used and pips[k] in cols(i)),
                          key=lambda i: (not srcs[i].get("equip_only"), len(cols(i))))
            for i in cand[:4]:
                used.append(i)
                if bt(k + 1):
                    return True
                used.pop()
            return False
        if not bt(0):
            return None
        rest = sorted((i for i in usable if i not in used),
                      key=lambda i: (not srcs[i].get("equip_only"), srcs[i].get("treasure", False), len(cols(i))))
        g = cost.get("g", 0)
        if len(rest) < g:
            return None
        return used + rest[:g]

    def can_pay(self, cost, equip=False, villain=False, reserve=None):
        a = self._alloc(cost, self.pool, equip, villain)
        if a is None:
            return False
        if reserve:
            rest = [s for i, s in enumerate(self.pool) if i not in a]
            return self._alloc(reserve, rest) is not None
        return True

    def pay(self, cost, equip=False, villain=False):
        a = self._alloc(cost, self.pool, equip, villain)
        if a is None:
            return False
        for i in sorted(a, reverse=True):
            if self.pool[i].get("treasure"):
                self.treasures -= 1
            self.pool.pop(i)
        return True

    SAVES = ("Flawless Maneuver", "Take Up the Shield", "Akroma's Will", "Teferi's Protection", "Stolen Stark Tech",
             "Mithril Coat")

    def reserve(self):
        if self.ws != "bf" or len(self.attached()) < 2:
            return None
        for c in self.SAVES:
            if c in self.hand:
                if c == "Flawless Maneuver":
                    return None      # free with my commander out
                d = OTHER.get(c) or EQUIP.get(c)
                return d["cost"]
        return None

    # ---------- costs ----------
    def spell_cost(self, c):
        kind, d = info(c)
        cost = dict(d["cost"])
        if kind in ("equip", "aura"):
            red = (1 if self.has("danitha") else 0) + (1 if self.has("cid") and kind == "equip" else 0)
            cost["g"] = max(0, cost.get("g", 0) - red)
        if "free_cmdr" in d.get("tags", ()) and self.ws == "bf":
            cost = {"g": 0}
        return cost

    def equip_cost(self, name):
        d = EQUIP[name]
        cost = dict(d.get("equip_leg", d["equip"]))
        if name == "Plate Armor":
            cost["g"] = max(0, cost["g"] - (len(self.equips) - 1))
        if self.has("puresteel") and self.artifacts() >= 3:
            return {"g": 0}, d.get("life_equip", 0)
        if self.has("danitha"):
            cost["g"] = max(0, cost.get("g", 0) - 1)
        return cost, d.get("life_equip", 0)

    # ---------- equipping ----------
    def equip_value(self, name):
        d = EQUIP[name]
        v = 2 + d.get("p", 0)
        k = d.get("kw", set())
        if "trample" in k: v += 4
        if "double" in k: v += 10
        if "unblockable" in k: v += 10
        if "hexproof" in k or "shroud" in k: v += 6
        if "indestr" in k: v += 5
        v += 2 * len(d.get("pro", ()))
        dyn = d.get("dyn")
        v += {"lands": len(self.lands), "artifacts_p": self.artifacts(), "swamps": self.swamps(),
              "art_ench": self.artifacts() + self.enchantments(), "steel": 2 * len(self.equips),
              "omnitool": self.artifacts(), "wrecking": 6, "jitte": 3, "sofi": 3, "mask": 2, "shield": 3,
              "vorpal": 3, "sofaf": 3}.get(dyn, 0)
        if name == "Lightning Greaves":
            v -= 3
        if name == "Skullclamp":
            v -= 4
        return v

    def auto_attach(self, e):
        """Sigarda's Aid / Hammer of Nazahn / ETB-attach equipment."""
        if self.ws != "bf":
            return
        d = EQUIP[e["name"]]
        if d.get("etb_attach") or self.has("aid") or any(x["name"] == "Hammer of Nazahn" for x in self.equips):
            if not (d.get("need_power") and self.stats()[0] < 3):
                e["on_ws"] = True
                self.log(f"  {e['name']} attaches on entry")

    def try_equips(self, floor=-99):
        if self.ws != "bf":
            return
        for _ in range(25):
            loose = [e for e in self.equips if not e["on_ws"]]
            if not loose:
                return
            p, _ = self.stats()
            loose = [e for e in loose if not (EQUIP[e["name"]].get("need_power") and p < 3) and self.equip_value(e["name"]) >= floor]
            if not loose:
                return
            loose.sort(key=lambda e: -self.equip_value(e["name"]))
            if self.has("automaton"):
                for e in loose:
                    e["on_ws"] = True
                return
            if self.has("squire") and not self.squire_used:
                self.squire_used = True
                loose[0]["on_ws"] = True
                continue
            res = self.reserve()
            done = False
            for e in loose:
                cost, life = self.equip_cost(e["name"])
                if life and self.life - life < 12:
                    continue
                if self.can_pay(cost, equip=True, reserve=res):
                    self.pay(cost, equip=True)
                    self.life -= life
                    e["on_ws"] = True
                    self.log(f"  equip {e['name']}")
                    done = True
                    break
            if not done:
                return

    # ---------- casting ----------
    def prio(self, c):
        if c in LANDS:
            return -5
        kind, d = info(c)
        tags = d.get("tags", set()) if kind not in ("equip", "aura") else set()
        if tags & {"rock", "burst3", "petal"}:
            return 95 if self.turn <= 5 else 20
        if tags & {"puresteel", "danitha", "cid", "squire", "ronin", "sfm", "aid", "automaton"}:
            return 85
        if tags & {"tutor_equip", "tutor_any"}:
            return 80
        if tags & {"tithe", "ring", "necro", "sentinel", "landtax"}:
            return 75
        if tags & {"enforcer", "bastion", "sram", "swordsman", "squall", "peggy", "mother", "stonehewer"}:
            return 70
        if tags & {"skyhunter", "cloak", "bodyguard", "shredder"}:
            return 55
        if tags & {"draw2"}:
            return 40
        if kind == "equip":
            return 50 + self.equip_value(c)
        if kind == "aura":
            return 60 if self.ws == "bf" else -1
        if kind in ("instant",) or tags & {"wipe", "wipe_overload", "spot", "tutor_top"}:
            return -1
        return 10

    def enter_permanent(self, c):
        kind, d = info(c)
        if kind == "equip":
            e = {"name": c, "on_ws": False}
            self.equips.append(e)
            if self.has("puresteel"):
                self.draw(1)
            if c == "Swordsman's Steel":
                self.draw(len(self.equips))
            self.auto_attach(e)
            if c == "Hammer of Nazahn":
                for x in self.equips:
                    if not x["on_ws"] and self.ws == "bf":
                        pass
            return
        self.perms.append(c)
        self.entered[c] = self.turn

    def cast(self, c):
        kind, d = info(c)
        self.hand.remove(c)
        self.log(f"cast {c}")
        if kind in ("equip", "aura") and self.has("sram"):
            self.draw(1)
        if kind == "equip":
            self.enter_permanent(c)
            return
        if kind == "aura":
            self.auras.append(c)
            return
        tags = d.get("tags", set())
        if kind in ("sorcery", "instant"):
            self.gy.append(c)
            if "draw2" in tags:
                self.draw(2)
            elif "tutor_equip" in tags or "tutor_any" in tags:
                self.tutor("tutor_any" in tags, to_top=False)
            elif "tutor_top" in tags:
                self.tutor(True, to_top=True)
            return
        self.enter_permanent(c)
        if "burst3" in tags:
            self.pool += [{"cols": {"C"}}] * 3
        if "petal" in tags:
            self.pool.append({"cols": set(WB)})
            self.perms.remove(c); self.gy.append(c)
        if "chrome" in tags:
            junk = sorted([x for x in self.hand if x not in LANDS], key=self.prio)
            if junk:
                self.hand.remove(junk[0])
        if "diamond" in tags:
            lands = [x for x in self.hand if x in LANDS]
            if lands:
                self.hand.remove(lands[0]); self.gy.append(lands[0])
        if d.get("prod"):
            prod = d["prod"]
            self.pool += [{"cols": {"C"}}, {"cols": {"C"}}] if prod == "CC" else [{"cols": set(prod)}]
        if "cloak" in tags:
            self.remove_blocker()
        if "sfm" in tags:
            self.tutor(False, to_top=False, prefer=["Batterskull", "Kaldra Compleat", "Colossus Hammer",
                                                   "Sword of Fire and Ice", "Sword of Feast and Famine"])
        if "automaton" in tags and self.ws == "bf":
            for e in self.equips:
                e["on_ws"] = True

    TUTOR_EQUIP = ["Colossus Hammer", "Sword of Fire and Ice", "Commander's Plate", "Umezawa's Jitte", "My Precious",
                   "Sword of Feast and Famine", "O-Naginata", "Shadowspear", "Champion's Helm", "Loxodon Warhammer",
                   "Genji Glove", "Kaldra Compleat", "Batterskull", "Nightmare Lash"]
    TUTOR_ANY = ["Puresteel Paladin", "Sigarda's Aid", "Super-Soldier Serum", "Bastion Protector", "General's Enforcer"]

    def tutor(self, any_card, to_top, prefer=None):
        have = set(self.hand) | {e["name"] for e in self.equips} | set(self.perms) | set(self.auras)
        order = list(prefer or []) + (self.TUTOR_ANY if any_card else []) + self.TUTOR_EQUIP
        if not (self.has("puresteel") or self.has("squire") or self.has("aid")):
            order = [c for c in order if c != "Colossus Hammer"] + ["Colossus Hammer"]
        for c in order:
            if c in self.lib and c not in have:
                self.lib.remove(c)
                self.rng.shuffle(self.lib)
                if to_top:
                    self.lib.append(c)
                else:
                    self.hand.append(c)
                return

    def cast_ws(self):
        if self.ws != "cz":
            return False
        cost = {"W": 1, "B": 1, "g": self.ws_tax}
        if self.can_pay(cost, villain=True):
            self.pay(cost, villain=True)
            self.ws_tax += 2
            self.ws, self.ws_final, self.ws_counters, self.jitte = "bf", False, 0, 0
            self.ws_sick = not any("haste" in EQUIP[e["name"]].get("kw", ()) for e in self.equips)
            self.st["ws_casts"] += 1
            self.log("cast Winter Soldier")
            if self.has("swordsman") and self.equips:
                max(self.equips, key=lambda e: self.equip_value(e["name"]))["on_ws"] = True
            return True
        return False

    def activations(self):
        """Stoneforge / Stonehewer once per turn."""
        if self.ready("sfm") and not self.sfm_used:
            big = [c for c in self.hand if c in EQUIP and EQUIP[c]["cost"].get("g", 0) >= 4]
            if big and self.can_pay({"g": 1, "W": 1}, reserve=self.reserve()):
                self.pay({"g": 1, "W": 1})
                self.sfm_used = True
                c = max(big, key=self.equip_value)
                self.hand.remove(c)
                self.enter_permanent(c)
        if self.ready("stonehewer") and self.ws == "bf" and self.can_pay({"g": 1, "W": 1}, reserve=self.reserve()):
            have = {e["name"] for e in self.equips} | set(self.hand)
            for c in self.TUTOR_EQUIP:
                if c in self.lib and c not in have:
                    self.pay({"g": 1, "W": 1})
                    self.lib.remove(c)
                    self.enter_permanent(c)
                    self.equips[-1]["on_ws"] = True
                    break

    def main_phase(self):
        for _ in range(40):
            if self.cast_ws():
                continue
            if self.ws == "gy" and not self.final_used and self.can_pay({"g": 3, "W": 1, "B": 1}):
                self.pay({"g": 3, "W": 1, "B": 1})
                self.recur()
                self.ws_sick = True
                continue
            self.activations()
            if self.ws == "bf" and EQUIP_FIRST:
                # don't spend mana on a weak loose Equipment while a better one sits in hand uncast
                hand_eq = [c for c in self.hand if c in EQUIP and self.can_pay(self.spell_cost(c), equip=True)]
                floor = max((self.equip_value(c) for c in hand_eq), default=-99) if SMART else -99
                self.try_equips(floor)
            res = self.reserve()
            cands = sorted({c for c in self.hand if c not in LANDS and self.prio(c) >= 0}, key=lambda c: -self.prio(c))
            done = False
            for c in cands:
                kind, d = info(c)
                cost = self.spell_cost(c)
                if self.can_pay(cost, equip=(kind == "equip"), villain=("swordsman" in d.get("tags", ())), reserve=res):
                    self.pay(cost, equip=(kind == "equip"))
                    self.cast(c)
                    done = True
                    break
            if not done:
                break
        # tutors to the top at end of turn effectively
        for c in [c for c in self.hand if "tutor_top" in OTHER.get(c, {}).get("tags", ())]:
            if self.can_pay(OTHER[c]["cost"], reserve=self.reserve()):
                self.pay(OTHER[c]["cost"])
                self.cast(c)
        if self.ws == "bf":
            self.try_equips()

    def recur(self):
        self.ws, self.ws_final, self.final_used = "bf", True, True
        self.ws_counters = self.jitte = 0
        self.st["recursions"] += 1
        loose = [e for e in self.equips if not e["on_ws"]]
        if loose:
            max(loose, key=lambda e: self.equip_value(e["name"]))["on_ws"] = True
        self.log("Winter Soldier returns from the graveyard")

    # ---------- my removal ----------
    def remove_blocker(self):
        al = [i for i in self.alive() if self.board[i]]
        if not al:
            return
        i = max(al, key=lambda k: len(self.board[k]))
        self.board[i].remove(max(self.board[i]))

    def precombat_removal(self, i, kw, pro):
        if "unblockable" in kw or len(self.blockers(i, pro)) != 2:
            return
        for c in [c for c in self.hand if "spot" in OTHER.get(c, {}).get("tags", ())]:
            cost = self.spell_cost(c)
            if self.can_pay(cost, reserve=self.reserve()):
                self.pay(cost)
                self.hand.remove(c)
                self.gy.append(c)
                b = max(self.blockers(i, pro))
                self.board[i].remove(b)
                self.log(f"  {c} removes a blocker")
                return

    def my_wipe(self):
        if sum(len(b) for b in self.board) < 6:
            return
        if self.ws == "bf" and "indestr" not in self.kw():
            return
        for c, cost in (("Damn", {"g": 2, "W": 2}), ("Farewell", {"g": 4, "W": 2}), ("Austere Command", {"g": 4, "W": 2})):
            if c in self.hand and self.can_pay(cost):
                self.pay(cost)
                self.hand.remove(c)
                self.gy.append(c)
                self.board = [[], [], []]
                for x in list(self.perms):
                    if OTHER.get(x, {}).get("type") == "creature":
                        self.perms.remove(x); self.gy.append(x)
                self.log(f"  {c} wipes the board")
                return

    # ---------- combat ----------
    def blockers(self, i, pro):
        names = [e["name"] for e in self.attached()]
        elig = [b for b in self.board[i] if b[2] not in pro]
        if "Wrecking Ball Arm" in names:
            elig = [b for b in elig if b[0] > 2]
        return elig

    def attack_once(self, extra=False):
        if self.ws != "bf" or (self.ws_sick and "haste" not in self.kw()) or not self.alive():
            return
        if "Super-Soldier Serum" in self.auras or self.has("automaton"):
            for e in self.equips:
                if not (EQUIP[e["name"]].get("need_power") and self.stats()[0] < 3):
                    e["on_ws"] = True
        names = [e["name"] for e in self.attached()]
        alone = self.has("squall") or self.has("peggy") or not self.ready("skyhunter")
        if not alone and not extra:
            top = self.lib[-6:]
            hits = [c for c in top if c in EQUIP]
            if hits:
                c = max(hits, key=self.equip_value)
                self.lib.remove(c)
                self.enter_permanent(c)
                self.equips[-1]["on_ws"] = True
            names = [e["name"] for e in self.attached()]
        if "Sword of the Animist" in names and not extra:
            for b in ("Swamp", "Plains"):
                if b in self.lib:
                    self.lib.remove(b)
                    c2, _, e2 = LANDS[b]
                    self.lands.append({"name": b, "colors": set(c2), "tapped": True, **e2})
                    break
        if "Adaptive Omnitool" in names and not extra:
            arts = [c for c in self.lib[-6:] if c in EQUIP or OTHER.get(c, {}).get("type") == "artifact"]
            if arts:
                self.lib.remove(arts[-1]); self.hand.append(arts[-1])
        if self.has("swordsman") and self.attached():
            self.draw(1)
            lands = [c for c in self.hand if c in LANDS]
            nl = sorted([c for c in self.hand if c not in LANDS], key=self.prio)
            if len(lands) > 1:
                self.hand.remove(lands[0]); self.gy.append(lands[0])
            elif nl:
                self.hand.remove(nl[0]); self.gy.append(nl[0]); self.ws_counters += 1
        kw, pro = self.kw(), self.pro()
        if alone and self.has("squall"):
            kw.add("double")
        if alone and self.has("peggy"):
            kw.add("indestr")
        P, T = self.stats()
        P += 2 * self.jitte
        self.st["max_power"] = max(self.st["max_power"], P)
        best = None
        for i in self.alive():
            dmg, dies, nb = self._combat(i, P, T, kw, pro, list(self.board[i]), False)
            need = min(21 - self.cmd[i], self.opp[i])
            score = (dmg >= need, dmg / max(need, 1), -nb)
            if best is None or score > best[0]:
                best = (score, i)
        i = best[1]
        self.precombat_removal(i, kw, pro)
        # Umezawa's Jitte: spend counters (-1/-1 each) to kill a blocker if that breaks the double block
        if self.jitte and "unblockable" not in kw:
            el = self.blockers(i, pro)
            if len(el) == 2:
                small = min(el, key=lambda x: x[1])
                if small[1] <= self.jitte:
                    self.jitte -= small[1]
                    self.board[i].remove(small)
                    P -= 2 * small[1]
                    self.log("  Jitte kills a blocker")
        if "unblockable" not in kw and len(self.blockers(i, pro)) >= 2:
            src = next((s for s in self.pool if s.get("land") == "Rogue's Passage"), None)
            if src:
                self.pool.remove(src)
                if self.can_pay({"g": 4}):
                    self.pay({"g": 4}); kw.add("unblockable")
                else:
                    self.pool.append(src)
        # Akroma's Will on offense: if it turns a blocked/short swing into a kill (or saves him)
        need = min(21 - self.cmd[i], self.opp[i])
        dmg, dies, _ = self._combat(i, P, T, kw, pro, list(self.board[i]), False)
        if "Akroma's Will" in self.hand and (dmg < need or dies) and self.can_pay(OTHER["Akroma's Will"]["cost"]):
            kw2 = kw | {"double", "indestr"}
            pro2 = pro | set(COLORS)
            d2, _, _ = self._combat(i, P, T, kw2, pro2, list(self.board[i]), False)
            if d2 >= need or (dies and d2 > dmg):
                self.pay(OTHER["Akroma's Will"]["cost"])
                self.hand.remove("Akroma's Will"); self.gy.append("Akroma's Will")
                kw, pro = kw2, pro2
                self.log("  Akroma's Will for the kill")
        vorpal = False
        if "Vorpal Sword" in names and self.can_pay({"g": 5, "B": 1}):
            d0, _, _ = self._combat(i, P, T, kw, pro, list(self.board[i]), False)
            if d0 > 0:
                self.pay({"g": 5, "B": 1}); vorpal = True
        dmg, dies, nb = self._combat(i, P, T, kw, pro, self.board[i], True)
        if dmg > 0:
            self.st["connects"] += 1
            if self.st["first_hit"] is None:
                self.st["first_hit"] = self.turn
            self.cmd[i] += dmg
            self.opp[i] -= dmg
            self.log(f"  hits opponent {i} for {dmg} (cmd {self.cmd[i]})")
            if vorpal:
                self.opp[i] = 0; self.st["vorpal"] += 1
            for _ in range(2 if "double" in kw else 1):
                self.on_hit(names, i)
            self.check()
        if dies:
            self.st["ws_died_combat"] += 1
            self.ws_leaves("destroy")
            return
        if "Genji Glove" in names and not extra:
            self.attack_once(extra=True)

    def _combat(self, i, P, T, kw, pro, board, commit):
        names = [e["name"] for e in self.attached()]
        elig = [] if "unblockable" in kw else [b for b in board if b[2] not in pro]
        if "Wrecking Ball Arm" in names:
            elig = [b for b in elig if b[0] > 2]
        if "Captain America's Shield" in names and elig:
            elig.remove(max(elig))
        need = min(21 - self.cmd[i], self.opp[i])
        strikes = 2 if "double" in kw else 1
        expected = P * strikes
        if not (len(elig) >= 2 and (expected >= 6 or expected >= need)):
            return expected, False, 0
        indestr = "indestr" in kw
        first = "first" in kw or "double" in kw
        top = sorted(elig, key=lambda b: -b[0])[:2]
        if not indestr and not first and sum(b[0] for b in top) >= T:
            pick = top
        else:
            pick = sorted(elig, key=lambda b: (b[1], b[0]))[:2]
        if commit:
            self.st["blocked"] += 1
        dt, tr = "deathtouch" in kw, "trample" in kw
        bl = [list(b) for b in pick]
        to_player, dies = 0, False

        def deal(power):
            nonlocal to_player
            rem = power
            for b in bl:
                if b[1] <= 0 or rem <= 0:
                    continue
                if dt:
                    b[1] = 0; rem -= 1
                else:
                    use = min(rem, b[1]); b[1] -= use; rem -= use
            if tr:
                to_player += rem
        if first:
            deal(P)
            surv = sum(b[0] for b in bl if b[1] > 0)
            if surv >= T and not indestr:
                dies = True
            if "double" in kw:
                if all(b[1] <= 0 for b in bl):
                    if tr:
                        to_player += P
                else:
                    deal(P)
        else:
            surv = sum(b[0] for b in bl)
            deal(P)
            if surv >= T and not indestr:
                dies = True
        if commit:
            for k, b in enumerate(bl):
                if b[1] <= 0 and tuple(pick[k]) in board:
                    board.remove(tuple(pick[k]))
                    self.st["chumps"] += 1
        return to_player, dies, len(pick)

    def on_hit(self, names, i):
        if "Sword of Fire and Ice" in names:
            al = self.alive()
            if al:
                j = min(al, key=lambda k: self.opp[k]); self.opp[j] -= 2
            self.draw(1)
        if "Sword of Feast and Famine" in names:
            for l in self.lands:
                l["tapped"] = False
            self.pool = self.build_pool()
        if "Mask of Memory" in names:
            self.draw(2)
            junk = sorted(self.hand, key=lambda c: (c not in LANDS, self.prio(c)))
            if junk:
                self.hand.remove(junk[0]); self.gy.append(junk[0])
        if "Umezawa's Jitte" in names:
            self.jitte += 2
        for _ in range(sum(1 for n in names if n == "Bloodforged Battle-Axe")):
            self.equips.append({"name": "Bloodforged Battle-Axe", "on_ws": False, "token": True})
        if self.has("squall"):
            back = [c for c in self.gy if c in EQUIP and EQUIP[c]["cost"].get("g", 0) <= 3]
            if back:
                self.gy.remove(back[0]); self.enter_permanent(back[0])

    def shredder_attack(self):
        """Shredder, Shadow Master: he attacks the healthiest opponent and a tapped, attacking token copy
        goes at each other one. Each is a plain 5/5, so anyone with a creature blocks: a wall (toughness 6+)
        stops it for free, a 5+ power creature trades (that kills the real Shredder, not a token), otherwise
        their smallest creature chump-blocks and dies. Unblocked: 5 damage, then that player loses half
        their remaining life, rounded up."""
        if not self.ready("shredder") or not self.alive():
            return
        real = max(self.alive(), key=lambda k: self.opp[k])
        for i in self.alive():
            b = self.board[i]
            if not b:
                self.opp[i] -= 5
                if self.opp[i] > 0:
                    self.opp[i] -= (self.opp[i] + 1) // 2
                self.log(f"  Shredder connects with opponent {i} (life {self.opp[i]})")
                continue
            if max(x[1] for x in b) > 5:
                continue
            big = [x for x in b if x[0] >= 5]
            blk = max(big, key=lambda x: x[0]) if big else min(b, key=lambda x: x[0])
            b.remove(blk)
            if big and i == real and "Shredder, Shadow Master" in self.perms:
                self.perms.remove("Shredder, Shadow Master"); self.gy.append("Shredder, Shadow Master")
        self.check()

    # ---------- commander leaving ----------
    def ws_leaves(self, how):
        for e in self.equips:
            e["on_ws"] = False
        self.gy += self.auras
        self.auras = []
        self.ws_counters = self.jitte = 0
        self.ws = "gy" if (how == "destroy" and not self.ws_final and not self.final_used) else "cz"
        self.log(f"  Winter Soldier leaves ({how}) -> {self.ws}")

    # ---------- opponents ----------
    def spend_held(self, a):
        for k in a:
            if self.held[k].get("treasure"):
                self.treasures -= 1
        self.held = [s for k, s in enumerate(self.held) if k not in a]

    def save(self, kind):
        if kind in ("destroy", "wipe"):
            opts = ["Flawless Maneuver", "Take Up the Shield", "Stolen Stark Tech", "Mithril Coat", "Akroma's Will",
                    "Teferi's Protection"]
        elif kind == "exile":
            opts = ["Akroma's Will", "Teferi's Protection"]
        else:
            opts = ["Teferi's Protection"]
        for c in opts:
            if c not in self.hand:
                continue
            d = OTHER.get(c) or EQUIP.get(c)
            cost = {"g": 0} if c == "Flawless Maneuver" else d["cost"]
            a = self._alloc(cost, self.held, equip=(c in EQUIP))
            if a is not None:
                self.spend_held(a)
                self.hand.remove(c)
                if c in EQUIP:
                    self.equips.append({"name": c, "on_ws": True})
                else:
                    self.gy.append(c)
                self.st["ws_saved"] += 1
                self.log(f"  {c} saves Winter Soldier from {kind}")
                return True
        return False

    def creatures_out(self):
        return [x for x in self.perms if OTHER.get(x, {}).get("type") == "creature"]

    def opponents(self):
        for i in range(3):
            if i not in self.alive():
                continue
            if self.turn >= 2 and self.rng.random() < self.p["creature_rate"]:
                pw = self.rng.choice([1, 1, 2, 2, 3, 3, 4, 5, 6])
                self.board[i].append((pw, max(1, pw + self.rng.choice([-1, 0, 0, 1])), self.rng.choice(COLORS)))
            if self.has("tithe") and self.rng.random() < 0.6:
                self.treasures += 1
            if self.turn < 3:
                continue
            r = self.rng.random()
            if r < self.p["wipe"] and self.turn >= 4:
                self.st["wiped"] += 1
                kind = "destroy" if self.rng.random() < 0.8 else "exile"
                if self.ws == "bf" and not (kind == "destroy" and "indestr" in self.kw()) and not self.save("wipe" if kind == "destroy" else "exile"):
                    self.st["ws_removed"] += 1
                    self.ws_leaves(kind)
                for x in self.creatures_out():
                    self.perms.remove(x); self.gy.append(x)
            elif r < self.p["wipe"] + self.p["removal"] and self.ws == "bf":
                self.targeted(i)
            elif r < self.p["wipe"] + self.p["removal"] + self.p["art"]:
                att = [e for e in self.equips if e["name"] not in ("Captain America's Shield", "Kaldra Compleat")]
                if att:
                    best = max(att, key=lambda e: self.equip_value(e["name"]))
                    self.equips.remove(best)
                    self.gy.append(best["name"])
        if self.ws == "gy" and not self.final_used:
            a = self._alloc({"g": 3, "W": 1, "B": 1}, self.held)
            if a is not None:
                self.spend_held(a)
                self.recur()
                self.ws_sick = False

    def targeted(self, i):
        kw, pro = self.kw(), self.pro()
        kind = self.rng.choices(["destroy", "exile", "edict"], [0.55, 0.35, 0.10])[0]
        color = self.rng.choices(*REMOVAL_COLORS)[0]
        if kind == "edict":
            if self.creatures_out():
                victim = self.creatures_out()[0]
                self.perms.remove(victim); self.gy.append(victim)
                return
        else:
            if "hexproof" in kw or "shroud" in kw:
                self.st["hexproof_saves"] += 1
                return
            if color in pro:
                self.st["pro_saves"] += 1
                return
            if "Plate Armor" in [e["name"] for e in self.attached()] and self.rng.random() < 0.4:
                return
            if self.ready("mother") and color != "C":
                self.st["mother_saves"] += 1
                return
            if self.has("bodyguard") and color != "C":
                for x in self.perms:
                    if "bodyguard" in OTHER.get(x, {}).get("tags", ()):
                        self.perms.remove(x); self.gy.append(x); break
                self.st["mother_saves"] += 1
                return
            if kind == "destroy" and "indestr" in kw:
                self.st["indestr_saves"] += 1
                return
        if self.save(kind):
            return
        self.st["ws_removed"] += 1
        self.ws_leaves(kind)

    # ---------- turn ----------
    def my_turn(self):
        self.turn += 1
        for l in self.lands:
            l["tapped"] = False
        if not (self.turn == 1 and self.on_play):
            self.draw(1)
        if self.has("ring"):
            self.ring += 1
            self.draw(self.ring)
        self.play_land()
        self.advance_sagas()
        self.squire_used = self.sfm_used = False
        self.pool = self.build_pool()
        self.main_phase()
        self.my_wipe()
        self.attack_once()
        self.shredder_attack()
        self.ws_sick = False
        self.main_phase()
        if self.has("necro") and self.life > 20:
            n = min(self.life - 20, 5)
            self.life -= n
            self.draw(n)
        self.held = list(self.pool)
        while len(self.hand) > 7:
            junk = sorted(self.hand, key=lambda c: (c not in LANDS, self.prio(c)))
            self.gy.append(junk[0]); self.hand.remove(junk[0])

    def run(self, max_turns=16):
        try:
            for _ in range(max_turns):
                self.my_turn()
                self.opponents()
        except Won:
            self.st["win"] = self.turn
        return self.st
