# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import json, os, datetime, shutil, sys, subprocess

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "data.json")
RECEIPT_DIR = os.path.join(APP_DIR, "receipts")

DEFAULT_PASSWORD = "1357"

# ---------- Utilities ----------
def ensure_storage():
    if not os.path.exists(RECEIPT_DIR):
        os.makedirs(RECEIPT_DIR)
    if not os.path.exists(DATA_FILE):
        data = {
            "password": DEFAULT_PASSWORD,
            "users": []  # each: {name, debt, paid, pending_cash, pending_card, receipt, payment_time, approved_by}
        }
        save_data(data)

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def find_users_by_name(query, data):
    q = query.strip().lower()
    if not q:
        return []
    # flexible matching: substring case-insensitive
    return [u for u in data["users"] if q in u["name"].lower()]

def open_file(path):
    if not path or not os.path.exists(path):
        messagebox.showwarning("فایل یافت نشد", "فایل رسید موجود نیست.")
        return
    try:
        if sys.platform.startswith("darwin"):
            subprocess.call(("open", path))
        elif os.name == "nt":
            os.startfile(path)
        else:
            subprocess.call(("xdg-open", path))
    except Exception as e:
        messagebox.showerror("خطا", str(e))

# ---------- GUI App ----------
class DangYarApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("سامانه دَنگ‌یار")
        self.geometry("900x600")
        self.resizable(True, True)

        ensure_storage()
        self.data = load_data()

        # Frames
        self.frame_welcome = ttk.Frame(self)
        self.frame_manager = ttk.Frame(self)
        self.frame_user = ttk.Frame(self)

        self.frame_welcome.pack(fill="both", expand=True)
        self.create_welcome()

    # ---------- Welcome ----------
    def create_welcome(self):
        for w in self.frame_welcome.winfo_children():
            w.destroy()
        label = ttk.Label(self.frame_welcome, text="به سامانهٔ دَنگ‌یار خوش آمدید", font=("Tahoma", 18))
        label.pack(pady=20)
        q_label = ttk.Label(self.frame_welcome, text="آیا مدیر هستید؟", font=("Tahoma", 14))
        q_label.pack(pady=10)
        btn_frame = ttk.Frame(self.frame_welcome)
        btn_frame.pack(pady=10)
        btn_yes = ttk.Button(btn_frame, text="بله (مدیر)", command=self.manager_login)
        btn_no = ttk.Button(btn_frame, text="خیر (کاربر)", command=self.user_panel_entry)
        btn_yes.grid(row=0, column=0, padx=10)
        btn_no.grid(row=0, column=1, padx=10)

    # ---------- Manager ----------
    def manager_login(self):
        # ask password
        pwd = simpledialog.askstring("ورود مدیر", "پسوورد را وارد کنید:", show="*")
        if pwd is None:
            return
        self.data = load_data()
        if pwd == self.data.get("password", DEFAULT_PASSWORD):
            self.open_manager_panel()
        else:
            messagebox.showerror("خطا", "پسوورد اشتباه است.")

    def open_manager_panel(self):
        self.frame_welcome.pack_forget()
        self.frame_user.pack_forget()
        self.frame_manager.pack(fill="both", expand=True)
        self.create_manager_ui()

    def create_manager_ui(self):
        for w in self.frame_manager.winfo_children():
            w.destroy()
        top_frame = ttk.Frame(self.frame_manager)
        top_frame.pack(fill="x", padx=10, pady=8)

        title = ttk.Label(top_frame, text="پنل مدیریت", font=("Tahoma", 16))
        title.pack(side="left")

        btn_logout = ttk.Button(top_frame, text="خروج", command=self.manager_logout)
        btn_logout.pack(side="right", padx=4)

        btn_change_pwd = ttk.Button(top_frame, text="تغییر پسوورد", command=self.change_password)
        btn_change_pwd.pack(side="right", padx=4)

        # Left: listbox of users
        left = ttk.Frame(self.frame_manager)
        left.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        self.user_listbox = tk.Listbox(left, font=("Tahoma", 12))
        self.user_listbox.pack(side="left", fill="both", expand=True)
        self.user_listbox.bind("<<ListboxSelect>>", lambda e: self.show_selected_user())

        sb = ttk.Scrollbar(left, orient="vertical", command=self.user_listbox.yview)
        sb.pack(side="right", fill="y")
        self.user_listbox.config(yscrollcommand=sb.set)

        # Right: detail & actions
        right = ttk.Frame(self.frame_manager)
        right.pack(side="right", fill="both", expand=True, padx=8, pady=8)

        # Detail labels
        self.detail_lbl = ttk.Label(right, text="انتخاب کنید", font=("Tahoma", 12))
        self.detail_lbl.pack(pady=4)

        # Buttons: add, edit, delete, reset all, confirm cash, confirm receipt
        btns = ttk.Frame(right)
        btns.pack(pady=6)

        ttk.Button(btns, text="افزودن فرد", command=self.add_user_dialog).grid(row=0, column=0, padx=3, pady=3)
        ttk.Button(btns, text="ویرایش انتخاب شده", command=self.edit_selected_user).grid(row=0, column=1, padx=3, pady=3)
        ttk.Button(btns, text="حذف انتخاب شده", command=self.delete_selected_user).grid(row=0, column=2, padx=3, pady=3)
        ttk.Button(btns, text="ریست کامل (حذف همه)", command=self.reset_all).grid(row=0, column=3, padx=3, pady=3)

        # Pending approvals
        ttk.Separator(right, orient="horizontal").pack(fill="x", pady=6)
        ttk.Label(right, text="درخواست‌های پرداخت (نقدی/رسید کارت):", font=("Tahoma", 12)).pack(anchor="w")
        self.pending_frame = ttk.Frame(right)
        self.pending_frame.pack(fill="both", expand=True)

        self.refresh_manager_lists()

    def refresh_manager_lists(self):
        self.data = load_data()
        # populate listbox
        self.user_listbox.delete(0, tk.END)
        for u in self.data["users"]:
            status = "✓" if u.get("paid") else ("(درخواست) " if u.get("pending_cash") or u.get("pending_card") else "–")
            self.user_listbox.insert(tk.END, f"{u['name']} — {u.get('debt',0):,} تومان {status}")

        # pending
        for w in self.pending_frame.winfo_children():
            w.destroy()
        idx=0
        for i,u in enumerate(self.data["users"]):
            if u.get("pending_cash") or u.get("pending_card"):
                f = ttk.Frame(self.pending_frame, relief="groove", padding=6)
                f.pack(fill="x", pady=3)
                ttk.Label(f, text=f"{u['name']} — {u.get('debt',0):,} تومان", font=("Tahoma", 11)).grid(row=0, column=0, sticky="w")
                status = []
                if u.get("pending_cash"): status.append("پرداخت نقدی (تأیید نشده)")
                if u.get("pending_card"): status.append("رسید کارت آپلود شده (تأیید نشده)")
                ttk.Label(f, text="، ".join(status)).grid(row=1, column=0, sticky="w")
                btn_confirm_cash = ttk.Button(f, text="تأیید نقدی", command=lambda i=i: self.confirm_cash(i))
                btn_confirm_card = ttk.Button(f, text="مشاهده/تأیید رسید", command=lambda i=i: self.view_and_confirm_receipt(i))
                btn_confirm_cash.grid(row=0, column=1, padx=4)
                btn_confirm_card.grid(row=1, column=1, padx=4)

                idx+=1

    def manager_logout(self):
        self.frame_manager.pack_forget()
        self.frame_welcome.pack(fill="both", expand=True)

    def change_password(self):
        newp = simpledialog.askstring("تغییر پسوورد", "پسورد جدید را وارد کنید (حداقل 4 رقم):", show="*")
        if not newp or len(newp.strip())<4:
            messagebox.showwarning("ناقص", "پسورد باید حداقل 4 کاراکتر باشد.")
            return
        self.data = load_data()
        self.data["password"] = newp.strip()
        save_data(self.data)
        messagebox.showinfo("موفق", "پسورد با موفقیت تغییر کرد.")

    def add_user_dialog(self):
        dlg = UserEditDialog(self, title="افزودن فرد")
        self.wait_window(dlg.top)
        if dlg.result:
            name, debt = dlg.result
            self.data = load_data()
            # prevent exact duplicate names? allow but warn
            # append
            self.data["users"].append({
                "name": name,
                "debt": float(debt),
                "paid": False,
                "pending_cash": False,
                "pending_card": False,
                "receipt": "",
                "payment_time": "",
                "approved_by": ""
            })
            save_data(self.data)
            self.refresh_manager_lists()

    def show_selected_user(self):
        sel = self.user_listbox.curselection()
        if not sel: 
            self.detail_lbl.config(text="انتخاب کنید")
            return
        idx = sel[0]
        u = self.data["users"][idx]
        txt = f"نام: {u['name']}\nمیزان بدهی: {u.get('debt',0):,} تومان\nوضعیت پرداخت: {'پرداخت شده' if u.get('paid') else 'پرداخت نشده'}"
        if u.get("pending_cash"): txt += "\nدرخواست نقدی (تأیید نشده)"
        if u.get("pending_card"): txt += "\nرسید کارت آپلود شده (تأیید نشده)"
        if u.get("receipt"):
            txt += f"\nرسید: {os.path.basename(u.get('receipt'))}"
        if u.get("approved_by"):
            txt += f"\nتأیید شده توسط: {u.get('approved_by')} در {u.get('payment_time')}"
        self.detail_lbl.config(text=txt)

    def edit_selected_user(self):
        sel = self.user_listbox.curselection()
        if not sel:
            messagebox.showwarning("هشدار", "یک فرد انتخاب کنید.")
            return
        idx = sel[0]
        u = self.data["users"][idx]
        dlg = UserEditDialog(self, title="ویرایش فرد", name=u["name"], debt=str(int(u.get("debt",0))))
        self.wait_window(dlg.top)
        if dlg.result:
            name, debt = dlg.result
            self.data = load_data()
            self.data["users"][idx]["name"] = name
            self.data["users"][idx]["debt"] = float(debt)
            save_data(self.data)
            self.refresh_manager_lists()

    def delete_selected_user(self):
        sel = self.user_listbox.curselection()
        if not sel:
            messagebox.showwarning("هشدار", "یک فرد انتخاب کنید.")
            return
        idx = sel[0]
        u = self.data["users"][idx]
        if messagebox.askyesno("حذف", f"آیا از حذف {u['name']} مطمئن هستید؟"):
            # remove receipt file if exists
            if u.get("receipt") and os.path.exists(u["receipt"]):
                try: os.remove(u["receipt"])
                except: pass
            self.data = load_data()
            self.data["users"].pop(idx)
            save_data(self.data)
            self.refresh_manager_lists()

    def reset_all(self):
        if not messagebox.askyesno("ریست کامل", "آیا می‌خواهید تمام اسامی و داده‌ها حذف شود؟ این عمل برگشت‌پذیر نیست."):
            return
        # remove receipts
        for u in self.data["users"]:
            if u.get("receipt") and os.path.exists(u["receipt"]):
                try: os.remove(u["receipt"])
                except: pass
        self.data = load_data()
        self.data["users"] = []
        save_data(self.data)
        self.refresh_manager_lists()

    def confirm_cash(self, idx):
        self.data = load_data()
        u = self.data["users"][idx]
        if not u.get("pending_cash"):
            messagebox.showinfo("اطلاع", "درخواستی موجود نیست.")
            return
        u["paid"] = True
        u["pending_cash"] = False
        u["payment_time"] = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
        u["approved_by"] = "مدیر"
        save_data(self.data)
        messagebox.showinfo("تأیید", f"پرداخت نقدی {u['name']} تأیید شد.")
        self.refresh_manager_lists()

    def view_and_confirm_receipt(self, idx):
        self.data = load_data()
        u = self.data["users"][idx]
        if not u.get("pending_card"):
            messagebox.showinfo("اطلاع", "درخواستی موجود نیست.")
            return
        # open file if exists
        if u.get("receipt") and os.path.exists(u["receipt"]):
            if messagebox.askyesno("دیدن رسید", "آیا می‌خواهید رسید را باز کنید؟ (پس از مشاهده می‌توانید تأیید کنید)"):
                open_file(u["receipt"])
        if messagebox.askyesno("تأیید رسید", "آیا این پرداخت را تأیید می‌کنید؟"):
            u["paid"] = True
            u["pending_card"] = False
            u["payment_time"] = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
            u["approved_by"] = "مدیر"
            save_data(self.data)
            messagebox.showinfo("تأیید", f"رسید {u['name']} تأیید شد.")
            self.refresh_manager_lists()

    # ---------- User panel ----------
    def user_panel_entry(self):
        self.frame_welcome.pack_forget()
        self.frame_manager.pack_forget()
        self.frame_user.pack(fill="both", expand=True)
        self.create_user_ui()

    def create_user_ui(self):
        for w in self.frame_user.winfo_children():
            w.destroy()
        top = ttk.Frame(self.frame_user)
        top.pack(fill="x", pady=8, padx=8)
        ttk.Label(top, text="پنل کاربری", font=("Tahoma", 16)).pack(side="left")
        ttk.Button(top, text="بازگشت", command=self.user_logout).pack(side="right")

        entry_frame = ttk.Frame(self.frame_user)
        entry_frame.pack(pady=12)

        ttk.Label(entry_frame, text="نام خود را وارد کنید:").grid(row=0, column=0, padx=4)
        self.name_entry = ttk.Entry(entry_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=4)
        ttk.Button(entry_frame, text="جستجو", command=self.user_search).grid(row=0, column=2, padx=4)

        # search results
        self.search_results = ttk.Frame(self.frame_user)
        self.search_results.pack(fill="x", padx=8, pady=6)

        # detail/payment area
        self.user_detail = ttk.Frame(self.frame_user, relief="ridge", padding=10)
        self.user_detail.pack(fill="both", expand=True, padx=8, pady=8)

        self.cur_user = None

    def user_logout(self):
        self.frame_user.pack_forget()
        self.frame_welcome.pack(fill="both", expand=True)

    def user_search(self):
        name = self.name_entry.get().strip()
        self.data = load_data()
        for w in self.search_results.winfo_children():
            w.destroy()
        results = find_users_by_name(name, self.data)
        if not results:
            ttk.Label(self.search_results, text="هیچ نامی یافت نشد. اگر جدید هستید، لطفاً از مدیر بخواهید نام شما را اضافه کند.", foreground="red").pack()
            self.clear_user_detail()
            return
        for u in results:
            f = ttk.Frame(self.search_results)
            f.pack(fill="x", pady=2)
            ttk.Label(f, text=f"{u['name']} — {int(u.get('debt',0)):,} تومان").pack(side="left")
            ttk.Button(f, text="انتخاب", command=lambda u=u: self.open_user_detail(u)).pack(side="right")

    def clear_user_detail(self):
        for w in self.user_detail.winfo_children():
            w.destroy()
        self.cur_user = None

    def open_user_detail(self, user_obj):
        # find actual index in data
        self.data = load_data()
        idx = None
        for i,u in enumerate(self.data["users"]):
            if u["name"] == user_obj["name"] and int(u.get("debt",0))==int(user_obj.get("debt",0)):
                idx = i
                break
        if idx is None:
            messagebox.showerror("خطا", "کاربر یافت نشد (داده‌ها تغییر کرده‌اند).")
            return
        u = self.data["users"][idx]
        self.cur_user = idx
        for w in self.user_detail.winfo_children():
            w.destroy()
        ttk.Label(self.user_detail, text=f"سلام {u['name']}", font=("Tahoma", 14)).pack(anchor="w")
        ttk.Label(self.user_detail, text=f"میزان بدهی: {int(u.get('debt',0)):,} تومان", font=("Tahoma", 12)).pack(anchor="w", pady=4)
        status_text = "پرداخت شده" if u.get("paid") else "پرداخت نشده"
        ttk.Label(self.user_detail, text=f"وضعیت: {status_text}").pack(anchor="w", pady=2)

        # reminder if unpaid
        if not u.get("paid") and float(u.get("debt",0))>0:
            ttk.Label(self.user_detail, text=f"یادآوری: امروز {int(u.get('debt',0)):,} تومان بدهی دارید، لطفاً پرداخت کنید.", foreground="blue").pack(anchor="w", pady=4)

        # payment options
        pay_frame = ttk.Frame(self.user_detail)
        pay_frame.pack(pady=8, anchor="w")

        # If already paid
        if u.get("paid"):
            ttk.Label(pay_frame, text="شما بدهی خود را پرداخت کرده‌اید.").pack(anchor="w")
            if u.get("payment_time"):
                ttk.Label(pay_frame, text=f"زمان پرداخت: {u.get('payment_time')} — تایید شده توسط: {u.get('approved_by','-')}").pack(anchor="w")
            return

        # show current pending state
        if u.get("pending_cash"):
            ttk.Label(pay_frame, text="وضعیت: پرداخت نقدی ثبت شده؛ در انتظار تأیید مدیر.", foreground="orange").pack(anchor="w")
        if u.get("pending_card"):
            ttk.Label(pay_frame, text="وضعیت: رسید کارت آپلود شده؛ در انتظار تأیید مدیر.", foreground="orange").pack(anchor="w")
            if u.get("receipt"):
                ttk.Button(pay_frame, text="مشاهده رسید", command=lambda p=u.get("receipt"): open_file(p)).pack(anchor="w", pady=2)

        # Payment controls - must always be available unless paid:
        ttk.Label(pay_frame, text="روش پرداخت:").pack(anchor="w")
        self.pay_method = tk.StringVar(value="cash")
        rb1 = ttk.Radiobutton(pay_frame, text="نقدی", variable=self.pay_method, value="cash")
        rb2 = ttk.Radiobutton(pay_frame, text="کارت (آپلود رسید)", variable=self.pay_method, value="card")
        rb1.pack(anchor="w")
        rb2.pack(anchor="w")

        btn_frame = ttk.Frame(pay_frame)
        btn_frame.pack(pady=6, anchor="w")
        btn_pay = ttk.Button(btn_frame, text="پرداخت کردم", command=self.user_click_paid)
        btn_pay.pack(side="left")
        # After pressing once, button will be ineffective because state saved. Also requirement: once entered can't press again — we enforce by checking paid/pending.

    def user_click_paid(self):
        if self.cur_user is None:
            messagebox.showwarning("هشدار", "ابتدا یک نام را انتخاب کنید.")
            return
        self.data = load_data()
        u = self.data["users"][self.cur_user]
        if u.get("paid"):
            messagebox.showinfo("اطلاع", "بدهی شما قبلاً پرداخت شده است.")
            return
        # If already pending, don't allow duplicate requests
        if u.get("pending_cash") or u.get("pending_card"):
            messagebox.showinfo("اطلاع", "درخواست پرداخت شما قبلاً ثبت شده است و در انتظار تأیید مدیر است.")
            return
        method = self.pay_method.get()
        if method == "cash":
            # mark pending cash
            u["pending_cash"] = True
            u["pending_card"] = False
            u["receipt"] = ""
            save_data(self.data)
            messagebox.showinfo("ثبت شد", "درخواست پرداخت نقدی ثبت شد. منتظر تأیید مدیر باشید.")
            self.open_user_detail(u)
            return
        else:
            # open file dialog to choose receipt image
            filetypes = [("تصاویر", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")]
            path = filedialog.askopenfilename(title="انتخاب فایل رسید", filetypes=filetypes)
            if not path:
                return
            # copy to receipts dir with unique name
            base = os.path.basename(path)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            dest = os.path.join(RECEIPT_DIR, f"{timestamp}_{base}")
            try:
                shutil.copy2(path, dest)
            except Exception as e:
                messagebox.showerror("خطا", f"کپی فایل انجام نشد: {e}")
                return
            u["pending_card"] = True
            u["pending_cash"] = False
            u["receipt"] = dest
            save_data(self.data)
            messagebox.showinfo("ثبت شد", "رسید آپلود شد. منتظر تأیید مدیر باشید.")
            self.open_user_detail(u)
            return

# ---------- Simple dialog for add/edit ----------
class UserEditDialog:
    def __init__(self, parent, title="ویرایش", name="", debt="0"):
        self.top = tk.Toplevel(parent)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.title(title)
        ttk.Label(self.top, text="نام:").grid(row=0, column=0, padx=6, pady=6)
        self.e_name = ttk.Entry(self.top, width=40)
        self.e_name.grid(row=0, column=1, padx=6, pady=6)
        self.e_name.insert(0, name)
        ttk.Label(self.top, text="میزان بدهی (تومان):").grid(row=1, column=0, padx=6, pady=6)
        self.e_debt = ttk.Entry(self.top, width=20)
        self.e_debt.grid(row=1, column=1, padx=6, pady=6, sticky="w")
        self.e_debt.insert(0, debt)
        btnf = ttk.Frame(self.top)
        btnf.grid(row=2, column=0, columnspan=2, pady=8)
        ttk.Button(btnf, text="ذخیره", command=self.on_ok).pack(side="left", padx=6)
        ttk.Button(btnf, text="انصراف", command=self.on_cancel).pack(side="left", padx=6)
        self.result = None

    def on_ok(self):
        name = self.e_name.get().strip()
        debt = self.e_debt.get().strip().replace(",", "")
        if not name:
            messagebox.showwarning("هشدار", "نام نباید خالی باشد.")
            return
        try:
            d = float(debt)
            if d < 0:
                raise ValueError
        except:
            messagebox.showwarning("هشدار", "مقدار بدهی نامعتبر است.")
            return
        self.result = (name, d)
        self.top.destroy()

    def on_cancel(self):
        self.top.destroy()

# ---------- Main ----------
if __name__ == "__main__":
    app = DangYarApp()
    app.mainloop()
