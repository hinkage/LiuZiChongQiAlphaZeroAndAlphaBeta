# -*- coding: utf-8 -*-
"""
    @author 何江
    @date 2019/2/8 12:44
"""
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

class Button:
    """
    opengl的坐标是以左下点为原点,横向为x,纵向为y
    """
    def __init__(self, x, y, endx, endy, textureId):
        """
        用左下角和右上角两个点来定义一个button的位置
        :param x: 左下角点x坐标
        :param y: 左下角点y坐标
        :param endx: 右上角点x坐标
        :param endy: 右上角点y坐标
        :param keyInTextureIdDict: 在纹理字典中的key,用于渲染button
        """
        self.x = x
        self.y = y
        self.endx = endx
        self.endy = endy
        self.onClickListener = None
        self.textureId = textureId

    def setOnClickListener(self, callBack):
        self.onClickListener = callBack

    def doClick(self):
        if self.onClickListener:
            self.onClickListener()

    def click(self, pointerX, pointerY):
        """
        如果指针在button范围内,则调用点击回调函数
        :param pointerX:
        :param pointerY:
        :return:
        """
        if pointerX > self.x and pointerX < self.endx:
            if pointerY > self.y and pointerY < self.endy:
                self.doClick()

    def render(self):
        """
        渲染纹理
        :return:
        """
        if self.textureId:
            glBindTexture(GL_TEXTURE_2D, self.textureId)
            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 0.0)
            glVertex2f(self.x, self.y)
            glTexCoord2f(1.0, 0.0)
            glVertex2f(self.endx, self.y)
            glTexCoord2f(1.0, 1.0)
            glVertex2f(self.endx, self.endy)
            glTexCoord2f(0.0, 1.0)
            glVertex2f(self.x, self.endy)
            glEnd()

