"""Card data for Doctor Doom, Unrivaled (mono-black empty-library) simulator.

cost: generic 'g' + 'B'. roles via tags.
"""


def C(g=0, B=0):
    return {"g": g, "B": B}


LANDS = {
    "Swamp": dict(prod="B", swamp=True),
    "Snow-Covered Swamp": dict(prod="B", swamp=True),
    "Urborg, Tomb of Yawgmoth": dict(prod="B", swamp=True),
    "Cabal Coffers": dict(prod="C", coffers=True),
    "Castle Locthwain": dict(prod="B", castle=True, cond="swamp"),
    "Takenuma, Abandoned Mire": dict(prod="B"),
    "Phyrexian Tower": dict(prod="C", tower=True),
    "Bojuka Bog": dict(prod="B", tapped=True, bog=True),
    "Reliquary Tower": dict(prod="C"),
    "War Room": dict(prod="C"),
    "Hall of the Bandit Lord": dict(prod="C", tapped=True, hall=True),
    "Ancient Tomb": dict(prod="CC"),
    "Urza's Saga": dict(prod="C", saga=True),
    "Vault of Whispers": dict(prod="B", artifact=True),
    "Lake of the Dead": dict(prod="B"),
    "Peat Bog": dict(prod="BB", tapped=True),
    "City of Brass": dict(prod="B", ping=1),
    "Mana Confluence": dict(prod="B", ping=1),
    "Gemstone Mine": dict(prod="B"),
    "Command Tower": dict(prod="B"),
    "Cavern of Souls": dict(prod="B"),
    "City of Traitors": dict(prod="CC", traitors=True),
    "Crystal Vein": dict(prod="C"),
    "Ebon Stronghold": dict(prod="B", tapped=True),
    "Spire of Industry": dict(prod="B"),
    "Tarnished Citadel": dict(prod="B"),
    "Gemstone Caverns": dict(prod="C"),
    "Shizo, Death's Storehouse": dict(prod="B"),
    "Tomb of Urami": dict(prod="B", ping=1),
    "Cabal Pit": dict(prod="B", ping=1),
    "Polluted Delta": dict(prod="B"),
    "Agadeem's Awakening // Agadeem, the Undercrypt": dict(prod="B"),
    "Fell the Profane // Fell Mire": dict(prod="B"),
    # Nov 16, 2026 (merged Doom + Ultron list)
    "Castle Doom": dict(prod="C"),                                  # artifact-only colored mana and the Doombot ability not modeled
    "Memorial to Folly": dict(prod="B", tapped=True, memorial=True),  # {2}{B}, T, sacrifice: creature card from graveyard to hand
    "Spymaster's Vault": dict(prod="B", cond="swamp"),              # connive ability not modeled; tapped without a Swamp
    # Nov 20, 2026: the Unique Pact land base (every name once) and the Owned build's lands
    "Eumidian Hatchery": dict(prod="B", ping=1),
    "Rogue's Passage": dict(prod="C"),
    "Thriving Moor": dict(prod="B", tapped=True),
    "Evolving Wilds": dict(prod="B", tapped=True, swamp=True),     # approximated as a tapped Swamp
    "Rocky Tar Pit": dict(prod="B", tapped=True, swamp=True),      # approximated as a tapped Swamp
    "Unclaimed Territory": dict(prod="C"),                         # Villain-only colored mana not modeled
    "Hive of the Eye Tyrant": dict(prod="B", cond="hive"),         # tapped if you control two or more other lands
    "Barad-d\u00fbr": dict(prod="B", cond="legend"),              # untapped only with Doom on the battlefield
    "Leechridden Swamp": dict(prod="B", tapped=True, swamp=True),
    "Witch's Cottage": dict(prod="B", swamp=True, cond="cottage"), # untapped with three other Swamps
    "Mortuary Mire": dict(prod="B", tapped=True),
    "The Dross Pits": dict(prod="B", tapped=True),
    "Barren Moor": dict(prod="B", tapped=True),                    # cycling not modeled
    "Polluted Mire": dict(prod="B", tapped=True),                  # cycling not modeled
    "Hagra Mauling // Hagra Broodpit": dict(prod="B", tapped=True),# played as the land only
    "Ifnir Deadlands": dict(prod="B", ping=1),
    "Darksteel Citadel": dict(prod="C", artifact=True),
    "Mirrex": dict(prod="C"),
    "Treasure Vault": dict(prod="C", artifact=True),
    "Buried Ruin": dict(prod="C"),
    "Path of Ancestry": dict(prod="B", tapped=True),
    "Exotic Orchard": dict(prod="C"),                              # conservative: opponents' colors ignored
    "Tomb of Urami": dict(prod="B", ping=1),
}

