"""Card data for the Winter Soldier, Icy Assassin voltron simulator (v2).

cost: generic 'g' plus W/B pips. Equipment fields:
  p, t      flat bonus to the equipped creature
  equip     equip cost; equip_leg = cost when attaching to a legendary creature
  kw        keywords: trample, first, double, deathtouch, hexproof, shroud, indestr,
            unblockable, haste, vigilance, lifelink
  pro       colors the equipped creature has protection from
  dyn       name of a dynamic bonus or trigger handled in the sim
  etb_attach  attaches to a creature when it enters
"""


def C(g=0, W=0, B=0):
    return {"g": g, "W": W, "B": B}


# ---------------- lands: (colors, enters_tapped, extra) ----------------
LANDS = {
    "Plains": ({"W"}, False, {"basic": True, "types": ("Plains",)}),
    "Swamp": ({"B"}, False, {"basic": True, "types": ("Swamp",)}),
    "Ancient Den": ({"W"}, False, {"artifact": True}),
    "Vault of Whispers": ({"B"}, False, {"artifact": True}),
    "Buried Ruin": ({"C"}, False, {"artifact": True}),
    "Goldmire Bridge": ({"W"}, True, {"artifact": True}),
    "Caves of Koilos": ({"W", "B"}, False, {}),
    "Command Tower": ({"W", "B"}, False, {}),
    "Fetid Heath": ({"W", "B"}, False, {"filter": True}),
    "Isolated Chapel": ({"W", "B"}, False, {"cond": ("Plains", "Swamp")}),
    "Shineshadow Snarl": ({"W", "B"}, False, {"cond": "reveal"}),
    "Tainted Field": ({"W", "B"}, False, {"tainted": True}),
    "Nesting Grounds": ({"C"}, False, {}),
    "Rogue's Passage": ({"C"}, False, {"passage": True}),
    "Vibrant Cityscape": ({"C"}, False, {"cityscape": True}),
    "Villainous Hideout": ({"C"}, False, {"villain": True}),
    # upgrade candidates
    "Godless Shrine": ({"W", "B"}, False, {"types": ("Plains", "Swamp"), "shock": True}),
    "Concealed Courtyard": ({"W", "B"}, False, {}),
    "Scoured Barrens": ({"W", "B"}, True, {}),
    "Silent Clearing": ({"W", "B"}, False, {}),
    "Brightclimb Pathway": ({"W", "B"}, False, {"pathway": True}),
    "Shattered Sanctum": ({"W", "B"}, False, {}),
    "Ancient Tomb": ({"C"}, False, {"tomb": True}),
    "Urza's Saga": ({"C"}, False, {"saga": True}),
    "Inventors' Fair": ({"C"}, False, {}),
    "Castle Ardenvale": ({"W"}, False, {}),
    "Castle Locthwain": ({"B"}, False, {}),
}

