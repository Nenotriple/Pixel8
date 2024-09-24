#region - Header


"""
########################################
#                                      #
#                Pixel8                #
#                                      #
#   Version : v1.01                    #
#   Author  : github.com/Nenotriple    #
#                                      #
########################################


-------------
Description:
-------------

Pixelate an image using various methods and conditions.

Process images by reducing their color depth and generating corresponding color palettes.
It employs various quantization algorithms and offers customizable settings for fine-tuning the pixelation process.

1) Reduce the number of colors used in the image.
2) The image is shrunk down, forcing the remaining colors to fill larger areas.
   - Optionally resize the image back to its original dimensions.


-------------
Key features:
-------------

01) Image Input:
    - Drag and drop images directly into the application for quick processing.

02) Image Resizing:
    - Downscale images to achieve pixelated effects, with the option to restore them to their original size afterward.

03) Color Reduction:
    - Reduce the number of colors in an image to create a distinct pixel art style.

04) Palette - Generation:
    - Generate color palettes using various methods, including:
      - k-means clustering, Simple quantization, octree quantization, MaxCoverage quantization, and random selection.

05) Palette - Customizable Color:
    - Utilize color palettes from other images or choose from a selection of predefined palettes.

06) Palette - Export:
    - Save your generated color palettes as image files for easy reference and reuse.

07) Fine-Tuned Control:
    - Adjust the number of colors, downscaling factor, and image sharpening to achieve your desired pixel art aesthetic.

08) Color Transfer:
    - Experiment with nine different color transfer modes to fine-tune the color mapping process, including:
      - Normal, Blend
        - `Normal` mode assigns each pixel to the nearest color in the palette.
        - `Blend` mode blends the two nearest colors based on their distance.

09) Efficient Batch Processing:
    - Process multiple images within a directory and its subfolders simultaneously.


"""


#endregion
################################################################################################################################################
#region - Imports


# Standard Library
import os
import re
import sys
import time
import ctypes
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, TclError


# Third-Party
import numpy as np
from tkinterdnd2 import TkinterDnD, DND_FILES
from sklearn.cluster import KMeans
from sklearn.neighbors import KDTree
from PIL import Image, ImageFilter, ImageTk


# Local Scripts
from TkToolTip import TkToolTip


#endregion
################################################################################################################################################
#region - CLASS: Pixel8


APP_VERSION = "v1.01"

# Used for resizing images everywhere except for the "Before" thumbnail.
RESAMPLE_FUNC = Image.NEAREST

# Supported image file types
FILETYPES = [".png", ".jpg", ".jpeg", ".jpg_large", ".bmp", ".jfif", ".tiff", ".tif", ".webp", ".ico"]


class Pixel8:
    def __init__(self, root):
        self.root = root
        self.set_appid()
        self.setup_window()
        self.set_icon()
        self.create_widgets()
        self.setup_drag_and_drop()
        self._update()
        self.update_palette_list()


#endregion
################################################################################################################################################
#region -   GUI


    def create_widgets(self):
        # Configure columns to expand
        self.root.columnconfigure(1, weight=1)


# --------------------------------------
# Input/Output Widgets
# --------------------------------------


        # Input image path cluster
        self.input_label = tk.Label(self.root, text="Input:", anchor='w')
        self.input_label.grid(row=0, column=0, padx=10, pady=5, sticky='ew')
        TkToolTip.create(self.input_label,
                 "(Drop image here)\n"
                 "The input image path",
                 delay=1000, padx=5, pady=10)
        self.image_path_entry = tk.Entry(self.root)
        self.image_path_entry.grid(row=0, column=1, padx=(10,5), pady=5, sticky='ew', columnspan=2)
        input_button_frame = tk.Frame(self.root)
        input_button_frame.grid(row=0, column=3, padx=(5,10), pady=5, sticky='w')
        self.browse_input_button = tk.Button(input_button_frame, text="Browse...", width=13, overrelief="groove", command=self.select_input_path)
        self.browse_input_button.pack(side=tk.LEFT)
        self.open_input_button = tk.Button(input_button_frame, text="Open", width=5, overrelief="groove", command=lambda: self.open_directory(self.image_path_entry.get()))
        self.open_input_button.pack(side=tk.LEFT, padx=5)
        self.clear_input_button = tk.Button(input_button_frame, text="X", width=1, overrelief="groove", command=lambda: [self.image_path_entry.delete(0, 'end'), self.display_colormap_palette(), self.clear_before_thumbnail()])
        self.clear_input_button.pack(side=tk.LEFT)


        # Output image path cluster
        self.output_label = tk.Label(self.root, text="Output:", anchor='w')
        self.output_label.grid(row=1, column=0, padx=10, pady=5, sticky='ew')
        TkToolTip.create(self.output_label,
                 "(Drop image here)\n"
                 "The filename and path the image will be saved to",
                 delay=1000, padx=5, pady=10)
        self.output_path_entry = tk.Entry(self.root)
        self.output_path_entry.grid(row=1, column=1, padx=(10,5), pady=5, sticky='ew', columnspan=2)
        output_button_frame = tk.Frame(self.root)
        output_button_frame.grid(row=1, column=3, padx=(5,10), pady=5, sticky='w')
        self.browse_output_button = tk.Button(output_button_frame, text="Save As...", width=13, overrelief="groove", command=self.select_output_path)
        self.browse_output_button.pack(side=tk.LEFT)
        self.open_output_button = tk.Button(output_button_frame, text="Open", width=5, overrelief="groove", command=lambda: self.open_directory(self.output_path_entry.get()))
        self.open_output_button.pack(side=tk.LEFT, padx=5)
        self.clear_output_button = tk.Button(output_button_frame, text="X", width=1, overrelief="groove", command=lambda: [self.output_path_entry.delete(0, 'end')])
        self.clear_output_button.pack(side=tk.LEFT)


        # Colormap path cluster
        self.color_palette_label = tk.Label(self.root, text="Color Palette (optional):", anchor='w')
        self.color_palette_label.grid(row=2, column=0, padx=10, pady=5, sticky='ew')
        TkToolTip.create(self.color_palette_label,
                 "(Drop image here)\n"
                 "Use any other image as a palette for the output image\n\n"
                 "If no path is provided, the input image will be used as the palette",
                 delay=1000, padx=5, pady=10)
        self.colormap_path_entry = tk.Entry(self.root)
        self.colormap_path_entry.grid(row=2, column=1, padx=(10,5), pady=5, sticky='ew', columnspan=2)
        self.colormap_path_entry.bind("<KeyRelease>", self.display_colormap_palette)
        colormap_button_frame = tk.Frame(self.root)
        colormap_button_frame.grid(row=2, column=3, padx=(5,10), pady=5, sticky='w')
        self.browse_colormap_button = tk.Button(colormap_button_frame, text="Browse...", width=13, overrelief="groove", command=self.select_colormap_path)
        self.browse_colormap_button.pack(side=tk.LEFT)
        self.open_colormap_button = tk.Button(colormap_button_frame, text="Open", width=5, overrelief="groove", command=lambda: self.open_directory(self.colormap_path_entry.get()))
        self.open_colormap_button.pack(side=tk.LEFT, padx=5)
        self.clear_colormap_button = tk.Button(colormap_button_frame, text="X", width=1, overrelief="groove", command=lambda: [self.colormap_path_entry.delete(0, 'end'), self.display_colormap_palette()])
        self.clear_colormap_button.pack(side=tk.LEFT)


        ttk.Separator(self.root, orient="horizontal").grid(row=3, column=0, columnspan=4, padx=10, pady=5, sticky='ew')


