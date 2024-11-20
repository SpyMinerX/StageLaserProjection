# **Stage Laser Projection Application**

The **Stage Laser Projection Application** allows you to create, edit, and play stunning stage laser effects with DMX control integration. The application supports `.spyLAZ` files (Base64 encoded) and dynamic real-time control via DMX using Art-Net.

---

## **Applications**

### **1. StageLazerProjection**
- The main application for running and controlling laser projection scenes.
- Loads `.spyLAZ` files from a folder and allows dynamic selection during runtime.

### **2. StageLazerEditor**
- A file creator tool for designing custom `.spyLAZ` scene files.
- Encodes scenes into Base64 format for secure and efficient storage.

---

## **DMX Address Map**

| **DMX Channel** | **Parameter**           | **Description**                                                                 | **Default Value** |
|------------------|------------------------|---------------------------------------------------------------------------------|-------------------|
| **1 (0)**        | **Brightness**         | Controls the overall brightness of the laser projection.                        | N/A               |
| **2 (1)**        | **Speed**              | Adjusts the speed of object motion, affecting both circular and path movements. | **128**           |
| **3 (2)**        | **Radius**             | Modifies the size of circular motions or path radii for dynamic effects.        | **128**           |
| **4 (3)**        | **X-Shift**            | Shifts the entire projection horizontally along the X-axis.                     | **128**           |
| **5 (4)**        | **Y-Shift**            | Shifts the entire projection vertically along the Y-axis.                       | **128**           |
| **6 (5)**        | **Scale**              | Scales the size of all objects in the projection relative to the screen center. | **128**           |

---

## **Working with .spyLAZ Files**

The `.spyLAZ` file format is Base64-encoded and stores scene configurations for the laser projector. These files must be placed in a folder, as the application loads scenes from a folder rather than individual files.

### **Creating .spyLAZ Files**

Use the built-in **StageLazerEditor** to design and save `.spyLAZ` files.

1. **Launch StageLazerEditor**:
   - Double-click `StageLazerEditor.exe` to open the editor.

2. **Design Your Scene**:
   - Add objects with specific motion types and parameters:
     - **Circular Motion**: Define the center, radius, angular velocity, and color.
     - **Path Motion**: Provide a list of points for objects to follow, along with speed and color.

3. **Save the Scene**:
   - When saving, the scene is automatically encoded into Base64 format and stored as a `.spyLAZ` file.
   - Save multiple `.spyLAZ` files in the same folder to use them in the application.

---

### **Loading Scenes into StageLazerProjection**

The **StageLazerProjection** application loads `.spyLAZ` files from a folder. You cannot load a single file directly.

1. **Prepare a Folder**:
   - Create a folder (e.g., `Scenes`) and place multiple `.spyLAZ` files in it.

2. **Launch StageLazerProjection**:
   - Double-click `StageLazerProjection.exe` to start the application.

3. **Load the Folder**:
   - Use the "Load Folder" button in the application GUI to select a folder containing `.spyLAZ` files.

4. **Choose a Scene**:
   - Once the folder is loaded, you can select scenes from the list displayed in the application.

---

### **Structure of a Base64-Encoded .spyLAZ File**

Internally, `.spyLAZ` files contain a JSON-like structure encoded in Base64. Here’s an example of the decoded content:

```json
{
  "scene_name": "Example Scene",
  "objects": [
    {
      "motion": "circular",
      "path_center": [0, 0],
      "path_radius": 150,
      "angular_velocity": 0.5,
      "color": [255, 0, 0],
      "radius": 10
    },
    {
      "motion": "path",
      "path": [[-100, -100], [100, -100], [100, 100], [-100, 100]],
      "speed": 1,
      "color": [0, 255, 0],
      "radius": 5
    }
  ]
}
```

---

## **Example Workflow**

### **Step 1: Create Multiple Scenes**
1. Open `StageLazerEditor.exe`.
2. Create several scenes, such as:
   - `circular_motion.spyLAZ`: A red circular motion effect.
   - `path_motion.spyLAZ`: A green object following a rectangular path.
3. Save all `.spyLAZ` files in a folder named `Scenes`.

---

### **Step 2: Run and Load Scenes**
1. Open `StageLazerProjection.exe`.
2. Select the `Scenes` folder using the "Load Folder" button in the GUI.
3. Choose a scene from the loaded list to start the projection.

---

### **Step 3: Control in Real Time**
- Adjust brightness, speed, and other parameters via your DMX controller.

---

## **Tips and Best Practices**
- **Organize Scenes**: Store related `.spyLAZ` files in a single folder for easy loading.
- **Save Frequently**: Use `StageLazerEditor` to create multiple scenes for performances.
- **Combine with DMX**: Use a DMX controller to adjust projection settings dynamically.
- **Base64 Validation**: If needed, decode `.spyLAZ` files for verification or modification, and re-encode them to maintain compatibility.

---

This Project is Owned and Maintained by [Spyminer(Miaya Engelbrecht)](https://spyminer.dev) and [S. Meyer](https://simeonmeyer.de)
