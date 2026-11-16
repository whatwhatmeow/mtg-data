#!/usr/bin/env python3
"""Download Scryfall's "Default Cards" bulk file (every printing of every card)
and slim it down to the columns we actually research with.

Output: data/cards.csv.gz (+ data/meta.json)
Usage:  python update.py            # real download
        python update.py --input f  # use a local bulk JSON (testing)
"""
import argparse, csv, gzip, json, os, re, sys, urllib.request
from collections import defaultdict
from datetime import datetime, timezone

HEADERS = {"User-Agent": "mtg-data-updater/1.0 (personal research)", "Accept": "application/json"}
SKIP_LAYOUTS = {"token", "double_faced_token", "emblem", "art_series"}  # not real cards
MIN_ROWS = 50_000  # sanity check so a bad download never overwrites good data
COLUMNS = ["id", "oracle_id", "name", "set_code", "set_name", "collector_number", "released_at",
           "rarity", "layout", "mana_cost", "cmc", "type_line", "oracle_text", "power",
           "toughness", "loyalty", "color_identity", "keywords", "commander_legality",
           "price_usd", "price_usd_foil", "price_usd_etched", "finishes", "promo",
           "promo_types", "digital", "game_changer", "marvel"]

# --- Marvel-printing flag -------------------------------------------------
# marvel = 1 when THIS printing is from a Marvel product:
#   * any set whose name mentions Marvel or Spider-Man (play boosters, Commander,
#     Jumpstart, Marvel Universe bonus sheet, promos, ...), plus sets listed in
#     data/marvel_extra.json;
#   * Secret Lair printings that sit in a Universes Beyond drop containing at least
#     one Marvel-original card (a card first printed in a Marvel set / Secret Lair
#     that also appears in a Marvel set). Drops are runs of consecutive collector
#     numbers released the same day.
# A Marvel Secret Lair made only of reprints can't be detected this way: add it to
# data/marvel_extra.json ("printings": [["sld", first_number, last_number], ...]).
MARVEL_SET_NAME = re.compile(r"marvel|spider-man", re.I)
SECRET_LAIR_SETS = {"sld", "slp", "slc"}


def _num(cn):
    m = re.match(r"\d+", cn or "")
    return int(m.group()) if m else None


def flag_marvel(rows, extra=None):
    extra = extra or {}
    marvel_sets = {r["set_code"] for r in rows if MARVEL_SET_NAME.search(r["set_name"])}
    marvel_sets |= set(extra.get("sets", []))
    first, in_marvel = {}, set()
    for r in rows:
        if str(r["digital"]) == "1":
            continue
        key = (r["released_at"], r["set_code"])
        if r["name"] not in first or key < first[r["name"]]:
            first[r["name"]] = key
        if r["set_code"] in marvel_sets:
            in_marvel.add(r["name"])
    originals = {n for n in in_marvel if first[n][1] in marvel_sets | SECRET_LAIR_SETS}
    groups = defaultdict(list)
    for r in rows:
        if r["set_code"] in SECRET_LAIR_SETS and "universesbeyond" in r["promo_types"] and _num(r["collector_number"]) is not None:
            groups[(r["set_code"], r["released_at"])].append(r)
    marvel_ids, drops = set(), []
    for key, rs in groups.items():
        rs.sort(key=lambda r: _num(r["collector_number"]))
        run = []
        for r in rs + [None]:
            if r is not None and (not run or _num(r["collector_number"]) - _num(run[-1]["collector_number"]) <= 1):
                run.append(r)
                continue
            if any(x["name"] in originals for x in run):
                marvel_ids.update(x["id"] for x in run)
                drops.append((key[0], key[1], run[0]["collector_number"], run[-1]["collector_number"], len(run)))
            run = [r] if r is not None else []
    ranges = [(s, int(a), int(b)) for s, a, b in extra.get("printings", [])]
    for r in rows:
        n = _num(r["collector_number"])
        hit = r["set_code"] in marvel_sets or r["id"] in marvel_ids or any(
            r["set_code"] == s and n is not None and a <= n <= b for s, a, b in ranges)
        r["marvel"] = int(hit)
    return sorted(drops)


