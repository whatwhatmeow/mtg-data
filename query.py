#!/usr/bin/env python3
"""Run SQL against the card data. Table `cards` = every printing; view `oracle` =
one row per unique card (cheapest non-digital printing price).

  python scripts/query.py "SELECT name, mana_cost FROM oracle WHERE ci_within(color_identity,'BG') AND type_line LIKE '%Creature%' LIMIT 20"

Helpers: ci_within(ci, 'BG')  -> card's color identity fits inside those colors
         ci_has(ci, 'U')      -> card's color identity includes that color
"""
import csv, gzip, sqlite3, sys, os

path = os.path.join(os.path.dirname(__file__), "..", "data", "cards.csv.gz")
db = sqlite3.connect(":memory:")
NUM = {"cmc", "price_usd", "price_usd_foil", "price_usd_etched"}
with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
    r = csv.DictReader(f)
    cols = r.fieldnames
    db.execute("CREATE TABLE cards (%s)" % ", ".join(c + (" REAL" if c in NUM else "") for c in cols))
    def conv(c, v):
        return (float(v) if v else None) if c in NUM else v
    db.executemany("INSERT INTO cards VALUES (%s)" % ",".join("?" * len(cols)),
                   ([conv(c, v) for c, v in row.items()] for row in r))
db.create_function("ci_within", 2, lambda ci, allowed: int(set(ci or "") <= set(allowed or "")))
db.create_function("ci_has", 2, lambda ci, c: int(c in (ci or "")))
db.execute("""CREATE VIEW oracle AS
  SELECT name, mana_cost, cmc, type_line, oracle_text, power, toughness, color_identity,
         keywords, commander_legality, MIN(price_usd) AS cheapest_usd, COUNT(*) AS printings,
         GROUP_CONCAT(DISTINCT set_name) AS sets
  FROM cards WHERE digital = '0' GROUP BY oracle_id""")
cur = db.execute(sys.argv[1])
w = csv.writer(sys.stdout)
w.writerow([d[0] for d in cur.description])
w.writerows(cur)
