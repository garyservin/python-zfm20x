#!/usr/bin/python
import struct, random

# modified from http://pseentertainmentcorp.com/smf/index.php?topic=2034.0
palette = [[0x00, 0x00, 0x00, 0x00],
            [0x11, 0x11, 0x11, 0x00],
            [0x22, 0x22, 0x22, 0x00],
            [0x33, 0x33, 0x33, 0x00],
            [0x44, 0x44, 0x44, 0x00],
            [0x55, 0x55, 0x55, 0x00],
            [0x66, 0x66, 0x66, 0x00],
            [0x77, 0x77, 0x77, 0x00],
            [0x88, 0x88, 0x88, 0x00],
            [0x99, 0x99, 0x99, 0x00],
            [0xAA, 0xAA, 0xAA, 0x00],
            [0xBB, 0xBB, 0xBB, 0x00],
            [0xCC, 0xCC, 0xCC, 0x00],
            [0xDD, 0xDD, 0xDD, 0x00],
            [0xEE, 0xEE, 0xEE, 0x00],
            [0xFF, 0xFF, 0xFF, 0x00]]

# important values: offset, headerlength, width, height and colordepth
# This is for a Windows Version 3 DIB header
# You will likely want to customize the width and height
default_bmp_header = {'mn1':0x42,
                      'mn2':0x4D,
                      'filesize':0,
                      'undef1':0,
                      'undef2':0,
                      'offset':54,
                      'headerlength':40,
                      'width':200,
                      'height':200,
                      'colorplanes':1,
                      'colordepth':24,
                      'compression':0,
                      'imagesize':0,
                      'res_hor':0,
                      'res_vert':0,
                      'palette':0,
                      'importantcolors':0}

def bmp_write(header, pixels, filename):
    '''It takes a header (based on default_bmp_header), 
    the pixel data (from structs, as produced by get_color and row_padding),
    and writes it to filename'''
    header_str = ""
    header_str += struct.pack('<B', header['mn1'])
    header_str += struct.pack('<B', header['mn2'])
    header_str += struct.pack('<L', header['filesize'])
    header_str += struct.pack('<H', header['undef1'])
    header_str += struct.pack('<H', header['undef2'])
    header_str += struct.pack('<L', header['offset'])
    header_str += struct.pack('<L', header['headerlength'])
    header_str += struct.pack('<L', header['width'])
    header_str += struct.pack('<L', header['height'])
    header_str += struct.pack('<H', header['colorplanes'])
    header_str += struct.pack('<H', header['colordepth'])
    header_str += struct.pack('<L', header['compression'])
    header_str += struct.pack('<L', header['imagesize'])
    header_str += struct.pack('<L', header['res_hor'])
    header_str += struct.pack('<L', header['res_vert'])
    header_str += struct.pack('<L', header['palette'])
    header_str += struct.pack('<L', header['importantcolors'])
    palette_str = ""
    # load palette
    for color in palette:
        r = color[0]
        g = color[1]
        b = color[2]
        a = color[3]
        palette_str += struct.pack('<BBBB', r, g, b, a)
    #create the outfile
    outfile = open(filename, 'wb')
    #write the header + pixels
    outfile.write(header_str + palette_str + pixels)
    outfile.close()

def row_padding(width, colordepth):
    '''returns any necessary row padding'''
    byte_length = width*colordepth/8
    # how many bytes are needed to make byte_length evenly divisible by 4?
    padding = (4-byte_length)%4
    padbytes = ''
    for i in range(padding):
        x = struct.pack('<B',0)
        padbytes += x
    return padbytes

def pack_pixel(data):
    '''accepts values from 0-255 for each value, returns a packed string'''
    return struct.pack('<B',data)

def pack_color(red, green, blue):
    '''accepts values from 0-255 for each value, returns a packed string'''
    return struct.pack('<BBB',blue,green,red)

def pack_hex_color(hex_color):
    '''accepts RGB hex colors like '#ACE024', returns a packed string'''
    base = 16
    red = int(hex_color[1:3], base)
    green = int(hex_color[3:5], base)
    blue = int(hex_color[5:7], base)
    return pack_color(red, green, blue)

###################################
def hexToBMP(hexImg, fileName):
    header = default_bmp_header
    header["colordepth"] = 4
    header["palette"] = len(palette)
    header["offset"] = header["offset"] + (len(palette) * len(palette[0]))
    header["width"] = len(hexImg[0]) * (8 / header["colordepth"])
    header["height"] = len(hexImg)

    #Build the byte array.  This code takes the height
    #and width values from the dictionary above and
    #generates the pixels row by row.  The row_padding
    #stuff is necessary to ensure that the byte count for each
    #row is divisible by 4.  This is part of the specification.

    pixels = ''
    #for row in range(header['height']-1,-1,-1):# (BMPs are L to R from the bottom L row)
        #for column in range(header['width']):
    for row in reversed(hexImg):
        for column in row:
            pixels += pack_pixel(column)
    pixels += row_padding(header['width'], header['colordepth'])

    #call the bmp_write function with the
    #dictionary of header values and the
    #pixels as created above.

    bmp_write(header, pixels, fileName + ".bmp")
    return fileName + '.bmp'