# --------------------------------------
# Color Settings
# --------------------------------------


        # Quantization mode combobox
        self.color_mode_label = tk.Label(self.root, text="Palette:", anchor='w')
        self.color_mode_label.grid(row=4, column=0, padx=10, pady=5, sticky='ew')
        TkToolTip.create(self.color_mode_label,
                 "KMeans: Groups similar colors together and then averages.\n\n"
                 "Simple: Simply reduce the number of colors to the target.\n\n"
                 "MaxCoverage: Selects colors that cover the most pixels.\n\n"
                 "Octree: Builds a tree structure to reduce colors and then averages.\n\n"
                 "Random: Selects random colors from the image.",
                 delay=1000, padx=5, pady=10)
        self.quant_mode_var = tk.StringVar()
        color_palette_frame = tk.Frame(self.root)
        color_palette_frame.grid(row=4, column=1, padx=10, sticky='w')
        self.quant_mode_combobox = ttk.Combobox(color_palette_frame, width=10, textvariable=self.quant_mode_var, state="readonly")
        self.quant_mode_combobox['values'] = ('Kmeans', 'Simple', 'Octree', 'MaxCoverage', 'Random')
        self.quant_mode_combobox.current(0)
        self.quant_mode_combobox.grid(row=0, column=0, padx=(0,5), pady=5, sticky='w')
        self.quant_mode_combobox.bind("<<ComboboxSelected>>", self.display_colormap_palette)

        # Color Palette Combobox
        self.color_palettes = {
            "From Image":       [""],
            "Game Boy Pocket":  ["#283818", "#607050", "#889878", "#b0c0a0"],
            "Ice Cream":        ["#7c3f58", "#eb6b6f", "#f9a875", "#fff6d3"],
            "Demichrome":       ["#211e20", "#555568", "#a0a08b", "#e9efec"],
            "Kirokaze":         ["#332c50", "#46878f", "#94e344", "#e2f3e4"],
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
            "Spooky":           ["#161317", "#2c262d", "#52474e", "#7a676f", "#522d2d", "#72403b", "#895142", "#aa644d", "#7e5c57", "#a68576", "#c2af91", "#f5e9bf", "#5d4e54", "#94797f", "#be9b97", "#e6bdaf", "#3f3e43", "#635d67", "#837481", "#a99aa4", "#303332", "#494e4b", "#5e675f", "#788374", "#242426", "#3e4143", "#5d6567", "#748382"],
            "Fex":              ["#f2f0e5", "#b8b5b9", "#868188", "#646365", "#45444f", "#3a3858", "#212123", "#352b42", "#43436a", "#4b80ca", "#68c2d3", "#a2dcc7", "#ede19e", "#d3a068", "#b45252", "#6a536e", "#4b4158", "#80493a", "#a77b5b", "#e5ceb4", "#c2d368", "#8ab060", "#567b79", "#4e584a", "#7b7243", "#b2b47e", "#edc8c4", "#cf8acb", "#5f556a"],
            "Apollo":           ["#172038", "#253a5e", "#3c5e8b", "#4f8fba", "#73bed3", "#a4dddb", "#19332d", "#25562e", "#468232", "#75a743", "#a8ca58", "#d0da91", "#4d2b32", "#7a4841", "#ad7757", "#c09473", "#d7b594", "#e7d5b3", "#341c27", "#602c2c", "#884b2b", "#be772b", "#de9e41", "#e8c170", "#241527", "#411d31", "#752438", "#a53030", "#cf573c", "#da863e", "#1e1d39", "#402751", "#7a367b", "#a23e8c", "#c65197", "#df84a5", "#090a14", "#10141f", "#151d28", "#202e37", "#394a50", "#577277", "#819796", "#a8b5b2", "#c7cfcc", "#ebede9"],
            "C64":              ["#2e222f", "#3e3546", "#625565", "#966c6c", "#ab947a", "#694f62", "#7f708a", "#9babb2", "#c7dcd0", "#ffffff", "#6e2727", "#b33831", "#ea4f36", "#f57d4a", "#ae2334", "#e83b3b", "#fb6b1d", "#f79617", "#f9c22b", "#7a3045", "#9e4539", "#cd683d", "#e6904e", "#fbb954", "#4c3e24", "#676633", "#a2a947", "#d5e04b", "#fbff86", "#165a4c", "#239063", "#1ebc73", "#91db69", "#cddf6c", "#313638", "#374e4a", "#547e64", "#92a984", "#b2ba90", "#0b5e65", "#0b8a8f", "#0eaf9b", "#30e1b9", "#8ff8e2", "#323353", "#484a77", "#4d65b4", "#4d9be6", "#8fd3ff", "#45293f", "#6b3e75", "#905ea9", "#a884f3", "#eaaded", "#753c54", "#a24b6f", "#cf657f", "#ed8099", "#831c5d", "#c32454", "#f04f78", "#f68181", "#fca790", "#fdcbb0"],
            }
        self.color_palette_combobox = ttk.Combobox(color_palette_frame, width=18, state="readonly")
        self.color_palette_combobox['values'] = list(self.color_palettes.keys())
        self.color_palette_combobox.current(0)
        self.color_palette_combobox.grid(row=0, column=1, padx=(5,0), pady=5, sticky='w')
        self.color_palette_combobox.bind("<<ComboboxSelected>>", self.display_colormap_palette)

        # Number of colors spinbox
        self.num_colors_label = tk.Label(self.root, text="Number of Colors:", anchor='w')
        self.num_colors_label.grid(row=5, column=0, padx=10, pady=5, sticky='ew')
        TkToolTip.create(self.num_colors_label,
                         "Range: From = 2, To = 256\n"
                         "The number of distinct colors used",
                         delay=1000, padx=5, pady=10)
        spinbox_frame1 = tk.Frame(self.root)
        spinbox_frame1.grid(row=5, column=1, sticky='w')
        self.num_colors_spinbox = tk.Spinbox(spinbox_frame1, from_=1, to=256, width=5, command=self.display_colormap_palette)
        self.num_colors_spinbox.grid(row=0, column=0, padx=10, pady=5, sticky='w')
        self.num_colors_spinbox.delete(0, "end")
        self.num_colors_spinbox.insert(0, "32")
        self.num_colors_spinbox.bind("<MouseWheel>", self.adjust_value_mousewheel)
        self.num_colors_spinbox.bind("<KeyRelease>", self.display_colormap_palette)

        # Nearest color combobox
        self.nearest_color_combobox = ttk.Combobox(spinbox_frame1, width=18, state="readonly")
        self.nearest_color_combobox['values'] = ['Normal', 'Blend']
        self.nearest_color_combobox.current(0)
        self.nearest_color_combobox.grid(row=0, column=1, padx=(38,0), pady=5, sticky='w')
        self.nearest_color_combobox.bind("<<ComboboxSelected>>", self.display_colormap_palette)
        TkToolTip.create(self.nearest_color_combobox,
                         "The color transfer mode",
                         delay=1000, padx=5, pady=10)


