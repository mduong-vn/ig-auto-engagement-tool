import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from session import SessionManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from plyer import notification
import main
import os
import json
import threading
import sys

# get resource path
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# save input to json
def save_input():
    data = {
        "accounts": accounts_text.get("1.0", tk.END).strip(),
        "comments": comments_text.get("1.0", tk.END).strip(),
        "reports": report_text.get("1.0", tk.END).strip(),
        "num_posts": num_posts_var.get().strip(),
        "caption": caption_text.get("1.0", tk.END).strip(),
        "post_accounts": post_accounts_text.get("1.0", tk.END).strip(),
        "post_hashtags": post_hashtags_text.get("1.0", tk.END).strip(),
        "post_images": post_images_text.get("1.0", tk.END).strip(),
        "comment_var": comment_var.get(),
        "report_var": report_var.get(),
        "post_new_var": post_new_var.get(),
        "link_var": link_var.get(),
        "link_links": link_text.get("1.0", tk.END).strip()
    }
    with open("input_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# load input from json
def load_input():
    if os.path.exists("input_data.json"):
        with open("input_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

            accounts_text.delete("1.0", tk.END)
            accounts_text.insert(tk.END, data.get("accounts", ""))

            comments_text.delete("1.0", tk.END)
            comments_text.insert(tk.END, data.get("comments", ""))

            report_text.delete("1.0", tk.END)
            report_text.insert(tk.END, data.get("reports", ""))

            num_posts_var.set(data.get("num_posts", "5"))

            link_text.delete("1.0", tk.END)
            link_text.insert(tk.END, data.get("link_links", ""))

            caption_text.delete("1.0", tk.END)
            caption_text.insert(tk.END, data.get("caption", ""))

            post_accounts_text.delete("1.0", tk.END)
            post_accounts_text.insert(tk.END, data.get("post_accounts", ""))

            post_hashtags_text.delete("1.0", tk.END)
            post_hashtags_text.insert(tk.END, data.get("post_hashtags", ""))

            post_images_text.delete("1.0", tk.END)
            post_images_text.insert(tk.END, data.get("post_images", ""))

            comment_var.set(data.get("comment_var", False))
            link_var.set(data.get("link_var", False))
            report_var.set(data.get("report_var", False))
            post_new_var.set(data.get("post_new_var", False))

# log messages to text area
def log_message(message):
    log_text.config(state=tk.NORMAL)
    log_text.insert(tk.END, message + "\n")
    log_text.see(tk.END)
    log_text.config(state=tk.DISABLED)

# redirect print to log
main.set_logger(log_message)

def safe_showerror(title, message):
    root.after(0, lambda: messagebox.showerror(title, message))

# update start button state
def update_start_button():
    if (report_var.get() and not report_text.get("1.0", tk.END).strip()) \
        or not accounts_text.get("1.0", tk.END).strip() \
        or (comment_var.get() and not (target1_var.get() or target2_var.get() or link_var.get())) \
        or (post_new_var.get() and (not post_images_text.get("1.0", tk.END).strip()
                                    or not post_accounts_text.get("1.0", tk.END).strip()
                                    or not any(tag.lower() in ["account_target1", "account_target2"]
                                                for tag in post_accounts_text.get("1.0", tk.END).strip().split("\n")))) \
        or (not comment_var.get() and not report_var.get() and not post_new_var.get()):
        start_button.config(state=tk.DISABLED, bg="white", fg="black")
    else:
        start_button.config(state=tk.NORMAL, bg="#f8f2fc", fg="black")

# toggle conditional frames
def toggle_conditional_frames():
    if post_new_var.get():
        post_frame.pack(fill=tk.X, pady=5, side=tk.TOP)
    else:
        post_frame.pack_forget()

    if comment_var.get():
        comment_frame.pack(fill=tk.X, pady=5)
        num_posts_frame.pack(fill=tk.X, pady=5)
        link_frame.pack(fill=tk.X, pady=2)
        if link_var.get():
            link_label.pack(anchor=tk.W)
            link_text.pack(fill=tk.X, pady=2)
        else:
            link_label.pack_forget()
            link_text.pack_forget()
    else:
        comment_frame.pack_forget()
        num_posts_frame.pack_forget()
        link_frame.pack_forget()
        link_label.pack_forget()
        link_text.pack_forget()

    if report_var.get():
        report_frame.pack(fill=tk.X, pady=5)
    else:
        report_frame.pack_forget()

    update_start_button()
    root.update_idletasks()
    root.geometry("")

# stop event for threading
stop_event = threading.Event()

# main bot function
def start_bot():
    accounts = accounts_text.get("1.0", tk.END).strip().split("\n")
    accounts = [line.split(":", 1) for line in accounts if ":" in line]
    accounts = [{"user": user.strip(), "pwd": pwd.strip()} for user, pwd in accounts]
    
    target_profiles = []
    if target1_var.get():
        target_profiles.append("account_target1")
    if target2_var.get():
        target_profiles.append("account_target2")

    for account in accounts:
        if stop_event.is_set():
            break
        try:
            comments = [line.strip() for line in comments_text.get("1.0", tk.END).splitlines() if line.strip()]
            reports = [line.strip() for line in report_text.get("1.0", tk.END).splitlines() if line.strip()]
            try:
                num_posts = int(num_posts_var.get().strip())
                if num_posts <= 0:
                    raise ValueError("positive only")
            except Exception:
                num_posts = 5

            ok = session_manager.add_account(account['user'], account['pwd'])
            if not ok:
                continue
            WebDriverWait(session_manager.sessions[account['user']].driver, 15).until(
                EC.url_contains("instagram.com")
            )

            # comment
            if comment_var.get():
                all_success = True
                for profile in target_profiles:
                    success = session_manager.action(account['user'], "comment", profile, comments, num_posts, account['user'])
                    if not success:
                        all_success = False
                        log_message(f"💩 error while running {account['user']}")
                        break

                if all_success and link_var.get():
                    link_links = [line.strip() for line in link_text.get("1.0", tk.END).splitlines() if line.strip()]
                    if link_links:
                        success = session_manager.action(account['user'], "comment", "", comments, num_posts, account['user'], links=link_links)
                        if not success:
                            all_success = False
                            log_message(f"💩 error while running {account['user']}")
                            break

                if all_success:
                    log_message(f"💜 finished commenting for {account['user']}")

            # report    
            if report_var.get():
                all_success = True
                for link in reports:
                    success = session_manager.action(account['user'], "report", link)
                    if not success:
                        all_success = False
                        log_message(f"💩 error while running {account['user']}")
                        break
                if all_success:
                    log_message(f"💜 finished reporting for {account['user']}")
            
            # post new
            if post_new_var.get():
                caption = [line.strip() for line in caption_text.get("1.0", tk.END).strip().split("\n") if line.strip()]
                tags = [line.strip().lstrip("@")
                        for line in post_accounts_text.get("1.0", tk.END).strip().split("\n") if line.strip()]
                hashtags = [line.strip().lstrip("#") 
                            for line in post_hashtags_text.get("1.0", tk.END).strip().split("\n") if line.strip()]
                images = [line.strip() 
                            for line in post_images_text.get("1.0", tk.END).strip().split("\n") if line.strip()]
                if not images:
                    log_message(f"💩 no images provided for {account['user']}")
                elif not tags:
                    log_message(f"💩 no tag accounts provided for {account['user']}")
                else:
                    for image in images:
                        if stop_event.is_set():
                            break
                        success = session_manager.action(account['user'], "post", [image], tags, caption.copy() if isinstance(caption, list) else caption, hashtags, account['user'])
                        if not success:
                            log_message(f"💩 error while running {account['user']}")
                            break
            notification.notify(
                message=f"💜 finished: {account['user']}",
                timeout=3
            )
        except Exception as e:
            safe_showerror("error", f"error for {account['user']}: {str(e)}")
        finally:            
            pass

    root.after(0, save_input)
    notification.notify(
        message=f"💜 finished all accounts",
        timeout=3
    )

# run bot in a separate thread
def threaded_start_bot():
    threading.Thread(target=start_bot).start()

# GUI setup
root = tk.Tk()
root.title("ig auto bot 🐥")
root.resizable(False, False)

num_posts_var = tk.StringVar(value="5")
comment_var = tk.BooleanVar(value=False)
target1_var = tk.BooleanVar(value=False)
target2_var = tk.BooleanVar(value=False)
link_var = tk.BooleanVar(value=False)
report_var = tk.BooleanVar(value=False)
post_new_var = tk.BooleanVar(value=False)

main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

author_label = tk.Label(main_frame, text="by mduong", fg="gray")
author_label.pack(anchor=tk.SE)

# left frame
left_frame = tk.LabelFrame(main_frame, text="settings", padx=10, pady=10)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# accounts
tk.Label(left_frame, text="accounts (USERNAME:PASSWORD):").pack(anchor=tk.W)
accounts_text = tk.Text(left_frame, height=3, width=40)
accounts_text.pack(fill=tk.X, pady=2)
accounts_text.insert(tk.END, "username1:password1\nusername2:password2")

# checkboxes
checkbox_frame = tk.Frame(left_frame)
checkbox_frame.pack(fill=tk.X, pady=5)

tk.Checkbutton(
    checkbox_frame,
    text="comment + like + save",
    variable=comment_var,
    command=toggle_conditional_frames
).pack(anchor=tk.W)

tk.Checkbutton(
    checkbox_frame,
    text="report",
    variable=report_var,
    command=toggle_conditional_frames
).pack(anchor=tk.W)

tk.Checkbutton(
    checkbox_frame,
    text="post",
    variable=post_new_var,
    command=toggle_conditional_frames
).pack(anchor=tk.W)

# comment
comment_frame = tk.Frame(left_frame)

# number of posts
num_posts_frame = tk.Frame(comment_frame)
tk.Label(num_posts_frame, text="number of posts (rcm <= 12):").pack(side=tk.LEFT)
num_posts_entry = tk.Entry(num_posts_frame, textvariable=num_posts_var, width=5)
num_posts_entry.pack(side=tk.LEFT, padx=5)
num_posts_frame.pack(fill=tk.X, pady=2)

# comments box
tk.Label(comment_frame, text="comments/leave empty to like posts only:").pack(anchor=tk.W)
comments_text = tk.Text(comment_frame, height=5, width=40)
comments_text.pack(fill=tk.X, pady=2)
comments_text.insert(tk.END, "nice pic 😍\nlove it 😘\namazing 🤩")

target1_checkbox = tk.Checkbutton(
    comment_frame,
    text="account_target1",
    variable=target1_var,
    anchor=tk.W
)
target1_checkbox.pack(fill=tk.X, pady=2)

target2_checkbox = tk.Checkbutton(
    comment_frame,
    text="account_target2",
    variable=target2_var,
    anchor=tk.W
)
target2_checkbox.pack(fill=tk.X, pady=2)

link_frame = tk.Frame(comment_frame)
link_checkbox = tk.Checkbutton(
    link_frame,
    text="link post",
    variable=link_var,
    anchor=tk.W
)
link_checkbox.pack(side=tk.LEFT)
link_frame.pack(fill=tk.X, pady=2) 

link_label = tk.Label(comment_frame, text="links of posts (posts/reels):")
link_text = tk.Text(comment_frame, height=4, width=40)

# report
report_frame = tk.Frame(left_frame)
tk.Label(report_frame, text="links/usernames to report:").pack(anchor=tk.W)
report_text = tk.Text(report_frame, height=4, width=40)
report_text.pack(fill=tk.X, pady=2)
report_text.insert(tk.END, """spam_account1
https://instagram.com/spam_account2
instagram.com/spam_account3""")

# right frame
right_frame = tk.LabelFrame(main_frame, text="log", padx=10, pady=10)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# post new 
post_frame = tk.Frame(right_frame)
tk.Label(post_frame, text="captions for posts (optional):").pack(anchor=tk.W)
caption_text = tk.Text(post_frame, height=3, width=35)
caption_text.pack(fill=tk.X, pady=2)
caption_text.insert(tk.END, "comment1\ncomment2")

tk.Label(post_frame, 
         text="tag accounts:\n" \
        "*must tag account_target1 or account_target2", 
        anchor=tk.W, 
        justify=tk.LEFT).pack(anchor=tk.W)
post_accounts_text = tk.Text(post_frame, height=3, width=35)
post_accounts_text.insert(tk.END, "account_target1\naccount_target2\nusername3")
post_accounts_text.pack(fill=tk.X, pady=2)

tk.Label(post_frame, text="hashtags (optional):").pack(anchor=tk.W)
post_hashtags_text = tk.Text(post_frame, height=2, width=35)
post_hashtags_text.insert(tk.END, "#hashtag1\n#hashtag2")
post_hashtags_text.pack(fill=tk.X, pady=2)

tk.Label(post_frame, text="images/videos (filenames, in same folder):").pack(anchor=tk.W)
post_images_text = tk.Text(post_frame, height=2, width=35)
post_images_text.pack(fill=tk.X, pady=2)
post_images_text.insert(tk.END, "image1.jpg\nimage2.png\nvideo1.mp4\nvideo2.mov")

# log ở bottom_right
log_text = tk.Text(
    right_frame, 
    height=8, 
    width=35, 
    state=tk.DISABLED
    )
log_text.pack(fill=tk.BOTH, expand=True)
log_text.tag_configure("center", justify='center')

log_text.config(state=tk.NORMAL)
log_text.insert("1.0", "hdsd: README.md\n\n=====log=====\n", "center")
log_text.config(state=tk.DISABLED)

# start button
start_button = tk.Button(
    root, 
    text="start", 
    command=threaded_start_bot, 
    state=tk.DISABLED, 
    bg="white", 
    fg="black"
    )
start_button.pack(pady=10)

# bind events
for widget in [
    accounts_text, 
    comments_text, 
    report_text, 
    caption_text, 
    post_accounts_text, 
    post_hashtags_text, 
    post_images_text, 
    num_posts_entry
    ]:
    widget.bind("<KeyRelease>", lambda e: update_start_button())
for var in [comment_var, link_var, report_var, post_new_var]:
    var.trace_add("write", lambda *args: toggle_conditional_frames())

# session manager
session_manager = SessionManager(log_message)

# def close
def on_closing():
    if messagebox.askyesno("quit", "do u wanna quit 🐥"):
        stop_event.set()
        session_manager.stop_all()
        root.destroy()
root.protocol("WM_DELETE_WINDOW", on_closing)

# initial load
load_input()
toggle_conditional_frames()
update_start_button()
root.mainloop()