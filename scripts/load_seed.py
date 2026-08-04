# seed/recipes.json -> db.save_recipe()
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

import json

import db

conn = db.connect()
with open(os.path.join(HERE, "..", "seed", "recipes.json")) as f:
    recipes = json.load(f)

for recipe in recipes:
    try:
        db.save_recipe(conn, recipe)
    except ValueError as e:
        print(f"Skipping: {e}")
conn.close()
