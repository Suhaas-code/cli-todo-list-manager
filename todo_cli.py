#!/usr/bin/env python3
"""Command-line To-Do List Manager."""

from __future__ import annotations

import json
import shutil
import os
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any

DATA_FILE = "tasks.json"
DATE_FORMAT = "%Y-%m-%d"
PRIORITY_LEVELS = {"low", "medium", "high"}

LOGO = r"""
███████████    ███████    ██████████      ███████    
░█░░░███░░░█  ███░░░░░███ ░░███░░░░███   ███░░░░░███ 
░   ░███  ░  ███     ░░███ ░███   ░░███ ███     ░░███
    ░███    ░███      ░███ ░███    ░███░███      ░███
    ░███    ░███      ░███ ░███    ░███░███      ░███
    ░███    ░░███     ███  ░███    ███ ░░███     ███ 
    █████    ░░░███████░   ██████████   ░░░███████░  
   ░░░░░       ░░░░░░░    ░░░░░░░░░░      ░░░░░░░   
"""


Task = Dict[str, Any]


def color(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def bold(text: str) -> str:
    return color(text, "1")


def section(text: str) -> str:
    return color(text, "36")


def success(text: str) -> str:
    return color(text, "32")


def warning(text: str) -> str:
    return color(text, "33")


def error(text: str) -> str:
    return color(text, "31")


def priority_color(priority: str) -> str:
    mapping = {
        "high": "31",
        "medium": "33",
        "low": "32",
    }
    return color(priority, mapping.get(priority, "37"))


def print_logo() -> None:
    width = shutil.get_terminal_size((80, 20)).columns
    for line in LOGO.splitlines():
        if line.strip():
            print(color(line.center(width), "35"))
    subtitle = "Command-Line To-Do Suite"
    print(bold(subtitle.center(width)))


def show_suite(tasks: List[Task]) -> None:
    total = len(tasks)
    completed = sum(1 for task in tasks if task.get("completed"))
    pending = total - completed
    due_soon = len(filter_tasks(tasks, "due-soon"))
    suite = (
        f"Suite → Total {bold(str(total))} | "
        f"Completed {success(str(completed))} | "
        f"Pending {warning(str(pending))} | "
        f"Due soon {color(str(due_soon), '35')}"
    )
    print(section(suite))


def load_tasks(file_path: str = DATA_FILE) -> List[Task]:
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        print(warning("Warning: Could not read tasks file. Starting with an empty list."))
        return []


def save_tasks(tasks: List[Task], file_path: str = DATA_FILE) -> None:
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2)
    except OSError as exc:
        print(error(f"Error saving tasks: {exc}"))


def next_task_id(tasks: List[Task]) -> int:
    if not tasks:
        return 1
    return max(task.get("id", 0) for task in tasks) + 1


def parse_date_input(raw: str) -> Optional[str]:
    raw = raw.strip()
    if not raw:
        return None
    try:
        parsed = datetime.strptime(raw, DATE_FORMAT).date()
        return parsed.strftime(DATE_FORMAT)
    except ValueError:
        print(error("Invalid date. Use YYYY-MM-DD."))
        return None


def prompt_priority(default: str = "medium") -> str:
    while True:
        raw = input(f"Priority [low/medium/high] (default {default}): ").strip().lower()
        if not raw:
            return default
        if raw in PRIORITY_LEVELS:
            return raw
        print(error("Invalid priority. Choose low, medium, or high."))


def display_tasks(tasks: List[Task]) -> None:
    if not tasks:
        print(warning("No tasks to show."))
        return
    for task in tasks:
        status = "✅" if task.get("completed") else "⏳"
        due = task.get("due_date") or "No due date"
        priority = task.get("priority", "medium")
        priority_display = priority_color(priority)
        desc = task.get("description")
        print(
            f"[{color(str(task.get('id')), '35')}] {status} {desc}"
            f" | due: {color(due, '36')} | priority: {priority_display}"
        )


def filter_tasks(tasks: List[Task], filter_option: str) -> List[Task]:
    today = date.today()
    if filter_option == "completed":
        return [task for task in tasks if task.get("completed")]
    if filter_option == "pending":
        return [task for task in tasks if not task.get("completed")]
    if filter_option == "due-soon":
        soon = today + timedelta(days=3)
        filtered: List[Task] = []
        for task in tasks:
            due_str = task.get("due_date")
            if not due_str:
                continue
            try:
                due = datetime.strptime(due_str, DATE_FORMAT).date()
            except ValueError:
                continue
            if today <= due <= soon:
                filtered.append(task)
        return filtered
    return tasks


