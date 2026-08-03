# seed/recipes.json -> db.save_recipe()
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

import db
import json

conn = db.connect()
recipes = json.load(open(os.path.join(HERE, "..", "seed", "recipes.json")))

for recipe in recipes:
	try:
		db.save_recipe(conn, recipe)
	except ValueError as e:
		print(f"Skipping: {e}")
conn.close()
