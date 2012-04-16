
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
from    scipy import integrate
import  re
import  thread

import  wx
import  wx.lib.newevent
import  wx.lib.masked           as masked
import  wx.lib.rcsizer          as rcs

USE_MOUSE_IMAGE = False
DRAW_MOUSE = True

MOUSE_CMD_RUN       = 1
MOUSE_CMD_PAUSE     = 2
MOUSE_CMD_STOP      = 10
MOUSE_CMD_MOVE      = 20
MOUSE_CMD_TEST      = 1000

MOUSE_SIZE      = ( 0.060, 0.080 )
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

g_r = 1   # using wheel velocity instead of angluar velocity v = w * r
g_vl0 = g_vr0 = 0.
g_al = g_ar = 0.
g_wl = 0.
g_angle = 0.

def GetAngle ( t ):
    vl0, vr0 = g_vl0, g_vr0
    al, ar  = g_al, g_ar
    wl  = g_wl 
    angle = (vr0 - vl0) / wl * t + ( ar - al ) / ( wl * 2 ) * t**2
    return angle 

def f_x ( t ):
    wl = ( g_vl0 + g_al * t ) / g_r
    wr = ( g_vr0 + g_ar * t ) / g_r
    angle = GetAngle (t)
    angle = angle + g_angle
    x = ( -g_r * sin ( angle ) / 2 ) * wl + ( -g_r * sin ( angle ) / 2 ) * wr
    return x

def f_y ( t ):
    wl = ( g_vl0 + g_al * t ) / g_r
    wr = ( g_vr0 + g_ar * t ) / g_r
    angle = GetAngle (t)
    angle = angle + g_angle
    y = (  g_r * cos ( angle ) / 2 ) * wl + (  g_r * cos ( angle ) / 2 ) * wr
    return y


