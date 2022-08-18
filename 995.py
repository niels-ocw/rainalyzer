''' comments of this type display program flow '''
# usage: 
# run normal mode:  $ python3 995.py        downloads a .gif
# run demo mode:    $ python3 995.py demo   selects a random .gif from demo-gifs
import time
from sys import exit, argv
from PIL import Image, ImageFont, ImageDraw
from matplotlib import pyplot as plt
import numpy as np
from pprint import pprint as pp
import random
import requests

# for the radar_IN-xxx and radar_OUT-xxx image files a random filename end is used
# to prevent browsers from re-using cached files and not updating to new image files
# this would result in no new image being displayed in the browser
import glob
glob.filename_random
glob.filename_random = str(random.randint(0, 1000))
# print(f"995.py: glob.filename_random == {glob.filename_random}")
with open('static/rand_int.txt', mode='w', encoding='utf-8') as f:
    f.write(glob.filename_random)

# colors in this palette are NOT clouds; sorted in order of frequency :)
# see: get_palette-3.py; these land and sea colors were obtained from a clear sky day image using PIL
# also see: plot_palette()
# also: all other colors therefor must be precipitation-pixels
not_a_cloud_RGBA = [(53, 147, 188, 255), (114, 166, 76, 255), (145, 185, 110, 255), (83, 138, 76, 255), (147, 186, 112, 255), (112, 166, 103, 255), (138, 180, 107, 255), (104, 152, 79, 255), (75, 151, 141, 255), (78, 145, 114, 255), (108, 169, 139, 255), (51, 148, 193, 255), (136, 181, 117, 255), (118, 163, 89, 255), (107, 163, 87, 255),
                    (131, 172, 99, 255), (60, 141, 147, 255), (72, 154, 165, 255), (90, 162, 153, 255), (109, 161, 75, 255), (98, 157, 100, 255), (94, 160, 111, 255), (80, 131, 60, 255), (84, 160, 160, 255), (62, 136, 117, 255), (129, 169, 93, 255), (69, 126, 65, 255), (59, 131, 83, 255), (128, 175, 113, 255), (71, 126, 62, 255), (128, 179, 129, 255)]

# filter: ignore clouds with area <= this
# see: def returns_sorted_cg_clouds(groups, cloudlines, frame_count):
IGNORE_AREA = 5

# filenames and locations
FILE_NAME_OUT = f"static/radar_OUT-{glob.filename_random}.gif"
BACKGROUND_FILE = "static/NL_map.png"
FONT_FILE = "04b03.ttf"

# selects running 995.py in either normal or demo mode
# FILE_NAME used in get_radar_image()
# FILE_NAME is the .gif image that is retrieved from KNMI
if len(argv) == 2 and argv[1] == 'demo':
    # select one of 27 demo radar images from demo-gifs folder
    # note: randint: both 1 and 27 included
    ri = random.randint(1, 27)
    FILE_NAME = f"demo-gifs/{ri}.gif"
    print("Rainalyzer: DEMO-MODE")
else:
    FILE_NAME = f"static/radar_IN-{glob.filename_random}.gif"
    print("Rainalyzer: NORMAL-MODE")


def main():
    # get latest radar image from online resource if in normal mode:
    if not (len(argv) == 2 and argv[1] == 'demo'):
        # on succesfully connecting to KNMI website will save 'radar_IN-xxx.gif' to disk,
        # as defined by FILE_NAME
        get_radar_image()

    # load input file from disk, create a list of separate image frames
    ''' frames_RGBA[] <<< FILE_NAME '''
    frames_RGBA, frame_count, w, h = load_gif_into_frames_list_RGBA(FILE_NAME)

    # checks if downloaded .gif has exactly 12 separate frames
    # PS: this is the 2nd check:
    # also image_is_valid(im) was run in load_gif_into_frames_list_RGBA() to check other image properties
    if not (frame_count == 12 and frame_count == len(frames_RGBA)):
        print("Error frame_count not 12.")
        exit(1)

    ''' frames_full_RGBA[] <<< frames_RGBA[] '''
    # initial frames list contains only per frame changes:
    # but we want the full images per frame in a list "frames_full_RGBA"
    # thus each frame is the sum of all its previous frames
    frames_full_RGBA = returns_full_frames_RGBA(frames_RGBA, frame_count)

    ''' clouds_L[] <<< frames_full_RGBA[] '''
    # (PS the term 'clouds' actually means where there is rain/precipitation)
    # in "frames_full_RGBA[]" all frames now have both the terrain and cloud pixels,
    # the cloudpixels will be extracted by comparing frames with colors from not_a_cloud_RGBA[]
    # therefore clouds_L[] contains only 255's for clouds and 0's for no clouds
    clouds_L = returns_only_cloud_pixel_frames(frames_full_RGBA, frame_count, w, h)
    
    # the following part is probably not easy to understand, see also function description of 'returns_groups_of_cloud_pixels()'
    # create groups of horizontally and vertically neighboring pixels 
    # done in 2 steps inside function returns_groups_of_cloud_pixels():
    ''' (1/2) cloudlines[] <<< clouds_L[]   (cloudlines are horizontally neighboring/connected cloud pixels) '''
    ''' (2/2) groups[] <<< cloudlines[]     (groups are vertically neighboring/connected cloudlines) '''
    # returns sets of cloudlines "groups" that together form a cloud;
    # eg. groups[11][-4] = {2048, 2051, 2054, 2057, 2060, 2045, 2062, 2063}
    # and then lookup the line_number gives:
    # cloudlines[11][2063] = [-1, 2063, 424, [138, 139, 140]]
    # cloudlines[i][line_nr] = [group_nr, cloudline_nr, y, [x0, x1, ..] ]
    # where in cloudlines[i][line_nr]:
    # ~[2] = y and ~[3] = [x-coordinates]
    groups, cloudlines = returns_groups_of_cloud_pixels(clouds_L, frame_count, w, h)

    ''' C[] <<< groups[], cloudlines '''
    # next we calculate the area-center of each cloud (CG) from groups[] and cloudlines[],
    # the data will be sorted such that the
    # largest area cloud is at index n=0 in each frame i, where n = cloud_nr and CG = (x,y)
    # C[i][n] = [[(x,y), ...], area, CG]
    C = returns_sorted_cg_clouds(groups, cloudlines, frame_count)
    
    ''' vx, vy <<< C[] '''
    # from the in-between frames movement of the clouds' CG's we can calculate their speeds: vx, vy
    # use the following plotting function to illustrate whats going on;
    # will output a graph (set False to True)
    if False:
        plot_cgs(C, frame_count)

    vx, vy = returns_vx_vy(C, frame_count)

    ''' next_12_frames[] <<< crop-translate-add <<< vx, vy, clouds_L[] '''
    # now that we have the velocity in x and y direction, we can use this
    # to calculate the predicted movement of cloud-pixels for the next 60 minutes.
    # with the last frame from clouds_L as a starting point we move the cloud-pixels by vx and vy
    # for the next 12*5-minute frames
    next_12_frames = translate_and_edges(clouds_L[frame_count - 1], vx, vy, frame_count)

    ''' FILE_NAME_OUT <<< next_12_frames[] '''
    # first add footer text to indicate relative time in frames:
    add_footer_text(next_12_frames, frame_count)
    # save as a .gif to disk:
    save_list_to_file(next_12_frames, FILE_NAME_OUT)

    # in demo mode save demo-gif in square format, same as output gif
    if len(argv) == 2 and argv[1] == 'demo':
        add_footer_text_negative(frames_full_RGBA, frame_count)
        save_list_to_file(frames_full_RGBA, f"static/radar_IN-{glob.filename_random}.gif")
        # print(f"DEMO-MODE: radar_IN-{glob.filename_random}.gif saved (square version with negative time)")

    # exit(0) moved into maintime()


