# -*- coding: utf-8 -*-
"""
    @author 何江
    @date 2019/1/20 21:10
"""
import numpy
import sys
import array
from PIL import Image
import random
import matplotlib.pyplot as plt

try:
    from OpenGL.GLUT import *
    from OpenGL.GL import *
    from OpenGL.GLU import *
except:
    print(''' Error PyOpenGL not installed properly !!''')
    sys.exit()


class Texture(object):
    """Texture either loaded from a file or initialised with random colors."""
    def __init__(self):
        self.xSize, self.ySize = 0, 0
        self.rawRefence = None


class RandomTexture(Texture):
    """Image with random RGB values."""
    def __init__(self, xSizeP, ySizeP):
        self.xSize, self.ySize = xSizeP, ySizeP
        tmpList = [random.randint(0, 255) for i in range(3 * self.xSize * self.ySize)]
        # 'B': unsigned char in C
        self.textureArray = array.array('B', tmpList)
        self.rawReference = self.textureArray.tostring()


class FileTexture(Texture):
    """Texture loaded from a file."""
    def __init__(self, fileName):
        im = Image.open(fileName)
        self.xSize = im.size[0]
        self.ySize = im.size[1]
        self.rawReference = numpy.array(list(im.getdata()), numpy.uint8)
        plt.imshow(im)
        plt.show()

def display():
    """Glut display function."""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glColor3f(1, 1, 1)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 1 - 0.0)
    glVertex2f(0.0, 0.0)
    glTexCoord2f(1.0, 1 - 0.0)
    glVertex2f(250.0, 0.0)
    glTexCoord2f(1.0, 1 - 1.0)
    glVertex2f(250.0, 250.0)
    glTexCoord2f(0.0, 1 - 1.0)
    glVertex2f(0.0, 250.0)
    glEnd()
    glutSwapBuffers()


def init(fileName):
    """Glut init function."""
    try:
        texture = FileTexture(fileName)
    except:
        print('could not open', fileName, '; using random texture')
        texture = RandomTexture(256, 256)
    glClearColor(0, 0, 0, 0)
    glShadeModel(GL_SMOOTH)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, texture.xSize, texture.ySize, 0,
                 GL_RGB, GL_UNSIGNED_BYTE, texture.rawReference)
    glEnable(GL_TEXTURE_2D)


glutInit(sys.argv)
glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
glutInitWindowSize(250, 250)
glutInitWindowPosition(100, 100)
glutCreateWindow(sys.argv[0])
gluOrtho2D(0.0, 250, 0.0, 250)  # 定义剪裁面
if len(sys.argv) > 1:
    init(sys.argv[1])
else:
    init('D:/1VSProject/Python/LiuZiChongQiFinal/Demo/timg.jpg')
glutDisplayFunc(display)
glutMainLoop()