# ---------------- Equipment ----------------
EQUIP = {
    "Colossus Hammer": dict(cost=C(1), p=10, t=10, equip=C(8)),
    "Kaldra Compleat": dict(cost=C(7), p=5, t=5, equip=C(7), kw={"first", "trample", "indestr", "haste"}),
    "Umezawa's Jitte": dict(cost=C(2), equip=C(2), dyn="jitte"),
    "Sword of Fire and Ice": dict(cost=C(3), p=2, t=2, equip=C(2), dyn="sofi", pro={"R", "U"}),
    "Sword of Sinew and Steel": dict(cost=C(3), p=2, t=2, equip=C(2), pro={"B", "R"}),
    "Sword of Feast and Famine": dict(cost=C(3), p=2, t=2, equip=C(2), dyn="sofaf", pro={"B", "G"}),
    "Sword of Light and Shadow": dict(cost=C(3), p=2, t=2, equip=C(2), pro={"W", "B"}),
    "Sword of the Animist": dict(cost=C(2), p=1, t=1, equip=C(2), dyn="animist"),
    "Blackblade Reforged": dict(cost=C(2), equip=C(7), equip_leg=C(3), dyn="lands"),
    "Loxodon Warhammer": dict(cost=C(3), p=3, equip=C(3), kw={"trample", "lifelink"}),
    "Cranial Plating": dict(cost=C(2), equip=C(1), dyn="artifacts_p"),
    "Lashwrithe": dict(cost=C(4), equip=C(0, 0, 2), dyn="swamps"),
    "Nightmare Lash": dict(cost=C(4), equip=C(0), dyn="swamps", life_equip=3),
    "Nettlecyst": dict(cost=C(3), equip=C(2), dyn="art_ench"),
    "Vorpal Sword": dict(cost=C(0, 0, 1), p=2, equip=C(0, 0, 3), kw={"deathtouch"}, dyn="vorpal"),
    "Plate Armor": dict(cost=C(2), p=3, t=3, equip=C(3), dyn="plate"),
    "O-Naginata": dict(cost=C(1), p=3, equip=C(2), kw={"trample"}, need_power=3),
    "Bloodforged Battle-Axe": dict(cost=C(1), p=2, equip=C(2), dyn="axe"),
    "Conqueror's Flail": dict(cost=C(2), p=2, t=2, equip=C(2)),
    "Genji Glove": dict(cost=C(5), equip=C(3), kw={"double"}, dyn="genji"),
    "Captain America's Shield": dict(cost=C(2), t=8, equip=C(2), kw={"vigilance"}, dyn="shield"),
    "Stolen Stark Tech": dict(cost=C(1, 0, 1), p=1, equip=C(1), flash=True, etb_attach=True),
    "Wrecking Ball Arm": dict(cost=C(2), equip=C(7), equip_leg=C(3), dyn="wrecking"),
    "Swordsman's Steel": dict(cost=C(4), equip=C(3), dyn="steel"),
    "Adaptive Omnitool": dict(cost=C(2), equip=C(3), dyn="omnitool"),
    "My Precious": dict(cost=C(3), equip=C(2), life_equip=2, kw={"hexproof", "unblockable"}),
    "Champion's Helm": dict(cost=C(3), p=2, t=2, equip=C(1), kw={"hexproof"}),
    "Mask of Memory": dict(cost=C(2), equip=C(1), dyn="mask"),
    "Sai of the Shinobi": dict(cost=C(1), p=1, t=1, equip=C(2)),
    "Lightning Greaves": dict(cost=C(2), equip=C(0), kw={"shroud", "haste"}),
    "Swiftfoot Boots": dict(cost=C(2), equip=C(1), kw={"hexproof", "haste"}),
    "Bone Saw": dict(cost=C(0), p=1, equip=C(1)),
    # upgrade candidates
    "Commander's Plate": dict(cost=C(1), p=3, t=3, equip=C(5), pro={"U", "R", "G"}),
    "Shadowspear": dict(cost=C(1), p=1, t=1, equip=C(2), kw={"trample", "lifelink"}),
    "Bonesplitter": dict(cost=C(1), p=2, equip=C(1)),
    "Hammer of Nazahn": dict(cost=C(4), p=2, equip=C(4), kw={"indestr"}, dyn="nazahn"),
    "Mithril Coat": dict(cost=C(3), equip=C(3), kw={"indestr"}, flash=True, etb_attach=True),
    "Batterskull": dict(cost=C(5), p=4, t=4, equip=C(5), kw={"vigilance", "lifelink"}),
    "Skullclamp": dict(cost=C(1), p=1, t=-1, equip=C(1)),
    "Embercleave": dict(cost=C(6), p=1, t=1, equip=C(3), kw={"double", "trample"}),      # off-color, unused
    # Marvel list extras (approximate)
    "Vibranium Energy Daggers": dict(cost=C(1), p=1, t=2, equip=C(2)),
    "Voltaic Whip": dict(cost=C(1), p=1, equip=C(1)),
    "S.H.I.E.L.D. Spy Kit": dict(cost=C(2), p=1, t=1, equip=C(2)),
    "Infinity Formula": dict(cost=C(2), p=1, t=1, equip=C(2)),
}

# ---------------- Auras ----------------
AURAS = {
    "Super-Soldier Serum": dict(cost=C(1, 1), p=2, t=2, kw={"first", "vigilance"}, serum=True),
    "With Great Power . . .": dict(cost=C(3, 2), dyn="wgp"),
    "All That Glitters": dict(cost=C(1, 1), dyn="glitters"),
}

