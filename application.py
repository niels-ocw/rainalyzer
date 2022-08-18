'''diff b2n redirect n render_template?'''
from flask import Flask, redirect, render_template, request
import glob
# from fun import DEMO, CALCULATE
# import calculate
import os

# Configure flask application
app = Flask(__name__)

# return render_template("index.html", loaded=loaded, image_load=image_load, image_load=f"{image_load}")
# return render_template("index.html", loaded=loaded, calculated=calculated)

# # DONE! >> redirect the user to homepage at route "/"
# return redirect("/")


@app.route("/", methods=["GET", "POST"])
def index():
    # initially on loading page, two grey images are shown:
    if request.method == "GET":
        # set the right images to be loaded: updates after post button push
        # set right images to be rendered to html:
        glob.image_current
        glob.image_future
        glob.loaded
        glob.calculated
        glob.mode
        glob.filename_random
        
        print(f"glob.loaded == {glob.loaded}, glob.calculated == {glob.calculated}, glob.filename_random == {glob.filename_random}")
        print(f"glob.image_current = {glob.image_current}, glob.image_future = {glob.image_future}")
        
        if glob.loaded:
            glob.image_current = f"static/radar_IN-{glob.filename_random}.gif"
        else:
            glob.image_current = "static/NL-grey.png"
        
        if glob.calculated:
            glob.image_future = f"static/radar_OUT-{glob.filename_random}.gif"
        else:
            glob.image_future = "static/NL-grey.png"
        
        print(f"glob.loaded == {glob.loaded}, glob.calculated == {glob.calculated}, glob.filename_random == {glob.filename_random}")
        print(f"glob.image_current = {glob.image_current}, glob.image_future = {glob.image_future}")
        
        # return render_template("index.html")
        # return render_template("index.html", loaded=loaded, calculated=calculated)
        image_current = str(glob.image_current)
        image_future = str(glob.image_future)
        return render_template("index.html", image_current=image_current, image_future=image_future)
        # return render_template("index.html", image_current="radar_IN.gif", image_future="radar_OUT.gif")

    elif request.method == "POST":
        button_pressed = request.form.get("button_pressed")
        print(button_pressed)
        
        glob.image_current
        glob.image_future
        glob.loaded
        glob.calculated
        glob.mode
        glob.filename_random
        
        if button_pressed == "demo_pressed":
            glob.mode = "demo"
            # calculate.main() # https://www.tutorialspoint.com/How-can-I-make-one-Python-file-run-another
            # execfile('calculate.py') // runfile
            os.system('python3 995.py demo')
            print(f"app: glob.filename_random == {glob.filename_random}")
            
            with open('static/rand_int.txt', 'r', encoding='utf-8') as f:
                #OR: open('82/test.txt', encoding = 'utf-8') >> 'r' is default
                contents = f.read()  # returns str
                glob.filename_random = contents
            
            print(f"ap2: glob.filename_random == {glob.filename_random}")
            
            glob.loaded = True
            glob.calculated = True
            return redirect("/")
        if button_pressed == "calculate_pressed":
            glob.mode = "calculate"
            os.system('python3 995.py')
            print(f"app: glob.filename_random == {glob.filename_random}")
            
            with open('static/rand_int.txt', 'r', encoding='utf-8') as f:
                #OR: open('82/test.txt', encoding = 'utf-8') >> 'r' is default
                contents = f.read()  # returns str
                glob.filename_random = contents
            
            print(f"ap2: glob.filename_random == {glob.filename_random}")
            
            glob.loaded = True
            glob.calculated = True
            return redirect("/")
        
    else:
        return "<h1>Something went wrong ...</h1>"