# retrieves and saves current radar image from KNMI (Netherlands metereological institute)
# https://requests.readthedocs.io/en/master/user/quickstart/#binary-response-content
# import requests
# uses: FILE_NAME
# returns: saves file to disk
def get_radar_image():
    radar_url = "https://cdn.knmi.nl/knmi/map/page/weer/actueel-weer/neerslagradar/WWWRADAR_loop.gif"

    try:
        r = requests.get(radar_url, timeout=2)
    except:
        print("Error: could not connect, try again later")
        exit(1)

    with open(FILE_NAME, 'wb') as f:
        f.write(r.content)
        print(f"saved image as:\t'{FILE_NAME}'")


# checks if the downloaded or any image's properties are as expected:
# checks if is GIF in Palette mode and size and if image has multiple frames: is animated
# PS does not check if frame_count == 12; this is done in main()
def image_is_valid(im):
    if im.format == "GIF" and im.mode == "P" and im.size == (425, 445) and im.is_animated:
        return True
    return False


# loads FILE_NAME ("radar_IN-xxx.gif") and extracts frames,
# puts separate frames into list ("frames_RGBA") and removes text by cropping frames
# (!) NOTE: these frames only contain the pixel changes in between frames; see also: returns_full_frames_RGBA()
# RETURNS: list of frames: 'frames_RGBA', frame_count, width, height
#   type: list items: <class 'PIL.Image.Image'>
#   frames_RGBA[i].info = {'version': b'GIF89a', 'background': 0, 'duration': 400, 'extension': (b'NETSCAPE2.0', 803), 'loop': 0}
def load_gif_into_frames_list_RGBA(FILE_NAME):
    frames_RGBA = []
    with Image.open(FILE_NAME) as im:
        # check if downloaded image from KNMI has the right properties:
        # ..will exit if not right properties
        if not image_is_valid(im):
            print("Radar input image format invalid.")
            exit(1)
        
        # ..continues if downloaded image properties are valid:
        frame_count = im.n_frames
        
        # plot_palette(im)

        # append each separate frame into frames list
        '''the seek(0) and seek(END) are required because else pillow will create black areas in images/frames. Cause unknown...'''
        for frame_index in range(0, frame_count):
            im.seek(0)
            im.seek(frame_index)
            # gif needs to be converted to be able to read from list later:
            frames_RGBA.append(im.convert("RGBA"))
            im.seek(11)
        
        # note: this will make the image frame into a square:
        # height == width
        w, h = im.width, im.width

        # crop the image, remove lower text part
        for i in range(0, frame_count):
            frames_RGBA[i] = frames_RGBA[i].crop((0, 0, w, h))

    return frames_RGBA, frame_count, w, h


# (!) NOT USED
# same as "load_gif_into_frames_list_RGBA" except for the "A",
# and does not return width, height
def load_gif_into_frames_list_RGB(FILE_NAME):
    frames = []
    with Image.open(FILE_NAME) as im:
        # check if downloaded image from KNMI website has the right properties:
        if not image_is_valid(im):
            print("Radar input image format invalid.")
            exit(1)

        frame_count = im.n_frames
        # plot_palette(im)

        # append each separate frame into frames list
        '''the seek(0) and seek(END) are required because else pillow will create black areas in images/frames. Cause unknown...'''
        for frame_index in range(0, frame_count):
            im.seek(0)
            im.seek(frame_index)
            # gif needs to be converted to be able to read from list later:
            frames.append(im.convert("RGB"))
            im.seek(11)

        # crop the image, remove lower text part
        for i in range(0, frame_count):
            frames[i] = frames[i].crop((0, 0, im.width, im.width))

    return frames, frame_count


