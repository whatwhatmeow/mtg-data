"""Monte Carlo simulator for Doctor Doom, Unrivaled (mono-black, win with an empty library).

Doom: {2}{B}{B}. {T}: draw a card, lose 1 life, then if your library is empty you win.
Win lines:
  * Demonic Consultation (name a card not in the deck) + Doom able to tap  -> instant-speed win
  * Leveler + Doom able to tap
  * Inverter of Truth with an empty graveyard (Bojuka Bog / Nihil Spellbomb / Tormod's Crypt) + Doom
  * Doomsday + two draw-2 spells (or Peer) + Doom
  * Draw-out: Doom activations (untappers, Bracers/Rings copies), self-mill (Mesmeric Orb, Altar,
    Millstone, Codex Shredder, Perpetual Timepiece, Stitcher's Supplier), Necropotence, Peer into the
    Abyss, Damnable Pact, Ad Nauseam, Bolas's Citadel.
Doom "able to tap" = under my control since my turn began, or haste (Greaves, Boots, Thousand-Year
Elixir, cast with Hall of the Bandit Lord mana).
Opponents: removal on Doom, wipes, disruption of combo attempts, and (cEDH) racing combos of their own.
"""
import random
from du_cards import LANDS, CARDS

DOOM = "Doctor Doom, Unrivaled"
FREE_INTERACT = {"Snuff Out", "Dismember", "Deadly Rollick", "Gut Shot", "Force of Despair", "Sheoldred's Edict", "Fatal Push"}


class Won(Exception):
    def __init__(self, how):
        self.how = how


class Lost(Exception):
    def __init__(self, how):
        self.how = how


PROFILES = {
    "goldfish": dict(removal=0.0, wipe=0.0, disrupt=0.0, race=0.0, race_from=99),
    "bracket3": dict(removal=0.07, wipe=0.03, disrupt=0.10, race=0.02, race_from=7),
    "bracket4": dict(removal=0.13, wipe=0.05, disrupt=0.30, race=0.03, race_from=6),
    "cedh": dict(removal=0.18, wipe=0.04, disrupt=0.50, race=0.10, race_from=3),
}


def tags(c):
    d = CARDS.get(c)
    return d["tags"] if d else set()


