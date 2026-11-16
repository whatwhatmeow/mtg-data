import json, sys
from nm_run import *
b = load("deck.json")
five = [("Merrow Wavebreakers","Kindred Discovery"),("We Say Thee Nay!","Pongify"),("Aether Tradewinds","Rapid Hybridization"),
        ("Commander's Sphere","Herald's Horn"),("Write into Being","Swiftfoot Boots")]
V = {"BASE (vault list)": b}
for o,i in five:
    V[f"+{i} -{o}"] = swap(b,[(o,i)])
V["ALL FIVE planned adds"] = swap(b, five)
V["+Arcane Denial -Merrow Wavebreakers"] = swap(b,[("Merrow Wavebreakers","Arcane Denial")])
V["+Swan Song -Merrow Wavebreakers"] = swap(b,[("Merrow Wavebreakers","Swan Song")])
V["+Mana Leak -Merrow Wavebreakers"] = swap(b,[("Merrow Wavebreakers","Mana Leak")])
V["+Arcane Denial +Swan Song (-Wavebreakers -Peel)"] = swap(b,[("Merrow Wavebreakers","Arcane Denial"),("Peel from Reality","Swan Song")])
V["-3 counters (Nay, Fracture, Negate) +Melody +Piracy +Silvergill"] = swap(b,[("We Say Thee Nay!","Distant Melody"),("Dream Fracture","Coastal Piracy"),("Negate","Silvergill Adept")])
V["+Distant Melody -Dream Fracture"] = swap(b,[("Dream Fracture","Distant Melody")])
V["+Coastal Piracy -Dream Fracture"] = swap(b,[("Dream Fracture","Coastal Piracy")])
V["+Silvergill Adept -Merfolk Cave-Diver"] = swap(b,[("Merfolk Cave-Diver","Silvergill Adept")])
V["+Into the Roil -Aether Tradewinds"] = swap(b,[("Aether Tradewinds","Into the Roil")])
for d in V.values(): check(d)
prof = sys.argv[1]
rows = compare(V, prof, N=int(sys.argv[2]))
json.dump(rows, open(f"tests_{prof}.json","w"))
show(rows, prof)
