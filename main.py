import getpass
import sys
import os
from concurrent.futures import ThreadPoolExecutor
import subprocess
import threading
import time
import shutil
from datetime import datetime
import webbrowser

import customtkinter
from CTkMessagebox import CTkMessagebox
from PIL import Image
from customtkinter import CTkImage

# pip install CTkMessagebox
# pip install customtkinter


# This Function just for convert the src to EXE
def resource_path(relative_path):
    """ Get the absolute path to a resource, works for dev and PyInstaller bundles """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class tmpCleaner:
    def __init__(self):
        self.driver = "C:/"
        self.storage_info = self.get_storage_info()
        self.files = []

    def get_storage_info(self):
        total, used, free = shutil.disk_usage(self.driver)

        return {
            "driver": self.driver,
            "total": self.convert_size(total),
            "used": self.convert_size(used),
            "free": self.convert_size(free),
            "used_raw": used,
            "free_raw": free
        }

    def convert_size(self, size_bytes):
        if size_bytes >= (1024 ** 3):
            return f"{size_bytes / (1024 ** 3):.2f} GB"
        elif size_bytes >= (1024 ** 2):
            return f"{size_bytes / (1024 ** 2):.2f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes} bytes"

    @staticmethod
    def get_user():
        return str(getpass.getuser())

    def count_files(self, host):
        host_to_path = {
            "tmp": [os.environ.get('TEMP'), os.environ.get('TMP'), rf"C:\Users\{self.get_user()}\AppData\Local\Temp", r"C:\windows\Temp"],
            "INetCache": [fr"C:\Users\{self.get_user()}\AppData\Local\Microsoft\Windows\INetCache\IE"],
            "MicrosoftEdgeCache": [fr"C:\Users\{self.get_user()}\AppData\Local\Microsoft\Edge\User Data\Default\Cache"],
            "GoogleChromCache": [fr"C:\Users\{self.get_user()}\AppData\Local\Google\Chrome\User Data\Default\Cache"],
            "RecycleBinFiles": [r"C:\$Recycle.Bin"],
            "VideosandPhotos": [
                r"C:\Users\Public\Videos",
                rf"C:\Users\{self.get_user()}\Videos",
                rf"C:\Users\{self.get_user()}\Pictures"
            ],
        }


        paths = host_to_path.get(host, [])

        if not paths:
            print(f"Invalid host: {host}")
            return

        if not isinstance(paths, list):
            paths = [paths]

        for path in paths:
            if path == r"C:\$Recycle.Bin":
                if not os.path.exists(path):
                    continue

                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            self.files.append({
                                "file_name": file,
                                "file_path": file_path,
                                "file_size_raw": file_size,
                                "file_size": self.convert_size(file_size),
                            })
                        except (PermissionError, FileNotFoundError):
                            continue
            else:
                if not path or not os.path.exists(path):
                    continue
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                        except (PermissionError, FileNotFoundError):
                            continue

                        self.files.append({
                            "file_name": file,
                            "file_path": file_path,
                            "file_size_raw": file_size,
                            "file_size": self.convert_size(file_size),
                        })


