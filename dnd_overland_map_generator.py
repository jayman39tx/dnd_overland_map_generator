#! /usr/share/bin/ python3

"""
generate maps for gaming
"""

from math import cos, pi, radians, sin, sqrt
from os import getcwd, path
from string import ascii_lowercase
import time

# from pprint import pprint
from secrets import choice, randbelow
import numpy as np
from PIL import Image, ImageDraw
import PySimpleGUI as sg
from scipy.spatial import Delaunay # , delaunay_plot_2d

start_time = time.time()

active_file_folder = getcwd()

random_filename = 'generated_map_' + ''.join([choice(ascii_lowercase) for n in range(4)])
# print(random_filename)

input_rows = [ [sg.Text('Map Generator 2019')],
           [sg.Text('Image dots-per-unit (e.g. dpmm): ') \
                   , sg.Input(default_text = '300' \
                   , tooltip = 'Enter only a number here.', focus = True)],
           [sg.Text('Image width in distance units (e.g. mm): ') \
                   , sg.Input(default_text = '5' \
                   , tooltip = 'Enter only a number here.')],
           [sg.Text('Image height in distance units (e.g. mm): ') \
                   , sg.Input(default_text = '5' \
                   , tooltip = 'Enter only a number here.')],
           [sg.Text('Include Hexagon lines?')],
           [sg.Radio('Draw Lines', 'Radio_button_group_1' \
                       , default=True, tooltip = 'Draw hexagons for scale.'),
               sg.Radio('Skip Lines', 'Radio_button_group_1' \
                       , tooltip = 'Do not draw hexagons for scale.')],
           [sg.Text('Include Hexagon dots')],
           [sg.Radio('Draw Dots', 'Radio_button_group_2' \
                       , default=True, tooltip = 'Draw dots in a hexagon pattern for scale.'),
               sg.Radio('Skip Dots', 'Radio_button_group_2' \
                       , tooltip = 'Do not draw dots for scale.')],
           [sg.Text('Include wagon tracks')],
           [sg.Radio('Draw Tracks', 'Radio_button_group_3' \
                       , default=True, tooltip = 'Draw wagon tracks on paths.'),
               sg.Radio('Skip Tracks', 'Radio_button_group_3' \
                       , tooltip = 'Do not draw tracks.')],
           [sg.Text('Image Folder: ') \
                   , sg.InputText(default_text = active_file_folder \
                   , tooltip = 'Enter the filepath here.') \
                   , sg.FolderBrowse()],
           [sg.Text('Image Type/Extension: ') \
                   , sg.Radio('PNG', 'Radio_button_group_4' \
                       , default=True, tooltip = 'Optimized PNG format'),
                   sg.Radio('GIF', 'Radio_button_group_4' \
                       , tooltip = 'Classic Static GIF format'),
                   sg.Radio('JPG', 'Radio_button_group_4' \
                       , tooltip = 'Classic JPEG format'),
                   sg.Radio('PCX', 'Radio_button_group_4' \
                       , tooltip = 'Classic PCX format'),
                   sg.Radio('TIF', 'Radio_button_group_4' \
                       , tooltip = 'Classic TIFF format'),
                   sg.Radio('BMP', 'Radio_button_group_4' \
                       , tooltip = 'Classic Windows Bitmap (BMP) format')],
           [sg.Text('Image File Basename (without extension): ') \
                   , sg.Input(default_text = random_filename \
                   , tooltip = 'Enter a file basename here without the file extension.')],
           [sg.OK(), sg.Cancel()]
           ]

input_event, (*input_array,) = sg.Window('Map Generator 2019').Layout(input_rows).Read()

# sg.Popup(input_event, *input_array)
# print(input_event, input_array)

if not input_event:
    print(f'User exited the input window. Exiting.')
    exit(0)

if input_event == 'Cancel':
    print(f'User selected "{input_event}". Exiting.')
    exit(0)

if input_array[0].isdigit():
    image_dpi = int(input_array[0])
else:
    image_dpi = 0
    print(f'Invalid dots-per-unit value ({input_array[0]}) not a valid integer. Exiting.')
    exit(1)

try:
    image_in = [float(input_array[1]), float(input_array[2])]
except:
    print(f'Invalid image width ({input_array[1]}) or height ({input_array[2]}). Exiting.')
    exit(1)

hexagons_bool = input_array[3]
dots_bool = input_array[5]
wagon_track_bool = input_array[7]

if input_array[10]:
    file_type_ext = 'png'
if input_array[11]:
    file_type_ext = 'gif'
if input_array[12]:
    file_type_ext = 'jpg'
if input_array[13]:
    file_type_ext = 'pcx'
if input_array[14]:
    file_type_ext = 'tif'
if input_array[15]:
    file_type_ext = 'bmp'
else:
    file_type_ext = 'png'

full_file_path = path.join(path.abspath(input_array[9]),f'{input_array[16]}.{file_type_ext}')

# print('draw hexagons: ', hexagons_bool, '\ndraw dots: ', dots_bool, '\ndraw wagon tracks: ', wagon_track_bool)

# print('full file path: ', full_file_path)