def load_extra(out):
    p = os.path.join(out, "marvel_extra.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=300)


def parse_cards(raw):
    """Accepts a JSON array or JSON Lines, gzipped or not."""
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    text = raw.decode("utf-8").lstrip()
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def load_bulk():
    meta = json.load(fetch("https://api.scryfall.com/bulk-data"))
    entry = next(e for e in meta["data"] if e["type"] == "default_cards")
    # Scryfall has used both field names over time; accept either.
    url = entry.get("download_uri") or entry.get("jsonl_download_uri")
    if not url:
        sys.exit("No download link found. Entry keys were: " + ", ".join(entry))
    size = entry.get("size") or entry.get("compressed_size") or 0
    print(f"Downloading {url} (~{size/1e6:.0f} MB)", flush=True)
    return parse_cards(fetch(url).read())


def face_join(card, key):
    """Multi-faced cards keep text per face; join with ' // '."""
    if card.get(key) not in (None, ""):
        return card[key]
    faces = card.get("card_faces") or []
    return " // ".join(f.get(key, "") or "" for f in faces)


def to_row(c):
    p = c.get("prices") or {}
    return {
        "id": c["id"], "oracle_id": c.get("oracle_id", ""),
        "name": c["name"], "set_code": c["set"], "set_name": c["set_name"],
        "collector_number": c["collector_number"], "released_at": c.get("released_at", ""),
        "rarity": c.get("rarity", ""), "layout": c.get("layout", ""),
        "mana_cost": face_join(c, "mana_cost"), "cmc": c.get("cmc", ""),
        "type_line": face_join(c, "type_line"), "oracle_text": face_join(c, "oracle_text"),
        "power": face_join(c, "power"), "toughness": face_join(c, "toughness"),
        "loyalty": face_join(c, "loyalty"),
        "color_identity": "".join(c.get("color_identity", [])),
        "keywords": ",".join(c.get("keywords", [])),
        "commander_legality": (c.get("legalities") or {}).get("commander", ""),
        "price_usd": p.get("usd") or "", "price_usd_foil": p.get("usd_foil") or "",
        "price_usd_etched": p.get("usd_etched") or "",
        "finishes": ",".join(c.get("finishes", [])),
        "promo": int(bool(c.get("promo"))),
        "promo_types": ",".join(c.get("promo_types", [])),
        "digital": int(bool(c.get("digital"))),
        "game_changer": int(bool(c.get("game_changer"))),
        "marvel": 0,  # filled in by flag_marvel()
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input")
    ap.add_argument("--out", default="data")
    ap.add_argument("--min-rows", type=int, default=MIN_ROWS)
    a = ap.parse_args()

    cards = json.load(open(a.input)) if a.input else load_bulk()
    rows = [to_row(c) for c in cards if c.get("layout") not in SKIP_LAYOUTS]
    rows.sort(key=lambda r: (r["set_code"], r["collector_number"].zfill(6), r["name"]))
    if len(rows) < a.min_rows:
        sys.exit(f"Only {len(rows)} rows - refusing to overwrite existing data.")

    drops = flag_marvel(rows, load_extra(a.out))
    gc = len({r["name"] for r in rows if r["game_changer"]})
    print(f"{gc} Game Changers, {sum(r['marvel'] for r in rows)} Marvel printings, {len(drops)} Marvel Secret Lair drops")
    if gc == 0:
        print("WARNING: no Game Changers flagged - did Scryfall rename the game_changer field?")

    os.makedirs(a.out, exist_ok=True)
    tmp = os.path.join(a.out, "cards.csv.gz.tmp")
    with gzip.open(tmp, "wt", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, os.path.join(a.out, "cards.csv.gz"))
    json.dump({"updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
               "printings": len(rows), "game_changers": gc,
               "marvel_printings": sum(r["marvel"] for r in rows), "source": "Scryfall default_cards bulk data"},
              open(os.path.join(a.out, "meta.json"), "w"), indent=2)
    print(f"Wrote {len(rows)} printings")


if __name__ == "__main__":
    main()