# --------------------------------------
# Image Settings
# --------------------------------------


        # Image downscale spinbox
        self.downscale_label = tk.Label(self.root, text="Image Downscale:", anchor='w')
        self.downscale_label.grid(row=6, column=0, padx=10, pady=5, sticky='ew')
        TkToolTip.create(self.downscale_label,
                         "0/1 = OFF | Range: From = 1, To = 128\n"
                         "If Downscale Factor = 4, the image will be divided by 4, or 25% its original size",
                         delay=1000, padx=5, pady=10)
        spinbox_frame2 = tk.Frame(self.root)
        spinbox_frame2.grid(row=6, column=1, sticky='w')
        self.image_downscale_spinbox = tk.Spinbox(spinbox_frame2, from_=1, to=128, width=5)
        self.image_downscale_spinbox.grid(row=0, column=0, padx=10, pady=5, sticky='w')
        self.image_downscale_spinbox.delete(0, "end")
        self.image_downscale_spinbox.insert(0, "4")
        self.image_downscale_spinbox.bind("<MouseWheel>", self.adjust_value_mousewheel)
        self.image_downscale_spinbox.bind("<KeyRelease>", self.display_colormap_palette)

        # Sharpen Spinbox
        self.sharpen_label = tk.Label(spinbox_frame2, text="Sharpen:")
        self.sharpen_label.grid(row=0, column=1, padx=(35, 0), pady=5, sticky='w')
        TkToolTip.create(self.sharpen_label,
                         "0 = OFF | Range: From = -100, To = 100\n"
                         "The sharpening amount applied to the image",
                         delay=1000, padx=5, pady=10)
        self.sharpen_spinbox = tk.Spinbox(spinbox_frame2, from_=-100, to=100, width=5)
        self.sharpen_spinbox.grid(row=0, column=2, padx=(38,0), pady=5, sticky='w')
        self.sharpen_spinbox.delete(0, "end")
        self.sharpen_spinbox.insert(0, "0")
        self.sharpen_spinbox.bind("<MouseWheel>", self.adjust_value_mousewheel)
        self.sharpen_spinbox.bind("<KeyRelease>", self.display_colormap_palette)

        # Restore original size checkbox
        self.restore_size_var = tk.BooleanVar(value=True)
        self.restore_size_checkbutton = tk.Checkbutton(self.root, text="Restore Original Size", overrelief="groove", variable=self.restore_size_var)
        self.restore_size_checkbutton.grid(row=7, column=0, padx=(8,0), pady=5, sticky='w')
        TkToolTip.create(self.restore_size_checkbutton,
                         "Optionally resize the image back to its original dimensions",
                         delay=1000, padx=5, pady=10)

        # Save Colormap checkbox
        checkbutton_frame = tk.Frame(self.root)
        checkbutton_frame.grid(row=7, column=1, sticky='w')
        self.save_colormap_var = tk.BooleanVar(value=False)
        self.save_colormap_checkbutton = tk.Checkbutton(checkbutton_frame, text="Save Palette", overrelief="groove", variable=self.save_colormap_var)
        self.save_colormap_checkbutton.grid(row=0, column=0, padx=(5,0), pady=5, sticky='w')
        TkToolTip.create(self.save_colormap_checkbutton, "Optionally save the current palette for future use", delay=1000, padx=5, pady=10)

        # Batch Mode checkbox
        self.batch_mode_var = tk.BooleanVar(value=False)
        self.batch_mode_checkbutton = tk.Checkbutton(checkbutton_frame, text="Batch Mode", overrelief="groove", variable=self.batch_mode_var, command=self.toggle_process_button_text)
        self.batch_mode_checkbutton.grid(row=0, column=1, padx=(5,0), pady=5, sticky='w')
        TkToolTip.create(self.batch_mode_checkbutton,
                         "Enable to allow the input and output entries to accept a folder path",
                         delay=1000, padx=5, pady=10)


# --------------------------------------
# Preview
# --------------------------------------


        # Preview cluster
        self.preview_frame = tk.Frame(self.root, relief="groove", borderwidth=4)
        self.preview_frame.grid(row=4, column=2, rowspan=4, padx=(0,5), pady=5, sticky='nsew')

        # Image preview
        self.debounce_delay = 200
        self.thumbnail_size = 115
        self.before_thumbnail = None
        self.thumbnail_process_id = None
        self.before_image_preview_canvas = tk.Canvas(self.preview_frame, width=self.thumbnail_size, height=self.thumbnail_size)
        self.before_image_preview_canvas.grid(row=0, column=0, sticky='nsew')
        ttk.Separator(self.preview_frame, orient="vertical").grid(row=0, column=1, sticky='ns')
        TkToolTip.create(self.before_image_preview_canvas,
                         "BEFORE image",
                         delay=1000, padx=5, pady=10)
        self.after_image_preview_canvas = tk.Canvas(self.preview_frame, width=self.thumbnail_size, height=self.thumbnail_size)
        self.after_image_preview_canvas.grid(row=0, column=2, sticky='nsew')
        ttk.Separator(self.preview_frame, orient="vertical").grid(row=0, column=3, sticky='ns')
        TkToolTip.create(self.after_image_preview_canvas,
                         "AFTER image",
                         delay=1000, padx=5, pady=10)

        # Palette preview
        self.palette_preview_canvas = tk.Canvas(self.preview_frame, width=self.thumbnail_size, height=self.thumbnail_size)
        self.palette_preview_canvas.grid(row=0, column=4, sticky='nsew')


# --------------------------------------
# Misc
# --------------------------------------


        # Process button
        self.stop_processing = False
        self.success_messages_enabled = True
        self.process_image_button = tk.Button(self.root, text="Process Image", width=13, overrelief="groove", command=self.toggle_process)
        self.process_image_button.grid(row=4, column=3, rowspan=4, padx=(5,10), pady=5, sticky='nsew')

        # Progress bar
        self.batch_progress = 0
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=200, mode="determinate")
        self.progress.grid(row=8, column=0, columnspan=4, padx=10, pady=(5, 10), sticky='ew')
        self.progress['value'] = 0


#endregion
################################################################################################################################################
#region -   GUI_Helpers


