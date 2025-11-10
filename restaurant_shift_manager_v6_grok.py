"""
File: restaurant_shift_manager_v5.py
Description:
Advanced Restaurant Shift Manager v5
- Tabbed GUI: Staff Management & Shift View (time rows, staff columns)
- Interval selection (15 / 30 / 60 minutes)
- Import CSV (Name,Role,Department) and sample CSV download
- Add/Edit staff times (Start, Break Start, Break End, Logout) in HH:MM
- Dynamic time slots based on earliest start and latest logout
- Color-coded grid (Working=green, Break=yellow, Off=white)
- Export to Excel/CSV
- Working Hours (net: total shift minus break) and Break Hours calculations
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
import pandas as pd
import csv
import io
import os

TIME_FORMAT = "%H:%M"

# Color constants
COLOR_WORK = "#c6f6d5"   # light green
COLOR_BREAK = "#fefcbf"  # light yellow
COLOR_OFF = "#ffffff"    # white
HEADER_BG = "#e2e8f0"    # light gray


def parse_time_safe(tstr):
    tstr = (tstr or "").strip()
    if not tstr:
        return None
    try:
        return datetime.strptime(tstr, TIME_FORMAT)
    except Exception:
        return None


def fmt_time(dt):
    if dt is None:
        return ""
    return dt.strftime(TIME_FORMAT)


class StaffRecord:
    def __init__(self, name, role, dept, start="", break_start="", break_end="", logout=""):
        self.name = name
        self.role = role
        self.dept = dept
        self.start = start.strip()
        self.break_start = break_start.strip()
        self.break_end = break_end.strip()
        self.logout = logout.strip()

    def to_dict(self):
        return {
            "Name": self.name,
            "Role": self.role,
            "Department": self.dept,
            "Start": self.start,
            "Break Start": self.break_start,
            "Break End": self.break_end,
            "Logout": self.logout,
            "Working Hours": self.working_hours(),
            "Break Hours": self.break_hours()
        }

    def working_hours(self):
        try:
            s = parse_time_safe(self.start)
            e = parse_time_safe(self.logout)
            if not s or not e:
                return "0.00"
            total = e - s
            b1 = parse_time_safe(self.break_start)
            b2 = parse_time_safe(self.break_end)
            if b1 and b2 and b2 > b1:
                total -= (b2 - b1)
            hrs = total.total_seconds() / 3600
            return f"{hrs:.2f}"
        except Exception:
            return "0.00"

    def break_hours(self):
        try:
            b1 = parse_time_safe(self.break_start)
            b2 = parse_time_safe(self.break_end)
            if b1 and b2 and b2 > b1:
                hrs = (b2 - b1).total_seconds() / 3600
                return f"{hrs:.2f}"
            return "0.00"
        except Exception:
            return "0.00"


class ShiftManagerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("🍽 Restaurant Shift Manager v5")
        self.master.geometry("1100x700")

        # Data
        self.staff = []  # list of StaffRecord
        self.roles = ["Chef", "Combi", "Helper", "Waiter", "Cleaner", "Biller", "Captain", "Manager"]  # editable
        self.depts = ["Tandoor", "Service", "Housekeeping", "Indian", "Chinese", "Shawarma", "Admin"]  # editable

        # Settings
        self.interval_minutes = tk.IntVar(value=30)  # 15,30,60
        self.margin_slots = 1  # padding rows if needed

        # UI
        self.create_widgets()

    def create_widgets(self):
        # Top controls - Import / Sample / Export / Interval
        top = ttk.Frame(self.master, padding=8)
        top.pack(side="top", fill="x")

        ttk.Button(top, text="Import CSV", command=self.import_csv).pack(side="left", padx=4)
        ttk.Button(top, text="Download Sample CSV", command=self.download_sample_csv).pack(side="left", padx=4)
        ttk.Button(top, text="Export to Excel", command=self.export_excel).pack(side="left", padx=4)
        ttk.Button(top, text="Export to CSV", command=self.export_csv).pack(side="left", padx=4)

        ttk.Label(top, text="   Interval:").pack(side="left", padx=(20, 2))
        interval_cb = ttk.Combobox(top, values=[15, 30, 60], width=4, textvariable=self.interval_minutes, state="readonly")
        interval_cb.pack(side="left")
        interval_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_shift_view())

        ttk.Label(top, text="    ").pack(side="left")
        ttk.Button(top, text="Refresh View", command=self.refresh_shift_view).pack(side="left", padx=4)

        # Tabs
        tab_control = ttk.Notebook(self.master)
        tab_control.pack(fill="both", expand=True, padx=6, pady=6)

        # Tab 1: Staff Management
        self.tab_staff = ttk.Frame(tab_control)
        tab_control.add(self.tab_staff, text="Staff Management")

        # Tab 2: Shift View
        self.tab_view = ttk.Frame(tab_control)
        tab_control.add(self.tab_view, text="Shift View (Time on rows, Staff on columns)")

        self.build_staff_tab()
        self.build_shift_view_tab()

    # ---------------- Staff Tab ----------------
    def build_staff_tab(self):
        frm = self.tab_staff

        left = ttk.Frame(frm, padding=8)
        left.pack(side="left", fill="y")

        ttk.Label(left, text="Add / Edit Staff", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
        entry_frame = ttk.Frame(left)
        entry_frame.pack(anchor="w", pady=4)

        ttk.Label(entry_frame, text="Name:").grid(row=0, column=0, sticky="w")
        self.ent_name = ttk.Entry(entry_frame, width=20)
        self.ent_name.grid(row=0, column=1, padx=6, pady=2)

        ttk.Label(entry_frame, text="Role:").grid(row=1, column=0, sticky="w")
        self.role_var = tk.StringVar()
        self.role_cb = ttk.Combobox(entry_frame, values=self.roles, textvariable=self.role_var, width=18)
        self.role_cb.grid(row=1, column=1, padx=6, pady=2)

        ttk.Label(entry_frame, text="Department:").grid(row=2, column=0, sticky="w")
        self.dept_var = tk.StringVar()
        self.dept_cb = ttk.Combobox(entry_frame, values=self.depts, textvariable=self.dept_var, width=18)
        self.dept_cb.grid(row=2, column=1, padx=6, pady=2)

        # Times
        ttk.Label(entry_frame, text="Start (HH:MM):").grid(row=3, column=0, sticky="w")
        self.start_var = ttk.Entry(entry_frame, width=12)
        self.start_var.grid(row=3, column=1, padx=6, pady=2, sticky="w")

        ttk.Label(entry_frame, text="Break Start (HH:MM):").grid(row=4, column=0, sticky="w")
        self.bstart_var = ttk.Entry(entry_frame, width=12)
        self.bstart_var.grid(row=4, column=1, padx=6, pady=2, sticky="w")

        ttk.Label(entry_frame, text="Break End (HH:MM):").grid(row=5, column=0, sticky="w")
        self.bend_var = ttk.Entry(entry_frame, width=12)
        self.bend_var.grid(row=5, column=1, padx=6, pady=2, sticky="w")

        ttk.Label(entry_frame, text="Logout (HH:MM):").grid(row=6, column=0, sticky="w")
        self.logout_var = ttk.Entry(entry_frame, width=12)
        self.logout_var.grid(row=6, column=1, padx=6, pady=2, sticky="w")

        btn_frame = ttk.Frame(left)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="Add Staff", command=self.add_staff).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Update Selected", command=self.update_selected_staff).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected_staff).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Clear Inputs", command=self.clear_inputs).pack(side="left", padx=4)

        # Right: Treeview of staff
        right = ttk.Frame(frm, padding=8)
        right.pack(side="left", fill="both", expand=True)

        cols = ("Name", "Role", "Department", "Start", "Break Start", "Break End", "Logout", "Working Hours", "Break Hours")
        self.staff_tree = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.staff_tree.heading(c, text=c)
            w = 120 if c == "Name" else 90 if c in ["Working Hours", "Break Hours"] else 100
            self.staff_tree.column(c, width=w, anchor="center")
        self.staff_tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(right, orient="vertical", command=self.staff_tree.yview)
        self.staff_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="left", fill="y")

        # Bind selection
        self.staff_tree.bind("<<TreeviewSelect>>", self.on_staff_select)

    # ---------------- Shift View Tab ----------------
    def build_shift_view_tab(self):
        frm = self.tab_view

        # top of view tab: summary label
        summary_frame = ttk.Frame(frm, padding=6)
        summary_frame.pack(side="top", fill="x")
        self.summary_label = ttk.Label(summary_frame, text="Shift view summary will appear here.")
        self.summary_label.pack(side="left", anchor="w")

        # canvas area with scrollbars
        canvas_frame = ttk.Frame(frm)
        canvas_frame.pack(fill="both", expand=True, padx=6, pady=6)

        self.canvas = tk.Canvas(canvas_frame, background="white")
        self.v_scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.h_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        # frame inside canvas
        self.table_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.table_frame, anchor="nw")

        self.table_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind('<Configure>', self._on_canvas_configure)

        # initial message
        lbl = ttk.Label(self.table_frame, text="No data yet. Import staff or add staff in Staff Management tab.", padding=20)
        lbl.grid(row=0, column=0)

    def _on_canvas_configure(self, event):
        # adjust the canvas window width to fill the canvas (optional)
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    # ---------------- Staff operations ----------------
    def add_staff(self):
        name = self.ent_name.get().strip()
        role = self.role_var.get().strip()
        dept = self.dept_var.get().strip()
        start = self.start_var.get().strip()
        bstart = self.bstart_var.get().strip()
        bend = self.bend_var.get().strip()
        logout = self.logout_var.get().strip()

        if not name:
            messagebox.showwarning("Input error", "Please provide staff Name.")
            return
        if not role:
            messagebox.showwarning("Input error", "Please provide Role (use dropdown or type).")
            return
        if not dept:
            messagebox.showwarning("Input error", "Please provide Department (use dropdown or type).")
            return

        # Validate times (empty allowed)
        for t in (start, bstart, bend, logout):
            if t and not parse_time_safe(t):
                messagebox.showwarning("Time format", f"Invalid time format: {t}\nPlease use HH:MM")
                return

        rec = StaffRecord(name, role, dept, start, bstart, bend, logout)
        self.staff.append(rec)
        self._insert_staff_tree(rec)
        self.clear_inputs()
        self.refresh_shift_view()

    def _insert_staff_tree(self, rec):
        self.staff_tree.insert("", "end", values=(rec.name, rec.role, rec.dept, rec.start, rec.break_start, rec.break_end, rec.logout, rec.working_hours(), rec.break_hours()))

    def clear_inputs(self):
        self.ent_name.delete(0, tk.END)
        self.role_var.set("")
        self.dept_var.set("")
        self.start_var.delete(0, tk.END)
        self.bstart_var.delete(0, tk.END)
        self.bend_var.delete(0, tk.END)
        self.logout_var.delete(0, tk.END)

    def on_staff_select(self, event):
        sel = self.staff_tree.selection()
        if not sel:
            return
        idx = self.staff_tree.index(sel[0])
        rec = self.staff[idx]
        # populate inputs for editing
        self.ent_name.delete(0, tk.END); self.ent_name.insert(0, rec.name)
        self.role_var.set(rec.role)
        self.dept_var.set(rec.dept)
        self.start_var.delete(0, tk.END); self.start_var.insert(0, rec.start)
        self.bstart_var.delete(0, tk.END); self.bstart_var.insert(0, rec.break_start)
        self.bend_var.delete(0, tk.END); self.bend_var.insert(0, rec.break_end)
        self.logout_var.delete(0, tk.END); self.logout_var.insert(0, rec.logout)

    def update_selected_staff(self):
        sel = self.staff_tree.selection()
        if not sel:
            messagebox.showwarning("Select row", "Select a staff row to update.")
            return
        idx = self.staff_tree.index(sel[0])

        name = self.ent_name.get().strip()
        role = self.role_var.get().strip()
        dept = self.dept_var.get().strip()
        start = self.start_var.get().strip()
        bstart = self.bstart_var.get().strip()
        bend = self.bend_var.get().strip()
        logout = self.logout_var.get().strip()

        if not name:
            messagebox.showwarning("Input error", "Please provide staff Name.")
            return

        for t in (start, bstart, bend, logout):
            if t and not parse_time_safe(t):
                messagebox.showwarning("Time format", f"Invalid time format: {t}\nPlease use HH:MM")
                return

        rec = self.staff[idx]
        rec.name = name; rec.role = role; rec.dept = dept
        rec.start = start; rec.break_start = bstart; rec.break_end = bend; rec.logout = logout

        # refresh tree
        self.staff_tree.delete(sel[0])
        self.staff_tree.insert("", idx, values=(rec.name, rec.role, rec.dept, rec.start, rec.break_start, rec.break_end, rec.logout, rec.working_hours(), rec.break_hours()))
        self.clear_inputs()
        self.refresh_shift_view()

    def delete_selected_staff(self):
        sel = self.staff_tree.selection()
        if not sel:
            messagebox.showwarning("Select row", "Select a staff row to delete.")
            return
        idx = self.staff_tree.index(sel[0])
        confirm = messagebox.askyesno("Confirm", f"Delete staff: {self.staff[idx].name}?")
        if not confirm:
            return
        self.staff_tree.delete(sel[0])
        del self.staff[idx]
        self.refresh_shift_view()

    # ---------------- Import / Export ----------------
    def import_csv(self):
        file = filedialog.askopenfilename(title="Select CSV or Excel file", filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx;*.xls"), ("All", "*.*")])
        if not file:
            return
        try:
            df = None
            if file.lower().endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            expected = ["Name", "Role", "Department"]
            for c in expected:
                if c not in df.columns:
                    messagebox.showwarning("Format", f"CSV/Excel must contain columns: {expected}. Found: {list(df.columns)}")
                    return
            # Append rows (Start/Break/Logout empty, so hours default to 0.00)
            imported_count = 0
            for _, row in df.iterrows():
                nm = str(row.get("Name", "")).strip()
                if not nm:
                    continue
                role = str(row.get("Role", "")).strip()
                dept = str(row.get("Department", "")).strip()
                rec = StaffRecord(nm, role, dept)
                self.staff.append(rec)
                self._insert_staff_tree(rec)
                imported_count += 1
            messagebox.showinfo("Imported", f"Imported {imported_count} rows (rows without name skipped).")
            self.refresh_shift_view()
        except Exception as e:
            messagebox.showerror("Import error", str(e))

    def download_sample_csv(self):
        sample = io.StringIO()
        writer = csv.writer(sample)
        writer.writerow(["Name", "Role", "Department"])
        writer.writerow(["Rahul", "Chef", "Kitchen"])
        writer.writerow(["Asha", "Waiter", "Service"])
        writer.writerow(["Vikram", "Cleaner", "Housekeeping"])
        sample.seek(0)
        file = filedialog.asksaveasfilename(title="Save sample CSV", defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file:
            return
        with open(file, "w", newline="") as f:
            f.write(sample.read())
        messagebox.showinfo("Saved", f"Sample CSV saved to:\n{file}")

    def export_excel(self):
        if not self.staff:
            messagebox.showwarning("No data", "No staff data to export.")
            return
        file = filedialog.asksaveasfilename(title="Save Excel", defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not file:
            return
        df = pd.DataFrame([s.to_dict() for s in self.staff])
        df.to_excel(file, index=False)
        messagebox.showinfo("Exported", f"Saved to {file}")

    def export_csv(self):
        if not self.staff:
            messagebox.showwarning("No data", "No staff data to export.")
            return
        file = filedialog.asksaveasfilename(title="Save CSV", defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file:
            return
        df = pd.DataFrame([s.to_dict() for s in self.staff])
        df.to_csv(file, index=False)
        messagebox.showinfo("Exported", f"Saved to {file}")

    # ---------------- Shift View generation ----------------
    def refresh_shift_view(self):
        # Clear previous table_frame content
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        if not self.staff:
            ttk.Label(self.table_frame, text="No staff data. Add or import staff in Staff Management tab.", padding=20).grid(row=0, column=0)
            self.summary_label.config(text="No data")
            return

        # Determine earliest start and latest logout among staff
        starts = [parse_time_safe(s.start) for s in self.staff if s.start]
        logouts = [parse_time_safe(s.logout) for s in self.staff if s.logout]
        if not starts or not logouts:
            ttk.Label(self.table_frame, text="Please ensure each staff has Start and Logout times filled to view shift grid.", padding=20).grid(row=0, column=0)
            self.summary_label.config(text="Incomplete times")
            return

        earliest = min(starts)
        latest = max(logouts)
        # safety: if latest <= earliest, abort
        if latest <= earliest:
            ttk.Label(self.table_frame, text="Invalid time range (latest logout <= earliest start).", padding=20).grid(row=0, column=0)
            self.summary_label.config(text="Invalid time range")
            return

        interval = int(self.interval_minutes.get())
        # build time slots rows (start times of slots)
        slots = []
        cur = earliest
        while cur < latest:
            slots.append(cur)
            cur = cur + timedelta(minutes=interval)

        # Build header: first column empty, then staff names as columns
        # Header background
        header_style = ttk.Style()
        header_style.configure("Header.TLabel", background=HEADER_BG)

        # Column 0: Time label header
        tk.Label(self.table_frame, text="", bg=HEADER_BG, relief="ridge", width=14).grid(row=0, column=0, sticky="nsew")

        # Staff columns (show Name\nRole\nDept)
        for c_idx, s in enumerate(self.staff):
            txt = f"{s.name}\n{s.role}\n{s.dept}"
            lbl = tk.Label(self.table_frame, text=txt, bg=HEADER_BG, relief="ridge", width=18, justify="center")
            lbl.grid(row=0, column=c_idx + 1, sticky="nsew", padx=0, pady=0)

        # Fill time rows and cells
        active_counts = [0] * len(slots)

        for r_idx, slot_start in enumerate(slots):
            # Time label
            time_label = f"{slot_start.strftime(TIME_FORMAT)}"
            tk.Label(self.table_frame, text=time_label, relief="ridge", width=14, anchor="e").grid(row=r_idx + 1, column=0, sticky="nsew")

            for c_idx, s in enumerate(self.staff):
                # Determine state for this slot: Work / Break / Off
                st = parse_time_safe(s.start)
                en = parse_time_safe(s.logout)
                b1 = parse_time_safe(s.break_start)
                b2 = parse_time_safe(s.break_end)

                slot_end = slot_start + timedelta(minutes=interval)
                state = "off"
                # working if slot overlaps [st, en)
                if st and en and (slot_start < en and slot_end > st):
                    # check break overlap
                    in_break = False
                    if b1 and b2 and (slot_start < b2 and slot_end > b1):
                        in_break = True
                    if in_break:
                        state = "break"
                    else:
                        state = "work"

                # cell display
                if state == "work":
                    bg = COLOR_WORK
                    active_counts[r_idx] += 1
                elif state == "break":
                    bg = COLOR_BREAK
                else:
                    bg = COLOR_OFF

                cell = tk.Label(self.table_frame, text="", bg=bg, width=18, relief="ridge")
                cell.grid(row=r_idx + 1, column=c_idx + 1, sticky="nsew", padx=0, pady=0)

            # allow row expansion
            self.table_frame.grid_rowconfigure(r_idx + 1, weight=1)

        # summary
        total_slots = len(slots)
        summary_parts = [f"Slots: {total_slots} ({interval} min each)"]
        # show sample counts for first few slots
        if total_slots > 0:
            preview = ", ".join([f"{slots[i].strftime(TIME_FORMAT)}={active_counts[i]}" for i in range(min(6, total_slots))])
            summary_parts.append(f"Active counts preview: {preview}")
        self.summary_label.config(text="  |  ".join(summary_parts))

        # adjust grid sizing for columns
        for j in range(len(self.staff) + 1):
            self.table_frame.grid_columnconfigure(j, weight=0)

        # update scrollregion
        self.table_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # end class


if __name__ == "__main__":
    root = tk.Tk()
    app = ShiftManagerApp(root)
    root.mainloop()
