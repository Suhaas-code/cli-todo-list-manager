#!/usr/bin/env python3
"""Dual-Mode To-Do List Manager (Tkinter + CLI) (GUI Version)."""

import json
import os
from datetime import datetime, date, timedelta
import tkinter as tk
from tkinter import ttk, messagebox

DATA_FILE = "tasks.json"
DATE_FORMAT = "%Y-%m-%d"
PRIORITY_LEVELS = ["low", "medium", "high"]
DEFAULT_PRIORITY = PRIORITY_LEVELS[1]
FILTER_OPTIONS = ["all", "completed", "pending", "due-soon"]
CATEGORY_OPTIONS = ["General", "Work", "Personal", "Urgent"]
DEFAULT_CATEGORY = CATEGORY_OPTIONS[0]
PRIORITY_FILTER_OPTIONS = ["all"] + PRIORITY_LEVELS
CATEGORY_FILTER_OPTIONS = ["all"] + CATEGORY_OPTIONS
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


def normalize_priority(value):
    if not value:
        return DEFAULT_PRIORITY
    value = value.lower()
    for level in PRIORITY_LEVELS:
        if level.lower() == value:
            return level
    return DEFAULT_PRIORITY


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


class TaskFormDialog:
    def __init__(self, parent, title, categories, priorities, initial=None):
        self.parent = parent
        self.dialog_title = title
        self.categories = list(categories)
        self.priorities = list(priorities)
        self.initial = initial or {}
        current_category = self.initial.get("category")
        if current_category and current_category not in self.categories:
            self.categories.append(current_category)
        current_priority = self.initial.get("priority")
        if current_priority and current_priority not in self.priorities:
            self.priorities.append(current_priority)
        self.result = None
        self._build_dialog()
        self.parent.wait_window(self.top)

    def _build_dialog(self):
        self.top = tk.Toplevel(self.parent)
        self.top.title(self.dialog_title)
        self.top.transient(self.parent)
        self.top.grab_set()
        self.top.resizable(True, True)
        self.top.geometry("520x420")
        self.top.protocol("WM_DELETE_WINDOW", self.on_cancel)

        form = ttk.Frame(self.top, padding=15)
        form.pack(fill="both", expand=True)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Title:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.title_var = tk.StringVar(value=self.initial.get("title", ""))
        ttk.Entry(form, textvariable=self.title_var).grid(row=0, column=1, sticky="ew", pady=(0, 5))

        ttk.Label(form, text="Description:").grid(row=1, column=0, sticky="nw")
        self.desc_text = tk.Text(form, height=6, wrap="word")
        self.desc_text.grid(row=1, column=1, sticky="nsew", pady=5)
        form.rowconfigure(1, weight=1)
        if self.initial.get("description"):
            self.desc_text.insert("1.0", self.initial.get("description"))

        ttk.Label(form, text="Category:").grid(row=2, column=0, sticky="w", pady=5)
        self.category_var = tk.StringVar(value=self.initial.get("category", DEFAULT_CATEGORY))
        category_box = ttk.Combobox(form, textvariable=self.category_var, values=self.categories, state="readonly")
        category_box.grid(row=2, column=1, sticky="ew", pady=5)

        ttk.Label(form, text="Priority:").grid(row=3, column=0, sticky="w", pady=5)
        self.priority_var = tk.StringVar(value=self.initial.get("priority", DEFAULT_PRIORITY))
        priority_box = ttk.Combobox(form, textvariable=self.priority_var, values=self.priorities, state="readonly")
        priority_box.grid(row=3, column=1, sticky="ew", pady=5)

        button_row = ttk.Frame(self.top, padding=(15, 0, 15, 15))
        button_row.pack(fill="x")
        self.save_button = ttk.Button(button_row, text="Save", command=self.on_save)
        self.save_button.pack(side="right", padx=(0, 10))
        ttk.Button(button_row, text="Cancel", command=self.on_cancel).pack(side="right")

        self.top.bind("<Return>", lambda _event: self.on_save())
        self.top.bind("<Escape>", lambda _event: self.on_cancel())

    def on_save(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("Validation", "Title is required.")
            return
        description = self.desc_text.get("1.0", "end").strip()
        category = self.category_var.get().strip() or DEFAULT_CATEGORY
        priority = self.priority_var.get().strip() or DEFAULT_PRIORITY
        self.result = {
            "title": title,
            "description": description,
            "category": category,
            "priority": normalize_priority(priority),
        }
        self.top.destroy()

    def on_cancel(self):
        self.result = None
        self.top.destroy()


class StartupWindow:
    def __init__(self, root, tasks, save_func):
        self.root = root
        self.tasks = tasks
        self.save = save_func
        self.root.title("To-Do Manager")
        self.root.geometry("600x420")
        self.root.resizable(False, False)

        frame = ttk.Frame(root, padding=20)
        frame.pack(fill="both", expand=True)

        logo_label = tk.Label(frame, text=LOGO, font=("Courier", 10), justify="center")
        logo_label.pack(pady=(0, 15))
        tagline = "Choose how you want to get things done."
        ttk.Label(frame, text=tagline, anchor="center").pack(pady=(0, 15))

        buttons = ttk.Frame(frame)
        buttons.pack()
        ttk.Button(buttons, text="GUI", width=12, command=self.launch_gui).pack(side="left", padx=10)
        ttk.Button(buttons, text="CLI", width=12, command=self.launch_cli).pack(side="left", padx=10)

    def launch_gui(self):
        self.root.destroy()
        launch_gui_app(self.tasks, self.save)

    def launch_cli(self):
        self.root.destroy()
        run_cli(self.tasks, self.save)


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
        ttk.Label(controls, text="Filters", font=("Helvetica", 11, "bold")).pack(side="left", padx=(0, 10))
        ttk.Label(controls, text="Status:").pack(side="left")
        self.status_filter_var = tk.StringVar(value=FILTER_OPTIONS[0])
        status_box = ttk.Combobox(controls, textvariable=self.status_filter_var, values=FILTER_OPTIONS, state="readonly", width=12)
        status_box.pack(side="left", padx=(5, 0))
        status_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh())

        ttk.Label(controls, text="Priority:").pack(side="left", padx=(15, 0))
        self.priority_filter_var = tk.StringVar(value=PRIORITY_FILTER_OPTIONS[0])
        priority_box = ttk.Combobox(controls, textvariable=self.priority_filter_var, values=PRIORITY_FILTER_OPTIONS, state="readonly", width=12)
        priority_box.pack(side="left", padx=(5, 0))
        priority_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh())

        ttk.Label(controls, text="Category:").pack(side="left", padx=(15, 0))
        self.category_filter_var = tk.StringVar(value=CATEGORY_FILTER_OPTIONS[0])
        category_box = ttk.Combobox(controls, textvariable=self.category_filter_var, values=CATEGORY_FILTER_OPTIONS, state="readonly", width=12)
        category_box.pack(side="left", padx=(5, 0))
        category_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh())

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
        ttk.Button(btns, text="Clear All", command=self.clear_all_tasks).pack(side="left", padx=5)
        ttk.Button(btns, text="Switch to CLI", command=self.switch_to_cli).pack(side="left", padx=5)

        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        status_filter = getattr(self, "status_filter_var", None)
        mode = status_filter.get() if status_filter else FILTER_OPTIONS[0]
        filtered_dicts = filter_tasks([t.to_dict() for t in self.tasks], mode)

        priority_filter = getattr(self, "priority_filter_var", None)
        if priority_filter and priority_filter.get().lower() != "all":
            desired_priority = priority_filter.get()
            filtered_dicts = [
                t for t in filtered_dicts if normalize_priority(t.get("priority")) == desired_priority
            ]

        category_filter = getattr(self, "category_filter_var", None)
        if category_filter and category_filter.get().lower() != "all":
            desired_category = category_filter.get().lower()
            filtered_dicts = [
                t for t in filtered_dicts if (t.get("category") or "").lower() == desired_category
            ]
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
        dialog = TaskFormDialog(
            self.root,
            "Add Task",
            categories=CATEGORY_OPTIONS,
            priorities=PRIORITY_LEVELS,
        )
        if not dialog.result:
            return
        data = dialog.result
        new_task = Task(
            next_task_id([t.to_dict() for t in self.tasks]),
            data["title"],
            data["description"],
            data["category"],
            data["priority"],
        )
        self.tasks.append(new_task)
        self.save([t.to_dict() for t in self.tasks])
        self.refresh()
        messagebox.showinfo("Task Added", f"Task '{data['title']}' added successfully.")

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
        dialog = TaskFormDialog(
            self.root,
            "Edit Task",
            categories=CATEGORY_OPTIONS,
            priorities=PRIORITY_LEVELS,
            initial={
                "title": t.title,
                "description": t.description,
                "category": t.category,
                "priority": t.priority,
            },
        )
        if not dialog.result:
            return
        data = dialog.result
        t.title = data["title"]
        t.description = data["description"]
        t.category = data["category"]
        t.priority = data["priority"]
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

    def clear_all_tasks(self):
        if not self.tasks:
            messagebox.showinfo("Clear Tasks", "There are no tasks to clear.")
            return
        if messagebox.askyesno("Clear All Tasks", "This will permanently delete all tasks. Continue?"):
            self.tasks.clear()
            self.save([])
            self.refresh()
            messagebox.showinfo("Cleared", "All tasks have been removed.")


