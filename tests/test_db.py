import sqlite3

import db


def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.executescript(db.SCHEMA)
    return c


def test_norm_roundtrip():
    assert db.norm_display("Phở bò") == "Phở bò"
    assert db.norm_key("Phở bò") == db.norm_key("Pho bo")
    assert db.norm_key(db.norm_display("Phở bò")) == db.norm_key("Phở bò")


def test_name_key_unique():
    c = conn()

    # Insert "Phở" -- normailize to "pho", creates row
    db.ingredient_ids(c, ["Phở"])

    # Insert "pho" -- normalize to "pho", should NOT create new row
    db.ingredient_ids(c, ["pho"])

    # Both should reference the same row_factory
    count = c.execute("SELECT COUNT(*) FROM ingredient").fetchone()[0]
    assert count == 1


def test_cascade():
    c = conn()

    # Save recipe with at least 1 ingredient
    recipe = db.save_recipe(c, {"title": "Test", "ingredients": [{"name": "garlic"}]})
    count = c.execute("SELECT COUNT(*) FROM recipe_ingredient").fetchone()[0]
    assert count == 1
    # Delete recipe
    db.delete_recipe(c, recipe)
    count = c.execute("SELECT COUNT(*) FROM recipe_ingredient").fetchone()[0]
    assert count == 0
