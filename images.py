from PIL import Image
import sys
import os.path
import math

_filter = filter # saving default filter

def memoize(f):
    memo = {}
    def helper(*args):
        x = args[0]
        if x not in memo:
            memo[x] = f(*args)
        return memo[x]
    return helper

def filter(img, fltr, *options):
    filters = {'color', 'negative', 'contrast', 'monochrome', 'sepia', 'cel'}
    assert fltr in filters, "%s is not an acceptable filter" % fltr
    fltr = eval(fltr)
    image = Image.open(img)
    pixels = image.load()
    for i in range(image.size[0]):
        for j in range(image.size[1]):
            pixels[i,j] = fltr(pixels[i,j], *options)
    image.show()

@memoize
def sepia(px):
    # Apply microsoft's recommended algorithm for sepia tone
    inputRed, inputGreen, inputBlue = px[0], px[1], px[2]
    outputRed = (inputRed * .393) + (inputGreen *.769) + (inputBlue * .189)
    outputGreen = (inputRed * .349) + (inputGreen *.686) + (inputBlue * .168)
    outputBlue = (inputRed * .272) + (inputGreen *.534) + (inputBlue * .131)
    setInt255 = lambda x: min(255, int(x))
    output = tuple(map(setInt255, (outputRed, outputGreen, outputBlue)))
    return output

@memoize
def monochrome(px):
    # Apply another recommended algorithm for monochrome transformation
    inputRed, inputGreen, inputBlue = px[0], px[1], px[2]
    output = int(0.2989 * inputRed + 0.5870 * inputGreen+ 0.114 * inputBlue)
    return (output, output, output)

@memoize
def contrast(px, adj):
    # Adjust contrast
    factor = (259 * (int(adj) + 255)) / (255 * (259 - int(adj)))
    inputRed, inputGreen, inputBlue = px[0], px[1], px[2]
    outputRed   = int(factor * (inputRed - 128) + 128)
    outputGreen = int(factor * (inputGreen - 128) + 128)
    outputBlue  = int(factor * (inputBlue - 128) + 128)
    return (outputRed, outputGreen, outputBlue)

@memoize
def negative(px):
    # Get negative of image
    inputRed, inputGreen, inputBlue = px[0], px[1], px[2]
    output = 255 - px[0], 255 - px[1], 255 - px[2]
    return output

@memoize
def color(px, col):
    colors = {'red', 'green', 'blue', 'R', 'G', 'B'}
    assert col in colors, "%s is not an acceptable color" % col
    if col == 'red' or col == 'R':
        return px[0], 0, 0
    if col == 'green' or col == 'G':
        return 0, px[0], 0
    if col == 'blue' or col == 'B':
        return 0, 0, px[0]

@memoize
def cel(px, band_size):
    assert band_size, "Must specify band size"
    band = int(band_size)
    return tuple(map(lambda col: int((col//band) * band + band/2), px))

def crop(img, *options):
    image = Image.open(img)
    if options[0] in {'top', 'left', 'bottom', 'right'}:
        return crop_edge(image, options[0], int(options[1]))
    assert len(options) >= 2, 'Improper arguments to crop'
    right, bottom = image.size
    try:
        top, left = tuple(map(int, options[:2]))
        if len(options) >= 4:
            bottom, right = tuple(map(int, options[2:4]))
        return crop_points(image, (left, top), (right, bottom))
    except ValueError:
        "Values for top, left, bottom, right must be numerical"

def crop_edge(img, edge, amt):
    width, height = img.size
    if edge == 'right':
        return crop_points(img, (0, 0), (width-amt, height))
    if edge == 'bottom':
        return crop_points(img, (0, 0), (width, height-amt))
    if edge == 'left':
        return crop_points(img, (amt, 0), (width, height))
    if edge == 'top':
        return crop_points(img, (0, amt), (width, height))

def crop_points(img, lt, rb):
    assert lt[0] >= 0 and lt[1] >= 0, "Points must be non-negative"
    assert rb[0] <= img.size[0] and rb[1] <= img.size[1], \
        "Points outside of image range"
    assert rb[0] > lt[0] and rb[1] > lt[1], \
        "Right-bottom values must be greater than Left-top values"
    width, height = rb[0] - lt[0], rb[1] - lt[1]
    cropped = Image.new('RGB', (width, height), "black")
    width_offset, height_offset = lt
    old_pixels = img.load()
    new_pixels = cropped.load()
    for i in range(width):
        for j in range(height):
            new_pixels[i,j] = old_pixels[i+width_offset,j+height_offset]
    cropped.show()

def resize(img, *options):
    image = Image.open(img)
    if len(options) == 1 and options[0][0] == 'x':
        try:
            factor = float(options[0][1:])
            assert factor > 0, "scaling factor must be positive"
            width, height = tuple(map(lambda x:int(x*factor), image.size))
            return resize_img(image, width, height)
        except ValueError:
            "Single-argument resize must take the form: x[int]"
    try:
        height, width = tuple(map(int, options[:2]))
        return resize_img(image, width, height)
    except ValueError:
        "Values for height and width must be numerical"

def resize_img(img, new_width, new_height):
    curr_width, curr_height = img.size
    resized = Image.new('RGB', (new_width, new_height), "black")
    old_pixels = img.load()
    new_pixels = resized.load()
    width_ratio = curr_width/new_width
    height_ratio = curr_height/new_height
    for i in range(new_width):
        for j in range(new_height):
            i_new = math.floor(i * width_ratio)
            j_new = math.floor(j * height_ratio)
            new_pixels[i,j] = old_pixels[i_new,j_new]
    resized.show()

def main(action, img, *options):
    actions = {'filter', 'crop', 'resize'}
    assert action in actions, "%s is not an acceptable action" % action
    action = eval(action)
    return action(img, *options)

if __name__ == "__main__":
    assert len(sys.argv) >= 3, "Must specify an action and image"
    assert os.path.exists(sys.argv[2]), "Must specify an existing filename"
    main(*sys.argv[1:])
