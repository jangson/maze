# -*- coding: cp949 -*-
# Copyright 2011 HyunJun Kim. All Rights Reserved.

"""Files and directories searching utility.
This program display result in window and depend on wxPython.
"""
import  sys, os
import  time
import  threading
from    math  import *
from    scipy import integrate
import  wx.lib.masked           as masked

import  wx

try:
    from floatcanvas import NavCanvas, FloatCanvas, Resources
except ImportError: # if it's not there locally, try the wxPython lib.
    from wx.lib.floatcanvas import NavCanvas, FloatCanvas, Resources
import wx.lib.colourdb
import time, random

DRAW_MOUSE = True
USE_MOUSE_IMAGE = False

#---------------------------------------------------------------------------
frame_size_x = 640
frame_size_y = 640
class AppFrame(wx.Frame):
    
    def __init__(self, parent, title):
        # create frame
        frame = wx.Frame.__init__(self, parent, -1, title, size=(frame_size_x, frame_size_y))

        self.MazeClassic = 1

        # create status bar
        self.m_status = self.CreateStatusBar(1)

        sizer = wx.BoxSizer ( wx.VERTICAL )

        bs = wx.BoxSizer ( wx.HORIZONTAL )
        b = wx.Button ( self, 1, "Init Classic" )
        self.Bind(wx.EVT_BUTTON, self.OnInitClassic, b)
        bs.Add ( b, 0, wx.ALIGN_LEFT )

        b = wx.Button ( self, 2, "Init Half" )
        self.Bind(wx.EVT_BUTTON, self.OnInitHalf, b)
        bs.Add ( b, 0, wx.ALIGN_LEFT )

        b = wx.Button ( self, 3, "Turn L90" )
        self.Bind(wx.EVT_BUTTON, self.OnBtn3, b)
        bs.Add ( b, 0, wx.ALIGN_LEFT )

        b = wx.Button ( self, 4, "Turn R90" )
        self.Bind(wx.EVT_BUTTON, self.OnBtn4, b)
        bs.Add ( b, 0, wx.ALIGN_LEFT )

        b = wx.Button ( self, 5, "None" )
        self.Bind(wx.EVT_BUTTON, self.OnBtn5, b)
        bs.Add ( b, 0, wx.ALIGN_LEFT )

        b = wx.Button ( self, 6, "None" )
        self.Bind(wx.EVT_BUTTON, self.OnBtn6, b)
        bs.Add ( b, 0, wx.ALIGN_LEFT )

        sizer.Add ( bs, 0, wx.ALIGN_TOP )

        bs = wx.BoxSizer ( wx.HORIZONTAL )
        b = wx.Button ( self, 20, "N->45" )
        self.Bind(wx.EVT_BUTTON, self.OnBtn45, b)
        bs.Add ( b, 0, wx.ALIGN_LEFT )

        b = wx.Button ( self, 21, "N->90" )
        self.Bind(wx.EVT_BUTTON, self.OnBtn90, b)
        bs.Add ( b, 0, wx.ALIGN_LEFT )

        b = wx.Button ( self, 22, "N->135" )
        self.Bind(wx.EVT_BUTTON, self.OnBtn135, b)
        bs.Add ( b, 0, wx.ALIGN_LEFT )

        b = wx.Button ( self, 23, "N->180" )
        self.Bind(wx.EVT_BUTTON, self.OnBtn180, b)
        bs.Add ( b, 0, wx.ALIGN_LEFT )

        sizer.Add ( bs, 0, wx.ALIGN_TOP )

        bs = wx.BoxSizer ( wx.HORIZONTAL )
        b = wx.Button ( self, 30, "D->45" )
        self.Bind(wx.EVT_BUTTON, self.OnBtnDiagTo45, b)
        bs.Add ( b, 0, wx.ALIGN_LEFT )

        b = wx.Button ( self, 31, "D->90" )
        self.Bind(wx.EVT_BUTTON, self.OnBtnDiagTo90, b)
        bs.Add ( b, 0, wx.ALIGN_LEFT )

        b = wx.Button ( self, 32, "D->135" )
        self.Bind(wx.EVT_BUTTON, self.OnBtnDiagTo135, b)
        bs.Add ( b, 0, wx.ALIGN_LEFT )

        sizer.Add ( bs, 0, wx.ALIGN_TOP )

        bs = wx.BoxSizer ( wx.HORIZONTAL )
        e = self.e1 = masked.Ctrl( self, integerWidth=1, fractionWidth=10, controlType=masked.controlTypes.NUMBER )
        bs.Add ( e, 0, wx.ALIGN_LEFT )
        e = self.e2 = masked.Ctrl( self, integerWidth=1, fractionWidth=10, controlType=masked.controlTypes.NUMBER )
        bs.Add ( e, 0, wx.ALIGN_LEFT )
        e = self.e3 = masked.Ctrl( self, integerWidth=1, fractionWidth=10, controlType=masked.controlTypes.NUMBER )
        bs.Add ( e, 0, wx.ALIGN_LEFT )

        sizer.Add ( bs, 0, wx.ALIGN_TOP )

        # Add the Canvas
        NC = NavCanvas.NavCanvas(self,
                                 Debug = 0,
                                 BackgroundColor = "Black")

        self.Canvas = NC.Canvas 
        sizer.Add ( NC, 1, wx.EXPAND )

        self.SetSizer ( sizer )

    def DrawBlock ( self ):
        Canvas = self.Canvas
        block = self.block
        poll = self.poll

        for y in range ( 8 ):
            for x in range ( 8 ):
                xy = ( x * block, y * block )
                size = ( block-poll, block-poll)
                Canvas.AddRectangle( xy, size, LineWidth = 1, LineColor = 'Gray')

        dmax = block * 8 - poll/2
        for d in range ( 8 ):
            d1 = d * block
            d2 = d * block + block / 2 - poll / 2
            d3 = d * block + block - poll * 2 
            d4 = d * block + block - poll

            pos21,pos22 = ( d2, 0 ), ( d2, dmax )
            Canvas.AddLine( ( pos21, pos22 ), LineWidth = 1, LineColor = 'Gray')
            pos21,pos22 = ( 0, d2 ), ( dmax, d2 )
            Canvas.AddLine( ( pos21, pos22 ), LineWidth = 1, LineColor = 'Gray')

            pos11,pos12 = ( d1+poll/2, -poll/2 ), ( -poll/2, d1+poll/2 )
            pos21,pos22 = ( d2, -poll/2 ), ( -poll/2, d2 )
            pos31,pos32 = ( d3+poll/2, -poll/2 ), ( -poll/2, d3+poll/2 )
            pos41,pos42 = ( d4+poll/2, -poll/2 ), ( -poll/2, d4+poll/2 )
            Canvas.AddLine( ( pos11, pos12 ), LineWidth = 1, LineColor = 'Gray')
            Canvas.AddLine( ( pos21, pos22 ), LineWidth = 1, LineColor = 'Gray')
            Canvas.AddLine( ( pos31, pos32 ), LineWidth = 1, LineColor = 'Gray')
            Canvas.AddLine( ( pos41, pos42 ), LineWidth = 1, LineColor = 'Gray')
            pos11,pos12 = ( d1+poll/2, dmax ), ( dmax, d1+poll/2 )
            pos21,pos22 = ( d2, dmax ), ( dmax, d2 )
            pos31,pos32 = ( d3+poll/2, dmax ), ( dmax, d3+poll/2 )
            pos41,pos42 = ( d4+poll/2, dmax ), ( dmax, d4+poll/2 )
            Canvas.AddLine( ( pos11, pos12 ), LineWidth = 1, LineColor = 'Gray')
            Canvas.AddLine( ( pos21, pos22 ), LineWidth = 1, LineColor = 'Gray')
            Canvas.AddLine( ( pos31, pos32 ), LineWidth = 1, LineColor = 'Gray')
            Canvas.AddLine( ( pos41, pos42 ), LineWidth = 1, LineColor = 'Gray')

            pos11,pos12 = ( -poll/2 , d1+poll/2),  ( dmax-d1-poll, dmax )
            pos21,pos22 = ( -poll/2 , d2),  ( dmax-d2-poll/2, dmax )
            pos31,pos32 = ( -poll/2 , d3+poll/2),  ( dmax-d3-poll, dmax )
            pos41,pos42 = ( -poll/2 , d4+poll/2),  ( dmax-d4-poll, dmax )
            Canvas.AddLine( ( pos11, pos12 ), LineWidth = 1, LineColor = 'Gray')
            Canvas.AddLine( ( pos21, pos22 ), LineWidth = 1, LineColor = 'Gray')
            Canvas.AddLine( ( pos31, pos32 ), LineWidth = 1, LineColor = 'Gray')
            Canvas.AddLine( ( pos41, pos42 ), LineWidth = 1, LineColor = 'Gray')
            pos11,pos12 = ( dmax, d1+poll/2), ( dmax-d1-poll, -poll/2 )
            pos21,pos22 = ( dmax, d2), ( dmax-d2-poll/2, -poll/2 )
            pos31,pos32 = ( dmax, d3+poll/2), ( dmax-d3-poll, -poll/2 )
            pos41,pos42 = ( dmax, d4+poll/2), ( dmax-d4-poll, -poll/2 )
            Canvas.AddLine( ( pos11, pos12 ), LineWidth = 1, LineColor = 'Gray')
            Canvas.AddLine( ( pos21, pos22 ), LineWidth = 1, LineColor = 'Gray')
            Canvas.AddLine( ( pos31, pos32 ), LineWidth = 1, LineColor = 'Gray')
            Canvas.AddLine( ( pos41, pos42 ), LineWidth = 1, LineColor = 'Gray')

    def InitEnv ( self, xy = None, angle = None ):
        #-----------------------------------
        if self.MazeClassic :
            print("classic")
            MOUSE_WHEEL_WIDTH = 0.060
            MOUSE_WIDTH = 0.060
            MOUSE_HEIGHT = 0.070
            MAZE_BLOCK = 0.18
            MAZE_POLL = 0.012
        else:
            print("half")
            MOUSE_WHEEL_WIDTH = 0.030
            MOUSE_WIDTH = 0.030
            MOUSE_HEIGHT = 0.035
            MAZE_BLOCK = 0.09
            MAZE_POLL = 0.006

        self.block = MAZE_BLOCK
        self.poll = MAZE_POLL

        self.wl = MOUSE_WHEEL_WIDTH
        self.mw = MOUSE_WIDTH
        self.mh = MOUSE_HEIGHT

        self.vl = self.vr = 0.
        self.sl = self.sr = 0.

        w = self.wl
        block = self.block
        poll = self.poll
        if not xy:
            x, y = block * 3 + (block-poll)/2, block * 0 + ( block-poll ) /2 
        else:
            ( x, y ) = xy

        self.pc = ( x, y )
        self.pl = ( x - (w/2 ), y )
        self.pr = ( x + (w/2 ), y )
        if not angle:
            self.angle = radians ( 0. )
        else:
            self.angle = angle

        self.starttime = 0.
        self.currtime = 0.
        self.drawtime = 0.02
        self.drawedtime = 0.00

        Canvas = self.Canvas
        if self.m_MousePoints:
            for obj in self.m_MousePoints:
                Canvas.RemoveObject ( obj )

        self.m_MousePoints = []

        self.DrawMouse( self.pc, self.angle )

    def OnInit ( self ):
        Canvas = self.Canvas
        self.m_MousePoly = None
        self.m_MousePoints = []

        Canvas.InitAll ()
        self.InitEnv ()
        self.DrawBlock ()
        self.Canvas.ZoomToBB()
        
    def OnInitClassic ( self, evt = None ):
        self.MazeClassic = 1
        self.OnInit ()

    def OnInitHalf ( self, evt = None ):
        self.MazeClassic = 0
        self.OnInit ()

    def LoadMouseImage ( self, filename = "mouse.png" ):
        size = self.m_MouseSize 
        bmp = wx.Bitmap( filename )        
        img = bmp.ConvertToImage()
        # img.Rescale ( size [ 0 ] , size [ 1 ] )
        return img 

    def DrawMouse ( self, pc, angle, color = 'Blue' ):
        Canvas = self.Canvas

        pl = self.MovePoint ( pc, self.wl/2, angle + radians ( 90 ) )
        pr = self.MovePoint ( pc, self.wl/2, angle - radians ( 90 ) )

        if DRAW_MOUSE:
            if USE_MOUSE_IMAGE: 
                obj = self.m_MouseObject
                if obj:
                    Canvas.RemoveObject ( obj )
                    obj = self.m_MouseObject = None
                img = self.m_MouseImage
                img = img.Rotate ( angle, (0,0) )
                bmp = img.ConvertToBitmap() 
                size = self.m_MouseSize
                obj = self.m_MouseObject = Canvas.AddScaledBitmap ( bmp, self.pc, Height = size [ 1 ], Position = "cc", InForeground = True)
                # self.m_MouseObject.SetPoint ( pc )
            else:
                mf = self.MovePoint ( pc, self.mh/2, angle )
                ml = self.MovePoint ( pc, self.mw/2, angle + radians ( 90 ) )
                mr = self.MovePoint ( pc, self.mw/2, angle - radians ( 90 ) )
                mb1 = self.MovePoint ( ml, self.mw/2, angle + radians ( 180 ) )
                mb2 = self.MovePoint ( mr, self.mw/2, angle + radians ( 180 ) )
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

        obj = Canvas.AddPoint(pc, color, Diameter = 2, InForeground = True) 
        self.m_MousePoints.append ( obj )
        obj = Canvas.AddPoint(pl, 'Pink', Diameter = 2, InForeground = True)
        self.m_MousePoints.append ( obj )
        obj = Canvas.AddPoint(pr, 'Red', Diameter = 2, InForeground = True) 
        self.m_MousePoints.append ( obj )
        Canvas.Draw ()

    def GetS ( self, al, ar, t ):
        vl0 = self.vl
        vr0 = self.vr
        vc0 = (vl0 + vr0) / 2
        ac  = (al + ar) / 2

        sl = vl0 * t + 0.5 * al * t ** 2
        sr = vr0 * t + 0.5 * ar * t ** 2
        s  = vc0 * t + 0.5 * ac * t ** 2 
        return ( s, sl, sr )

    def GetV ( self, al, ar, t ):
        vl0 = self.vl
        vr0 = self.vr
        vc0 = (vl0 + vr0) / 2
        ac  = (al + ar) / 2

        vl = vl0 + al * t
        vr = vr0 + ar * t
        vc = vr0 + ar * t
        return ( vc, vl, vr )

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
        # ( angle, error ) = integrate.quad ( f_angle, 0, t )
        angle = self.GetAngle ( al, ar, t )
        ( x, errx ) = integrate.quad ( f_x, 0, t )
        ( y, erry ) = integrate.quad ( f_y, 0, t )
        # ( s, erry ) = integrate.quad ( f_s, 0, t )
        # print "GetMove:", x, y, s
        return ( x, y, angle )

    def Move ( self, al, ar, dt ):
        Canvas = self.Canvas

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
                self.DrawMouse ( pc, angle )
            else:
                break

        # Updated status
        ( x, y, angle ) = self.GetMove ( al, ar, dt )
        angle = self.angle + angle
        pc = ( self.pc [ 0 ]  + x  , self.pc [ 1 ] + y )
        ( vc, vl, vr ) = self.GetV ( al, ar, dt )
        ( sc, sl, sr ) = self.GetS ( al, ar, dt )

        self.pc = pc
        self.angle = angle
        ( self.vl, self.vr ) = ( vl, vr )
        ( self.sl, self.sr ) = ( sl, sr )
        self.currtime = self.currtime + dt

        self.drawedtime = self.currtime 
        self.DrawMouse ( pc, angle, 'Green' )
        print("RT/T=%.3f,%.3f,A=%.2f,VL/VR=%.3f,%.3f,S/SL/SR=%.3f,%3.f,%.3f,DX,DY=%.3f,%.3f" % ( 
                time.time ()-self.starttime, 
                self.currtime - self.starttime, 
                degrees ( self.angle ),
                self.vl, self.vr, 
                sc * 1000, self.sl * 1000, self.sr * 1000,
                x, y
                ))

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

    def MoveTurnAccel ( self, angle, right = False, time = 1 ):
        block = self.block
        poll = self.poll
        v0 = self.vl
        wl = self.wl
        r = block / 2.
        angle = radians ( angle ) 
        t = r * angle / v0 * time
        a = 2 * wl * angle / ( t ** 2 ) 
        
        if right:
            al, ar = 2*a, 0 
        else:
            al, ar = 0, 2*a

        self.Move ( al, ar, t/2) 
        self.Move ( -al, -ar, t/2) 

    def MoveTurn90 ( self, right = False ):
        block = self.block
        poll = self.poll
        v0 = self.vl
        wl = self.wl
        r = block / 2.
        angle = radians ( 90 ) 
        t = r * angle / v0 * 1.07
        a = 2 * wl * angle / ( t ** 2 ) 
        
        if right:
            al, ar = a, -a 
        else:
            al, ar = -a, a

        self.Move ( al, ar, t/2) 
        self.Move ( -al, -ar, t/2) 

    def MoveTurnInPlace ( self, angle, a, right = False ):
        v0 = self.vl
        wl = self.wl
        angle = radians ( angle ) / 2 
        t = sqrt ( wl * angle / a )
        
        if right:
            al, ar = a, -a
        else:
            al, ar = -a, a

        self.Move ( al, ar, t) 
        self.Move ( -al, -ar, t) 

    def OnBtn3 (self, evt = None):
        block = self.block
        poll = self.poll
        self.InitEnv ()
        self.currtime = self.starttime = self.drawedtime = time.time ()

        self.MoveWithAccelDistance ( 10, block/2 )
        self.MoveTurn90 ( False )
        # self.MoveWithVelocityDistance ( 0, block/2 )

        x = ( block * 1 - (poll/2) )
        y = ( block * 1 - (poll/2) ) + block / 2
        print("pr", self.pc)
        print("Over X", x - self.pc [ 0 ])
        print("Over y", self.pc [ 1 ] - y)

    def OnBtn4 (self, evt = None):
        block = self.block
        poll = self.poll
        self.InitEnv ()
        self.currtime = self.starttime = self.drawedtime = time.time ()

        self.MoveWithAccelDistance ( 10, block/2 )
        self.MoveTurn90 ( True )
        # self.MoveWithVelocityDistance ( 0, block/2 )

        x = ( block * 1 - (poll/2) )
        y = ( block * 1 - (poll/2) ) + block / 2
        print("pr", self.pc)
        print("Over X", x - self.pc [ 0 ])
        print("Over y", self.pc [ 1 ] - y)

    def OnBtn5 (self, evt = None):
        pass

    def OnBtn6 (self, evt = None):
        pass
        
    def OnBtn45 (self, evt = None):
        block = self.block
        diag = sqrt ( 2 ) * ( block/2 )
        poll = self.poll
        x, y = block * 2 + (block-poll)/2, block * 1 - poll / 2
        angle = radians ( 0 )
        self.InitEnv ( ( x, y ), angle )
        self.currtime = self.starttime = self.drawedtime = time.time ()

        # 0->45
        self.MoveWithAccelDistance ( 10, block  - self.e1.GetValue () ) # -0.05
        self.MoveTurnAccel ( 45, True )
        self.MoveWithAccelDistance ( 0, diag + self.e2.GetValue ()) # +0.0788

        print("pr", self.pc)
        x = x + 1 * block/2 - self.pc [ 0 ] 
        y = y + 1 * block - self.pc [ 1 ]
        print("X:", x)
        print("Y:", y)
        print("X+Y:", x+y)
        print("X-Y:", x-y)

    def OnBtn90 (self, evt = None):
        block = self.block
        diag = sqrt ( 2 ) * ( block/2 )
        poll = self.poll
        x, y = block * 2 + (block-poll)/2, block * 1 - poll / 2
        angle = radians ( 0 )
        self.InitEnv ( ( x, y ), angle )
        self.currtime = self.starttime = self.drawedtime = time.time ()

        # 0->90
        self.MoveWithAccelDistance ( 10, block - self.e1.GetValue ()) # -0.024
        self.MoveTurnAccel ( 90, True )
        self.MoveWithAccelDistance ( 0, block - self.e2.GetValue () ) # -0.024

        print("pr", self.pc)
        x = x + 1 * block/2 - self.pc [ 0 ] 
        y = y + 1 * block - self.pc [ 1 ]
        print("X:", x)
        print("Y:", y)
        print("X+Y:", x+y)
        print("X-Y:", x-y)

    def OnBtn135 (self, evt = None):
        block = self.block
        diag = sqrt ( 2 ) * ( block/2 )
        poll = self.poll
        x, y = block * 2 + (block-poll)/2, block * 1 - poll / 2
        angle = radians ( 0 )
        self.InitEnv ( ( x, y ), angle )
        self.currtime = self.starttime = self.drawedtime = time.time ()

        # 0->135: too short from poll
        self.MoveWithAccelDistance ( 10, block - self.e1.GetValue () ) # -0.075
        self.MoveTurnAccel ( 135, True )
        self.MoveWithAccelDistance ( 0, diag ) # 0

        print("pr", self.pc)
        x = x + 1 * block/2 - self.pc [ 0 ] 
        y = y + 1 * block - self.pc [ 1 ]
        print("X:", x)
        print("Y:", y)
        print("X+Y:", x+y)
        print("X-Y:", x-y)

    def OnBtn180 (self, evt = None):
        block = self.block
        diag = sqrt ( 2 ) * ( block/2 )
        poll = self.poll
        x, y = block * 2 + (block-poll)/2, block * 1 - poll / 2
        angle = radians ( 0 )
        self.InitEnv ( ( x, y ), angle )
        self.currtime = self.starttime = self.drawedtime = time.time ()

        # 0->180: x error occur
        self.MoveWithAccelDistance ( 10, block - self.e1.GetValue () ) # -0.06
        self.MoveTurnAccel ( 180, True )
        self.MoveWithAccelDistance ( 0, block - self.e2.GetValue () ) # -0.06

        print("pr", self.pc)
        x = x + 1 * block/2 - self.pc [ 0 ] 
        y = y + 1 * block - self.pc [ 1 ]
        print("X:", x)
        print("Y:", y)
        print("X+Y:", x+y)
        print("X-Y:", x-y)

    def OnBtnDiagTo45 (self, evt = None):
        block = self.block
        diag = sqrt ( 2 ) * ( block/2 )
        poll = self.poll
        x, y = block * 1 + (block-poll)/2, block * 0 + ( block-poll ) /2 + block / 2
        angle = radians ( -45 )
        self.InitEnv ( ( x, y ), angle )
        self.currtime = self.starttime = self.drawedtime = time.time ()

        # diag->45
        self.MoveWithAccelDistance ( 10, diag - self.e1.GetValue () ) # -0.049
        self.MoveTurnAccel ( 45, True )
        self.MoveWithAccelDistance ( 0, block - self.e2.GetValue () ) # -0.049

        print("pr", self.pc)
        x = x + 1 * block - self.pc [ 0 ] 
        y = y + 2 * block - self.pc [ 1 ]
        print("X:", x)
        print("Y:", y)
        print("X+Y:", x+y)
        print("X-Y:", x-y)

    def OnBtnDiagTo90 (self, evt = None):
        block = self.block
        diag = sqrt ( 2 ) * ( block/2 )
        poll = self.poll
        x, y = block * 1 + (block-poll)/2, block * 0 + ( block-poll ) /2 + block / 2
        angle = radians ( -45 )
        self.InitEnv ( ( x, y ), angle )
        self.currtime = self.starttime = self.drawedtime = time.time ()

        # diag->90
        # too short from poll
        self.MoveWithAccelDistance ( 10, diag*2 )
        self.MoveWithAccelDistance ( 0, diag - diag/2 - self.e1.GetValue () ) # -diag/2-0.05
        self.MoveTurnAccel ( 90, True )
        self.MoveWithAccelDistance ( 0, diag + diag/2 - self.e2.GetValue () ) # +diag/2-0.05

        print(diag/2)
        print("pr", self.pc)
        x = x + 2 * block - self.pc [ 0 ] 
        y = y + 1 * block - self.pc [ 1 ]
        print("X:", x)
        print("Y:", y)
        print("X+Y:", x+y)
        print("X-Y:", x-y)
    
    def OnBtnDiagTo135 (self, evt = None):
        block = self.block
        diag = sqrt ( 2 ) * ( block/2 )
        poll = self.poll
        x, y = block * 1 + (block-poll)/2, block * 0 + ( block-poll ) /2 + block / 2
        angle = radians ( -45 )
        self.InitEnv ( ( x, y ), angle )
        self.currtime = self.starttime = self.drawedtime = time.time ()

        # diag->135
        self.MoveWithAccelDistance ( 10, diag )
        self.MoveWithAccelDistance ( 0, diag - self.e1.GetValue () ) # 0
        self.MoveTurnAccel ( 135, True )
        self.MoveWithAccelDistance ( 0, block - self.e2.GetValue () ) # 0.075

        print("pr", self.pc)
        x = x + 2 * block - self.pc [ 0 ] 
        y = y + 0 * block - self.pc [ 1 ]
        print("X:", x)
        print("Y:", y)
        print("X+Y:", x+y)
        print("X-Y:", x-y)

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
    b = g_wl
    wl = ( g_vl0 + g_al * t ) / g_r
    wr = ( g_vr0 + g_ar * t ) / g_r
    angle = GetAngle ( t )
    angle = angle + g_angle
    x = ( -g_r * sin ( angle ) / 2 ) * wl + ( -g_r * sin ( angle ) / 2 ) * wr
    return x

