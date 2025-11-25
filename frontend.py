# frontend.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import backend
import datetime

LOGO_PATH = "BANK_SYSTEM_LOGO.png"

# Initialize DB if needed
backend.init_db()

class AdminApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Bank System")
        self.geometry("900x650")
        self.configure(bg="#f5f7fa")
        self.admin_user = None
        self._build_login()

    def _build_login(self):
        for w in self.winfo_children():
            w.destroy()
        frame = tk.Frame(self, bg="#f5f7fa")
        frame.pack(expand=True)

        # logo
        try:
            img = Image.open(LOGO_PATH).resize((140, 140))
            self.logo_img = ImageTk.PhotoImage(img)
            logo_label = tk.Label(frame, image=self.logo_img, bg="#f5f7fa")
            logo_label.pack(pady=10)
        except Exception as e:
            print("Logo load failed:", e)

        tk.Label(frame, text="ADMIN LOGIN", font=("Segoe UI", 18, "bold"), bg="#f5f7fa").pack(pady=6)
        tk.Label(frame, text="Username", bg="#f5f7fa").pack()
        self.username_entry = tk.Entry(frame, width=30)
        self.username_entry.pack(pady=5)
        tk.Label(frame, text="Password", bg="#f5f7fa").pack()
        self.password_entry = tk.Entry(frame, show="*", width=30)
        self.password_entry.pack(pady=5)
        tk.Button(frame, text="Login", bg="#1d4f91", fg="white", width=20, command=self._login).pack(pady=12)

    def _login(self):
        u = self.username_entry.get().strip()
        p = self.password_entry.get().strip()
        if backend.authenticate_admin(u, p):
            self.admin_user = u
            backend.log_action(u, "login")
            self._build_dashboard()
        else:
            messagebox.showerror("Login failed", "Invalid username or password")

    def _build_dashboard(self):
        for w in self.winfo_children():
            w.destroy()
        # top bar
        top = tk.Frame(self, bg="#1d4f91", height=60)
        top.pack(fill="x")
        tk.Label(top, text=f"Admin: {self.admin_user}", bg="#1d4f91", fg="white", font=("Segoe UI", 12)).pack(side="left", padx=12)
        tk.Button(top, text="Logout", command=self._logout, bg="#e74c3c", fg="white").pack(side="right", padx=12, pady=12)

        # main area with tabs
        tab_control = ttk.Notebook(self)
        tab_control.pack(expand=True, fill="both", padx=10, pady=10)

        # Accounts tab
        self.accounts_tab = tk.Frame(tab_control)
        tab_control.add(self.accounts_tab, text="Accounts")
        self._build_accounts_tab()

        # Transactions tab
        self.trans_tab = tk.Frame(tab_control)
        tab_control.add(self.trans_tab, text="Transactions")
        self._build_transactions_tab()

        # Loans tab
        self.loans_tab = tk.Frame(tab_control)
        tab_control.add(self.loans_tab, text="Loans")
        self._build_loans_tab()

        # Reports tab
        self.reports_tab = tk.Frame(tab_control)
        tab_control.add(self.reports_tab, text="Reports")
        self._build_reports_tab()

        # Audit tab
        self.audit_tab = tk.Frame(tab_control)
        tab_control.add(self.audit_tab, text="Audit Logs")
        self._build_audit_tab()

        # Settings
        self.settings_tab = tk.Frame(tab_control)
        tab_control.add(self.settings_tab, text="Settings")
        self._build_settings_tab()

    def _logout(self):
        backend.log_action(self.admin_user, "logout")
        self.admin_user = None
        self._build_login()

    # ---------- Accounts Tab ----------
    def _build_accounts_tab(self):
        for w in self.accounts_tab.winfo_children():
            w.destroy()
        left = tk.Frame(self.accounts_tab, width=380)
        left.pack(side="left", fill="y", padx=8, pady=8)
        right = tk.Frame(self.accounts_tab)
        right.pack(side="right", expand=True, fill="both", padx=8, pady=8)

        tk.Label(left, text="Create New Account", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(left, text="Name").pack(anchor="w")
        self.acc_name = tk.Entry(left)
        self.acc_name.pack(fill="x")
        tk.Label(left, text="Email").pack(anchor="w")
        self.acc_email = tk.Entry(left)
        self.acc_email.pack(fill="x")
        tk.Label(left, text="Phone").pack(anchor="w")
        self.acc_phone = tk.Entry(left)
        self.acc_phone.pack(fill="x")
        tk.Label(left, text="Initial balance").pack(anchor="w")
        self.acc_balance = tk.Entry(left)
        self.acc_balance.insert(0, "0")
        self.acc_balance.pack(fill="x")
        tk.Button(left, text="Create Account", bg="#2e8b57", fg="white", command=self._create_account).pack(pady=8)

        # accounts list
        tk.Label(right, text="Existing Accounts", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        cols = ("id","account_no","name","email","phone","balance","created_at")
        self.acc_tree = ttk.Treeview(right, columns=cols, show="headings")
        for c in cols:
            self.acc_tree.heading(c, text=c)
        self.acc_tree.pack(expand=True, fill="both")
        btn_frame = tk.Frame(right)
        btn_frame.pack(fill="x", pady=6)
        tk.Button(btn_frame, text="Refresh", command=self._refresh_accounts).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Edit", command=self._edit_account).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Delete", command=self._delete_account).pack(side="left", padx=6)
        self._refresh_accounts()

    def _create_account(self):
        name = self.acc_name.get().strip()
        email = self.acc_email.get().strip()
        phone = self.acc_phone.get().strip()
        try:
            balance = float(self.acc_balance.get())
        except:
            balance = 0.0
        if not name:
            messagebox.showwarning("Validation", "Name is required")
            return
        acc_no = backend.generate_account_no()
        ok = backend.create_account(acc_no, name, email, phone, balance)
        if ok:
            messagebox.showinfo("Success", f"Account created: {acc_no}")
            self.acc_name.delete(0, "end")
            self.acc_email.delete(0, "end")
            self.acc_phone.delete(0, "end")
            self.acc_balance.delete(0, "end")
            self._refresh_accounts()
        else:
            messagebox.showerror("Error", "Could not create account")

    def _refresh_accounts(self):
        for r in self.acc_tree.get_children():
            self.acc_tree.delete(r)
        rows = backend.get_accounts()
        for r in rows:
            self.acc_tree.insert("", "end", values=r)

    def _edit_account(self):
        sel = self.acc_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Choose an account row to edit")
            return
        item = self.acc_tree.item(sel[0])
        acc_id = item['values'][0]
        name = simpledialog.askstring("Edit name", "Name:", initialvalue=item['values'][2])
        email = simpledialog.askstring("Edit email", "Email:", initialvalue=item['values'][3])
        phone = simpledialog.askstring("Edit phone", "Phone:", initialvalue=item['values'][4])
        if name is None:
            return
        backend.update_account(acc_id, name=name, email=email, phone=phone)
        self._refresh_accounts()

    def _delete_account(self):
        sel = self.acc_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Choose an account row to delete")
            return
        item = self.acc_tree.item(sel[0])
        acc_id = item['values'][0]
        if messagebox.askyesno("Confirm", "Delete account?"):
            backend.delete_account(acc_id)
            self._refresh_accounts()

    # ---------- Transactions Tab ----------
    def _build_transactions_tab(self):
        for w in self.trans_tab.winfo_children():
            w.destroy()
        top = tk.Frame(self.trans_tab)
        top.pack(fill="x", padx=8, pady=8)
        tk.Label(top, text="Account No:").pack(side="left")
        self.tx_account_no = tk.Entry(top, width=18)
        self.tx_account_no.pack(side="left", padx=6)
        tk.Label(top, text="Amount:").pack(side="left")
        self.tx_amount = tk.Entry(top, width=12)
        self.tx_amount.pack(side="left", padx=6)
        tk.Button(top, text="Deposit", bg="#2e8b57", fg="white",
                  command=lambda: self._do_tx("deposit")).pack(side="left", padx=6)
        tk.Button(top, text="Withdraw", bg="#e67e22", fg="white",
                  command=lambda: self._do_tx("withdraw")).pack(side="left", padx=6)

        self.tx_tree = ttk.Treeview(self.trans_tab, columns=("id","account_no","type","amount","timestamp","note"), show="headings")
        for c in ("id","account_no","type","amount","timestamp","note"):
            self.tx_tree.heading(c, text=c)
        self.tx_tree.pack(expand=True, fill="both", padx=8, pady=8)
        tk.Button(self.trans_tab, text="Refresh", command=self._refresh_tx).pack(pady=4)
        self._refresh_tx()

    def _do_tx(self, ttype):
        acc = self.tx_account_no.get().strip()
        try:
            amt = float(self.tx_amount.get())
        except:
            messagebox.showerror("Invalid", "Enter a numeric amount")
            return
        ok, msg = backend.add_transaction(acc, ttype, amt, note=f"By {self.admin_user}")
        if ok:
            messagebox.showinfo("Success", msg)
            self._refresh_tx()
            self._refresh_accounts()
        else:
            messagebox.showerror("Error", msg)

    def _refresh_tx(self):
        for r in self.tx_tree.get_children():
            self.tx_tree.delete(r)
        rows = backend.get_transactions(200)
        for r in rows:
            self.tx_tree.insert("", "end", values=r)

    # ---------- Loans Tab ----------
    def _build_loans_tab(self):
        for w in self.loans_tab.winfo_children():
            w.destroy()
        top = tk.Frame(self.loans_tab)
        top.pack(fill="x", padx=8, pady=8)
        tk.Label(top, text="Account No:").pack(side="left")
        self.loan_acc = tk.Entry(top, width=16)
        self.loan_acc.pack(side="left", padx=6)
        tk.Label(top, text="Amount:").pack(side="left")
        self.loan_amt = tk.Entry(top, width=12)
        self.loan_amt.pack(side="left", padx=6)
        tk.Button(top, text="Request Loan", bg="#3498db", fg="white", command=self._request_loan).pack(side="left", padx=6)
        # loan list
        cols = ("id","account_no","amount","status","created_at","updated_at")
        self.loan_tree = ttk.Treeview(self.loans_tab, columns=cols, show="headings")
        for c in cols:
            self.loan_tree.heading(c, text=c)
        self.loan_tree.pack(expand=True, fill="both", padx=8, pady=8)
        btn_frame = tk.Frame(self.loans_tab)
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="Refresh", command=self._refresh_loans).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Approve", command=lambda: self._change_loan("approved")).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Mark Paid", command=lambda: self._change_loan("paid")).pack(side="left", padx=6)
        self._refresh_loans()

    def _request_loan(self):
        acc = self.loan_acc.get().strip()
        try:
            amt = float(self.loan_amt.get())
        except:
            messagebox.showerror("Invalid", "Enter valid amount")
            return
        backend.create_loan(acc, amt)
        messagebox.showinfo("Requested", "Loan requested")
        self._refresh_loans()

    def _refresh_loans(self):
        for r in self.loan_tree.get_children():
            self.loan_tree.delete(r)
        rows = backend.get_loans()
        for r in rows:
            self.loan_tree.insert("", "end", values=r)

    def _change_loan(self, status):
        sel = self.loan_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a loan")
            return
        item = self.loan_tree.item(sel[0])
        loan_id = item['values'][0]
        backend.update_loan_status(loan_id, status)
        messagebox.showinfo("OK", f"Loan {loan_id} -> {status}")
        self._refresh_loans()

    # ---------- Reports ----------
    def _build_reports_tab(self):
        for w in self.reports_tab.winfo_children():
            w.destroy()
        tk.Label(self.reports_tab, text="Reports", font=("Segoe UI", 14, "bold")).pack(pady=6)
        tk.Button(self.reports_tab, text="Refresh Summary", command=self._report_summary).pack()
        self.report_text = tk.Text(self.reports_tab, height=20)
        self.report_text.pack(expand=True, fill="both", padx=8, pady=8)
        self._report_summary()

    def _report_summary(self):
        self.report_text.delete("1.0", "end")
        total_deposits = backend.total_deposits()
        total_withdraws = backend.total_withdraws()
        accounts = backend.get_accounts()
        loans = backend.get_loans()
        summary = f"Summary at {datetime.datetime.utcnow().isoformat()} UTC\n\n"
        summary += f"Total accounts: {len(accounts)}\n"
        summary += f"Total deposits: {total_deposits}\n"
        summary += f"Total withdrawals: {total_withdraws}\n"
        summary += f"Loans: {len(loans)} (pending/approved/paid) breakdown:\n"
        statuses = {}
        for L in loans:
            statuses[L[3]] = statuses.get(L[3], 0) + 1
        for k,v in statuses.items():
            summary += f"  {k}: {v}\n"
        self.report_text.insert("1.0", summary)

    # ---------- Audit ----------
    def _build_audit_tab(self):
        for w in self.audit_tab.winfo_children():
            w.destroy()
        tk.Button(self.audit_tab, text="Refresh", command=self._refresh_audit).pack(pady=6)
        self.audit_tree = ttk.Treeview(self.audit_tab, columns=("id","admin","action","timestamp"), show="headings")
        for c in ("id","admin","action","timestamp"):
            self.audit_tree.heading(c, text=c)
        self.audit_tree.pack(expand=True, fill="both", padx=8, pady=8)
        self._refresh_audit()

    def _refresh_audit(self):
        for r in self.audit_tree.get_children():
            self.audit_tree.delete(r)
        rows = backend.get_audit_logs(200)
        for r in rows:
            self.audit_tree.insert("", "end", values=r)

    # ---------- Settings ----------
    def _build_settings_tab(self):
        for w in self.settings_tab.winfo_children():
            w.destroy()
        tk.Label(self.settings_tab, text="Settings", font=("Segoe UI", 14, "bold")).pack(pady=8)
        tk.Label(self.settings_tab, text="(You can add more settings here)").pack()
        
if __name__ == "__main__":
    app = AdminApp()
    app.mainloop()