# returns a list of image frames filled with cloud and non-cloud pixels
# initially created "frames_RGBA" list from "load_gif_into_frames_list_RGBA()" contains only per frame changes:
# but we want the full images per frame
# thus each frame is the sum of all its previous frames
# RETURNS: frames_full_RGBA
def returns_full_frames_RGBA(frames_RGBA, frame_count):
    # all full color frames to be stored in a new list:
    frames_full_RGBA = []

    # the next for-loop is going over all pixels in all frames: frame N = frame N-1 ...
    # adding up the pixel information from all previous frames
    # copying pixels that are not A = 0, using copy and mask:
    
    # preparing the loop:
    # 1st frame is skipped in iteration, as its already complete
    # 1st frame is basis for all the following frames
    frames_full_RGBA.append(frames_RGBA[0].copy())

    # 1st frame is also needed to paste the next frame onto:
    # so stored here as prev_frame for use in loop
    prev_frame = frames_full_RGBA[0].copy()

    # all other frames are the sum of all previous frames
    for i in range(1, frame_count):
        new_frame = prev_frame.copy()
        # the A channel is used as mask:
        # (see online manual Pillow)
        # Image.paste(im, box=None, mask=None)
        new_frame.paste(frames_RGBA[i], box=None, mask=frames_RGBA[i])
        frames_full_RGBA.append(new_frame)
        # set current frame to be "prev_frame" for next iteration:
        prev_frame = frames_full_RGBA[i].copy()

    return frames_full_RGBA


# extracts cloud pixels from input list "frames_full_RGBA[]",
# and stores the clouds in a new list of frames
# (L-mode images are single channel images, they store per pixel luminance as values 0-255)
# (L-mode aka grey scale (0-255))
def returns_only_cloud_pixel_frames(frames_full_RGBA, frame_count, w, h):
    clouds_L = []

    # fill clouds_L[] with all black frames;
    # makes a list of 12 mode-L-frames, all color 0
    # (frame_count = 12)
    for i in range(frame_count):
        new_empty_frame = Image.new(mode="L", size=(w, h), color=0)
        clouds_L.append(new_empty_frame)

    # if a pixel in RGBA frame is a cloud, set mode-L to color=255
    # (for all frames)
    for i in range(0, frame_count):
        # (go through all rows)
        for y in range(0, h):
            # go through all pixels in x direction:
            for x in range(0, w):
                pixel = frames_full_RGBA[i].getpixel((x, y))  # (R, G, B, A)
                # if RGBA-pixel IS a cloud: set value in L-mode-pixel from 0 to 2555
                # IS a cloud == is not not_a_cloud
                # (we only have a list of non-cloud pixels and not of are-cloud-pixels)
                if not pixel in not_a_cloud_RGBA:
                    clouds_L[i].putpixel((x, y), 255)

    return clouds_L


