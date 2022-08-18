'''For using global variables across modules'''
# https://www.edureka.co/community/52900/how-do-i-share-global-variables-across-modules-python

loaded, calculated = False, False
image_current, image_future = None, None
mode = None

# for the radar_IN-xxx and radar_OUT-xxx image files a random filename end is used
# to prevent browsers from re-using cached files and not updating to new image files
# this would result in no new image being displayed in the browser
# filename_random's value will be changed in 995.py
filename_random = "999"