def launch_gui_app(tasks, save):
    gui_root = tk.Tk()
    TodoGUI(gui_root, tasks, save)
    gui_root.mainloop()


def _match_cli_option(value, options):
    if not value:
        return None
    normalized = value.strip().lower()
    for option in options:
        if option.lower() == normalized:
            return option
    if len(normalized) == 1:
        for option in options:
            if option[0].lower() == normalized:
                return option
    return None


def _prompt_cli_option(label, options, default_value, current_value=None):
    options_display = ", ".join(options)
    while True:
        print(f"Available {label}s: {options_display} (enter name or first letter)")
        if current_value is not None:
            response = input(f"{label.title()} (leave blank to keep '{current_value}'): ").strip()
            if not response:
                print(f"{label.title()} unchanged ({current_value}).")
                return current_value
        else:
            response = input(f"{label.title()} (default: {default_value}): ").strip()
            if not response:
                print(f"{label.title()} set to default '{default_value}'.")
                return default_value

        match = _match_cli_option(response, options)
        if match:
            return match

        print(f"Unknown {label}. Please choose from: {options_display}.")


def prompt_category_cli(current_value=None):
    return _prompt_cli_option("category", CATEGORY_OPTIONS, DEFAULT_CATEGORY, current_value)


def prompt_priority_cli(current_value=None):
    return _prompt_cli_option("priority", PRIORITY_LEVELS, DEFAULT_PRIORITY, current_value)


