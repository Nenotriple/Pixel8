"""
########################################
#                                      #
#                Pixel8                #
#                                      #
#   Version : v1.00                    #
#   Author  : github.com/Nenotriple    #
#                                      #
########################################

Description:
-------------
Pixelate an image using various methods and conditions.

Key features:
1) Drag-and-Drop images into the Widgets to quickly set their path.
2) Downscale the image. (And optionally upscale the image back to its original size.)
3) Reduce the amount of color in the image.
4) Generate a color palette using these methods: kmeans, mediancut, octree, and random.
5) Use a custom color palette using any other image or from a list of predefined palettes.
6) Save the color palette independent of the output image.
7) Easily adjust the number of colors and the downscale factor.

"""


#endregion
################################################################################################################################################
#region - Imports


import os
import re
import ctypes
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from sklearn.cluster import KMeans
from PIL import Image

from TkToolTip import TkToolTip

#endregion
################################################################################################################################################
#region - CLASS: Pixel8


class Pixel8:
    def __init__(self, root):
        self.root = root
        self.set_appid()
        self.set_icon()
        self.setup_window()


        self.create_widgets()
        self.setup_dnd()
        #root.bind("<Configure>", lambda event: print(f"\rWindow size (W,H): {event.width},{event.height}    ", end='') if event.widget == root else None, add="+")


