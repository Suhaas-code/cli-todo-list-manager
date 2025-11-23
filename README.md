# cli-todo-list-manager

A dual-mode to-do manager that bundles a Tkinter GUI and the original
colorful CLI into a single script backed by a shared JSON datastore.

## Running the App
- GUI mode (default): `python todo.py`
- CLI mode: `python todo.py -cli`

## Features
- **Shared storage**: both modes read/write `tasks.json`.
- **CLI**: colored menus, add/edit/delete/complete, filters, due reminders.
- **GUI**: task table, filters (status/category/priority), add/edit dialogs,
  due-soon panel, inline summary, and a "Switch to CLI" button.

## Notes
- Python 3.9+ with Tkinter (ships with CPython) is required.
- Tasks accept optional due dates (`YYYY-MM-DD`), priorities (low/medium/high),
  and categories (General, Work, Personal, Errands, Study).
- Everything lives in `todo.py` for easy sharing.