# --------------------------------------
# Entry Widgets
# --------------------------------------


    def update_output_entry(self, input_path):
        if input_path:
            basename, _ = os.path.splitext(os.path.basename(input_path))
            if not self.batch_mode_var.get() and not os.path.isdir(input_path):
                output_path = os.path.join(os.path.dirname(input_path), f"{basename}_px.png")
                self.display_before_thumbnail(input_path)
                self.process_settings(thumbnail=True)
            else:
                output_path = os.path.join(os.path.dirname(input_path), f"{basename}_px")
            self.output_path_entry.delete(0, 'end')
            self.output_path_entry.insert(0, os.path.normpath(output_path))
            self.output_path_entry.xview_moveto(1)
            if os.path.isfile(output_path):
                self.process_settings(thumbnail=True)


    def select_input_path(self):
        if self.batch_mode_var.get():
            foldername = filedialog.askdirectory(title="Select Folder")
            if foldername:
                self.image_path_entry.delete(0, 'end')
                self.image_path_entry.insert(0, os.path.normpath(foldername))
                self.image_path_entry.xview_moveto(1)
                self.update_output_entry(foldername)
        else:
            filename = filedialog.askopenfilename(title="Select Image", filetypes=[("Image files", f"*{';*'.join(FILETYPES)}")])
            if filename:
                self.image_path_entry.delete(0, 'end')
                self.image_path_entry.insert(0, os.path.normpath(filename))
                self.image_path_entry.xview_moveto(1)
                self.update_output_entry(filename)
                self.display_colormap_palette()
                self.display_before_thumbnail(filename)
                self.process_settings(thumbnail=True)


    def select_output_path(self):
        if self.batch_mode_var.get():
            foldername = filedialog.askdirectory(title="Select Folder")
            if foldername:
                self.output_path_entry.delete(0, 'end')
                self.output_path_entry.insert(0, os.path.normpath(foldername))
                self.output_path_entry.xview_moveto(1)
        else:
            filename = filedialog.asksaveasfilename(title="Save Processed Image", defaultextension=".png", filetypes=[("PNG files", "*.png")])
            if filename:
                self.output_path_entry.delete(0, 'end')
                self.output_path_entry.insert(0, os.path.normpath(filename))
                self.output_path_entry.xview_moveto(1)
                self.display_colormap_palette()


    def select_colormap_path(self):
        filename = filedialog.askopenfilename(title="Select Colormap Image (optional)", filetypes=[("Image files", f"*{';*'.join(FILETYPES)}")])
        if filename:
            self.colormap_path_entry.delete(0, 'end')
            self.colormap_path_entry.insert(0, os.path.normpath(filename))
            self.colormap_path_entry.xview_moveto(1)
            self.display_colormap_palette()
            self.display_before_thumbnail(filename)
            self.process_settings(thumbnail=True)


    def on_drop(self, event, entry_widget):
        data = event.data
        pattern = r'\{[^}]+\}|\S+'
        filepaths = re.findall(pattern, data)
        first_filepath = os.path.normpath(filepaths[0])
        if first_filepath.startswith('{') and first_filepath.endswith('}'):
            first_filepath = first_filepath[1:-1]
        if not os.path.isdir(first_filepath) and not any(first_filepath.lower().endswith(ext) for ext in FILETYPES):
            file_type = os.path.splitext(first_filepath)[1]
            supported_types = ', '.join(FILETYPES)
            messagebox.showerror("Unsupported File Type", f"The file type '{file_type}' is not supported.\n\nPlease try again with a supported image filetypes!\n\nSupported types: {supported_types}")
            return
        entry_widget.delete(0, 'end')
        entry_widget.insert(0, first_filepath)
        entry_widget.xview_moveto(1)
        if os.path.isdir(first_filepath):
            if entry_widget == self.image_path_entry:
                self.update_output_entry(first_filepath)
        else:
            self.display_colormap_palette()
            if entry_widget == self.image_path_entry:
                self.update_output_entry(first_filepath)


# --------------------------------------
# Misc
# --------------------------------------


    def _update(self, value=None):
        if value is not None:
            if self.batch_mode_var.get():
                value = self.batch_progress
            self.progress.config(value=value)
        root.update_idletasks()
        root.update()


    def toggle_widget_state(self, state):
        widgets = [ self.input_label,
                    self.image_path_entry,
                    self.browse_input_button,
                    self.clear_input_button,

                    self.output_label,
                    self.output_path_entry,
                    self.browse_output_button,
                    self.clear_output_button,

                    self.color_palette_label,
                    self.colormap_path_entry,
                    self.browse_colormap_button,
                    self.clear_colormap_button,

                    self.color_mode_label,
                    self.quant_mode_combobox,
                    self.color_palette_combobox,

                    self.num_colors_label,
                    self.num_colors_spinbox,
                    self.nearest_color_combobox,
                    self.sharpen_label,
                    self.sharpen_spinbox,

                    self.downscale_label,
                    self.image_downscale_spinbox,

                    self.restore_size_checkbutton,
                    self.save_colormap_checkbutton,
                    self.batch_mode_checkbutton
                    ]
        for widget in widgets:
            if isinstance(widget, ttk.Combobox) and state == "normal":
                widget.configure(state="readonly")
            else:
                widget.configure(state=state)


    def toggle_process_button_text(self):
        if self.batch_mode_var.get():
            text = "Batch\nProcess Images"
            self.clear_before_thumbnail()
            if self.color_palette_combobox.get() == "From Image":
                self.clear_palette()
        else:
            text = "Process Image"
            input_path = self.image_path_entry.get()
            if os.path.isfile(input_path):
                self.display_colormap_palette()
                self.display_before_thumbnail(input_path)
                self.process_settings(thumbnail=True)
        self.process_image_button.config(text=text)


    def adjust_value_mousewheel(self, event):
        widget = event.widget
        if event.delta > 0:
            widget.invoke('buttonup')
        else:
            widget.invoke('buttondown')


    def setup_drag_and_drop(self):
        def bind_dnd(widget, event, handler):
            if not widget.bind(event):
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind(event, handler)

        bind_dnd(self.image_path_entry, '<<Drop>>', lambda e: self.on_drop(e, self.image_path_entry))
        bind_dnd(self.output_path_entry, '<<Drop>>', lambda e: self.on_drop(e, self.output_path_entry))
        bind_dnd(self.colormap_path_entry, '<<Drop>>', lambda e: self.on_drop(e, self.colormap_path_entry))
        bind_dnd(self.before_image_preview_canvas, '<<Drop>>', lambda e: self.on_drop(e, self.image_path_entry))
        bind_dnd(self.palette_preview_canvas, '<<Drop>>', lambda e: self.on_drop(e, self.colormap_path_entry))


# --------------------------------------
# Context Menu
# --------------------------------------


    def create_colorpalette_context_menu(self):
        self.context_menu = tk.Menu(self.preview_frame, tearoff=0)
        self.context_menu.add_command(label="Save As...", command=self.save_palette_image)
        self.preview_frame.bind("<Button-3>", self.show_colorpalette_context_menu)


    def show_colorpalette_context_menu(self, event):
        if not self.preview_frame.winfo_children():
            return
        self.context_menu.post(event.x_root, event.y_root)


#endregion
################################################################################################################################################
#region -   Start_Process


    def toggle_process(self):
        if self.process_image_button['text'] in ["Process Image", "Batch\nProcess Images"]:
            self.process_settings()
        else:
            self.stop_processing = True
            self.process_image_button.config(text="Process Image")