image_max_width = int(image_in[0] * image_dpi)
image_max_height = int(image_in[1] * image_dpi)
image_min_corner = (0, 0)
image_max_corner = (image_max_width-1, image_max_height-1)
image_mid_point = (image_max_width//2-1, image_max_height//2-1)
side_length = min(image_max_width, image_max_height)
square_size = side_length // 8
half_length = side_length // 2
half_square = square_size // 2
hex_radius_ratio = 1.155

road_color = 223
ditch_color = 191

wagon_track_color = 0
wagon_track_alpha = 15

start_coord = [image_max_width//2 - 1, 0]
path_coords = [start_coord, [start_coord[0], image_max_width // 8 - 1]]
hypot_value = image_max_width//16
hypot_squared = hypot_value**2

print('Image will contain this many pixels: ', image_max_width * image_max_height)

def angled_coords(source_coords, source_angle_degrees,
        destination_coords, destination_angle_degrees,
        segment_length=None, angle_coords=None):
    """
    calculate new list of coordinate pairs in an arc around a given center point

    :param source_coords: a coordinate pair ([x, y]) that represents an endpoint of the line
    :param source_angle_degrees: the direction in degrees of the endpoint 
    :param destination_coords: a coordinate pair ([x, y]) that represents an endpoint of the line
    :param destination_angle_degrees: the direction in degrees of the endpoint 
    :param segment_length: distance value that represents the distance between points on the line
    :param angle_coords: a coordinate pair that represents the center of the arc line
    :returns: list of coordinate pairs
    :raises TypeError: none
    """
    angled_coord_list = []
    if source_coords[0] == destination_coords[0]:
        if segment_length is None or segment_length < 1:
            segment_length = abs(source_coords[1] - destination_coords[1]) // 14.14
        for y_coord in range(source_coords[1] + segment_length, destination_coords[1], segment_length//2):
            angled_coord_list.append([source_coords[0], y_coord])
    elif source_coords[1] == destination_coords[1]:
        if segment_length is None or segment_length < 1:
            segment_length = abs(source_coords[0] - destination_coords[0]) // 14.14
        for x_coord in range(source_coords[0] + segment_length, destination_coords[0], segment_length//2):
            angled_coord_list.append([x_coord, source_coords[1]])
    else: # true angle
        # print('90 degree angle to one side or the other.')
        angle_radius = abs((source_coords[0] - destination_coords[0]))
        if angle_radius == 0:
            angle_radius = abs((source_coords[1] - destination_coords[1]))
        # angle_radius=95
        angle_radius_sqrt = sqrt(angle_radius)
        angle_radius_sqrt_half = angle_radius_sqrt // 3
        arc_segment_degrees = int(13 - angle_radius_sqrt_half)
        if arc_segment_degrees < 1:
            arc_segment_degrees = 1
        # print('90 degree turn angle data: ', angle_radius, angle_radius_sqrt, angle_radius_sqrt_half, arc_segment_degrees)
        if segment_length is None or segment_length < 1:
            segment_length = abs(source_coords[0] - destination_coords[0]) // 10
        # print('source angle degrees: ', source_angle_degrees, ", destination angle degrees: ", destination_angle_degrees)
        if source_angle_degrees > destination_angle_degrees:
            # print('angles: ', source_angle_degrees, destination_angle_degrees, arc_segment_degrees)
            # print('range of angles: ', list(range(source_angle_degrees - arc_segment_degrees, destination_angle_degrees, -1 * arc_segment_degrees)))
            for arc_angle in range(source_angle_degrees - arc_segment_degrees,
                    destination_angle_degrees,
                    -1 * arc_segment_degrees):
                new_arc_coords = coords_from_vector(angle_coords,
                        angle_radius, arc_angle)
                # print("new arc coords: ", new_arc_coords)
                angled_coord_list.append(new_arc_coords)
        else:
            # print('angles: ', source_angle_degrees,
            #         destination_angle_degrees,
            #         arc_segment_degrees)
            # print('range of angles: ', list(range(source_angle_degrees - arc_segment_degrees,
            #     destination_angle_degrees,
            #     -1 * arc_segment_degrees)))
            for arc_angle in range(source_angle_degrees + arc_segment_degrees, destination_angle_degrees, arc_segment_degrees):
                # print('vector data: ', angle_coords, angle_radius, arc_angle)
                new_arc_coords = coords_from_vector(angle_coords, angle_radius, arc_angle)
                # print("new arc coords: ", new_arc_coords)
                angled_coord_list.append(new_arc_coords)
    # print(angled_coord_list)
    return angled_coord_list

def coords_from_vector(source_coords, vector_length, direction_degrees):
    """
    calculate new coordinate pair based on vector offset from given coordinates

    :param source_coords: a coordinate pair ([x, y]) that represents the origin
    :param vector_length: distance value that represents the magnitude of a vector
    :param direction_degrees: angle in degrees that represents the direction of a vector
    :returns: new coordinate pair
    :raises TypeError: none
    """
    direction_radians = pi/2 - radians(direction_degrees)
    destination_x = source_coords[0] + int(vector_length * cos(direction_radians))
    destination_y = source_coords[1] - int(vector_length * sin(direction_radians))
    return([destination_x, destination_y])

def copy_polygon(polygon_coords=None, move_coords=None, limit_x=None, limit_y=None):
    """
    Generate coordinate pairs in a list by copying a polygon list of coordinates by a given offset

    :param polygon_coords: a list of coordinate pairs
    :param move_coords: a coordinate pair that holds offset values for the x and y directions
    :param limit_x: a value that represents the maximum x value
    :param limit_y: a value that represents the maximum y value
    :returns: Updated coordinate pair list or False
    :raises TypeError: none
    """
    if polygon_coords and move_coords:
        # print("Initial first point: ", polygon_coords[0], end=" ")
        new_polygon_coords = []
        for polygon_coord_pair in polygon_coords:
            new_x = polygon_coord_pair[0] + move_coords[0]
            new_y = polygon_coord_pair[1] + move_coords[1]

            if new_x < 0:
                new_x = 0
            if limit_x is not None and new_x > limit_x:
                new_x = limit_x

            if new_y < 0:
                new_y = 0
            if limit_y is not None and new_y > limit_y:
                new_y = limit_y

            new_polygon_coords.append([new_x, new_y])
        # print("Original first point: ", polygon_coords[0], end=" ")
        # print("Move Vector: ", move_coords, end=" ")
        # print("Updated first point: ", new_polygon_coords[0])
        # print(new_polygon_coords)
        return new_polygon_coords
    else:
        return False

def draw_dot(image=None, coordinates=None,
        radius=None, color=None):
    """
    Generate a dot on a given image canvas at the given coordinates

    :param image: Pillow/PIL Image Canvas
    :param coordinates: coordinate pair that will be the center of the dot
    :param radius: radius size of the dot
    :param color: color of the dot 
    :returns: image ellipse return or False
    :raises TypeError: none
    """
    if image \
        and coordinates \
        and radius \
        and color:
        drawn_dot = image.ellipse([coordinates[0]-radius,
            coordinates[1]-radius, coordinates[0]+radius,
            coordinates[1]+radius],
            fill=color, outline=color)
        return drawn_dot
    else:
        return False

def draw_hexagon(image=None, coordinates=None,
        radius=None, thickness=None,
        color_hex=None,
        radius_dot=None, color_dot=None,
        polygon_bool=None, draw_dots_bool=None):
    """
    Generate a regular hexagon on a given image canvas with dots along the edge

    :param image: Pillow/PIL Image Canvas
    :param coordinates: coordinate pair that will be the center of the polygon
    :param radius: the distance from the center to the corner of the polygon
    :param thickness: the thickness of the lines of the edge of the polygon
    :param color_hex: the color of the lines of the polygon
    :param radius_dot: the size of the dots on the perimeter of the polygon
    :param color_dot: the color of the dots on the perimeter of the polygon
    :returns: list of coordinate pairs
    :raises TypeError: none
    """
    if image and coordinates and radius and thickness and color_hex and polygon_bool:
        angle_list = draw_regular_polygon(image, coordinates, 6, radius, thickness, color_hex)
    else:
        angle_list = [0, 60, 120, 180, 240, 300]

    if radius_dot and color_dot and draw_dots_bool:
        dot_coordinate_list = []
        for angle_degrees in angle_list:
            dot_coordinate_list.append(point_pos(coordinates, radius-(thickness//2), angle_degrees))

        dot_coordinate_list_2 = midpoint_list(dot_coordinate_list)
        dot_coordinate_list_3 = midpoint_list(dot_coordinate_list_2)
        # print(dot_coordinate_list_3)

        for dot_coordinates in dot_coordinate_list_3:
            draw_dot(image, dot_coordinates, radius_dot, color_dot)
        return dot_coordinate_list_3
    else:
        return False

def draw_regular_polygon(image=None, coordinates=None, sides=None, radius=None, thickness=None, color=None):
    """
    Generate a regular polygon on a given image canvas

    :param image: Pillow/PIL Image Canvas
    :param coordinates: coordinate pair that will be the center of the polygon
    :param sides: the number of sides of the polygon
    :param radius: the distance from the center to the corner of the polygon
    :param thickness: the thickness of the lines of the edge of the polygon
    :param color: the color of the lines of the polygon
    :returns: list of coordinate pairs or False
    :raises TypeError: none
    """
    # print("draw_regular_polygon: coordinates: ", coordinates, "\nsides: ", sides, "\nradius: ", radius, "\nthickness: ", thickness, "\ncolor: ", color)
    if image and coordinates \
            and sides and radius and thickness \
            and color:
        angle_per_side = 360.0 / sides
        angle_degrees_list = []
        outer_coordinate_list = []
        inner_coordinate_list = []

        for side in range(sides):
            current_angle = angle_per_side * side
            angle_degrees_list.append(current_angle)
            outer_coordinate_list.append(point_pos(coordinates, radius, current_angle))
            inner_coordinate_list.append(point_pos(coordinates, radius-thickness, current_angle))
        # print(outer_coordinate_list, inner_coordinate_list, angle_degrees_list)
        polygon_points = outer_coordinate_list[:]
        polygon_points.append(outer_coordinate_list[0])
        polygon_points.extend(inner_coordinate_list)
        polygon_points.append(inner_coordinate_list[0])

        # print(polygon_points)

        image.polygon(polygon_points, color)
        return angle_degrees_list
    else:
        return False

def generate_bounding_box_int(center_point_coords=None,
        box_radius=None, length_x=None, length_y=None):
    """
    Generate a pair of coordinate pairs representing a box of a given size

    :param center_point_coords: coordinate pair for the box center
    :param box_radius: distance from ceenter coordinate to the center of the edge
    :param length_x: maximum horizontal size of grid
    :param length_y: maximum vertical size of grid
    :returns: two-element list of coordinate pairs or False
    :raises TypeError: none
    """
    if center_point_coords \
            and box_radius \
            and length_x \
            and length_y:
        if validate_coordinate_int_in_range(center_point_coords, length_x, length_y):
            bounding_box = [[center_point_coords[0] - box_radius, center_point_coords[1] - box_radius], [center_point_coords[0] + box_radius, center_point_coords[1] + box_radius]]
            if bounding_box[0][0] < 0:
                bounding_box[0][0] = 0
            if bounding_box[0][1] < 0:
                bounding_box[0][1] = 0
            if bounding_box[1][0] >= length_x:
                bounding_box[1][0] = length_x-1
            if bounding_box[1][1] >= length_y:
                bounding_box[1][1] = length_y-1
            return bounding_box
        else:
            return False
    else:
        return False

def generate_box_points_int(length_x=None, length_y=None):
    """
    Generate a list of coordinate pairs around the perimeter of a grid of given size

    :param length_x: horizontal size of grid
    :param length_y: vertical size of grid
    :returns: list of coordinate pairs
    :raises TypeError: none
    """
    if length_x is not None and length_y is not None:
        box_points = [[0, 0], [length_x-1, 0], [0, length_y-1], [length_x-1, length_y-1], [length_x//8 * 3 - 1, 0], [0, length_y//8 * 3 - 1], [length_x//8 * 3 - 1, length_y - 1], [length_x - 1, length_y//8 * 3 - 1], [length_x//8 * 5 - 1, 0], [0, length_y//8 * 5 - 1], [length_x//8 * 5 - 1, length_y - 1], [length_x - 1, length_y//8 * 5 - 1]]
        # print(box_points)
        return box_points
    else:
        return False

def generate_point_list_in_box(length_x=None, length_y=None):
    """
    Generate a list of randomly-located coordinate pairs within a given grid

    :param length_x: horizontal size of grid
    :param length_y: vertical size of grid
    :returns: list of coordinate pairs
    :raises TypeError: none
    """
    if length_x and length_y:
        min_side_length = min(length_x, length_y)
        bbox_radius = min_side_length // 64
        # print("Point-Generation Bounding box radius: ", bbox_radius)
        bbox_r2 = bbox_radius ** 2
        start_rand_list = generate_box_points_int(length_x, length_y)

        while len(start_rand_list) < min_side_length:
            temp_point = generate_rand_point_int(length_x, length_y)
            bounding_box = generate_bounding_box_int(temp_point, bbox_radius, length_x, length_y)

            # print(temp_point, bounding_box)

            if start_rand_list:
                hypot_list = []
                for coord_pairs in start_rand_list:
                    if coord_pairs[0] in range(bounding_box[0][0],bounding_box[1][0] + 1) and coord_pairs[1] in range(bounding_box[0][1],bounding_box[1][1] + 1):
                        x_delta = coord_pairs[0] - temp_point[0]
                        x_squared = x_delta**2
                        y_delta = coord_pairs[1] - temp_point[1]
                        y_squared = y_delta**2
                        hypot_list.append((x_squared + y_squared) > bbox_r2)
                # print("hypot_list: ", hypot_list)
                if all(hypot_list):
                    start_rand_list.append(temp_point)
                    # print(temp_point, bounding_box)
            else:
                start_rand_list.append(temp_point)
                # print(len(start_rand_list))
        return start_rand_list
    else:
        return False

def generate_polygon_from_horizontal_line(line_coords=None, thickness=None):
    """
    Generate a list of coordinate pairs that represent a polygon of given thickness around a line

    :param line_coords: list of coordinate pairs that represent a horizontal line.
    :param thickness: overall thickness of the resulting polygon.
    :returns: list of coordinate pairs that make up the resulting polygon
    :raises TypeError: none
    """
    if line_coords is not None and thickness is not None:
        # print(f"line_coords in generate_polygon_from_horizontal_line", line_coords)
        polygon_coords = []
        half_thickness = thickness // 2
        line_coords.sort(key=lambda x: x[0])
        rev_coords = line_coords[::-1]
        # print("reverse coordinates: ", rev_coords)
        for line_coord_pair in rev_coords:
            top_side = line_coord_pair[1]-half_thickness
            if top_side < 0:
                top_side = 0
            polygon_coords.append([line_coord_pair[0], top_side])
        for line_coord_pair in line_coords:
            bottom_side = line_coord_pair[1]+half_thickness
            polygon_coords.append([line_coord_pair[0], bottom_side])
        # print(polygon_coords)
        return polygon_coords
    else:
        return False

def generate_polygon_from_vertical_line(line_coords=None, thickness=None):
    """
    Generate a list of coordinate pairs that represent a polygon of given thickness around a line

    :param line_coords: list of coordinate pairs that represent a vertical line.
    :param thickness: overall thickness of the resulting polygon.
    :returns: list of coordinate pairs that make up the resulting polygon
    :raises TypeError: none
    """
    if line_coords and thickness:
        polygon_coords = []
        half_thickness = thickness // 2
        line_coords.sort(key=lambda x: x[1])
        rev_coords = line_coords[::-1]
        polygon_coords.append([line_coords[0][0]+half_thickness,line_coords[0][1]])
        for line_coord_pair in line_coords:
            left_side = line_coord_pair[0]-half_thickness
            if left_side < 0:
                left_side = 0
            polygon_coords.append([left_side,line_coord_pair[1]])
        for line_coord_pair in rev_coords[:-1]:
            right_side = line_coord_pair[0]+half_thickness
            polygon_coords.append([right_side, line_coord_pair[1]])
        # print(polygon_coords)
        return polygon_coords
    else:
        return False

def generate_rand_point_int(length_x=None, length_y=None):
    """
    Get a random coordinate pair for a coordinate anywhere in the rectangular grid

    :param length_x: horizontal size of field
    :param length_y: vertical size of field
    :returns: coordinate pair that falls within a rectangle with the given dimensions
    :raises TypeError: none
    """
    if length_x is not None and length_y is not None:
        point_coords = [randbelow(length_x), randbelow(length_y)]
        return point_coords
    else:
        return False

def get_all_coords_in_image(length_x, length_y):
    """
    Get a list of all possible coordinates, based on two numbers representing a rectangular grid

    :param length_x: horizontal size of field
    :param length_y: vertical size of field
    :returns: list of all coordinate pairs in a field of size length_x x length_y
    :raises TypeError: none
    """
    if length_x and length_y:
        new_coord_list = []
        for spot_y in range(length_y):
            for spot_x in range(length_x):
                new_coord_list.append((spot_x, spot_y))
        # print(new_coord_list)
        return new_coord_list
    else:
        return False

def jitter_point(center_point_coords=None, jitter_x=None, jitter_y=None):
    """
    Calculate new coordinate pair from a coordinate pair and jitter values

    :param center_point_coords: coordinate pair
    :param jitter_x: value that a point can be moved left or right
    :param jitter_y: value that a point can be moved up or down
    :returns: coordinate pair
    :raises TypeError: none
    """
    if center_point_coords and validate_coordinate_pair_int(center_point_coords):
        new_point_coords=center_point_coords[:]
        if jitter_x is not None:
            new_point_coords[0] = int(new_point_coords[0] + choice(range(-1*jitter_x, jitter_x)))
        if jitter_y is not None:
            new_point_coords[1] = int(new_point_coords[1] + choice(range(-1*jitter_y,jitter_y)))
        return new_point_coords
    else:
        return False

def jitter_points_in_list(point_list=None, jitter_x=None, jitter_y=None, first_point_static=True, last_point_static=True):
    """
    Calculate new list of coordinate pairs based on an original list of coordinate pairs.

    :param point_list: a list of coordinate pairs
    :param jitter_x: how far to jitter points left or right
    :param jitter_y: how far to jitter points up or down
    :param first_point_static: Whether to leave the first point in the list un-moved
    :param last_point_static: Whether to leave the last point in the list un-moved
    :returns: Updated coordinate pair list
    :raises TypeError: none
    """
    # print('Attempting to jitter points: ', validate_coordinate_pair_list(point_list), point_list)
    if point_list and jitter_x and jitter_y and validate_coordinate_pair_list(point_list):
        if first_point_static is True:
            first_point = point_list[0]
        else:
            first_point = jitter_point(point_list[0], jitter_x, jitter_y)
        if last_point_static is True:
            last_point = point_list[-1]
        else:
            last_point = jitter_point(point_list[-1], jitter_x, jitter_y)
        new_point_list = [first_point]
        for old_point in point_list[1:-1]:
            new_point = jitter_point(old_point, jitter_x, jitter_y)
            new_point_list.append(new_point)
        new_point_list.append(last_point)
        return new_point_list
    else:
        return False

def midpoint(point_1=None, point_2=None):
    """
    Calculate a new coordinate pair between two points

    :param point_1: coordinate pair
    :param point_2: coordinate pair
    :returns: coordinate pair midway between the parameter points or False
    :raises TypeError: none
    """
    if point_1 and point_2:
        # print('midpoint points: ', point_1, point_2, point_1[0], point_2[0])
        return (point_1[0]+point_2[0])/2, (point_1[1]+point_2[1])/2
    else:
        return False

def midpoint_list(original_list=None):
    """
    Build new list of points from a list of points

    :param original_list: a list of coordinate pairs
    :returns: Updated coordinate pair list or False
    :raises TypeError: none
    """
    if original_list is not None:
        pair_list = list(zip(original_list[:-1], original_list[1:]))
        pair_list.append((original_list[-1],original_list[0]))
        # print('midpoint_list input list pairs: ', pair_list)

        midpoint_new_list = []
        for point_0, point_1 in pair_list:
            midpoint_new_list.append(midpoint(point_0, point_1))

        new_list_pairs = list(zip(original_list, midpoint_new_list))

        new_list = []
        for new_pair_1, new_pair_2 in new_list_pairs:
            new_list.append(new_pair_1)
            new_list.append(new_pair_2)
        # print('midpoint_list new list points: ', new_list)
        return new_list
    else:
        return False

def move_polygon(polygon_coords=None, move_coords=None, limit_x=None, limit_y=None):
    """
    update coordinate pairs in a list by the specified coordinate pair that represents distance

    :param polygon_coords: a list of coordinate pairs
    :param move_coords: a coordinate pair that holds offset values for the x and y directions
    :param limit_x: a value that represents the maximum x value
    :param limit_y: a value that represents the maximum y value
    :returns: Updated coordinate pair list or False
    :raises TypeError: none
    """
    if polygon_coords and move_coords:
        new_polygon_coords = []
        for polygon_coord_pair in polygon_coords:
            polygon_coord_pair[0] += move_coords[0]
            polygon_coord_pair[1] += move_coords[1]

            if polygon_coord_pair[0] < 0:
                polygon_coord_pair[0] = 0
            if limit_x is not None and polygon_coord_pair[0] > limit_x:
                polygon_coord_pair[0] = limit_x

            if polygon_coord_pair[1] < 0:
                polygon_coord_pair[1] = 0
            if limit_y is not None and polygon_coord_pair[1] > limit_y:
                polygon_coord_pair[1] = limit_y

            new_polygon_coords.append(polygon_coord_pair)
        return new_polygon_coords
    else:
        return False

def point_pos(coordinates=None, distance=None, degrees=None):
    """
    calculate new coordinate pair based on argument values

    :param coordinates: a coordinate pair ([x, y]) that represents the origin
    :param distance: distance value that represents the magnitude of a vector
    :param degrees: angle in degrees that represents the direction of a vector
    :returns: new coordinate pair or False
    :raises TypeError: none
    """
    if coordinates and distance and (degrees or degrees == 0):
        theta_rad = pi/2 - radians(degrees)
        return coordinates[0] - distance*cos(theta_rad), coordinates[1] - distance*sin(theta_rad)
    else:
        return False

def stipple_pixel(pixel_point=None):
    """
    change greyscale pixel value randomly

    :param pixel_point: a greyscale value from 0 to 255
    :returns: Updated Pixel value or False
    :raises TypeError: none
    """
    max_value = 255
    if pixel_point:
        # print(pixel_point, end=' ')
        random_change = choice(range(-44,46))
        # print(random_change, end=' ')
        if random_change == 4 and pixel_point + random_change * 8 > max_value:
            pixel_point = max_value
        elif random_change == -4 and pixel_point + random_change * 8 < 0:
            pixel_point = 0
        else:
            if random_change == -4:
                pixel_point -= 32
            elif random_change > 40:
                pixel_point += 32
            # pixel_point += random_change
        # print(pixel_point)
        return(pixel_point)
    else:
        return(False)

def validate_coordinate_pair_int(center_point_coords=None):
    """
    Verify that the coordinate pair is a two-element list,
    with each element in the coordinate pair being an int.

    :param center_point_coords: a coordinate pair ([x, y])
    :returns: True or False
    :raises TypeError: if the param is not a list,
    or if the individual elements are not ints.
    """
    if center_point_coords:
        if isinstance(center_point_coords, list) and len(center_point_coords) == 2:
            return isinstance(center_point_coords[0],int) and isinstance(center_point_coords[1],int)
        else:
            return False
    else:
        return False

def validate_coordinate_pair_list(coordinate_list=None):
    """
    Verify that each coordinate pair in a list is a two-element list,
    with each element in the coordinate pair being an int.

    :param coordinate_list: the list of coordinate pairs ([[x, y], [x, y]])
    :returns: True or False
    :raises keyError: none
    """
    if coordinate_list:
        return(all(map(validate_coordinate_pair_int, coordinate_list)))
    else:
        return False

def validate_coordinate_int_in_range(center_point_coords=None, length_x=None, length_y=None):
    """
    Verify that the coordinate pair falls within the range of (0, length_x) and (0, length_y)

    :param center_point_coords: the coordinate pair ([x, y])
    :param length_x: the size of the horizontal coordinate space
    :param length_y: the size of the vertical coordinate space
    :returns: True or False
    :raises keyError: none
    """
    if length_x is not None and length_y is not None:
        if validate_coordinate_pair_int(center_point_coords):
            return center_point_coords[0] in range(length_x) and center_point_coords[1] in range(length_y)
        else:
            return False
    else:
        return False

new_time = time.time()
time_diff = new_time - start_time
print(f"initialization: {time_diff} seconds. Generating array of random points. ")

rand_array = np.array(generate_point_list_in_box(image_max_width, image_max_height))

old_time = new_time
new_time = time.time()
time_diff = new_time - old_time
print(f"generated point list: {time_diff} seconds. Generating Delaunay triangle array. ")

array_triangles = Delaunay(rand_array)

old_time = new_time
new_time = time.time()
time_diff = new_time - old_time
print(f"generated triangle array: {time_diff} seconds. Generating image arrays. ")

image_array = np.full(shape=[1, image_max_width, image_max_height, 1], fill_value=159, dtype=np.uint8)
image_array_2 = np.full(shape=[1, image_max_width, image_max_height, 1], fill_value=191, dtype=np.uint8)

old_time = new_time
new_time = time.time()
time_diff = new_time - old_time
print(f"array initialization: {time_diff} seconds")

image_object = Image.fromarray(image_array[0, :, :, 0], mode="L")
triangle_object = Image.fromarray(image_array_2[0, :, :, 0], mode="L")

old_time = new_time
new_time = time.time()
time_diff = new_time - old_time
print(f"images built from arrays: {time_diff} seconds")

other_edge_attempts = randbelow(6)

edge_coords = []
road_coords = []

# print(other_edge_attempts)

if other_edge_attempts > 0:
    for attempt in range(other_edge_attempts):
        new_edge_coord = 0
        edge_number = randbelow(5)
        if edge_number == 1:
            new_edge_coord = [0, image_max_height//2 - 1]
        elif edge_number == 2:
            new_edge_coord = [image_max_width//2 - 1,image_max_height - 1]
        elif edge_number == 3:
            new_edge_coord = [image_max_width - 1,image_max_height//2 - 1]
        # print(new_edge_coord, edge_coords)
        if new_edge_coord and new_edge_coord not in edge_coords:
            edge_coords.append(new_edge_coord)
            # print(new_edge_coord, edge_coords)

# pprint(edge_coords)

for edge_coord in edge_coords:
    # print('Pre-update road coordinates:')
    # pprint(road_coords)
    adjacent_coords = []
    updated_path_coords = []

    if edge_coord[0] < image_max_width//2 - 1:
        adjacent_coords.append(square_size - 1)
    elif edge_coord[0] in range(image_max_width//2, image_max_width - square_size):
        adjacent_coords.append(image_max_width - square_size - 1)
    else:
        adjacent_coords.append(edge_coord[0])
    if edge_coord[1] < image_max_width//2 - 1:
        adjacent_coords.append(square_size - 1)
    elif edge_coord[1] in range(image_max_height//2, image_max_height - square_size):
        adjacent_coords.append(image_max_height - square_size - 1)
    else:
        adjacent_coords.append(edge_coord[1])

    # pprint(adjacent_coords)

    if edge_coord == [image_max_width//2 - 1, image_max_height - 1]:
        adjacent_angle = 0
        edge_angle_coords = [image_max_width-1, image_max_height-square_size-1]
    elif edge_coord == [0, image_max_height//2 - 1]:
        adjacent_angle = 90
        edge_angle_coords = [square_size-1, square_size-1]
    elif edge_coord == [image_max_width-1, image_max_height//2-1]:
        adjacent_angle = 270
        edge_angle_coords = [image_max_width - square_size - 1, square_size-1]

    # print('path coordinates: ', path_coords[:], edge_coord, adjacent_coords, adjacent_angle, edge_angle_coords)

    new_coords = angled_coords(path_coords[1], 180, adjacent_coords, adjacent_angle, square_size, edge_angle_coords)

    # print(len(new_coords), "new_coords: ", new_coords)

    if new_coords:
        new_coords = jitter_points_in_list(new_coords, half_square//4, half_square//4, True, True)
        # print("new-new coords:", new_coords)

    # if len(new_coords) > 0:
    #     print('new_coords gathered from angled_coords function: ')
    #     pprint(new_coords)

    if new_coords:
        if updated_path_coords:
            if adjacent_angle == 90:
                updated_path_coords.append(edge_coord)
                updated_path_coords.append(adjacent_coords)
                updated_path_coords.extend(new_coords)
                updated_path_coords.append(path_coords[1])
                updated_path_coords.append(path_coords[0])
            else:
                updated_path_coords.extend(list(path_coords[:]))
                updated_path_coords.extend(new_coords)
                updated_path_coords.append(adjacent_coords)
                updated_path_coords.append(edge_coord)
        else:
            if adjacent_angle == 90:
                updated_path_coords.append(edge_coord)
                updated_path_coords.append(adjacent_coords)
                updated_path_coords.extend(new_coords)
                updated_path_coords.append(path_coords[1])
                updated_path_coords.append(path_coords[0])
            else:
                updated_path_coords.extend(list(path_coords[:]))
                updated_path_coords.extend(new_coords)
                updated_path_coords.append(adjacent_coords)
                updated_path_coords.append(edge_coord)
        # print('new road coordinates for new path:')
        # pprint(updated_path_coords)
        road_coords.append(updated_path_coords)

old_time = new_time
new_time = time.time()
time_diff = new_time - old_time
print(f"edge calculations: {time_diff} seconds")

if [0, half_length-1] in edge_coords and [side_length-1, half_length-1] in edge_coords:
    adjacent_angle = 90
    edge_angle_coords = [side_length-1, half_length-1]
    new_coords = angled_coords([square_size-1, half_length-1], 270, [side_length-square_size-1, half_length-1], adjacent_angle, half_square, edge_angle_coords)

    updated_path_coords = []
    updated_path_coords.extend([[0, half_length-1], [square_size-1, half_length-1]])
    updated_path_coords.extend(new_coords)
    updated_path_coords.append(adjacent_coords)
    updated_path_coords.extend([[side_length-square_size-1, half_length-1], [side_length-1, half_length-1]])
    road_coords.append(updated_path_coords)

old_time = new_time
new_time = time.time()
time_diff = new_time - old_time
print(f"road calculations: {time_diff} seconds. Painting ditches...")

if len(road_coords) > 0:
    # print('Complete set of road paths:')
    # pprint(road_coords)

    road_paint = ImageDraw.Draw(image_object)
    for road_line in road_coords:
        line_road = []
        for road_point in road_line:
            line_road.append(tuple(road_point))
        # pprint(line_road)
        road_paint.line(line_road, fill=191, width=square_size*3)
        for line_point in line_road:
            # print(line_point)
            corner0 = (line_point[0] - square_size, line_point[1] - square_size)
            corner1 = (line_point[0] + square_size, line_point[1] + square_size)
            box_paint = [corner0, corner1]
            # print('ditch box_coords: ', box_paint)
            diamond_paint = [(line_point[0] + square_size * 2, line_point[1]), (line_point[0], line_point[1] + square_size * 2), (line_point[0] - square_size * 2, line_point[1]), (line_point[0], line_point[1] - square_size * 2)]
            # print('ditch diamond coords: ', box_paint)
            # pprint(box_paint)
            road_paint.rectangle(box_paint, fill=191, outline=191)
            road_paint.polygon(diamond_paint, fill=191, outline=191)

    if [0, image_max_height//2-1] in edge_coords and [image_max_width//2-1, image_max_height-1] in edge_coords:
        road_paint.rectangle(((image_max_width//2 - square_size * 3, image_max_height//2), (image_max_width//2, image_max_height//2 + square_size*3)), fill=ditch_color, outline=ditch_color)
    if [image_max_width - 1, image_max_height//2-1] in edge_coords and [image_max_width//2-1, image_max_height-1] in edge_coords:
        road_paint.rectangle(((image_max_width//2, image_max_height//2), (image_max_width//2 + square_size*3, image_max_height//2 + square_size*3)), fill=ditch_color, outline=ditch_color)

    old_time = new_time
    new_time = time.time()
    time_diff = new_time - old_time
    print(f"painted ditches: {time_diff} seconds. Painting roads...")

    for road_line in road_coords:
        line_road = []
        for road_point in road_line:
            line_road.append(tuple(road_point))
        # pprint(line_road)

        road_paint.line(line_road, fill=223, width=square_size*2)
        for line_point in line_road:
            corner0 = (line_point[0] - half_square, line_point[1] - half_square)
            corner1 = (line_point[0] + half_square, line_point[1] + half_square)
            box_paint = [corner0, corner1]
            # print('road box_coords: ', box_paint)
            # pprint(box_paint)
            diamond_paint = [(line_point[0] + square_size, line_point[1]), (line_point[0], line_point[1] + square_size), (line_point[0] - square_size, line_point[1]), (line_point[0], line_point[1] - square_size)]
            road_paint.rectangle(box_paint, fill=223, outline=223)
            road_paint.polygon(diamond_paint, fill=223, outline=223)

    if [0, image_max_height//2-1] in edge_coords and [image_max_width//2-1, image_max_height-1] in edge_coords:
        road_paint.rectangle(((image_max_width//2 - square_size * 2, image_max_height//2), (image_max_width//2, image_max_height//2 + square_size * 2)), fill=road_color, outline=road_color)
    if [image_max_width - 1, image_max_height//2-1] in edge_coords and [image_max_width//2-1, image_max_height-1] in edge_coords:
        road_paint.rectangle(((image_max_width//2, image_max_height//2), (image_max_width//2 + square_size * 2, image_max_height//2 + square_size * 2)), fill=road_color, outline=road_color)

    del(road_paint)

    # image_object.show()

    old_time = new_time
    new_time = time.time()
    time_diff = new_time - old_time
    print(f"painting roads: {time_diff} seconds")

    triangle_paint = ImageDraw.Draw(triangle_object)

    for triangle_coord_list in rand_array[array_triangles.simplices]:
        triangle_coordinates = []
        lightest_color = 159
        # lightest_color = randint(191,223)
        for coordinate_pair in triangle_coord_list:
            #coordinate_tuple = tuple(coordinate_pair)
            coordinate_tuple = (int(coordinate_pair[0]), int(coordinate_pair[1]))
            triangle_coordinates.append(coordinate_tuple)
            # print(coordinate_pair, coordinate_tuple)
            # print('pre-getpixel')
            current_color = image_object.getpixel(coordinate_tuple)
            # print(road_image[int(coordinate_tuple[0]), int(coordinate_tuple[1])])
            # print('post-getpixel')
            if current_color > lightest_color:
               lightest_color = current_color
        if lightest_color > 230:
            lightest_color = 255 # just go pure white at this level
        # print(triangle_coordinates)
        triangle_paint.polygon(triangle_coordinates, fill=lightest_color, outline=lightest_color)

    old_time = new_time
    new_time = time.time()
    time_diff = new_time - old_time
    print(f"repainting roads as triangles: {time_diff} seconds")

    coord_list = get_all_coords_in_image(side_length, side_length)
    px = triangle_object.load()
    for coords in coord_list:
        new_value = stipple_pixel(px[coords])
        if new_value != px[coords]:
            px[coords] = new_value

    old_time = new_time
    new_time = time.time()
    time_diff = new_time - old_time
    print(f"stippling base image: {time_diff} seconds. Converting to full color and overlaying wagon tracks.")

    del(triangle_paint)

    # triangle_object.convert(mode="RGBA")

    overlay_image = Image.new('RGBA', (image_max_width, image_max_height), (255,255,255,0))

    overlay_paint = ImageDraw.Draw(overlay_image)

    # print(path_coords)

    # print(edge_coords)

    if wagon_track_bool and [image_max_width//2-1, image_max_height-1] in edge_coords:
        track_list = [path_coords[0]]
        track_list.extend(angled_coords(path_coords[0], 180, (image_max_width//2-1, image_max_height - 1), 0, square_size, (path_coords[1])))
        track_list.append([path_coords[0][0],image_max_height - 1])
        track_list = jitter_points_in_list(track_list, half_square//16+1, half_square//16+1, True, True)

        # print(track_list)

        track1_polygon = generate_polygon_from_vertical_line(track_list, half_square//2)
        track2_polygon = copy_polygon(track1_polygon, [half_square,0], image_max_width, image_max_height)
        track1_polygon = copy_polygon(track1_polygon, [half_square*-1,0], image_max_width, image_max_height)
        # print(track1_polygon, track2_polygon)

        track_1_polygon = list(map(tuple, track1_polygon))
        track_2_polygon = list(map(tuple, track2_polygon))
        # print(track_1_polygon)
        # print(track_2_polygon)
        overlay_paint.polygon(track_1_polygon, fill=(wagon_track_color, wagon_track_color, wagon_track_color, wagon_track_alpha))
        overlay_paint.polygon(track_2_polygon, fill=(wagon_track_color, wagon_track_color, wagon_track_color, wagon_track_alpha))

    if wagon_track_bool and [0, image_max_height//2-1] in edge_coords and [image_max_width-1, image_max_height//2-1] in edge_coords:
        track_list = [[0, image_max_height//2-1]]
        track_list.extend(angled_coords((0, image_max_height//2-1), 90, (image_max_width-1, image_max_height//2 - 1), 270, square_size, (square_size-1, image_max_height//2-1)))
        track_list.append([image_max_width-1, image_max_height//2-1])
        track_list = jitter_points_in_list(track_list, half_square//16+1, half_square//16+1, True, True)

        # print(f"Horizontal Track line: ", track_list)

        track_polygon = generate_polygon_from_horizontal_line(track_list, half_square//2)
        track2_polygon = copy_polygon(track_polygon, [0,half_square], image_max_width, image_max_height)
        track1_polygon = copy_polygon(track_polygon, [0,half_square*-1], image_max_width, image_max_height)

        track_1_polygon = list(map(tuple, track1_polygon))
        track_2_polygon = list(map(tuple, track2_polygon))
        # print(track_1_polygon)
        # print(track_2_polygon)
        overlay_paint.polygon(track_1_polygon, fill=(wagon_track_color, wagon_track_color, wagon_track_color, wagon_track_alpha))
        overlay_paint.polygon(track_2_polygon, fill=(wagon_track_color, wagon_track_color, wagon_track_color, wagon_track_alpha))

    if wagon_track_bool and [0, image_max_height//2-1] in edge_coords:
        track_list = [[image_max_width//2 - (half_square//4*3) - 1, 0]]
        track_list.append([image_max_width//2 - (half_square//4*5) - 1, 0])
        track_list.append([image_max_width//2 - (half_square//4*5) - 1, square_size - 1])
        track_list.extend(list(sorted(angled_coords((image_max_width//2 - (half_square//4*5) - 1, square_size - 1), 180, (square_size - 1, image_max_height//2 - (half_square//4*5) - 1), 90, square_size, (square_size-1, square_size-1)), key=lambda x: x[0], reverse=True)))
        track_list.append([square_size - 1, image_max_height//2 - (half_square//4*5) - 1])
        track_list.append([0, image_max_height//2 - (half_square//4*5) - 1])
        track_list.append([0, image_max_height//2 - (half_square//4*3) - 1])
        track_list.append([square_size - 1, image_max_height//2 - (half_square//4*3) - 1])
        track_list.extend(list(sorted(angled_coords((image_max_width//2 - (half_square//4*3) - 1, square_size - 1), 180, (square_size - 1, image_max_height//2 - (half_square//4*3) - 1), 90, square_size, (square_size-1, square_size-1)), key=lambda x: x[1], reverse=True)))
        track_list.append([image_max_width//2 - (half_square//4*3) - 1, square_size - 1])
        track_list = jitter_points_in_list(track_list, half_square//16+1, half_square//16+1, False, False)

        # print(f"First Curved Track Polygon: ", track_list)

        track_list_polygon = list(map(tuple, track_list))
        # print(track_list_polygon)
        overlay_paint.polygon(track_list_polygon, fill=(wagon_track_color, wagon_track_color, wagon_track_color, wagon_track_alpha))

        track_list = [[image_max_width//2 + (half_square//4*5) - 1, 0]]
        track_list.append([image_max_width//2 + (half_square//4*3) - 1, 0])
        track_list.append([image_max_width//2 + (half_square//4*3) - 1, square_size - 1])
        track_list.extend(list(sorted(angled_coords((image_max_width//2 + (half_square//4*3) - 1, square_size - 1), 180, (square_size - 1, image_max_height//2 + (half_square//4*3) - 1), 90, square_size, (square_size-1, square_size-1)), key=lambda x: x[0], reverse=True)))
        track_list.append([square_size - 1, image_max_height//2 + (half_square//4*3) - 1])
        track_list.append([0, image_max_height//2 + (half_square//4*3) - 1])
        track_list.append([0, image_max_height//2 + (half_square//4*5) - 1])
        track_list.append([square_size - 1, image_max_height//2 + (half_square//4*5) - 1])
        track_list.extend(list(sorted(angled_coords((image_max_width//2 + (half_square//4*5) - 1, square_size - 1), 180, (square_size - 1, image_max_height//2 + (half_square//4*5) - 1), 90, square_size, (square_size-1, square_size-1)), key=lambda x: x[1], reverse=True)))
        track_list.append([image_max_width//2 + (half_square//4*5) - 1, square_size - 1])
        track_list = jitter_points_in_list(track_list, half_square//16+1, half_square//16+1, False, False)

        # print(f"Second Curved Track Polygon: ", track_list)

        track_list_polygon = list(map(tuple, track_list))
        # print(track_list_polygon)
        overlay_paint.polygon(track_list_polygon, fill=(wagon_track_color, wagon_track_color, wagon_track_color, wagon_track_alpha))

    if wagon_track_bool and [image_max_width - 1, image_max_height//2-1] in edge_coords:
        track_list = [[image_max_width - 1, image_max_height//2 - (half_square//4*5) - 1]]
        track_list.append([image_max_width - square_size - 1, image_max_height//2 - (half_square//4*5) - 1])
        track_list.extend(list(sorted(angled_coords((image_max_width//2 + (half_square//4*5) - 1, square_size - 1), 180, (image_max_width - square_size - 1, image_max_height//2 - (half_square//4*5) - 1), 270, square_size, (image_max_width - square_size - 1, square_size-1)), key=lambda x: x[0], reverse=True)))
        track_list.append([image_max_width//2 + (half_square//4*5) - 1, square_size - 1])
        track_list.append([image_max_width//2 + (half_square//4*5) - 1, 0])
        track_list.append([image_max_width//2 + (half_square//4*3) - 1, 0])
        track_list.append([image_max_width//2 + (half_square//4*3) - 1, square_size - 1])
        track_list.extend(list(sorted(angled_coords((image_max_width//2 + (half_square//4*3) - 1, square_size - 1), 180, (image_max_width - square_size - 1, image_max_height//2 - (half_square//4*3) - 1), 270, square_size, (image_max_width - square_size - 1, square_size-1)), key=lambda x: x[0], reverse=False)))
        track_list.append([image_max_width - square_size - 1, image_max_height//2 - (half_square//4*3) - 1])
        track_list.append([image_max_width - 1, image_max_height//2 - (half_square//4*3) - 1])
        track_list = jitter_points_in_list(track_list, half_square//16+1, half_square//16+1, False, False)

        # print(f"First Curved Track Polygon: ", track_list)

        track_list_polygon = list(map(tuple, track_list))
        # print(track_list_polygon)
        overlay_paint.polygon(track_list_polygon, fill=(wagon_track_color, wagon_track_color, wagon_track_color, wagon_track_alpha))

        track_list = [[image_max_width - 1, image_max_height//2 + (half_square//4*3) - 1]]
        track_list.append([image_max_width - square_size - 1, image_max_height//2 + (half_square//4*3) - 1])
        track_list.extend(list(sorted(angled_coords((image_max_width//2 - (half_square//4*3) - 1, square_size - 1), 180, (image_max_width - square_size - 1, image_max_height//2 + (half_square//4*3) - 1), 270, square_size, (image_max_width - square_size - 1, square_size-1)), key=lambda x: x[0], reverse=True)))
        track_list.append([image_max_width//2 - (half_square//4*3) - 1, square_size - 1])
        track_list.append([image_max_width//2 - (half_square//4*3) - 1, 0])
        track_list.append([image_max_width//2 - (half_square//4*5) - 1, 0])
        track_list.append([image_max_width//2 - (half_square//4*5) - 1, square_size - 1])
        track_list.extend(list(sorted(angled_coords((image_max_width//2 - (half_square//4*5) - 1, square_size - 1), 180, (image_max_width - square_size - 1, image_max_height//2 + (half_square//4*5) - 1), 270, square_size, (image_max_width - square_size - 1, square_size-1)), key=lambda x: x[0], reverse=False)))
        track_list.append([image_max_width - square_size - 1, image_max_height//2 + (half_square//4*5) - 1])
        track_list.append([image_max_width - 1, image_max_height//2 + (half_square//4*5) - 1])
        track_list = jitter_points_in_list(track_list, half_square//16+1, half_square//16+1, False, False)

        # print(f"Second Curved Track Polygon: ", track_list)

        track_list_polygon = list(map(tuple, track_list))
        # print(track_list_polygon)
        overlay_paint.polygon(track_list_polygon, fill=(wagon_track_color, wagon_track_color, wagon_track_color, wagon_track_alpha))

    if wagon_track_bool and [0, image_max_height//2-1] in edge_coords and [image_max_width//2-1, image_max_height-1] in edge_coords:
        side_coords = [0, image_max_height//2 - 1]
        bottom_coords = [image_max_width//2 - 1, image_max_height - 1]

        side_track_coords = [[side_coords[0] + square_size - 1, side_coords[1] - (half_square*5//4)],
                [side_coords[0], side_coords[1] - (half_square*5//4)],
                [side_coords[0], side_coords[1] - (half_square*3//4)],
                [side_coords[0] + square_size - 1, side_coords[1] - (half_square*3//4)],
                [side_coords[0] + square_size - 1, side_coords[1] + (half_square*3//4)],
                [side_coords[0], side_coords[1] + (half_square*3//4)],
                [side_coords[0], side_coords[1] + (half_square*5//4)],
                [side_coords[0] + square_size - 1, side_coords[1] + (half_square*5//4)]]
        bottom_track_coords = [[bottom_coords[0] + (half_square*5//4), bottom_coords[1] - square_size],
                [bottom_coords[0] + (half_square*3//4), bottom_coords[1] - square_size],
                [bottom_coords[0] + (half_square*3//4), bottom_coords[1]],
                [bottom_coords[0] + (half_square*5//4), bottom_coords[1]],
                [bottom_coords[0] - (half_square*3//4), bottom_coords[1] - square_size],
                [bottom_coords[0] - (half_square*5//4), bottom_coords[1] - square_size],
                [bottom_coords[0] - (half_square*5//4), bottom_coords[1]],
                [bottom_coords[0] - (half_square*3//4), bottom_coords[1]]]

        track_list = [bottom_track_coords[0]]
        track_list.extend(list(sorted(angled_coords(side_track_coords[0], 90, bottom_track_coords[0], 0, square_size, (side_track_coords[0][0], bottom_track_coords[0][1])), key=lambda x: x[0], reverse=True)))
        track_list.extend(side_track_coords[0:4])
        # print("First curve and four points west points of the top West-to-South track: ", track_list)
        track_list.extend(list(sorted(angled_coords(side_track_coords[3], 90, bottom_track_coords[1], 0, square_size, (side_track_coords[0][0], bottom_track_coords[0][1])), key=lambda x: x[0], reverse=False)))
        track_list.extend(bottom_track_coords[1:4])
        track_list = jitter_points_in_list(track_list, half_square//16+1, half_square//16+1, False, False)

        # print(f"First Curved Track Polygon: ", track_list)

        track_list_polygon = list(map(tuple, track_list))
        # print(track_list_polygon)
        overlay_paint.polygon(track_list_polygon, fill=(wagon_track_color, wagon_track_color, wagon_track_color, wagon_track_alpha))

        track_list = [bottom_track_coords[4]]
        track_list.extend(list(sorted(angled_coords(side_track_coords[4], 90, bottom_track_coords[4], 0, square_size, (side_track_coords[0][0], bottom_track_coords[0][1])), key=lambda x: x[0], reverse=True)))
        track_list.extend(side_track_coords[4:])
        # print("First curve and four points west points of the top West-to-South track: ", track_list)
        track_list.extend(list(sorted(angled_coords(side_track_coords[7], 90, bottom_track_coords[5], 0, square_size, (side_track_coords[0][0], bottom_track_coords[0][1])), key=lambda x: x[0], reverse=False)))
        track_list.extend(bottom_track_coords[5:])
        track_list = jitter_points_in_list(track_list, half_square//16+1, half_square//16+1, False, False)

        # print(f"Second Curved Track Polygon: ", track_list)

        track_list_polygon = list(map(tuple, track_list))
        # print(track_list_polygon)
        overlay_paint.polygon(track_list_polygon, fill=(wagon_track_color, wagon_track_color, wagon_track_color, wagon_track_alpha))

    if wagon_track_bool and [image_max_width-1, image_max_height//2-1] in edge_coords and [image_max_width//2-1, image_max_height-1] in edge_coords:
        side_coords = [image_max_width-1, image_max_height//2 - 1]
        bottom_coords = [image_max_width//2 - 1, image_max_height - 1]

        side_track_coords = [[side_coords[0], side_coords[1] - (half_square*5//4)],
                [side_coords[0] - square_size, side_coords[1] - (half_square*5//4)],
                [side_coords[0] - square_size, side_coords[1] - (half_square*3//4)],
                [side_coords[0], side_coords[1] - (half_square*3//4)],
                [side_coords[0], side_coords[1] + (half_square*3//4)],
                [side_coords[0] - square_size, side_coords[1] + (half_square*3//4)],
                [side_coords[0] - square_size, side_coords[1] + (half_square*5//4)],
                [side_coords[0], side_coords[1] + (half_square*5//4)]]
        bottom_track_coords = [[bottom_coords[0] + (half_square*5//4), bottom_coords[1] - square_size],
                [bottom_coords[0] + (half_square*3//4), bottom_coords[1] - square_size],
                [bottom_coords[0] + (half_square*3//4), bottom_coords[1]],
                [bottom_coords[0] + (half_square*5//4), bottom_coords[1]],
                [bottom_coords[0] - (half_square*3//4), bottom_coords[1] - square_size],
                [bottom_coords[0] - (half_square*5//4), bottom_coords[1] - square_size],
                [bottom_coords[0] - (half_square*5//4), bottom_coords[1]],
                [bottom_coords[0] - (half_square*3//4), bottom_coords[1]]]

        track_list = side_track_coords[0:2]
        # print('East to South angle coordinates: ', (side_track_coords[1][0], bottom_track_coords[1][1]))
        # print('South starting coordinates: ', bottom_track_coords[5])
        # print('East starting coordinates: ', side_track_coords[1])
        track_list.extend(list(sorted(angled_coords(side_track_coords[1], 270, bottom_track_coords[5], 360, square_size, (side_track_coords[1][0], bottom_track_coords[1][1])), key=lambda x: x[0], reverse=True)))
        track_list.extend(bottom_track_coords[5:7])
        track_list.append(bottom_track_coords[7])
        track_list.append(bottom_track_coords[4])
        track_list.extend(list(sorted(angled_coords(bottom_track_coords[4], 360, side_track_coords[2], 270, square_size, (side_track_coords[1][0], bottom_track_coords[1][1])), key=lambda x: x[0], reverse=False)))
        track_list.extend(side_track_coords[2:4])
        track_list = jitter_points_in_list(track_list, half_square//16+1, half_square//16+1, False, False)

        # print(f"First Curved Track Polygon: ", track_list)

        track_list_polygon = list(map(tuple, track_list))
        # print('First Curved Track Polygon as tuples: ', track_list_polygon)
        overlay_paint.polygon(track_list_polygon \
                , fill=(wagon_track_color, wagon_track_color, wagon_track_color, wagon_track_alpha))

        track_list = side_track_coords[4:6]
        track_list.extend(list(sorted(angled_coords(side_track_coords[5], 270
            , bottom_track_coords[1], 360
            , square_size, (side_track_coords[1][0], bottom_track_coords[1][1]))
            , key=lambda x: x[0], reverse=True)))
        track_list.extend(bottom_track_coords[1:4])
        track_list.append(bottom_track_coords[0])
        # print("First curve and four points west points of the top West-to-South track: ", track_list)
        track_list.extend(list(sorted(angled_coords(side_track_coords[6], 270
            , bottom_track_coords[0], 360
            , square_size, (side_track_coords[1][0], bottom_track_coords[1][1]))
            , key=lambda x: x[0], reverse=False)))
        track_list.extend(side_track_coords[6:])
        track_list = jitter_points_in_list(track_list
                , half_square//16+1, half_square//16+1, False, False)

        # print(f"Second Curved Track Polygon: ", track_list)

        track_list_polygon = list(map(tuple, track_list))
        # print('Second Curved Track Polygon as tuples: \n', track_list_polygon)
        overlay_paint.polygon(track_list_polygon \
                , fill=(wagon_track_color, wagon_track_color, wagon_track_color, wagon_track_alpha))

    old_time = new_time
    new_time = time.time()
    time_diff = new_time - old_time
    print(f"added wagon tracks: {time_diff} seconds. Overlaying hexagons.")

    for inches in range(1, 6):
        if inches % 2 == 1:
            draw_hexagon(overlay_paint, (inches * image_dpi, hex_radius_ratio * image_dpi) \
                    , hex_radius_ratio * image_dpi \
                    , half_square//4, (128, 128, 128, 128) \
                    , half_square//16, (0, 0, 0, 255), hexagons_bool, dots_bool)
            draw_hexagon(overlay_paint, ((inches-1) * image_dpi, hex_radius_ratio * image_dpi * 2.5) \
                    , hex_radius_ratio * image_dpi \
                    , half_square//4, (128, 128, 128, 128) \
                    , half_square//16, (0, 0, 0, 255), hexagons_bool, dots_bool)
            draw_hexagon(overlay_paint, (inches * image_dpi, hex_radius_ratio * image_dpi * 4) \
                    , hex_radius_ratio * image_dpi \
                    , half_square//4, (128, 128, 128, 128)\
                    , half_square//16, (0, 0, 0, 255), hexagons_bool, dots_bool)

    del overlay_paint

    base_image = triangle_object.convert(mode="RGBA")
    hex_image = Image.alpha_composite(base_image, overlay_image)
    grid_image = hex_image.convert(mode="L")

    old_time = new_time
    new_time = time.time()
    time_diff = new_time - old_time
    print(f"overlaid hexagons: {time_diff} seconds. Saving Image. ")

    # image_object.show()

    # Do not use Image.eval!
    # Any random functions are run once and used on all pixels.
    # new_triangle_object = Image.eval(triangle_object, stipple_pixel)

    # triangle_object.filter(ImageFilter.BLUR())
    # triangle_object.filter(ImageFilter.BoxBlur(2))
    # triangle_object.filter(ImageFilter.SMOOTH())
    # triangle_object.show()
    # grid_image.show()

    # old_time = new_time
    # new_time = time.time()
    # time_diff = new_time - old_time
    # print(f"showed base image: {time_diff} seconds. ")

    if file_type_ext == 'png':
        grid_image.save(full_file_path, format='PNG', optimize=True, dpi=(image_dpi,image_dpi))
    elif file_type_ext == 'gif':
        grid_image.save(full_file_path, format='GIF')
    elif file_type_ext == 'jpg':
        grid_image.save(full_file_path, format='JPEG', quality=85, optimize=True, dpi=(image_dpi,image_dpi))
    elif file_type_ext == 'pcx':
        grid_image.save(full_file_path, format='PCX')
    elif file_type_ext == 'tif':
        grid_image.save(full_file_path, format='TIFF', dpi=(image_dpi, image_dpi))
    elif file_type_ext == 'bmp':
        grid_image.save(full_file_path, format='BMP')
    else:
        grid_image.save(full_file_path, format='PNG', optimize=True, dpi=(image_dpi,image_dpi))

    old_time = new_time
    new_time = time.time()
    time_diff = new_time - old_time
    print(f"saved image to file: {time_diff} seconds. ")

    time_diff = new_time - start_time
    print(f"Total Processing Time: {time_diff} seconds")
