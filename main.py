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


class StageLaserProjectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stage Laser Projection")

        # Monitor selection
        self.monitor_label = tk.Label(root, text="Select Monitor for Projection:")
        self.monitor_label.pack(pady=5)

        self.monitor_combobox = ttk.Combobox(root, state="readonly")
        self.monitor_combobox.pack(pady=5)
        self.monitor_combobox['values'] = [f"Monitor {i+1}: {m.width}x{m.height}" for i, m in enumerate(get_monitors())]
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

        # Start and Stop buttons
        self.start_button = tk.Button(root, text="Start Projection", command=self.start_scene)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(root, text="Stop Projection", command=self.stop_scene)
        self.stop_button.pack(pady=5)

        self.running = False
        self.current_scene_name = None
        self.selected_monitor = None

        # Scene data
        self.scenes = {}

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
            print("No folder selected.")
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
                        print(f"Invalid scene format in file: {file_path}")

            # Update scene combobox
            self.scene_combobox["values"] = list(self.scenes.keys())
            if self.scenes:
                self.scene_combobox.current(0)
                self.current_scene_name = self.scene_combobox.get()
        except Exception as e:
            print(f"Error loading scenes from folder: {e}")

    def start_scene(self):
        if self.running:
            return

        monitor_index = self.monitor_combobox.current()
        self.selected_monitor = get_monitors()[monitor_index]
        self.current_scene_name = self.scene_combobox.get()

        if self.current_scene_name not in self.scenes:
            return

        self.running = True
        threading.Thread(target=self.run_scene, daemon=True).start()

    def change_scene(self, event=None):
        """Change the current scene live."""
        new_scene_name = self.scene_combobox.get()
        if new_scene_name != self.current_scene_name:
            self.current_scene_name = new_scene_name

    def run_scene(self):
        pygame.init()

        # Set up the full-screen window on the selected monitor
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{self.selected_monitor.x},{self.selected_monitor.y}"
        screen = pygame.display.set_mode((self.selected_monitor.width, self.selected_monitor.height), pygame.NOFRAME)
        pygame.display.set_caption("Stage Laser Projection")
        clock = pygame.time.Clock()

        while self.running:
            # Reload the current scene if it has changed
            scene = self.scenes.get(self.current_scene_name, {})
            objects = scene.get("objects", [])

            # Initialize motion attributes
            for obj in objects:
                if obj.get("motion") == "path" and "current_checkpoint" not in obj:
                    obj["current_checkpoint"] = 0
                    obj["reverse"] = False
                elif obj.get("motion") == "circular" and "angle" not in obj:
                    obj["angle"] = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # Clear screen
            screen.fill((0, 0, 0))

            # Adjust brightness
            brightness = self.brightness_slider.get()

            # Update and draw objects
            for obj in objects:
                if obj.get("motion") == "circular":
                    # Update position for circular motion
                    angle_rad = math.radians(obj["angle"])
                    center_x, center_y = obj["path_center"]
                    obj["x"] = center_x + obj["path_radius"] * math.cos(angle_rad)
                    obj["y"] = center_y + obj["path_radius"] * math.sin(angle_rad)
                    obj["angle"] += obj["angular_velocity"]

                elif obj.get("motion") == "path":
                    # Move along the defined path
                    path = obj["path"]
                    speed = obj.get("speed", 1)
                    current_checkpoint = obj["current_checkpoint"]
                    reverse = obj["reverse"]

                    if reverse:
                        next_checkpoint = path[current_checkpoint - 1]
                    else:
                        next_checkpoint = path[current_checkpoint]

                    dx = next_checkpoint[0] - obj.get("x", path[0][0])
                    dy = next_checkpoint[1] - obj.get("y", path[0][1])
                    distance = math.sqrt(dx**2 + dy**2)

                    if distance > speed:
                        obj["x"] = obj.get("x", path[0][0]) + speed * dx / distance
                        obj["y"] = obj.get("y", path[0][1]) + speed * dy / distance
                    else:
                        obj["x"], obj["y"] = next_checkpoint

                        if reverse:
                            obj["current_checkpoint"] -= 1
                            if obj["current_checkpoint"] <= 0:
                                obj["reverse"] = False
                        else:
                            obj["current_checkpoint"] += 1
                            if obj["current_checkpoint"] >= len(path):
                                animation = obj.get("animation", "none")
                                if animation == "bounce":
                                    obj["reverse"] = True
                                    obj["current_checkpoint"] -= 1
                                elif animation == "loop":
                                    obj["current_checkpoint"] = 0
                                else:
                                    obj["motion"] = None  # Stop motion

                # Adjust color brightness
                base_color = obj["color"]
                adjusted_color = (
                    int(base_color[0] * (brightness / 255)),
                    int(base_color[1] * (brightness / 255)),
                    int(base_color[2] * (brightness / 255)),
                )

                # Draw the object
                pygame.draw.circle(screen, adjusted_color, (int(obj["x"]), int(obj["y"])), obj["radius"])

            # Update the display
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def stop_scene(self):
        """Stop the currently running projection."""
        self.running = False


if __name__ == "__main__":
    root = tk.Tk()
    app = StageLaserProjectionApp(root)

    root.protocol("WM_DELETE_WINDOW", app.stop_scene)  # Stop scene on close
    root.mainloop()
