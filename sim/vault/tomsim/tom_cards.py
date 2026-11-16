"""Card data for Tom's Bombs (Tom Bombadil) simulator.

cost: generic 'g' + pips W U B R G.
Sagas: chapters list of effects; effect tuples:
  ("token", power, kind)       kind: fly / menace / ground / hexfly / haste_fly_smaug / trample
  ("remove", n)                remove n opponent threats/blockers (spot removal / exile)
  ("draw", n) ("mill", n) ("ramp", n) ("treasure", n) ("copytoken", 1) ("gain", n)
  ("dmg_mv",)                  Bahamut IV: damage = total MV of other permanents to each opponent
  ("drain_gy",)                One Ring to Rule Them All III
  ("wipe_nonleg",)             destroy all nonlegendary creatures (mine too)
  ("tapall",)                  opponents can't block next turn
  ("cheat2",)                  World Spell III: put 2 permanents from hand onto battlefield
  ("dig",)                     look at 7, take a non-Saga permanent
  ("lands_back",)              Titan II
  ("odin",)                    Primal Odin II: combat damage makes that player lose
  ("tutor01",)                 Urza's Saga III
  ("return_hand",)             Aesir III: Saga back to hand
  ("transform",)               Kami War III: becomes 6/6 flying dragon
  ("anthem", n)                creatures get +n/+n this turn
"""


def C(g=0, W=0, U=0, B=0, R=0, G=0):
    return {"g": g, "W": W, "U": U, "B": B, "R": R, "G": G}


ANY = {"W", "U", "B", "R", "G"}

# lands: (colors, enters_tapped, extra)
LANDS = {
    "Plains": ({"W"}, False, {"basic": True}),
    "Island": ({"U"}, False, {"basic": True}),
    "Swamp": ({"B"}, False, {"basic": True}),
    "Mountain": ({"R"}, False, {"basic": True}),
    "Forest": ({"G"}, False, {"basic": True}),
    "Command Tower": (ANY, False, {}),
    "Underground Sea": ({"U", "B"}, False, {}),
    "Nesting Grounds": ({"C"}, False, {"nesting": True}),
    "Plaza of Harmony": (ANY, False, {"plaza": True}),
    "The World Tree": ({"G"}, True, {"worldtree": True}),
    "Maze's End": ({"C"}, True, {"gate_mazes": True}),
    "Urza's Saga": ({"C"}, False, {"urza": True}),
    "Thran Portal": (ANY, False, {"gate": True, "thran": True}),
    "Gateway Plaza": (ANY, True, {"gate": True}),
    "Gond Gate": (ANY, True, {"gate": True, "gond": True}),
    "Baldur's Gate": (ANY, True, {"gate": True}),
    "Basilisk Gate": ({"C"}, False, {"gate": True}),
    "Black Dragon Gate": ({"B"}, True, {"gate": True}),
    "Citadel Gate": ({"W"}, True, {"gate": True}),
    "Cliffgate": ({"R"}, True, {"gate": True}),
    "Heap Gate": ({"C"}, True, {"gate": True}),
    "Manor Gate": ({"W", "B"}, True, {"gate": True}),
    "Sea Gate": ({"U"}, True, {"gate": True}),
    "Azorius Guildgate": ({"W", "U"}, True, {"gate": True}),
    "Boros Guildgate": ({"R", "W"}, True, {"gate": True}),
    "Dimir Guildgate": ({"U", "B"}, True, {"gate": True}),
    "Golgari Guildgate": ({"B", "G"}, True, {"gate": True}),
    "Gruul Guildgate": ({"R", "G"}, True, {"gate": True}),
    "Izzet Guildgate": ({"U", "R"}, True, {"gate": True}),
    "Orzhov Guildgate": ({"W", "B"}, True, {"gate": True}),
    "Rakdos Guildgate": ({"B", "R"}, True, {"gate": True}),
    "Selesnya Guildgate": ({"G", "W"}, True, {"gate": True}),
    "Simic Guildgate": ({"G", "U"}, True, {"gate": True}),
    # upgrade candidates
    "Mana Confluence": (ANY, False, {}),
    "City of Brass": (ANY, False, {}),
    "Reflecting Pool": (ANY, False, {"pool": True}),
    "Exotic Orchard": (ANY, False, {}),
    "Path of Ancestry": (ANY, True, {}),
    "Arcane Lighthouse": ({"C"}, False, {}),
}

