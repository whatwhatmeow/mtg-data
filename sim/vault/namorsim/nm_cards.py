"""Card data for the Namor the Sub-Mariner Merfolk simulator.

cost: generic part, u: blue pips. Creatures: p/t, merfolk flag, tags.
Spells: kind tags drive the AI. pips = blue mana symbols (Namor makes that many tokens).
"""
COMMANDER = "Namor the Sub-Mariner"   # {1}{U}{U} */4 flying, power = # Merfolk

LANDS = {
    "Island": dict(island=True),
    "Mystic Sanctuary": dict(island=True, cond_tapped="islands3"),
    "Fabled Passage": dict(fetch=True, untapped_if_4=True),
    "Terramorphic Expanse": dict(fetch=True),
    "Vibrant Cityscape": dict(fetch=True),
    "Baxter Building": dict(colorless=True, baxter=True),
    "Rogue's Passage": dict(colorless=True, rogue=True),
    "Castle Vantress": dict(island=False, cond_tapped="island1"),
}

C = {}
def cr(name, g, u, p, t, mf=True, *tags, flash=False):
    C[name] = dict(type="creature", kind="creature", cost=g, u=u, p=p, t=t, merfolk=mf, tags=set(tags), flash=flash)

def sp(name, g, u, kind, *tags, typ="sorcery", pips=None):
    C[name] = dict(type=typ, cost=g, u=u, kind=kind, tags=set(tags), pips=u if pips is None else pips)

# ---- Merfolk ----
cr("Atlantean Cavalry", 2, 1, 3, 2, True, "vigilance", "second_counter")
cr("Atlantean Skirmisher", 1, 1, 2, 1, True, "attack_connive")          # cost assumed
cr("Attuma, Atlantean Warlord", 2, 2, 3, 4, True, "lord", "attuma")
cr("Brineborn Cutthroat", 1, 1, 2, 1, True, "brineborn", flash=True)
cr("Daughter of the Deep", 1, 1, 2, 1, True, "daughter")
cr("Kopala, Warden of Waves", 1, 1, 2, 2, True, "kopala")
cr("Lord of Atlantis", 0, 2, 2, 2, True, "lord", "walk")
cr("Master of the Pearl Trident", 0, 2, 2, 2, True, "lord", "walk")
cr("Merfolk Cave-Diver", 1, 1, 2, 1, True)                               # explore payoff, no explore here
cr("Merfolk Looter", 1, 1, 1, 1, True, "looter")
cr("Merfolk Secretkeeper", 0, 1, 0, 4, True, "noattack")
cr("Merfolk Windrobber", 0, 1, 1, 1, True, "flying")
cr("Merrow Reejerey", 2, 1, 2, 2, True, "lord", "reejerey")
cr("Merrow Wavebreakers", 4, 1, 3, 3, True)
cr("Mist Dancer", 4, 1, 3, 3, True, "flying", "dancer")
cr("Mist-Cloaked Herald", 0, 1, 1, 1, True, "unblockable")
cr("Namor, Scourge of the Seas", 3, 2, 4, 4, True, "flying", "scourge")
cr("Namora, the Sea Queen", 2, 1, 2, 3, True, "flying", "namora")
cr("Prismwake Merrow", 2, 1, 2, 2, True, flash=True)
cr("Merrow Levitator", 3, 1, 2, 3, True)
cr("Merfolk Falconer", 1, 1, 2, 1, True)
cr("Tideshaper Mystic", 0, 1, 1, 1, True, "tideshaper")
cr("Shipwreck Patrol", 3, 1, 3, 3, True, "stun")
cr("Stonybrook Banneret", 1, 1, 1, 1, True, "banneret", "islandwalk")
cr("Svyelun of Sea and Sky", 1, 2, 3, 4, True, "svyelun")
cr("Harbinger of the Tides", 1, 2, 2, 2, True, "harbinger", flash=True)
cr("Merfolk Sovereign", 2, 1, 2, 2, True, "lord", "sovereign")
cr("Merfolk Wayfinder", 2, 1, 1, 2, True, "flying", "wayfinder")
cr("Scroll Thief", 2, 1, 1, 3, True, "hitdraw")
cr("Merfolk Skyscout", 2, 2, 2, 3, True, "flying")
cr("Silvergill Adept", 1, 1, 2, 1, True, "cantrip_etb")
cr("Coralhelm Commander", 1, 2, 2, 2, True)
cr("Seafloor Oracle", 2, 2, 2, 3, True, "hitdraw")
cr("Chasm Skulker", 2, 1, 1, 1, False, "skulker")
cr("Hullbreacher", 2, 1, 3, 2, False, flash=True)