def add_task(tasks: List[Task]) -> None:
    description = input("Task description: ").strip()
    if not description:
        print(error("Description cannot be empty."))
        return
    due_date = None
    while True:
        due_input = input("Due date (YYYY-MM-DD) [optional]: ")
        if not due_input.strip():
            break
        parsed = parse_date_input(due_input)
        if parsed:
            due_date = parsed
            break
    priority = prompt_priority()
    task = {
        "id": next_task_id(tasks),
        "description": description,
        "due_date": due_date,
        "completed": False,
        "priority": priority,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    tasks.append(task)
    save_tasks(tasks)
    print(success("Task added."))


def select_task(tasks: List[Task]) -> Optional[Task]:
    if not tasks:
        print(warning("No tasks available."))
        return None
    display_tasks(tasks)
    try:
        task_id = int(input("Enter task ID: "))
    except ValueError:
        print(error("Invalid ID."))
        return None
    for task in tasks:
        if task.get("id") == task_id:
            return task
    print(error("Task not found."))
    return None


def mark_task_completed(tasks: List[Task]) -> None:
    task = select_task(tasks)
    if not task:
        return
    task["completed"] = True
    save_tasks(tasks)
    print(success("Task marked as completed."))


def edit_task(tasks: List[Task]) -> None:
    task = select_task(tasks)
    if not task:
        return
    new_desc = input(f"New description (leave blank to keep '{task['description']}'): ").strip()
    if new_desc:
        task["description"] = new_desc
    while True:
        new_due = input(
            f"New due date in {DATE_FORMAT} (leave blank to keep {task.get('due_date') or 'none'}): "
        ).strip()
        if not new_due:
            break
        parsed = parse_date_input(new_due)
        if parsed is not None:
            task["due_date"] = parsed
            break
    change_priority = input("Change priority? (y/N): ").strip().lower()
    if change_priority == "y":
        task["priority"] = prompt_priority(task.get("priority", "medium"))
    save_tasks(tasks)
    print(success("Task updated."))


def delete_task(tasks: List[Task]) -> None:
    task = select_task(tasks)
    if not task:
        return
    confirm = input(f"Delete task '{task['description']}'? (y/N): ").strip().lower()
    if confirm == "y":
        tasks.remove(task)
        save_tasks(tasks)
        print(success("Task deleted."))
    else:
        print(warning("Deletion cancelled."))


def show_due_soon_reminders(tasks: List[Task]) -> None:
    due_soon = filter_tasks(tasks, "due-soon")
    if due_soon:
        print(section("\nReminder: Tasks due within 3 days:"))
        display_tasks(due_soon)
        print()


def view_tasks_menu(tasks: List[Task]) -> None:
    print(section("\nView Tasks:"))
    print("1. All tasks")
    print("2. Completed tasks")
    print("3. Pending tasks")
    print("4. Tasks due soon")
    choice = input("Choose an option: ").strip()
    filter_map = {
        "1": "all",
        "2": "completed",
        "3": "pending",
        "4": "due-soon",
    }
    filter_option = filter_map.get(choice, "all")
    filtered = filter_tasks(tasks, filter_option)
    display_tasks(filtered)


def main() -> None:
    tasks = load_tasks()
    print_logo()
    show_suite(tasks)
    print(section("Welcome to the Command-Line To-Do List Manager!"))
    show_due_soon_reminders(tasks)
    while True:
        print(section("\nMain Menu:"))
        print("1. Add task")
        print("2. View tasks")
        print("3. Mark task as completed")
        print("4. Edit task")
        print("5. Delete task")
        print("6. Exit")
        choice = input("Select an option: ").strip()
        if choice == "1":
            add_task(tasks)
        elif choice == "2":
            view_tasks_menu(tasks)
        elif choice == "3":
            mark_task_completed(tasks)
        elif choice == "4":
            edit_task(tasks)
        elif choice == "5":
            delete_task(tasks)
        elif choice == "6":
            print(success("Goodbye!"))
            break
        else:
            print(error("Invalid option. Please choose 1-6."))
        show_suite(tasks)


if __name__ == "__main__":
    main()
