"""
File: restaurant_shift_manager.py
Advanced Restaurant Shift Manager
---------------------------------
Track start time, break time, and logout time for each staff member.
Automatically calculates total working hours and allows exporting to Excel.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import pandas as pd


class ShiftManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🍽 Restaurant Shift Manager v2")
        self.root.geometry("1000x600")
        self.root.resizable(False, False)

        self.staff_data = []
        self.setup_ui()

    # -------------------------------------------------
    def setup_ui(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Name:").grid(row=0, column=0, padx=5, pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.name_var, width=15).grid(row=0, column=1)

        ttk.Label(top, text="Role:").grid(row=0, column=2, padx=5)
        self.role_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.role_var, width=15).grid(row=0, column=3)

        ttk.Label(top, text="Department:").grid(row=0, column=4, padx=5)
        self.dept_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.dept_var, width=15).grid(row=0, column=5)

        ttk.Button(top, text="Add Staff", command=self.add_staff).grid(row=0, column=6, padx=10)

        # -------------------------------------------------
        columns = ["Name", "Role", "Department", "Start Time", "Break Start", "Break End", "Logout Time", "Total Hours"]
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        # -------------------------------------------------
        bottom = ttk.Frame(self.root, padding=10)
        bottom.pack(fill="x")

        ttk.Button(bottom, text="Mark Time", command=self.mark_time).pack(side="left", padx=5)
        ttk.Button(bottom, text="Export to Excel", command=self.export_to_excel).pack(side="left", padx=5)
        ttk.Button(bottom, text="Delete Staff", command=self.delete_staff).pack(side="left", padx=5)

    # -------------------------------------------------
    def add_staff(self):
        name = self.name_var.get().strip()
        role = self.role_var.get().strip()
        dept = self.dept_var.get().strip()

        if not name or not role or not dept:
            messagebox.showwarning("Missing Info", "Please fill all details.")
            return

        self.staff_data.append({
            "Name": name,
            "Role": role,
            "Department": dept,
            "Start": "",
            "Break Start": "",
            "Break End": "",
            "Logout": "",
            "Total": ""
        })
        self.tree.insert("", "end", values=(name, role, dept, "", "", "", "", ""))
        self.name_var.set("")
        self.role_var.set("")
        self.dept_var.set("")

    # -------------------------------------------------
    def mark_time(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a staff row to update.")
            return

        index = self.tree.index(selected[0])
        win = tk.Toplevel(self.root)
        win.title("Update Shift Times")
        win.geometry("400x400")

        staff = self.staff_data[index]
        ttk.Label(win, text=f"Update shift times for {staff['Name']}", font=("Arial", 11, "bold")).pack(pady=10)

        frame = ttk.Frame(win)
        frame.pack(pady=10)

        ttk.Label(frame, text="Start Time (HH:MM):").grid(row=0, column=0, sticky="w", pady=5)
        start_var = tk.StringVar(value=staff["Start"])
        ttk.Entry(frame, textvariable=start_var).grid(row=0, column=1)

        ttk.Label(frame, text="Break Start:").grid(row=1, column=0, sticky="w", pady=5)
        break_start_var = tk.StringVar(value=staff["Break Start"])
        ttk.Entry(frame, textvariable=break_start_var).grid(row=1, column=1)

        ttk.Label(frame, text="Break End:").grid(row=2, column=0, sticky="w", pady=5)
        break_end_var = tk.StringVar(value=staff["Break End"])
        ttk.Entry(frame, textvariable=break_end_var).grid(row=2, column=1)

        ttk.Label(frame, text="Logout Time:").grid(row=3, column=0, sticky="w", pady=5)
        logout_var = tk.StringVar(value=staff["Logout"])
        ttk.Entry(frame, textvariable=logout_var).grid(row=3, column=1)

        def save_times():
            staff["Start"] = start_var.get().strip()
            staff["Break Start"] = break_start_var.get().strip()
            staff["Break End"] = break_end_var.get().strip()
            staff["Logout"] = logout_var.get().strip()
            staff["Total"] = self.calculate_hours(staff)
            self.update_tree(index, staff)
            win.destroy()

        ttk.Button(win, text="Save", command=save_times).pack(pady=20)

    # -------------------------------------------------
    def calculate_hours(self, s):
        """Compute total working hours = (Logout - Start) - (Break End - Break Start)"""
        try:
            if not all([s["Start"], s["Logout"]]):
                return ""
            fmt = "%H:%M"
            start = datetime.strptime(s["Start"], fmt)
            end = datetime.strptime(s["Logout"], fmt)
            total = end - start
            if s["Break Start"] and s["Break End"]:
                b1 = datetime.strptime(s["Break Start"], fmt)
                b2 = datetime.strptime(s["Break End"], fmt)
                total -= (b2 - b1)
            hours = total.total_seconds() / 3600
            return f"{hours:.2f}"
        except Exception:
            return ""

    # -------------------------------------------------
    def update_tree(self, index, s):
        self.tree.delete(self.tree.get_children()[index])
        self.tree.insert("", index, values=(s["Name"], s["Role"], s["Department"],
                                            s["Start"], s["Break Start"], s["Break End"], s["Logout"], s["Total"]))

    # -------------------------------------------------
    def delete_staff(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a staff to delete.")
            return
        index = self.tree.index(selected[0])
        del self.staff_data[index]
        self.tree.delete(selected[0])

    # -------------------------------------------------
    def export_to_excel(self):
        if not self.staff_data:
            messagebox.showwarning("No Data", "No staff records to export.")
            return
        df = pd.DataFrame(self.staff_data)
        file = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            filetypes=[("Excel Files", "*.xlsx")])
        if file:
            df.to_excel(file, index=False)
            messagebox.showinfo("Exported", f"Shift data exported to:\n{file}")


# -------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = ShiftManagerApp(root)
    root.mainloop()