# groups together all pixels that are directly neighboring in horizontal or/and vertical direction
# returns cloudlines[]: horizontally neighboring cloud-pixels in the same row
# they share the same y-coordinate and individual pixels can be restored from the cloudlines,
# by combining the y-coordinate and all entries from the x-coordinate list:
# cloudlines[i][line_nr] = [group_nr, cloudline_nr, y, [x0, x1, ..] ]
# returns also groups[]: sets of cloudlines that together form a cloud,
# or in other words: cloudlines that are directly neighboring in y-direction
def returns_groups_of_cloud_pixels(clouds_L, frame_count, w, h):
    ''' (1/2) grouping all neighbouring pixels in each y-row in groups identified by cloudline_nr '''
    # cloudlines contains lists per frame
    # these lists contain coordinate collection lists per horizontally touching pixels: called cloud lines
    # cloudlines[i][0] thus gives a list containing all coordinate tuples that belong to cloud number 0:
    # cloudlines[i][cloudline_nr] = [(yx), ...], and
    # cloudlines[i][cloudline_nr].append((y,x)) appends coordinate to list
    # cloudline_nr is actually the index of the sub arrays
    #
    # fill the cloudlines with empty lists for easier access in next for loop
    cloudlines = [[] for i in range(frame_count)]

    # cloud number map per pixel: gives per pixel(x,y) the corresponding cloudline_nr
    # each frame gets its own cloud number reference per pixel
    # cloudline_nrs_map[frame=i][y=y][x=x] = -1 <default values> = cloudline_nr
    cloudline_nrs_map = [[[-1 for x in range(w)] for y in range(h)] for i in range(frame_count)]

    for i in range(frame_count):
        cloudline_nr = -1

        for y in range(h):
            last_p = False

            for x in range(w):
                # pixel returned is either 0: no cloud, or 255: yes cloud
                p = clouds_L[i].getpixel((x, y))

                if last_p == False and p == 0:
                    pass

                elif last_p == False and p == 255:
                    cloudline_nr = cloudline_nr + 1
                    last_p = True

                    # init new cloudline:
                    # cloudline = [group_nr, cloudline_nr, y, [x0, x1, ..] ]
                    cloudlines[i].append([-1, cloudline_nr, y, []])
                    # append x coordinates:
                    cloudlines[i][cloudline_nr][3].append(x)

                    # put cloudline_nr into map; replace the -1 by cloudline_nr
                    cloudline_nrs_map[i][y][x] = cloudline_nr

                elif last_p == True and p == 0:
                    last_p = False

                elif last_p == True and p == 255:
                    # append x coordinates:
                    cloudlines[i][cloudline_nr][3].append(x)

                    # put cloudline_nr into map; replace the -1 by cloudline_nr
                    cloudline_nrs_map[i][y][x] = cloudline_nr

    ''' (2/2) connectiong all vertically adjacent y-rows in groups identified by cloud_id (NOT cloudline_nr) '''
    # {notes pages 20,..}

    # cloudline = [group_nr, cloudline_nr, y, [x0, x1, ..] ]
    # cloudline_nrs_map[i][y][x] = cloudline_nr

    # after next loop groups[i] will contain groups[i] = groups[GROUP_NR]
    groups = [[] for i in range(frame_count)]
    group_nr_for_lines = [[] for i in range(frame_count)]

    for i in range(0, frame_count):
        groups_i = groups[i]
        # list of all line#'s in this frame:
        all_line_nrs = [n for n in range(len(cloudlines[i]))]
        unassigned = set(all_line_nrs)
        group_nr_for_line = dict([(n, None) for n in all_line_nrs])
        # G is last MAIN group#:
        G = -1
        # small-g is current group#
        g = None

        # n = cloudline_nr
        for n in all_line_nrs:
            current_line = cloudlines[i][n]
            X = current_line[3]  # = [x0..xn]
            y = current_line[2]

            if group_nr_for_line[n] == None:
                # line is ungrouped: create new group and assign line to it:
                groups_i.append(set())  # groups[i] = [{ <filled with cloudline_nr's> }, ..]
                G = G + 1  # G is now at right index: groups_i[G] = groups[i][G] = set() :: references current group set
                # small-g is current group#
                g = G

                # add n to dict and to group-set:
                current_group = groups_i[g]
                group_nr_for_line[n] = g
                current_group.add(n)

                # remove newly assigned line-nrs from the unassigned set
                unassigned.remove(n)

            else:
                # line is already grouped: get its group number:
                g = group_nr_for_line[n]

            # current_group = groups_i[g]
            new_neighbors = set()  # {}
            ass_neighbors = set()  # {}

            # check north neighbors:
            if not y == 0:
                for x in X:
                    # get line# for this (x,y):
                    line_nr = cloudline_nrs_map[i][y - 1][x]

                    if not line_nr == -1:
                        if line_nr in unassigned:
                            # current_group.add(n)
                            new_neighbors.add(line_nr)
                        else:
                            # if already assigned
                            ass_neighbors.add(line_nr)

            # check south neighbors:
            if y < h - 1:
                for x in X:
                    # get line# for this (x,y):
                    line_nr = cloudline_nrs_map[i][y + 1][x]

                    if not line_nr == -1:
                        if line_nr in unassigned:
                            # current_group.add(n)
                            new_neighbors.add(line_nr)
                        else:
                            # if already assigned
                            ass_neighbors.add(line_nr)

            # update new neighbors's line# to group# mapping:
            for line_nr in new_neighbors:
                # delme:
                if not group_nr_for_line[line_nr] == None:
                    print("logic error 516")
                    exit(1)

                # assign groupnr to linenr:
                group_nr_for_line[line_nr] = g

            # put new_neighbors's members into current group
            current_group = groups_i[g]
            current_group.update(new_neighbors)

            # remove newly assigned line-nrs from the unassigned set
            for nrs in new_neighbors:
                unassigned.remove(nrs)

            if ass_neighbors:  # == line numbers
                # need to add n, to determine if it has the lowest group number
                # n = current line nr:
                if n not in ass_neighbors:
                    ass_neighbors.add(n)

                # get group numbers of assigned neighbors:
                ass_neighbor_group_nrs = set()
                for nrs in ass_neighbors:
                    ass_neighbor_group_nrs.add(group_nr_for_line[nrs])

                # determine the leading groupnumber: this is the lowest from the set
                leader = min(ass_neighbor_group_nrs)  # leader = group nr
                mergers = ass_neighbor_group_nrs  # mergers = group nrs
                if leader in ass_neighbor_group_nrs:
                    mergers.remove(leader)

                # now we have the leader group and all other groups
                #   are mergers to be merged into the leader group

                # merge:
                # (1) update dict: overwrite old groupnumbers to new leader groupnumber:
                for g_nr in mergers:  # mergers = group nrs
                    for merger_line_number in groups_i[g_nr]:
                        group_nr_for_line[merger_line_number] = leader

                # (2) put mergers into leader group AND
                leader_group = groups_i[leader]  # leader = group nr
                for g_nr in mergers:  # mergers = group nrs
                    merger_group_i = groups_i[g_nr]
                    leader_group.update(merger_group_i)
                    # (3) delete/empty/clear the merger groups
                    merger_group_i.clear()

        group_nr_for_lines[i] = group_nr_for_line

    return groups, cloudlines


