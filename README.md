# cli-todo-list-manager

A lightweight command-line suite for tracking tasks with colored menus, priorities,
and due-date reminders backed by a JSON datastore.

## Getting Started
1. Ensure Python 3.9+ is installed.
2. Install dependencies (none beyond the standard library).
3. Run the CLI: `python todo_cli.py`.

## Features
- Add, edit, delete, and complete tasks with optional due dates and priorities.
- Filter views for completed, pending, or due-soon tasks.
- Persistent storage in `tasks.json`, reloaded automatically on start.

## Tips
- Use the due date format `YYYY-MM-DD`.
- Priorities accept `low`, `medium`, or `high`.
- Watch the suite summary after each action for totals and reminders.
