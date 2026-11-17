"""Solitaire kill-turn sim for the Lawyer deck (Kynaios and Tiro). Win routes: Felidar Sovereign (40+ life at upkeep),
Azor's Elocutors (5 upkeeps), Approach of the Second Sun (cast twice from hand). Opponents: removal/wipes/counter rolls like tomsim."""
import json, random, csv, gzip, sys
csv.field_size_limit(10**9)
D = json.load(open('deck.json')); D = D.get('data', D)
deck = [c['name'] for c in D['cards'] for _ in range(c.get('qty', 1))]
want = set(deck)
R = {}
for r in csv.DictReader(gzip.open(__import__('os').environ.get('CARDS_CSV','cards.csv.gz'), 'rt')):
    if r['name'] in want and r['name'] not in R:
        R[r['name']] = r
LAND = {}
for n, r in R.items():
    if 'Land' in r['type_line']:
        ci = set(r['color_identity']) & set('WUBRG')   # color_identity is letters ('GW') in the repo CSV
        o = r['oracle_text']
        tapped = ('enters tapped' in o or 'enters the battlefield tapped' in o) and 'unless' not in o
        if 'Basic' in r['type_line']:
            ci = {{'Plains': 'W', 'Island': 'U', 'Mountain': 'R', 'Forest': 'G'}[n]}
        if n in ('Command Tower', 'Exotic Orchard', 'Fabled Passage', 'Plaza of Heroes'):
            ci = set('WURG')
        if not ci:
            ci = {'C'}
        LAND[n] = (ci, tapped)
LAND['Fabled Passage'] = (set('WURG'), False)
LAND['Cascade Bluffs'] = (set('UR'), False)
COST = {  # generic, pips (hybrid as frozenset-string in list)
 'Felidar Sovereign': (4, ['W', 'W']), "Azor's Elocutors": (3, ['WU', 'WU']), 'Approach of the Second Sun': (6, ['W']),
 'Kynaios and Tiro of Meletis': (0, ['R', 'G', 'W', 'U']), 'Sol Ring': (1, []), 'Azorius Signet': (2, []),
 'Talisman of Conviction': (2, []), 'Chromatic Lantern': (3, []), 'Birds of Paradise': (0, ['G']),
 'Faeburrow Elder': (1, ['G', 'W']), 'Cultivate': (2, ['G']), 'Stock Up': (2, ['U']), 'Fact or Fiction': (3, ['U']),
}
ROCK = {'Sol Ring': ('CC', 2), 'Azorius Signet': ('WU', 1), 'Talisman of Conviction': ('CRW', 1), 'Chromatic Lantern': ('WURG', 1),
        'Birds of Paradise': ('WURG', 1), 'Faeburrow Elder': ('GW', 1)}
DORK = {'Birds of Paradise', 'Faeburrow Elder'}
PROF = {'bracket3': dict(removal=.08, wipe=.03, disrupt=.15), 'bracket4': dict(removal=.15, wipe=.05, disrupt=.30)}