# returns a per-ith-frame list containing pixel-coordinates, area and 
# x,y-coordinate of center of gravity of each cloud n. For example:
#   C[i][n][0] = [(x,y), ...];
#   C[i][n][1] = area;
#   C[i][n][2] = (cg_x_coo, cg_y_coo)
# largest area cloud at index n=0 in each frame i, where n = cloud_nr
def returns_sorted_cg_clouds(groups, cloudlines, frame_count):
    # clean-up groups[]:
    # remove empty sets() from groups[]:
    # always start at end of list when removing in-loop
    # {empty sets were left overs from group creation process in returns_groups_of_cloud_pixels}
    for i in range(frame_count):
        for n in range(len(groups[i])-1, -1, -1):
            if groups[i][n] == set():
                del groups[i][n]

    C = [[] for i in range(frame_count)]

    # puts coordinates, area, cg into C[]
    for frame_i, frame in enumerate(groups):
        for group in frame:
            coordinates = []
            area, sumx, sumy = 0, 0, 0

            for cloudline_nr in group:
                y = cloudlines[frame_i][cloudline_nr][2]
                X = cloudlines[frame_i][cloudline_nr][3]

                for x in X:
                    # area == pixelcount
                    area = area + 1
                    sumx = sumx + x
                    sumy = sumy + y
                    coordinates.append((x, y))

                # alternatively:
                # area = area + len(X)
                # sumx = sumx + sum(X) = sum(X, sumx)
                # sumy = sumy + len(X) * y

            # filter: ignore clouds with area <= IGNORE_AREA
            if area <= IGNORE_AREA:
                continue

            avgx = round(sumx / area)
            avgy = round(sumy / area)

            # data:
            area = area
            cg = (avgx, avgy)

            C[frame_i].append([coordinates, area, cg])

    ''' sorting C[] in order of cloud area '''
    # sort clouds in order of area: largest first:
    for i in range(frame_count):
        if len(C[i]) > 1:
            # C[i] = sorted(C[i], key=len, reverse=True)
            C[i] = sorted(C[i], key=lambda cloud: cloud[1], reverse=True)

    return C


# calculate average speeds of CG in x and y direction: vx, vy
# speed defined as change in x and y for CG in between two frames
# for this, one CG is used: the CG of the cloud with the largest area
# this will result in some faulty speeds, when there are multiple
# clouds with similar areas that switch number one positions in between
# frames. for this reason and others, results will be substantially filtered
def returns_vx_vy(C, frame_count):
    # use data only of largest cloud: in C[i][n] with n = 0:
    # C[i][0] == data for largest cloud in frame i
    n = 0

    # velocity is 2D-version of vx and vy, speed is magnitude of vx and vy combined
    velocities_n = []
    speeds_n = []

    # add frames velocities into array, starting with 2nd frame (index 1):
    velocities_n = []
    for i in range(1, frame_count):
        # vx is current x(i) - prev x(i-1)
        # same for y
        # # (!) old: problem with empty frames with no CG
        # vx = C[i][n][2][0] - C[i-1][n][2][0]
        # print(vx)
        # vy = C[i][n][2][1] - C[i-1][n][2][1]
        # print(vy)
        # (!) solution: only if 2 consequtive frames contain clouds and CG's then vx and vy will be calculated:
        if (len(C[i]) != 0 and len(C[i-1]) != 0):
            vx1 = C[i][n][2][0]
            vx0 = C[i-1][n][2][0]
            vx = vx1 - vx0
            
            vy1 = C[i][n][2][1]
            vy0 = C[i-1][n][2][1]
            vy = vy1 - vy0
        
            velocities_n.append((vx, vy))

    # append speeds (pythagoras on x and y coordinates of velocities)
    for v in velocities_n:
        speeds_n.append(round((v[0]**2 + v[1]**2)**.5, 1))

    # combine (speed, vx, vy) before sorting by speed:
    sv_n = [(speeds_n[i], velocities_n[i]) for i in range(len(speeds_n))]

    # sorting by speed (sv[_][0])
    sv_n = sorted(sv_n, key=lambda item: item[0], reverse=True)

    # print("checkpoint 0")  ##
    # check if there are enough speed data to continue
    if len(sv_n) < 1:
        print("not enough data, clouds will not move (1)")
        return 0, 0
    # print("checkpoint 1")  ##
    
    # filter data (1): delete speeds that are too high (due to highest
    # area cloud jumping positions)
    # speedlimit at 117kmh = 150px/h = 13px per frame of 5 minutes:
    for i in range(len(sv_n)-1, -1, -1):
        if sv_n[i][0] > 13:
            del sv_n[i]

    # filter data (2): sometimes cloud data can have similar speed, but
    # pointing in opposite direction: delete these values
    # get rid of spped vectors pointing wrong way:
    xposcount, xnegcount, yposcount, ynegcount = 0, 0, 0, 0
    for i in range(len(sv_n)-1, -1, -1):
        if sv_n[i][1][0] > 0:
            xposcount = xposcount + 1
        elif sv_n[i][1][0] < 0:
            xnegcount = xnegcount + 1

        if sv_n[i][1][1] > 0:
            yposcount = yposcount + 1
        elif sv_n[i][1][1] < 0:
            ynegcount = ynegcount + 1

    # positive x vel is dominant: delete all values with neg xvel:
    if xposcount > xnegcount:
        for i in range(len(sv_n)-1, -1, -1):
            if sv_n[i][1][0] < 0:
                del sv_n[i]
    # negative x vel is dominant: delete all values with pos xvel:
    elif xposcount < xnegcount:
        for i in range(len(sv_n)-1, -1, -1):
            if sv_n[i][1][0] > 0:
                del sv_n[i]

    # positive y vel is dominant: delete all values with neg yvel:
    if yposcount > ynegcount:
        for i in range(len(sv_n)-1, -1, -1):
            if sv_n[i][1][1] < 0:
                del sv_n[i]
    # negative y vel is dominant: delete all values with pos yvel:
    elif yposcount < ynegcount:
        for i in range(len(sv_n)-1, -1, -1):
            if sv_n[i][1][1] > 0:
                del sv_n[i]

    # check if there are enough data left after filtering
    if len(sv_n) < 1:
        print("not enough data, clouds will not move (2)")
        return 0, 0
    # print("checkpoint 2")  ##
    
    # # trim first and last "extreme" value:
    if len(sv_n) > 5:
        sv_n = sv_n[1:-1]

    # calculate average velocity:
    sumX, sumY = 0, 0
    L = len(sv_n)
    for i in range(L):
        sumX += sv_n[i][1][0]
        sumY += sv_n[i][1][1]

    # velocity: average speeds in x and y direction:
    vx, vy = (sumX / L, sumY / L)

    return vx, vy