# ---- Noncreature ----
sp("Aether Tradewinds", 2, 1, "bounce", typ="instant")
sp("Aetherize", 3, 1, "aetherize", typ="instant")                      # only vs attackers: dead here
sp("Archmage's Charm", 0, 3, "counter", "charm", typ="instant")
sp("Brainstorm", 0, 1, "brainstorm", typ="instant")
sp("Counterspell", 0, 2, "counter", typ="instant")
sp("Depower", 2, 1, "draw1", typ="instant")
sp("Dig Through Time", 6, 2, "dig", typ="instant")
sp("Dream Fracture", 1, 2, "counter", "fracture", typ="instant")
sp("Fact or Fiction", 3, 1, "fof", typ="instant")
sp("Harmonized Crescendo", 4, 2, "crescendo", typ="instant")
sp("High Tide", 0, 1, "hightide", typ="instant")
sp("Negate", 1, 1, "counter", typ="instant")
sp("Peel from Reality", 1, 1, "peel", typ="instant")
sp("Unstable Experiment", 1, 1, "unstable", typ="instant")
sp("We Say Thee Nay!", 1, 1, "counter", "soft", typ="instant")
sp("Whoosh!", 1, 1, "whoosh", typ="instant")
sp("Crashing Tide", 2, 1, "crashing", typ="sorcery")
sp("Atlantis Attacks", 5, 2, "leviathan")
sp("Extract Power", 5, 1, "extract")
sp("Fantastic Bounce", 3, 1, "bounce_draw")
sp("Here Comes a New Hero!", 2, 1, "newhero")
sp("Multiversal Incursion", 5, 2, "incursion")
sp("Pym Particles", 0, 1, "pym")
sp("Stock Up", 2, 1, "stockup")
sp("Write into Being", 2, 1, "manifest")
sp("Back to Basics", 2, 1, "b2b", typ="enchantment")
sp("Frozen in Ice", 2, 1, "freeze", typ="enchantment")
sp("Quantum Reduction", 1, 1, "shrink", typ="enchantment")
sp("Super Intelligence", 0, 1, "superint", typ="enchantment")
sp("Familiar's Ruse", 0, 2, "counter", "ruse", typ="instant")
sp("Bident of Thassa", 2, 1, "bident", typ="enchantment")
# artifacts (no blue pips)
sp("Sol Ring", 1, 0, "rock", "sol", typ="artifact")
sp("Arcane Signet", 2, 0, "rock", typ="artifact")
sp("Mind Stone", 2, 0, "rock", "cless", typ="artifact")
sp("Commander's Sphere", 3, 0, "rock", typ="artifact")
sp("Sky Diamond", 2, 0, "rock", "tapped", typ="artifact")
sp("Patchwork Banner", 3, 0, "rock", "banner", typ="artifact")
sp("Arcade Cabinet", 3, 0, "cabinet", typ="artifact")
sp("Idol of Oblivion", 2, 0, "idol", typ="artifact")
sp("Zephyr Boots", 1, 0, "boots", typ="artifact")
# candidates for testing
sp("Kindred Discovery", 3, 2, "kindred", typ="enchantment")
sp("Pongify", 0, 1, "kill", typ="instant")
sp("Rapid Hybridization", 0, 1, "kill", typ="instant")
sp("Herald's Horn", 3, 0, "horn", typ="artifact")
sp("Swiftfoot Boots", 2, 0, "swiftfoot", typ="artifact")
sp("Arcane Denial", 1, 1, "counter", typ="instant")
sp("Swan Song", 0, 1, "counter", typ="instant")
sp("Dismissive Denial", 2, 2, "counter", typ="instant")
sp("Mana Leak", 1, 1, "counter", "soft", typ="instant")
sp("Coastal Piracy", 2, 2, "piracy", typ="enchantment")
sp("Reconnaissance Mission", 2, 2, "piracy", typ="enchantment")
sp("Into the Roil", 1, 1, "whoosh", typ="instant")
sp("Distant Melody", 3, 1, "melody")
sp("Thought Vessel", 2, 0, "rock", "cless", typ="artifact")
sp("Fellwar Stone", 2, 0, "rock", typ="artifact")
# Nov 16, 2026: cards added to the vault list after v1
cr("Chrome Host Seedshark", 2, 1, 2, 4, False, "flying", "seedshark")   # incubate X on each noncreature spell
sp("Muddle the Mixture", 0, 2, "counter", typ="instant")               # instants/sorceries only; transmute not modeled
sp("Treasure Cruise", 7, 1, "cruise")                                  # delve, draw 3
sp("Timeline Inquiry", 3, 1, "inquiry", typ="instant")                 # draw 3; teamwork 2 skips the discard
sp("Thirst for Knowledge", 2, 1, "thirst", typ="instant")              # draw 3, discard an artifact or two cards
sp("Assassin Gauntlet", 2, 1, "gauntlet", typ="artifact")              # taps one opponent's team; +1/+1 and loot on hit
sp("BLANK", 99, 0, "blank")
cr(COMMANDER, 1, 2, 0, 4, True, "flying")
