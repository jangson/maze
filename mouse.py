
#-------------------------------------------------------------------------------
# Name:        mouse
# Purpose:     Micro mouse simulator
#
# Author:      hjkim
#
# Created:     05-06-2012
# Copyright:   (c) HyunJun Kim 2012. All Rights Reserved.
# Licence:     GPL 
#-------------------------------------------------------------------------------
# -*- coding: cp949 -*-

import  sys, os
import  time
from    array import *
from    math  import *
import  re
import  thread

import  wx
import  wx.lib.newevent
import  wx.lib.masked           as masked
import  wx.lib.rcsizer          as rcs

MOUSE_CMD_RUN       = 1
MOUSE_CMD_PAUSE     = 2
MOUSE_CMD_STOP      = 10
MOUSE_CMD_MOVE      = 20
MOUSE_CMD_TEST      = 1000

MOUSE_SIZE      = ( 60, 80 )
MOUSE_CENTER    = ( 30, 40 )
MOUSE_L_WHEEL   = ( 2, 40 )
MOUSE_R_WHEEL   = ( 58, 40 )

#---------------------------------------------------------------------------
# Mouse test dialog 
class TestDialog(wx.Dialog):
    def __init__(
        self, parent, ID=-1, title="Testing mouse", size=wx.DefaultSize, pos=wx.DefaultPosition, 
        style=wx.DEFAULT_DIALOG_STYLE,
        useMetal=False,
        ):
        wx.Dialog.__init__( self, parent, ID, title )

        print "mouse test"
        
#---------------------------------------------------------------------------
# Mouse 
class Mouse(wx.Window):
    def __init__(self, parent):
        self.m_Parent = parent
        
        self.m_Mouse = 0 
        self.m_MousePos = [ 0., 0. ]
        self.m_MousePosMM = [ 0., 0. ] 
        self.m_MouseSize = MOUSE_SIZE 
        self.m_MouseAngle = radians(0) 
        self.m_MouseCenter = MOUSE_CENTER
        self.m_MouseLWheel = MOUSE_L_WHEEL
        self.m_MouseLWheel = MOUSE_R_WHEEL

        self.m_MouseDistance = 0.
        self.m_MouseVelocityLeft = 0.
        self.m_MouseVelocityRight = 0.
        self.m_MouseDrawTime = 100.
        self.m_MouseCurrentTime = 0.

        self.LoadMouse ( 'mouse.png')


    def GetMouseSize ( self ):
        return self.m_MouseSize

    def SetMouseSize ( self, size ):
        self.m_MouseSize = size

    def GetMousePos ( self, pos ): 
        return self.m_MousePos

    def SetMousePos ( self, pos ): 
        self.m_MousePos = pos 

    def GetMousePosMM ( self, pos ): 
        return self.m_MousePosMM

    def SetMousePosMM ( self, pos ): 
        self.m_MousePosMM = pos 

    def LoadMouse ( self, filename ): 
        bmp = wx.Bitmap( filename )        
        self.m_Mouse = bmp.ConvertToImage()

    def GetScreenXY ( self, x, y ):
        return ( x, self.m_Parent.m_MaxH - y ) 

    def DrawMouse ( self, dc, margine = (0, 0) ) :
        img = self.m_Mouse
        img = img.Rotate(self.m_MouseAngle,wx.Point(self.m_MouseCenter [ 0 ], self.m_MouseCenter [ 1 ]))
        img.Rescale ( self.m_MouseSize [ 0 ], self.m_MouseSize [ 1 ] )
        bmp = img.ConvertToBitmap() 
        
        x = self.m_MousePosMM [ 0 ] - self.m_MouseSize [ 0 ] / 2
        y = self.m_MousePosMM [ 1 ] + self.m_MouseSize [ 1 ] / 2
        [ x, y ] = self.GetScreenXY ( x, y )
        dc.DrawBitmap ( bmp, x + margine [ 0 ], y + margine [ 1 ], True )   



    def MoveMouse ( self, move ):
        for m in move:
            wx.MilliSleep (100)
            self.SetMousePosMM ( ( m [ 0 ], m [ 1 ] ) )
            print m
            self.m_Parent.Refresh ()

    def MoveMouseDistance ( self, ldist, dist, timems ):
        pass

    def MoveMouseVelocity ( self, left, right, time ):
        pass

    def MoveMouseAcceleration ( self, left, right, time ):
        ( x, y ) = self.m_MousePosMM
        move = []

        for i in range ( 10 ):
            y = y + 10
            move.append ( ( x, y ) )

        self.MoveMouse ( move )

        # self.m_MouseDrawTime
        # time = self.m_MouseCurrentTime
# 
        # d = self.m_MouseDistance
        # vl = self.m_MouseVelocityLeft = 0.
        # vr = self.m_MouseVelocityRight = 0.

    def CommandMouse ( self, cmd ): 
        if cmd == MOUSE_CMD_RUN:
            print "mouse is running"
        elif cmd == MOUSE_CMD_PAUSE:
            print "mouse is pausing"
        elif cmd == MOUSE_CMD_STOP:
            print "mouse is stopping"
        elif cmd == MOUSE_CMD_TEST:
            print "mouse is stopping"
            self.MoveMouseAcceleration ( 10, 10, 10 )
            # dlg = TestDialog ( self.m_Parent )
            # dlg.ShowModal ()

    def OnPaint ( self, event ):
        print "Mouse: OnPaint"
        pass

