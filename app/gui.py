import threading
import pyperclip
import requests
from io import BytesIO
from pathlib import Path
from PIL import Image
import customtkinter as ctk
from tkinter import messagebox, filedialog

from app.downloader import download_audio, clean_youtube_url


class App(ctk.CTk):
    def __init__(self):
        # Class constructing
        super().__init__()
        self.title("YT to MP3 Converter")
        self.geometry("500x500")
        self.resizable(False, False)
        self.configure(
            fg_color="#1e1e1e",  # Background color of window
            corner_radius=10,  # Rounded window corners (not all platforms)
        )
        # Setting up object to delay function call:
        self.url_check_timer = None

        # Tracking if batch mode is ON/OFF
        self.is_batch_mode = False

        # Setting background color
        bg_color = self.cget("bg")  # get main window background color

        # Creating the place holder image:
        black_img = Image.new("RGB", (250, 200), "black")
        self.placeholder_image = ctk.CTkImage(
            light_image=black_img, dark_image=black_img, size=(250, 150)
        )

        # Default download folder for mp3:
        self.output_folder = str(Path.home() / "Downloads")

        # -------------------------FRAMES----------------------------------

        # Input frame - fixed spot in the main layout 1 (row=0)
        self.input_frame = ctk.CTkFrame(
            self, fg_color=bg_color, border_width=0, corner_radius=0
        )
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_rowconfigure(1, weight=1)
        self.input_frame.grid(row=0, column=0, sticky="ew", pady=5)

        # Name frame - fixed spot in the main layout 2 (row=1)
        self.name_frame = ctk.CTkFrame(
            self, fg_color=bg_color, border_width=0, corner_radius=0
        )
        self.name_frame.grid_columnconfigure(0, weight=1)
        self.name_frame.grid(row=1, column=0, sticky="ew", pady=5)

        # Thumbnail frame - fixed spot in the main layout 3 (row=2)
        self.thumbnail_frame = ctk.CTkFrame(
            self, fg_color=bg_color, border_width=0, corner_radius=0
        )
        self.thumbnail_frame.grid_columnconfigure(0, weight=1)
        self.thumbnail_frame.grid(row=2, column=0, sticky="ew", pady=5)

        # Directory frame - fixed spot in the main layout 4 (row=3)
        self.directory_frame = ctk.CTkFrame(
            self, fg_color=bg_color, border_width=0, corner_radius=0
        )
        self.directory_frame.grid_columnconfigure(0, weight=1)
        self.directory_frame.grid(row=3, column=0, sticky="ew", pady=5)

        # Button frame - fixed spot in the main layout 5 (row=4)
        self.button_frame = ctk.CTkFrame(
            self, fg_color=bg_color, border_width=0, corner_radius=0
        )
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid(row=4, column=0, sticky="ew", pady=5)

        # Status frame - fixed spot in the main layout 6 (row=5)
        self.status_frame = ctk.CTkFrame(
            self, fg_color=bg_color, border_width=0, corner_radius=0
        )
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid(row=5, column=0, sticky="ew", pady=5)

        # Optionally, make the column stretch to fill horizontal space
        self.grid_columnconfigure(0, weight=1)
        # -----------------------FRAMES END--------------------------------

        # -------------------------- Input frame widgets ------------------------------
        # Batch
        self.batch_label = ctk.CTkLabel(
            self.input_frame, text="Batch URLs (one per line)"
        )
        self.batch_label.grid(row=0, column=0, pady=(5, 0), sticky="")
        self.batch_label.grid_remove()

        self.batch_textbox = ctk.CTkTextbox(
            self.input_frame,
            height=244,
            width=400,
            fg_color="#2b2b2b",
            text_color="white",
        )
        self.batch_textbox.grid(row=1, column=0, pady=(5, 5), sticky="")
        self.batch_textbox.bind("<<Paste>>", self.on_batch_paste)
        self.batch_textbox.grid_remove()

        # Single
        self.url_label = ctk.CTkLabel(self.input_frame, text="YouTube URL")
        self.url_label.grid(row=0, column=0, pady=(5, 0), sticky="")

        self.url_entry = ctk.CTkEntry(self.input_frame, width=400, justify="center")
        self.url_entry.grid(row=1, column=0, pady=5, sticky="")

        # Pasting the string from the clipboard if its a valid link(not exactly YT link):
        clipboard_url = (
            pyperclip.paste() if pyperclip.paste().startswith(("http", "www")) else ""
        )
        self.url_entry.insert(0, clipboard_url)
        self.url_entry.bind("<KeyRelease>", self.on_url_change)
        self.url_entry.bind("<KeyRelease>", lambda e: print(e))

        # Logging for the URL input:
        self.url_entry.bind("<KeyRelease>", lambda e: print(e))
        # ----------------------------------------------------------------------------

        # -------------------------- Name frame widgets ------------------------------
        self.name_label = ctk.CTkLabel(self.name_frame, text="MP3 File Name (optional)")
        self.name_label.grid(row=0, column=0, pady=(5, 0), sticky="")

        self.name_entry = ctk.CTkEntry(
            self.name_frame,
            width=400,
            justify="center",
            placeholder_text="Output file name",
        )
        self.name_entry.grid(row=1, column=0, pady=5, sticky="")
        # ---------------------------------------------------------------------------

        # ---------------------- Thumbnail frame widgets ----------------------------
        self.thumb_label = ctk.CTkLabel(
            self.thumbnail_frame, text="", width=250, height=150
        )
        self.thumb_label.grid(row=0, column=0, pady=(5, 0), sticky="")
        # ---------------------------------------------------------------------------

        # ---------------------- Directory frame widgets ----------------------------
        self.output_button = ctk.CTkButton(
            self.directory_frame,
            text="Select Output Folder",
            command=self.select_folder,
        )
        self.output_button.grid(row=1, column=0, pady=5, sticky="")

        self.folder_path_label = ctk.CTkLabel(
            self.directory_frame,
            text=f"{self.output_folder}",
            wraplength=440,
            text_color="white",
        )
        self.folder_path_label.grid(row=2, column=0, pady=5, sticky="")
        # ----------------------------------------------------------------------------

        # ------------------------ Button frame widgets ------------------------------
        self.batch_button = ctk.CTkButton(
            self.button_frame, text="Batch Mode ", command=self.toggle_batch_mode
        )
        self.batch_button.grid(row=1, column=0, padx=11, sticky="e")

        self.download_button = ctk.CTkButton(
            self.button_frame, text="Download MP3", command=self.download
        )
        self.download_button.grid(row=1, column=1, padx=11, sticky="w")
        # ----------------------------------------------------------------------------

        # ------------------------ Status frame widgets ------------------------------
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Idle",
            text_color="gray",
            font=("Arial", 12, "italic"),
        )
        self.status_label.grid(row=1, column=0, pady=5, sticky="")
        # ----------------------------------------------------------------------------

        # Show thumbnail or placeholder initially if URL is present in the clipboard
        if clipboard_url:
            print(f"Pasting URL from clipboard: {clipboard_url}")
            self.show_thumbnail_from_url(clipboard_url)
        else:
            self.show_placeholder(self.placeholder_image)

    # ------------------------- FUNCTIONS -------------------------------

    def on_batch_paste(self, event):
        cursor_pos = self.batch_textbox.index("insert")
        clipboard = self.batch_textbox.clipboard_get()
        self.batch_textbox.insert(cursor_pos, clipboard)
        self.batch_textbox.insert(cursor_pos + f"+{len(clipboard)}c", "\n")
        return "break"

    def toggle_batch_mode(self):
        self.is_batch_mode = not self.is_batch_mode

        if self.is_batch_mode:
            print("Batch mode ON")

            # Hide single URL inputs
            self.url_label.grid_remove()
            self.url_entry.grid_remove()

            # Hide name frame content + collapse the frame
            self.name_label.grid_remove()
            self.name_entry.grid_remove()
            self.name_frame.grid_propagate(False)
            self.name_frame.configure(height=5)

            # Hide thumbnail content + collapse the frame
            self.thumb_label.grid_remove()
            self.thumbnail_frame.grid_propagate(False)
            self.thumbnail_frame.configure(height=5)

            # Show batch widgets
            self.batch_label.grid()
            self.batch_textbox.grid()

        else:
            print("Batch mode OFF")

            # Hide batch widgets
            self.batch_label.grid_remove()
            self.batch_textbox.grid_remove()

            # Restore single URL inputs
            self.url_label.grid()
            self.url_entry.grid()

            # Show name frame + contents
            self.name_frame.configure(height=None)  # Reset height
            self.name_frame.grid_propagate(True)  # Let it resize
            self.name_label.grid()
            self.name_entry.grid()

            # Show thumbnail frame + contents
            self.thumbnail_frame.configure(height=None)  # Reset height
            self.thumbnail_frame.grid_propagate(True)
            self.thumb_label.grid()

    # Starts timer after the user URL input for the validity check:
    def on_url_change(self, event=None):
        if self.url_check_timer:
            self.url_check_timer.cancel()  # Cancel previous timer if still running

        self.url_check_timer = threading.Timer(0.7, self.check_url_validity)
        self.url_check_timer.start()

    # (Background thread) Swap to main thread, strips the URL and starts the process for validation:
    def check_url_validity(self):
        url = self.url_entry.get().strip()
        self.after(0, lambda: self._process_url(url))

    # Showing the thumbnail call:
    def _process_url(self, url):
        if url.startswith("http"):
            self.show_thumbnail_from_url(url)
        elif not url:
            self.show_placeholder(self.placeholder_image)

    # Showing the placeholder image from the memory:
    def show_placeholder(self, ctk_image):
        print("Showing placeholder thumbnail")
        self.thumb_label.configure(image=ctk_image)
        self.thumb_label.image = ctk_image

    # Showing the thumbnail of the video:
    def show_thumbnail_from_url(self, url):
        print(f"Fetching thumbnail for URL: {url}")
        try:
            # 1. Extract the YouTube video ID from the URL (you need a method `extract_video_id` for this)
            video_id = self.extract_video_id(url)

            if video_id:
                # 2. Construct the thumbnail URL based on the video ID
                thumb_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

                # 3. Send a GET request to fetch the thumbnail image bytes
                response = requests.get(thumb_url, timeout=3)

                # 4. Open the image from the downloaded bytes and resize it to 250x150 px
                image = Image.open(BytesIO(response.content)).resize((250, 150))

                # 5. Wrap the image for CustomTkinter to handle light/dark mode
                ctk_image = ctk.CTkImage(
                    light_image=image, dark_image=image, size=(250, 150)
                )

                # 6. Update your thumbnail label to display this image
                self.thumb_label.configure(image=ctk_image)
                self.thumb_label.image = (
                    ctk_image  # keep reference to prevent garbage collection
                )

                print(f"Thumbnail loaded for video ID: {video_id}")
            else:
                # If video ID couldn't be extracted, show the placeholder instead
                print("Invalid video ID, showing placeholder")
                self.show_placeholder()

        except Exception as e:
            # Catch any errors (network, invalid image, etc.) and fallback to placeholder
            print(f"Exception while loading thumbnail: {e}")
            self.show_placeholder()

    # Extracting the ID of the video from the URL:
    def extract_video_id(self, url):
        if "v=" in url:
            return url.split("v=")[-1].split("&")[0]
        elif "youtu.be/" in url:
            return url.split("youtu.be/")[-1].split("?")[0]
        return None

    # User choice of the output folder:
    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder = folder
            self.folder_path_label.configure(
                text=f"Output Folder: {self.output_folder}"
            )

    # Update for the status widget:
    def update_status(self, message, color="gray"):
        print(f"Status update: {message}")
        self.status_label.configure(text=message, text_color=color)

    # Initialization/preparation for video download:
    def download(self):
        if self.is_batch_mode:
            self.batch_download()
        else:
            url = self.url_entry.get().strip()
            url = clean_youtube_url(url)
            name = self.name_entry.get().strip()

            if not url:
                messagebox.showerror("Error", "Please enter a YouTube URL")
                print("Download error: No URL entered")
                return

            self.update_status("Downloading...", "orange")
            self.show_thumbnail_from_url(url)

            # Starts the download process in the side thread:
            threading.Thread(
                target=self._run_download, args=(url, name), daemon=True
            ).start()

    def _run_download(self, url, name):
        try:
            print(f"Download started for URL: {url}")

            # Download audio (blocking call)
            download_audio(url, self.output_folder, name if name else None)

            # Schedule UI update back on main thread
            self.after(0, lambda: self.update_status("Download complete!", "green"))
            print("Download succeeded")

        except Exception as e:
            self.after(0, lambda: self.update_status("Failed to download", "red"))
            print(f"Download failed: {e}")
            self.after(0, lambda: messagebox.showerror("Error", str(e)))

    # Initialize batch download in the side thread:
    def batch_download(self):
        self.after(
            0, lambda: self.update_status("Starting batch download...", "orange")
        )
        if not hasattr(self, "batch_textbox"):
            messagebox.showerror("Error", "Batch mode is not enabled.")
            return
        urls_text = self.batch_textbox.get("1.0", "end").strip()
        if not urls_text:
            messagebox.showerror("Error", "Please enter at least one URL")
            return

        # Now start the thread and pass the urls_text as argument
        threading.Thread(
            target=self._batch_download_worker, args=(urls_text,), daemon=True
        ).start()

    # Proper batch download:
    def _batch_download_worker(self, urls_text):
        urls = [url.strip() for url in urls_text.split() if url.strip()]
        print(f"Batch downloading {len(urls)} URLs")

        # Disable download buttons during batch
        self.after(
            0,
            lambda: (
                self.download_button.configure(state="disabled"),
                self.batch_button.configure(state="disabled"),
            ),
        )

        for i, url in enumerate(urls, start=1):
            try:
                clean_url = clean_youtube_url(url)
                name = download_audio(clean_url, self.output_folder)
                self.after(
                    0,
                    lambda name=name, idx=i: self.update_status(
                        f"Downloaded {idx}/{len(urls)}: {name}", "green"
                    ),
                )
            except Exception as e:
                self.after(
                    0,
                    lambda url=url, idx=i: self.update_status(
                        f"Failed {idx}/{len(urls)}: {url}", "red"
                    ),
                )

        self.after(
            0, lambda: self.update_status("Batch download complete!", color="#800080")
        )

        # Re-enable buttons on main thread
        self.after(
            0,
            lambda: (
                self.download_button.configure(state="normal"),
                self.batch_button.configure(state="normal"),
            ),
        )
