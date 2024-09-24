
<h1 align="center">
  <img src="https://github.com/user-attachments/assets/24299630-81ff-4a10-a40e-f31cf25a447e" alt="icon" width="50">
  Pixel8
</h1>

<p align="center">Pixelate an image using various methods and conditions.</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/20d3bbad-047b-4017-b511-4d7adef5758b" alt="cover">
</p>


![head_px_group](https://github.com/user-attachments/assets/f159ed1a-10f7-403d-877c-d79126b2718e)



# 📝 Usage

> [!NOTE]
>  - Supported image types: `.png` `.webp` `.jpg` `.jpeg` `.jpg_large` `.bmp` `.jfif` `.tiff` `.tif` `.ico`

This tool is designed to be used with AI-generated images in the pixel art style. It's common for these images to be generated with *mushed* colors and/or sloppy pixel shaping. Processing those images with this tool can enhance the pixel art style, and improve image quality.


---

![Before__After_400](https://github.com/user-attachments/assets/58413593-61ce-424b-989b-257c862fd8c3)


# 💡 Tips and Features


<details>
  <summary>Drag-and-Drop files into input fields...</summary>
  
![Drag images to input fields](https://github.com/user-attachments/assets/14864cd6-f73e-4888-b779-c0460ad133ff)

</details>

<details>
  <summary>Use another image as the color palette...</summary>
  
![Use another image as the color palette](https://github.com/user-attachments/assets/7f55da6e-3620-44a1-88d9-850aa942ae93)

</details>

<details>
  <summary>Pick from a list of pre-defined color palettes...</summary>
  
![Pre-defined custom palettes](https://github.com/user-attachments/assets/40bfce46-d387-4ddc-b23e-7b78b709b347)

</details>

<details>
  <summary>Normal and Blend color modes...</summary>
  
![Normal and Blend color modes](https://github.com/user-attachments/assets/adf1504d-def0-400d-bde8-a6be065d9ca5)

</details>


# 🚩 Requirements

> [!TIP]
> You don't need to worry about any requirements with the Windows [💾portable/executable](https://github.com/Nenotriple/Pixel8/releases/tag/v1.00) version.

<details>
  <summary>Python requirements...</summary>
  
**Python 3.10+**

You will need `Pillow`, `NumPy`, `TkinterDnD2`, `scikit-learn`, and `matplotlib`:
- `pip install pillow numpy tkinterdnd2 scikit-learn matplotlib`

Or use the included `requirements.txt` when creating your virtual enviroment.

</details>


# 📜 Version History

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
    - Fixed error when processing non-RGB format images. Alpha channels are now preserved.
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
     

</details>
