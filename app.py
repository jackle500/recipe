"""FastAPI app, routes, Pydantic models. NO SQL."""

import sqlite3
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db
import suggest


class SuggestRequest(BaseModel):
    names: list[str]
    limit: int = 50


app = FastAPI()

"""Connect to database"""


def get_db():
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()


@app.get("/health")
async def health():
    return {"status": "ok"}


"""Get recipe wiht id, promp recipe page, return none if not found"""


@app.get("/api/recipes/{recipe_id}")
async def get_recipe(
    recipe_id: int, conn: Annotated[sqlite3.Connection, Depends(get_db)]
):
    recipe = db.load_recipe(conn, recipe_id)
    if recipe is None:
        return JSONResponse(status_code=404, content={"error": "not found"})
    return recipe


@app.get("/api/recipes")
async def list_recipes(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    limit: int = 50,
    offset: int = 0,
    q: str | None = None,
):
    return JSONResponse(status_code=501, content={"task": "3.4"})


@app.post("/api/recipes")
async def create_recipe():
    return JSONResponse(status_code=501, content={"task": "3.4"})


@app.put("/api/recipes/{recipe_id}")
async def update_recipe(recipe_id: int):
    return JSONResponse(status_code=501, content={"task": "3.4"})


@app.delete("/api/recipes/{recipe_id}")
async def delete_recipe(recipe_id: int):
    return JSONResponse(status_code=501, content={"task": "3.4"})


@app.get("/api/ingredients")
async def search_ingredients(q: str, limit: int = 20):
    return JSONResponse(status_code=501, content={"task": "3.2"})


@app.post("/api/suggest")
async def suggest_recipes(
    req: SuggestRequest, conn: Annotated[sqlite3.Connection, Depends(get_db)]
):
    return suggest.rank(conn, req.names, req.limit)


@app.post("/api/import/preview")
async def import_preview():
    return JSONResponse(status_code=501, content={"task": "2.6"})


@app.post("/api/invent")
async def invent():
    return JSONResponse(status_code=501, content={"task": "3.3"})


app.mount("/", StaticFiles(directory="static", html=True), name="static")