# calculates the predicted movement of cloud-pixels for the next 60 minutes.
# with the last frame from clouds_L (im_last) as a starting point we move the cloud-pixels by vx and vy
# for the next 12*5-minute frames
# (from file fingerpaint-4.py or 6?)
# secondly, it also moves image border clouds linearly using velocity
# in other words: if a cloud moves away from the border, instead of leaving an abrubt gap in it's wake,
# cloud-pixels will be added according to the velocity vector
def translate_and_edges(im_last, vx, vy, frame_count):
    w, h = im_last.size

    # load background image
    with Image.open(BACKGROUND_FILE).convert("RGBA") as im:
        nl = im.copy()

    vx = round(vx)
    vy = round(vy)

    ''' (1) Move last frame with velocity (vx, vy) '''
    out = []
    for i in range(frame_count):
        left = 0 if vx >= 0 else (i+1) * -vx
        upper = 0 if vy >= 0 else (i+1) * -vy
        right = w - ((i+1) * vx) if vx >= 0 else w
        lower = h - ((i+1) * vy) if vy >= 0 else h

        cloud_i = im_last.copy()
        cloud_i = cloud_i.crop((left, upper, right, lower))

        left = (i+1) * vx if vx >= 0 else 0
        upper = (i+1) * vy if vy >= 0 else 0
        right = w if vx >= 0 else w - ((i+1) * -vx)
        lower = h if vy >= 0 else h - ((i+1) * -vy)

        # "box" b: An optional 4-tuple giving the region to paste into.
        # b = None
        b = (left, upper, right, lower)

        out_i = nl.copy()
        out_i.paste(cloud_i, box=b, mask=cloud_i)

        out.append(out_i)

    ''' (2) Adds out of frame lost edges '''
    # add clouds to empty spaces at edges: cloud-pixels will be added according to the velocity vector
    # notes 44-01;
    # from last frame (im_last) get edge pixels:

    cloudcol = (255, 255, 255, 255)
    emptycol = (0, 0, 0, 0)

    if vy > 0:
        # upper row where y = 0:
        r0 = [cloudcol if im_last.getpixel((x, 0)) == 255 else emptycol for x in range(0, w)]  # h exclusive

    if vy < 0:
        # lower row where y = h - 1:
        rh = [cloudcol if im_last.getpixel((x, h-1)) == 255 else emptycol for x in range(0, w)]  # h exclusive

    if vx > 0:
        # left column where x = 0:
        c0 = [cloudcol if im_last.getpixel((0, y)) == 255 else emptycol for y in range(0, h)]  # h exclusive

    if vx < 0:
        # right column where x = w - 1:
        cw = [cloudcol if im_last.getpixel((w-1, y)) == 255 else emptycol for y in range(0, h)]  # h exclusive

    if not vx == 0:
        a = vy / vx
    if not vy == 0:
        # a1 = a**(-1) # = vx / vy
        a1 = vx / vy

    # upper row r0 where y = 0:
    # r0 moving down y+ and right or left x+ x-
    if vy > 0:
        for i in range(frame_count):
            for y in range(0, vy * (i + 1)):  # frame 0 needs +1
                if vx == 0:
                    for x in range(0, w):
                        out[i].putpixel((x, y), r0[x])
                else:
                    # starting x position of where to start drawing r0:
                    xb, yb = 0, 0
                    b = yb - a * xb
                    # y = a * x + b linear equation with b determines from one point (xb, yb) through straight line
                    # >> x = a1*y -a1*b
                    ###### x0 = round(a1 * y - a1 * b)
                    x0 = int(a1 * y - a1 * b)  # int seems prettier: try eg: vy vx 400 100

                    if vx > 0:
                        # draw r0[0: w-1 - x0] at (x0, y0) with reduced length [0: w-x0]: trimmed right
                        n = 0
                        for x in range(x0, w):
                            # out[i].putpixel((x, y), r0[x - x0])
                            out[i].putpixel((x, y), r0[n])
                            n += 1
                    if vx < 0:
                        # draw r0[x0: w] at (x0, y0) with reduced length [x0: w]: trimmed left
                        n = abs(x0)
                        for x in range(0, w - abs(x0)):
                            # out[i].putpixel((x, y), r0[x - abs(x0)])
                            out[i].putpixel((x, y), r0[n])
                            n += 1

    # lower row rh where y = h:
    # rh moving up y- and right or left x+ x-
    if vy < 0:
        for i in range(frame_count):
            # y in range of height to y where original cloud frame borders
            for y in range(h-1, h-1 - abs(vy) * (i + 1), -1):  # frame 0 needs +1
                if vx == 0:
                    for x in range(0, w):
                        out[i].putpixel((x, y), rh[x])
                else:
                    # starting x position of where to start drawing rh:
                    xb, yb = 0, h-1
                    b = yb - a * xb
                    # y = a * x + b linear equation with b determines from one point (xb, yb) through straight line
                    # >> x = a1*y -a1*b
                    ###### x0 = round(a1 * y - a1 * b)
                    x0 = int(a1 * y - a1 * b)  # int seems prettier: try eg: vy vx 400 100

                    if vx > 0:
                        # draw rh[0: w-1 - x0] at (x0, y0) with reduced length
                        # use n to only get the necessary values from rh
                        n = 0
                        for x in range(x0, w):
                            # out[i].putpixel((x, y), r0[x - x0])
                            out[i].putpixel((x, y), rh[n])
                            n += 1
                    if vx < 0:
                        # draw rh[x0: w] at (x0, y0) with reduced length
                        n = abs(x0)
                        for x in range(0, w - abs(x0)):
                            # out[i].putpixel((x, y), r0[x - abs(x0)])
                            out[i].putpixel((x, y), rh[n])
                            n += 1

    # left column x = 0:
    # c0 moving right x+ and down or up y+ y-
    if vx > 0:
        for i in range(frame_count):
            # y in range of height to y where original cloud frame borders
            for x in range(0, vx * (i + 1)):  # frame 0 needs +1
                if vy == 0:
                    for y in range(0, h):
                        out[i].putpixel((x, y), c0[y])
                else:
                    # starting x position of where to start drawing c0:
                    xb, yb = 0, 0
                    b = yb - a * xb
                    # y = a * x + b linear equation with b determines from one point (xb, yb) through straight line
                    ###### x0 = round(a1 * y - a1 * b)
                    y0 = int(a * x + b)  # int seems prettier: try eg: vy vx 400 100

                    # right down movement
                    if vy > 0:
                        # draw c0[0: h-1 - y0] at (x0, y0) with reduced length
                        # use n to only get the necessary values from rh
                        n = 0
                        for y in range(y0, h):
                            out[i].putpixel((x, y), c0[n])
                            n += 1
                    # right up movement of left column
                    if vy < 0:
                        # draw rh[x0: w] at (x0, y0) with reduced length
                        n = abs(y0)
                        for y in range(0, h - abs(y0)):
                            # out[i].putpixel((x, y), r0[x - abs(x0)])
                            out[i].putpixel((x, y), c0[n])
                            n += 1

    # right column x = w-1:
    # cw moving left x- and down or up y+ y-
    if vx < 0:
        for i in range(frame_count):
            # y in range of height to y where original cloud frame borders
            for x in range(w-1, w-1 - abs(vx) * (i + 1), -1):  # frame 0 needs +1
                if vy == 0:
                    for y in range(0, h):
                        out[i].putpixel((x, y), cw[y])
                else:
                    # starting x position of where to start drawing rh:
                    xb, yb = w-1, 0
                    b = yb - a * xb
                    # y = a * x + b linear equation with b determines from one point (xb, yb) through straight line
                    # >> x = a1*y -a1*b
                    ###### x0 = round(a1 * y - a1 * b)
                    y0 = int(a * x + b)  # int seems prettier: try eg: vy vx 400 100

                    if vy > 0:
                        # draw rh[0: w-1 - x0] at (x0, y0) with reduced length
                        # use n to only get the necessary values from rh
                        n = 0
                        for y in range(y0, h):
                            # out[i].putpixel((x, y), r0[x - x0])
                            out[i].putpixel((x, y), cw[n])
                            n += 1
                    if vy < 0:
                        # draw rh[x0: w] at (x0, y0) with reduced length
                        n = abs(y0)
                        for y in range(0, w - abs(y0)):
                            # out[i].putpixel((x, y), cw[x - abs(y0)])
                            out[i].putpixel((x, y), cw[n])
                            n += 1

    out_final = []
    # paste results on NL_map.png
    for i in range(frame_count):
        temp = nl.copy()
        b = None
        # b = (left, upper, right, lower)
        temp.paste(out[i], box=b, mask=out[i])
        out_final.append(temp)

    return out_final


