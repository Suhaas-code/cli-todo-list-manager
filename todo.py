#!/usr/bin/env python3
"""Dual-Mode To-Do List Manager (Tkinter + CLI) (GUI Version)."""

import json
import os
from datetime import datetime, date, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

DATA_FILE = "tasks.json"
DATE_FORMAT = "%Y-%m-%d"
PRIORITY_LEVELS = ["low", "medium", "high"]
FILTER_OPTIONS = ["all", "completed", "pending", "due-soon"]
CLI_CATEGORIES = ["General", "Work", "Personal", "Urgent"]
CLI_DEFAULT_CATEGORY = CLI_CATEGORIES[0]


def normalize_priority(value):
    if not value:
        return PRIORITY_LEVELS[1]
    value = value.lower()
    for level in PRIORITY_LEVELS:
        if level.lower() == value:
            return level
    return PRIORITY_LEVELS[1]


def load_tasks():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_tasks(tasks):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)


def next_task_id(tasks):
    if not tasks:
        return 1
    return max(task.get("id", 0) for task in tasks) + 1


def filter_tasks(tasks, mode):
    today = date.today()
    if mode == "completed":
        return [t for t in tasks if t.get("completed")]
    if mode == "pending":
        return [t for t in tasks if not t.get("completed")]
    if mode == "due-soon":
        soon = today + timedelta(days=3)
        result = []
        for t in tasks:
            due = t.get("due_date")
            if not due:
                continue
            try:
                d = datetime.strptime(due, DATE_FORMAT).date()
                if today <= d <= soon:
                    result.append(t)
            except Exception:
                pass
        return result
    return tasks


class Task:
    def __init__(self, task_id, title, description, category, priority=None, completed=False):
        self.id = task_id
        self.title = title
        self.description = description
        self.category = category
        self.priority = normalize_priority(priority)
        self.completed = completed
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "completed": self.completed,
            "created_at": self.created_at,
        }


class TodoGUI:
    def __init__(self, root, tasks, save_func):
        self.root = root
        self.tasks = tasks
        self.save = save_func
        self.root.title("To-Do List Manager")

        frame = ttk.Frame(root, padding=10)
        frame.pack(fill="both", expand=True)

        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=(0, 10))
        ttk.Label(controls, text="Filter:").pack(side="left")
        self.filter_var = tk.StringVar(value=FILTER_OPTIONS[0])
        filter_box = ttk.Combobox(controls, textvariable=self.filter_var, values=FILTER_OPTIONS, state="readonly", width=12)
        filter_box.pack(side="left", padx=(5, 0))
        filter_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh())

        self.tree = ttk.Treeview(frame, columns=("title", "desc", "cat", "priority", "status"), show="headings")
        for col in ["title", "desc", "cat", "priority", "status"]:
            self.tree.heading(col, text=col.capitalize())
        self.tree.pack(fill="both", expand=True)

        btns = ttk.Frame(frame)
        btns.pack(pady=10)
        ttk.Button(btns, text="Add", command=self.add_task).pack(side="left", padx=5)
        ttk.Button(btns, text="Edit", command=self.edit_task).pack(side="left", padx=5)
        ttk.Button(btns, text="Delete", command=self.delete_task).pack(side="left", padx=5)
        ttk.Button(btns, text="Update Status", command=self.update_status).pack(side="left", padx=5)
        ttk.Button(btns, text="Switch to CLI", command=self.switch_to_cli).pack(side="left", padx=5)

        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        selected_filter = getattr(self, "filter_var", None)
        mode = selected_filter.get() if selected_filter else FILTER_OPTIONS[0]
        filtered_dicts = filter_tasks([t.to_dict() for t in self.tasks], mode)
        tasks_by_id = {t.id: t for t in self.tasks}
        for task_info in filtered_dicts:
            tid = task_info.get("id")
            task = tasks_by_id.get(tid)
            if not task:
                continue
            self.tree.insert(
                "",
                "end",
                iid=str(task.id),
                values=(task.title, task.description, task.category, task.priority, "Done" if task.completed else "Pending"),
            )

    def add_task(self):
        title = simpledialog.askstring("Title", "Enter task title:")
        if not title:
            return
        desc = simpledialog.askstring("Description", "Enter description:") or ""
        cat = simpledialog.askstring("Category", "Enter category (Work/Personal/Urgent):") or "General"
        priority_input = simpledialog.askstring(
            "Priority",
            f"Enter priority ({', '.join(PRIORITY_LEVELS)}):",
            initialvalue=PRIORITY_LEVELS[1],
        )
        priority = normalize_priority(priority_input)
        new_task = Task(next_task_id([t.to_dict() for t in self.tasks]), title, desc, cat, priority)
        self.tasks.append(new_task)
        self.save([t.to_dict() for t in self.tasks])
        self.refresh()
        messagebox.showinfo("Task Added", f"Task '{title}' added successfully.")

    def get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "No task selected.")
            return None
        tid = int(sel[0])
        for t in self.tasks:
            if t.id == tid:
                return t
        return None

    def edit_task(self):
        t = self.get_selected()
        if not t:
            return
        t.title = simpledialog.askstring("Edit Title", "New title:", initialvalue=t.title) or t.title
        t.description = simpledialog.askstring("Edit Description", "New description:", initialvalue=t.description) or t.description
        t.category = simpledialog.askstring("Edit Category", "New category:", initialvalue=t.category) or t.category
        new_priority = simpledialog.askstring(
            "Edit Priority",
            f"New priority ({', '.join(PRIORITY_LEVELS)}):",
            initialvalue=t.priority,
        )
        t.priority = normalize_priority(new_priority)
        self.save([x.to_dict() for x in self.tasks])
        self.refresh()
        messagebox.showinfo("Task Updated", f"Task '{t.title}' updated successfully.")

    def delete_task(self):
        t = self.get_selected()
        if not t:
            return
        if messagebox.askyesno("Confirm", f"Delete '{t.title}'?"):
            self.tasks.remove(t)
            self.save([x.to_dict() for x in self.tasks])
            self.refresh()
            messagebox.showinfo("Task Deleted", f"Task '{t.title}' deleted.")

    def update_status(self):
        t = self.get_selected()
        if not t:
            return
        mark_complete = messagebox.askyesno(
            "Update Status",
            f"Mark '{t.title}' as completed? Selecting 'No' will mark it as pending.",
        )
        t.completed = mark_complete
        self.save([x.to_dict() for x in self.tasks])
        self.refresh()
        messagebox.showinfo(
            "Status Updated",
            f"Task '{t.title}' marked as {'completed' if t.completed else 'pending'}.",
        )

    def switch_to_cli(self):
        self.root.destroy()
        run_cli(self.tasks, self.save)


