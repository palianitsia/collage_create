import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import os

class CollageCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Collage Creator")
        self.image_paths = []

        # Set up GUI
        self.setup_gui()

    def setup_gui(self):
        # Button to upload images
        self.upload_button = tk.Button(self.root, text="Aggiungi Immagini", command=self.upload_images)
        self.upload_button.pack(pady=10)

        # Collage type options
        self.collage_type_label = tk.Label(self.root, text="Seleziona tipo di collage:")
        self.collage_type_label.pack(pady=5)

        self.collage_type_var = tk.StringVar(value="grid")
        self.grid_option = tk.Radiobutton(self.root, text="Griglia", variable=self.collage_type_var, value="grid")
        self.grid_option.pack()

        self.horizontal_option = tk.Radiobutton(self.root, text="Orizzontale", variable=self.collage_type_var, value="horizontal")
        self.horizontal_option.pack()

        self.vertical_option = tk.Radiobutton(self.root, text="Verticale", variable=self.collage_type_var, value="vertical")
        self.vertical_option.pack()

        # Entry fields for output dimensions
        self.dimension_label = tk.Label(self.root, text="Dimensioni del collage finale (in pixel):")
        self.dimension_label.pack(pady=5)

        self.width_label = tk.Label(self.root, text="Larghezza:")
        self.width_label.pack()
        self.width_entry = tk.Entry(self.root)
        self.width_entry.pack()

        self.height_label = tk.Label(self.root, text="Altezza:")
        self.height_label.pack()
        self.height_entry = tk.Entry(self.root)
        self.height_entry.pack()

        # Button to create collage
        self.create_button = tk.Button(self.root, text="Crea Collage", command=self.create_collage)
        self.create_button.pack(pady=10)

    def upload_images(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if file_paths:
            self.image_paths.extend(file_paths)
            messagebox.showinfo("Successo", f"{len(file_paths)} immagini aggiunte!")

    def create_collage(self):
        if not self.image_paths:
            messagebox.showwarning("Errore", "Devi aggiungere almeno un'immagine!")
            return

        try:
            # Open images and store them in a list
            images = [Image.open(path) for path in self.image_paths]

            # Retrieve output dimensions
            output_width = int(self.width_entry.get()) if self.width_entry.get() else None
            output_height = int(self.height_entry.get()) if self.height_entry.get() else None

            if output_width is None or output_height is None:
                messagebox.showwarning("Errore", "Devi specificare entrambe le dimensioni (larghezza e altezza)!")
                return

            # Determine collage type
            collage_type = self.collage_type_var.get()

            if collage_type == "grid":
                self.create_grid_collage(images, output_width, output_height)
            elif collage_type == "horizontal":
                self.create_horizontal_collage(images, output_width, output_height)
            else:
                self.create_vertical_collage(images, output_width, output_height)
        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def create_grid_collage(self, images, output_width, output_height):
        num_images = len(images)
        grid_size = int(num_images**0.5) + 1

        image_width, image_height = images[0].size
        collage_width = image_width * grid_size
        collage_height = image_height * grid_size

        # Create the collage with the original dimensions
        collage = Image.new('RGB', (collage_width, collage_height))

        for i, img in enumerate(images):
            x = (i % grid_size) * image_width
            y = (i // grid_size) * image_height
            collage.paste(img, (x, y))

        # Resize the collage to the desired output size using LANCZOS (anti-aliasing)
        collage = collage.resize((output_width, output_height), Image.LANCZOS)

        self.save_collage(collage)

    def create_horizontal_collage(self, images, output_width, output_height):
        total_width = sum(img.size[0] for img in images)
        max_height = max(img.size[1] for img in images)

        collage = Image.new('RGB', (total_width, max_height))

        x_offset = 0
        for img in images:
            collage.paste(img, (x_offset, 0))
            x_offset += img.size[0]

        # Resize the collage to the desired output size using LANCZOS (anti-aliasing)
        collage = collage.resize((output_width, output_height), Image.LANCZOS)
        self.save_collage(collage)

    def create_vertical_collage(self, images, output_width, output_height):
        total_height = sum(img.size[1] for img in images)
        max_width = max(img.size[0] for img in images)

        collage = Image.new('RGB', (max_width, total_height))

        y_offset = 0
        for img in images:
            collage.paste(img, (0, y_offset))
            y_offset += img.size[1]

        # Resize the collage to the desired output size using LANCZOS (anti-aliasing)
        collage = collage.resize((output_width, output_height), Image.LANCZOS)
        self.save_collage(collage)

    def save_collage(self, collage):
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")])
        if save_path:
            collage.save(save_path)
            messagebox.showinfo("Successo", f"Collage salvato in {save_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CollageCreatorApp(root)
    root.mainloop()