# ---------------- creatures / other ----------------
OTHER = {
    "Puresteel Paladin": dict(cost=C(0, 2), type="creature", tags={"puresteel"}),
    "Brass Squire": dict(cost=C(3), type="creature", tags={"squire"}, artifact=True),
    "Danitha Capashen, Paragon": dict(cost=C(2, 1), type="creature", tags={"danitha"}),
    "Sram, Senior Edificer": dict(cost=C(1, 1), type="creature", tags={"sram"}),
    "Cid, Freeflier Pilot": dict(cost=C(1, 1), type="creature", tags={"cid"}),
    "Ronin, Shadow Stalker": dict(cost=C(2, 0, 1), type="creature", tags={"ronin"}),
    "Swordsman, Sharp Scoundrel": dict(cost=C(1, 0, 1), type="creature", tags={"swordsman"}),
    "Peggy Carter, Secret Agent": dict(cost=C(1, 1), type="creature", tags={"peggy"}),
    "Squall, SeeD Mercenary": dict(cost=C(2, 1, 1), type="creature", tags={"squall"}),
    "General's Enforcer": dict(cost=C(0, 1, 1), type="creature", tags={"enforcer"}),
    "Bastion Protector": dict(cost=C(2, 2), type="creature", tags={"bastion"}),
    "Armored Skyhunter": dict(cost=C(3, 1), type="creature", tags={"skyhunter"}),
    "Cloak and Dagger, Entwined": dict(cost=C(1, 1, 1), type="creature", tags={"cloak"}),
    # spells
    "Steelshaper's Gift": dict(cost=C(0, 1), type="sorcery", tags={"tutor_equip"}),
    "Open the Armory": dict(cost=C(1, 1), type="sorcery", tags={"tutor_equip"}),
    "Demonic Tutor": dict(cost=C(1, 0, 1), type="sorcery", tags={"tutor_any"}),
    "Enlightened Tutor": dict(cost=C(0, 1), type="instant", tags={"tutor_top"}),
    "Vampiric Tutor": dict(cost=C(0, 0, 1), type="instant", tags={"tutor_top"}),
    "Imperial Seal": dict(cost=C(0, 0, 1), type="sorcery", tags={"tutor_top"}),
    "Night's Whisper": dict(cost=C(1, 0, 1), type="sorcery", tags={"draw2"}),
    "Sign in Blood": dict(cost=C(0, 0, 2), type="sorcery", tags={"draw2"}),
    "Read the Bones": dict(cost=C(2, 0, 1), type="sorcery", tags={"draw2"}),
    "Smothering Tithe": dict(cost=C(3, 1), type="enchantment", tags={"tithe"}),
    "Teferi's Protection": dict(cost=C(2, 1), type="instant", tags={"teferi"}),
    "Take Up the Shield": dict(cost=C(1, 1), type="instant", tags={"save_destroy"}),
    "Flawless Maneuver": dict(cost=C(2, 1), type="instant", tags={"flawless"}),
    "Akroma's Will": dict(cost=C(3, 1), type="instant", tags={"akroma"}),
    "Austere Command": dict(cost=C(4, 2), type="sorcery", tags={"wipe"}),
    "Damn": dict(cost=C(0, 0, 2), type="sorcery", tags={"spot", "wipe_overload"}),
    "Swords to Plowshares": dict(cost=C(0, 1), type="instant", tags={"spot"}),
    "Path to Exile": dict(cost=C(0, 1), type="instant", tags={"spot"}),
    "Despark": dict(cost=C(0, 1, 1), type="instant", tags={"spot"}),
    "Silverquill Charm": dict(cost=C(0, 1, 1), type="instant", tags={"spot"}),
    "Fracture": dict(cost=C(0, 1, 1), type="instant", tags=set()),
    "Infernal Grasp": dict(cost=C(1, 0, 1), type="instant", tags={"spot"}),
    "Deadly Rollick": dict(cost=C(3, 0, 1), type="instant", tags={"spot", "free_cmdr"}),
    "Anguished Unmaking": dict(cost=C(1, 1, 1), type="instant", tags={"spot"}),
    "Vindicate": dict(cost=C(1, 1, 1), type="sorcery", tags={"spot"}),
    "Generous Gift": dict(cost=C(2, 1), type="instant", tags={"spot"}),
    "Farewell": dict(cost=C(4, 2), type="sorcery", tags={"wipe"}),
    # protection creatures / enchantments
    "Mother of Runes": dict(cost=C(0, 1), type="creature", tags={"mother"}),
    "Giver of Runes": dict(cost=C(0, 1), type="creature", tags={"mother"}),
    "Benevolent Bodyguard": dict(cost=C(0, 1), type="creature", tags={"bodyguard"}),
    "Sigarda's Aid": dict(cost=C(0, 1), type="enchantment", tags={"aid"}),
    "Stoneforge Mystic": dict(cost=C(1, 1), type="creature", tags={"sfm"}),
    "Stonehewer Giant": dict(cost=C(3, 2), type="creature", tags={"stonehewer"}),
    "Armory Automaton": dict(cost=C(3), type="creature", tags={"automaton"}, artifact=True),
    "Esper Sentinel": dict(cost=C(0, 1), type="creature", tags={"sentinel"}, artifact=True),
    "Land Tax": dict(cost=C(0, 1), type="enchantment", tags={"landtax"}),
    "Drannith Magistrate": dict(cost=C(1, 1), type="creature", tags=set()),
    # rocks / fast mana
    "Sol Ring": dict(cost=C(1), type="artifact", tags={"rock"}, prod="CC"),
    "Arcane Signet": dict(cost=C(2), type="artifact", tags={"rock"}, prod={"W", "B"}),
    "Mind Stone": dict(cost=C(2), type="artifact", tags={"rock"}, prod={"C"}),
    "Orzhov Signet": dict(cost=C(2), type="artifact", tags={"rock"}, prod={"W", "B"}),
    "Talisman of Hierarchy": dict(cost=C(2), type="artifact", tags={"rock"}, prod={"W", "B"}),
    "Fellwar Stone": dict(cost=C(2), type="artifact", tags={"rock"}, prod={"W", "B"}),
    "Mana Vault": dict(cost=C(1), type="artifact", tags={"burst3"}),
    "Grim Monolith": dict(cost=C(2), type="artifact", tags={"burst3"}),
    "Chrome Mox": dict(cost=C(0), type="artifact", tags={"rock", "chrome"}, prod={"W", "B"}),
    "Mox Diamond": dict(cost=C(0), type="artifact", tags={"rock", "diamond"}, prod={"W", "B"}),
    "Lotus Petal": dict(cost=C(0), type="artifact", tags={"petal"}),
    "The One Ring": dict(cost=C(4), type="artifact", tags={"ring"}),
    "Necropotence": dict(cost=C(0, 0, 3), type="enchantment", tags={"necro"}),
    # Marvel list creatures (treated as plain creatures)
    "Black Widow, Double Agent": dict(cost=C(1, 0, 1), type="creature", tags=set()),
    "Bucky Barnes, Eager Ally": dict(cost=C(1, 1), type="creature", tags=set()),
    "Viper, Cruel Conspirator": dict(cost=C(2, 0, 1), type="creature", tags=set()),
    "Spider-Man Noir": dict(cost=C(2, 0, 1), type="creature", tags=set()),
    "Whiplash, Vengeful Engineer": dict(cost=C(2, 0, 1), type="creature", tags=set()),
    "Red Guardian, Super-Soldier": dict(cost=C(2, 1), type="creature", tags=set()),
    "White Widow, Free Agent": dict(cost=C(2, 0, 1), type="creature", tags=set()),
    "Costume Closet": dict(cost=C(1), type="artifact", tags=set()),
    "The Soul Stone": dict(cost=C(1), type="artifact", tags=set()),
    "BLANK": dict(cost=C(99), type="sorcery", tags=set()),
}

COMMANDER = "Winter Soldier, Icy Assassin"

GAME_CHANGERS = {"Demonic Tutor", "Smothering Tithe", "Teferi's Protection", "Enlightened Tutor", "Vampiric Tutor",
                 "Imperial Seal", "Mana Vault", "Grim Monolith", "Chrome Mox", "Mox Diamond", "Ancient Tomb",
                 "The One Ring", "Necropotence", "Drannith Magistrate", "Farewell", "Opposition Agent",
                 "Orcish Bowmasters", "Bolas's Citadel", "Ad Nauseam", "Tergrid, God of Fright // Tergrid's Lantern"}
