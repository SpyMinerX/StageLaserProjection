import tkinter as tk
from tkinter import ttk, filedialog
import pygame
import threading
from screeninfo import get_monitors
import os
import json
import glob
import math
import base64
import random
from tkinter.colorchooser import askcolor


class StageLaserProjectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stage Laser Projection")

        # Monitor selection
        self.monitor_label = tk.Label(root, text="Select Monitor for Projection:")
        self.monitor_label.pack(pady=5)

        self.monitor_combobox = ttk.Combobox(root, state="readonly")
        self.monitor_combobox.pack(pady=5)
        self.monitor_combobox['values'] = [f"Monitor {i + 1}: {m.width}x{m.height}" for i, m in
                                           enumerate(get_monitors())]
        self.monitor_combobox.current(0)

        # Scene folder selection
        self.folder_label = tk.Label(root, text="Select Folder with spyLAZ Files:")
        self.folder_label.pack(pady=5)

        self.folder_path = tk.StringVar(value="")
        self.folder_entry = tk.Entry(root, textvariable=self.folder_path, state="readonly", width=40)
        self.folder_entry.pack(pady=5)

        self.browse_button = tk.Button(root, text="Browse Folder", command=self.browse_folder)
        self.browse_button.pack(pady=5)

        # Scene selection
        self.scene_label = tk.Label(root, text="Select Scene for Laser Animation:")
        self.scene_label.pack(pady=5)

        self.scene_combobox = ttk.Combobox(root, state="readonly")
        self.scene_combobox.pack(pady=5)
        self.scene_combobox.bind("<<ComboboxSelected>>", self.change_scene)

        # Brightness slider
        self.brightness_label = tk.Label(root, text="Laser Brightness:")
        self.brightness_label.pack(pady=5)

        self.brightness_slider = tk.Scale(root, from_=0, to=255, orient="horizontal")
        self.brightness_slider.set(255)
        self.brightness_slider.pack(pady=5)

        # Multi-scene playback
        self.playback_label = tk.Label(root, text="Multi-Scene Playback (seconds per scene):")
        self.playback_label.pack(pady=5)

        self.playback_entry = tk.Entry(root, width=5)
        self.playback_entry.insert(0, "5")
        self.playback_entry.pack(pady=5)

        # Playback toggle
        self.playback_var = tk.BooleanVar(value=False)
        self.playback_checkbox = tk.Checkbutton(root, text="Enable Multi-Scene Playback",
                                                variable=self.playback_var)
        self.playback_checkbox.pack(pady=5)

        # Interactive Controls
        self.edit_button = tk.Button(root, text="Edit Scene Live", command=self.edit_scene_live)
        self.edit_button.pack(pady=5)

        # Start and Stop buttons
        self.start_button = tk.Button(root, text="Start Projection", command=self.start_scene)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(root, text="Stop Projection", command=self.stop_scene)
        self.stop_button.pack(pady=5)

        # Interactive log
        self.log_label = tk.Label(root, text="Log:")
        self.log_label.pack(pady=5)

        self.log_text = tk.Text(root, height=10, width=60, state="disabled")
        self.log_text.pack(pady=5)

        self.running = False
        self.current_scene_name = None
        self.selected_monitor = None
        self.playback_thread = None
        self.playback_active = False

        # Scene data
        self.scenes = {}
        self.current_objects = []

    def log(self, message):
        """Log a message to the interactive log."""
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.config(state="disabled")
        self.log_text.see("end")

    def browse_folder(self):
        """Open a file dialog to select a folder containing .spyLAZ files."""
        folder_selected = filedialog.askdirectory(title="Select Folder with spyLAZ Files")
        if folder_selected:
            self.folder_path.set(folder_selected)
            self.load_scenes()

    def load_scenes(self):
        """Load scenes from all .spyLAZ files in the selected folder."""
        folder = self.folder_path.get()
        if not folder:
            self.log("No folder selected.")
            return

        # Clear previous scenes
        self.scenes = {}

        try:
            # Scan folder for .spyLAZ files
            for file_path in glob.glob(os.path.join(folder, "*.spyLAZ")):
                with open(file_path, "rb") as file:
                    encoded_data = file.read()
                    decoded_data = base64.b64decode(encoded_data).decode("utf-8")
                    scene_data = json.loads(decoded_data)

                    # Ensure the file contains a valid scene
                    if "name" in scene_data and "objects" in scene_data:
                        self.scenes[scene_data["name"]] = scene_data
                    else:
                        self.log(f"Invalid scene format in file: {file_path}")

            # Update scene combobox
            self.scene_combobox["values"] = list(self.scenes.keys())
            if self.scenes:
                self.scene_combobox.current(0)
                self.current_scene_name = self.scene_combobox.get()
            self.log(f"Loaded {len(self.scenes)} scenes from {folder}.")
        except Exception as e:
            self.log(f"Error loading scenes from folder: {e}")

    def start_scene(self):
        """Start the projection."""
        if self.running:
            return

        monitor_index = self.monitor_combobox.current()
        self.selected_monitor = get_monitors()[monitor_index]
        self.current_scene_name = self.scene_combobox.get()

        if self.current_scene_name not in self.scenes:
            self.log("No scene selected or invalid scene.")
            return

        self.running = True
        self.playback_active = self.playback_var.get()

        # Start projection thread
        threading.Thread(target=self.run_scene, daemon=True).start()

        # Start multi-scene playback if enabled
        if self.playback_active:
            threading.Thread(target=self.multi_scene_playback, daemon=True).start()

    def edit_scene_live(self):
        """Open a live editor for the current scene."""
        self.log("Live scene editing feature is under development.")

    def change_scene(self, event=None):
        """Change the current scene live."""
        new_scene_name = self.scene_combobox.get()
        if new_scene_name != self.current_scene_name:
            self.current_scene_name = new_scene_name
            self.log(f"Switched to scene: {new_scene_name}")

    def multi_scene_playback(self):
        """Cycle through scenes during playback."""
        scene_names = list(self.scenes.keys())
        scene_duration = int(self.playback_entry.get())

        while self.playback_active and self.running:
            for scene_name in scene_names:
                if not (self.playback_active and self.running):
                    break

                self.current_scene_name = scene_name
                self.log(f"Playing scene: {scene_name}")

                # Wait for scene duration
                pygame.time.wait(scene_duration * 1000)

    def run_scene(self):
        """Run the current scene with advanced motion rendering."""
        pygame.init()

        # Set up the full-screen window on the selected monitor
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{self.selected_monitor.x},{self.selected_monitor.y}"
        screen = pygame.display.set_mode((self.selected_monitor.width, self.selected_monitor.height), pygame.NOFRAME)
        pygame.display.set_caption("Stage Laser Projection")
        clock = pygame.time.Clock()

        # Track object states
        object_states = []
        try:
            for obj in self.scenes[self.current_scene_name]["objects"]:
                object_states.append({
                    "obj": obj,
                    "time": random.uniform(0, 10),  # Randomize start time
                    "current_pos": None
                })
        except KeyError:
            self.log("Error: Unable to find current scene.")
            self.running = False
            pygame.quit()
            return

        while self.running:
            screen.fill((0, 0, 0))  # Black background

            for state in object_states:
                obj = state["obj"]
                t = state["time"]
                brightness = self.brightness_slider.get() / 255.0

                try:
                    if obj["motion"] == "circular":
                        # Circular motion calculation
                        center_x, center_y = obj["path_center"]
                        radius = obj["path_radius"]
                        angular_velocity = obj["angular_velocity"]
                        x = center_x + radius * math.cos(t * angular_velocity)
                        y = center_y + radius * math.sin(t * angular_velocity)
                        current_pos = (int(x), int(y))

                    elif obj["motion"] == "path":
                        path = obj["path"]
                        speed = obj.get("speed", 1)

                        # Interpolate along the path
                        total_path_length = len(path) - 1
                        current_segment = int(t * speed) % total_path_length
                        next_segment = (current_segment + 1) % len(path)

                        start_point = path[current_segment]
                        end_point = path[next_segment]

                        # Linear interpolation
                        progress = (t * speed) % 1
                        x = start_point[0] + (end_point[0] - start_point[0]) * progress
                        y = start_point[1] + (end_point[1] - start_point[1]) * progress

                        current_pos = (int(x), int(y))

                    # Apply brightness
                    color = tuple(min(255, int(c * brightness)) for c in obj["color"])

                    # Draw the object
                    pygame.draw.circle(screen, color, current_pos, obj["radius"])

                    # Update time
                    state["time"] += 0.016  # Roughly 60 FPS
                    state["current_pos"] = current_pos

                except Exception as e:
                    self.log(f"Error rendering object: {e}")

            pygame.display.flip()
            clock.tick(60)

            # Handle Pygame events to allow closing
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

        pygame.quit()

    def stop_scene(self):
        """Stop the currently running projection."""
        self.running = False
        self.playback_active = False
        self.log("Projection stopped.")


if __name__ == "__main__":
    root = tk.Tk()
    app = StageLaserProjectionApp(root)
    root.protocol("WM_DELETE_WINDOW", app.stop_scene)  # Stop scene on close
    root.mainloop()