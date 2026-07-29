"""SQLite access. ponytail: stdlib sqlite3, no ORM — single user, one process."""

import os
import sqlite3
import unicodedata #Vietnamese support"

DB_PATH = os.environ.get("DB_PATH", "./data/recipes.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS recipe (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL,
    instructions TEXT NOT NULL DEFAULT '',
    source_url  TEXT UNIQUE,
    servings    INTEGER,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS ingredient (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE          -- normalized: lowercase, stripped
);
CREATE TABLE IF NOT EXISTS recipe_ingredient (
    recipe_id     INTEGER NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES ingredient(id),
    qty           TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (recipe_id, ingredient_id)
);
"""


def connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def norm(name: str) -> str:
	#1. NFD Standardize the string to use single, pre-composed characters (NFC)
	decomposed_char = unicodedata.normalize('NFD', name)

	#2. Keep only non-combininng characters
	stripped = "".join(c for c in decomposed_char if unicodedata.category(c) != "Mn")

	#3. Map đ -> d, Đ -> D
	trans = str.maketrans({"đ": "d", "Đ": "D"})
	translated = stripped.translate(trans)

	#4. NFC - recompose (Korean hangul cleanup)
	composed = unicodedata.normalize('NFC', translated)

	#5. lowercase + collapse whitespace
	return " ".join(composed.lower().split())



def ingredient_ids(conn: sqlite3.Connection, names: list[str]) -> list[int]:
    """Get-or-create ingredient rows, returns ids in input order."""
    ids = []
    for raw in names:
        n = norm(raw)
        if not n:
            continue
        conn.execute("INSERT OR IGNORE INTO ingredient (name) VALUES (?)", (n,))
        ids.append(conn.execute("SELECT id FROM ingredient WHERE name = ?", (n,)).fetchone()["id"])
    return ids


def save_recipe(conn: sqlite3.Connection, r: dict, recipe_id: int | None = None) -> int:
    """Insert or replace a recipe plus its ingredient links. Returns recipe id."""
    with conn:
        if recipe_id is None:
            cur = conn.execute(
                "INSERT INTO recipe (title, instructions, source_url, servings) VALUES (?,?,?,?)",
                (r["title"], r.get("instructions", ""), r.get("source_url"), r.get("servings")),
            )
            recipe_id = cur.lastrowid
        else:
            conn.execute(
                "UPDATE recipe SET title=?, instructions=?, servings=? WHERE id=?",
                (r["title"], r.get("instructions", ""), r.get("servings"), recipe_id),
            )
            conn.execute("DELETE FROM recipe_ingredient WHERE recipe_id=?", (recipe_id,))
        for ing, iid in zip(r.get("ingredients", []), ingredient_ids(conn, [i["name"] for i in r.get("ingredients", [])])):
            conn.execute(
                "INSERT OR REPLACE INTO recipe_ingredient (recipe_id, ingredient_id, qty) VALUES (?,?,?)",
                (recipe_id, iid, ing.get("qty", "")),
            )
    return recipe_id


def load_recipe(conn: sqlite3.Connection, recipe_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM recipe WHERE id=?", (recipe_id,)).fetchone()
    if row is None:
        return None
    ings = conn.execute(
        "SELECT i.name, ri.qty FROM recipe_ingredient ri"
        " JOIN ingredient i ON i.id = ri.ingredient_id WHERE ri.recipe_id=?",
        (recipe_id,),
    ).fetchall()
    return dict(row) | {"ingredients": [dict(i) for i in ings]}