# adds footer text into each frame
# Returns nothing: directly modifies temp image
# requires: from PIL import Image, ImageFont, ImageDraw
def add_footer_text(im_list, frame_count):
    # select font, fontsize:
    font, font_size = FONT_FILE, 24
    footer_font = ImageFont.truetype(font, font_size)

    # get frame size:
    w, h = im_list[0].size

    # now add text to frames:
    for i in range(0, frame_count):
        temp = im_list[i]

        # format footer text contents:
        footer_text = f"+:{(i + 1) * 5:02}"

        # create helper array/im temp_draw object from temp image
        # to draw text from temp_draw into original temp
        # it changes the temp at the same time, just as with arrays
        # and helper arrays: the changes to helpers affect the original array
        # (!) will modify original object (temp)
        temp_draw = ImageDraw.Draw(temp)
        temp_draw.text((w - font_size * len(footer_text) / 2 - 2,
                        h - (3/4) * (font_size) - 2), footer_text, fill=(0, 0, 0, 255), font=footer_font)


# saves image frames list into a .gif with the right durations and in complete color
def save_list_to_file(im_list, file_name_save):
    # FILE_NAME_SAVE = f"{file_name_save}.gif"
    # FILE_NAME_SAVE = f"{file_name_save} - " + f"{FILE_NAME[:-4]}" + ".gif"
    FILE_NAME_SAVE = file_name_save
    # per-frame duration in [ms]:
    DURATION = [400 for i in range(0, 12 - 1)] + [1200]
    im_list[0].save(FILE_NAME_SAVE, save_all=True, append_images=im_list[1:], loop=0, duration=DURATION)
    
    print(f"saved image as:\t'{FILE_NAME_SAVE}'")