SAGAS = {
    # ---- Star Trek (TRK) Sagas ----
    "Year of Hell": dict(cost=C(1, U=1, R=1), ch=[[("draw", 1), ("lose2",)]] * 3),
    "The Wrath of Khan": dict(cost=C(2, R=1), ch=[[("remove", 1)], [("draw", 1)], [("remove", 1)]]),
    "In the Pale Moonlight": dict(cost=C(3, B=2), ch=[[("remove", 1)], [("draw", 1)], [("token", 2, "ground"), ("token", 2, "ground")]]),
    "The City on the Edge of Forever": dict(cost=C(3, W=1, B=1), ch=[[("token", 0, "ground")], [("draw", 2), ("lose2",)], [("gain", 5)]]),
    "All Good Things...": dict(cost=C(3, G=1, U=1), ch=[[("draw", 1)], [("draw", 1)], [("draw", 1)], [("gain", 10)]]),
    "Those Old Scientists": dict(cost=C(2, U=1), ch=[[("draw", 0)], [("draw", 1)], [("gain", 0)]]),
    # back face of Terra, Magical Adept (never cast; entered via Trance)
    "Esper Terra": dict(cost=C(1, R=1, G=1), ch=[[("terra_copy",)], [("terra_copy",)], [("terra_copy",)], [("terra_mana",), ("terra_flip",)]]),
    "Battle at the Helvault": dict(cost=C(4, W=2), ch=[[("remove", 3)], [("remove", 3)], [("token", 8, "fly")]]),
    "Binding the Old Gods": dict(cost=C(2, B=1, G=1), ch=[[("remove", 1)], [("ramp", 1)], [("anthem", 0)]]),
    "In the Darkness Bind Them": dict(cost=C(2, U=1, B=1, R=1), ch=[[("token", 3, "menace")]] * 3 + [[("tapall",)]]),
    "Kiora Bests the Sea God": dict(cost=C(5, U=2), ch=[[("token", 8, "hexfly")], [("tapall",)], [("remove", 1)]]),
    "One Ring to Rule Them All": dict(cost=C(2, B=2), ch=[[("mill", 3)], [("wipe_nonleg",)], [("drain_gy",)]]),
    "The Aesir Escape Valhalla": dict(cost=C(2, G=1), ch=[[("gain", 4)], [("anthem", 0)], [("return_hand",)]]),
    "The Horus Heresy": dict(cost=C(3, U=1, B=1, R=1), ch=[[("remove", 3)], [("draw", 3)], [("remove", 2)]]),
    "The Kami War": dict(cost=C(1, W=1, U=1, B=1, R=1, G=1), ch=[[("remove", 1)], [("remove", 1)], [("transform",)]]),
    "The World Spell": dict(cost=C(5, G=2), ch=[[("dig",)], [("dig",)], [("cheat2",)]], read_ahead=True),
    "There and Back Again": dict(cost=C(3, R=2), ch=[[("tapall_one",)], [("ramp", 1)], [("token", 6, "smaug")]]),
    "Three Blind Mice": dict(cost=C(2, W=1), ch=[[("token", 1, "ground")], [("copytoken", 1)], [("copytoken", 1)], [("anthem", 1)]]),
    "City of Death": dict(cost=C(2, G=1), ch=[[("treasure", 1)]] + [[("copytoken", 1)]] * 5),
    "Firja's Retribution": dict(cost=C(1, W=2, B=1), ch=[[("token", 4, "fly")], [("remove", 1)], [("anthem", 0)]]),
    "Summon: Bahamut": dict(cost=C(9), ch=[[("remove", 1)], [("remove", 1)], [("draw", 2)], [("dmg_mv",)]], creature=(9, "fly")),
    "Summon: Knights of Round": dict(cost=C(6, W=2), ch=[[("token", 2, "ground"), ("token", 2, "ground"), ("token", 2, "ground")]] * 4 + [[("anthem", 2)]], creature=(3, "ground")),
    "Summon: Primal Odin": dict(cost=C(4, B=2), ch=[[("remove", 1)], [("odin",)], [("draw", 2)]], creature=(5, "ground")),
    "Summon: Titan": dict(cost=C(3, G=2), ch=[[("mill", 5)], [("lands_back",)], [("anthem", 0)]], creature=(7, "trample")),
}