class Mouse(wx.Window):
    def __init__(self, parent):
        self.m_Parent = parent
        self.Canvas = parent.Canvas

        # wheel and mouse size
        size = self.m_MouseSize = MOUSE_SIZE 
        self.wl = MOUSE_SIZE [ 0 ]

        # mouse velocity and acceleration
        self.vl = self.vr = 0.
        self.sl = self.sr = 0.

        # mouse position and angle 
        self.pc = [ 0., 0. ] 
        self.angle = radians ( 0. )

        # draw time 
        self.starttime = 0.
        self.currtime = 0.
        self.drawtime = 0.04
        self.drawedtime = 0.0

        # draw time 
        self.block = 0.180
        self.poll = 0.012

        self.m_MouseRoute = []
        self.m_MousePoly = None
        self.m_MouseImage = None
        self.m_MouseObject = None
        self.LoadMouseImage ()

    def LoadMouseImage ( self, filename = "mouse.png" ):
        size = self.m_MouseSize 
        bmp = wx.Bitmap( filename )        
        img = bmp.ConvertToImage()
        self.m_MouseImage = img 

    def InitMouse(self):
        self.m_MousePoly = None
        self.m_MouseObject = None

    def SetMouse(self, pos, angle):
        Canvas = self.Canvas
        if self.m_MousePoly:
            Canvas.RemoveObject ( self.m_MousePoly )
            self.m_MousePoly = None
            
        if self.m_MouseObject:
            Canvas.RemoveObject ( self.m_MouseObject )
            self.m_MouseObject = None

        if self.m_MouseRoute:
            for objs in self.m_MouseRoute:
                for obj in objs:
                    Canvas.RemoveObject ( obj )
            self.m_MouseRoute = []

        self.pc = self.position = pos
        self.vl = 0.
        self.vr = 0.
        self.angle = radians ( 0. )
        self.DrawMouse ( self.pc, self.angle, color = 'White' )

    def Run(self):
        block = self.block
        self.currtime = self.starttime = self.drawdtime = time.time ()

        self.MoveWithAccelDistance ( 10, block/2 + block*5 )
        self.MoveTurn90 ( -90 )
        self.MoveWithAccelDistance ( 0, block*4 )
        self.MoveWithVelocityDistance  ( 0, block/2 )


    ########################################################################
    # Methods for draw mouse 
    ########################################################################
    def DrawMouse ( self, pc, angle, redraw = True, color = 'White' ):
        Canvas = self.Canvas
        (mw, mh) = self.m_MouseSize
        
        pl = self.MovePoint ( pc, self.wl/2, angle + radians ( 90 ) )
        pr = self.MovePoint ( pc, self.wl/2, angle - radians ( 90 ) )

        if DRAW_MOUSE:
            if USE_MOUSE_IMAGE: 
                self.DrawMouseImage( pc, angle, redraw )
            else:
                mf = self.MovePoint ( pc, mh/2, angle )
                ml = self.MovePoint ( pc, mw/2, angle + radians ( 90 ) )
                mr = self.MovePoint ( pc, mw/2, angle - radians ( 90 ) )
                mb1 = self.MovePoint ( ml, mw/2, angle + radians ( 180 ) )
                mb2 = self.MovePoint ( mr, mw/2, angle + radians ( 180 ) )
                points = (mf, ml, mb1, mb2, mr)

                if not self.m_MousePoly:
                    self.m_MousePoly = Canvas.AddPolygon( 
                                    points, 
                                    LineWidth = 2, 
                                    LineColor = "Blue", 
                                    FillColor = "Blue",
                                    FillStyle = 'Solid',
                                    InForeground = True)                            
                else:
                    self.m_MousePoly.SetPoints( points )

        obj1 = Canvas.AddPoint(pc, color, Diameter = 2, InForeground = True)
        obj2 = Canvas.AddPoint(pl, 'Pink', Diameter = 2, InForeground = True)
        obj3 = Canvas.AddPoint(pr, 'Red', Diameter = 2, InForeground = True)
        self.m_MouseRoute.append( (obj1, obj2, obj3) )

        if redraw:
            Canvas.Draw ()

    def DrawMouseImage( self, pos, angle, redraw = True ):

        img = self.m_MouseImage
        if not img:
            return

        size = self.m_MouseSize 
        obj = self.m_MouseObject

        if angle != self.m_MouseAngle:
            img = img.Rotate ( angle, pos )
            self.m_MouseAngle = angle
            if obj: 
                self.Canvas.RemoveObject ( obj )
                obj = None

        bmp = img.ConvertToBitmap() 
        if not obj:
            obj = self.m_MouseObject = self.Canvas.AddScaledBitmap ( bmp, pos, Height = size [ 1 ], Position = "cc", InForeground = True)
        else:
            obj.SetPoint ( pos )

        if redraw:
            self.Canvas.Draw ( )


    ########################################################################
    # Methods for mouse movement 
    ########################################################################
    def GetS ( self, al, ar, t ):
        sl0 = self.sl
        sr0 = self.sr
        vl0 = self.vl
        vr0 = self.vr

        sl = vl0 * t + 0.5 * al * t ** 2
        sr = vr0 * t + 0.5 * ar * t ** 2
        return ( sl, sr )

    def GetV ( self, al, ar, t ):
        vl0 = self.vl
        vr0 = self.vr

        vl = vl0 + al * t
        vr = vr0 + ar * t
        return ( vl, vr )

    def GetAngle ( self, al, ar, t ):
        vl0 = self.vl
        vr0 = self.vr
        wl  = self.wl
        angle = (vr0 - vl0) / wl * t + ( ar - al ) / ( wl * 2 ) * t**2
        return angle 

    def MovePoint ( self, p, l, angle ):
        ( x, y ) = p
        xo = x - l * sin ( angle )
        yo = y + l * cos ( angle )
        return ( xo, yo )

    def GetMove ( self, al, ar, t ):
        angle = self.GetAngle ( al, ar, t )
        ( x, error ) = integrate.quad ( f_x, 0, t )
        ( y, error ) = integrate.quad ( f_y, 0, t )
        return ( x, y, angle )

    def Move ( self, al, ar, dt ):
        global g_vl0, g_vr0, g_al, g_ar, g_wl, g_angle
        g_wl = self.wl
        g_vl0, g_vr0 = self.vl, self.vr
        g_al, g_ar = al, ar
        g_angle = self.angle

        currtime = self.currtime 
        deltadraw = self.drawtime
        while True:
            drawtime = self.drawedtime + deltadraw 
            if drawtime <= currtime + dt :
                if drawtime < currtime:
                    drawtime = currtime

                ( x, y, angle ) = self.GetMove ( al, ar, drawtime - currtime )
                angle = self.angle + angle
                pc = ( self.pc [ 0 ]  + x  , self.pc [ 1 ] + y )
                    
                realtime = time.time ()
                if drawtime > realtime:
                    time.sleep ( drawtime - realtime )

                self.drawedtime = drawtime
                self.DrawMouse( pc, angle, 'Green' )
            else:
                break

        # Updated status
        ( x, y, angle ) = self.GetMove ( al, ar, dt )
        angle = self.angle + angle
        pc = ( self.pc [ 0 ]  + x  , self.pc [ 1 ] + y )
        ( vl, vr ) = self.GetV ( al, ar, dt )
        ( sl, sr ) = self.GetS ( al, ar, dt )

        self.pc = pc
        self.angle = angle
        ( self.vl, self.vr ) = ( vl, vr )
        ( self.sl, self.sr ) = ( sl, sr )
        self.currtime = self.currtime + dt

        self.DrawMouse( pc, angle, 'Green' )
        print "RT/T=%.3f,%.3f, AG=%.3f,%.3f, VL/VR=%.3f,%.3f, SL/SR=%.3f,%.3f" % ( 
                time.time ()-self.starttime, 
                self.currtime - self.starttime, 
                self.angle,
                degrees ( self.angle ),
                self.vl, self.vr, 
                self.sl * 1000, self.sr * 1000 )

    def GetTimeWithAccel ( self, a, s, v0 ):
        if a == 0:
            t = s / v0
        else:
            t = ( -2 * v0 + sqrt( (2*v0)**2 + 8*a*s ) ) / ( 2 * a )
        return t

    def GetAccelWithTime ( self, t, s, v0 ):
        a = ( s - v0 * t ) * 2. / ( t**2. )
        return a

    def GetAccelWithVelocity ( self, s, v, v0 ):
        a = ( v ** 2 - v0 ** 2 ) / ( 2 * s )
        return a 

    def MoveWithTimeDistance ( self, t, s ):
        a = self.GetAccelWithTime ( t, s, self.vl ) 
        self.Move ( a, a, t) 

    def MoveWithAccelDistance ( self, a, s ):
        t = self.GetTimeWithAccel ( abs(a), s, self.vl ) 
        self.Move ( a, a, t) 

    def MoveWithVelocityDistance ( self, v, s ):
        v0 = self.vl
        a = self.GetAccelWithVelocity ( s, v, v0 ) 
        t = ( v - v0 ) / a
        self.Move ( a, a, t) 
        
    def MoveTurn90 ( self, angle ):
        # al = - ar
        # when sr = r * angle in right turn ( r = turn diameter )
        v0 = self.vl
        wl = self.wl
        r = ( self.block - self.wl ) / 2
        half_angle = radians ( abs ( angle ) ) / 2
        t = r * half_angle / v0 * 1.6041958
        a = 2 * wl * half_angle / ( t ** 2 ) 
        a = a / 2
        if angle < 0:
            al, ar = a, -a
        else:
            al, ar = -a, a

        self.Move ( al, ar, t) 
        self.Move ( -al, -ar, t) 

