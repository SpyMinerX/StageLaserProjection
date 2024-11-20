import time
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
import socket
from tkinter.colorchooser import askcolor


class ArtNetReceiver(threading.Thread):
    def __init__(self, app):
        super().__init__(daemon=True)
        self.app = app
        self.dmx_channel = 0
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", 6454))  # Default Art-Net port

    def run(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(1024)
                if data[:8] == b"Art-Net\0" and data[8:10] == b"\x00\x50":
                    # Parse ArtDMX packet
                    dmx_data = data[18:]  # DMX data starts at byte 18
                    if len(dmx_data) > 511:
                        brightness = dmx_data[0]
                        speed = dmx_data[1]
                        radius = dmx_data[2]
                        self.app.update_slider(brightness, speed, radius)
            except Exception as e:
                print(f"Art-Net receiver error: {e}")

    def stop(self):
        self.running = False
        self.sock.close()

class StageLaserProjectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stage Laser Projection")

        # Art-Net Receiver
        self.artnet_receiver = ArtNetReceiver(self)
        self.artnet_receiver.start()

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

        # Laser Settings Label
        self.settings_label = tk.Label(root, text="Laser Settings:")
        self.settings_label.pack(pady=5)

        # Brightness Slider with Label
        brightness_frame = tk.Frame(root)
        brightness_frame.pack(pady=5, fill="x")

        brightness_label = tk.Label(brightness_frame, text="Brightness:")
        brightness_label.pack(side="left", padx=5)

        self.brightness_slider = tk.Scale(brightness_frame, from_=0, to=255, orient="horizontal")
        self.brightness_slider.set(255)
        self.brightness_slider.pack(side="left", fill="x", expand=True)

        # Speed Slider with Label
        speed_frame = tk.Frame(root)
        speed_frame.pack(pady=5, fill="x")

        speed_label = tk.Label(speed_frame, text="Speed:")
        speed_label.pack(side="left", padx=5)

        self.speed_slider = tk.Scale(speed_frame, from_=0, to=255, orient="horizontal")
        self.speed_slider.set(128)
        self.speed_slider.pack(side="left", fill="x", expand=True)

        # radius Slider with Label
        radius_frame = tk.Frame(root)
        radius_frame.pack(pady=5, fill="x")

        radius_label = tk.Label(radius_frame, text="Radius:")
        radius_label.pack(side="left", padx=5)

        self.radius_slider = tk.Scale(radius_frame, from_=0, to=255, orient="horizontal")
        self.radius_slider.set(128)
        self.radius_slider.pack(side="left", fill="x", expand=True)

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
        self.running_thread = None
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
        self.running_thread = threading.Thread(target=self.run_scene, daemon=True).start()

        # Start multi-scene playback if enabled
        if self.playback_active:
            self.running_thread = threading.Thread(target=self.multi_scene_playback, daemon=True).start()

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
        scene_duration = int(self.playback_entry.get())  # Duration per scene in seconds

        while self.playback_active and self.running:
            for scene_name in scene_names:
                if not (self.playback_active and self.running):
                    break  # Exit if playback or running stops

                # Update the current scene name
                self.current_scene_name = scene_name
                self.log(f"Playing scene: {scene_name}")

                # Wait for the specified scene duration
                for _ in range(scene_duration * 100):  # Check every 10 ms
                    if not (self.playback_active and self.running):
                        break
                    pygame.time.wait(10)

    def run_scene(self):
        """Run the current scene with advanced motion rendering."""
        pygame.init()

        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{self.selected_monitor.x},{self.selected_monitor.y}"
        screen = pygame.display.set_mode((self.selected_monitor.width, self.selected_monitor.height), pygame.NOFRAME)
        pygame.display.set_caption("Stage Laser Projection")
        clock = pygame.time.Clock()

        object_states = None

        while self.running:
            # Dynamically fetch the current scene
            scene_name = self.current_scene_name
            scene = self.scenes.get(scene_name)

            if not scene:
                self.log(f"Error: Scene '{scene_name}' not found.")
                self.running = False
                break

            # Initialize object states if the scene changes
            if object_states is None or scene_name != getattr(self, "last_scene_name", None):
                object_states = []
                for obj in scene["objects"]:
                    object_states.append({
                        "obj": obj,
                        "time": random.uniform(0, 10),  # Randomize start time
                        "current_pos": None
                    })
                self.last_scene_name = scene_name

            # Clear screen
            screen.fill((0, 0, 0))  # Black background

            # Render objects
            for state in object_states:
                obj = state["obj"]
                t = state["time"]
                brightness = self.brightness_slider.get() / 255.0
                speedMultiplier = (self.speed_slider.get() / 128.0) ** 2
                radiusMultiplier = (self.radius_slider.get() / 128.0) ** 2

                try:
                    if obj["motion"] == "circular":
                        center_x, center_y = obj["path_center"]
                        radius = obj["path_radius"]
                        angular_velocity = obj["angular_velocity"] * speedMultiplier
                        x = center_x + radius * math.cos(t * angular_velocity)
                        y = center_y + radius * math.sin(t * angular_velocity)
                        current_pos = (int(x), int(y))

                    elif obj["motion"] == "path":
                        path = obj["path"]
                        speed = obj.get("speed", 1) * speedMultiplier

                        total_path_length = len(path) - 1
                        current_segment = int(t * speed) % total_path_length
                        next_segment = (current_segment + 1) % len(path)

                        start_point = path[current_segment]
                        end_point = path[next_segment]

                        progress = (t * speed) % 1
                        x = start_point[0] + (end_point[0] - start_point[0]) * progress
                        y = start_point[1] + (end_point[1] - start_point[1]) * progress

                        current_pos = (int(x), int(y))

                    color = tuple(min(255, int(c * brightness)) for c in obj["color"])
                    pygame.draw.circle(screen, color, current_pos, obj["radius"] * radiusMultiplier)
                    state["time"] += 0.016  # Roughly 60 FPS
                    state["current_pos"] = current_pos

                except Exception as e:
                    self.log(f"Error rendering object: {e}")

            pygame.display.flip()
            clock.tick(60)

            # Handle Pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

        pygame.quit()

    def stop_scene(self):
        """Stop the currently running projection."""
        self.running = False
        self.playback_active = False
        self.log("Projection stopped.")

    def quit(self):
        """Stop the projection and close the application."""
        self.stop_scene()  # Wait for threads to stop
        self.root.quit()

    def update_slider(self, brightness, speed, radius):
        """Update the brightness slider from Art-Net data."""
        self.brightness_slider.set(brightness)
        self.speed_slider.set(speed)
        self.radius_slider.set(radius)


import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import json


class LiveSceneEditor:
    def __init__(self, parent, update_callback, current_scene):
        self.parent = parent
        self.update_callback = update_callback
        self.current_scene = current_scene.copy()

        # Create editor window
        self.editor_window = tk.Toplevel(parent)
        self.editor_window.title("Live Scene Editor")
        self.editor_window.geometry("800x600")

        # Scene name
        tk.Label(self.editor_window, text="Scene Name:").pack(pady=5)
        self.scene_name_var = tk.StringVar(value=self.current_scene.get("name", "Unnamed Scene"))
        tk.Entry(self.editor_window, textvariable=self.scene_name_var, width=50).pack(pady=5)

        # Objects Frame
        self.objects_frame = tk.Frame(self.editor_window)
        self.objects_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Objects Listbox
        self.objects_listbox = tk.Listbox(self.objects_frame, width=50)
        self.objects_listbox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.objects_listbox.bind('<<ListboxSelect>>', self.load_object_details)

        # Object Details Frame
        self.details_frame = tk.Frame(self.objects_frame)
        self.details_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=10)

        # Populate objects listbox
        self.populate_objects_listbox()

        # Object Manipulation Buttons
        button_frame = tk.Frame(self.editor_window)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Add Object", command=self.add_object).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Remove Object", command=self.remove_object).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Save Scene", command=self.save_scene).pack(side=tk.LEFT, padx=5)

        # Object Details Widgets
        self.create_object_detail_widgets()

    def populate_objects_listbox(self):
        """Populate the listbox with objects from the current scene."""
        self.objects_listbox.delete(0, tk.END)
        for i, obj in enumerate(self.current_scene.get("objects", [])):
            motion_type = obj.get("motion", "Unknown")
            display_text = f"Object {i + 1}: {motion_type} Motion"
            self.objects_listbox.insert(tk.END, display_text)

    def create_object_detail_widgets(self):
        """Create widgets for editing object details."""
        # Motion Type
        tk.Label(self.details_frame, text="Motion Type:").pack()
        self.motion_var = tk.StringVar()
        self.motion_combobox = ttk.Combobox(self.details_frame,
                                            textvariable=self.motion_var,
                                            values=["circular", "path"],
                                            state="readonly")
        self.motion_combobox.pack()
        self.motion_combobox.bind("<<ComboboxSelected>>", self.update_motion_fields)

        # Path/Center Coordinates
        tk.Label(self.details_frame, text="Path/Center Coordinates:").pack()
        self.coordinates_text = tk.Text(self.details_frame, height=3, width=40)
        self.coordinates_text.pack()

        # Color Selection
        tk.Label(self.details_frame, text="Color:").pack()
        self.color_frame = tk.Frame(self.details_frame)
        self.color_frame.pack()
        self.color_button = tk.Button(self.color_frame, text="Choose Color", command=self.choose_color)
        self.color_button.pack(side=tk.LEFT)
        self.color_display = tk.Label(self.color_frame, text="Current Color", width=20)
        self.color_display.pack(side=tk.LEFT)

        # Radius
        tk.Label(self.details_frame, text="Radius:").pack()
        self.radius_var = tk.IntVar(value=30)
        self.radius_scale = tk.Scale(self.details_frame, from_=5, to=100,
                                     orient=tk.HORIZONTAL)
        self.radius_scale.pack()

        # Motion-Specific Fields
        tk.Label(self.details_frame, text="Motion Parameters:").pack()
        self.motion_params_text = tk.Text(self.details_frame, height=3, width=40)
        self.motion_params_text.pack()

        # Update Button
        tk.Button(self.details_frame, text="Update Object", command=self.update_object).pack(pady=10)

    def load_object_details(self, event=None):
        """Load details of the selected object."""
        try:
            selected_index = self.objects_listbox.curselection()[0]
            obj = self.current_scene["objects"][selected_index]

            # Set motion type
            self.motion_var.set(obj.get("motion", ""))

            # Set coordinates
            if obj.get("motion") == "circular":
                coords = obj.get("path_center", [0, 0])
                self.coordinates_text.delete(1.0, tk.END)
                self.coordinates_text.insert(tk.END, f"{coords[0]}, {coords[1]}")

                # Set angular velocity
                self.motion_params_text.delete(1.0, tk.END)
                self.motion_params_text.insert(tk.END,
                                               f"Angular Velocity: {obj.get('angular_velocity', 1)}\n"
                                               f"Path Radius: {obj.get('path_radius', 100)}")

            elif obj.get("motion") == "path":
                path = obj.get("path", [])
                self.coordinates_text.delete(1.0, tk.END)
                self.coordinates_text.insert(tk.END,
                                             "\n".join([f"{p[0]}, {p[1]}" for p in path]))

                # Set path-specific parameters
                self.motion_params_text.delete(1.0, tk.END)
                self.motion_params_text.insert(tk.END,
                                               f"Animation: {obj.get('animation', 'loop')}\n"
                                               f"Speed: {obj.get('speed', 1)}")

            # Set color
            color = obj.get("color", [255, 0, 0])
            self.color_display.config(bg=f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}')

            # Set radius
            self.radius_scale.set(obj.get("radius", 30))

        except (IndexError, KeyError):
            messagebox.showwarning("Selection Error", "Please select an object to edit.")

    def choose_color(self):
        """Open color chooser dialog."""
        color = colorchooser.askcolor(title="Choose object color")
        if color[0]:  # If a color was chosen
            # Convert to RGB
            rgb = [int(x) for x in color[0]]
            self.color_display.config(bg=color[1])
            return rgb
        return None

    def update_motion_fields(self, event=None):
        """Update fields based on selected motion type."""
        motion_type = self.motion_var.get()

        # Clear previous entries
        self.coordinates_text.delete(1.0, tk.END)
        self.motion_params_text.delete(1.0, tk.END)

        if motion_type == "circular":
            # Default circular motion parameters
            self.coordinates_text.insert(tk.END, "400, 300")
            self.motion_params_text.insert(tk.END,
                                           "Angular Velocity: 1\n"
                                           "Path Radius: 150")

        elif motion_type == "path":
            # Default path motion parameters
            self.coordinates_text.insert(tk.END,
                                         "100, 100\n"
                                         "700, 100\n"
                                         "700, 700\n"
                                         "100, 700")
            self.motion_params_text.insert(tk.END,
                                           "Animation: loop\n"
                                           "Speed: 2")

    def add_object(self):
        """Add a new object to the scene."""
        new_object = {
            "motion": "circular",
            "path_center": [400, 300],
            "path_radius": 150,
            "angular_velocity": 1,
            "color": [255, 0, 0],
            "radius": 30
        }

        # Add to current scene
        if "objects" not in self.current_scene:
            self.current_scene["objects"] = []
        self.current_scene["objects"].append(new_object)

        # Refresh listbox
        self.populate_objects_listbox()

        # Select the new object
        self.objects_listbox.selection_clear(0, tk.END)
        self.objects_listbox.selection_set(tk.END)
        self.objects_listbox.event_generate('<<ListboxSelect>>')

    def remove_object(self):
        """Remove the selected object from the scene."""
        try:
            selected_index = self.objects_listbox.curselection()[0]
            del self.current_scene["objects"][selected_index]
            self.populate_objects_listbox()
        except IndexError:
            messagebox.showwarning("Selection Error", "Please select an object to remove.")

    def update_object(self):
        """Update the selected object with current details."""
        try:
            selected_index = self.objects_listbox.curselection()[0]
            obj = self.current_scene["objects"][selected_index]

            # Update motion type
            obj["motion"] = self.motion_var.get()

            # Parse coordinates
            coords_text = self.coordinates_text.get(1.0, tk.END).strip()

            if obj["motion"] == "circular":
                # Parse center coordinates
                center_coords = [int(x.strip()) for x in coords_text.split(',')]
                obj["path_center"] = center_coords

                # Parse motion parameters
                params = self.motion_params_text.get(1.0, tk.END).strip().split('\n')
                param_dict = dict(param.split(': ') for param in params)

                obj["angular_velocity"] = float(param_dict.get('Angular Velocity', 1))
                obj["path_radius"] = int(param_dict.get('Path Radius', 150))

            elif obj["motion"] == "path":
                # Parse path coordinates
                path_coords = [
                    [int(x.strip()) for x in coord.split(',')]
                    for coord in coords_text.split('\n')
                ]
                obj["path"] = path_coords

                # Parse motion parameters
                params = self.motion_params_text.get(1.0, tk.END).strip().split('\n')
                param_dict = dict(param.split(': ') for param in params)

                obj["animation"] = param_dict.get('Animation', 'loop')
                obj["speed"] = float(param_dict.get('Speed', 2))

            # Update color
            current_color = self.color_display.cget('bg')
            # Convert hex to RGB
            obj["color"] = [
                int(current_color[1:3], 16),
                int(current_color[3:5], 16),
                int(current_color[5:7], 16)
            ]

            # Update radius
            obj["radius"] = self.radius_scale.get()

            # Refresh display
            self.populate_objects_listbox()

            messagebox.showinfo("Success", "Object updated successfully!")

        except Exception as e:
            messagebox.showerror("Update Error", f"Failed to update object: {str(e)}")

    def save_scene(self):
        """Save the modified scene."""
        # Update scene name
        self.current_scene["name"] = self.scene_name_var.get()

        # Call the update callback with the modified scene
        self.update_callback(self.current_scene)

        # Close the editor
        self.editor_window.destroy()