class UI:
    def __init__(self):
        self.root = customtkinter.CTk()
        self.nav_sections = ["Home", "Terminal", "Settings", "Info"]
        self.nav_buttons = {}
        self.section_frames = {}
        self.global_font = ("Arial", 14, "bold")

        self.diskManager = tmpCleaner()

    def run(self):
        self.set_ui_setting()
        self.set_nav()
        self.set_content()
        self.root.after(500, self.show_alert, "warning", "Please be careful when using this tool.", "This tool may delete important files. Always double-check your selections to avoid unintended data loss.")  # Show alert after 500ms
        self.log("none", "Starting The Tool")
        self.log("none", f"Using Driver : {self.diskManager.driver}")
        self.root.mainloop()

    def close(self):
        return self.root.quit()

    def set_ui_setting(self):
        window_width, window_height = 930, 570
        customtkinter.set_default_color_theme("dark-blue")
        customtkinter.set_appearance_mode("dark")
        customtkinter.deactivate_automatic_dpi_awareness()
        self.root.title("tmpCleaner")
        self.root.resizable(False, False)
        self.root.iconbitmap(resource_path("img/img.ico"))

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_position = (screen_width // 2) - (window_width // 2)
        y_position = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

    def set_nav(self):
        nav_frame = customtkinter.CTkFrame(self.root, width=150)
        nav_frame.pack(side="left", fill="y", padx=10, pady=10)

        for section in self.nav_sections:
            btn = customtkinter.CTkButton(
                nav_frame,
                text=section,
                command=lambda sec=section: self.handle_nav_click(sec),
                corner_radius=10,
                fg_color="#191919",
                hover_color="#565656",
                text_color="#ffffff",
                font=self.global_font
            )
            btn.pack(fill="x", pady=10, padx=10)
            self.nav_buttons[section] = btn


        exit_button = customtkinter.CTkButton(
            nav_frame,
            text="Exit",
            command=self.close,
            corner_radius=10,
            fg_color="#2D1F1F",
            hover_color="#8B0000",
            text_color="#FF4500",
            font=self.global_font
        )
        exit_button.pack(side="bottom", pady=10, padx=10)

    def log(self, _type, message):
        timestamp = datetime.now().strftime("%d-%m-%Y %I:%M %p")
        message = f"[{timestamp}] {message}\n"

        self.terminal_text.configure(state="normal")

        # Determine the color for the message
        if _type == "warning":
            color = "#FFA500"
            tag = "warning"
        elif _type == "error":
            color = "#FF0000"
            tag = "error"
        elif _type == "success":
            color = "#00FF00"
            tag = "success"
        elif _type == "info":
            color = "#00BFFF"
            tag = "info"
        else:
            color = "#FFFFFF"
            tag = "default"

        # Insert the message into the terminal
        self.terminal_text.insert("end", message)

        # Get the start and end indices for the message
        start_index = f"{self.terminal_text.index('end')}-{len(message) + 1}c"
        end_index = self.terminal_text.index("end")

        # Create a unique tag for this message type
        self.terminal_text.tag_add(tag, start_index, end_index)
        self.terminal_text.tag_config(tag, foreground=color)

        self.terminal_text.see("end")
        self.terminal_text.configure(state="disabled")

    def handle_nav_click(self, section):
        for btn in self.nav_buttons.values():
            btn.configure(fg_color="#191919")
        self.nav_buttons[section].configure(fg_color="#03346E") # Highlight the selected button with a new color

        for frame in self.section_frames.values():
            frame.pack_forget()
        self.section_frames[section].pack(fill="both", expand=True, padx=20, pady=20)

    def set_content(self):
        for section in self.nav_sections:
            frame = customtkinter.CTkFrame(self.root)
            frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
            self.section_frames[section] = frame

            if section == "Home":
                try:
                    image_path = resource_path("img/img.png")
                    icon_image = CTkImage(Image.open(image_path), size=(200, 200))
                    icon_label = customtkinter.CTkLabel(frame, image=icon_image, text="")
                    icon_label.pack(pady=(20, 10))
                except Exception as e:
                    print(f"Error loading icon: {e}")

                self.analysis_row_frame = customtkinter.CTkFrame(frame)
                self.analysis_row_frame.pack(fill="x", padx=20, pady=20)

                storage_info = self.diskManager.get_storage_info()
                box_data = [
                    ("Driver Name", storage_info['driver']),
                    ("Total Space", storage_info['total']),
                    ("Used Space", storage_info['used']),
                    ("Free Space", storage_info['free'])
                ]

                for title, description in box_data:
                    element_frame = customtkinter.CTkFrame(self.analysis_row_frame, corner_radius=10, width=150, height=100)
                    element_frame.pack(side="left", padx=10, pady=10, expand=True, fill="both")
                    title_label = customtkinter.CTkLabel(element_frame, text=title, font=self.global_font)
                    title_label.pack(pady=(10, 2))
                    description_label = customtkinter.CTkLabel(element_frame, text=description, font=("Arial", 12))
                    description_label.pack(pady=(0, 10))

                self.start_button = customtkinter.CTkButton(
                    frame,
                    text="Start",
                    command=self.start_clean,
                    corner_radius=10,
                    fg_color="#006400",
                    hover_color="#008000",
                    text_color="#ffffff",
                    font=self.global_font,
                    width=200
                )
                self.start_button.pack(pady=(20, 5))

                separator_label = customtkinter.CTkLabel(
                    frame,
                    text="* Please review and configure all settings in the 'Settings' section before running the tool .",
                    text_color="#B0B0B0",
                    font=("Arial", 12)
                )
                separator_label.pack(fill="x", pady=(0, 0))

                self.progress_frame = customtkinter.CTkFrame(frame)
                self.progress_frame.pack(fill="x", padx=20, pady=10)
                self.progress_bar = customtkinter.CTkProgressBar(self.progress_frame, orientation="horizontal", mode="determinate")
                self.progress_bar.pack(side="left", fill="x", expand=True)
                self.progress_bar.set(0)
                self.percentage_label = customtkinter.CTkLabel(self.progress_frame, text="0%", font=("Arial", 12))
                self.percentage_label.pack(side="right", padx=10)
                self.progress_frame.pack_forget()

                self.LiveLabel = customtkinter.CTkLabel(
                    frame,
                    text="Hola",
                    text_color="#B0B0B0",
                    font=self.global_font
                )
                # self.LiveLabel.pack(fill="x", pady=(0, 0))
                self.LiveLabel.pack_forget()

            elif section == "Terminal":
                terminal_text = customtkinter.CTkTextbox(
                    frame,
                    font=self.global_font,
                    fg_color="#000000",
                    text_color="#ffffff",
                    wrap="none",
                    state="normal",
                    height=400,

                )
                terminal_text.pack(fill="both", expand=True, padx=10, pady=10)

                terminal_text.configure(state="disabled")
                self.terminal_text = terminal_text

            elif section == "Settings":
                # Row 1: Remove Microsoft Windows INetCache IE
                self.row1_frame = customtkinter.CTkFrame(frame)  # Row container
                self.row1_frame.pack(fill="x", padx=60, pady=(10, 10))

                self.checkbox1 = customtkinter.CTkCheckBox(self.row1_frame, text="")
                self.checkbox1.select()
                self.checkbox1.pack(side="left", padx=10, pady=5, anchor="center")

                self.text_frame1 = customtkinter.CTkFrame(self.row1_frame, fg_color="transparent")
                self.text_frame1.pack(side="left", fill="x", expand=True, padx=2, anchor="w")

                self.title_label1 = customtkinter.CTkLabel(
                    self.text_frame1,
                    text="Remove Microsoft Windows INetCache IE",
                    font=self.global_font,
                    text_color="#EEEEEE",
                )
                self.title_label1.pack(anchor="w", pady=(5, 0))

                self.button1 = customtkinter.CTkButton(
                    self.row1_frame,
                    text="More Info",
                    corner_radius=10,
                    fg_color="#191919",
                    hover_color="#565656",
                    text_color="#ffffff",
                    font=self.global_font,
                    width=100,
                    command=lambda: self.show_alert("info", "About Microsoft Windows INetCache IE", fr"The files in 'C:\Users\{self.diskManager.get_user()}\AppData\Local\Microsoft\Windows\INetCache\IE' are temporary internet cache files from Internet Explorer. It is safe to delete them to free up space and fix potential browsing issues.", file_path=fr"C:\Users\{self.diskManager.get_user()}\AppData\Local\Microsoft\Windows\INetCache\IE")
                )
                self.button1.pack(side="right", padx=10, pady=5, anchor="center")

                # Row 2: Remove Microsoft Edge Cache
                self.row2_frame = customtkinter.CTkFrame(frame)  # Row container
                self.row2_frame.pack(fill="x", padx=60, pady=(10, 10))

                self.checkbox2 = customtkinter.CTkCheckBox(self.row2_frame, text="")
                self.checkbox2.pack(side="left", padx=10, pady=5, anchor="center")

                self.text_frame2 = customtkinter.CTkFrame(self.row2_frame, fg_color="transparent")
                self.text_frame2.pack(side="left", fill="x", expand=True, padx=2, anchor="w")

                self.title_label2 = customtkinter.CTkLabel(
                    self.text_frame2,
                    text="Remove Microsoft Edge Cache",
                    font=self.global_font,
                    text_color="#EEEEEE",
                )
                self.title_label2.pack(anchor="w", pady=(5, 0))

                self.button2 = customtkinter.CTkButton(
                    self.row2_frame,
                    text="More Info",
                    corner_radius=10,
                    fg_color="#191919",
                    hover_color="#565656",
                    text_color="#ffffff",
                    font=self.global_font,
                    width=100,
                    command=lambda: self.show_alert(
                        "info",
                        "About Microsoft Edge Cache",
                        fr"The files in 'C:\Users\{self.diskManager.get_user()}\AppData\Local\Microsoft\Edge\User Data\Default\Cache' are temporary cache files from Microsoft Edge. It is safe to delete them to free up space and fix potential browsing issues.",
                        file_path=fr"C:\Users\{self.diskManager.get_user()}\AppData\Local\Microsoft\Edge\User Data\Default\Cache",
                    )
                )
                self.button2.pack(side="right", padx=10, pady=5, anchor="center")

                # Row 3: Remove Google Chrome Cache
                self.row3_frame = customtkinter.CTkFrame(frame)  # Row container
                self.row3_frame.pack(fill="x", padx=60, pady=(10, 10))

                self.checkbox3 = customtkinter.CTkCheckBox(self.row3_frame, text="")
                self.checkbox3.pack(side="left", padx=10, pady=5, anchor="center")

                self.text_frame3 = customtkinter.CTkFrame(self.row3_frame, fg_color="transparent")
                self.text_frame3.pack(side="left", fill="x", expand=True, padx=2, anchor="w")

                self.title_label3 = customtkinter.CTkLabel(
                    self.text_frame3,
                    text="Remove Google Chrome Cache",
                    font=self.global_font,
                    text_color="#EEEEEE",
                )
                self.title_label3.pack(anchor="w", pady=(5, 0))

                self.button3 = customtkinter.CTkButton(
                    self.row3_frame,
                    text="More Info",
                    corner_radius=10,
                    fg_color="#191919",
                    hover_color="#565656",
                    text_color="#ffffff",
                    font=self.global_font,
                    width=100,
                    command=lambda: self.show_alert(
                        "info",
                        "About Google Chrome Cache",
                        fr"The files in 'C:\Users\{self.diskManager.get_user()}\AppData\Local\Google\Chrome\User Data\Default\Cache' are temporary cache files from Google Chrome. It is safe to delete them to free up space and fix potential browsing issues.",
                        file_path=fr"C:\Users\{self.diskManager.get_user()}\AppData\Local\Google\Chrome\User Data\Default\Cache",
                    ),
                )
                self.button3.pack(side="right", padx=10, pady=5, anchor="center")

                # Row 4: Remove Temp files
                self.row4_frame = customtkinter.CTkFrame(frame)  # Row container
                self.row4_frame.pack(fill="x", padx=60, pady=(10, 10))

                self.checkbox4 = customtkinter.CTkCheckBox(self.row4_frame, text="")
                self.checkbox4.pack(side="left", padx=10, pady=5, anchor="center")
                self.checkbox4.select()

                self.text_frame4 = customtkinter.CTkFrame(self.row4_frame, fg_color="transparent")
                self.text_frame4.pack(side="left", fill="x", expand=True, padx=2, anchor="w")

                self.title_label4 = customtkinter.CTkLabel(
                    self.text_frame4,
                    text="Remove Temp files",
                    font=self.global_font,
                    text_color="#EEEEEE",
                )
                self.title_label4.pack(anchor="w", pady=(5, 0))

                self.button4 = customtkinter.CTkButton(
                    self.row4_frame,
                    text="More Info",
                    corner_radius=10,
                    fg_color="#191919",
                    hover_color="#565656",
                    text_color="#ffffff",
                    font=self.global_font,
                    width=100,
                    command=lambda: self.show_alert(
                        "info",
                        "About Temp Files",
                        fr"The files in 'C:\Users\{self.diskManager.get_user()}\AppData\Local\Temp' are temporary files. It is safe to delete them to free up space and resolve temporary file issues.",
                        file_path=fr"C:\Users\{self.diskManager.get_user()}\AppData\Local\Temp",
                    ),
                )
                self.button4.pack(side="right", padx=10, pady=5, anchor="center")

                # Row 5: Remove Recycle bin files
                self.row5_frame = customtkinter.CTkFrame(frame)  # Row container
                self.row5_frame.pack(fill="x", padx=60, pady=(10, 10))

                self.checkbox5 = customtkinter.CTkCheckBox(self.row5_frame, text="")
                self.checkbox5.pack(side="left", padx=10, pady=5, anchor="center")
                self.checkbox5.select()

                self.text_frame5 = customtkinter.CTkFrame(self.row5_frame, fg_color="transparent")
                self.text_frame5.pack(side="left", fill="x", expand=True, padx=2, anchor="w")

                self.title_label5 = customtkinter.CTkLabel(
                    self.text_frame5,
                    text="Remove Recycle bin files",
                    font=self.global_font,
                    text_color="#EEEEEE",
                )
                self.title_label5.pack(anchor="w", pady=(5, 0))

                self.button5 = customtkinter.CTkButton(
                    self.row5_frame,
                    text="More Info",
                    corner_radius=10,
                    fg_color="#191919",
                    hover_color="#565656",
                    text_color="#ffffff",
                    font=self.global_font,
                    width=100,
                    command=lambda: self.show_alert(
                        "info",
                        "About Recycle Bin Files",
                        "The Recycle Bin contains deleted files. Emptying it will free up space.",
                        file_path="C:\\$Recycle.Bin",
                    ),
                )
                self.button5.pack(side="right", padx=10, pady=5, anchor="center")

                # Row 6: Remove Videos\Photos
                self.row6_frame = customtkinter.CTkFrame(frame)  # Row container
                self.row6_frame.pack(fill="x", padx=60, pady=(10, 10))

                self.checkbox6 = customtkinter.CTkCheckBox(self.row6_frame, text="")
                self.checkbox6.pack(side="left", padx=10, pady=5, anchor="center")

                self.text_frame6 = customtkinter.CTkFrame(self.row6_frame, fg_color="transparent")
                self.text_frame6.pack(side="left", fill="x", expand=True, padx=2, anchor="w")

                self.title_label6 = customtkinter.CTkLabel(
                    self.text_frame6,
                    text="Remove Videos And Photos",
                    font=self.global_font,
                    text_color="#EEEEEE",
                )
                self.title_label6.pack(anchor="w", pady=(5, 0))

                self.button6 = customtkinter.CTkButton(
                    self.row6_frame,
                    text="More Info",
                    corner_radius=10,
                    fg_color="#191919",
                    hover_color="#565656",
                    text_color="#ffffff",
                    font=self.global_font,
                    width=100,
                    command=lambda: self.show_alert(
                        "info",
                        "About Videos and Photos",
                        "Removing videos and photos will free up significant space. Be cautious and back up important files.",
                    ),
                )
                self.button6.pack(side="right", padx=10, pady=5, anchor="center")

            elif section == "Info":
                info_frame = customtkinter.CTkFrame(frame)
                info_frame.pack(fill="both", expand=True, padx=20, pady=20)

                tool_name_label = customtkinter.CTkLabel(
                    info_frame,
                    text="tmpCleaner",
                    font=("Arial", 28, "bold")
                )
                tool_name_label.pack(pady=(30, 10))

                description_text = (
                    "tmpCleaner is a tool designed to help you clean up temporary files and directories from your system. "
                    "It helps free up disk space and improve system performance by removing unnecessary files."
                )
                description_label = customtkinter.CTkLabel(
                    info_frame,
                    text=description_text,
                    font=self.global_font,
                    wraplength=600,
                    justify="center"
                )
                description_label.pack(pady=(0, 20))

                social_frame = customtkinter.CTkFrame(info_frame, fg_color="transparent")
                social_frame.pack(side="bottom", pady=30)

                github_button = customtkinter.CTkButton(
                    social_frame,
                    text="GitHub",
                    command=lambda: self.open_link("https://github.com/AnonShade"),
                    corner_radius=10,
                    fg_color="#24292E",
                    hover_color="#333",
                    text_color="#FFFFFF",
                    font=self.global_font,
                    width=120
                )
                github_button.pack(side="left", padx=20)

                twitter_button = customtkinter.CTkButton(
                    social_frame,
                    text="Twitter",
                    command=lambda: self.open_link("https://x.com/_AnonShade"),
                    corner_radius=10,
                    fg_color="#1DA1F2",
                    hover_color="#0d8ddb",
                    text_color="#FFFFFF",
                    font=self.global_font,
                    width=120
                )
                twitter_button.pack(side="right", padx=20)

            else:
                label = customtkinter.CTkLabel(frame, text=f"Welcome to the {section} Section", font=("Arial", 20))
                label.pack(pady=20)

        self.handle_nav_click("Home")

    def show_alert(self, _type, title, message, file_path=None):

        def open_file_explorer(file_path):
            subprocess.Popen(f'explorer "{file_path}"')

        if _type == "warning":
            # Show the messagebox and get the clicked option
            result = CTkMessagebox(
                title=title,
                message=message,
                icon="warning",
                option_1="OK" if not file_path else "Open in File Explorer",
                option_2=None if not file_path else "OK",
                font=self.global_font,
                sound=True,
            ).get()

            if result == "Open in File Explorer":
                open_file_explorer(file_path)

        elif _type == "info":
            result = CTkMessagebox(
                title=title,
                message=message,
                icon="info",
                option_1="OK" if not file_path else "Open in File Explorer",
                option_2=None if not file_path else "OK",
                font=self.global_font,
                sound=True,
            ).get()
            if result == "Open in File Explorer":
                open_file_explorer(file_path)

        elif _type == "success":
            result = CTkMessagebox(
                title=title,
                message=message,
                icon="check",
                option_1="OK" if not file_path else "Open in File Explorer",
                option_2=None if not file_path else "OK",
                font=self.global_font,
                sound=True,
            ).get()
        else:
            pass

    def start_clean(self):
        self.log("info", "Starting The Tool ..")
        self.start_button.configure(
            state="disabled",
            text="Processing...",
            fg_color="#555555",
            hover_color="#555555",
        )

        self.progress_frame.pack(fill="x", padx=20, pady=10)
        self.progress_bar.set(0)
        self.percentage_label.configure(text="0%")

        self.LiveLabel.pack(fill="x", pady=(0, 0))
        self.LiveLabel.configure(text="Counting The Files...")

        threads = []

        def monitor_threads():
            total_size = sum(file["file_size_raw"] for file in self.diskManager.files)
            self.LiveLabel.configure(
                text=f"Found {len(self.diskManager.files)} Files | Size: {self.diskManager.convert_size(total_size)}"
            )
            self.LiveLabel.update_idletasks()

            if not any(thread.is_alive() for thread in threads):
                self.log("info", f"Found {len(self.diskManager.files)} Files")
                self.LiveLabel.configure(
                    text=f"Found {len(self.diskManager.files)} Files | Size: {self.diskManager.convert_size(total_size)} (Completed)"
                )
                self.log("info", f"Files size : {self.diskManager.convert_size(total_size)}")
                time.sleep(5)
                self.clean()
                return
            self.root.after(500, monitor_threads)

        if self.checkbox1.get():
            self.log("warning", "Removing Microsoft Windows INetCache IE Temp Files")
            thread = threading.Thread(target=self.diskManager.count_files, args=("INetCache",))
            threads.append(thread)

        if self.checkbox2.get():
            self.log("warning", "Removing Microsoft Edge Cache Temp Files")
            thread = threading.Thread(target=self.diskManager.count_files, args=("MicrosoftEdgeCache",))
            threads.append(thread)

        if self.checkbox3.get():
            self.log("warning", "Removing Google Chrome Cache Temp Files")
            thread = threading.Thread(target=self.diskManager.count_files, args=("GoogleChromCache",))
            threads.append(thread)

        if self.checkbox4.get():
            self.log("warning", "Removing All Temp Files")
            thread = threading.Thread(target=self.diskManager.count_files, args=("tmp",))
            threads.append(thread)

        if self.checkbox5.get():
            self.log("warning", "Removing Recycle Bin Files Files")
            thread = threading.Thread(target=self.diskManager.count_files, args=("RecycleBinFiles",))
            threads.append(thread)

        if self.checkbox6.get():
            self.log("warning", "Removing Videos And Photos")
            thread = threading.Thread(target=self.diskManager.count_files, args=("VideosandPhotos",))
            threads.append(thread)

        for thread in threads:
            thread.start()

        monitor_threads()

    def update_progress(self, progress):
        self.progress_bar.set(progress)
        percentage = int(progress * 100)
        self.percentage_label.configure(text=f"{percentage}%")

    def clean(self):
        self.log("warning", "Start Deleting The Files .. ")
        self.LiveLabel.configure(
            text=f"Deleting all temp files .."
        )

        def delete_target(target_path):
            try:
                if os.path.isfile(target_path):
                    os.remove(target_path)
                    self.log("info", f"Deleted file: {target_path}")
                elif os.path.isdir(target_path):
                    shutil.rmtree(target_path)
                    self.log("info", f"Deleted directory: {target_path}")
                else:
                    self.log("error", f"Unknown target type: {target_path}")
            except FileNotFoundError:
                self.log("error", f"File or directory not found: {target_path}")
            except PermissionError:
                self.log("error", f"Permission denied: {target_path}")
            except OSError as e:
                self.log("error", f"Error deleting {target_path}: {e}")
            except Exception as e:
                self.log("error", f"Unexpected error: {e}")

        def delete_files_and_dirs():
            total_targets = len(self.diskManager.files)
            if total_targets == 0:
                self.update_progress(0.8)
                time.sleep(0.5)
                self.end_of_scan()
                return

            progress = 0
            progress_lock = threading.Lock()
            progress_increment = 0.8 / total_targets

            with ThreadPoolExecutor(max_workers=20) as executor:
                for file_info in self.diskManager.files:
                    target_path = file_info["file_path"]
                    executor.submit(delete_target, target_path)
                    with progress_lock:
                        progress += progress_increment
                        self.update_progress(min(progress, 0.8))

            self.update_progress(0.8)
            self.end_of_scan()

        threading.Thread(target=delete_files_and_dirs, daemon=True).start()

    def end_of_scan(self):
        # More Futures Soon ..

        old_storage = self.diskManager.storage_info["used_raw"]
        new_storage = self.diskManager.get_storage_info()["used_raw"]
        cleaned_data = old_storage - new_storage
        cleaned_data_human_readable = self.diskManager.convert_size(cleaned_data)

        for i in range(20):
            progress = 0.8 + (i + 1) * 0.01
            self.update_progress(progress)
            time.sleep(0.1)
        self.update_progress(1.0)

        self.LiveLabel.configure(text="Done! Your disk is now clean and free of temporary files. 🚀")
        self.show_alert("success", "Cleaning Complete", f"Done! Your disk is now clean and free of temporary files. And You cleaned {cleaned_data_human_readable} of data.🚀")
        self.log("success", "Done! Your disk is now clean and free of temporary files. 🚀")
        self.start_button.configure(
            text="Done",
            state="disabled",
            command=self.start_clean,
            corner_radius=10,
            fg_color="#006400",
            hover_color="#008000",
            text_color="#ffffff",
            font=self.global_font,
            width=200
        )

    def open_link(self, url):
        webbrowser.open(url)


app = UI()
app.run()
