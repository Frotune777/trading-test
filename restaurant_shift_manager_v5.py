#!/usr/bin/env python3
"""
restaurant_shift_manager_v6_5.py
Advanced Restaurant Shift Manager v6.5 - Fixed Shift View Horizontal Scrollbar
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta, date, time as dtime
import pandas as pd
import csv
import io

TIME_FORMAT = "%H:%M"

# Colors
COLOR_WORK = "#c6f6d5"   # light green
COLOR_BREAK = "#fefcbf"  # light yellow
COLOR_OFF = "#ffffff"    # white
HEADER_BG = "#e2e8f0"    # light gray

def generate_time_options(granularity_minutes=15):
    """Generates time options in HH:MM format for comboboxes."""
    options = []
    cur = datetime.combine(date.today(), dtime(0, 0))
    end_time = cur + timedelta(days=1)
    while cur < end_time:
        options.append(cur.strftime(TIME_FORMAT))
        cur += timedelta(minutes=granularity_minutes)
    return options

TIME_OPTIONS = generate_time_options(15)

def parse_time_str(tstr):
    """Safely parses HH:MM string to a datetime.time object."""
    tstr = (tstr or "").strip()
    if not tstr:
        return None
    try:
        return datetime.strptime(tstr, TIME_FORMAT).time()
    except Exception:
        return None

def to_datetime_today(t):
    """Converts datetime.time to a datetime object on the current date."""
    if t is None:
        return None
    return datetime.combine(date.today(), t)

def normalize_interval_minutes(v):
    """Ensures interval is 15, 30, or 60 minutes."""
    try:
        iv = int(v)
        if iv in (15, 30, 60):
            return iv
    except:
        pass
    return 30

class StaffRecord:
    def __init__(self, name, role, dept, start="", break_start="", break_end="", logout=""):
        self.name = name
        self.role = role
        self.dept = dept
        self.start = start.strip()
        self.break_start = break_start.strip()
        self.break_end = break_end.strip()
        self.logout = logout.strip()

    def get_datetimes(self):
        """
        Calculates adjusted datetimes for overnight shifts.
        Returns: (start_dt, logout_dt, break_start_dt, break_end_dt)
        """
        s = parse_time_str(self.start)
        e = parse_time_str(self.logout)
        if s is None or e is None:
            return None
        sdt = to_datetime_today(s)
        edt = to_datetime_today(e)
        
        # Adjust for overnight shift: if logout <= start, assume logout is next day
        if edt <= sdt:
            edt += timedelta(days=1)
            
        # breaks
        b1 = parse_time_str(self.break_start) if self.break_start else None
        b2 = parse_time_str(self.break_end) if self.break_end else None
        
        bd1 = to_datetime_today(b1) if b1 else None
        bd2 = to_datetime_today(b2) if b2 else None
        
        # Adjust break for overnight (if break crosses midnight)
        if bd1 and bd2 and bd2 <= bd1:
            bd2 += timedelta(days=1)
            
        # If break is valid but starts before main shift
        if bd1 and bd1 < sdt:
            bd1 += timedelta(days=1)
            if bd2 and bd2 <= bd1:
                bd2 += timedelta(days=1)

        return (sdt, edt, bd1, bd2)

    def working_hours(self):
        try:
            dt = self.get_datetimes()
            if not dt:
                return ""
            sdt, edt, bd1, bd2 = dt
            total = (edt - sdt)
            if bd1 and bd2:
                # Only subtract if break end is after break start
                total -= max(timedelta(0), (bd2 - bd1))
            secs = total.total_seconds()
            if secs < 0:
                return ""
            return f"{secs/3600:.2f}"
        except:
            return ""

    def break_hours(self):
        try:
            if not self.break_start or not self.break_end:
                return "0.00"
            b1 = parse_time_str(self.break_start)
            b2 = parse_time_str(self.break_end)
            if not b1 or not b2:
                return "0.00"
            
            bd1 = to_datetime_today(b1)
            bd2 = to_datetime_today(b2)
            
            if bd2 <= bd1:
                bd2 += timedelta(days=1)
            
            secs = (bd2 - bd1).total_seconds()
            return f"{secs/3600:.2f}"
        except:
            return "0.00"

    def total_hours(self):
        try:
            dt = self.get_datetimes()
            if not dt:
                return ""
            sdt, edt, _, _ = dt
            secs = (edt - sdt).total_seconds()
            return f"{secs/3600:.2f}"
        except:
            return ""

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
            "Break Hours": self.break_hours(),
            "Total Hours": self.total_hours()
        }

class ShiftManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🍽 Restaurant Shift Manager v6.5")
        self.root.geometry("1400x780") 
        self.staff = []
        self.roles = ["Chef","Combi","Helper","Waiter","Cleaner","Biller","Captain","Manager"]
        self.depts = ["Tandoor","Service","Housekeeping","Indian","Chinese","Shawarma","Admin"]
        self.interval_var = tk.IntVar(value=30)
        
        # Staff Management Filter variables
        self.filter_name_var = tk.StringVar()
        self.filter_role_var = tk.StringVar()
        self.filter_dept_var = tk.StringVar()
        
        # Shift View Filter variables
        self.view_role_var = tk.StringVar()
        self.view_dept_var = tk.StringVar()
        
        self.create_ui()

    def create_ui(self):
        top = ttk.Frame(self.root, padding=6)
        top.pack(side="top", fill="x")
        ttk.Button(top, text="Import CSV", command=self.import_csv).pack(side="left", padx=4)
        ttk.Button(top, text="Download Sample CSV", command=self.download_sample_csv).pack(side="left", padx=4)
        ttk.Button(top, text="Export to Excel", command=self.export_excel).pack(side="left", padx=4)
        ttk.Button(top, text="Export to CSV", command=self.export_csv).pack(side="left", padx=4)
        ttk.Label(top, text="   Interval:").pack(side="left", padx=(12,2))
        cb = ttk.Combobox(top, values=[15,30,60], width=4, textvariable=self.interval_var, state="readonly")
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_view())
        ttk.Button(top, text="Refresh View", command=self.refresh_view).pack(side="left", padx=6)

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=6, pady=6)

        self.tab_staff = ttk.Frame(notebook)
        self.tab_view = ttk.Frame(notebook)
        self.tab_stats = ttk.Frame(notebook)
        notebook.add(self.tab_staff, text="Staff Management")
        notebook.add(self.tab_view, text="Shift View")
        notebook.add(self.tab_stats, text="Statistics")

        self.build_staff_tab()
        self.build_view_tab()
        self.build_stats_tab()
        
        self.filter_staff_tree()

    def build_staff_tab(self):
        frm = self.tab_staff
        left = ttk.Frame(frm, padding=8)
        left.pack(side="left", fill="y")
        
        # --- Input/Edit Panel ---
        ttk.Label(left, text="Add / Edit Staff", font=("Arial",11,"bold")).pack(anchor="w")
        ef = ttk.Frame(left)
        ef.pack(anchor="w", pady=6)

        ttk.Label(ef, text="Name:").grid(row=0, column=0, sticky="w")
        self.name_e = ttk.Entry(ef, width=22); self.name_e.grid(row=0, column=1, pady=2)
        ttk.Label(ef, text="Role:").grid(row=1, column=0, sticky="w")
        self.role_cb = ttk.Combobox(ef, values=self.roles, width=20); self.role_cb.grid(row=1, column=1, pady=2)
        ttk.Label(ef, text="Department:").grid(row=2, column=0, sticky="w")
        self.dept_cb = ttk.Combobox(ef, values=self.depts, width=20); self.dept_cb.grid(row=2, column=1, pady=2)

        ttk.Label(ef, text="Start (HH:MM):").grid(row=3, column=0, sticky="w")
        self.start_cb = ttk.Combobox(ef, values=TIME_OPTIONS, width=12, state="readonly"); self.start_cb.grid(row=3, column=1, pady=2, sticky="w")
        ttk.Label(ef, text="Break Start (HH:MM):").grid(row=4, column=0, sticky="w")
        self.bstart_cb = ttk.Combobox(ef, values=TIME_OPTIONS, width=12, state="readonly"); self.bstart_cb.grid(row=4, column=1, pady=2, sticky="w")
        ttk.Label(ef, text="Break End (HH:MM):").grid(row=5, column=0, sticky="w")
        self.bend_cb = ttk.Combobox(ef, values=TIME_OPTIONS, width=12, state="readonly"); self.bend_cb.grid(row=5, column=1, pady=2, sticky="w")
        ttk.Label(ef, text="Logout (HH:MM):").grid(row=6, column=0, sticky="w")
        self.logout_cb = ttk.Combobox(ef, values=TIME_OPTIONS, width=12, state="readonly"); self.logout_cb.grid(row=6, column=1, pady=2, sticky="w")

        btnf = ttk.Frame(left); btnf.pack(pady=8)
        ttk.Button(btnf, text="Add Staff", command=self.add_staff).pack(side="left", padx=4)
        ttk.Button(btnf, text="Update Selected", command=self.update_selected).pack(side="left", padx=4)
        ttk.Button(btnf, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=4)
        ttk.Button(btnf, text="Clear Inputs", command=self.clear_inputs).pack(side="left", padx=4)
        
        # --- Staff List Panel (Treeview) ---
        right = ttk.Frame(frm, padding=8)
        right.pack(side="left", fill="both", expand=True)

        # Filter controls
        filter_frame = ttk.Frame(right); filter_frame.pack(fill="x", pady=(0, 5))
        
        ttk.Label(filter_frame, text="Filter:").pack(side="left", padx=(0, 10))
        
        self.filter_name_e = ttk.Entry(filter_frame, textvariable=self.filter_name_var, width=15)
        self.filter_name_e.pack(side="left", padx=4)
        ttk.Label(filter_frame, text="Name").pack(side="left")
        self.filter_name_e.bind("<KeyRelease>", lambda e: self.filter_staff_tree())
        
        self.filter_role_cb = ttk.Combobox(filter_frame, values=[""] + self.roles, textvariable=self.filter_role_var, width=12, state="readonly")
        self.filter_role_cb.pack(side="left", padx=4)
        ttk.Label(filter_frame, text="Role").pack(side="left")
        self.filter_role_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_staff_tree())
        
        self.filter_dept_cb = ttk.Combobox(filter_frame, values=[""] + self.depts, textvariable=self.filter_dept_var, width=15, state="readonly")
        self.filter_dept_cb.pack(side="left", padx=4)
        ttk.Label(filter_frame, text="Dept").pack(side="left")
        self.filter_dept_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_staff_tree())
        
        ttk.Button(filter_frame, text="Clear Filters", command=self.clear_filters).pack(side="left", padx=10)


        # Treeview with Scrollbars
        tree_frame = ttk.Frame(right)
        tree_frame.pack(fill="both", expand=True)
        
        cols = ("Name","Role","Department","Start","Break Start","Break End","Logout","Working Hrs","Break Hrs","Total Hrs")
        self.staff_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=20)
        
        # Define column properties for better readability
        col_widths = {"Name": 140, "Role": 100, "Department": 100, 
                      "Start": 70, "Break Start": 90, "Break End": 90, "Logout": 70, 
                      "Working Hrs": 85, "Break Hrs": 85, "Total Hrs": 85}
                      
        for c in cols:
            self.staff_tree.heading(c, text=c)
            self.staff_tree.column(c, width=col_widths.get(c, 100), anchor="center")
            
        # Vertical Scrollbar
        sb_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.staff_tree.yview)
        # Horizontal Scrollbar
        sb_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.staff_tree.xview)
        
        self.staff_tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        
        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self.staff_tree.pack(fill="both", expand=True, side="left")
        
        self.staff_tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def filter_staff_tree(self):
        # Clear existing view
        for item in self.staff_tree.get_children():
            self.staff_tree.delete(item)
            
        name_filter = self.filter_name_var.get().strip().lower()
        role_filter = self.filter_role_var.get().strip().lower()
        dept_filter = self.filter_dept_var.get().strip().lower()
        
        # Populate with filtered data
        for rec in self.staff:
            name_match = not name_filter or name_filter in rec.name.lower()
            role_match = not role_filter or role_filter == rec.role.lower()
            dept_match = not dept_filter or dept_filter == rec.dept.lower()
            
            if name_match and role_match and dept_match:
                # Store the index/ID in the treeview for lookup
                self.staff_tree.insert("", "end", values=(rec.name, rec.role, rec.dept, rec.start, rec.break_start, rec.break_end, rec.logout, rec.working_hours(), rec.break_hours(), rec.total_hours()))

    def clear_filters(self):
        self.filter_name_var.set("")
        self.filter_role_var.set("")
        self.filter_dept_var.set("")
        self.filter_staff_tree() 

    def insert_staff_tree(self, rec):
        self.filter_staff_tree()

    def add_staff(self):
        name = self.name_e.get().strip()
        role = self.role_cb.get().strip()
        dept = self.dept_cb.get().strip()
        start = self.start_cb.get().strip()
        bstart = self.bstart_cb.get().strip()
        bend = self.bend_cb.get().strip()
        logout = self.logout_cb.get().strip()
        if not name or not role or not dept:
            messagebox.showwarning("Missing", "Please fill Name, Role, Department.")
            return
        for t in (start, bstart, bend, logout):
            if t and parse_time_str(t) is None:
                messagebox.showwarning("Time", f"Invalid time: {t}")
                return
        rec = StaffRecord(name, role, dept, start, bstart, bend, logout)
        s = parse_time_str(start); e = parse_time_str(logout)
        if s and e and (e <= s):
            messagebox.showinfo("Overnight shift", f"Logout {logout} is earlier or equal to Start {start}. Treated as next day logout.")
        
        if any(r.name == name for r in self.staff):
            messagebox.showerror("Error", f"Staff member with name '{name}' already exists.")
            return

        self.staff.append(rec)
        self.filter_staff_tree() 
        self.clear_inputs()
        self.refresh_view()

    def clear_inputs(self):
        self.name_e.delete(0, tk.END)
        self.role_cb.set("")
        self.dept_cb.set("")
        self.start_cb.set("")
        self.bstart_cb.set("")
        self.bend_cb.set("")
        self.logout_cb.set("")

    def on_tree_select(self, ev):
        sel = self.staff_tree.selection()
        if not sel: return
        
        selected_values = self.staff_tree.item(sel[0], 'values')
        if not selected_values: return
        
        selected_name = selected_values[0]
        rec = next((r for r in self.staff if r.name == selected_name), None)
        
        if rec:
            self.name_e.delete(0,tk.END); self.name_e.insert(0, rec.name)
            self.role_cb.set(rec.role); self.dept_cb.set(rec.dept)
            self.start_cb.set(rec.start); self.bstart_cb.set(rec.break_start)
            self.bend_cb.set(rec.break_end); self.logout_cb.set(rec.logout)

    def update_selected(self):
        sel = self.staff_tree.selection()
        if not sel:
            messagebox.showwarning("Select","Select a staff to update.")
            return
        
        old_name = self.staff_tree.item(sel[0], 'values')[0]
        rec = next((r for r in self.staff if r.name == old_name), None)
        if not rec:
            messagebox.showerror("Error", "Staff record not found in data.")
            return

        name = self.name_e.get().strip(); role = self.role_cb.get().strip(); dept = self.dept_cb.get().strip()
        start = self.start_cb.get().strip(); bstart = self.bstart_cb.get().strip(); bend = self.bend_cb.get().strip(); logout = self.logout_cb.get().strip()
        
        if not name or not role or not dept:
            messagebox.showwarning("Missing", "Please fill Name, Role, Department.")
            return
        for t in (start, bstart, bend, logout):
            if t and parse_time_str(t) is None:
                messagebox.showwarning("Time", f"Invalid time: {t}")
                return
        
        # Check for name change resulting in duplicate
        if name != old_name and any(r.name == name for r in self.staff):
            messagebox.showerror("Error", f"Staff member with new name '{name}' already exists.")
            return
            
        # Update the record object
        rec.name, rec.role, rec.dept = name, role, dept
        rec.start, rec.break_start, rec.break_end, rec.logout = start, bstart, bend, logout
        
        self.filter_staff_tree() 
        self.clear_inputs()
        self.refresh_view()

    def delete_selected(self):
        sel = self.staff_tree.selection()
        if not sel:
            return
        
        name_to_delete = self.staff_tree.item(sel[0], 'values')[0]
        confirm = messagebox.askyesno("Confirm", f"Delete {name_to_delete}?")
        if not confirm:
            return
            
        self.staff = [r for r in self.staff if r.name != name_to_delete]
        
        self.filter_staff_tree() 
        self.refresh_view()
        
    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV","*.csv"),("Excel","*.xlsx;*.xls"),("All","*.*")])
        if not path: return
        try:
            if path.lower().endswith(".csv"):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
            expected = ["Name","Role","Department"]
            for c in expected:
                if c not in df.columns:
                    messagebox.showwarning("Format", f"CSV/Excel must contain: {expected}")
                    return
            
            imported_count = 0
            existing_names = {s.name for s in self.staff}
            
            for _, row in df.iterrows():
                name = str(row.get("Name","")).strip()
                if not name: continue
                
                if name in existing_names:
                    messagebox.showwarning("Duplicate", f"Staff '{name}' skipped: already exists. Delete or modify existing record manually.")
                    continue
                    
                role = str(row.get("Role","")).strip()
                dept = str(row.get("Department","")).strip()
                start = str(row.get("Start","")).strip() if "Start" in df.columns else ""
                bstart = str(row.get("Break Start","")).strip() if "Break Start" in df.columns else ""
                bend = str(row.get("Break End","")).strip() if "Break End" in df.columns else ""
                logout = str(row.get("Logout","")).strip() if "Logout" in df.columns else ""
                rec = StaffRecord(name, role, dept, start, bstart, bend, logout)
                self.staff.append(rec)
                imported_count += 1
                
            messagebox.showinfo("Imported", f"Import complete. Added {imported_count} new staff.")
            self.filter_staff_tree()
            self.refresh_view()
        except Exception as e:
            messagebox.showerror("Import error", str(e))

    def download_sample_csv(self):
        sample = io.StringIO()
        w = csv.writer(sample)
        w.writerow(["Name","Role","Department","Start","Break Start","Break End","Logout"])
        w.writerow(["Rahul","Chef","Kitchen","09:00","13:00","13:30","18:00"])
        w.writerow(["Asha","Waiter","Service","08:00","12:00","12:30","16:30"])
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="sample_staff.csv")
        if not path: return
        with open(path, "w", newline="") as f:
            f.write(sample.getvalue())
        messagebox.showinfo("Saved", f"Sample saved: {path}")

    def export_excel(self):
        if not self.staff:
            messagebox.showwarning("No data", "No staff to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if not path: return
        df = pd.DataFrame([s.to_dict() for s in self.staff])
        df.to_excel(path, index=False)
        messagebox.showinfo("Saved", f"Excel saved: {path}")

    def export_csv(self):
        if not self.staff:
            messagebox.showwarning("No data", "No staff to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path: return
        df = pd.DataFrame([s.to_dict() for s in self.staff])
        df.to_csv(path, index=False)
        messagebox.showinfo("Saved", f"CSV saved: {path}")
        
    # --- Shift View Tab Logic ---

    def build_view_tab(self):
        frm = self.tab_view
        top = ttk.Frame(frm); top.pack(side="top", fill="x", pady=4)
        
        # Shift View Filters
        ttk.Label(top, text="Filter By:").pack(side="left", padx=(0, 5))
        
        self.view_role_cb = ttk.Combobox(top, values=["All"] + self.roles, textvariable=self.view_role_var, width=12, state="readonly")
        self.view_role_cb.set("All")
        self.view_role_cb.pack(side="left", padx=4)
        ttk.Label(top, text="Role").pack(side="left")
        self.view_role_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_view())
        
        self.view_dept_cb = ttk.Combobox(top, values=["All"] + self.depts, textvariable=self.view_dept_var, width=15, state="readonly")
        self.view_dept_cb.set("All")
        self.view_dept_cb.pack(side="left", padx=4)
        ttk.Label(top, text="Dept").pack(side="left")
        self.view_dept_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_view())

        # Other controls
        ttk.Label(top, text="   Interval:").pack(side="left", padx=(12,2))
        cb = ttk.Combobox(top, values=[15,30,60], width=4, textvariable=self.interval_var, state="readonly")
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_view())
        
        ttk.Button(top, text="Refresh Grid", command=self.refresh_view).pack(side="left", padx=6)
        self.summary_lbl = ttk.Label(top, text="Summary will appear here."); self.summary_lbl.pack(side="left", padx=12)
        
        canvas_frame = ttk.Frame(frm); canvas_frame.pack(fill="both", expand=True, padx=6, pady=6)
        
        self.canvas = tk.Canvas(canvas_frame, background="white")
        self.vbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview); self.vbar.pack(side="right", fill="y")
        self.hbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview); self.hbar.pack(side="bottom", fill="x")
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)
        
        self.table_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0,0), window=self.table_frame, anchor="nw")
        
        # Binding the internal frame to update the scroll region whenever it changes size
        self.table_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # This is for horizontal resizing of the window
        # NOTE: We remove the width=e.width binding as it conflicts with horizontal scrolling
        # self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

    def refresh_view(self):
        # 1. Clear existing content
        for w in self.table_frame.winfo_children():
            w.destroy()
            
        # 2. Apply Filters
        role_filter = self.view_role_var.get().strip()
        dept_filter = self.view_dept_var.get().strip()
        
        filtered_staff = [s for s in self.staff if 
            (role_filter == "All" or s.role == role_filter) and
            (dept_filter == "All" or s.dept == dept_filter)]
            
        staff_with_times = [s for s in filtered_staff if s.get_datetimes()]

        if not staff_with_times:
            msg = "No staff data meets the filters or has valid start/logout times."
            ttk.Label(self.table_frame, text=msg).grid(row=0, column=0, padx=10, pady=10)
            self.summary_lbl.config(text="No valid data")
            self.refresh_stats_tab()
            
            # Crucial: Update scrollregion even for an empty table to reset scrollbars
            self.table_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            return
            
        # 3. Determine Time Range
        starts = [dt[0] for s in staff_with_times if (dt:=s.get_datetimes())]
        logouts = [dt[1] for s in staff_with_times if (dt:=s.get_datetimes())]
        
        earliest = min(starts)
        latest = max(logouts)
        
        if latest <= earliest:
            ttk.Label(self.table_frame, text="Invalid time range after normalization.").grid(row=0, column=0, padx=10, pady=10)
            self.summary_lbl.config(text="Invalid range")
            self.refresh_stats_tab()
            self.table_frame.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            return
            
        # 4. Generate Time Slots
        interval = normalize_interval_minutes(self.interval_var.get())
        slots = []
        cur = earliest
        while cur < latest:
            slots.append(cur)
            cur += timedelta(minutes=interval)
            
        # 5. Draw Header
        # Column 0: Time Slot
        tk.Label(self.table_frame, text="Time Slot", bg=HEADER_BG, relief="ridge", width=16).grid(row=0, column=0, sticky="nsew")
        
        # Staff column headers
        for cidx, s in enumerate(staff_with_times):
            txt = f"{s.name}\n{s.role}\n{s.dept}"
            tk.Label(self.table_frame, text=txt, bg=HEADER_BG, relief="ridge", width=18, justify="center").grid(row=0, column=cidx+1, sticky="nsew")
        
        # 6. Draw Grid Cells
        active_counts = [0]*len(slots)
        
        for ridx, slot_start in enumerate(slots):
            # Time slot label (Row ridx+1, Column 0)
            tk.Label(self.table_frame, text=slot_start.strftime(TIME_FORMAT), relief="ridge", width=16, anchor="e").grid(row=ridx+1, column=0, sticky="nsew")
            
            slot_end = slot_start + timedelta(minutes=interval)
            
            # Draw a cell for each employee for this time slot
            for cidx, s in enumerate(staff_with_times):
                dt = s.get_datetimes() # This is already checked to be non-None
                state = "off"
                sdt, edt, bd1, bd2 = dt
                
                # Check for overlap with shift
                if (slot_start < edt) and (slot_end > sdt):
                    in_break = False
                    # Check for overlap with break
                    if bd1 and bd2 and (slot_start < bd2 and slot_end > bd1):
                        in_break = True
                        
                    if in_break:
                        state = "break"
                    else:
                        state = "work"

                if state=="work":
                    bg = COLOR_WORK; active_counts[ridx]+=1
                elif state=="break":
                    bg = COLOR_BREAK
                else:
                    bg = COLOR_OFF
                    
                cell = tk.Label(self.table_frame, bg=bg, width=18, relief="ridge")
                # Cell is placed at ridx+1 (for time slots) and cidx+1 (for staff columns)
                cell.grid(row=ridx+1, column=cidx+1, sticky="nsew")
            
            self.table_frame.grid_rowconfigure(ridx+1, weight=0)
            
        # 7. Finalize View and Summary
        
        # --- FIX: Force Update and Scrollregion Calculation ---
        # 1. Ensure all widgets are drawn and size is known
        self.table_frame.update_idletasks()
        
        # 2. Update the Canvas scrollregion based on the total bounding box (width and height) of the content
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        total_slots = len(slots)
        preview = ", ".join([f"{slots[i].strftime(TIME_FORMAT)}={active_counts[i]}" for i in range(min(6,total_slots))])
        self.summary_lbl.config(text=f"Staff: {len(staff_with_times)} | Slots: {total_slots} ({interval}m) | Preview: {preview}")
        for j in range(len(staff_with_times)+1):
            self.table_frame.grid_columnconfigure(j, weight=0)
        
        self.refresh_stats_tab()

    def build_stats_tab(self):
        frm = self.tab_stats
        self.stats_canvas = tk.Canvas(frm)
        self.stats_canvas.pack(side="left", fill="both", expand=True)
        self.stats_vbar = ttk.Scrollbar(frm, orient="vertical", command=self.stats_canvas.yview)
        self.stats_vbar.pack(side="right", fill="y")
        self.stats_canvas.configure(yscrollcommand=self.stats_vbar.set)
        
        self.stats_frame = ttk.Frame(self.stats_canvas)
        self.stats_window = self.stats_canvas.create_window((0,0), window=self.stats_frame, anchor="nw")
        
        # Bind for dynamic resizing of the content frame
        self.stats_frame.bind("<Configure>", lambda e: self.stats_canvas.configure(scrollregion=self.stats_canvas.bbox("all")))
        self.stats_canvas.bind("<Configure>", lambda e: self.stats_canvas.itemconfig(self.stats_window, width=e.width))

    def refresh_stats_tab(self):
        for w in self.stats_frame.winfo_children():
            w.destroy()
        if not self.staff:
            ttk.Label(self.stats_frame, text="No staff data.").pack(padx=10, pady=10)
            return
            
        # Individual Statistics
        ttk.Label(self.stats_frame, text="📋 Individual Statistics", font=("Arial",11,"bold")).pack(anchor="w", padx=10, pady=(6,2))
        cols = ("Name","Role","Dept","Working Hrs","Break Hrs","Total Hrs")
        treef = ttk.Frame(self.stats_frame); treef.pack(fill="x", padx=10)
        st = ttk.Treeview(treef, columns=cols, show="headings", height=min(10, len(self.staff)+2))
        for c in cols:
            st.heading(c, text=c); st.column(c, width=120, anchor="center")
        for s in self.staff:
            st.insert("", "end", values=(s.name, s.role, s.dept, s.working_hours(), s.break_hours(), s.total_hours()))
        st.pack(fill="x")
        
        # Department summary
        ttk.Label(self.stats_frame, text="🏢 Department Summary", font=("Arial",11,"bold")).pack(anchor="w", padx=10, pady=(10,2))
        dept_stats = {}
        for s in self.staff:
            dept_stats.setdefault(s.dept, {"count":0,"work":0.0,"break":0.0})
            dept_stats[s.dept]["count"] += 1
            try:
                dept_stats[s.dept]["work"] += float(s.working_hours() or 0)
                dept_stats[s.dept]["break"] += float(s.break_hours() or 0)
            except:
                pass
        df_cols = ("Department","Count","Total Work","Total Break","Avg Work")
        df_tree = ttk.Treeview(self.stats_frame, columns=df_cols, show="headings", height=min(8,len(dept_stats)+2))
        for c in df_cols:
            df_tree.heading(c, text=c); df_tree.column(c, width=130, anchor="center")
        for d,stt in dept_stats.items():
            avg = stt["work"]/stt["count"] if stt["count"]>0 else 0
            df_tree.insert("", "end", values=(d, stt["count"], f"{stt['work']:.2f}", f"{stt['break']:.2f}", f"{avg:.2f}"))
        df_tree.pack(fill="x", padx=10, pady=(0,10))
        
        # Suggestions (simple)
        ttk.Label(self.stats_frame, text="💡 Suggestions", font=("Arial",11,"bold")).pack(anchor="w", padx=10, pady=(6,2))
        suggestions = self.generate_suggestions()
        for s in suggestions:
            lbl = ttk.Label(self.stats_frame, text="• " + s, wraplength=900, justify="left")
            lbl.pack(fill="x", padx=12, pady=2)
            
        self.stats_frame.update_idletasks()
        self.stats_canvas.config(scrollregion=self.stats_canvas.bbox("all"))

    def generate_suggestions(self):
        if not self.staff: return ["No data"]
        suggestions = []
        wh = []
        for s in self.staff:
            try:
                val = float(s.working_hours() or 0)
                if val>0:
                    wh.append((s.name,val))
            except:
                pass
        if wh:
            wh.sort(key=lambda x:x[1])
            suggestions.append(f"Work hours range: **{wh[0][0]} {wh[0][1]:.2f}h** .. **{wh[-1][0]} {wh[-1][1]:.2f}h** for {len(wh)} staff. Review workload balance.")
        total_work = sum(float(s.working_hours() or 0) for s in self.staff)
        total_break = sum(float(s.break_hours() or 0) for s in self.staff)
        if total_work>0:
            ratio = (total_break/total_work)*100
            suggestions.append(f"Break to total working hours ratio: **{ratio:.1f}%**.")
        # dept balance
        dept_counts = {}
        for s in self.staff:
            dept_counts[s.dept] = dept_counts.get(s.dept,0)+1
        if dept_counts:
            mx = max(dept_counts.values()); mn = min(dept_counts.values())
            if mx > mn*2:
                suggestions.append(f"Uneven department distribution detected. Max: {mx}, Min: {mn}. Consider rebalancing staff.")
        return suggestions or ["No critical issues detected. Schedule looks balanced."]

if __name__ == "__main__":
    root = tk.Tk()
    app = ShiftManagerApp(root)
    root.mainloop()