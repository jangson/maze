
#-------------------------------------------------------------------------------
# Name:        mycanvas
# Purpose:     Micro mouse simulator
#
# Author:      hjkim
#
# Created:     20-04-2012
# Copyright:   (c) HyunJun Kim 2012. All Rights Reserved.
# Licence:     GPL 
#-------------------------------------------------------------------------------
# -*- coding: cp949 -*-

from wx.lib.floatcanvas import NavCanvas, FloatCanvas, Resources, GUIMode
import wx.lib.colourdb
import time, random
import numpy as N

class MyFloatCanvas(FloatCanvas.FloatCanvas):
    def __init__(self, parent, id = -1,
                 size = wx.DefaultSize,
                 ProjectionFun = None,
                 BackgroundColor = "WHITE",
                 Debug = False,
                 **kwargs):

        FloatCanvas.FloatCanvas.__init__(self, parent, id,
                 size,
                 ProjectionFun,
                 BackgroundColor,
                 Debug,
                 **kwargs)

    def _DrawObject(self, Object, HTdc = None):
        """
        This is a convenience function;
        This function takes the list of objects and draws them to specified
        device context.
        """
        dc = wx.MemoryDC()
        dc.SelectObject(self._Buffer)
        
        ScreenDC =  wx.ClientDC(self)
        ViewPortWorld = N.array(( self.PixelToWorld((0,0)),
                                  self.PixelToWorld(self.PanelSize) )
                                     )
        self.ViewPortBB = N.array( ( N.minimum.reduce(ViewPortWorld),
                              N.maximum.reduce(ViewPortWorld) ) )


        dc.SetBackground(self.BackgroundBrush)
        dc.BeginDrawing()
        #i = 0
        PanelSize0, PanelSize1 = self.PanelSize # for speed
        WorldToPixel = self.WorldToPixel # for speed
        ScaleWorldToPixel = self.ScaleWorldToPixel # for speed
        Blit = ScreenDC.Blit # for speed
        NumBetweenBlits = self.NumBetweenBlits # for speed
        Object._Draw(dc, WorldToPixel, ScaleWorldToPixel, HTdc)
        Blit(0, 0, PanelSize0, PanelSize1, dc, 0, 0)
        dc.EndDrawing()

    def LeftDownEvent(self, event):
        pass
    def LeftUpEvent(self, event):
        pass

    def _LeftDownEvent(self, event):
        if self.GUIMode:
            self.GUIMode.OnLeftDown(event)
        event.Skip()

    def _LeftUpEvent(self, event):
        if self.HasCapture():
            self.ReleaseMouse()
        if self.GUIMode:
            self.GUIMode.OnLeftUp(event)
        event.Skip()
        

"""
A Panel that includes the FloatCanvas and Navigation controls

"""

# import FloatCanvas, Resources, GUIMode

class NavCanvas(wx.Panel):
    """
    NavCanvas.py

    This is a high level window that encloses the FloatCanvas in a panel
    and adds a Navigation toolbar.

    """

    def __init__(self,
                   parent,
                   id = wx.ID_ANY,
                   size = wx.DefaultSize,
                   **kwargs): # The rest just get passed into FloatCanvas
        wx.Panel.__init__(self, parent, id, size=size)

        self.Modes = [("Pointer",  GUIMode.GUIMouse(),   Resources.getPointerBitmap()),
                      ("Zoom In",  GUIMode.GUIZoomIn(),  Resources.getMagPlusBitmap()),
                      ("Zoom Out", GUIMode.GUIZoomOut(), Resources.getMagMinusBitmap()),
                      ("Pan",      GUIMode.GUIMove(),    Resources.getHandBitmap()),
                      ]
        
        self.BuildToolbar()
        ## Create the vertical sizer for the toolbar and Panel
        # box = wx.BoxSizer(wx.VERTICAL)
        # box.Add(self.ToolBar, 0, wx.ALL | wx.ALIGN_LEFT | wx.GROW, 4)

        # self.Canvas = FloatCanvas.FloatCanvas(self, **kwargs)
        self.Canvas = MyFloatCanvas ( self, ** kwargs )
        # box.Add(self.Canvas, 1, wx.GROW)
# 
        # self.SetSizerAndFit(box)

        # default to first mode
        #self.ToolBar.ToggleTool(self.PointerTool.GetId(), True)
        self.Canvas.SetMode(self.Modes[0][1])

        return None

    def BuildToolbar(self):
        """
        This is here so it can be over-ridden in a ssubclass, to add extra tools, etc
        """
        tb = wx.ToolBar(self)
        self.ToolBar = tb
        tb.SetToolBitmapSize((24,24))
        self.AddToolbarModeButtons(tb, self.Modes)
        self.AddToolbarZoomButton(tb)
        tb.Realize()
        ## fixme: remove this when the bug is fixed!
        #wx.CallAfter(self.HideShowHack) # this required on wxPython 2.8.3 on OS-X
    
    def AddToolbarModeButtons(self, tb, Modes):
        self.ModesDict = {}
        for Mode in Modes:
            tool = tb.AddRadioTool(wx.ID_ANY, shortHelp=Mode[0], bitmap=Mode[2])
            self.Bind(wx.EVT_TOOL, self.SetMode, tool)
            self.ModesDict[tool.GetId()]=Mode[1]
        #self.ZoomOutTool = tb.AddRadioTool(wx.ID_ANY, bitmap=Resources.getMagMinusBitmap(), shortHelp = "Zoom Out")
        #self.Bind(wx.EVT_TOOL, lambda evt : self.SetMode(Mode=self.GUIZoomOut), self.ZoomOutTool)

    def AddToolbarZoomButton(self, tb):
        tb.AddSeparator()

        self.ZoomButton = wx.Button(tb, label="Zoom To Fit")
        tb.AddControl(self.ZoomButton)
        self.ZoomButton.Bind(wx.EVT_BUTTON, self.ZoomToFit)


    def HideShowHack(self):
        ##fixme: remove this when the bug is fixed!
        """
        Hack to hide and show button on toolbar to get around OS-X bug on
        wxPython2.8 on OS-X
        """
        self.ZoomButton.Hide()
        self.ZoomButton.Show()

    def SetMode(self, event):
        Mode = self.ModesDict[event.GetId()]
        self.Canvas.SetMode(Mode)

    def ZoomToFit(self,Event):
        self.Canvas.ZoomToBB()
        self.Canvas.SetFocus() # Otherwise the focus stays on the Button, and wheel events are lost.

