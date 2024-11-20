import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import base64


class PathJsonCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Path JSON Creator")
        self.objects = []

        # File handling
        self.load_button = tk.Button(root, text="Load spyLAZ", command=self.load_file)
        self.load_button.grid(row=0, column=0, padx=10, pady=10)

        self.save_button = tk.Button(root, text="Save spyLAZ", command=self.save_file)
        self.save_button.grid(row=0, column=1, padx=10, pady=10)

        # Object properties
        self.add_object_label = tk.Label(root, text="Add/Edit Object")
        self.add_object_label.grid(row=1, column=0, padx=10, pady=5, columnspan=2)

        self.name_label = tk.Label(root, text="Scene Name:")
        self.name_label.grid(row=2, column=0, padx=10, pady=5)
        self.name_entry = tk.Entry(root)
        self.name_entry.grid(row=2, column=1, padx=10, pady=5)

        self.color_label = tk.Label(root, text="Color (R,G,B):")
        self.color_label.grid(row=3, column=0, padx=10, pady=5)
        self.color_entry = tk.Entry(root)
        self.color_entry.grid(row=3, column=1, padx=10, pady=5)

        self.radius_label = tk.Label(root, text="Radius:")
        self.radius_label.grid(row=4, column=0, padx=10, pady=5)
        self.radius_entry = tk.Entry(root)
        self.radius_entry.grid(row=4, column=1, padx=10, pady=5)

        self.motion_label = tk.Label(root, text="Motion Type:")
        self.motion_label.grid(row=5, column=0, padx=10, pady=5)
        self.motion_combobox = ttk.Combobox(root, values=["path", "circular"], state="readonly")
        self.motion_combobox.grid(row=5, column=1, padx=10, pady=5)
        self.motion_combobox.current(0)

        # Path properties
        self.path_label = tk.Label(root, text="Path (x,y pairs):")
        self.path_label.grid(row=6, column=0, padx=10, pady=5)
        self.path_text = tk.Text(root, height=5, width=30)
        self.path_text.grid(row=6, column=1, padx=10, pady=5)

        # Circular motion properties
        self.circular_label = tk.Label(root, text="Circular Motion")
        self.circular_label.grid(row=7, column=0, padx=10, pady=5, columnspan=2)

        self.center_label = tk.Label(root, text="Center (x,y):")
        self.center_label.grid(row=8, column=0, padx=10, pady=5)
        self.center_entry = tk.Entry(root)
        self.center_entry.grid(row=8, column=1, padx=10, pady=5)

        self.path_radius_label = tk.Label(root, text="Path Radius:")
        self.path_radius_label.grid(row=9, column=0, padx=10, pady=5)
        self.path_radius_entry = tk.Entry(root)
        self.path_radius_entry.grid(row=9, column=1, padx=10, pady=5)

        self.angular_label = tk.Label(root, text="Angular Velocity:")
        self.angular_label.grid(row=10, column=0, padx=10, pady=5)
        self.angular_entry = tk.Entry(root)
        self.angular_entry.grid(row=10, column=1, padx=10, pady=5)

        # Animation type
        self.animation_label = tk.Label(root, text="Animation Type:")
        self.animation_label.grid(row=11, column=0, padx=10, pady=5)
        self.animation_combobox = ttk.Combobox(root, values=["none", "loop", "bounce"], state="readonly")
        self.animation_combobox.grid(row=11, column=1, padx=10, pady=5)
        self.animation_combobox.current(0)

        # Object management
        self.add_object_button = tk.Button(root, text="Add Object", command=self.add_object)
        self.add_object_button.grid(row=12, column=0, pady=10)

        self.edit_object_button = tk.Button(root, text="Edit Selected", command=self.edit_object)
        self.edit_object_button.grid(row=12, column=1, pady=10)

        # Display list of added objects
        self.object_list_label = tk.Label(root, text="Added Objects:")
        self.object_list_label.grid(row=13, column=0, columnspan=2)
        self.object_listbox = tk.Listbox(root, width=50, height=10)
        self.object_listbox.grid(row=14, column=0, columnspan=2, padx=10, pady=5)

    def add_object(self):
        """Add an object to the scene."""
        try:
            color = tuple(map(int, self.color_entry.get().split(",")))
            radius = int(self.radius_entry.get())
            motion = self.motion_combobox.get()
            animation = self.animation_combobox.get()

            obj = {"color": color, "radius": radius, "motion": motion}

            if motion == "path":
                path = [
                    list(map(int, point.split(",")))
                    for point in self.path_text.get("1.0", "end").strip().split("\n")
                ]
                obj["path"] = path
                obj["animation"] = animation

            elif motion == "circular":
                center = tuple(map(int, self.center_entry.get().split(",")))
                path_radius = int(self.path_radius_entry.get())
                angular_velocity = float(self.angular_entry.get())
                obj["path_center"] = center
                obj["path_radius"] = path_radius
                obj["angular_velocity"] = angular_velocity

            self.objects.append(obj)
            self.object_listbox.insert(tk.END, f"Object: {obj}")
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add object: {e}")

    def edit_object(self):
        """Edit the selected object."""
        try:
            selected_index = self.object_listbox.curselection()[0]
            obj = self.objects[selected_index]

            # Load object data into the form for editing
            self.color_entry.delete(0, tk.END)
            self.color_entry.insert(0, ",".join(map(str, obj["color"])))

            self.radius_entry.delete(0, tk.END)
            self.radius_entry.insert(0, str(obj["radius"]))

            self.motion_combobox.set(obj["motion"])
            if obj["motion"] == "path":
                self.path_text.delete("1.0", tk.END)
                self.path_text.insert(
                    "1.0", "\n".join(",".join(map(str, point)) for point in obj["path"])
                )
                self.animation_combobox.set(obj["animation"])
            elif obj["motion"] == "circular":
                self.center_entry.delete(0, tk.END)
                self.center_entry.insert(0, ",".join(map(str, obj["path_center"])))

                self.path_radius_entry.delete(0, tk.END)
                self.path_radius_entry.insert(0, str(obj["path_radius"]))

                self.angular_entry.delete(0, tk.END)
                self.angular_entry.insert(0, str(obj["angular_velocity"]))

            # Remove the object for re-adding
            self.objects.pop(selected_index)
            self.object_listbox.delete(selected_index)
        except IndexError:
            messagebox.showerror("Error", "No object selected for editing.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to edit object: {e}")

    def load_file(self):
        """Load an existing .spyLAZ file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("spyLAZ files", "*.spyLAZ"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "rb") as file:
                    encoded_data = file.read()
                    decoded_data = base64.b64decode(encoded_data).decode("utf-8")
                    data = json.loads(decoded_data)
                    self.objects = data.get("objects", [])
                    self.name_entry.delete(0, tk.END)
                    self.name_entry.insert(0, data.get("name", ""))
                    self.object_listbox.delete(0, tk.END)
                    for obj in self.objects:
                        self.object_listbox.insert(tk.END, f"Object: {obj}")
                    messagebox.showinfo("Success", "spyLAZ file loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load spyLAZ file: {e}")

    def save_file(self):
        """Save the scene as a .spyLAZ file."""
        if not self.objects:
            messagebox.showwarning("Warning", "No objects to save!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".spyLAZ",
            filetypes=[("spyLAZ files", "*.spyLAZ"), ("All files", "*.*")],
        )
        if file_path:
            try:
                scene = {
                    "name": self.name_entry.get(),
                    "objects": self.objects
                }
                json_data = json.dumps(scene, indent=4)
                encoded_data = base64.b64encode(json_data.encode("utf-8"))
                with open(file_path, "wb") as file:
                    file.write(encoded_data)
                messagebox.showinfo("Success", f"Scene saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save spyLAZ file: {e}")

    def clear_form(self):
        """Clear all form fields."""
        self.color_entry.delete(0, tk.END)
        self.radius_entry.delete(0, tk.END)
        self.path_text.delete("1.0", tk.END)
        self.center_entry.delete(0, tk.END)
        self.path_radius_entry.delete(0, tk.END)
        self.angular_entry.delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = PathJsonCreator(root)
    root.mainloop()