class Game:
    def __init__(self, deck, prof, rng, log=False, combo_from=1):
        self.rng, self.p, self.logging, self.lines = rng, prof, log, []
        self.combo_from = combo_from
        self.lib = list(deck)
        rng.shuffle(self.lib)
        self.hand, self.gy, self.exile = [], [], []
        self.lands = []
        self.perms = []
        self.entered = {}
        self.doom = "cz"
        self.doom_tax = 0
        self.doom_entered = None
        self.doom_haste = False
        self.life = 40
        self.turn = 0
        self.on_play = rng.random() < 0.25
        self.ring = 0
        self.discard_round = -1
        self.pool = []
        self.held = []
        self.st = dict(win=None, how=None, attempts=0, disrupted=0, doom_removed=0, doom_casts=0, raced=False)
        self.mulligan()

    def log(self, s):
        if self.logging:
            self.lines.append(f"T{self.turn}: {s}")

    def has(self, tag):
        return any(tag in tags(c) for c in self.perms)

    def count(self, tag):
        return sum(tag in tags(c) for c in self.perms)

    def mulligan(self):
        for a in range(4):
            if a:
                self.lib += self.hand
                self.hand = []
                self.rng.shuffle(self.lib)
            self.hand = [self.lib.pop() for _ in range(7)]
            nl = sum(c in LANDS for c in self.hand)
            fast = sum(1 for c in self.hand if tags(c) & {"rock", "burst3", "ritual", "petal"})
            plan = sum(1 for c in self.hand if tags(c) & {"consult", "win", "tutor", "tutor_top", "necro", "wishclaw"})
            if self.p.get("strict"):
                big = sum(2 if c in ("Sol Ring", "Ancient Tomb", "Jeweled Lotus") else (3 if tags(c) & {"burst3", "ritual"} else 0) for c in self.hand)
                speed = min(nl, 3) + fast + big // 2
                ok = 1 <= nl <= 4 and speed >= 4 and (plan or speed >= 5)
                if a >= 2:
                    ok = 1 <= nl <= 5 and nl + fast >= 3
            else:
                ok = 1 <= nl <= 5 and nl + fast >= 3 and (plan or nl + fast >= 4)
            if ok or a == 3:
                for _ in range(max(0, a - 1)):
                    lands = [c for c in self.hand if c in LANDS]
                    sp = [c for c in self.hand if c not in LANDS]
                    pick = lands[-1] if len(lands) > 3 or not sp else sp[-1]
                    self.hand.remove(pick)
                    self.lib.insert(0, pick)
                return

    def draw(self, n=1):
        for _ in range(n):
            if not self.lib:
                return
            self.hand.append(self.lib.pop())

    def mill(self, n):
        for _ in range(n):
            if self.lib:
                self.gy.append(self.lib.pop())

    # ---------------- mana ----------------
    def swamps(self):
        if any(l["name"] == "Urborg, Tomb of Yawgmoth" for l in self.lands):
            return len(self.lands)
        return sum(1 for l in self.lands if LANDS[l["name"]].get("swamp"))

    def build_pool(self):
        pool = []
        ghast = self.has("ghast")
        for l in self.lands:
            if l["tapped"]:
                continue
            d = LANDS[l["name"]]
            prod = d["prod"]
            if any(x["name"] == "Urborg, Tomb of Yawgmoth" for x in self.lands):
                prod = "B" if prod == "C" else prod
            if d.get("coffers"):
                n = max(0, self.swamps() - 2)
                pool += ["B"] * n if n else ["C"]
                continue
            if d.get("hall"):
                pool.append("H")
                continue
            pool += list(prod)
            if ghast and (d.get("swamp") or prod == "B"):
                pool.append("B")
        if "Mox Amber" in self.perms and self.doom == "bf":
            pool.append("B")
        for c in self.perms:
            d = CARDS[c]
            if d.get("prod") and self.entered.get(c, 99) <= self.turn and not (d.get("tapped") and self.entered.get(c) == self.turn):
                pool += list(d["prod"])
        return pool

    def _can(self, cost, pool):
        b = cost.get("B", 0)
        g = cost.get("g", 0)
        bs = pool.count("B")
        if bs < b:
            return False
        return len(pool) - b >= g

    def cost(self, c):
        d = CARDS[c]
        cost = dict(d["cost"])
        if self.has("medallion") and cost.get("B") and c != DOOM:
            cost["g"] = max(0, cost["g"] - self.count("medallion"))
        return cost

    def can_pay(self, cost, extra=0):
        return self._can({"g": cost.get("g", 0) + extra, "B": cost.get("B", 0)}, self.pool)

    def pay(self, cost, prefer_hall=False):
        b = cost.get("B", 0)
        g = cost.get("g", 0)
        used_hall = False
        for _ in range(b):
            self.pool.remove("B")
        for _ in range(g):
            for t in (("H", "C", "B") if prefer_hall else ("C", "H", "B")):
                if t in self.pool:
                    self.pool.remove(t)
                    if t == "H":
                        used_hall = True
                        self.life -= 3
                    break
        return used_hall

    def mana(self):
        return len(self.pool)

    # ---------------- Doom ----------------
    def doom_ready(self, instant=False):
        if self.doom != "bf":
            return False
        if self.doom_haste or any("haste" in tags(c) and ("drawbridge" not in tags(c) or self.entered.get(c, 99) < self.turn) for c in self.perms):
            return True
        return self.doom_entered is not None and self.doom_entered < self.turn

    def cast_doom(self):
        if self.doom != "cz":
            return False
        cost = {"g": 2 + self.doom_tax, "B": 2}
        if "Jeweled Lotus" in self.hand:
            cost = {"g": 1 + self.doom_tax, "B": 0}
            if self._can(cost, self.pool):
                self.hand.remove("Jeweled Lotus"); self.gy.append("Jeweled Lotus")
        if self._can(cost, self.pool):
            hall = "H" in self.pool
            self.pay(cost, prefer_hall=True)
            self.doom_haste = hall
            self.doom = "bf"
            self.doom_entered = self.turn
            self.doom_tax += 2
            self.st["doom_casts"] += 1
            self.log("cast Doom")
            return True
        return False

    # ---------------- disruption ----------------
    def disrupted(self):
        p = self.p["disrupt"]
        if self.has("grid"):
            p *= 0.6
        if self.discarded_this_turn:
            p *= 0.7
        if self.has("stax"):
            p *= 0.9
        return self.rng.random() < p

    def attempt(self, how):
        if self.turn < self.combo_from:
            return False
        self.st["attempts"] += 1
        prot = self.has("shroud") or self.has("hexproof")
        if self.disrupted() and not (prot and self.rng.random() < 0.4):
            self.st["disrupted"] += 1
            self.log(f"  {how} disrupted")
            # removal on Doom in response after the library is already gone = we deck ourselves
            if not prot and how.split()[0] in ("consultation", "leveler", "inverter") and self.rng.random() < 0.4:
                raise Lost("combo fizzled (Doom removed in response)")
            if how.startswith("doomsday") and not prot and self.rng.random() < 0.4:
                raise Lost("doomsday pile stranded")
            return False
        raise Won(how)

    # ---------------- win checks ----------------
    def gy_exiler_ready(self):
        return self.has("gyexile") or ("Bojuka Bog" in self.hand and not self.land_played)

    def try_wins(self):
        ready = self.doom_ready()
        if not ready:
            return
        if not self.lib:
            raise Won("library empty")
        # Demonic Consultation
        if "Demonic Consultation" in self.hand and self.can_pay(self.cost("Demonic Consultation")):
            self.pay(self.cost("Demonic Consultation"))
            self.hand.remove("Demonic Consultation")
            if self.attempt("consultation"):
                return
            self.gy.append("Demonic Consultation")
            return
        # Tainted Pact: works as a second Consultation when every card left in the library has a unique name
        if "Tainted Pact" in self.hand and self.can_pay(self.cost("Tainted Pact")) and len(set(self.lib)) == len(self.lib):
            self.pay(self.cost("Tainted Pact")); self.hand.remove("Tainted Pact")
            if not self.attempt("pact"):
                self.gy.append("Tainted Pact")
            return
        # Reanimation: Entomb / discard Leveler (or Inverter), then Reanimate / Animate Dead / Necromancy
        rean = sorted([c for c in self.hand if "reanimate" in tags(c)], key=lambda c: sum(self.cost(c).values()))
        if rean:
            r = rean[0]
            tgt = next((c for c in ("Leveler", "Inverter of Truth") if c in self.gy and (c == "Leveler" or len(self.gy) <= 4)), None)
            if not tgt and "Entomb" in self.hand and "Leveler" in self.lib and self.can_pay(self.cost(r), extra=1):
                self.pay(self.cost("Entomb")); self.hand.remove("Entomb"); self.gy.append("Entomb")
                self.lib.remove("Leveler"); self.gy.append("Leveler"); tgt = "Leveler"
                self.log("  Entomb -> Leveler")
            if tgt and self.can_pay(self.cost(r)):
                self.pay(self.cost(r)); self.hand.remove(r); self.gy.append(r); self.gy.remove(tgt)
                if r == "Reanimate":
                    self.life -= 5 if tgt == "Leveler" else 4
                if not self.attempt("reanimate " + tgt):
                    self.gy.append(tgt)
                return
        # Leveler
        led = 3 if "Lion's Eye Diamond" in self.hand else 0
        if "Leveler" in self.hand and self.can_pay(self.cost("Leveler"), extra=-led):
            self.pay(dict(self.cost("Leveler"), g=max(0, self.cost("Leveler")["g"] - led)))
            self.hand.remove("Leveler")
            if not self.attempt("leveler"):
                self.gy.append("Leveler")
            return
        # Inverter of Truth with an empty graveyard
        if "Inverter of Truth" in self.hand and self.can_pay(self.cost("Inverter of Truth")) and \
                (self.gy_exiler_ready() or len(self.gy) <= self.draw_capacity()):
            self.pay(self.cost("Inverter of Truth"))
            self.hand.remove("Inverter of Truth")
            if not self.attempt("inverter"):
                self.gy.append("Inverter of Truth")
            return
        # Doomsday + two draw spells
        if "Doomsday" in self.hand and self.can_pay(self.cost("Doomsday"), extra=3):
            # pile: Dark Ritual / Lotus Petal + Night's Whisper / Sign in Blood style draw spells, Doom tap last
            piled = [c for c in self.lib if tags(c) & {"draw2", "ritual", "petal"}]
            if len(piled) >= 3:
                self.pay(self.cost("Doomsday"))
                self.pay({"g": 3})
                self.hand.remove("Doomsday")
                if not self.attempt("doomsday"):
                    self.gy.append("Doomsday")
                return
        # Dig for a win piece with Ad Nauseam / Peer into the Abyss (keep 1-5 mana for the finisher)
        for dig, extra in (("Ad Nauseam", 1), ("Peer into the Abyss", 1)):
            if dig in self.hand and self.can_pay(self.cost(dig), extra=extra) and self.turn >= self.combo_from:
                self.pay(self.cost(dig)); self.hand.remove(dig); self.gy.append(dig)
                self.log(f"  dig with {dig}")
                if dig == "Peer into the Abyss":
                    n = (len(self.lib) + 1) // 2
                    self.draw(n); self.life -= self.life // 2
                else:
                    while self.lib and self.life > 6:
                        c = self.lib.pop(); self.hand.append(c)
                        d = CARDS.get(c)
                        self.life -= sum(d["cost"].values()) if d else 0
                        if c == "Demonic Consultation" or ("ritual" in tags(c) and self.life > 10):
                            if c == "Demonic Consultation":
                                break
                for r in [c for c in self.hand if tags(c) & {"petal", "ritual"}]:
                    if "petal" in tags(r):
                        self.hand.remove(r); self.gy.append(r); self.pool.append("B")
                    elif self.can_pay(self.cost(r)):
                        self.pay(self.cost(r)); self.hand.remove(r); self.gy.append(r)
                        self.pool += ["B"] * CARDS[r]["gain"]
                return self.try_wins()
        # Draw-out this turn?
        if self.draw_capacity(full=True) >= len(self.lib):
            if self.rng.random() < 0.5 * self.p["disrupt"] * (0.6 if self.has("grid") else 1):
                self.st["disrupted"] += 1
                return
            raise Won("draw-out")

    def untaps_affordable(self, mana):
        n = 0
        for c in self.perms:
            t = tags(c)
            if "untap1" in t and mana >= 1:
                n += 1; mana -= 1
            if "staff" in t and mana >= 2:
                n += 1; mana -= 2
        if self.has("mantle"):
            n += mana // 3
            mana -= 3 * (mana // 3)
        return n

    def draw_capacity(self, full=False):
        """How many cards I could remove from my library this turn (Doom taps + mills + big draws)."""
        if self.doom != "bf":
            return 0
        copies = 1 + self.count("copy") + self.count("rings")
        acts = (1 if self.doom_ready() else 0) + self.untaps_affordable(max(0, self.mana() - 1))
        cap = acts * copies
        if self.has("orb"):
            cap += acts                       # every untap mills one
        cap += 2 * self.count("millstone") + self.count("mill1") + 2 * self.count("mill2")
        if self.has("altar"):
            cap += 4 * (sum(1 for c in self.perms if CARDS[c]["type"] == "creature") + 1)
        if self.has("necro") and full:
            cap += max(0, self.life - 3)
        if full and "Peer into the Abyss" in self.hand and self.mana() >= 7:
            cap += (len(self.lib) + 1) // 2
        if full and "Damnable Pact" in self.hand:
            cap += max(0, min(self.mana() - 2, self.life - 3))
        if full and "Ad Nauseam" in self.hand and self.mana() >= 5:
            cap += max(0, self.life - 10) // 2
        return cap

    # ---------------- tutors ----------------
    def want(self):
        have = set(self.hand) | set(self.perms)
        wins = [c for c in ("Demonic Consultation", "Leveler", "Inverter of Truth", "Doomsday", "Tainted Pact") if c in have]
        if any("reanimate" in tags(c) for c in have) and ("Entomb" in have or "Leveler" in self.gy):
            wins.append("reanimation")
        order = []
        if not wins:
            order += ["Demonic Consultation", "Tainted Pact" if len(set(self.lib)) == len(self.lib) else "Leveler", "Leveler", "Doomsday", "Inverter of Truth"]
        if self.doom == "bf" and not self.doom_ready():
            order += ["Thousand-Year Elixir", "Lightning Greaves", "Swiftfoot Boots"]
        if self.doom == "cz" and self.mana() < 4 + self.doom_tax:
            order += ["Sol Ring", "Mana Vault", "Dark Ritual", "Grim Monolith"]
        if any("reanimate" in tags(c) for c in have) and "Leveler" not in self.gy and "Leveler" in self.lib and "Entomb" in self.lib:
            order.insert(0, "Entomb") if not wins else order.append("Entomb")
        if "Inverter of Truth" in have and not self.has("gyexile"):
            order += ["Tormod's Crypt", "Nihil Spellbomb"]
        order += ["Necropotence", "Demonic Consultation", "Leveler", "Doomsday", "Bolas's Citadel", "Mesmeric Orb",
                  "Peer into the Abyss", "Sol Ring", "Mana Vault"]
        for c in order:
            if c in self.lib and c not in have:
                return c
        return None

    def tutor(self, to_top=False):
        c = self.want()
        if not c:
            return
        self.lib.remove(c)
        self.rng.shuffle(self.lib)
        if to_top:
            self.lib.append(c)
        else:
            self.hand.append(c)
        self.log(f"  tutor -> {c}")

    # ---------------- casting ----------------
    def prio(self, c):
        if c in LANDS or c not in CARDS:
            return -5
        t = tags(c)
        if t & {"rock"}:
            return 95
        if "amber" in t and self.doom == "bf":
            return 95
        if t & {"tutor", "tutor_top", "wishclaw"}:
            if "sac" in t and not any(CARDS[x]["type"] == "creature" for x in self.perms):
                return -1
            return 85 if self.want() else -1
        if t & {"haste"} and self.doom != "cz":
            return 82
        if t & {"necro", "citadel", "bob", "arena", "ring", "orb", "copy", "rings", "untap1", "staff", "mantle",
                "grid", "stax", "medallion", "horn", "clamp", "altar", "millstone", "mill1", "mill2", "bmc",
                "ghast", "indestr", "haste", "supplier", "gyexile", "top", "ratking"}:
            return 70
        if t & {"draw2", "dispute"}:
            return 40
        if t & {"discard"}:
            return 60 if self.doom_ready() else 20
        if t & {"entomb", "reanimate", "amber", "burst3", "petal", "jlotus", "win", "consult", "ritual", "culling", "led", "pact", "peer", "dpact", "adnaus", "interact",
                "save", "rites", "doomsday"}:
            return -1
        return 15

    def cast(self, c):
        self.hand.remove(c)
        self.log(f"cast {c}")
        d = CARDS[c]
        t = d["tags"]
        if d["type"] in ("sorcery", "instant"):
            self.gy.append(c)
            if "draw2" in t:
                self.draw(2)
                self.life -= 2 if c == "Sign in Blood" else 0
            elif "tutor" in t:
                if c == "Grim Tutor":
                    self.life -= 3
                self.tutor()
            elif "tutor_top" in t:
                self.tutor(to_top=True)
                if c == "Vampiric Tutor":
                    self.life -= 2
            elif "discard" in t:
                self.discarded_this_turn = True
                self.discard_round = self.turn
            return
        self.perms.append(c)
        self.entered[c] = self.turn
        if "amber" in t and self.doom == "bf":
            self.pool.append("B")
        if d.get("prod") and not d.get("tapped"):
            self.pool += list(d["prod"])
        if "burst3" in t:
            self.pool += ["C", "C", "C"]
        if "petal" in t:
            self.pool.append("B")
            self.perms.remove(c); self.gy.append(c)
        if "chrome" in t:
            junk = sorted([x for x in self.hand if x not in LANDS], key=self.prio)
            if junk:
                self.hand.remove(junk[0]); self.exile.append(junk[0])
        if "diamond" in t:
            lands = [x for x in self.hand if x in LANDS]
            if lands:
                self.hand.remove(lands[0]); self.gy.append(lands[0])
        if "supplier" in t:
            self.mill(3)
        if "grief" in t:
            self.discarded_this_turn = True
        if "wishclaw" in t:
            self.tutor()
            self.perms.remove(c)

    def rituals(self):
        """Burst mana (rituals, Petal, Mana Vault, Grim Monolith) used only when it enables something now."""
        for c in [c for c in self.hand if tags(c) & {"ritual", "petal", "burst3"}]:
            t = tags(c)
            if self.can_pay(self.cost(c)):
                self.pay(self.cost(c))
                self.hand.remove(c)
                if "ritual" in t:
                    self.pool += ["B"] * CARDS[c]["gain"]; self.gy.append(c)
                elif "petal" in t:
                    self.pool.append("B"); self.gy.append(c)
                else:
                    self.pool += ["C", "C", "C"]; self.perms.append(c); self.entered[c] = self.turn
                self.log(f"burst {c}")
                return True
        return False

    def main_phase(self):
        for _ in range(40):
            self.try_wins()
            if self.cast_doom():
                continue
            cands = sorted({c for c in self.hand if self.prio(c) >= 0}, key=lambda c: -self.prio(c))
            done = False
            for c in cands:
                if self.can_pay(self.cost(c)):
                    self.pay(self.cost(c))
                    self.cast(c)
                    done = True
                    break
            if not done:
                break
        # burst mana to go for it
        if self.doom_ready() and any(x in self.hand for x in ("Leveler", "Inverter of Truth", "Doomsday", "Ad Nauseam", "Demonic Consultation")):
            snap = (list(self.pool), list(self.hand), list(self.gy), list(self.perms))
            for _ in range(4):
                if not self.rituals():
                    break
                self.try_wins()
        if self.doom == "cz" and any(tags(c) & {"ritual", "petal", "burst3"} for c in self.hand):
            for _ in range(4):
                if self.cast_doom():
                    self.main_phase(); return
                if not self.rituals():
                    break
        self.try_wins()

    def value_actions(self):
        """Fair turn: tap Doom once to draw, run mills, Necro at end step."""
        if self.doom_ready():
            self.draw(1 + self.count("copy") + self.count("rings"))
            self.life -= 1
            if self.has("orb"):
                self.mill(1)
        self.mill(2 * self.count("millstone") + self.count("mill1") + 2 * self.count("mill2"))
        nowin = not any(c in self.hand for c in ("Demonic Consultation", "Leveler", "Inverter of Truth"))
        if self.has("necro") and self.life > (10 if nowin else 15):
            n = min(self.life - 10, 12) if nowin else min(self.life - 15, 6)
            self.life -= n
            for _ in range(n):
                if self.lib:
                    self.exile.append(self.lib.pop())
            self.necro_pending = n
        if self.has("bmc") and self.life > 15:
            self.draw(1); self.life -= 2

    # ---------------- opponents ----------------
    def opponents(self):
        for i in range(3):
            if self.p["race"] and self.turn >= self.p["race_from"]:
                pr = self.p["race"] * (0.85 ** self.count("stax"))
                if self.discard_round == self.turn:
                    pr *= 0.75
                if self.rng.random() < pr:
                    ans = [c for c in self.hand if "interact" in tags(c)]
                    free = [c for c in ans if c in FREE_INTERACT]
                    use = free[0] if free else (ans[0] if ans and self.held else None)
                    if use and self.rng.random() < 0.5:
                        self.hand.remove(use); self.gy.append(use)
                        if use not in FREE_INTERACT:
                            self.held.pop()
                        self.st["stopped"] = self.st.get("stopped", 0) + 1
                        self.log(f"  stopped an opposing win with {use}")
                    else:
                        raise Lost("raced")
            if self.turn < 2:
                continue
            r = self.rng.random()
            if self.doom == "bf":
                if r < self.p["wipe"]:
                    if self.has("indestr"):
                        continue
                    self.remove_doom()
                elif r < self.p["wipe"] + self.p["removal"]:
                    if self.has("shroud") or self.has("hexproof"):
                        continue
                    if self.has("indestr") and self.rng.random() < 0.55:
                        continue
                    if any("save" in tags(c) for c in self.hand) and "B" in self.held:
                        c = next(c for c in self.hand if "save" in tags(c))
                        self.hand.remove(c); self.gy.append(c); self.held.remove("B")
                        continue
                    self.remove_doom()
            # instant-speed Consultation at the end of an opponent's turn
            if self.doom_ready() and "Demonic Consultation" in self.hand and "B" in self.held and self.turn >= self.combo_from:
                self.held.remove("B")
                self.hand.remove("Demonic Consultation")
                self.discarded_this_turn = False
                if not self.attempt("consultation (instant)"):
                    self.gy.append("Demonic Consultation")

    def remove_doom(self):
        self.doom = "cz"
        self.doom_entered = None
        self.doom_haste = False
        self.st["doom_removed"] += 1
        self.log("  Doom removed")

    # ---------------- turn ----------------
    def my_turn(self):
        self.turn += 1
        self.land_played = False
        self.discarded_this_turn = False
        if getattr(self, "necro_pending", 0):
            for _ in range(self.necro_pending):
                if self.exile:
                    self.hand.append(self.exile.pop())
            self.necro_pending = 0
        untapping = 0
        for l in self.lands:
            if l["tapped"]:
                untapping += 1
            l["tapped"] = False
        if self.has("orb"):
            self.mill(len(self.lands) // 2 + 1)
        if self.has("bob"):
            self.draw(1); self.life -= 1
        if self.has("arena"):
            self.draw(1); self.life -= 1
        if self.has("ring"):
            self.ring += 1
            self.draw(self.ring)
        if not (self.turn == 1 and self.on_play):
            self.draw(1)
        self.play_land()
        self.pool = self.build_pool()
        self.main_phase()
        if self.doom == "bf":
            self.value_actions()
        self.main_phase()
        self.held = list(self.pool)
        while len(self.hand) > 7 and not any(l["name"] == "Reliquary Tower" for l in self.lands):
            junk = sorted(self.hand, key=lambda c: (c not in LANDS, self.prio(c)))
            self.gy.append(junk[0]); self.hand.remove(junk[0])

    def play_land(self):
        hl = [c for c in self.hand if c in LANDS]
        if not hl:
            return
        def key(l):
            d = LANDS[l]
            score = 0
            if d.get("bog") and "Inverter of Truth" in self.hand:
                score = -10
            elif d.get("bog"):
                score = 5
            if d.get("tapped") and not d.get("bog"):
                score += 3
            if d.get("hall") and self.doom == "cz":
                score -= 2
            return score
        pick = sorted(hl, key=key)[0]
        self.hand.remove(pick)
        d = LANDS[pick]
        for l in list(self.lands):
            if LANDS[l["name"]].get("traitors"):
                self.lands.remove(l); self.gy.append(l["name"])
        self.lands.append({"name": pick, "tapped": bool(d.get("tapped"))})
        self.land_played = True
        if d.get("bog"):
            self.gy = []
        if self.has("horn"):
            self.draw(1)
        if d.get("saga"):
            self.saga_turn = self.turn

    def urza(self):
        for l in list(self.lands):
            if l["name"] == "Urza's Saga" and self.turn - getattr(self, "saga_turn", self.turn) >= 2:
                for c in ("Tormod's Crypt", "Nihil Spellbomb", "Mana Vault", "Sol Ring", "Chrome Mox", "Lotus Petal"):
                    if c in self.lib and (c not in ("Tormod's Crypt", "Nihil Spellbomb") or "Inverter of Truth" in self.hand):
                        self.lib.remove(c)
                        self.perms.append(c)
                        self.entered[c] = self.turn
                        break
                self.lands.remove(l)
                self.gy.append("Urza's Saga")

    def run(self, max_turns=16):
        try:
            for _ in range(max_turns):
                self.my_turn()
                self.urza()
                self.opponents()
        except Won as w:
            self.st["win"] = self.turn
            self.st["how"] = w.how
        except Lost as l:
            self.st["how"] = "lost:" + l.how
            self.st["raced"] = True
        return self.st
