"""Ranking and bucketing."""

from collections import defaultdict

import db


def rank(conn, names: list[str], limit: int = 50) -> dict:
    # 1. Fold display strings -> normalized keys
    keys = [db.norm_key(name) for name in names]
    if not keys:
        raise ValueError("empty ingredient list")
    # 2. Get ranked recipes from DB (matched DESC, needed ASC)
    ranked = db.coverage(conn, keys, limit)

    if not ranked:
        return {"results": []}

    recipe_ids = [row["id"] for row in ranked]

    # 3. Fetch all non-staple ingredients for those recipes — one query
    placeholder = ", ".join("?" * len(recipe_ids))
    rows = conn.execute(
        f"""
		SELECT ri.recipe_id, i.name, i.name_key, i.id
		FROM recipe_ingredient ri
		JOIN ingredient i ON i.id = ri.ingredient_id
		WHERE ri.recipe_id IN ({placeholder}) AND i.is_staple = 0
	""",
        recipe_ids,
    ).fetchall()

    # Group by recipe_id
    by_recipe: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_recipe[row["recipe_id"]].append(dict(row))

    # 4. Build result with missing lists per recipe
    key_set = set(keys)
    results = []
    for row in ranked:
        ring = by_recipe.get(row["id"], [])
        missing = [r["name"] for r in ring if r["name_key"] not in key_set]
        results.append(
            {
                "id": row["id"],
                "title": row["title"],
                "servings": row["servings"],
                "matched": row["matched"],
                "needed": row["needed"],
                "missing": missing,
                "ingredient_ids": [r["id"] for r in ring],
            }
        )

    return {"results": results}