# other spells/permanents; tags drive the pilot
OTHER = {
    "Tom Bombadil": dict(cost=C(0, W=1, U=1, B=1, R=1, G=1), type="creature", tags={"tom"}, power=4),
    "All Will Be One": dict(cost=C(3, R=2), type="enchantment", tags={"awbo"}),
    "Helix Pinnacle": dict(cost=C(0, G=1), type="enchantment", tags={"helix"}),
    "Clockspinning": dict(cost=C(0, U=1), type="instant", tags={"clock"}),
    "Freed from the Real": dict(cost=C(2, U=1), type="aura", tags={"untapaura"}),
    "Pemmin's Aura": dict(cost=C(1, U=2), type="aura", tags={"untapaura"}),
    "Bloom Tender": dict(cost=C(1, G=1), type="creature", tags={"dork", "bloom"}, power=1),
    "Faeburrow Elder": dict(cost=C(1, G=1, W=1), type="creature", tags={"dork", "bloom"}, power=2),
    "Sage of the Maze": dict(cost=C(2, G=1), type="creature", tags={"dork", "sage"}, power=1),
    "Sanctum Weaver": dict(cost=C(1, G=1), type="creature", tags={"dork", "weaver"}, ench=True, power=0),
    "Delighted Halfling": dict(cost=C(0, G=1), type="creature", tags={"dork1"}, power=1),
    "Gatecreeper Vine": dict(cost=C(1, G=1), type="creature", tags={"vine"}, power=1),
    "Evolution Sage": dict(cost=C(2, G=1), type="creature", tags={"evosage"}, power=3),
    "Satsuki, the Living Lore": dict(cost=C(0, G=1, W=1), type="creature", tags={"satsuki"}, power=1),
    "Garnet, Princess of Alexandria": dict(cost=C(0, G=1, W=1), type="creature", tags=set(), power=2),
    "Narci, Fable Singer": dict(cost=C(1, W=1, B=1, G=1), type="creature", tags={"narci"}, power=3),
    "Weaver of Harmony": dict(cost=C(1, G=1), type="creature", tags={"harmony"}, ench=True, power=2),
    "Jukai Naturalist": dict(cost=C(0, G=1, W=1), type="creature", tags={"jukai"}, ench=True, power=2),
    "Eidolon of Blossoms": dict(cost=C(2, G=2), type="creature", tags={"eidolon"}, ench=True, power=2),
    "Sythis, Harvest's Hand": dict(cost=C(0, G=1, W=1), type="creature", tags={"sythis"}, ench=True, power=1),
    "Archon of Sun's Grace": dict(cost=C(2, W=2), type="creature", tags={"archon"}, ench=True, power=3, fly=True),
    "Ondu Spiritdancer": dict(cost=C(4, W=1), type="creature", tags={"ondu"}, power=3),
    "Destiny Spinner": dict(cost=C(1, G=1), type="creature", tags={"spinner"}, ench=True, power=2),
    "Goldberry, River-Daughter": dict(cost=C(1, U=2), type="creature", tags={"goldberry"}, power=1),
    "O'aka, Traveling Merchant": dict(cost=C(1, U=1), type="creature", tags={"oaka"}, power=1),
    "Xavier Sal, Infested Captain": dict(cost=C(0, B=1, G=1, U=1), type="creature", tags={"xavier"}, power=3),
    "Zur, Eternal Schemer": dict(cost=C(0, W=1, U=1, B=1), type="creature", tags={"zur"}, power=1),
    "Terra, Magical Adept": dict(cost=C(1, R=1, G=1), type="creature", tags={"terra"}, power=4),
    "Hex Parasite": dict(cost=C(1), type="creature", tags=set(), power=1),
    "Enchantress's Presence": dict(cost=C(2, G=1), type="enchantment", tags={"presence"}),
    "Historian's Boon": dict(cost=C(3, W=1), type="enchantment", tags={"boon"}),
    "Walking Ballista": dict(cost=C(0), type="artifact", tags={"ballista"}),   # X creature; only modeled as an infinite-mana outlet
    "Return of the Mole Man": dict(cost=C(1, G=1), type="enchantment", tags={"moleman"}),
    "Mirrormade": dict(cost=C(1, U=2), type="enchantment", tags={"mirrormade"}),
    "Spelunking": dict(cost=C(2, G=1), type="enchantment", tags={"spelunking"}),
    "Prismatic Omen": dict(cost=C(1, G=1), type="enchantment", tags={"omen"}),
    "Mystic Remora": dict(cost=C(0, U=1), type="enchantment", tags={"remora"}),
    "Sterling Grove": dict(cost=C(0, G=1, W=1), type="enchantment", tags={"grove"}),
    "Power Conduit": dict(cost=C(2), type="artifact", tags=set()),
    "Amulet of Vigor": dict(cost=C(1), type="artifact", tags={"amulet"}),
    "Arcane Signet": dict(cost=C(2), type="artifact", tags={"rock"}, prod=ANY),
    "Sol Ring": dict(cost=C(1), type="artifact", tags={"rock"}, prod="CC"),
    "Chromatic Lantern": dict(cost=C(3), type="artifact", tags={"rock", "lantern"}, prod=ANY),
    "Lightning Greaves": dict(cost=C(2), type="artifact", tags={"greaves"}),
    "The One Ring": dict(cost=C(4), type="artifact", tags={"ring"}),
    "Demonic Tutor": dict(cost=C(1, B=1), type="sorcery", tags={"tutor"}),
    "Crop Rotation": dict(cost=C(0, G=1), type="instant", tags={"croprot"}),
    "Sylvan Scrying": dict(cost=C(1, G=1), type="sorcery", tags={"landtutor"}),
    "Explore the Underdark": dict(cost=C(4, G=2), type="sorcery", tags={"explore"}),
    "Counterspell": dict(cost=C(0, U=2), type="instant", tags={"counter"}),
    "Eerie Ultimatum": dict(cost=C(0, W=2, B=3, G=2), type="sorcery", tags={"eerie"}),
    # upgrade candidates
    "Umbral Mantle": dict(cost=C(3), type="artifact", tags={"mantle"}),
    "Staff of Domination": dict(cost=C(3), type="artifact", tags={"staff"}),
    "Isochron Scepter": dict(cost=C(2), type="artifact", tags={"scepter"}),
    "Dramatic Reversal": dict(cost=C(1, U=1), type="instant", tags={"reversal"}),
    "Idyllic Tutor": dict(cost=C(2, W=1), type="sorcery", tags={"enchtutor"}),
    "Plea for Guidance": dict(cost=C(3, W=2), type="sorcery", tags={"enchtutor2"}),
    "Finale of Devastation": dict(cost=C(0, G=2), type="sorcery", tags={"finale"}),   # X=2-3 creature to battlefield
    "Green Sun's Zenith": dict(cost=C(1, G=1), type="sorcery", tags={"gsz"}),
    "Eladamri's Call": dict(cost=C(0, G=1, W=1), type="instant", tags={"creaturetutor"}),
    "Dimir Machinations": dict(cost=C(2, B=1), type="sorcery", tags={"trans3"}),
    "Perplex": dict(cost=C(1, U=1, B=1), type="instant", tags={"trans3", "counter"}),
    "Muddle the Mixture": dict(cost=C(0, U=2), type="instant", tags={"trans2", "counter"}),
    "Shred Memory": dict(cost=C(1, B=1), type="instant", tags={"trans2"}),
    "Merchant Scroll": dict(cost=C(1, U=1), type="sorcery", tags={"scroll"}),
    "Personal Tutor": dict(cost=C(0, U=1), type="sorcery", tags={"ptutor"}),
    "Enlightened Tutor": dict(cost=C(0, W=1), type="instant", tags={"etutor"}),
    "Mystical Tutor": dict(cost=C(0, U=1), type="instant", tags={"mtutor"}),
    "Worldly Tutor": dict(cost=C(0, G=1), type="instant", tags={"wtutor"}),
    "Gamble": dict(cost=C(0, R=1), type="sorcery", tags={"tutor", "gamble"}),
    "Grim Tutor": dict(cost=C(1, B=2), type="sorcery", tags={"tutor"}),
    "Diabolic Intent": dict(cost=C(1, B=1), type="sorcery", tags={"tutor"}),
    "Academy Rector": dict(cost=C(3, W=1), type="creature", tags=set(), power=1),
    "Doubling Season": dict(cost=C(4, G=1), type="enchantment", tags={"doubling"}),
    "Smothering Tithe": dict(cost=C(3, W=1), type="enchantment", tags={"tithe"}),
    "Rhystic Study": dict(cost=C(2, U=1), type="enchantment", tags={"rhystic"}),
    "Setessan Champion": dict(cost=C(2, G=1), type="creature", tags={"eidolon"}, power=1),
    "Argothian Enchantress": dict(cost=C(1, G=1), type="creature", tags={"eidolon"}, ench=True, power=0),
    "Satyr Enchanter": dict(cost=C(1, G=1, W=1), type="creature", tags={"sythis"}, power=2),
    "Utopia Sprawl": dict(cost=C(0, G=1), type="aura", tags={"sprawl"}),
    "Wild Growth": dict(cost=C(0, G=1), type="aura", tags={"sprawl"}),
    "Birds of Paradise": dict(cost=C(0, G=1), type="creature", tags={"dork1"}, power=0),
    "Mana Vault": dict(cost=C(1), type="artifact", tags={"burst3"}),
    "Grim Monolith": dict(cost=C(2), type="artifact", tags={"burst3"}),
    "Ancient Tomb": None,
    "BLANK": dict(cost=C(99), type="sorcery", tags=set()),
    "Scepter+Reversal": dict(cost=C(99), type="artifact", tags={"scepter_reversal"}),
}
OTHER.pop("Ancient Tomb")

GAME_CHANGERS = {"Demonic Tutor", "The One Ring", "Crop Rotation", "Enlightened Tutor", "Mystical Tutor", "Worldly Tutor",
                 "Gamble", "Smothering Tithe", "Rhystic Study", "Mana Vault", "Grim Monolith"}
