# dnd_overland_map_generator
Generates a hand-drawn-style DnD map file of an overland map segment, with several options.

The hand-drawn effect is created with the use of a Delaunay Triangle grid, with random soft stippling.
The map generated generally has between 2 and 4 entry/exit points at the midpoint of each edge of the image.
The script will attempt to automatically create curved, slightly irregular paths between each entry/exit point.
When there is a straight path from one edge to the opposite edge, the path will be mostly straight,
with some slight randomness, to simulate a natural road.
To create a more "lived-in" look, you can select whether to draw wagon tracks on all the paths or not.
Caveat: Occasionally, the script will not find any paths (only one entry/exit point).
If it cannot build any paths, it will exit out of the operation, not generating any map image at all.

Options available at the GUI input:

Output Image dots-per-unit ("dpi", for example): Defaults to 300, but can be set to 150, 144, 72, etc.

Image width in units ("mm" or "inches", for example): Defaults to 5, but can be set to any number.
This is multiplied by the dots-per-unit value to get the total number of pixels wide of the final image.

Image height in unites ("mm" or "inches", for example): Defaults to 5, but can be set to any number.
This is multiplied by the dots-per-unit value to get the total number of pixels high of the final image.

Include Hexagon lines: Defaults to draw lines.
This draws multiple 2-inch wide hexagons across the map segment, to assist with scale and in-game movement.

Include Hexagon dots: Defaults to draw dots.
This draws multiple sets of black dots in hexagon patterns in the same pattern and scale as the Hexagon lines.

Include wagon tracks: Defaults to draw tracks.
This draws lines in the generated paths, which represent wagon tracks, to make the path look more used.

Image Folder: Select a folder to contain the resulting image file generated from this script.

Image Type/Extension: Defaults to "PNG".
You can select one of six image types: PNG, GIF, JPG, PCX, TIF, or BMP

Image File Basename (without extension): defaults to "generated_map_xxxx", where "xxxx" is four random lower-case letters.
You can change this to output a specific filename in the Image Folder selected.
