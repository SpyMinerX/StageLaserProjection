import tkinter as tk
from tkinter import ttk
import pygame
import threading
from screeninfo import get_monitors
import os
import json
import glob
import math


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

        # Scene selection
        self.scene_label = tk.Label(root, text="Select Scene for Laser Animation:")
        self.scene_label.pack(pady=5)

        self.scene_combobox = ttk.Combobox(root, state="readonly")
        self.scene_combobox.pack(pady=5)

        # Brightness slider
        self.brightness_label = tk.Label(root, text="Laser Brightness:")
        self.brightness_label.pack(pady=5)

        self.brightness_slider = tk.Scale(root, from_=0, to=255, orient="horizontal")
        self.brightness_slider.set(255)
        self.brightness_slider.pack(pady=5)

        # Start button
        self.start_button = tk.Button(root, text="Start Projection", command=self.start_scene)
        self.start_button.pack(pady=10)

        self.running = False
        self.selected_monitor = None

        # Scene data
        self.scenes = {}
        self.load_scenes()

    def load_scenes(self):
        """Load scenes from JSON files in the 'scenes' directory."""
        scene_files = glob.glob("scenes/*.json")
        for file in scene_files:
            with open(file, "r") as f:
                scene_data = json.load(f)
                self.scenes[scene_data["name"]] = scene_data
        self.scene_combobox["values"] = list(self.scenes.keys())
        if self.scenes:
            self.scene_combobox.current(0)

    def start_scene(self):
        if self.running:
            return

        monitor_index = self.monitor_combobox.current()
        self.selected_monitor = get_monitors()[monitor_index]
        scene_name = self.scene_combobox.get()

        if scene_name not in self.scenes:
            return

        self.running = True
        threading.Thread(target=self.run_scene, args=(self.scenes[scene_name],), daemon=True).start()

    def run_scene(self, scene):
        pygame.init()

        # Set up the full-screen window on the selected monitor
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{self.selected_monitor.x},{self.selected_monitor.y}"
        screen = pygame.display.set_mode((self.selected_monitor.width, self.selected_monitor.height), pygame.NOFRAME)
        pygame.display.set_caption("Stage Laser Projection")
        clock = pygame.time.Clock()

        # Objects in the scene
        objects = scene.get("objects", [])

        # Initialize angular positions for circular paths
        for obj in objects:
            if obj.get("motion") == "circular":
                obj["angle"] = 0

        while self.running:
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
                    # Update angle for circular motion
                    obj["angle"] += obj["angular_velocity"]
                    angle_rad = math.radians(obj["angle"])
                    center_x, center_y = obj["path_center"]
                    obj["x"] = center_x + obj["path_radius"] * math.cos(angle_rad)
                    obj["y"] = center_y + obj["path_radius"] * math.sin(angle_rad)
                else:  # Linear motion
                    obj["x"] += obj["vx"]
                    obj["y"] += obj["vy"]

                    # Bounce off edges
                    if obj["x"] - obj["radius"] < 0 or obj["x"] + obj["radius"] > self.selected_monitor.width:
                        obj["vx"] = -obj["vx"]
                    if obj["y"] - obj["radius"] < 0 or obj["y"] + obj["radius"] > self.selected_monitor.height:
                        obj["vy"] = -obj["vy"]

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
        self.running = False


if __name__ == "__main__":
    root = tk.Tk()
    app = StageLaserProjectionApp(root)

    root.protocol("WM_DELETE_WINDOW", app.stop_scene)  # Stop scene on close
    root.mainloop()
