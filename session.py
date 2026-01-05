import threading, time
from tkinter import messagebox
import main

class AccountSession:
    def __init__(self, username, password, logger):
        self.username = username
        self.password = password
        self.logger = logger
        self.driver = None
        self.thread = None
        self.stop_event = threading.Event()
        self.last_action_time = time.time()
        self.ready_event = threading.Event()
        self.login_ok = False

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        try:
            self.driver = main.setup_driver()
            if not self.driver:
                self.login_ok = False
                self.ready_event.set()
                return
            
            self.login_ok = main.login(self.driver, self.username, self.password)
            if self.login_ok:
                self.logger(f"💜 login in as {self.username}")
            else:
                self.logger(f"💩 login failed for {self.username}")

            self.ready_event.set()

            if not self.login_ok:
                self.login_ok = False
                self.ready_event.set()
                return
            while not self.stop_event.is_set():
                if time.time() - self.last_action_time > 600:
                    try:
                        ans = messagebox.askyesno("session idle", f"session {self.username} idle for 10 min. close? 💩")
                    except Exception:
                        ans = True
                    if ans:
                        self.stop()
                        return
                    self.stop_event.wait(60)
                time.sleep(1)

        except Exception as e:
            self.logger(f"💩 error in session {self.username}: {e}")
            self.login_ok = False
            self.ready_event.set()
        finally:
            if self.driver:
                self.driver.quit()
                self.logger(f"💜 session {self.username} closed")

    def do_action(self, action, *args, **kwargs):
        if not self.driver or not self.driver.service.is_connectable:
            self.logger(f"💩 session {self.username} not started or driver crashed")
            return
        self.last_action_time = time.time()
        try:
            if action == "comment":
                main.like_comment(self.driver, *args, **kwargs)
                res = True
            elif action == "report":
                main.report(self.driver, *args, **kwargs)
                res = True
            elif action == "post":
                res = main.post_new(self.driver, *args, **kwargs)
            else:
                res= False
            return res

        except main.AccountRestrictedError as e:
            self.logger(f"💩 {self.username} is restricted. session stopped")
            self.stop()
            return False
        except Exception as e:
            main.safe_showerror("action error", f"error doing {action} for {self.username}: {e}")
            return False
        
    def stop(self):
        self.stop_event.set()

class SessionManager:
    def __init__(self, logger):
        self.sessions = {}
        self.logger = logger

    def add_account(self, username, password):
        if username in self.sessions:
            self.logger(f"already running: {username}")
            return True
        session = AccountSession(username, password, self.logger)
        session.start()
        session.ready_event.wait()
        if not session.login_ok:
            self.sessions[username] = session
            return True
        self.sessions[username] = session
        self.logger(f"session started for {username}")
        return True

    def remove_account(self, username):
        if username in self.sessions:
            self.sessions[username].stop()
            self.sessions[username].thread.join()
            del self.sessions[username]
            self.logger(f"session stopped for {username}")

    def action(self, username, action, *args, **kwargs):
        if username in self.sessions:
            return self.sessions[username].do_action(action, *args, **kwargs)
        return False

    def stop_all(self):
        for username, session in list(self.sessions.items()):
            session.stop()
            if session.thread and session.thread.is_alive():
                session.thread.join()
            self.logger(f"session {username} stopped")
        self.sessions.clear()