# see also "add_footer_text()"
# adds footer text into each frame for demo mode
def add_footer_text_negative(im_list, frame_count):
    # select font, fontsize:
    font, font_size = FONT_FILE, 24
    footer_font = ImageFont.truetype(font, font_size)

    # get frame size:
    w, h = im_list[0].size

    # now add text to frames:
    for i in range(0, frame_count):
        temp = im_list[i]

        # format footer text contents:
        if i != frame_count - 1:
            footer_text = f"-:{(55 - i * 5):02}"
        else:
            footer_text = f"+:{(55 - i * 5):02}"

        # create helper array/im temp_draw object from temp image
        # to draw text from temp_draw into original temp
        # it changes the temp at the same time, just as with arrays
        # and helper arrays: the changes to helpers affect the original array
        # (!) will modify original object (temp)
        temp_draw = ImageDraw.Draw(temp)
        temp_draw.text((w - font_size * len(footer_text) / 2 - 2,
                        h - (3/4) * (font_size) - 2), footer_text, fill=(0, 0, 0, 255), font=footer_font)


# executes main() and measures execution times
# from: "04-timeit-test.py"
def maintime():
    '''requires "import time"'''
    # before times:
    time_0_pc = time.perf_counter()
    time_0_pt = time.process_time()
    # function call:
    main()
    # Total time {including waits}:
    time_t_pc = time.perf_counter()
    delta_pc = time_t_pc - time_0_pc
    print(f"Grand Total : {delta_pc:.3f} [s]")
    # Pure process time:
    time_t_pt = time.process_time()
    delta_pt = time_t_pt - time_0_pt
    print(f"Process Time: {delta_pt:.3f} [s]")
    exit(0)


''' (!) the code hereafter is not currently used '''
''' uncomment lines 990-1089 if using any of its functions '''


# # plot all largest cloud cg coordinates for all frames in one plot: visualise movement
# # scatter-dot color is what code thinks is same cloud (eg. same dot color is "same" n'th largest cloud from different frames)
# # numbers refer to framenumber of cg's origin
# def plot_cgs(C, frame_count):
    # # N is number of largest area clouds to be displayed: eg N = 2 displays 2 clouds from each frame times number of frames
    # N = 12

    # colors = ['#8B0000', '#FF0000', '#FFA500', '#FFFF00', '#7CFC00', '#32CD32',
              # '#008000', '#00FFFF', '#0000FF', '#9400D3', '#4B0082', '#000000']

    # for n in range(N):
        # X = [C[i][n][2][0] for i in range(frame_count)]
        # Y = [C[i][n][2][1] for i in range(frame_count)]

        # # plt.plot(xx, yy, 'r*', label='cg movement over time')
        # # plt.plot(xx1, yy1, 'go', label='cg movement over time')
        # plt.scatter(X, Y, c=colors[n])

        # for i in range(frame_count):
            # s = f"{i:>3}"
            # # plt.annotate(s, (X[i], Y[i]), c=colors[i])
            # plt.annotate(s, (X[i], Y[i]), c='#000000') # black framenumber notations

    # # plt.xlim(0, w)
    # # plt.ylim(h, 0)
    # plt.show()


# # Plots a palette list with 256 RGB tuples
# # see commented lines "# plot_palette(im)"
# # see also: get_palette-3.py
# def plot_palette(im):
    # pal = im.getpalette()
    # if len(pal) != 256*3:
        # print("plot_palette(im): could not plot: length invalid:")
        # print(f"len(pal) = {len(pal)}")
        # return
    # # list of 256*3
    # l = [tuple((pal[i+0], pal[i+1], pal[i+2])) for i in range(0, len(pal), 3)]
    # # reshape to 16*16*3 for image display
    # if len(l) == 256:
        # # resize palette to 16*16 matrix
        # ''' fun plots to try '''
        # # l = [ [x for x in range(y, y + 16)] for y in range(0, 16) ]
        # # l = [ [x for x in range(y*16, y*16 + 16)] for y in range(0, 16) ]
        # l = [[l[x] for x in range(y*16, y*16 + 16)] for y in range(0, 16)]
    # # r = np.array(l)
    # # print(r.size) # size is number of elements, not x * y
    # # plot(r)
    # plot(l)


# # the plot command will halt the program flow until plot window is closed
# # requires: from matplotlib import pyplot as plt
# def plot(image):
    # plt.imshow(image, interpolation='nearest')
    # # figure title:
    # # plt.title("Title")
    # # window title:
    # fig = plt.gcf()
    # # fig.canvas.set_window_title('My title')
    # fig.canvas.set_window_title(str(image))
    # plt.show()


# # # (old simple version)
# # def plot(image):
    # # plt.imshow(image, interpolation='nearest')
    # # plt.show()


# # print dict-im.info's (k,v)-pairs alphabetically by key
# # im.info returns a dict
# # gif: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif
# def print_image_info(im):
    # for key in sorted(im.info.keys()):
        # print(f"im.info[{key:>10}] = {im.info[key]}")  # same as: '{:>10}'.format('test')
    # print()


# # extract A-channel from frames list and store in new list:
# # RETURNS: mode="1" list of frames that can serve as masks for the original list frames_RGBA
# def extract_A_from_RGBA(frames_RGBA):
    # # creates separate frames list where only A is stored a s 0-1 value ipv 0-255 value:
    # # method probably not required ...
    # '''FRAMES[] (RGBA) >> frames_A_mask (A): extract A-channel'''
    # # representing Alpha value
    # frames_A_mask = []

    # for frame in frames_RGBA:
        # temp = frame.copy()
        # # Returns an image in “L” mode:
        # A = temp.getchannel("A")
        # # Returns a converted copy of this image:
        # A_converted = A.convert(mode="1", dither=None)
        # # out = ImageMath.eval("convert(min(a, b), mode='1')", a=im1, b=im2) ??
        # frames_A_mask.append(A_converted)
        # # << a 1 bit mask per frame has been created and put into the list "frames_A_mask"

    # return frames_A_mask


''' main() runs from maintime() '''
maintime()