def run_cli(tasks, save):
    while True:
        print("\n1. Add Task")
        print("2. View Tasks")
        print("3. Mark Task Completed")
        print("4. Delete Task")
        print("5. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            title = input("Title: ")
            desc = input("Description: ")
            print(f"Available categories: {', '.join(CLI_CATEGORIES)}")
            cat_input = input(f"Category (default: {CLI_DEFAULT_CATEGORY}): ").strip()
            cat = CLI_DEFAULT_CATEGORY
            if cat_input:
                match = next((c for c in CLI_CATEGORIES if c.lower() == cat_input.lower()), None)
                if match:
                    cat = match
                else:
                    print(f"Unknown category. Using default '{CLI_DEFAULT_CATEGORY}'.")
            else:
                print(f"No category provided. Using default '{CLI_DEFAULT_CATEGORY}'.")
            print(f"Available priorities: {', '.join(PRIORITY_LEVELS)}")
            priority_input = input(f"Priority (default: {PRIORITY_LEVELS[1]}): ").strip()
            priority_value = priority_input if priority_input else PRIORITY_LEVELS[1]
            priority = normalize_priority(priority_value)
            t = Task(next_task_id([x.to_dict() for x in tasks]), title, desc, cat, priority)
            tasks.append(t)
            save([x.to_dict() for x in tasks])
            print(f"Task '{title}' added.")
        elif choice == "2":
            if not tasks:
                print("No tasks available.")
            else:
                for t in tasks:
                    print(
                        f"[{t.id}] {t.title} - {t.category} - {t.priority} - {'Done' if t.completed else 'Pending'}"
                    )
        elif choice == "3":
            try:
                tid = int(input("Task ID: "))
            except ValueError:
                print("Please enter a valid numeric task ID.")
                continue
            updated = False
            for t in tasks:
                if t.id == tid:
                    t.completed = True
                    updated = True
                    break
            if updated:
                save([x.to_dict() for x in tasks])
                print("Task marked as completed.")
            else:
                print("Task not found.")
        elif choice == "4":
            try:
                tid = int(input("Task ID: "))
            except ValueError:
                print("Please enter a valid numeric task ID.")
                continue
            before_count = len(tasks)
            tasks[:] = [t for t in tasks if t.id != tid]
            if len(tasks) < before_count:
                save([x.to_dict() for x in tasks])
                print("Task deleted.")
            else:
                print("Task not found.")
        elif choice == "5":
            save([x.to_dict() for x in tasks])
            print("Changes saved. Goodbye!")
            break
        else:
            print("Invalid option")


if __name__ == "__main__":
    tasks_data = load_tasks()
    tasks = []
    for d in tasks_data:
        title = d.get("title") or d.get("description") or "Untitled"
        desc = d.get("description") or ""
        cat = d.get("category") or "General"
        priority = normalize_priority(d.get("priority"))
        completed = d.get("completed", False)
        tasks.append(Task(d.get("id"), title, desc, cat, priority, completed))

    root = tk.Tk()
    gui = TodoGUI(root, tasks, save_tasks)
    root.mainloop()