def f_y ( t ):
    b = g_wl
    wl = ( g_vl0 + g_al * t ) / g_r
    wr = ( g_vr0 + g_ar * t ) / g_r
    angle = GetAngle ( t )
    angle = angle + g_angle
    y = (  g_r * cos ( angle ) / 2 ) * wl + (  g_r * cos ( angle ) / 2 ) * wr
    return y

def f_s ( t ):
    b = g_wl
    wl = ( g_vl0 + g_al * t ) / g_r
    wr = ( g_vr0 + g_ar * t ) / g_r
    angle = GetAngle ( t )
    angle = angle + g_angle
    x = ( -g_r * sin ( angle ) / 2 ) * wl + ( -g_r * sin ( angle ) / 2 ) * wr
    y = (  g_r * cos ( angle ) / 2 ) * wl + (  g_r * cos ( angle ) / 2 ) * wr
    s = sqrt ( x**2 + y**2 )
    return s

def f_angle ( t ):
    b = g_wl
    wl = ( g_vl0 + g_al * t ) / g_r
    wr = ( g_vr0 + g_ar * t ) / g_r
    angle = -g_r / b * wl + g_r / b * wr
    return angle

class AppMain(wx.App):
    def OnInit(self):
        frame = AppFrame(None, "TEST")
        self.SetTopWindow(frame)
        frame.Show(True)
        frame.OnInit()
        return True

#---------------------------------------------------------------------------
if __name__ == '__main__':
    app = AppMain(redirect=False)
    app.MainLoop()


