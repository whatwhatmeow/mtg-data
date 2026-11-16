"""Doctor Doom deck simulator (vault tools/doomsim v6), rebuilt Nov 12 with Oracle-checked fixes:
- Cephalid Coliseum: only you draw 3 / discard 3 (Oracle: "Target player"); was modeled as each player.
- Jace {1}{U}{U}{U}, Bone Miser {4}{B}, Currency Converter {1} (+ its {2},T loot) in cards.py.
- New lands: Riverglide Pathway, Hidden Lair, Graven Cairns, Capital City, Desolate Lighthouse.
- Howling Mine, Echo of Eons (no discard; flashback {2}{U}).
- REAL_HANDS: opponents dump 0-1 extra card per turn through turn 5.
"""
import random
from cards import LANDS, CARDS

DOOM = "Doctor Doom, King of Latveria"
UBR = {"U", "B", "R"}
DREDGE = True
CIPHER = True
EOT_TRADE = True
TRADE_MIN_LANDS = 6
COLISEUM = True
MAYHEM = True
REAL_HANDS = True
COLISEUM_EACH_PLAYER = False   # set True to reproduce the old (wrong) model


class Lost(Exception):
    pass


class Won(Exception):
    def __init__(self, how):
        self.how = how


class Game:
    def __init__(self, deck, profile, rng, log=False):
        self.rng = rng
        self.p = profile
        self.logging = log
        self.lines = []
        self.lib = list(deck)
        rng.shuffle(self.lib)
        self.hand, self.gy, self.exile = [], [], []
        self.lands = []
        self.perms = []
        self.copies = 0
        self.copy_cards = []
        self.irma_is_doom = False
        self.doom_bf = False
        self.doom_tax = 0
        self.boots_on_doom = False
        self.class_level = 0
        self.treasures = 0
        self.life = 40
        self.opp = [40, 40, 40]
        self.opp_hand = [7, 7, 7]
        self.opp_board = [[], [], []]
        self.moon = []
        self.army = 0
        self.cipher = False
        self.tapped_treasures = 0
        self.frog_counters = 0
        self.goblin_counters = 0
        self.spells_cast_turn = 0
        self.discarded_cards_turn = set()
        self.land_played = False
        self.mayhem_pending = False
        self.dredge_on = DREDGE
        self.discarded_turn = 0
        self.turn = 0
        self.on_play = rng.random() < 0.25
        self.sick = set()
        self.held = []
        self.pool = []
        self.pool_src = []
        self.monument_modes = set()
        self.drawn_this_turn = 0
        self.miracle = False
        self.dmg_turn = 0
        self.ping_turn = 0
        self.stats = dict(engine=None, inevitable=None, win=None, how=None,
                          doom_removed=0, removal_stopped=0, wipes=0, doom_casts=0, boots_used=False)
        self.laser_dmg = 0
        self.last_laser_turn = None
        self.mulligan()

    def log(self, s):
        if self.logging:
            self.lines.append(f"T{self.turn}: {s}")

    def bump(self, k, n=1):
        self.stats[k] = self.stats.get(k, 0) + n

    def alive(self):
        return [i for i in range(3) if self.opp[i] > 0]

    def check_win(self):
        if not self.alive():
            raise Won("drain")

    def lose_each(self, n, src=""):
        if n <= 0:
            return
        for i in self.alive():
            self.opp[i] -= n
        self.dmg_turn += n
        self.check_win()

    def ping(self, n):
        for _ in range(n):
            al = self.alive()
            if not al:
                break
            i = min(al, key=lambda k: self.opp[k])
            self.opp[i] -= 1
            self.ping_turn += 1
        self.check_win()

    def has(self, tag):
        return any(tag in CARDS[c]["tags"] for c in self.perms)

    def count(self, tag):
        return sum(tag in CARDS[c]["tags"] for c in self.perms)

    def doom_instances(self):
        return int(self.doom_bf) + self.copies + int(self.irma_is_doom)

    def creatures(self):
        return [c for c in self.perms if CARDS[c]["type"] == "creature"]

    def mulligan(self):
        for attempt in range(4):
            if attempt:
                self.lib += self.hand
                self.hand = []
                self.rng.shuffle(self.lib)
            self.hand = [self.lib.pop() for _ in range(7)]
            nl = sum(c in LANDS and c != "Dakmor Salvage" for c in self.hand)
            if 3 <= nl <= 5 or attempt == 3:
                bottom = max(0, attempt - 1)
                for _ in range(bottom):
                    lands = [c for c in self.hand if c in LANDS]
                    spells = [c for c in self.hand if c not in LANDS]
                    pick = lands[-1] if len(lands) > 4 or not spells else spells[-1]
                    self.hand.remove(pick)
                    self.lib.insert(0, pick)
                return

    def draw(self, n, draw_step=False):
        for k in range(n):
            reps = 1
            if self.has("insight") and not (draw_step and k == 0):
                reps = 2
            for _ in range(reps):
                if self.can_dredge():
                    self.dredge()
                    continue
                if not self.lib:
                    if self.has("jace"):
                        raise Won("jace")
                    raise Lost("decked")
                c = self.lib.pop()
                self.hand.append(c)
                self.drawn_this_turn += 1
                if self.drawn_this_turn == 1 and c == "Reforge the Soul":
                    self.miracle = True
                if self.has("crawler"):
                    self.lose_each(self.count("crawler"))

    DAK = "Dakmor Salvage"

    def can_dredge(self):
        if self.DAK not in self.gy or not self.dredge_on:
            return False
        if len(self.lib) < 2 or (len(self.lib) < 8 and not self.has("jace")):
            return False
        engine = self.doom_instances() > 0 or self.class_level >= 2
        outlet = self.has("outlet_free") or self.has("seismic") or self.has("tectonic") or self.has("trade") \
            or self.doom_instances() > 0
        return engine and outlet

    def dredge(self):
        self.gy.remove(self.DAK)
        for _ in range(2):
            self.gy.append(self.lib.pop())
        self.hand.append(self.DAK)
        self.bump("dredges")

    def ammo(self):
        real = [c for c in self.hand if c in LANDS and c != self.DAK]
        real.sort(key=lambda l: (not LANDS[l][2].get("basic"), not LANDS[l][1]))
        out = [self.DAK] if self.DAK in self.hand else []
        if self.mayhem_pending and "Oscorp Industries" in real:
            real.remove("Oscorp Industries")
            out = ["Oscorp Industries"] + out
            return out + real[:max(0, len(real) - self.keep_lands() + 1)]
        return out + real[:max(0, len(real) - self.keep_lands())]

    def draws_safe(self, mine, opp_each=0):
        if self.has("jace"):
            return True
        mult = 2 if self.has("insight") else 1
        total = mine * mult
        if self.has("thief"):
            total += opp_each * len(self.alive()) * mult
        return total + 2 < len(self.lib)

    def opp_draw(self, i, n, extra_only=False):
        """Opponent i draws n cards outside the first draw of their draw step."""
        if self.opp[i] <= 0 or n <= 0:
            return
        if self.has("thief"):
            self.draw(n)
            return
        if self.has("narset"):
            n = 0 if extra_only else min(n, 1)
            if n == 0:
                return
        self.opp_hand[i] += n
        if self.has("bowmasters"):
            self.bow_trigger(n * self.count("bowmasters"))

    def discard(self, cards):
        if not cards:
            return
        for c in cards:
            self.hand.remove(c)
            self.gy.append(c)
        self.discarded_turn += len(cards)
        self.discarded_cards_turn.update(cards)
        if "Archfiend of Ifnir" in self.perms:
            self.shrink_opp_boards(len(cards))
        nland = sum(c in LANDS for c in cards)
        if nland:
            mult = 2 if self.has("throne") else 1
            self.lose_each(2 * self.doom_instances() * mult)
        if self.has("tinybones"):
            self.lose_each(1)
        if self.class_level >= 2:
            self.lose_each(2 * len(cards))
        if "Green Goblin, Nemesis" in self.perms:
            for c in cards:
                if c in LANDS:
                    self.tapped_treasures += 1
                else:
                    self.goblin_counters += 1
        if "Glint-Horn Buccaneer" in self.perms:
            self.lose_each(self.perms.count("Glint-Horn Buccaneer") * len(cards))
        for c in cards:
            if self.has("monument"):
                for mode in ("drain", "draw", "treasure"):
                    if mode not in self.monument_modes:
                        self.monument_modes.add(mode)
                        if mode == "drain":
                            self.lose_each(3)
                        elif mode == "draw":
                            self.draw(1)
                        else:
                            self.treasures += 1
                        break
            if self.has("miser"):
                if c in LANDS:
                    self.pool += [{"B"}, {"B"}]
                elif CARDS.get(c, {}).get("type") != "creature":
                    self.draw(1)

    def shrink_opp_boards(self, n):
        for i in range(3):
            self.opp_board[i] = [t - n for t in self.opp_board[i] if t - n > 0]

    def laser_attack(self):
        if "Living Laser" not in self.perms:
            return
        if self.has("outlet_free") and self.alive():
            i = min(self.alive(), key=lambda k: self.opp[k])
            need = -(-self.opp[i] // 4) + len(self.opp_board[i])
            if 1 + self.discarded_turn + len(self.hand) >= need:
                for c in list(self.hand):
                    self.discard([c])
        attackers = 1 + self.discarded_turn
        dealt = 0
        for i in sorted(self.alive(), key=lambda k: self.opp[k]):
            if attackers <= 0:
                break
            blockers = len(self.opp_board[i])
            need = -(-self.opp[i] // 4) + blockers
            send = min(attackers, need)
            attackers -= send
            unblocked = max(0, send - blockers)
            blocked = min(send, blockers)
            self.opp_board[i] = sorted(self.opp_board[i])[blocked:] + [t for t in sorted(self.opp_board[i])[:blocked] if t > 4]
            self.opp[i] -= 4 * unblocked
            dealt += 4 * unblocked
        self.laser_dmg += dealt
        self.last_laser_turn = self.turn
        self.check_win()

    def bow_trigger(self, k):
        self.army += k
        self.ping(k)

    def opp_discard(self, i, n):
        if n <= 0 or self.opp[i] <= 0:
            return
        self.opp_hand[i] -= n
        if self.has("tinybones"):
            self.lose_each(1)
        if self.has("wastenot"):
            for _ in range(n):
                r = self.rng.random()
                if r < 0.35:
                    self.draw(1)
                elif r < 0.65:
                    self.pool += [{"B"}, {"B"}]

    # ---------------- mana ----------------
    def build_pool(self):
        pool = []
        lantern = self.has("lantern")
        artifact = any(CARDS[c]["type"] == "artifact" or c == "Doom Variant" for c in self.perms)
        types = self.types_in_play()
        swamp = "Swamp" in types
        basic = any(l.get("basic") for l in self.lands)
        others = sum(1 for l in self.lands if not l["entered_tapped"] and not l.get("filter")) + \
            sum(1 for c in self.perms if CARDS[c].get("prod"))
        for l in self.lands:
            if l["entered_tapped"]:
                continue
            cols = set(l["colors"])
            if l.get("tainted") and not swamp:
                cols = {"C"}
            if l.get("lair") and not (basic or l.get("new")):
                cols = {"C"}
            if l.get("filter") and others == 0:
                cols = {"C"}
            if l.get("spire") and artifact:
                cols = set(UBR)
            if lantern:
                cols = set(UBR)
            src = {"cols": cols, "land": l["name"]}
            if l.get("tomb"):
                pool.append({"cols": {"C"}, "land": "Ancient Tomb"})
            if l.get("plaza"):
                src["plaza"] = True
            if l.get("villain"):
                src["villain"] = True
            pool.append(src)
        for c in self.perms:
            prod = CARDS[c].get("prod")
            if prod == "CC":
                pool += [{"cols": {"C"}}, {"cols": {"C"}}]
            elif prod:
                pool.append({"cols": set(prod)})
        return pool

    _villain_spell = False
    VILLAINS = {"Doctor Doom, King of Latveria", "Living Laser", "Green Goblin, Nemesis",
                "Norman Osborn // Green Goblin", "Moonstone, Harsh Mistress", "M.O.D.O.K.",
                "Chameleon, Master of Disguise", "Taskmaster, Mercenary Mimic", "Loki, God of Mischief"}

    def _alloc(self, cost, sources, legend):
        pips = []
        for col in "UBR":
            pips += [col] * cost.get(col, 0)
        idx = list(range(len(sources)))

        def cols_of(i):
            s = sources[i]
            if s.get("plaza") and legend:
                return UBR
            if s.get("villain") and self._villain_spell:
                return UBR
            return s["cols"]

        used = []

        def bt(k):
            if k == len(pips):
                return True
            col = pips[k]
            cands = sorted((i for i in idx if i not in used and col in cols_of(i)), key=lambda i: len(cols_of(i)))
            for i in cands[:4]:
                used.append(i)
                if bt(k + 1):
                    return True
                used.pop()
            return False

        if not bt(0):
            return None
        rest = sorted((i for i in idx if i not in used), key=lambda i: len(cols_of(i)) if "C" not in cols_of(i) else 0)
        g = cost.get("g", 0)
        if len(rest) < g:
            return None
        return used + rest[:g]

    def all_sources(self):
        return self.pool_src + [{"cols": set(x)} for x in self.pool] + [{"cols": set(UBR), "treasure": True}] * self.treasures

    def can_pay(self, cost, legend=False, reserve=None):
        srcs = self.all_sources()
        a = self._alloc(cost, srcs, legend)
        if a is None:
            return False
        if reserve:
            rest = [s for i, s in enumerate(srcs) if i not in a]
            return self._alloc(reserve, rest, False) is not None
        return True

    def pay(self, cost, legend=False):
        srcs = self.all_sources()
        a = self._alloc(cost, srcs, legend)
        if a is None:
            return False
        n_src = len(self.pool_src)
        n_pool = len(self.pool)
        used_src = sorted([i for i in a if i < n_src], reverse=True)
        used_pool = sorted([i - n_src for i in a if n_src <= i < n_src + n_pool], reverse=True)
        used_tr = sum(1 for i in a if i >= n_src + n_pool)
        for i in used_src:
            self.pool_src.pop(i)
        for i in used_pool:
            self.pool.pop(i)
        self.treasures -= used_tr
        return True

    def take_land_src(self, name, cost):
        """Tap a specific land plus pay cost from the rest; returns True if done."""
        src = next((x for x in self.pool_src if x.get("land") == name), None)
        if src is None:
            return False
        self.pool_src.remove(src)
        if not self.can_pay(cost, reserve=self.reserve_cost()):
            self.pool_src.append(src)
            return False
        self.pay(cost)
        return True

    def reserve_cost(self):
        if self.doom_instances() == 0:
            return None
        counters = [c for c in self.hand if "counter" in CARDS.get(c, {}).get("tags", ())]
        if not counters:
            return None
        best = min(counters, key=lambda c: sum(CARDS[c]["cost"].values()))
        return CARDS[best]["cost"]

    # ---------------- casting ----------------
    def cast(self, card, from_cz=False):
        info = CARDS[card]
        self.spell_cast()
        if not from_cz and card in self.hand:
            self.hand.remove(card)
        t = info["type"]
        tags = info["tags"]
        self.log(f"cast {card}")
        if card == DOOM:
            self.stats["doom_casts"] += 1
            self.doom_tax += 2
            if self.rng.random() < self.p["counter_doom"]:
                return
            self.doom_bf = True
            self.sick.add(card)
            if self.has("boots") and self.can_pay({"g": 1}):
                self.pay({"g": 1})
                self.boots_on_doom = True
            return
        if t in ("instant", "sorcery"):
            self.gy.append(card)
            self.resolve_spell(card)
            return
        self.perms.append(card)
        self.sick.add(card)
        prod = info.get("prod")
        if prod == "CC":
            self.pool_src += [{"cols": {"C"}}, {"cols": {"C"}}]
        elif prod:
            self.pool_src.append({"cols": set(prod)})
        if "copy" in tags and self.doom_instances() > 0:
            self.copies += 1
            self.copy_cards.append(card)
        if "yoh" in tags:
            self.yoh_left = 3
            self.year_of_hell()
        if card == "Cool but Rude":
            self.class_level = 1
        if card == "Tinybones, Pocket Nuisance":
            for i in self.alive():
                self.opp_discard(i, min(1, self.opp_hand[i]))
        if card == "Orcish Bowmasters":
            self.bow_trigger(1)
        if "boots" in tags and self.doom_bf and self.can_pay({"g": 1}):
            self.pay({"g": 1})
            self.boots_on_doom = True

    def year_of_hell(self):
        if getattr(self, "yoh_left", 0) <= 0:
            return
        self.yoh_left -= 1
        self.draw(1)
        for i in self.alive():
            self.opp_draw(i, 1)
        self.lose_each(2)
        self.life -= 2
        if self.yoh_left == 0 and "Year of Hell" in self.perms:
            self.perms.remove("Year of Hell")
            self.gy.append("Year of Hell")

    def resolve_spell(self, card):
        info = CARDS[card]
        if "wheel" in info["tags"]:
            self.do_wheel(info["wheel"])
        elif "loot2" in info["tags"]:
            self.draw(2)
            self.discard_best(2)
            if "free" in info["tags"]:
                for _ in range(3):
                    self.pool.append(set(UBR) if self.has("lantern") else {"U"})
        elif "inquiry" in info["tags"]:
            self.draw(3)
            for i in self.alive():
                self.opp_draw(i, 3)
            k = min(3, len(self.hand))
            self.discard(self.rng.sample(self.hand, k))
            for i in self.alive():
                self.opp_discard(i, min(3, self.opp_hand[i]))
        elif "echo" in info["tags"]:
            self.do_echo()

    def do_echo(self):
        """Each player shuffles hand + graveyard into library, then draws seven. No discard."""
        self.bump("echo_casts")
        back = [c for c in self.hand + self.gy if c != "Echo of Eons"]
        keep = [c for c in self.gy if c == "Echo of Eons"]
        self.lib += back
        self.hand = []
        self.gy = keep
        self.rng.shuffle(self.lib)
        self.draw(7)
        for i in self.alive():
            self.opp_hand[i] = 0
            self.opp_draw(i, 7)

    def discard_best(self, n):
        lands = sorted([c for c in self.hand if c in LANDS], key=lambda l: l != self.DAK)
        spells = [c for c in self.hand if c not in LANDS]
        pick = (lands + sorted(spells, key=self.spell_value))[:n]
        if pick:
            self.discard(pick)

    def spell_value(self, c):
        tags = CARDS[c]["tags"]
        if "echo" in tags:
            return -1
        if tags & {"removal", "wipe"}:
            return 0
        if not tags:
            return 1
        return 5

    # ---------------- wheels ----------------
    def wheel_draws(self, kind, my_hand):
        opp_h = [self.opp_hand[i] for i in self.alive()]
        if kind == "max":
            return max([my_hand] + opp_h)
        if kind == "minus1":
            return max(0, my_hand - 1)
        return kind

    def expected_self_draws(self, kind):
        my_h = len(self.hand) - 1
        x = self.wheel_draws(kind, my_h)
        mult = 2 if self.has("insight") else 1
        total = x * mult
        if self.has("thief"):
            if kind == "minus1":
                opp = sum(max(0, self.opp_hand[i] - 1) for i in self.alive())
            else:
                opp = x * len(self.alive())
            total += opp * mult
        return total

    def do_wheel(self, kind):
        my_h = len(self.hand)
        x = self.wheel_draws(kind, my_h)
        self.bump("wheels")
        self.discard(list(self.hand))
        opp_counts = {}
        for i in self.alive():
            opp_counts[i] = self.opp_hand[i]
            self.opp_discard(i, self.opp_hand[i])
        self.draw(x if kind != "minus1" else max(0, my_h - 1))
        for i in self.alive():
            self.opp_draw(i, x if kind != "minus1" else max(0, opp_counts[i] - 1))

    def payoff_out(self):
        return (self.doom_instances() or self.has("crawler") or self.has("thief")
                or self.has("tinybones") or (self.has("bowmasters") and not self.has("narset")))

    def wheel_ok(self, kind):
        if not self.payoff_out():
            return False
        if self.expected_self_draws(kind) + 3 >= len(self.lib) and not self.has("jace"):
            return False
        if self.has("jace") and self.expected_self_draws(kind) >= len(self.lib):
            return True
        nonland = [c for c in self.hand if c not in LANDS and "wheel" not in CARDS[c]["tags"]]
        locked = self.has("thief") or self.has("narset")
        if not any(c in LANDS for c in self.hand):
            return True
        return locked or len(nonland) <= 2

    def echo_ok(self):
        if not self.payoff_out():
            return False
        if not self.has("jace") and len(self.lib) + len(self.hand) + len(self.gy) < 20:
            return False
        nonland = [c for c in self.hand if c not in LANDS and c != "Echo of Eons"]
        return len(self.hand) <= 3 or len(nonland) <= 1

    # ---------------- discard outlets ----------------
    def keep_lands(self):
        if self.has("crucible") and len(self.lands) >= 6:
            return 0
        return 2 if len(self.lands) < 6 else 1

    def outlet_loop(self):
        guard = 0
        while guard < 200:
            guard += 1
            am = self.ammo()
            want = self.doom_instances() > 0 or self.class_level >= 2 or self.has("seismic") or self.has("glint")
            if not want or not am:
                break
            res = self.reserve_cost()
            land = am[0]
            safe = self.draws_safe(1)
            if safe and self.has("tectonic") and self.can_pay({"R": 1}, reserve=res):
                self.pay({"R": 1})
                self.discard([land])
                self.draw(1)
                continue
            if safe and self.has("trade") and self.can_pay({"g": 1}, reserve=res):
                self.pay({"g": 1})
                self.discard([land])
                self.draw(1)
                continue
            cyc = LANDS[land][2].get("cycle")
            if safe and cyc and self.can_pay(cyc, reserve=res):
                self.pay(cyc)
                self.discard([land])
                self.draw(1)
                continue
            if self.has("outlet_free"):
                self.discard([land])
                if "Psychic Frog" in self.perms:
                    self.frog_counters += 1
                if "Seismic Assault" in self.perms:
                    self.ping(2)
                continue
            if safe and self.converter_ready and self.take_converter():
                self.draw(1)
                self.discard([land])
                continue
            if safe and self.lighthouse_ready and self.take_lighthouse():
                self.draw(1)
                self.discard([land])
                continue
            break

    converter_ready = False
    lighthouse_ready = False

    def take_converter(self):
        if "Currency Converter" not in self.perms or "Currency Converter" in self.sick:
            return False
        if not self.can_pay({"g": 2}, reserve=self.reserve_cost()):
            return False
        self.pay({"g": 2})
        self.converter_ready = False
        self.bump("converter_loots")
        return True

    def take_lighthouse(self):
        if not self.take_land_src("Desolate Lighthouse", {"g": 1, "U": 1, "R": 1}):
            return False
        self.lighthouse_ready = False
        self.bump("lighthouse_loots")
        return True

    def trade_routes_bounce(self):
        if not (self.has("trade") and self.doom_instances()):
            return
        free = self.has("outlet_free")
        guard = 0
        while guard < 20 and len(self.lands) > TRADE_MIN_LANDS:
            guard += 1
            res = self.reserve_cost()
            if not free and not self.draws_safe(1):
                break
            cost = {"g": 1 if free else 2}
            if not self.can_pay(cost, reserve=res):
                break
            self.pay(cost)
            l = sorted(self.lands, key=lambda x: (not LANDS[x["name"]][2].get("basic")))[0]
            self.lands.remove(l)
            self.hand.append(l["name"])
            self.discard([l["name"]])
            if free:
                if "Seismic Assault" in self.perms:
                    self.ping(2)
            else:
                self.draw(1)
            self.outlet_loop()

    # ---------------- my turn ----------------
    PRIORITY = [
        ("rock", 90), ("boots", 80), ("outlet_free", 70), ("class", 72), ("tectonic", 65), ("trade", 64),
        ("seismic", 66), ("tinybones", 60), ("monument", 58), ("miser", 50),
        ("throne", 68), ("copy", 67), ("yoh", 58), ("irma", 63), ("thief", 75), ("narset", 57),
        ("bowmasters", 61), ("crawler", 56), ("wastenot", 52), ("insight", 54), ("bmc", 53),
        ("crucible", 51), ("archivist", 59), ("jace", 74), ("laser", 60), ("glint", 69), ("norman", 58),
        ("goblin", 64), ("converter", 50), ("leng", 52), ("archfiend", 60), ("shredder", 64), ("loki", 58),
        ("taskmaster", 60), ("mine", 71), ("vise", 40),
    ]

    def prio(self, c):
        tags = CARDS[c]["tags"]
        if "rock" in tags:
            return 90 if self.turn <= 5 else 30
        if tags & {"copy", "throne"} and self.doom_instances() == 0:
            return -1
        if "irma" in tags and self.doom_instances() == 0:
            return -1
        if tags & {"counter", "removal", "wipe", "wheel", "loot2", "inquiry", "shred", "tutor_any", "echo"}:
            return -1
        if "jace" in tags and len(self.lib) > 45:
            return 20
        best = 10
        for t, v in self.PRIORITY:
            if t in tags:
                best = max(best, v)
        return best

    TUTOR_ORDER = ["Cool but Rude", "Black Market Connections", "Monument to Endurance", "Jace's Archivist",
                   "Psychic Frog", "Doom Variant", "Windfall", "Crucible of Worlds", "Notion Thief"]

    def try_transmute(self):
        for card, cost in (("Muddle the Mixture", {"g": 1, "U": 2}), ("Shred Memory", {"g": 1, "B": 2})):
            self._transmute2(card, cost)
        for t in [c for c in self.hand if c in CARDS and "tutor_any" in CARDS[c]["tags"]]:
            self.try_tutor(t)

    def try_tutor(self, t):
        if t not in self.hand:
            return
        have = set(self.hand) | set(self.perms)
        if self.class_level:
            have.add("Cool but Rude")
        want = [c for c in self.TUTOR_ORDER if c in self.lib and c not in have]
        if not want or not self.can_pay(CARDS[t]["cost"], reserve=self.reserve_cost()):
            return
        self.pay(CARDS[t]["cost"])
        self.hand.remove(t)
        self.gy.append(t)
        self.lib.remove(want[0])
        self.hand.append(want[0])
        self.rng.shuffle(self.lib)

    def _transmute2(self, card, cost):
        if card not in self.hand or self.class_level or "Cool but Rude" in self.hand:
            return
        if "Cool but Rude" not in self.lib:
            return
        if self.can_pay(cost):
            self.pay(cost)
            self.discard([card])
            if "Cool but Rude" in self.lib:
                self.lib.remove("Cool but Rude")
                self.hand.append("Cool but Rude")
            self.rng.shuffle(self.lib)

    PERPLEX_TARGETS = ["Black Market Connections", "Monument to Endurance", "Jace's Archivist",
                       "Windfall", "Crucible of Worlds", "Wheel of Fortune"]

    def try_perplex(self):
        card, cost = "Perplex", {"g": 1, "U": 1, "B": 1}
        if card not in self.hand:
            return
        have = set(self.hand) | set(self.perms)
        want = [c for c in self.PERPLEX_TARGETS if c in self.lib and c not in have]
        if not want or not self.can_pay(cost):
            return
        if self.doom_instances() and want[0] not in self.PERPLEX_TARGETS[:3]:
            return
        self.pay(cost)
        self.discard([card])
        if want[0] in self.lib:
            self.lib.remove(want[0])
            self.hand.append(want[0])
            self.rng.shuffle(self.lib)

    def main_phase(self):
        self.try_transmute()
        self.try_perplex()
        guard = 0
        while guard < 40:
            guard += 1
            if not self.doom_bf and self.doom_tax < 12:
                cost = dict(CARDS[DOOM]["cost"])
                cost["g"] += self.doom_tax
                self._villain_spell = True
                ok = self.can_pay(cost, legend=True)
                if ok:
                    self.pay(cost, legend=True)
                self._villain_spell = False
                if ok:
                    self.cast(DOOM, from_cz=True)
                    continue
            res = self.reserve_cost()
            CH = "Chameleon, Master of Disguise"
            if CH in self.gy and CH in self.discarded_cards_turn and self.doom_instances() \
                    and self.can_pay({"g": 2, "U": 1}, reserve=res):
                self.pay({"g": 2, "U": 1})
                self.gy.remove(CH)
                self.hand.append(CH)
                self.discarded_cards_turn.discard(CH)
                self.cast(CH)
                continue
            cands = sorted({c for c in self.hand if c in CARDS and self.prio(c) >= 0}, key=lambda c: -self.prio(c))
            done = False
            for c in cands:
                info = CARDS[c]
                self._villain_spell = c in self.VILLAINS
                ok = self.can_pay(info["cost"], legend=info.get("legend", False), reserve=res)
                if ok:
                    self.pay(info["cost"], legend=info.get("legend", False))
                self._villain_spell = False
                if ok:
                    self.cast(c)
                    done = True
                    break
            if done:
                continue
            if 1 <= self.class_level < 3 and self.can_pay({"g": 1, "R": 1}, reserve=res):
                self.pay({"g": 1, "R": 1})
                self.class_level += 1
                if self.class_level == 3:
                    self.tutor()
                    if self.hand:
                        self.discard([self.rng.choice(self.hand)])
                continue
            break

    def tutor(self):
        wants = ["Psychic Frog", "Seismic Assault", "Notion Thief", "Doom Variant", "Trade Routes",
                 "Psychosis Crawler", "Windfall", "Jace, Wielder of Mysteries"]
        for w in wants:
            if w in self.lib and w not in self.perms:
                self.lib.remove(w)
                self.hand.append(w)
                self.rng.shuffle(self.lib)
                return

    def play_land(self):
        OS = "Oscorp Industries"
        if MAYHEM and OS in self.hand and self.life > 12 and \
                (self.doom_instances() or self.has("outlet_free") or self.has("seismic")):
            self.mayhem_pending = True
            return
        self._play_land()

    NORMAN = "Norman Osborn // Green Goblin"

    def maybe_encode(self, w):
        if CIPHER and w == "Whispering Madness" and self.NORMAN in self.perms and not self.cipher \
                and "Whispering Madness" in self.gy:
            self.gy.remove("Whispering Madness")
            self.cipher = True

    TASK = "Taskmaster, Mercenary Mimic"

    def taskmaster_copy(self):
        if self.TASK in self.copy_cards:
            self.copy_cards.remove(self.TASK)
            self.copies -= 1
        if self.TASK in self.perms and self.doom_instances() > 0:
            self.copy_cards.append(self.TASK)
            self.copies += 1

    def frog_attack(self):
        F = "Psychic Frog"
        if F not in self.perms or F in self.sick or not self.alive():
            return
        fodder = [c for c in self.gy if c not in LANDS]
        if len(fodder) < 3:
            return
        for c in fodder[:3]:
            self.gy.remove(c)
            self.exile.append(c)
        if self.rng.random() < 0.8:
            i = min(self.alive(), key=lambda k: self.opp[k])
            self.opp[i] -= 1 + self.frog_counters
            self.check_win()
            if self.draws_safe(1):
                self.draw(1)

    def goblin_attack(self):
        G = "Green Goblin, Nemesis"
        if G not in self.perms or G in self.sick or not self.alive():
            return
        if self.rng.random() < 0.8:
            i = min(self.alive(), key=lambda k: self.opp[k])
            self.opp[i] -= 3 + self.goblin_counters
            self.check_win()

    def connive(self):
        if self.draws_safe(1):
            self.draw(1)
        am = self.ammo()
        if am:
            self.discard([am[0]])
        elif self.hand:
            self.discard_best(1)

    def spell_cast(self):
        self.spells_cast_turn += 1
        if self.spells_cast_turn == 2 and "Ledger Shredder" in self.perms:
            self.connive()

    def norman_attack(self):
        if self.NORMAN not in self.perms or self.NORMAN in self.sick or not self.alive():
            return
        i = min(self.alive(), key=lambda k: self.opp[k])
        self.opp[i] -= 1
        self.check_win()
        if self.draws_safe(1):
            self.draw(1)
            am = self.ammo()
            if am:
                self.discard([am[0]])
            elif self.hand:
                self.discard_best(1)
        if self.cipher and self.wheel_ok("max"):
            self.outlet_loop()
            self.do_wheel("max")
            self.outlet_loop()

    LAND_TYPES = {"Island": ("Island",), "Swamp": ("Swamp",), "Mountain": ("Mountain",),
                  "Fetid Pools": ("Island", "Swamp"), "Sunken Hollow": ("Island", "Swamp"),
                  "Canyon Slough": ("Swamp", "Mountain"), "Smoldering Marsh": ("Swamp", "Mountain"),
                  "Scorched Geyser": ("Island", "Mountain")}

    def types_in_play(self):
        t = set()
        for l in self.lands:
            t.update(self.LAND_TYPES.get(l["name"], ()))
        return t

    def enters_tapped(self, name):
        cols, tapped, extra = LANDS[name]
        cond = extra.get("cond")
        if cond is None:
            return tapped
        if cond == "swamp":
            return "Swamp" not in self.types_in_play()
        if cond == "2basics":
            return sum(1 for l in self.lands if l.get("basic")) < 2
        if cond == "reveal_UB":
            return not any(any(t in ("Island", "Swamp") for t in self.LAND_TYPES.get(c, ())) for c in self.hand)
        return not (set(cond) & self.types_in_play())

    def try_petrified(self):
        land = next((l for l in self.lands if l.get("petrified")), None)
        if not land or self.ammo() or not self.doom_instances() or len(self.lands) < 7:
            return
        src = next((x for x in self.pool_src if x.get("land") == "Petrified Field"), None)
        targets = [c for c in self.gy if c in LANDS]
        if src is None or not targets:
            return
        self.pool_src.remove(src)
        self.lands.remove(land)
        self.gy.append("Petrified Field")
        pick = self.DAK if self.DAK in targets else targets[0]
        self.gy.remove(pick)
        self.hand.append(pick)
        self.outlet_loop()

    def try_hideout(self):
        if not self.doom_instances():
            return
        if self.take_land_src("Villainous Hideout", {"g": 3}):
            self.connive()
            self.outlet_loop()

    def try_coliseum(self):
        if not COLISEUM:
            return
        land = next((l for l in self.lands if l.get("coliseum")), None)
        if not land or len(self.gy) < 7 or len(self.lands) < 6:
            return
        payoff = self.doom_instances() or self.class_level >= 2 or self.has("tinybones") or self.has("glint")
        if COLISEUM_EACH_PLAYER:
            payoff = payoff or (self.has("bowmasters") and not self.has("narset")) or self.has("thief")
        if not payoff or not self.draws_safe(3, 3 if COLISEUM_EACH_PLAYER else 0):
            return
        if not self.take_land_src("Cephalid Coliseum", {"U": 1}):
            return
        self.lands.remove(land)
        self.gy.append("Cephalid Coliseum")
        self.bump("coliseum")
        self.draw(3)
        if COLISEUM_EACH_PLAYER:
            for i in self.alive():
                self.opp_draw(i, 3)
        lands = sorted([c for c in self.hand if c in LANDS], key=lambda l: l != self.DAK)
        spells = sorted([c for c in self.hand if c not in LANDS], key=self.spell_value)
        pick = (lands + spells)[:3]
        if pick:
            self.discard(pick)
        if COLISEUM_EACH_PLAYER:
            for i in self.alive():
                self.opp_discard(i, min(3, self.opp_hand[i]))
        self.outlet_loop()

    def finish_land_drop(self):
        if not self.mayhem_pending or self.land_played:
            return
        self.mayhem_pending = False
        OS = "Oscorp Industries"
        if OS in self.gy and OS in self.discarded_cards_turn:
            self.gy.remove(OS)
            self.life -= 2
            cols, _, extra = LANDS[OS]
            self.lands.append({"name": OS, "colors": cols, "entered_tapped": True, **extra})
            self.land_played = True
        else:
            n = len(self.lands)
            self._play_land()
            if len(self.lands) > n and not self.lands[-1]["entered_tapped"]:
                l = self.lands[-1]
                self.pool_src.append({"cols": set(UBR) if self.has("lantern") else set(l["colors"]), "land": l["name"]})

    def _play_land(self):
        self.land_played = True
        gy_lands = [c for c in self.gy if c in LANDS and c != self.DAK]
        hand_lands = [c for c in self.hand if c in LANDS and c != self.DAK]
        if self.has("crucible") and gy_lands:
            pick = sorted(gy_lands, key=lambda l: LANDS[l][1])[0]
            self.gy.remove(pick)
        elif hand_lands:
            pick = sorted(hand_lands, key=lambda l: (LANDS[l][1], -len(LANDS[l][0])))[0]
            self.hand.remove(pick)
        else:
            return
        cols, tapped, extra = LANDS[pick]
        tapped = self.enters_tapped(pick)
        if extra.get("pathway"):
            a, b = extra["pathway"]
            counts = {k: sum(k in x["colors"] for x in self.lands) for k in (a, b)}
            cols = {min((a, b), key=lambda k: counts[k])}
        entry = {"name": pick, "colors": cols, "entered_tapped": tapped, "new": True, **extra}
        self.lands.append(entry)

    def my_turn(self):
        self.turn += 1
        self.dmg_turn = 0
        self.ping_turn = 0
        self.drawn_this_turn = 0
        self.miracle = False
        self.monument_modes = set()
        self.discarded_turn = 0
        self.discarded_cards_turn = set()
        self.land_played = False
        self.mayhem_pending = False
        self.converter_ready = True
        self.lighthouse_ready = True
        self.sick = set()
        self.pool = []
        for l in self.lands:
            l["entered_tapped"] = False
            l["new"] = False
        self.treasures += self.tapped_treasures
        self.tapped_treasures = 0
        self.spells_cast_turn = 0
        for l in list(self.lands):
            if l.get("landscape") and l.get("age", 0) >= 1:
                counts = {col: sum(col in x["colors"] for x in self.lands) for col in "UBR"}
                need = min("UBR", key=lambda k: counts[k])
                basic = {"U": "Island", "B": "Swamp", "R": "Mountain"}[need]
                if basic in self.lib:
                    self.lib.remove(basic)
                    self.lands.remove(l)
                    self.gy.append(l["name"])
                    cols, _, extra = LANDS[basic]
                    self.lands.append({"name": basic, "colors": cols, "entered_tapped": False, **extra})
            l["age"] = l.get("age", 0) + 1
        start = list(self.opp)
        if not (self.turn == 1 and self.on_play):
            self.draw(1, draw_step=True)
            if self.has("mine"):
                self.draw(self.count("mine"))
        self.year_of_hell()
        self.play_land()
        self.pool_src = self.build_pool()
        if self.has("bmc") and self.life > 20 and self.draws_safe(1):
            self.life -= 3
            self.treasures += 1
            self.draw(1)
        if self.miracle and "Reforge the Soul" in self.hand and self.can_pay({"g": 1, "R": 1}) and self.wheel_ok(7):
            self.pay({"g": 1, "R": 1})
            self.hand.remove("Reforge the Soul")
            self.gy.append("Reforge the Soul")
            self.do_wheel(7)
        self.main_phase()
        self.outlet_loop()
        for l in self.lands:
            if l.get("geier"):
                if self.draws_safe(1, 1) and (self.doom_instances() or self.has("tinybones") or self.has("bowmasters")):
                    if self.take_land_src("Geier Reach Sanitarium", {"g": 2}):
                        self.draw(1)
                        for i in self.alive():
                            self.opp_draw(i, 1)
                        self.discard_best(1)
                        for i in self.alive():
                            self.opp_discard(i, min(1, self.opp_hand[i]))
        self.try_coliseum()
        self.try_petrified()
        self.try_hideout()
        for _ in range(3):
            self.outlet_loop()
            wheels = [c for c in self.hand if c in CARDS and "wheel" in CARDS[c]["tags"]]
            cast_one = False
            for w in sorted(wheels, key=lambda c: sum(CARDS[c]["cost"].values())):
                if self.wheel_ok(CARDS[w]["wheel"]) and self.can_pay(CARDS[w]["cost"]):
                    self.pay(CARDS[w]["cost"])
                    self.hand.remove(w)
                    self.gy.append(w)
                    self.spell_cast()
                    self.do_wheel(CARDS[w]["wheel"])
                    self.maybe_encode(w)
                    cast_one = True
                    break
            if not cast_one:
                E = "Echo of Eons"
                if E in self.gy and self.echo_ok() and self.can_pay({"g": 2, "U": 1}):
                    self.pay({"g": 2, "U": 1})
                    self.gy.remove(E)
                    self.exile.append(E)
                    self.spell_cast()
                    self.do_echo()
                    cast_one = True
                elif E in self.hand and self.echo_ok() and self.can_pay(CARDS[E]["cost"]):
                    self.pay(CARDS[E]["cost"])
                    self.hand.remove(E)
                    self.spell_cast()
                    self.do_echo()
                    self.gy.append(E)
                    cast_one = True
            if not cast_one:
                break
            self.main_phase()
        if "Jace's Archivist" in self.perms and "Jace's Archivist" not in self.sick \
                and self.wheel_ok("max") and self.can_pay({"U": 1}):
            self.outlet_loop()
            self.pay({"U": 1})
            self.do_wheel("max")
            self.outlet_loop()
            self.main_phase()
        if self.doom_instances():
            for c in [c for c in self.hand if c in CARDS and CARDS[c]["tags"] & {"loot2", "inquiry"}]:
                n_me, n_opp = (3, 3) if "inquiry" in CARDS[c]["tags"] else (2, 0)
                if c in self.hand and self.draws_safe(n_me, n_opp) and self.can_pay(CARDS[c]["cost"], reserve=self.reserve_cost()):
                    self.pay(CARDS[c]["cost"])
                    self.hand.remove(c)
                    self.gy.append(c)
                    self.spell_cast()
                    self.resolve_spell(c)
                    self.outlet_loop()
        self.trade_routes_bounce()
        self.taskmaster_copy()
        self.main_phase()
        if (self.doom_bf or self.copies) and "Loki, God of Mischief" in self.perms and self.draws_safe(1):
            self.draw(1)
        if self.doom_bf or self.copies:
            if "Irma, Part-Time Mutant" in self.perms and "Irma, Part-Time Mutant" not in self.sick:
                self.irma_is_doom = True
            if self.draws_safe(1):
                self.draw(1)
            am = self.ammo()
            if am:
                self.discard([am[0]])
            elif self.hand:
                self.discard_best(1)
            if self.class_level >= 1 and self.hand and self.draws_safe(1):
                self.discard_best(1)
                self.draw(1)
        self.laser_attack()
        self.norman_attack()
        self.goblin_attack()
        self.frog_attack()
        self.outlet_loop()
        self.finish_land_drop()
        self.main_phase()
        self.outlet_loop()
        if len(self.hand) > 7 and "Library of Leng" not in self.perms:
            extra = len(self.hand) - 7
            lands = [c for c in self.hand if c in LANDS]
            pick = (lands + sorted([c for c in self.hand if c not in LANDS], key=self.spell_value))[:extra]
            self.discard(pick)
        self.held = self.all_sources()
        if self.boots_on_doom:
            self.stats["boots_used"] = True
        if self.stats["engine"] is None and self.doom_instances() and self.engine_outlet() \
                and len(self.lands) + sum(1 for c in self.perms if "rock" in CARDS[c]["tags"]) >= 5:
            self.stats["engine"] = self.turn

    def engine_outlet(self):
        return (self.has("outlet_free") or self.has("seismic") or self.has("tectonic") or self.has("trade")
                or self.class_level >= 2)

    # ---------------- opponents ----------------
    def can_counter(self, kind):
        counters = [c for c in self.hand if c in CARDS and "counter" in CARDS[c]["tags"]]
        if kind == "removal" and self.rng.random() > 0.8:
            counters = [c for c in counters if c not in ("Swan Song", "Muddle the Mixture")]
        for c in sorted(counters, key=lambda c: sum(CARDS[c]["cost"].values())):
            a = self._alloc(CARDS[c]["cost"], self.held, False)
            if a is not None and c == "Perplex" and self.rng.random() < 0.4:
                self.held = [s for i, s in enumerate(self.held) if i not in a]
                self.hand.remove(c)
                self.gy.append(c)
                return False
            if a is not None:
                self.held = [s for i, s in enumerate(self.held) if i not in a]
                self.hand.remove(c)
                self.gy.append(c)
                return True
        return False

    def plaza_save(self):
        for i, s in enumerate(self.held):
            if s.get("plaza"):
                rest = self.held[:i] + self.held[i + 1:]
                a = self._alloc({"g": 3}, rest, False)
                if a is not None:
                    self.held = [s2 for j, s2 in enumerate(rest) if j not in a]
                    for l in self.lands:
                        if l.get("plaza"):
                            self.lands.remove(l)
                            break
                    return True
        return False

    def opponents_turns(self):
        for i in range(3):
            if self.opp[i] <= 0:
                continue
            plays = self.rng.choice([0, 1, 1, 2])
            self.opp_hand[i] = max(0, self.opp_hand[i] + 1 - plays)
            if self.has("mine"):
                self.opp_draw(i, self.count("mine"), extra_only=True)
            if REAL_HANDS and self.turn <= 5:
                self.opp_hand[i] = max(0, self.opp_hand[i] - self.rng.choice([0, 1]))
            if plays >= 2 and "Ledger Shredder" in self.perms and (self.doom_instances() or self.class_level >= 2):
                self.connive()
            if self.turn >= 2 and self.rng.random() < 0.6:
                self.opp_board[i].append(self.rng.choice([1, 1, 2, 2, 3, 3, 4, 5]))
            if self.turn < 3:
                continue
            r = self.rng.random()
            if r < self.p["wipe"] and self.turn >= 4:
                if self.creatures() or self.doom_instances():
                    if self.can_counter("wipe"):
                        self.stats["removal_stopped"] += 1
                        continue
                    self.stats["wipes"] += 1
                    if self.doom_bf:
                        self.stats["doom_removed"] += 1
                    self.doom_bf = False
                    self.goblin_counters = 0
                    self.frog_counters = 0
                    self.boots_on_doom = False
                    self.copies = 0
                    self.irma_is_doom = False
                    self.cipher = False
                    self.army = 0
                    for c in self.creatures():
                        self.perms.remove(c)
                        self.gy.append(c)
                    self.copy_cards = []
            elif r < self.p["wipe"] + self.p["removal"]:
                self.targeted_removal()

    def eot_trade_routes(self):
        if not (EOT_TRADE and self.has("trade") and (self.doom_instances() or self.class_level >= 2)):
            return
        guard = 0
        while guard < 10 and self.held and self.draws_safe(1):
            guard += 1
            am = self.ammo()
            if not am:
                break
            a = self._alloc({"g": 1}, self.held, False)
            if a is None:
                break
            self.held = [x for i, x in enumerate(self.held) if i not in a]
            self.discard([am[0]])
            self.draw(1)

    def targeted_removal(self):
        target = None
        if self.doom_bf and not self.boots_on_doom:
            target = "doom"
        elif self.copy_cards:
            target = self.copy_cards[0]
        else:
            for key in ("Notion Thief", "Glint-Horn Buccaneer", *([self.NORMAN] if self.cipher else []), "Living Laser",
                        "Psychic Frog", "Doom Variant", "Archfiend of Ifnir", "Psychosis Crawler",
                        "Orcish Bowmasters", "Tinybones, Pocket Nuisance"):
                if key in self.perms:
                    target = key
                    break
        if target is None:
            return
        important = target == "doom" or target in self.copy_cards or target in ("Notion Thief", "Psychic Frog")
        if important and self.can_counter("removal"):
            self.stats["removal_stopped"] += 1
            return
        if target == "doom" and self.plaza_save():
            self.stats["removal_stopped"] += 1
            return
        if target == "doom":
            self.doom_bf = False
            self.stats["doom_removed"] += 1
        else:
            if target in self.perms:
                self.perms.remove(target)
                self.gy.append(target)
                if target == "Psychic Frog":
                    self.frog_counters = 0
            if target == self.NORMAN:
                self.cipher = False
            if target in self.copy_cards:
                self.copy_cards.remove(target)
                self.copies -= 1

    def run(self, max_turns=16):
        try:
            for _ in range(max_turns):
                self.my_turn()
                self.opponents_turns()
                self.eot_trade_routes()
        except Won as w:
            self.stats["win"] = self.turn
            self.stats["how"] = w.how
        except Lost:
            self.stats["how"] = "decked"
        return self.stats


PROFILES = {
    "bracket3": {"removal": 0.08, "wipe": 0.03, "counter_doom": 0.03},
    "bracket4": {"removal": 0.15, "wipe": 0.05, "counter_doom": 0.10},
}