#endregion
################################################################################################################################################
#region - GUI


    def create_widgets(self):
        # Configure columns to expand
        self.root.columnconfigure(1, weight=1)

        # Input image path
        tk.Label(self.root, text="Input:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        self.image_path_entry = tk.Entry(self.root)
        self.image_path_entry.grid(row=0, column=1, padx=10, pady=5, sticky=tk.EW, columnspan=2)
        TkToolTip.create(self.image_path_entry, "(Drop image here)\nThe input image path", delay=400, padx=5, pady=10)
        input_button_frame = tk.Frame(self.root)
        input_button_frame.grid(row=0, column=3, padx=10, pady=5, sticky=tk.W)
        tk.Button(input_button_frame, text="Browse...", width=13, overrelief="groove", command=self.select_input_path).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(input_button_frame, text="X", width=1, overrelief="groove", command=lambda: [self.image_path_entry.delete(0, tk.END), self.display_colormap_palette()]).pack(side=tk.LEFT)

        # Output image path
        tk.Label(self.root, text="Output:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.output_path_entry = tk.Entry(self.root)
        self.output_path_entry.grid(row=1, column=1, padx=10, pady=5, sticky=tk.EW, columnspan=2)
        TkToolTip.create(self.output_path_entry, "(Drop image here)\nThe filename and path the image will be saved to", delay=400, padx=5, pady=10)
        output_button_frame = tk.Frame(self.root)
        output_button_frame.grid(row=1, column=3, padx=10, pady=5, sticky=tk.W)
        tk.Button(output_button_frame, text="Save As...", width=13, overrelief="groove", command=self.select_output_path).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(output_button_frame, text="X", width=1, overrelief="groove", command=lambda: [self.output_path_entry.delete(0, tk.END)]).pack(side=tk.LEFT)

        # Colormap path
        tk.Label(self.root, text="Color Palette (optional):").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        self.colormap_path_entry = tk.Entry(self.root)
        self.colormap_path_entry.grid(row=2, column=1, padx=10, pady=5, sticky=tk.EW, columnspan=2)
        self.colormap_path_entry.bind("<KeyRelease>", self.display_colormap_palette)
        colormap_button_frame = tk.Frame(self.root)
        colormap_button_frame.grid(row=2, column=3, padx=10, pady=5, sticky=tk.W)
        tk.Button(colormap_button_frame, text="Browse...", width=13, overrelief="groove", command=self.select_colormap_path).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(colormap_button_frame, text="X", width=1, overrelief="groove", command=lambda: [self.colormap_path_entry.delete(0, tk.END), self.display_colormap_palette()]).pack(side=tk.LEFT)
        TkToolTip.create(self.colormap_path_entry, "(Drop image here)\nUse any other image as a colormap for the output image\n\nIf no path is provided, the input image will be used as the colormap", delay=400, padx=5, pady=10)

        # Quantization mode combobox
        tk.Label(self.root, text="Color Mode:").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        self.quant_mode_var = tk.StringVar()
        color_palette_frame = tk.Frame(self.root)
        color_palette_frame.grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)
        self.quant_mode_combobox = ttk.Combobox(color_palette_frame, width=10, textvariable=self.quant_mode_var, state="readonly")
        self.quant_mode_combobox['values'] = ('Kmeans', 'MedianCut', 'Octree', 'Random')
        self.quant_mode_combobox.current(0)
        self.quant_mode_combobox.grid(row=0, column=0, padx=(0,5), pady=5, sticky=tk.W)
        self.quant_mode_combobox.bind("<<ComboboxSelected>>", self.display_colormap_palette)
        TkToolTip.create(self.quant_mode_combobox, "KMeans: Groups similar colors together and then averages.\n\nMedianCut: Splits colors into regions and then averages.", delay=400, padx=5, pady=10)

        # Color Palette Combobox
        self.color_palettes = {
            "From Image":  [""],
            "Game Boy Pocket":  ["#283818", "#607050", "#889878", "#b0c0a0"],
            "Ice Cream":        ["#7c3f58", "#eb6b6f", "#f9a875", "#fff6d3"],
            "Demichrome":       ["#211e20", "#555568", "#a0a08b", "#e9efec"],
            "Kirokaze":         ["#332c50", "#46878f", "#94e344", "#e2f3e4"],
            "Rustic":           ["#2c2137", "#764462", "#edb4a1", "#a96868"],
            "Mist":             ["#2d1b00", "#1e606e", "#5ab9a8", "#c4f0c2"],
            "Wish":             ["#622e4c", "#7550e8", "#608fcf", "#8be5ff"],
            "Neon":             ["#f8e3c4", "#cc3495", "#6b1fb1", "#0b0630"],
            "Crimson":          ["#eff9d6", "#ba5044", "#7a1c4b", "#1b0326"],
            "Aqua":             ["#002b59", "#005881", "#00afb4", "#95e5d7"],
            "Nostalgia":        ["#d0d058", "#a0a840", "#708028", "#405010"],
            "Cherry":           ["#2d162c", "#412752", "#683a68", "#9775a6"],
            "Pastel":           ["#46425e", "#5b768d", "#d17c7c", "#f6c6a8"],
            "Gold":             ["#210b1b", "#4d222c", "#9d654c", "#cfab51"],
            "Candy":            ["#151640", "#3f6d9e", "#f783b0", "#e6f2ef"],
            "Emerald":          ["#2c2137", "#446176", "#3fac95", "#a1ef8c"],
            "Chrome":           ["#221e31", "#41485d", "#778e98", "#c5dbd4"],
            "Soviet":           ["#e8d6c0", "#92938d", "#a1281c", "#000000"],
            "Sepia":            ["#cca66e", "#99683d", "#664930", "#332920"],
            "Slime":            ["#d1cb95", "#40985e", "#1a644e", "#04373b", "#0a1a2f"],
            "Sunset Beach":     ["#ffcf47", "#f98542", "#fc6767", "#4b79a1", "#283e51"],
            "Cyberpunk City":   ["#1a1a2e", "#f72585", "#3a0ca3", "#4361ee", "#4cc9f0"],
            "Forest Dawn":      ["#2e352f", "#6a8860", "#d3b88c", "#f4e2d8", "#8b5a2b"],
            "Retro Arcade":     ["#00ff87", "#ff4b5c", "#ff9f1c", "#011627", "#39c0ed"],
            "Vintage Cinema":   ["#1c1b29", "#ae7f42", "#856046", "#dbd3c9", "#5a3f37"],
            "Aqua2":            ["#000000", "#083131", "#105d63", "#318e9c", "#84bece", "ffffff"],
            "Anaglyph":         ["#1a0908", "#4d1313", "#b3242d", "#f26174", "#85b1f2", "335ccc", "141f66", "0a0a1a"],
            "DMG":              ["#333030", "#423d4d", "#4d5966", "#667f59", "#88985b", "b3b37e", "d8ceae", "f0f0e4"],
            "Spoky":            ["#161317", "#2c262d", "#52474e", "#7a676f", "#522d2d", "#72403b", "#895142", "#aa644d", "#7e5c57", "#a68576", "#c2af91", "#f5e9bf", "#5d4e54", "#94797f", "#be9b97", "#e6bdaf", "#3f3e43", "#635d67", "#837481", "#a99aa4", "#303332", "#494e4b", "#5e675f", "#788374", "#242426", "#3e4143", "#5d6567", "#748382"],
            "Fex":              ["#f2f0e5", "#b8b5b9", "#868188", "#646365", "#45444f", "#3a3858", "#212123", "#352b42", "#43436a", "#4b80ca", "#68c2d3", "#a2dcc7", "#ede19e", "#d3a068", "#b45252", "#6a536e", "#4b4158", "#80493a", "#a77b5b", "#e5ceb4", "#c2d368", "#8ab060", "#567b79", "#4e584a", "#7b7243", "#b2b47e", "#edc8c4", "#cf8acb", "#5f556a"],
            "Apollo":           ["#172038", "#253a5e", "#3c5e8b", "#4f8fba", "#73bed3", "#a4dddb", "#19332d", "#25562e", "#468232", "#75a743", "#a8ca58", "#d0da91", "#4d2b32", "#7a4841", "#ad7757", "#c09473", "#d7b594", "#e7d5b3", "#341c27", "#602c2c", "#884b2b", "#be772b", "#de9e41", "#e8c170", "#241527", "#411d31", "#752438", "#a53030", "#cf573c", "#da863e", "#1e1d39", "#402751", "#7a367b", "#a23e8c", "#c65197", "#df84a5", "#090a14", "#10141f", "#151d28", "#202e37", "#394a50", "#577277", "#819796", "#a8b5b2", "#c7cfcc", "#ebede9"],
            "C64":              ["#2e222f", "#3e3546", "#625565", "#966c6c", "#ab947a", "#694f62", "#7f708a", "#9babb2", "#c7dcd0", "#ffffff", "#6e2727", "#b33831", "#ea4f36", "#f57d4a", "#ae2334", "#e83b3b", "#fb6b1d", "#f79617", "#f9c22b", "#7a3045", "#9e4539", "#cd683d", "#e6904e", "#fbb954", "#4c3e24", "#676633", "#a2a947", "#d5e04b", "#fbff86", "#165a4c", "#239063", "#1ebc73", "#91db69", "#cddf6c", "#313638", "#374e4a", "#547e64", "#92a984", "#b2ba90", "#0b5e65", "#0b8a8f", "#0eaf9b", "#30e1b9", "#8ff8e2", "#323353", "#484a77", "#4d65b4", "#4d9be6", "#8fd3ff", "#45293f", "#6b3e75", "#905ea9", "#a884f3", "#eaaded", "#753c54", "#a24b6f", "#cf657f", "#ed8099", "#831c5d", "#c32454", "#f04f78", "#f68181", "#fca790", "#fdcbb0"],
            }
        self.color_palette_combobox = ttk.Combobox(color_palette_frame, width=18, state="readonly")
        self.color_palette_combobox['values'] = list(self.color_palettes.keys())
        self.color_palette_combobox.current(0)
        self.color_palette_combobox.grid(row=0, column=1, padx=(5,0), pady=5, sticky=tk.W)
        self.color_palette_combobox.bind("<<ComboboxSelected>>", self.display_colormap_palette)
        TkToolTip.create(self.color_palette_combobox, "Use a predefined color palette", delay=400, padx=5, pady=10)

        # Number of colors
        tk.Label(self.root, text="Number of Colors:").grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        self.num_colors_spinbox = tk.Spinbox(self.root, from_=2, to=999, width=5, command=self.display_colormap_palette)
        self.num_colors_spinbox.grid(row=4, column=1, padx=10, pady=5, sticky=tk.W)
        self.num_colors_spinbox.delete(0, "end")
        self.num_colors_spinbox.insert(0, "32")
        self.num_colors_spinbox.bind("<KeyRelease>", self.display_colormap_palette)
        TkToolTip.create(self.num_colors_spinbox, "The number of distinct colors used", delay=400, padx=5, pady=10)

        # Image downscale amount
        tk.Label(self.root, text="Image Downscale:").grid(row=5, column=0, padx=10, pady=5, sticky=tk.W)
        self.image_downscale_spinbox = tk.Spinbox(self.root, from_=1, to=16, width=5)
        self.image_downscale_spinbox.grid(row=5, column=1, padx=10, pady=5, sticky=tk.W)
        self.image_downscale_spinbox.delete(0, "end")
        self.image_downscale_spinbox.insert(0, "4")
        TkToolTip.create(self.image_downscale_spinbox, "The downscale factor\n\nIf Downscale Factor = 4, the image will be divided by 4, or 25% it's original size", delay=400, padx=5, pady=10)

        # Restore original size checkbox
        self.restore_size_var = tk.BooleanVar(value=True)
        self.restore_size_checkbutton = tk.Checkbutton(self.root, text="Restore Original Size", overrelief="groove", variable=self.restore_size_var)
        self.restore_size_checkbutton.grid(row=6, column=0, padx=(8,0), pady=5, sticky=tk.W)
        TkToolTip.create(self.restore_size_checkbutton, "Optionally resize the image back to it's original dimensions", delay=400, padx=5, pady=10)

        # Save Colormap checkbox
        self.save_colormap_var = tk.BooleanVar(value=False)
        self.save_colormap_checkbutton = tk.Checkbutton(self.root, text="Save Palette", overrelief="groove", variable=self.save_colormap_var)
        self.save_colormap_checkbutton.grid(row=6, column=1, padx=(5,0), pady=5, sticky=tk.W)
        TkToolTip.create(self.save_colormap_checkbutton, "Optionally save the current pallete for future use", delay=400, padx=5, pady=10)

        # Process button
        prococess_image_button = tk.Button(self.root, text="Process Image", width=13, overrelief="groove", command=self.process)
        prococess_image_button.grid(row=3, column=3, rowspan=4, padx=10, pady=5, sticky=tk.NSEW)
        prococess_image_button.bind("<Button-3>", lambda event: self.open_directory(self.output_path_entry.get()))

        # Frame for color palette display
        self.palette_frame = tk.Frame(self.root, relief="ridge", borderwidth=1)
        self.palette_frame.grid(row=3, column=2, rowspan=4, padx=(0,10), pady=5, sticky=tk.NSEW)
        TkToolTip.create(self.palette_frame, "(Drop image here)\nThe color palette", delay=400, padx=5, pady=10)
        self.colormap_label = tk.Label(self.palette_frame, text="\t\t")
        self.colormap_label.grid(row=0, column=0, columnspan=3, padx=10, pady=5)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=200, mode="determinate")
        self.progress.grid(row=7, column=0, columnspan=4, padx=10, pady=(5, 10), sticky=tk.EW)
        self.progress['value'] = 0


    def setup_dnd(self):
        self.image_path_entry.drop_target_register(DND_FILES)
        self.image_path_entry.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, self.image_path_entry))

        self.output_path_entry.drop_target_register(DND_FILES)
        self.output_path_entry.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, self.output_path_entry))

        self.colormap_path_entry.drop_target_register(DND_FILES)
        self.colormap_path_entry.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, self.colormap_path_entry))

        self.palette_frame.drop_target_register(DND_FILES)
        self.palette_frame.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, self.colormap_path_entry))