# --------------------------------------
# Process Settings
# --------------------------------------


    def process_settings(self, thumbnail=False):
        image_path = self.image_path_entry.get()
        output_path = self.output_path_entry.get()
        colormap_path = self.colormap_path_entry.get() or None
        restore_size = self.restore_size_var.get()
        quant_mode = self.quant_mode_var.get()
        if not self.batch_mode_var.get() and os.path.isdir(image_path):
            messagebox.showwarning("Invalid Input", "The selected input is a folder, but batch mode is not enabled.\n\nPlease select a valid image file or enable batch mode to process a folder of images.")
            return
        if not thumbnail and (not image_path or not output_path):
            messagebox.showwarning("Missing Input", "Please select the input image and output path.")
            return
        try:
            num_colors = int(self.num_colors_spinbox.get() or 1)
            num_colors = max(1, min(num_colors, 256))
            self.num_colors_spinbox.delete(0, "end")
            self.num_colors_spinbox.insert(0, str(num_colors))
        except ValueError:
            messagebox.showerror("Invalid Input", "~Number of Colors~\n\nPlease enter a valid whole number.\n\nRange: From = 2, To = 256")
            return
        try:
            downscale_factor = int(self.image_downscale_spinbox.get())
            downscale_factor = max(1, min(128, downscale_factor))
            self.image_downscale_spinbox.delete(0, "end")
            self.image_downscale_spinbox.insert(0, downscale_factor)
        except ValueError:
            messagebox.showerror("Invalid Input", "~Image Downscale~\n\nPlease enter a valid whole number.\n\nRange: From = 1, To = 128")
            return
        try:
            sharpening_input = self.sharpen_spinbox.get()
            sharpening = int(sharpening_input) if sharpening_input else 0
            sharpening = max(-100, min(100, sharpening))
            self.sharpen_spinbox.delete(0, "end")
            self.sharpen_spinbox.insert(0, sharpening)
        except ValueError:
            messagebox.showerror("Invalid Input", "~Sharpen~\n\nPlease enter a valid whole number.\n\nRange: From = -100, To = 100")
            return
        if thumbnail and os.path.isfile(image_path) and not self.batch_mode_var.get():
            self.process_image(image_path, output_path, colormap_path, num_colors, restore_size, quant_mode, downscale_factor, sharpening, thumbnail=True)
        elif self.batch_mode_var.get():
            if thumbnail:
                return
            if not os.path.isdir(image_path):
                messagebox.showerror("Invalid Input", "~Input Path~\n\nBatch mode is enabled, but the input is a filepath!\n\nIf you want to process a single image, please disable batch mode.")
                return
            if messagebox.askyesno("Batch Mode", "Batch mode will process all images in the selected directory and its subfolders.\n\nImages will be saved to the output path with their folder structure preserved.\n\nDo you want to continue?"):
                self.process_image_button.config(text="Stop!")
                self.process_images_batch(image_path, output_path, colormap_path, num_colors, restore_size, quant_mode, downscale_factor, sharpening)
        else:
            self.process_image(image_path, output_path, colormap_path, num_colors, restore_size, quant_mode, downscale_factor, sharpening)


# --------------------------------------
# Batch Image Process
# --------------------------------------


    def process_images_batch(self, input_folder, output_folder, colormap_path=None, num_colors=32, restore_size=True, quant_mode='Kmeans', downscale_factor=4, sharpening=None):
        try:
            self.toggle_widget_state('disabled')
            image_files = [os.path.join(root, file)
                           for root, _, files in os.walk(input_folder)
                           for file in files if file.lower().endswith(tuple(FILETYPES))]
            total_images = len(image_files)
            if total_images == 0:
                messagebox.showinfo("No Images", "No valid image files found in the input folder.")
                return
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            processed_images = 0
            start_time = time.time()
            self.root.title(f"{APP_VERSION} - *Pixel8 - Processing...")
            for image_path in image_files:
                if self.stop_processing:
                    break
                relative_path = os.path.relpath(image_path, input_folder)
                output_path = os.path.join(output_folder, relative_path)
                output_dir = os.path.dirname(output_path)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                self.process_image(image_path, output_path, colormap_path, num_colors, restore_size, quant_mode, downscale_factor, sharpening)
                processed_images += 1
                self.batch_progress = int((processed_images / total_images) * 100)
                self._update(self.batch_progress)
                elapsed_time = time.time() - start_time
                formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time)) + f".{int((elapsed_time % 1) * 1000):03d}"
                self.root.title(f"{APP_VERSION} - *Pixel8 - Processing {processed_images} of {total_images} images - {formatted_time}")
            elapsed_time = time.time() - start_time
            formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time)) + f".{int((elapsed_time % 1) * 1000):03d}"
            self.root.title(f"{APP_VERSION} - Pixel8 - Done Processing!")
            if not self.stop_processing:
                if messagebox.askyesno("Success", f"{processed_images} of {total_images} images processed and saved to:\n{output_folder}\n\nTime taken: {formatted_time}\n\nOpen folder?"):
                    self.open_directory(output_folder)
            else:
                messagebox.showinfo("Process Interrupted", f"Processing was interrupted. {processed_images} of {total_images} images processed.")
        except TclError:
            return
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            try:
                self.stop_processing = False
                self.process_image_button.config(text="Process Image")
                self.root.title(f"{APP_VERSION} - Pixel8 - github.com/Nenotriple")
                self.toggle_widget_state('normal')
                self.batch_progress = 0
                self._update(self.batch_progress)
            except Exception:
                return