class Game:
    def __init__(self, prof, rng):
        self.p, self.rng = prof, rng
        self.lib = list(deck); rng.shuffle(self.lib)
        self.hand = []; self.lands = []; self.rocks = []; self.cre = {}; self.turn = 0; self.life = 40
        self.on_play = rng.random() < .25
        self.kyn = 'cz'; self.tax = 0; self.elo = 0; self.apr = 0; self.won = None
        for a in range(4):
            if a:
                self.lib += self.hand; self.hand = []; rng.shuffle(self.lib)
            self.hand = [self.lib.pop() for _ in range(7)]
            nl = sum(c in LAND for c in self.hand)
            if 3 <= nl <= 5 or a == 3:
                for _ in range(max(0, a - 1)):
                    ls = [c for c in self.hand if c in LAND]; sp = [c for c in self.hand if c not in LAND]
                    k = ls[-1] if len(ls) > 4 or not sp else sp[-1]
                    self.hand.remove(k); self.lib.insert(0, k)
                break

    def draw(self, n=1):
        for _ in range(n):
            if self.lib: self.hand.append(self.lib.pop())

    def land_drop(self, tappedok=True):
        ls = [c for c in self.hand if c in LAND]
        if not ls: return False
        ls.sort(key=lambda l: (LAND[l][1], -len(LAND[l][0])))
        c = ls[0]; self.hand.remove(c)
        if c == 'Fabled Passage':
            b = [x for x in self.lib if x in ('Plains', 'Island', 'Forest', 'Mountain')]
            if b:
                self.lib.remove(b[0]); self.rng.shuffle(self.lib); c = b[0]
        self.lands.append(dict(n=c, cols=set(LAND[c][0]), tapped=LAND[c][1] and len(self.lands) < 3 or (LAND[c][1] and LAND[c][1])))
        return True

    def sources(self):
        lant = 'Chromatic Lantern' in [r['n'] for r in self.rocks]
        s = []
        for l in self.lands:
            if not l['tapped']:
                s.append(set('WURG') if lant else l['cols'])
        for r in self.rocks:
            if r['sick']: continue
            cols, n = ROCK[r['n']]
            for _ in range(n): s.append(set(cols))
        return s

    def alloc(self, name):
        g, pips = COST[name]
        srcs = self.sources(); used = []
        def bt(k):
            if k == len(pips): return True
            for i, c in enumerate(srcs):
                if i in used: continue
                if any(p in c for p in pips[k]):
                    used.append(i)
                    if bt(k + 1): return True
                    used.pop()
            return False
        if not bt(0): return None
        rest = [i for i in range(len(srcs)) if i not in used]
        if len(rest) < g + (self.tax if name.startswith('Kynaios') else 0): return None
        return used + rest[:g + (self.tax if name.startswith('Kynaios') else 0)]

    def pay(self, name):
        a = self.alloc(name)
        if a is None: return False
        # tap: remove matching sources (approx: remove lands first then rocks)
        srcs = self.sources(); need = len(a)
        order = [('l', l) for l in self.lands if not l['tapped']] + [('r', r) for r in self.rocks if not r['sick']]
        # rebuild mapping: each source corresponds in same order as sources(); rocks may give 2
        idx = 0; items = []
        for l in self.lands:
            if not l['tapped']: items.append(('l', l))
        for r in self.rocks:
            if r['sick']: continue
            for _ in range(ROCK[r['n']][1]): items.append(('r', r))
        for i in sorted(a):
            k, o = items[i]
            if k == 'l': o['tapped'] = True
            else: o['used'] = o.get('used', 0) + 1
        for r in self.rocks:
            if r.get('used', 0) >= ROCK[r['n']][1]: r['sick'] = True; r['used'] = 0
        return True

    def mana(self): return len(self.sources())

    def counter_roll(self, factor=1.0):
        return self.rng.random() < self.p['disrupt'] * factor

    def cast(self, c):
        if c in ROCK and c not in DORK:
            self.rocks.append(dict(n=c, sick=c != 'Sol Ring' and True))
            if c == 'Sol Ring': self.rocks[-1]['sick'] = False
            return
        if c in DORK:
            self.rocks.append(dict(n=c, sick=True)); self.cre[c] = self.turn; return
        if c == 'Cultivate':
            b = [x for x in self.lib if x in ('Plains', 'Island', 'Forest', 'Mountain')]
            if b:
                x = b[0]; self.lib.remove(x); self.lands.append(dict(n=x, cols=set(LAND[x][0]), tapped=True))
                y = [z for z in self.lib if z in ('Plains', 'Island', 'Forest', 'Mountain') and z != x] or b[1:2]
                if y: self.lib.remove(y[0]); self.hand.append(y[0])
                self.rng.shuffle(self.lib)
            return
        if c in ('Stock Up',): self.draw(2); return
        if c == 'Fact or Fiction': self.draw(2); return
        if c == 'Kynaios and Tiro of Meletis':
            self.kyn = 'bf'; self.tax += 2; return
        if c == 'Felidar Sovereign':
            if not self.counter_roll(.5): self.cre[c] = self.turn
            return
        if c == "Azor's Elocutors":
            if not self.counter_roll(.5): self.cre[c] = self.turn; self.elo = 0
            return
        if c == 'Approach of the Second Sun':
            if self.counter_roll(1.0): return
            if self.apr:
                self.won = self.turn; return
            self.apr = 1; self.life += 7
            self.lib.insert(max(0, len(self.lib) - 7), c)
            return

    def my_turn(self):
        self.turn += 1
        # upkeep wins
        if 'Felidar Sovereign' in self.cre and self.cre['Felidar Sovereign'] < self.turn and self.life >= 40:
            self.won = self.turn; return
        if "Azor's Elocutors" in self.cre and self.cre["Azor's Elocutors"] < self.turn:
            self.elo += 1
            if self.elo >= 5: self.won = self.turn; return
        if not (self.turn == 1 and self.on_play): self.draw(1)
        for r in self.rocks: r['sick'] = False if r['n'] not in DORK or self.cre.get(r['n'], 99) < self.turn else True
        for l in self.lands: l['tapped'] = False
        self.land_drop()
        # fix lands entering tapped this turn
        # (treat tapped lands as unusable the turn they enter)
        new = self.lands[-1] if self.lands else None
        if new and LAND.get(new['n'], (0, False))[1] and not new.get('seen'): new['tapped'] = True
        for l in self.lands: l['seen'] = True
        guard = 0
        while guard < 30 and self.won is None:
            guard += 1
            order = ["Felidar Sovereign", "Azor's Elocutors", 'Approach of the Second Sun', 'Sol Ring', 'Azorius Signet', 'Talisman of Conviction', 'Chromatic Lantern',
                     'Birds of Paradise', 'Faeburrow Elder', 'Kynaios and Tiro of Meletis', 'Cultivate', 'Stock Up', 'Fact or Fiction']
            did = False
            for c in order:
                if c not in self.hand: continue
                if c == 'Felidar Sovereign' and 'Felidar Sovereign' in self.cre: continue
                if c == "Azor's Elocutors" and "Azor's Elocutors" in self.cre: continue
                if c == 'Kynaios and Tiro of Meletis' and self.kyn == 'bf': continue
                if c == 'Approach of the Second Sun' and self.mana() < 7: continue
                if self.alloc(c) is not None:
                    self.pay(c); self.hand.remove(c); self.cast(c); did = True; break
            if not did: break
            if self.won: return
        # Kynaios end step
        if self.kyn == 'bf':
            self.draw(1)
            if any(c in LAND for c in self.hand): self.land_drop()
        while len(self.hand) > 7:
            junk = sorted(self.hand, key=lambda c: (c not in LAND, c in COST))
            self.hand.remove(junk[0])

    def opponents(self):
        for i in range(3):
            if self.turn < 3: continue
            r = self.rng.random()
            if r < self.p['wipe'] and self.turn >= 4:
                for c in list(self.cre): del self.cre[c]
                self.rocks = [x for x in self.rocks if x['n'] not in DORK]
            elif r < self.p['wipe'] + self.p['removal']:
                tg = [c for c in self.cre if c in ('Felidar Sovereign', "Azor's Elocutors")]
                if tg and self.rng.random() < .75: del self.cre[tg[0]]
                elif self.cre:
                    c = next(iter(self.cre)); del self.cre[c]
                    self.rocks = [x for x in self.rocks if x['n'] != c]

    def run(self, T=16):
        for _ in range(T):
            self.my_turn()
            if self.won: return self.won
            self.opponents()
        return 99


def play(prof, N, seed=7_000_003):
    return [Game(PROF[prof], random.Random(seed * (k + 1))).run() for k in range(N)]

if __name__ == '__main__':
    N = int(sys.argv[1])
    for prof in PROF:
        w = play(prof, N)
        print(prof, {f'by{t}': round(sum(x <= t for x in w) / N, 3) for t in (6, 8, 10, 12, 16)})
