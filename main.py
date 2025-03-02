import os
import sys
import threading
from tkinter import BOTH, END, Listbox, Scrollbar, Y, messagebox
from tkinter import filedialog as fd

import ttkbootstrap as ttk
from PIL import Image, ImageSequence
from ttkbootstrap.constants import *

# Check if rembg is installed
try:
    from rembg import remove

    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False


class GIFProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GIF Processor")
        self.root.geometry("500x400+400+200")

        # Variables
        self.remove_bg = ttk.BooleanVar(value=False)
        self.export_png = ttk.BooleanVar(value=True)
        self.export_gif = ttk.BooleanVar(value=False)
        self.progress = ttk.DoubleVar(value=0)
        self.status = ttk.StringVar(value="Ready")

        self.create_widgets()

    def create_widgets(self):
        # Create a main frame to center the content
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(expand=True, fill="both")

        # Title
        title_label = ttk.Label(
            main_frame, text="GIF Processor", font=("Helvetica", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        # Options frame
        options_frame = ttk.Labelframe(main_frame, text="Options", padding=10)
        options_frame.pack(fill="x", pady=10)

        # Background removal checkbox
        bg_checkbox = ttk.Checkbutton(
            options_frame,
            text="Remove Background from GIF",
            variable=self.remove_bg,
            state="normal" if REMBG_AVAILABLE else "disabled",
            command=self.toggle_export_options,
        )
        bg_checkbox.pack(anchor="w", padx=10, pady=5)

        if not REMBG_AVAILABLE:
            warning_label = ttk.Label(
                options_frame,
                text="The 'rembg' package is not installed. Install with: pip install rembg",
                foreground="red",
            )
            warning_label.pack(anchor="w", padx=10, pady=5)

        # Export options frame
        self.export_frame = ttk.Frame(options_frame)
        self.export_frame.pack(fill="x", padx=25, pady=5)

        # Export PNG checkbox
        png_checkbox = ttk.Checkbutton(
            self.export_frame,
            text="Export PNG frames",
            variable=self.export_png,
        )
        png_checkbox.pack(anchor="w")

        # Export GIF checkbox
        self.gif_checkbox = ttk.Checkbutton(
            self.export_frame,
            text="Export processed GIF",
            variable=self.export_gif,
            state=DISABLED,
        )
        self.gif_checkbox.pack(anchor="w")

        # Hide export options if background removal is not selected
        if not self.remove_bg.get():
            self.export_frame.pack_forget()

        # Progress section
        progress_frame = ttk.Frame(main_frame, padding=10)
        progress_frame.pack(fill="x", pady=10)

        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress, length=100
        )
        self.progress_bar.pack(fill="x")

        self.status_label = ttk.Label(progress_frame, textvariable=self.status)
        self.status_label.pack(pady=5)

        # GIF selection button
        convert_button = ttk.Button(
            main_frame,
            text="Select and Process GIFs",
            command=self.process_gifs,
            bootstyle="primary",
            width=30,
        )
        convert_button.pack(pady=20)

    def toggle_export_options(self):
        # Show or hide export options based on background removal setting
        if self.remove_bg.get():
            self.export_frame.pack(fill="x", padx=25, pady=5)
            self.gif_checkbox.config(state=NORMAL)  # Enable the GIF checkbox
        else:
            self.export_frame.pack_forget()
            self.export_png.set(True)  # Default to PNG export when bg removal is off
            self.export_gif.set(False)  # Make GIF export off
            self.gif_checkbox.config(state=DISABLED)  # Disable the GIF checkbox

    def custom_file_dialog(self):
        dialog = ttk.Toplevel(self.root)
        dialog.title("Select GIF Files")
        dialog.geometry("600x400")

        # Frame for the file list
        frame = ttk.Frame(dialog)
        frame.pack(fill="both", expand=True)

        # Create a listbox with scrollbar
        file_listbox = Listbox(frame, selectmode="extended")
        file_listbox.pack(side="left", fill=BOTH, expand=True)

        scrollbar = Scrollbar(frame, command=file_listbox.yview)
        scrollbar.pack(side="right", fill=Y)
        file_listbox.config(yscrollcommand=scrollbar.set)

        # Load files from the directory
        initial_dir = os.path.expanduser("~")
        selected_dir = fd.askdirectory(
            initialdir=initial_dir, title="Select a Folder with GIF Files"
        )
        if not selected_dir:
            dialog.destroy()
            return []

        files = [
            os.path.join(selected_dir, f)
            for f in os.listdir(selected_dir)
            if f.lower().endswith(".gif")
        ]
        for file in files:
            file_listbox.insert(END, file)

        selected_files = []

        def select_all():
            file_listbox.select_set(0, END)

        def select_files():
            nonlocal selected_files
            selected_files = [
                file_listbox.get(idx) for idx in file_listbox.curselection()
            ]
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill="x")

        select_all_button = ttk.Button(
            button_frame, text="Select All", command=select_all
        )
        select_all_button.pack(side="left", padx=5, pady=5)

        ok_button = ttk.Button(button_frame, text="OK", command=select_files)
        ok_button.pack(side="left", padx=5, pady=5)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=dialog.destroy)
        cancel_button.pack(side="left", padx=5, pady=5)

        dialog.wait_window()
        return selected_files

    def process_gifs(self):
        """Main processing function"""
        import_filenames = self.custom_file_dialog()
        if not import_filenames:
            return  # No files selected

        # Validate export options
        if self.remove_bg.get() and not (
            self.export_png.get() or self.export_gif.get()
        ):
            messagebox.showerror(
                "Error", "Please select at least one export option (PNG or GIF)."
            )
            return

        # Start processing in a separate thread to keep UI responsive
        thread = threading.Thread(
            target=self.process_gifs_thread, args=(import_filenames,)
        )
        thread.daemon = True
        thread.start()

    def process_gifs_thread(self, import_filenames):
        """Thread for processing GIFs"""
        # Create the appropriate output directory
        base_dir = os.path.dirname(import_filenames[0])
        if self.remove_bg.get():
            output_dir = os.path.join(base_dir, "nobg_converted")
        else:
            output_dir = os.path.join(base_dir, "converted")

        os.makedirs(output_dir, exist_ok=True)

        total_files = len(import_filenames)
        for file_index, import_filename in enumerate(import_filenames):
            if import_filename.lower().endswith(".gif"):
                try:
                    self.status.set(
                        f"Processing {os.path.basename(import_filename)} ({file_index + 1}/{total_files})"
                    )
                    self.root.update_idletasks()

                    # Open the GIF file
                    im = Image.open(import_filename)
                    base_name = os.path.basename(import_filename).rsplit(".", 1)[0]

                    # Count frames to update progress
                    try:
                        frame_count = im.n_frames
                    except AttributeError:
                        max_frames = 1000
                        frame_count = 0
                        for _ in ImageSequence.Iterator(im):
                            frame_count += 1
                            if frame_count >= max_frames:
                                break

                    # Extract frames
                    frames = []
                    for i, frame in enumerate(ImageSequence.Iterator(im)):
                        self.status.set(
                            f"Processing {base_name}: frame {i + 1}/{frame_count}"
                        )
                        frame_progress = (file_index / total_files) * 100 + (
                            i / frame_count
                        ) * (100 / total_files)
                        self.progress.set(frame_progress)
                        self.root.update_idletasks()

                        # Convert to RGBA to ensure transparency is preserved
                        frame_rgba = frame.convert("RGBA")

                        # Remove background if option is checked
                        if self.remove_bg.get() and REMBG_AVAILABLE:
                            frame_rgba = remove(frame_rgba)

                        frames.append(frame_rgba.copy())

                    # Save each frame individually if PNG export is selected
                    if self.export_png.get():
                        self.status.set(f"Saving PNG frames for {base_name}")
                        for i, frame in enumerate(frames):
                            export_filename = os.path.join(
                                output_dir, f"{base_name}_frame_{i}.png"
                            )
                            frame.save(export_filename, "PNG")

                    # If background removal is enabled and GIF export is selected, save the processed GIF
                    if (
                        self.remove_bg.get()
                        and self.export_gif.get()
                        and REMBG_AVAILABLE
                    ):
                        self.status.set(f"Saving processed GIF for {base_name}")
                        gif_output_path = os.path.join(
                            output_dir, f"nobg_{base_name}.gif"
                        )

                        duration = im.info.get("duration", 100)
                        frames[0].save(
                            gif_output_path,
                            save_all=True,
                            append_images=frames[1:],
                            optimize=False,
                            duration=duration,
                            loop=0,
                            disposal=2,
                        )

                except Exception as e:
                    messagebox.showerror(
                        "Error", f"Failed to convert {import_filename}:\n{e}"
                    )
                    self.status.set(
                        f"Error processing {os.path.basename(import_filename)}"
                    )
                    continue

        self.progress.set(100)
        self.status.set("Processing complete!")
        messagebox.showinfo("Success", "All GIFs processed successfully!")


# Run the application
if __name__ == "__main__":
    try:
        root = ttk.Window(themename="cosmo")
        app = GIFProcessorApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error starting the application: {e}")
        if "_tkinter" in str(e) or "TclError" in str(e):
            print("\nPossible tkinter issues:")
            print("- Tkinter might not be installed or working properly.")
            print("- Try 'pip install python-tk' or use your system package manager.")
            print("- On Linux: sudo apt-get install python3-tk")
            print(
                "- On macOS: brew install python-tk@3.x (replace 3.x with your version)"
            )
        sys.exit(1)