# Modify the main application class to integrate the live scene editor
def add_live_scene_editing_method(cls):
    def edit_scene_live(self):
        """Open a live editor for the current scene."""
        if not self.current_scene_name:
            self.log("No scene selected for editing.")
            return

        # Get the current scene
        current_scene = self.scenes.get(self.current_scene_name)

        if not current_scene:
            self.log("Unable to find current scene.")
            return

        # Create the live scene editor
        LiveSceneEditor(self.root,
                        update_callback=self.update_current_scene,
                        current_scene=current_scene)

    def update_current_scene(self, updated_scene):
        """Update the current scene in the scenes dictionary."""
        # Update the scene in the main scenes dictionary
        self.scenes[updated_scene["name"]] = updated_scene

        # Update the scene combobox if the name changed
        scene_names = list(self.scenes.keys())
        self.scene_combobox['values'] = scene_names

        # Select the updated scene
        current_index = scene_names.index(updated_scene["name"])
        self.scene_combobox.current(current_index)
        self.current_scene_name = updated_scene["name"]

        self.log(f"Scene '{updated_scene['name']}' updated successfully.")

    # Add the methods to the class
    cls.edit_scene_live = edit_scene_live
    cls.update_current_scene = update_current_scene

    return cls



StageLaserProjectionApp = add_live_scene_editing_method(StageLaserProjectionApp)
if __name__ == "__main__":
    root = tk.Tk()
    app = StageLaserProjectionApp(root)
    root.protocol("WM_DELETE_WINDOW", app.quit())  # Stop scene on close
    root.mainloop()

