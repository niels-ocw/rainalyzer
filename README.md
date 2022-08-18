# Rainalyzer
#### Video Demo:  <https://youtu.be/BXUVJ571rSg>
#### Description:
Using Python and Flask a rainfall prediction for the next 60 minutes is calculated and displayed in a webbrowser. For the meteriological source input data see the link provided on the web-interface.

#### Introduction:
Did you ever feel like you should have left ten minutes earlier to get your groceries on your bike? Well here's the solution for all your first world problems!

Freely available radar images from the Dutch Meteriological Institute ([KNMI](https://cdn.knmi.nl/knmi/map/page/weer/actueel-weer/neerslagradar/WWWRADAR_loop.gif)) are used to generate similar image-sequences for the next hour. This is done below the hood in Python, and a neat web-interface is available for the user that runs on Flask.

What you get is a browser window with two buttons and two images. The right button "Live Mode" will use actual precipitation data from KNMI to calculate the predictions for the next hour. The left button "Demo Mode" will use a random gif image from another day from the "demo-gifs" -folder. As it will not always be raining, this option allows the user to see what the program does independent of current weather.

#### Installation:
The program requires Python 3.

For installation Python offers the option to use virtual environments (venv). In this way the extra packages needed are installed locally and will not be permanently integrated into your system.

You will need the "requirements.txt" file from the project folder.

1. Open a Terminal window and navigate to the project folder. Create a virtual environment:

    ```$ python3 -m venv env```

    (will create a new folder)

2. You will now activate the venv by:

    ```$ source env/bin/activate```

3. In order to check if the previous step was done correctly you can now type:

    ```$ which python```

    This should give something like "/rainalyzer/env/bin/python" and **not** "/usr/bin/python"

4. Install the packages from the requirements:

    ```$ pip3 install -r requirements.txt```
    
    ```$ pip3 install --upgrade requests```

    Installation is now complete.

5. Deactivate the venv:

    ```$ deactivate```

6. In order to check if the previous step was done correctly you can now type:

    ```$ which python```

    This should give something like "/usr/bin/python" and **not** "/rainalyzer/env/bin/python"

#### Use:
How to run Rainalyzer using Flask and Python's venv:

1. Open Terminal in project folder
2. Activate venv and run application:

    ```$ source env/bin/activate && export FLASK_APP=application.py && flask run```

3. Open browser with provided link

How to quit:

1. In terminal window exit Flask server: [CTRL] + [C]

2. Quit browser window

Cleanup:

1. In project folder delete \static\radar_OUT-\*\*\*.gif files
This is not neccessary if you have enough harddisk space. There will be a maximum of 1000 temp files created.

#### Use as standalone:
The Python-part (995.py) can also be used stand-alone as you normally would any other Python program:

* Live-Mode:

    ```$ python3 rainalyzer.py```

* Demo-Mode:

    ```$ python3 rainalyzer.py demo```

Or, depending on your default Python version:

* Live-Mode:

    ```$ python rainalyzer.py```

* Demo-Mode:

    ```$ python rainalyzer.py demo```

####  Files and Folders:
This section explains the included project files and folders and what they are contain and do. Names in _italic_ might not be present initially.

Folders:

* demo-gifs:	contains 27 gifs used in "Demo-Mode" to demonstrate what Rainalyzer does in case there is no rain.
* _env_:	virtual environment folder created in installation
* _\_\_pycache\_\__:	created by Python after running Rainalyzer at least once
* static:	contains different files for Flask (see also under "Files")
* templates:	contains one file for Flask (see also under "Files")

Files:

* 995.py:	the main program that downloads and calculates the radar images and outputs the predictions
* 04b03.ttf:	font used for time stamps inside gif frames
* application.py:	Flask application
* glob.py:	contains global variables for use among 995.py and application.py
* requirements.txt:	used during installation; contains a list of all required packages
* how_to_run.txt: short-hand instructions on how to run the program

In folder "templates":

* index.html:	html sheet for Flask

In folder "static":

* styles.css:	styles sheet for Flask
* *.png:	map images used by 995.py and a 32x32 icon for the browser bar
* _radar*.gif_:	input and output radar images
* _rand_int.txt_:	stores last integer used for radar images


#### Program Flow:
##### The calculation part: 995.py
1. Using the requests library in Python a gif-file is downloaded from [KNMI](https://cdn.knmi.nl/knmi/map/page/weer/actueel-weer/neerslagradar/WWWRADAR_loop.gif) and saved locally.

2. Using the Python image processing library "Pillow" the gif is split into each of its twelve 5-minute frames.

3. From these frames text is removed and the rain data are separated from the map image. A list of colors was generated from an image from a rain-less day and these colors are subtracted from the frames. Gifs use one 8-bit unsigned integer (0 - 255) to refer to RGB tuples. A color list was generated once from a rain-less image and this list can be found at the top of the python program.

Now rain-data are separated into rain and no-rain pixels and we can do do some calculations: The goal to keep in mind is predicting movement of clouds in the next hour. For this some measure for velocity needs to be deduced from the frames: the movement of the area center (CG) of the cloud with the largest area across the frames.

In a step by step approach this looks as follows:

- Group neighboring pixels as clouds
- Take the average of x and y positions of all pixels in each cloud cloud (= coordinates of CG)
- Sort the CG's in each frame by area (= size)
- Mark the CG of the largest cloud in each frame
- Calculate the differences in position of this CG in between all 12 frames
- From this 11 in-between-frames velocities follow. (12 frames -> 11 differences)

That is ofcourse in an ideal cloud world. It is possible though that what is identified in code as the same cloud by area, is on fact a different cloud as we humans would perceive. Caused by multiple similarly sized clouds.

This would result in the CG jumping around in between frames. For this reason some filtering on the results is done with respect to:

- Removing lowest and highest values from the collection
- Removing values with a very different direction

Now that we are left with a list of a few velocities that are reasonable the average is calculated and used for the following steps:

- Get the real-world's last frame cloud pixels
- Move them in x and y for each frame per average speed
- Add pixels to the sides of clouds that move away from image edges

Finally the resulting cloud pixels are pasted onto a cloud-less map of the Netherlands and saved as a new gif using Pillow.

##### The user inerface: index.html and styles.css
The body of the html contains a table with two descriptions and two buttons. On the bottom row the input and output images are shown. Grey images are used on initially loading the page, showing that the main program has not yet run. This is done by pressing either the "Demo-Mode" or "Live-Mode" -buttons.

##### Flask: application.py
0. GET:
Sets the right images to be loaded: updates after post button push. Loads the "NL-grey.png" images initially or the "radar-IN" and "radar-OUT" after calculation.

1. POST:
Handles button presses which trigger running "python3 995.py". This creates the calculated images appended by a random integer stored in the "rand_int.txt" file. In this way the browser will be forced to reload the images. Else the browser will re-use cached images and it will seem like nothing is happening.


####  Design choices: / ideas
The following points discuss design choices and dealing with programming challenges.

1. For separating cloud-pixels from the background initially I was looking up the cloud-pixel colors, but depending on the amount of rain the pixels would have different shades of grey and red. The latter of which I didn't have the colors from until I would have a day of heavy rain. 

    Therefor I used an inverted solution to find the cloud pixels: I collected the colors from the gif-color-palette using Pillow. But now for a cloud-less sky (so only the green land-colors and blue water colors). These map-colors I then compared with the radar-image-frames to extract any non-clear-skies-colors. These are the same as cloud-colors.

2. Having used the Numpy-library initially, for processing the gif-frames, I switched to doing all work in Pillow. Though I was expecting Numpy-route to be the faster one, it was not. As an example processing the same image as a Numpy array took 110 seconds, while in Pillow it only took 5 seconds. I do not yet know why this was.

3. Working with gifs wasn't very "user-friendly". Getting to save and load them correctly took quite some time to figure out. To give an example one of the peculiarities was that when opening a gif the following frames only contained information about changed pixels and not complete frames.

    So I had to copy paste these per frame changed pixels onto all the previous frames. Iteratively this meant pasting the new last frame data onto the previous one consequtively.

4. Identifying what a cloud is, is probably the most important part of this program. After extracting the cloud pixels from frames the idea was to find the first cloud-pixel and determine if it had also-cloud neighboring pixels. Like on a checker board. Find the first white one, assign it a cloud number and also separately register that it was checked. Then for all new neighbours check if it has been registered yet, and then, check if it is a cloud pixel and neighboring. Continue until all pixels are registered.

    This kind of recursive approach though became somewhat messy and hard to understand. 

    So I switched to a more systematic approach: beginning at the upper left corner checking if a pixel is a cloud-pixel and adding each and all right-neighboring pixels that are cloud-pixels until they are not. Thus first analysing all rows. Calling these cloud lines.

    Secondly checking if each cloud-line has vertical neighbors and assigning them to new groups als clouds. This required some time to get right as a cloud-line in a next row can back-connect to a previously created cloudline.

    So to solve this when a neighboring pixel has a lower (earlier) cloud-number the current pixels inherit that previous number. 

5. Extracting the movement information from frames was challenging: When a cloud moves from one frame into the next, the trailing edge loses pixels and the leading edge gains pixels. The idea was to calculate a directional vector using the middle pixel of the trailing edge and pointing it towards the middle pixel of the leading edge. This would result in as many "wind-direction-vectors" as there were were clouds in the frames.

    Unfortunately clouds are a lot more messy than that idea. They merge, swirl, appear and disappear. 

    Then there's also the problem of how to identify the same cloud in between frames. Easy for the human eye, but harder to translate that into code.

    So I switched to a simpler approach: Using the CG (centre of gravity, or, middle pixel of an area: averaging both the x and y coordinates of all pixels in a cloud) of only the biggest cloud and ignoring smaller clouds. Also not all frames would have to be used. Just as long as there were enough frames to extract some data from.

6. For the user-experience just some Python-code was a little unimpressive I thought. So it seemed the quickest way to get some user-interface would be to use my knowledge from the 2020 web-track and use Flask. A little quirck that took some time to figure out was that a browser will not update a picture that you recalculate if it carries the same name (due to caching). So I added a random integer at the end. Which will fill up a harddrive. It's a work around that is not very charming, but it's possible to add a clean-up when the code finishes. 

7. The square shaped radar image has clouds moving across its borders into the visible frame. In order to not have those cross border clouds abrubtly end, extra pixels are added ont those clouds' trailing edges. This can be seen in some images and might look somewhat artificial. It was done so that locations under those trailing edges near map borders would not get false-negative rain predictions.
