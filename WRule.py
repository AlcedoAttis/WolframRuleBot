import numpy as np
from requests import post as rqp
from json import loads
from PIL import Image
from instabot import Bot
import time
import sys

draft = True


def rule_generation():
    # return 2229223812056 // makes an ABACABA pattern
    return np.random.randint(0, 7625597484987)


def setup_generation():
    width = 160
    height = 1080
    inits = np.random.randint(0, 3, size=width)
    return {'pixel_factor': 2, 'width': width, 'height': height, 'initial_cond': inits}


def interesting(world):
    # If something converges, then it can be interesting, but not if in the first few lines
    checked_height = len(world)//2

    # rules with only 1 or 2 colors in the are not interesting
    if set(world[checked_height:].flatten('A')) < {0, 1, 2}:
        return False

    # rules which just move and dont change the rows are also not interesting
    pattern = world[checked_height+1][1:-2]  # cut edges off
    for i in range(3):  # offset (kinda)
        if np.array_equal(world[checked_height][i:-3+i], pattern):
            return False

    return True


# Yeah this is just the 3-color 3-wide case, but thats good enough, Herbert has a more general one
def wolfram_rule(draft, pixel_factor, width, height, initial_cond):
    # create rule-canvas and set up inital conditions
    world = np.empty(shape=(height, width), dtype="b")
    world[0] = initial_cond
    # load a colorscheme from colormind.io
    try:
        colors = loads(rqp("http://colormind.io/api/", '{"model":"default"}').text)['result'][::2][:3]
        pixels = [Image.new('RGB', (pixel_factor, pixel_factor), tuple(color)) for color in colors]
    except Exception:
        print('We probably overused the API of the color generator. :C')
        sys.exit("no color API answer")

    while True:
        # get rule to follow
        rule = rule_generation()

        # create a list of all subrules the rule encapsulates
        subrules = np.vectorize(lambda num, index: (num % 3**(index+1))//3**index)(rule, np.array(range(3**3)))

        def step(index, array, array_length):
            # get the next state from the subrules array with the currently needed subrules
            return subrules[3*3*array[index-1]+3*array[index]+array[1+index-array_length]]

        # apply the rule over the array
        inner_length = len(world[0])
        for index_outer in range(1, len(world)):
            for index_inner in range(inner_length):
                world[index_outer][index_inner] = step(index_inner, world[index_outer-1], inner_length)

        # disallows boring rules
        if interesting(world):
            break

    img_out = Image.new('RGB', (width*pixel_factor, height*pixel_factor))
    for y, row in enumerate(world):
        for x, color in enumerate(row):
            img_out.paste(pixels[color], (x*pixel_factor, y*pixel_factor))

    if draft:
        print(rule)
        img_out.show()

    return img_out, rule


def post(draft, username, password, rule):
    if draft:
        return True
    bot = Bot()
    bot.login(username=username, password=password)
    worked = bot.upload_photo('temporary.png', caption="Rule: {0}".format(rule))
    bot.logout()
    return worked


# Generation
img, rule = wolfram_rule(draft, **setup_generation())
img.save('temporary.png', "PNG")
# Posting
while not post(draft, username="here username", password="here password", rule=rule):
    time.sleep(60)  # Idk why, aber manchmal machen die requests nen 500 error, hoffentlich liegts nich am bild
