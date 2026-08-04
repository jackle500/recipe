"""SQLite access. ponytail: stdlib sqlite3, no ORM — single user, one process."""

import json
import os
import sqlite3
import unicodedata  # Vietnamese support

DB_PATH = os.environ.get("DB_PATH", "./data/recipes.db")
_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "aliases.json")) as f:
    ALIASES = json.load(f)

SCHEMA = """
CREATE TABLE IF NOT EXISTS recipe (
    id          INTEGER PRIMARY KEY,
    title       TEXT NOT NULL,
    title_key   TEXT NOT NULL UNIQUE,
    instructions TEXT NOT NULL DEFAULT '',
    source_url  TEXT UNIQUE,
    servings    INTEGER,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS ingredient (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,               -- display form
    name_key   TEXT NOT NULL UNIQUE,        -- normalised key for search/dedup
    is_staple  INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS recipe_ingredient (
    recipe_id     INTEGER NOT NULL REFERENCES recipe(id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES ingredient(id),
    qty           TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (recipe_id, ingredient_id)
);
CREATE INDEX IF NOT EXISTS idx_ri_ingredient ON recipe_ingredient(ingredient_id);
-- FTS5 deferred: external-content trigram index ~1k ingredient rows
"""


def connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


def norm_display(name: str) -> str:
    return unicodedata.normalize("NFC", name)


def norm_key(name: str) -> str:
    # 1. NFD Standardize the string to use single, pre-composed characters (NFC)
    decomposed = unicodedata.normalize("NFD", name)

    # 2. Keep only non-combininng characters
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    composed = unicodedata.normalize("NFC", stripped)
    # 3. Map đ -> d, Đ -> D
    trans = str.maketrans({"đ": "d", "Đ": "D"})
    translated = composed.translate(trans)
    return " ".join(translated.lower().split())


def ingredient_ids(conn: sqlite3.Connection, names: list[str]) -> list[int]:
    """Get-or-create ingredient rows, returns ids in input order."""
    ids = []
    for raw in names:
        nk = norm_key(raw)
        canonical = ALIASES.get(nk)
        if canonical:
            raw, nk = canonical, norm_key(canonical)
        if not nk:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO ingredient (name, name_key) VALUES (?,?)",
            (norm_display(raw), nk),
        )
        ids.append(
            conn.execute(
                "SELECT id FROM ingredient WHERE name_key = ?", (nk,)
            ).fetchone()["id"]
        )
    return ids


def save_recipe(conn: sqlite3.Connection, r: dict, recipe_id: int | None = None) -> int:
    """Insert or replace a recipe plus its ingredient links. Returns recipe id."""
    with conn:
        if recipe_id is None:
            cur = conn.execute(
                "INSERT OR IGNORE INTO recipe (title, title_key, instructions, source_url, servings) VALUES (?,?,?,?,?)",
                (
                    r["title"],
                    norm_key(r["title"]),
                    r.get("instructions", ""),
                    r.get("source_url"),
                    r.get("servings"),
                ),
            )
            if cur.rowcount == 0:
                raise ValueError(f"Recipe already exists: {r['title']}")
            recipe_id = cur.lastrowid
        else:
            conn.execute(
                "UPDATE recipe SET title=?, title_key=?, instructions=?, servings=? WHERE id=?",
                (
                    r["title"],
                    norm_key(r["title"]),
                    r.get("instructions", ""),
                    r.get("servings"),
                    recipe_id,
                ),
            )
            conn.execute(
                "DELETE FROM recipe_ingredient WHERE recipe_id=?", (recipe_id,)
            )
        ings = [i for i in r.get("ingredients", []) if norm_key(i.get("name", ""))]
        for ing, iid in zip(ings, ingredient_ids(conn, [i["name"] for i in ings])):
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


def load_recipes(
    conn: sqlite3.Connection, limit: int = 50, offset: int = 0, q: str | None = None
) -> list[dict]:
    query = "SELECT id, title, servings, created_at FROM recipe"
    params: list = []
    if q:
        query += " WHERE title LIKE ?"
        params.append(f"%{q}%")
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    return [dict(r) for r in conn.execute(query, params).fetchall()]


def delete_recipe(conn: sqlite3.Connection, recipe_id: int) -> bool:
    cur = conn.execute("DELETE FROM recipe WHERE id=?", (recipe_id,))
    return cur.rowcount > 0


def coverage(
    conn: sqlite3.Connection, name_keys: list[str], limit: int = 50
) -> list[dict]:
    """Rank recipes by how many of the given ingredients they use."""
    holder = ", ".join("?" * len(name_keys))
    sql = f"""
	WITH have AS (
		SELECT id FROM ingredient
		WHERE name_key IN ({holder})
			AND is_staple = 0
	),
	cand AS (
		SELECT DISTINCT recipe_id
		FROM recipe_ingredient
		WHERE ingredient_id IN (SELECT id FROM have)
	)
	SELECT
		r.id, r.title, r.servings,
		COUNT(*) FILTER (WHERE ri.ingredient_id IN (SELECT id FROM have)) AS matched,
		COUNT(*) AS needed
	FROM cand c
	JOIN recipe				r ON r.id = c.recipe_id
	JOIN recipe_ingredient ri ON ri.recipe_id = c.recipe_id
	JOIN ingredient			i ON i.id = ri.ingredient_id
	WHERE i.is_staple = 0
	GROUP BY r.id
	HAVING matched >= ?
	ORDER By matched DESC, needed ASC
	LIMIT ?
	"""
    params = name_keys + [1, limit]
    cur = conn.execute(sql, params)
    return [dict(r) for r in cur.fetchall()]


def search_ingredients(
    conn: sqlite3.Connection, query: str, limit: int = 10
) -> list[str]:
    query_key = norm_key(query)
    pattern = f"%{query_key}%"
    canonicals = [v for k, v in ALIASES.items() if k.startswith(query_key)]
    if canonicals:
        in_clause = ", ".join("?" * len(canonicals))
        sql = f"SELECT name FROM ingredient WHERE name_key LIKE ? OR name_key IN ({in_clause}) ORDER BY name_key LIMIT ?"
        params = [pattern, *canonicals, limit]
    else:
        sql = "SELECT name FROM ingredient WHERE name_key LIKE ? ORDER BY name_key LIMIT ?"
        params = [pattern, limit]

    rows = conn.execute(sql, params).fetchall()
    return [row["name"] for row in rows]
