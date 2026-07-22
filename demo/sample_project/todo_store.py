"""Simple in-memory todo store."""

import json
from datetime import datetime

_TODOS = []


def add_todo(text):
    todo = {
        "id": len(_TODOS) + 1,
        "text": text,
        "done": False,
        "created": datetime.now().isoformat(),
    }
    _TODOS.append(todo)
    return todo


def remove_todo(todo_id):
    global _TODOS
    _TODOS = [t for t in _TODOS if t["id"] != todo_id]


def mark_done(todo_id):
    for t in _TODOS:
        if t["id"] == todo_id:
            t["done"] = True


def export_json():
    return json.dumps(_TODOS)