CARDS = {
    "Doctor Doom, Unrivaled": dict(cost=C(2, 2), type="creature", tags={"doom"}),
    # fast mana / rocks
    "Sol Ring": dict(cost=C(1), type="artifact", tags={"rock"}, prod="CC"),
    "Arcane Signet": dict(cost=C(2), type="artifact", tags={"rock"}, prod="B"),
    "Mind Stone": dict(cost=C(2), type="artifact", tags={"rock"}, prod="C"),
    "Charcoal Diamond": dict(cost=C(2), type="artifact", tags={"rock"}, prod="B", tapped=True),
    "Jet Medallion": dict(cost=C(2), type="artifact", tags={"rock", "medallion"}),
    "Thought Vessel": dict(cost=C(2), type="artifact", tags={"rock"}, prod="C"),
    "Worn Powerstone": dict(cost=C(3), type="artifact", tags={"rock"}, prod="CC", tapped=True),
    "Wayfarer's Bauble": dict(cost=C(1), type="artifact", tags={"bauble"}),
    "Mana Vault": dict(cost=C(1), type="artifact", tags={"burst3"}),
    "Grim Monolith": dict(cost=C(2), type="artifact", tags={"burst3"}),
    "Chrome Mox": dict(cost=C(0), type="artifact", tags={"rock", "chrome"}, prod="B"),
    "Mox Diamond": dict(cost=C(0), type="artifact", tags={"rock", "diamond"}, prod="B"),
    "Jeweled Lotus": dict(cost=C(0), type="artifact", tags={"jlotus"}),
    "Cruel Tutor": dict(cost=C(2, 1), type="sorcery", tags={"tutor_top"}),
    "Lotus Petal": dict(cost=C(0), type="artifact", tags={"petal"}),
    "Lion's Eye Diamond": dict(cost=C(0), type="artifact", tags={"led"}),
    "Dark Ritual": dict(cost=C(0, 1), type="instant", tags={"ritual"}, gain=3),
    "Cabal Ritual": dict(cost=C(1, 1), type="instant", tags={"ritual"}, gain=3),
    "Culling the Weak": dict(cost=C(0, 1), type="instant", tags={"culling"}),
    "Crypt Ghast": dict(cost=C(3, 1), type="creature", tags={"ghast"}),
    # win pieces
    "Demonic Consultation": dict(cost=C(0, 1), type="instant", tags={"consult", "win"}),
    "Tainted Pact": dict(cost=C(1, 1), type="instant", tags={"pact"}),
    "Leveler": dict(cost=C(5), type="creature", tags={"leveler", "win"}, artifact=True),
    "Inverter of Truth": dict(cost=C(2, 2), type="creature", tags={"inverter", "win"}),
    "Doomsday": dict(cost=C(0, 3), type="instant", tags={"doomsday", "win"}),
    "Nihil Spellbomb": dict(cost=C(1), type="artifact", tags={"gyexile"}),
    "Tormod's Crypt": dict(cost=C(0), type="artifact", tags={"gyexile"}),
    "Ad Nauseam": dict(cost=C(3, 2), type="instant", tags={"adnaus"}),
    "Peer into the Abyss": dict(cost=C(4, 3), type="sorcery", tags={"peer"}),
    "Aetherflux Reservoir": dict(cost=C(4), type="artifact", tags={"aetherflux"}),
    "Exsanguinate": dict(cost=C(0, 2), type="sorcery", tags={"exsang"}),
    # haste / untap / copy
    "Lightning Greaves": dict(cost=C(2), type="artifact", tags={"haste", "shroud"}),
    "Swiftfoot Boots": dict(cost=C(2), type="artifact", tags={"haste", "hexproof"}),
    "Thousand-Year Elixir": dict(cost=C(3), type="artifact", tags={"haste", "untap1"}),
    "Magewright's Stone": dict(cost=C(2), type="artifact", tags={"untap1"}),
    "Patriar's Seal": dict(cost=C(3), type="artifact", tags={"untap1"}),
    "Staff of Domination": dict(cost=C(3), type="artifact", tags={"staff"}),
    "Umbral Mantle": dict(cost=C(3), type="artifact", tags={"mantle"}),
    "Clock of Omens": dict(cost=C(4), type="artifact", tags={"clock"}),
    "Illusionist's Bracers": dict(cost=C(2), type="artifact", tags={"copy"}),
    "Rings of Brighthearth": dict(cost=C(3), type="artifact", tags={"rings"}),
    "Darksteel Plate": dict(cost=C(3), type="artifact", tags={"indestr"}),
    # self-mill
    "Mesmeric Orb": dict(cost=C(2), type="artifact", tags={"orb"}),
    "Altar of Dementia": dict(cost=C(2), type="artifact", tags={"altar"}),
    "Codex Shredder": dict(cost=C(1), type="artifact", tags={"mill1"}),
    "Millstone": dict(cost=C(2), type="artifact", tags={"millstone"}),
    "Perpetual Timepiece": dict(cost=C(2), type="artifact", tags={"mill2"}),
    "Stitcher's Supplier": dict(cost=C(0, 1), type="creature", tags={"supplier"}),
    # draw
    "Necropotence": dict(cost=C(0, 3), type="enchantment", tags={"necro"}),
    "Bolas's Citadel": dict(cost=C(3, 3), type="artifact", tags={"citadel"}),
    "Phyrexian Arena": dict(cost=C(1, 2), type="enchantment", tags={"arena"}),
    "Black Market Connections": dict(cost=C(2, 1), type="enchantment", tags={"bmc"}),
    "Dark Confidant": dict(cost=C(1, 1), type="creature", tags={"bob"}),
    "Night's Whisper": dict(cost=C(1, 1), type="sorcery", tags={"draw2"}),
    "Sign in Blood": dict(cost=C(0, 2), type="sorcery", tags={"draw2"}),
    "Read the Bones": dict(cost=C(2, 1), type="sorcery", tags={"draw2"}),
    "Damnable Pact": dict(cost=C(0, 2), type="sorcery", tags={"dpact"}),
    "Skullclamp": dict(cost=C(1), type="artifact", tags={"clamp"}),
    "Horn of Greed": dict(cost=C(3), type="artifact", tags={"horn"}),
    "The One Ring": dict(cost=C(4), type="artifact", tags={"ring"}),
    "Rat King, Pale Piper": dict(cost=C(2, 1), type="creature", tags={"ratking"}),
    "Sensei's Divining Top": dict(cost=C(1), type="artifact", tags={"top"}),
    "Deadly Dispute": dict(cost=C(1, 1), type="instant", tags={"sacdraw", "dispute"}),
    "Village Rites": dict(cost=C(0, 1), type="instant", tags={"sacdraw"}),
    "Feed the Swarm": dict(cost=C(1, 1), type="sorcery", tags={"removal"}),
    # tutors
    "Demonic Tutor": dict(cost=C(1, 1), type="sorcery", tags={"tutor"}),
    "Vampiric Tutor": dict(cost=C(0, 1), type="instant", tags={"tutor_top"}),
    "Imperial Seal": dict(cost=C(0, 1), type="sorcery", tags={"tutor_top"}),
    "Grim Tutor": dict(cost=C(1, 2), type="sorcery", tags={"tutor"}),
    "Diabolic Intent": dict(cost=C(1, 1), type="sorcery", tags={"tutor", "sac"}),
    "Diabolic Tutor": dict(cost=C(2, 2), type="sorcery", tags={"tutor"}),
    "Wishclaw Talisman": dict(cost=C(1), type="artifact", tags={"wishclaw"}),
    "Lim-Dûl's Vault": dict(cost=C(0, 1), type="instant", tags={"tutor_top"}),
    "Beseech the Mirror": dict(cost=C(1, 3), type="sorcery", tags={"tutor"}),
    "Scheming Symmetry": dict(cost=C(0, 1), type="sorcery", tags={"tutor_top"}),
    # interaction / protection (value to the pilot mostly as disruption reduction)
    "Snuff Out": dict(cost=C(0), type="instant", tags={"interact"}),
    "Deadly Rollick": dict(cost=C(0), type="instant", tags={"interact"}),
    "Dismember": dict(cost=C(1), type="instant", tags={"interact"}),
    "Fatal Push": dict(cost=C(0, 1), type="instant", tags={"interact"}),
    "Infernal Grasp": dict(cost=C(1, 1), type="instant", tags={"interact"}),
    "Go for the Throat": dict(cost=C(1, 1), type="instant", tags={"interact"}),
    "Bitter Triumph": dict(cost=C(1, 1), type="instant", tags={"interact"}),
    "Toxic Deluge": dict(cost=C(2, 1), type="sorcery", tags={"interact"}),
    "Damnation": dict(cost=C(2, 2), type="sorcery", tags={"interact"}),
    "Hagra Mauling": dict(cost=C(2, 2), type="instant", tags={"interact"}),
    "Duress": dict(cost=C(0, 1), type="sorcery", tags={"discard"}),
    "Thoughtseize": dict(cost=C(0, 1), type="sorcery", tags={"discard"}),
    "Cabal Therapy": dict(cost=C(0, 1), type="sorcery", tags={"discard"}),
    "Grief": dict(cost=C(2, 2), type="creature", tags={"discard", "grief"}),
    "Opposition Agent": dict(cost=C(2, 1), type="creature", tags={"stax"}),
    "Orcish Bowmasters": dict(cost=C(1, 1), type="creature", tags={"stax"}),
    "Damping Sphere": dict(cost=C(2), type="artifact", tags={"stax"}),
    "Hymn to Tourach": dict(cost=C(0, 2), type="sorcery", tags={"discard"}),
    "Inquisition of Kozilek": dict(cost=C(0, 1), type="sorcery", tags={"discard"}),
    "Cut Down": dict(cost=C(0, 1), type="instant", tags={"interact"}),
    "Sheoldred's Edict": dict(cost=C(1, 1), type="instant", tags={"interact"}),
    "Defense Grid": dict(cost=C(2), type="artifact", tags={"grid"}),
    "Tergrid, God of Fright // Tergrid's Lantern": dict(cost=C(3, 2), type="creature", tags={"stax"}),
    # recursion / misc value (light modeling)
    "Animate Dead": dict(cost=C(1, 1), type="enchantment", tags={"reanimate"}),
    "Reanimate": dict(cost=C(0, 1), type="sorcery", tags={"reanimate"}),
    "Animate Dead": dict(cost=C(1, 1), type="enchantment", tags={"reanimate"}),
    "Necromancy": dict(cost=C(2, 1), type="enchantment", tags={"reanimate"}),
    "Entomb": dict(cost=C(0, 1), type="instant", tags={"entomb"}),
    "Tainted Pact": dict(cost=C(1, 1), type="instant", tags={"pact"}),
    "Crashing Drawbridge": dict(cost=C(2), type="creature", tags={"haste", "drawbridge"}),
    "Lavaspur Boots": dict(cost=C(1), type="artifact", tags={"haste", "equip1"}),
    "Mox Amber": dict(cost=C(0), type="artifact", tags={"amber"}),
    "Feign Death": dict(cost=C(0, 1), type="instant", tags={"save"}),
    "Undying Malice": dict(cost=C(0, 1), type="instant", tags={"save"}),
    "Malakir Rebirth": dict(cost=C(0, 1), type="instant", tags={"save"}),
    "Liliana, Death's Majesty": dict(cost=C(3, 2), type="planeswalker", tags=set()),
    # ---- Nov 16, 2026: the merged Doom + Ultron list (card text from data/cards.csv.gz) ----
    # Ultron the Annihilator: a Robot token when he enters and each turn he attacks; every artifact that
    # reaches the graveyard drains each opponent for 1.
    "Ultron the Annihilator": dict(cost=C(3, 2), type="creature", tags={"ultron_a"}, artifact=True),
    "Ultron, Artificial Malevolence": dict(cost=C(3), type="creature", tags={"ultron_m"}, artifact=True),   # copies not modeled
    "The Soul Stone": dict(cost=C(1, 1), type="artifact", tags={"rock"}, prod="B"),                         # harness not modeled
    "Liquimetal Torque": dict(cost=C(2), type="artifact", tags={"rock"}, prod="C"),
    "Howling Mine": dict(cost=C(2), type="artifact", tags={"mine"}),
    "Idol of Oblivion": dict(cost=C(2), type="artifact", tags={"idol"}),
    "Peter Parker's Camera": dict(cost=C(1), type="artifact", tags={"camera"}),
    "Adaptive Omnitool": dict(cost=C(2), type="artifact", tags={"omnitool"}),
    "Grim Reaper's Scythe": dict(cost=C(2, 1), type="artifact", tags={"scythe"}),
    "Cranial Plating": dict(cost=C(2), type="artifact", tags={"equip_dmg"}),     # combat damage is not modeled
    "Lashwrithe": dict(cost=C(4), type="artifact", tags={"lash"}),               # only its Germ token matters here
    "Psychosis Crawler": dict(cost=C(5), type="creature", tags={"crawler"}, artifact=True),
    "Big Mother Mouser": dict(cost=C(4), type="creature", tags={"mouser"}, artifact=True),
    "Doom's Servo-Guards": dict(cost=C(1, 1), type="creature", tags={"servo"}, artifact=True),
    "Doombot Harbinger": dict(cost=C(2, 1), type="creature", tags={"harbinger"}, artifact=True),
    "Reclamation Specialist": dict(cost=C(2, 1), type="creature", tags={"reclaim"}, artifact=True),
    "Kingpin, Wilson Fisk": dict(cost=C(3, 1), type="creature", tags={"kingpin"}),
    "Doctor Doom": dict(cost=C(4, 2), type="creature", tags={"doom6"}),
    "Zombie Infestation": dict(cost=C(1, 1), type="enchantment", tags={"infest"}),
    "Age of Ultron": dict(cost=C(4, 1), type="enchantment", tags={"saga"}, last=3),
    "Genesis of the Daleks": dict(cost=C(4, 2), type="enchantment", tags={"saga"}, last=4),
    "The War in Heaven": dict(cost=C(3, 3), type="enchantment", tags={"saga"}, last=3),
    "Phyrexian Scriptures": dict(cost=C(2, 2), type="enchantment", tags={"saga"}, last=3),   # no effect in a solitaire model
    "Buried Alive": dict(cost=C(2, 1), type="sorcery", tags={"entomb", "buried"}),
    "Persist": dict(cost=C(1, 1), type="sorcery", tags={"reanimate"}),
    "Splinter's Technique": dict(cost=C(3, 1), type="sorcery", tags={"tutor"}),               # sneak cost not modeled
    "Shred Memory": dict(cost=C(1, 2), type="sorcery", tags={"transmute2"}),                  # always transmuted
    "Stargaze": dict(cost=C(0, 2), type="sorcery", tags={"stargaze"}),                        # plus X
    "Nasty End": dict(cost=C(1, 1), type="instant", tags={"sacdraw"}),
    "Doom Blade": dict(cost=C(1, 1), type="instant", tags={"interact"}),
    "Doomfall": dict(cost=C(2, 1), type="sorcery", tags={"discard"}),
    "Stitcher": None,
    # ---- Nov 20, 2026: the Owned build's stand-ins (light models) ----
    "Arc Reactor": dict(cost=C(5), type="artifact", tags={"rock"}, prod="CCC", tapped=True),   # improvise not modeled
    "Fellwar Stone": dict(cost=C(2), type="artifact", tags={"rock"}, prod="B"),
    "Isolinear Processor": dict(cost=C(2), type="artifact", tags={"rock"}, prod="C"),
    "Murmuring Volume": dict(cost=C(3), type="artifact", tags={"rock"}, prod="B"),
    "Leaden Myr": dict(cost=C(2), type="artifact", tags={"rock"}, prod="B", tapped=True),     # summoning sickness as tapped
    "Millikin": dict(cost=C(2), type="artifact", tags={"rock"}, prod="C", tapped=True),
    "Champion's Helm": dict(cost=C(3), type="artifact", tags={"hexproof"}),
    "Risky Research": dict(cost=C(2, 1), type="sorcery", tags={"draw2"}),
    "Resentful Revelation": dict(cost=C(1, 1), type="sorcery", tags={"draw2"}),
    "The Cruelty of Gix": dict(cost=C(3, 2), type="sorcery", tags={"tutor"}),
    "Lash of the Balrog": dict(cost=C(4, 1), type="sorcery", tags={"interact"}),
    "Withering Torment": dict(cost=C(2, 1), type="instant", tags={"interact"}),
    "Zombify": dict(cost=C(3, 1), type="sorcery", tags={"reanimate"}),
    "Victimize": dict(cost=C(2, 1), type="sorcery", tags={"reanimate"}),
    "Rescue from the Underworld": dict(cost=C(4, 1), type="instant", tags={"reanimate"}),
    "Breach the Multiverse": dict(cost=C(5, 2), type="sorcery", tags={"reanimate"}),
    "Chromatic Sphere": dict(cost=C(99), type="sorcery", tags=set()),      # blanks that keep their own names (Tainted Pact)
    "Chromatic Star": dict(cost=C(99), type="sorcery", tags=set()),
    "Mask of Memory": dict(cost=C(99), type="sorcery", tags=set()),
    "Rat King, Verminister": dict(cost=C(99), type="sorcery", tags=set()),
    "BLANK": dict(cost=C(99), type="sorcery", tags=set()),
}
CARDS.pop("Stitcher")

GAME_CHANGERS = {"Jeweled Lotus", "Necropotence", "Bolas's Citadel", "Demonic Tutor", "Vampiric Tutor", "Imperial Seal", "Ad Nauseam",
                 "The One Ring", "Mana Vault", "Grim Monolith", "Chrome Mox", "Mox Diamond", "Ancient Tomb",
                 "Lion's Eye Diamond", "Opposition Agent", "Orcish Bowmasters", "Tergrid, God of Fright // Tergrid's Lantern"}