def show_startup(tasks, save):
    root = tk.Tk()
    StartupWindow(root, tasks, save)
    root.mainloop()


def edit_task_cli(tasks, save):
    try:
        tid = int(input("Task ID to edit: "))
    except ValueError:
        print("Please enter a valid numeric task ID.")
        return

    task = next((t for t in tasks if t.id == tid), None)
    if not task:
        print("Task not found.")
        return

    pending = {
        "title": task.title,
        "description": task.description,
        "category": task.category,
        "priority": task.priority,
    }

    while True:
        print(f"\nEditing Task [{task.id}]")
        print(f"1. Title: {pending['title']}")
        print(f"2. Description: {pending['description'] or '(empty)'}")
        print(f"3. Category: {pending['category']}")
        print(f"4. Priority: {pending['priority']}")
        print("S. Save changes")
        print("C. Cancel")
        choice = input("Select an option: ").strip().lower()

        if choice == "1":
            new_title = input("New title: ").strip()
            if new_title:
                pending["title"] = new_title
            else:
                print("Title unchanged.")
        elif choice == "2":
            new_desc = input("New description: ").strip()
            if new_desc:
                pending["description"] = new_desc
            else:
                print("Description unchanged.")
        elif choice == "3":
            pending["category"] = prompt_category_cli(current_value=pending["category"])
        elif choice == "4":
            pending["priority"] = prompt_priority_cli(current_value=pending["priority"])
        elif choice in {"s", "save"}:
            task.title = pending["title"]
            task.description = pending["description"]
            task.category = pending["category"]
            task.priority = pending["priority"]
            save([x.to_dict() for x in tasks])
            print("Task updated and saved.")
            return
        elif choice in {"c", "cancel"}:
            print("Edit cancelled. No changes saved.")
            return
        else:
            print("Invalid option. Please choose again.")


def run_cli(tasks, save):
    while True:
        print("\n1. Add Task")
        print("2. View Tasks")
        print("3. Edit Task")
        print("4. Mark Task Completed")
        print("5. Delete Task")
        print("6. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            title = input("Title: ")
            desc = input("Description: ")
            cat = prompt_category_cli()
            priority = prompt_priority_cli()
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
            edit_task_cli(tasks, save)
        elif choice == "4":
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
        elif choice == "5":
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
        elif choice == "6":
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

    show_startup(tasks, save_tasks)