# --------------------------------------
# Image Process
# --------------------------------------


    def process_image(self, image_path, output_path, colormap_path=None, num_colors=32, restore_size=True, quant_mode='Kmeans', downscale_factor=4, sharpening=None, thumbnail=False):
        try:
            if thumbnail:
                self.process_thumbnail(colormap_path, num_colors, quant_mode, downscale_factor, sharpening)
            else:
                self.process_full_image(image_path, output_path, colormap_path, num_colors, restore_size, quant_mode, downscale_factor, sharpening)
        except TclError:
            return
        except FileNotFoundError:
            messagebox.showerror("Error", "File not found. Please check the file path.")
        except ValueError as ve:
            messagebox.showerror("Error", f"Value error: {ve}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


#endregion
################################################################################################################################################
#region -   Process_Image


# --------------------------------------
# Initial
# --------------------------------------


    def process_thumbnail(self, colormap_path, num_colors, quant_mode, downscale_factor, sharpening):
        def _process_thumbnail(colormap_path, num_colors, quant_mode, downscale_factor, sharpening):
            if not self.before_thumbnail:
                return
            img = self.before_thumbnail
            alpha_channel = img.split()[-1] if img.mode == 'RGBA' else None
            self._update(0)
            img = self.apply_sharpening(img, sharpening)
            self._update(25)
            img_resized, new_size = self.resize_image(img, downscale_factor)
            self._update(50)
            img_rgb = self.convert_to_rgb(img_resized)
            self._update(75)
            palette = self.get_palette(img_rgb, colormap_path, num_colors, quant_mode)
            quantized_image = self.quantize_image_with_palette(img_rgb, palette, new_size)
            if alpha_channel:
                quantized_image.putalpha(alpha_channel.resize(new_size, RESAMPLE_FUNC))
            self._update(100)
            self.display_after_thumbnail(quantized_image)
            self._update(0)
        if self.thumbnail_process_id:
            self.root.after_cancel(self.thumbnail_process_id)
        self.thumbnail_process_id = self.root.after(self.debounce_delay, lambda: _process_thumbnail(colormap_path, num_colors, quant_mode, downscale_factor, sharpening))


    def process_full_image(self, image_path, output_path, colormap_path, num_colors, restore_size, quant_mode, downscale_factor, sharpening):
        if not os.path.isfile(image_path):
            return
        with Image.open(image_path) as img:
            self._update(0)
            original_size = img.size
            alpha_channel = img.split()[-1] if img.mode == 'RGBA' else None
            img = self.apply_sharpening(img, sharpening)
            img_resized, new_size = self.resize_image(img, downscale_factor)
            img_rgb = self.convert_to_rgb(img_resized)
            self._update(10)
            palette = self.get_palette(img_rgb, colormap_path, num_colors, quant_mode)
            self._update(20)
            quantized_image = self.quantize_image_with_palette(img_rgb, palette, new_size)
            if restore_size:
                quantized_image = quantized_image.resize(original_size, RESAMPLE_FUNC)
                self._update(90)
            if alpha_channel:
                quantized_image.putalpha(alpha_channel.resize(original_size if restore_size else new_size, RESAMPLE_FUNC))
            quantized_image.save(output_path)
            if self.save_colormap_var.get():
                self.save_palette(output_path, palette)
            self._update(100)
            self.handle_success(output_path)


# --------------------------------------
# Functions
# --------------------------------------


    def apply_sharpening(self, img, sharpening):
        if sharpening:
            sharpen_amount = sharpening
            img = img.filter(ImageFilter.UnsharpMask(radius=32.0, percent=sharpen_amount, threshold=0))
        return img


    def resize_image(self, img, downscale_factor):
        if downscale_factor in [0, 1, ""]:
            new_size = img.size
        else:
            downscale_factor = downscale_factor // 2
            new_size = (img.size[0] // downscale_factor, img.size[1] // downscale_factor)
        img_resized = img.resize(new_size, RESAMPLE_FUNC)
        return img_resized, new_size


    def convert_to_rgb(self, img):
        if img.mode != 'RGB':
            img_rgb = img.convert('RGB')
        else:
            img_rgb = img
        return img_rgb


    def get_palette(self, img_rgb, colormap_path, num_colors, quant_mode):
        selected_palette = self.color_palette_combobox.get()
        if selected_palette != "From Image":
            palette = np.array([list(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) for color in self.color_palettes[selected_palette]])
            num_colors = len(palette)
        else:
            if colormap_path:
                palette = self.get_color_palette(colormap_path, num_colors)
            else:
                palette = self.quantize_image(img_rgb, num_colors, quant_mode)
            num_colors = len(palette)
        return palette


    def quantize_image_with_palette(self, img_rgb, palette, new_size):
        quantized_pixels = self.find_nearest_color(img_rgb, palette, new_size)
        quantized_image = Image.fromarray(quantized_pixels.astype('uint8'))
        return quantized_image


    def find_nearest_color(self, img_resized, palette, new_size):
        pixels = np.array(img_resized).reshape(-1, 3)
        tree = KDTree(palette)
        if self.nearest_color_combobox.get() == "Normal":
            _, nearest_indices = tree.query(pixels)
            nearest_colors = palette[nearest_indices.flatten()]
            quantized_pixels = nearest_colors.reshape(new_size[1], new_size[0], 3)
        elif self.nearest_color_combobox.get() == "Blend":
            distances, nearest_indices = tree.query(pixels, k=min(2, len(palette)))
            nearest_colors = palette[nearest_indices]
            weights = 1 / (distances + 1e-5)
            weights /= np.sum(weights, axis=1, keepdims=True)
            blended_pixels = np.einsum('ijk,ij->ik', nearest_colors, weights)
            quantized_pixels = blended_pixels.reshape(new_size[1], new_size[0], 3).astype(np.uint8)
        return quantized_pixels


# --------------------------------------
# Misc
# --------------------------------------


    def save_palette(self, output_path, palette):
        palette_image_path = os.path.splitext(output_path)[0] + "_palette.png"
        palette_image = Image.new('RGB', (len(palette), 1))
        palette_image.putdata([tuple(color) for color in palette])
        palette_image = palette_image.resize((len(palette) * 1, 1), RESAMPLE_FUNC)
        palette_image.save(palette_image_path)


    def handle_success(self, output_path):
        if not self.batch_mode_var.get() and self.success_messages_enabled:
            self.process_image_button.config(text="Process Image")
            response = messagebox.askyesnocancel("Success", f"Image saved to:\n{output_path}\n\nOpen image?\n\n(Press Cancel to stop further popups)")
            if response is None:
                self.success_messages_enabled = False
            elif response:
                self.open_current_image(output_path)
        self._update(0)


#endregion
################################################################################################################################################
#region -   Image_Preview


    def display_before_thumbnail(self, image_path):
        with Image.open(image_path) as before_image:
            before_image.thumbnail((self.thumbnail_size, self.thumbnail_size), Image.LANCZOS)
            self.before_thumbnail = before_image
            photo = ImageTk.PhotoImage(self.before_thumbnail)
            canvas_width = self.before_image_preview_canvas.winfo_width()
            canvas_height = self.before_image_preview_canvas.winfo_height()
            x = (canvas_width - self.before_thumbnail.width) // 2
            y = (canvas_height - self.before_thumbnail.height) // 2
            self.before_image_preview_canvas.create_image(x, y, anchor=tk.NW, image=photo)
            self.before_image_preview_canvas.image = photo


    def display_after_thumbnail(self, image):
        aspect_ratio = image.width / image.height
        if image.width > image.height:
            new_width = self.thumbnail_size
            new_height = int(self.thumbnail_size / aspect_ratio)
        else:
            new_height = self.thumbnail_size
            new_width = int(self.thumbnail_size * aspect_ratio)
        after_thumbnail = image.resize((new_width, new_height), RESAMPLE_FUNC)
        photo = ImageTk.PhotoImage(after_thumbnail)
        canvas_width = self.after_image_preview_canvas.winfo_width()
        canvas_height = self.after_image_preview_canvas.winfo_height()
        x = (canvas_width - after_thumbnail.width) // 2
        y = (canvas_height - after_thumbnail.height) // 2
        self.after_image_preview_canvas.create_image(x, y, anchor=tk.NW, image=photo)
        self.after_image_preview_canvas.image = photo


    def clear_before_thumbnail(self):
        #self.before_thumbnail = None
        self.before_image_preview_canvas.image = None
        self.clear_after_thumbnail()


    def clear_after_thumbnail(self):
        self.after_image_preview_canvas.image = None


#endregion
################################################################################################################################################
#region -   Color_Palette


# --------------------------------------
# Create Palette
# --------------------------------------


    def get_color_palette(self, colormap_path, num_colors):
        quant_mode = self.quant_mode_combobox.get()
        downscale_factor = self.image_downscale_spinbox.get() or 1
        downscale_factor = round(float(downscale_factor))
        self.image_downscale_spinbox.delete(0, "end")
        self.image_downscale_spinbox.insert(0, downscale_factor)
        with Image.open(colormap_path) as cmap_img:
            if cmap_img.mode != 'RGB':
                cmap_img = cmap_img.convert('RGB')
            width, height = cmap_img.size
            if downscale_factor > 1:
                new_width = max(1, width // downscale_factor)
                new_height = max(1, height // downscale_factor)
                new_size = (new_width, new_height)
            else:
                new_size = (width, height)
            cmap_img = cmap_img.resize(new_size, RESAMPLE_FUNC)
        return self.quantize_image(cmap_img, num_colors, quant_mode)


    def quantize_image(self, img, num_colors, quant_mode):
        pixels = np.array(img).reshape(-1, 3)
        unique_pixels = np.unique(pixels, axis=0)
        num_colors = min(num_colors, unique_pixels.shape[0])
        if quant_mode == 'Kmeans':
            kmeans = KMeans(n_clusters=num_colors, max_iter=300, random_state=42)
            kmeans.fit(unique_pixels)
            palette = np.rint(kmeans.cluster_centers_).astype(int)
        elif quant_mode == 'Simple':
            img_quantized = img.quantize(colors=num_colors)
            palette = np.array(img_quantized.getpalette()).reshape(-1, 3)[:num_colors]
        elif quant_mode == 'Octree':
            num_colors = min(num_colors, 256)
            img_quantized = img.quantize(colors=num_colors, method=Image.FASTOCTREE)
            palette = np.array(img_quantized.getpalette()).reshape(-1, 3)[:num_colors]
        elif quant_mode == 'MaxCoverage':
            num_colors = min(num_colors, 256)
            img_quantized = img.quantize(colors=num_colors, method=Image.MAXCOVERAGE)
            palette = np.array(img_quantized.getpalette()).reshape(-1, 3)[:num_colors]
        elif quant_mode == 'Random':
            indices = np.random.choice(unique_pixels.shape[0], num_colors, replace=False)
            palette = unique_pixels[indices]
        palette = np.unique(palette, axis=0)
        palette = palette[np.argsort(np.sum(palette, axis=1))]
        return palette


# --------------------------------------
# Display Palette
# --------------------------------------


    def display_colormap_palette(self, event=None):
        canvas_width, canvas_height = self.thumbnail_size, self.thumbnail_size
        selected_palette = self.color_palette_combobox.get()
        if selected_palette != "From Image":
            self.quant_mode_combobox.config(state="disabled")
            self.num_colors_spinbox.config(state="disabled")
            palette = np.array([list(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) for color in self.color_palettes[selected_palette]])
            num_colors = len(palette)
            self.num_colors_label.config(text=f"Number of Colors: {num_colors}")
        else:
            if self.batch_mode_var.get():
                self.clear_palette()
                return
            self.quant_mode_combobox.config(state="readonly")
            self.num_colors_spinbox.config(state="normal")
            self.num_colors_label.config(text="Number of Colors:")
            colormap_path = self.colormap_path_entry.get() if self.colormap_path_entry.get() else self.image_path_entry.get()
            if not colormap_path and not os.path.isdir(colormap_path):
                self.clear_palette()
                return
            try:
                num_colors = int(self.num_colors_spinbox.get())
                num_colors = max(1, min(num_colors, 256))
                self.num_colors_spinbox.delete(0, "end")
                self.num_colors_spinbox.insert(0, num_colors)
            except ValueError:
                num_colors = 1
            if not os.path.isdir(colormap_path):
                palette = self.get_color_palette(colormap_path, num_colors)
            else:
                self.clear_palette()
                return
            self.clear_palette()
        palette = palette[np.argsort(np.sum(palette, axis=1))]
        self.setup_palette_preview_canvas(canvas_width, canvas_height)
        self.palette_preview_canvas.bind("<Button-3>", self.show_colorpalette_context_menu)
        TkToolTip.create(self.palette_preview_canvas,
                         "(Drop image here)\n"
                         "The color palette",
                         delay=1000, padx=5, pady=10)
        if os.path.isfile(self.image_path_entry.get()):
            self.process_settings(thumbnail=True)
        grid_size = int(np.ceil(np.sqrt(num_colors)))
        rect_width = canvas_width / grid_size
        rect_height = canvas_height / grid_size
        for i, color in enumerate(palette):
            hex_color = f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}'
            row = i // grid_size
            col = i % grid_size
            self.palette_preview_canvas.create_rectangle(col * rect_width, row * rect_height, (col + 1) * rect_width, (row + 1) * rect_height, fill=hex_color, outline=hex_color)


# --------------------------------------
# Create and Clear Palette
# --------------------------------------


    def setup_palette_preview_canvas(self, canvas_width=None, canvas_height=None):
        if not canvas_width:
            canvas_width = self.thumbnail_size
        if not canvas_height:
            canvas_height = self.thumbnail_size
        self.palette_preview_canvas = tk.Canvas(self.preview_frame, width=canvas_width, height=canvas_height)
        self.palette_preview_canvas.grid(row=0, column=4, sticky='nsew')
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)
        self.create_colorpalette_context_menu()
        self.setup_drag_and_drop()


    def clear_palette(self):
        self.palette_preview_canvas.destroy()
        self.setup_palette_preview_canvas()
        TkToolTip.create(self.palette_preview_canvas,
                         "(Drop image here)\n"
                         "The color palette",
                         delay=1000, padx=5, pady=10)


# --------------------------------------
# Save Palette
# --------------------------------------


    def save_palette_image(self):
        try:
            save_path = filedialog.asksaveasfilename(initialfile="palette.png", defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
            if not save_path:
                return
            selected_palette = self.color_palette_combobox.get()
            self._update(10)
            if selected_palette != "From Image":
                palette = np.array([list(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)) for color in self.color_palettes[selected_palette]])
            else:
                colormap_path = self.colormap_path_entry.get() if self.colormap_path_entry.get() else self.image_path_entry.get()
                if not colormap_path or not os.path.isfile(colormap_path):
                    messagebox.showerror("Error", "Invalid colormap path.")
                    return
                num_colors = int(self.num_colors_spinbox.get())
                palette = self.get_color_palette(colormap_path, num_colors)
            self._update(33)
            palette_image = Image.new('RGB', (len(palette), 1))
            palette_image.putdata([tuple(color) for color in palette])
            self._update(66)
            palette_image = palette_image.resize((len(palette) * 1, 1), RESAMPLE_FUNC)
            palette_image.save(save_path)
            self._update(100)
            if messagebox.askyesno("Success", "Palette image saved successfully!\n\nOpen output folder?"):
                self.open_directory(save_path)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self._update(0)


# --------------------------------------
# Load Palettes
# --------------------------------------


    def update_palette_list(self):
        additional_palettes = self.load_palettes_from_folder('Palettes', 'Palettes\#palettes.txt')
        self.color_palettes.update(additional_palettes)
        self.color_palettes = dict(sorted(self.color_palettes.items(), key=lambda item: (len(item[1]), item[0])))
        self.color_palette_combobox['values'] = list(self.color_palettes.keys())
        self._update(0)


    def load_palettes_from_folder(self, folder_path, palette_cache):
        def read_palette_cache(palette_cache):
            cache = {}
            if os.path.exists(palette_cache):
                try:
                    with open(palette_cache, 'r') as f:
                        for line in f:
                            palette_name, hex_colors = line.strip().split(': ')
                            cache[palette_name] = eval(hex_colors)
                except Exception as e:
                    messagebox.showerror("Error", f"Error reading palette cache:\n\n{e}")
            return cache

        def write_palette_cache(palette_cache, palettes):
            try:
                with open(palette_cache, 'w') as f:
                    sorted_palettes = dict(sorted(palettes.items(), key=lambda item: (len(item[1]), item[0])))
                    for palette_name, hex_colors in sorted_palettes.items():
                        f.write(f"{palette_name}: {hex_colors}\n")
            except Exception as e:
                messagebox.showerror("Error", f"Error writing palette cache:\n\n{e}")

        def process_palette_image(image_path):
            try:
                with Image.open(image_path) as image:
                    colors = image.getdata()
                    unique_colors = list(set(colors))
                    if len(unique_colors) > 256:
                        image = image.quantize(colors=256)
                        image = image.convert("RGB")
                        colors = image.getdata()
                        unique_colors = list(set(colors))
                    return ['#%02x%02x%02x' % color[:3] for color in unique_colors]
            except Exception as e:
                messagebox.showerror("Error", f"Error processing palette image:\n\n{e}")
                return []

        palettes = {}
        try:
            cache = read_palette_cache(palette_cache)
            filenames_in_folder = [os.path.splitext(f)[0] for f in os.listdir(folder_path) if f.endswith(".png")]
            cache = {k: v for k, v in cache.items() if k in filenames_in_folder}
            if not filenames_in_folder:
                palettes.clear()
                write_palette_cache(palette_cache, palettes)
                return palettes
            for index, filename in enumerate(filenames_in_folder):
                palette_name = os.path.splitext(filename)[0]
                if palette_name in cache:
                    palettes[palette_name] = cache[palette_name]
                else:
                    image_path = os.path.join(folder_path, f"{palette_name}.png")
                    palettes[palette_name] = process_palette_image(image_path)
                self._update((index + 1) * 100 // len(filenames_in_folder))
            write_palette_cache(palette_cache, palettes)
        except Exception as e:
            messagebox.showerror("Error", f"Error loading palettes from folder:\n\n{e}\n\nPlease make sure the 'Palettes' folder is in the app's parent directory.\n\nThis error can be ignored.")
        return palettes


#endregion
################################################################################################################################################
#region -   Misc


    def open_directory(self, directory=None):
        if not directory:
            directory = self.output_path_entry.get()
        try:
            if os.path.isfile(directory):
                directory = os.path.dirname(directory)
            elif not os.path.exists(directory) and os.path.isdir(os.path.dirname(directory)):
                directory = os.path.dirname(directory)
            if os.path.isdir(directory):
                os.startfile(directory)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while trying to open the directory: {e}")


    def open_current_image(self, filepath):
        try:
            os.startfile(filepath)
        except Exception: return


#endregion
################################################################################################################################################
#region -   Framework


    def set_appid(self):
        myappid = 'Pixel8.Nenotriple'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


    def set_icon(self):
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        elif __file__:
            application_path = os.path.dirname(__file__)
        self.icon_path = os.path.join(application_path, "icon.ico")
        self.root.iconbitmap(self.icon_path)


    def setup_window(self):
        window_width = 960
        window_height = 295
        self.root.title(f"{APP_VERSION} - Pixel8 - github.com/Nenotriple")
        self.root.minsize(window_width, window_height)
        self.root.resizable(True, False)
        position_right = self.root.winfo_screenwidth()//2 - window_width//2
        position_top = self.root.winfo_screenheight()//2 - window_height//2
        self.root.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")
        # Print window dimensions
        #self.root.bind("<Configure>", lambda event: print(f"\rWindow size (W,H): {event.width},{event.height}    ", end='') if event.widget == self.root else None, add="+")


    def on_closing(self):
        self.stop_processing = True
        if self.root:
            self.root.after(100, self.root.destroy)


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = Pixel8(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


#endregion
################################################################################################################################################
#region - Changelog


'''


[💾v1.01](https://github.com/Nenotriple/Pixel8/releases/tag/v1.01)

<details>
  <summary>Click here to view release notes for v1.01</summary>


  - New:
    - `Batch Mode`: Allows input/output entries to accept folder paths.
      - Processes all supported images in subfolders while maintaining folder structure.
    - Before and After preview images are now displayed. *(When not in Batch mode)*
      - The Before image also works as a drop target to set the input image path.
    - Right-click on the palette in the UI to quickly save the palette image with `Save As...`.
    - Additional palettes can be used by placing `.PNG` files in a `Palettes` folder in the app's parent directory.
        - Supports up to 256 colors per palette.
    - `Sharpen` Setting: Enhances image sharpness to improve pixel contrast and color.
      - Sharpen value range: From -100, to 100.
    - You can now choose between two color transfer modes: `Normal` and `Blend`.
      - `Normal` mode assigns each pixel to the nearest color in the palette. *(Previous behavior)*
      - `Blend` mode blends the two nearest colors based on their distance.
    - Added `Open` buttons to each input entry to quickly open the selected directory.


  - Fixed:
    - Fixed error when processing non-RGB format images.
    - Fixed issue where color palettes included colors not present in the input image.
    - Unsupported file types can no longer be drag-and-dropped into input fields.


  - Other changes:
    - Image processing is ~70% faster (Kmeans/Normal) due to improved pixel-color handling.
    - Setting `Image Downscale` to `0`, or `1`, now disables downscaling.
    - Palette images are now saved as 1x1 grids, expanding in width.
    - Palettes contain only unique colors, sorted by brightness.
      - Unfortunately, it's not easy to prevent very *similar* colors from being included.
    - Maximum number of colors changed from 999 to 256.
    - Supported image file types now include: `.jfif`, `.tiff`, `.tif`, and `.ico`.
    - All spinboxes can be adjusted with the mouse-wheel.
    - Tooltips now mostly appear when hovering the mouse over label text and not input widgets, reducing their annoyance.
    - Numerous small tweaks, fixes, and improvements in both logic and UI.
      - The app has been internally restructured and organized.


'''


#endregion
################################################################################################################################################
#region - Todo


'''


- Todo
  -


- Tofix
  -


  '''

#endregion