#endregion
################################################################################################################################################
#region - GUI Helpers


    def update_output_entry(self, input_path):
        if input_path:
            basename, _ = os.path.splitext(os.path.basename(input_path))
            output_path = os.path.join(os.path.dirname(input_path), f"{basename}_px.png")
            self.output_path_entry.delete(0, tk.END)
            self.output_path_entry.insert(0, os.path.normpath(output_path))
            self.output_path_entry.xview_moveto(1)


    def select_input_path(self):
        filename = filedialog.askopenfilename(title="Select Image", filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;")])
        if filename:
            self.image_path_entry.delete(0, tk.END)
            self.image_path_entry.insert(0, os.path.normpath(filename))
            self.image_path_entry.xview_moveto(1)
            self.update_output_entry(filename)
            self.display_colormap_palette()


    def select_output_path(self):
        filename = filedialog.asksaveasfilename(title="Save Processed Image", defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if filename:
            self.output_path_entry.delete(0, tk.END)
            self.output_path_entry.insert(0, os.path.normpath(filename))
            self.output_path_entry.xview_moveto(1)
            self.display_colormap_palette()


    def select_colormap_path(self):
        filename = filedialog.askopenfilename(title="Select Colormap Image (optional)", filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if filename:
            self.colormap_path_entry.delete(0, tk.END)
            self.colormap_path_entry.insert(0, os.path.normpath(filename))
            self.colormap_path_entry.xview_moveto(1)
            self.display_colormap_palette()


    def on_drop(self, event, entry_widget):
        data = event.data
        pattern = r'\{[^}]+\}|\S+'
        filepaths = re.findall(pattern, data)
        first_filepath = os.path.normpath(filepaths[0])
        if first_filepath.startswith('{') and first_filepath.endswith('}'):
            first_filepath = first_filepath[1:-1]
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, first_filepath)
        entry_widget.xview_moveto(1)
        self.display_colormap_palette()
        if entry_widget == self.image_path_entry:
            self.update_output_entry(first_filepath)


#endregion
################################################################################################################################################
#region - Primary


    def process(self):
        image_path = self.image_path_entry.get()
        output_path = self.output_path_entry.get()
        colormap_path = self.colormap_path_entry.get() or None
        if not image_path or not output_path:
            messagebox.showwarning("Missing input", "Please select the input image and output file.")
            return
        try:
            num_colors = self.num_colors_spinbox.get()
            if not num_colors:
                num_colors = 2
            else:
                num_colors = int(num_colors)
        except ValueError:
            messagebox.showerror("Invalid input", "~Number of Colors~\n\nPlease enter a valid whole number.")
            return
        try:
            downscale_factor = int(self.image_downscale_spinbox.get())
        except ValueError:
            messagebox.showerror("Invalid input", "~Image Downscale~\n\nPlease enter a valid whole number.")
            return
        restore_size = self.restore_size_var.get()
        quant_mode = self.quant_mode_var.get()
        self.process_image(image_path, output_path, colormap_path, num_colors, restore_size, quant_mode, downscale_factor)


    def process_image(self, image_path, output_path, colormap_path=None, num_colors=32, restore_size=True, quant_mode='Kmeans', downscale_factor=4):
        try:
            with Image.open(image_path) as img:
                self.progress.config(value=5)
                self.root.update_idletasks()
                original_size = img.size
                new_size = (original_size[0] // downscale_factor, original_size[1] // downscale_factor)
                img_resized = img.resize(new_size, Image.NEAREST)
                self.progress.config(value=10)
                self.root.update_idletasks()
                selected_palette = self.color_palette_combobox.get()
                if selected_palette != "From Image":
                    palette = np.array([list(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) for color in self.color_palettes[selected_palette]])
                    num_colors = len(palette)
                else:
                    img_rgb = img_resized.convert('RGB')
                    if colormap_path:
                        palette = self.get_colormap(colormap_path, num_colors)
                    else:
                        palette = self.quantize_image(img_rgb, num_colors, quant_mode)
                    num_colors = len(palette)
                num_colors = len(palette)
                self.progress.config(value=20)
                self.root.update_idletasks()

                def find_nearest_color(pixel):
                    distances = np.linalg.norm(palette - pixel, axis=1)
                    return palette[np.argmin(distances)]

                quantized_pixels = np.apply_along_axis(find_nearest_color, 1, np.array(img_resized).reshape(-1, 3))
                self.progress.config(value=35)
                self.root.update_idletasks()
                quantized_image = Image.fromarray(quantized_pixels.reshape(new_size[1], new_size[0], 3).astype('uint8'))
                self.progress.config(value=50)
                self.root.update_idletasks()
                if restore_size:
                    quantized_image = quantized_image.resize(original_size, Image.NEAREST)
                quantized_image.save(output_path)
                self.progress.config(value=75)
                self.root.update_idletasks()
                if self.save_colormap_var.get():
                    palette_image_path = os.path.splitext(image_path)[0] + "_palette.png"
                    palette_image = Image.new('RGB', (num_colors, 1))
                    palette_image.putdata([tuple(color) for color in palette])
                    palette_image = palette_image.resize((num_colors * 10, 10), Image.NEAREST)
                    palette_image.save(palette_image_path)
                self.progress.config(value=100)
                self.root.update_idletasks()
                if messagebox.askyesno("Success", f"Image saved to:\n{output_path}\n\nOpen image?"):
                    self.open_current_image(output_path)
                self.progress.config(value=0)
                self.root.update_idletasks()
        except FileNotFoundError:
            messagebox.showerror("Error", "File not found. Please check the file path.")
        except ValueError as ve:
            messagebox.showerror("Error", f"Value error: {ve}")
        except Exception as e:
            messagebox.showerror("Error", str(e))



#endregion
################################################################################################################################################
#region - Colormap


    def get_colormap(self, colormap_path, num_colors):
        quant_mode = self.quant_mode_combobox.get()
        with Image.open(colormap_path) as cmap_img:
            cmap_img = cmap_img.convert('RGB')
            width, height = cmap_img.size
            cmap_img = cmap_img.resize((width // 4, height // 4))
        return self.quantize_image(cmap_img, num_colors, quant_mode)


    def quantize_image(self, img, num_colors, quant_mode):
        pixels = np.array(img).reshape(-1, 3)
        unique_pixels = np.unique(pixels, axis=0)
        num_colors = min(num_colors, unique_pixels.shape[0])
        if quant_mode == 'Kmeans':
            kmeans = KMeans(n_clusters=num_colors, random_state=42)
            kmeans.fit(unique_pixels)
            palette = np.rint(kmeans.cluster_centers_).astype(int)
        elif quant_mode == 'MedianCut':
            img_quantized = img.quantize(colors=num_colors, method=Image.MEDIANCUT)
            palette = np.array(img_quantized.getpalette()).reshape(-1, 3)[:num_colors]
        elif quant_mode == 'Octree':
            img_quantized = img.quantize(colors=num_colors, method=Image.FASTOCTREE)
            palette = np.array(img_quantized.getpalette()).reshape(-1, 3)[:num_colors]
        elif quant_mode == 'Random':
            indices = np.random.choice(unique_pixels.shape[0], num_colors, replace=False)
            palette = unique_pixels[indices]
        return palette


    def display_colormap_palette(self, event=None):
        selected_palette = self.color_palette_combobox.get()
        if selected_palette != "From Image":
            self.quant_mode_combobox.config(state="disabled")
            self.num_colors_spinbox.config(state="disabled")
            palette = np.array([list(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) for color in self.color_palettes[selected_palette]])
            num_colors = len(palette)
        else:
            self.quant_mode_combobox.config(state="readonly")
            self.num_colors_spinbox.config(state="normal")
            colormap_path = self.colormap_path_entry.get() if self.colormap_path_entry.get() else self.image_path_entry.get()
            if not colormap_path:
                for widget in self.palette_frame.winfo_children():
                    widget.destroy()
                return
            try:
                num_colors = int(self.num_colors_spinbox.get())
                if num_colors < 1:
                    num_colors = 2
                elif num_colors > 999:
                    num_colors = 999
                    self.num_colors_spinbox.delete(0, "end")
                    self.num_colors_spinbox.insert(0, num_colors)
            except ValueError:
                num_colors = 2
            palette = self.get_colormap(colormap_path, num_colors)
        for widget in self.palette_frame.winfo_children():
            widget.destroy()
        if num_colors > 25:
            grid_size = int(num_colors ** 0.5) + 1
            canvas_width = 100
            canvas_height = 100
            rect_width = canvas_width // grid_size
            rect_height = canvas_height // grid_size
            canvas = tk.Canvas(self.palette_frame, width=canvas_width, height=canvas_height)
            canvas.grid(row=0, column=0, padx=10, pady=5, sticky=tk.NSEW)
            for i, color in enumerate(palette):
                hex_color = f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}'
                row = i // grid_size
                col = i % grid_size
                canvas.create_rectangle(col * rect_width, row * rect_height, (col + 1) * rect_width, (row + 1) * rect_height, fill=hex_color, outline=hex_color)
        else:
            canvas_height = 100
            rect_height = canvas_height // num_colors
            canvas = tk.Canvas(self.palette_frame, width=100, height=canvas_height)
            canvas.grid(row=0, column=0, padx=10, pady=5, sticky=tk.NSEW)
            for i, color in enumerate(palette):
                hex_color = f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}'
                canvas.create_rectangle(0, i * rect_height, 100, (i + 1) * rect_height, fill=hex_color, outline=hex_color)
        self.palette_frame.grid_columnconfigure(0, weight=1)
        self.palette_frame.grid_rowconfigure(0, weight=1)



#endregion
################################################################################################################################################
#region - Misc


    def open_directory(self, directory):
        directory = os.path.dirname(directory)
        try:
            if os.path.isdir(directory):
                os.startfile(directory)
        except Exception: return


    def open_current_image(self, filepath):
            try:
                os.startfile(filepath)
            except Exception: return


#endregion
################################################################################################################################################
#region - Framework


    def set_appid(self):
        myappid = 'Pixel8.Nenotriple'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


    def set_icon(self):
        import sys
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        elif __file__:
            application_path = os.path.dirname(__file__)
        self.icon_path = os.path.join(application_path, "icon.ico")
        self.root.iconbitmap(self.icon_path)


    def setup_window(self):
        self.root.title("Pixel8 - github.com/Nenotriple")
        self.root.minsize(675, 280) # w, h
        window_width = 675
        window_height = 280
        position_right = root.winfo_screenwidth()//2 - window_width//2
        position_top = root.winfo_screenheight()//2 - window_height//2
        self.root.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = Pixel8(root)
    root.mainloop()
