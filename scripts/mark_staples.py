import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

import db

with open(os.path.join(HERE, "..", "staples.txt")) as f:
    staple_names = [line.strip() for line in f if line.strip()]
    conn = db.connect()
    with conn:
        for name in staple_names:
            nk = db.norm_key(name)
            insert_status = conn.execute(
                "INSERT OR IGNORE INTO ingredient(name, name_key, is_staple) VALUES(?, ?, 1)",
                (
                    name,
                    nk,
                ),
            )
            if insert_status.rowcount == 1:
                print(f"Added: {name}")
            else:
                update_status = conn.execute(
                    "UPDATE ingredient SET is_staple = 1 WHERE name_key=?", (nk,)
                )
                print(f"Marked: {name}")
conn.close()
