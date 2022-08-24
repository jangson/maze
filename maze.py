
#-------------------------------------------------------------------------------
# Name:        maze
# Purpose:     Micro mouse simulator
#
# Author:      hjkim
#
# Created:     05-04-2012
# Copyright:   (c) HyunJun Kim 2012. All Rights Reserved.
# Licence:     GPL 
#-------------------------------------------------------------------------------
# -*- coding: cp949 -*-

import  sys, os
import  time
from    struct import *
from    array import *
from    math  import *
import  re
import  threading
from    scipy import integrate
import  numpy as N

# wxPython module
import  wx
import  wx.lib.masked           as masked
from    wx.lib.floatcanvas import FloatCanvas, Resources, GUIMode

# user module
import  mycanvas
import  mouse

# log module
import inspect
import logging

logging.basicConfig(format='%(asctime)s.%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', datefmt='%d-%m-%Y:%H:%M:%S', level=logging.DEBUG)
logger = logging.getLogger("logger_1")
# log example
## inspect
# print("[",inspect.currentframe().f_lineno,"] RUN MakeLookUpWall")
## logging
# logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
# logging.debug('This message should go to the log file')
# logging.info('So should this')
# logging.warning('And this, too')
# logging.error('And non-ASCII stuff')

#-------------------------------------------------------------------------------
# Maze Panel 
#-------------------------------------------------------------------------------
load_dir = False
USE_MOUSE_IMAGE = False
DRAW_MOUSE = True

# .maz file format description
# Using one byte per block. Bit description is below.
#           | Known |  wall |
#           | 1  / 0| 1 / 0 |
# bits      7 6 5 4 3 2 1 0
#           +-+-+-+-+-+-+-+-+
# direction |W|S|E|N|W|S|E|N|
#           +-+-+-+-+-+-+-+-+
WALL_N = 1
WALL_E = 2
WALL_S = 4
WALL_W = 8
WALL_N_D = 0x10
WALL_E_D = 0x20
WALL_S_D = 0x40
WALL_W_D = 0x80

# Wall type
WALL_NONE       = 0
WALL_UNKNOWN    = 1
WALL_EXIST      = 2
WALL_DETECTED   = 3
WALL_MUST_EXIST = 4

# Wall index for lookup
WALL_LU_N   = 0
WALL_LU_E   = 1
WALL_LU_S   = 2
WALL_LU_W   = 3

# Default size
MAZE_SIZE               = ( 16, 16 )
MAZE_BLOCK_WIDTH        = 0.180   # 180 milimeter
MAZE_POLL_WIDTH         = 0.012   # Real size is 12 mm
MOUSE_SIZE              = ( 0.060, 0.080 )
MAZE_START_POSITION     = ( 0, 0 )
MAZE_TARGET_POSITION    = ( 0xff, 0xff )
MAZE_TARGET_SECTION     = ( ( 7, 7 ), ( 8, 8 ) )

NAZE_COLORS = {
        'Background'        : ( 20, 20, 20 ),
        'WallUnknown'       : ( 40, 40, 40 ),
        'MazeBorder'        : 'Red',
        'Poll'              : 'Red',
        'WallExist'         : 'Green',
        'WallDetected'      : 'Red',
        'WallMustExisted'   : 'White',
} 

class MazePanel(wx.Panel):
    def __init__(self,
                   parent,
                   id = wx.ID_ANY,
                   size = wx.DefaultSize,
                   BackgroundColor = ( 20, 20, 20 ),
                   **kwargs): # The rest just get passed into FloatCanvas
        wx.Panel.__init__(self, parent, id, size=size)

        self.EditMode = None
        self.Modes = [
                ("Pointer",  GUIMode.GUIMouse(),   Resources.getPointerBitmap()),
                ("Start",    GUIMode.GUIMouse(),   Resources.getPointerBitmap()),
                ("Target",   GUIMode.GUIMouse(),   Resources.getPointerBitmap()),
                ("Edit",     GUIMode.GUIMouse(),   wx.Bitmap ("resource/edit.png")),
                ("Erase",    GUIMode.GUIMouse(),   wx.Bitmap ("resource/erase.png")),
                ("Zoom In",  GUIMode.GUIZoomIn(),  Resources.getMagPlusBitmap()),
                ("Zoom Out", GUIMode.GUIZoomOut(), Resources.getMagMinusBitmap()),
                ("Pan",      GUIMode.GUIMove(),    Resources.getHandBitmap()),
                ]

        self.Log = wx.FindWindowById ( ID_WINDOW_LOG )
        if self.Log:
            self.Log = self.Log.Log

        self.m_Parent = parent

        path = os.getcwd()
        self.m_Path = os.path.join(path, "maze")

        box = wx.BoxSizer(wx.VERTICAL)

        self.BuildToolbar()
        box.Add(self.ToolBar, 0, wx.ALL | wx.ALIGN_LEFT | wx.GROW, 4)

        sp = wx.SplitterWindow ( self )
        self.Canvas = mycanvas.MyFloatCanvas ( sp, BackgroundColor = ( 20, 20, 20 ), ** kwargs )
        self.Canvas.SetMode(self.Modes[0][1])

        # mouse
        self.LoadMouseImage ()
        self.m_MousePoly = None
        self.m_MouseRoute = None
        self.m_MouseObject = None
        self.m_Mouse = mouse.Mouse(self) 

        # Init default maze variables
        self.m_Colors = NAZE_COLORS
        self.m_MazeSize = list ( MAZE_SIZE )
        self.m_BlockWidth = MAZE_BLOCK_WIDTH
        self.m_PollWidth  = MAZE_POLL_WIDTH
        self.m_StartXY = list ( MAZE_START_POSITION )
        self.m_TargetXY = list ( MAZE_TARGET_POSITION )
        self.m_TargetSection = list ( MAZE_TARGET_SECTION )

        # Initialize maze
        # ( w, h ) = self.m_MazeSize
        # self.m_MaxW = float(self.m_BlockWidth * w + self.m_PollWidth)
        # self.m_MaxH = float(self.m_BlockWidth * h + self.m_PollWidth)
        self.m_Walls = None
        self.m_WallInfos = None
        self.m_WallPoints = None
        self.m_LookupWall = None
        self.m_TypeWalls = None
        self.InitMaze ()
        self.FileNewMaze () 

        # mouse
        size = MOUSE_SIZE
        way = self.m_BlockWidth - self.m_PollWidth  
        pos = ( way/2+self.m_PollWidth, way/2+self.m_PollWidth )

        self.m_MouseSize = size
        self.m_MousePos = pos
        self.m_MouseAngle = radians(0)

        # others
        self.MouseAutoPaused = False
        self.ShiftDown = False 
        self.ControlDown = False 

        # Setup panel
        # self.Bind(wx.EVT_SIZE, self.OnSize)
        # self.Bind(wx.EVT_PAINT, self.OnPaint)
        # self.Bind(wx.EVT_NC_PAINT, self.OnNCPaint)
        self.Canvas.Bind(FloatCanvas.EVT_MOTION, self.OnMove) 
        self.Canvas.Bind ( wx.EVT_KEY_DOWN, self.OnKeyDown )
        self.Canvas.Bind ( wx.EVT_KEY_UP, self.OnKeyUp )
        self.Canvas.Bind ( wx.EVT_LEFT_DOWN, self.LeftDownEvent )
        self.Canvas.Bind ( wx.EVT_LEFT_UP, self.LeftUpEvent )

        self.m_Control = ControlPanel ( sp, ID_WINDOW_CONTROL )
        sp.SplitVertically(self.Canvas, self.m_Control)
        sp.SetSashGravity ( 1 )
        sp.SetMinimumPaneSize(200)

        box.Add(sp, 1, wx.GROW)
        self.SetSizer(box)


    ########################################################################
    # Methods for initialization
    ########################################################################
    def InitMaze ( self ):
        ( w, h ) = self.m_MazeSize
        self.m_MaxW = float(self.m_BlockWidth * w + self.m_PollWidth)
        self.m_MaxH = float(self.m_BlockWidth * h + self.m_PollWidth)

        self.m_Polls = []
        self.m_Walls, self.m_LookupWall = [], []
        self.m_TypeWalls = []
        self.Canvas.InitAll()

        self.m_Polls = self.MakePolls ()
        self.m_Walls = []
        self.m_WallLines = []
        self.m_WallInfos = []
        self.m_WallPoints = []
        self.MakeWalls ()
        self.m_LookupWall = self.MakeLookUpWall ()
        self.m_TypeWalls = [ WALL_UNKNOWN ] * len(self.m_Walls)  
        self.SetKnownWalls()
        self.InitMouse ()
        self.InitCursor ()

    def InitCursor ( self ):
        Canvas = self.Canvas
        cw = self.m_BlockWidth / 2
        self.m_Cursor = Canvas.AddRectangle ( ( 0, 0 ), ( cw, cw ), LineColor = None, FillColor = None, InForeground = True )
        self.m_CursorRect = [ [ 0, 0 ], [ cw, cw ] ]

    def LoadMouseImage ( self, filename = "mouse.png" ):
        if USE_MOUSE_IMAGE:
            bmp = wx.Bitmap( filename )
            img = bmp.ConvertToImage()
            self.m_MouseImage = img 

    def InitMouse ( self ):
        self.m_MousePoly = None
        self.m_Mouse.InitMouse()

    def ResetMouse ( self ):
        mazesize = self.m_MazeSize
        start = self.m_StartXY
        target = self.m_TargetXY
        target_section = self.m_TargetSection

        size = ( self.m_BlockWidth / 3, self.m_BlockWidth / 3 )
        way = self.m_BlockWidth - self.m_PollWidth  
        pos = ( way/2+self.m_PollWidth, way/2+self.m_PollWidth )

        self.m_MouseSize = size
        self.m_MousePos = pos
        self.m_MouseAngle = radians(0)

        if target [ 0 ] >= mazesize [ 0 ] or target [ 1 ] >= mazesize [ 1 ]:
            target = None

        self.m_Mouse.SetMouse(self.m_MazeSize, self.m_MouseSize, self.m_MousePos, self.m_MouseAngle, self.m_BlockWidth, self.m_PollWidth, start, target, target_section, drawtime = 0.04)

    def PostInit ( self ):
        self.DrawMaze ()

    ########################################################################
    # Methods for Making wall, poll
    ########################################################################
    def GetPollRect(self, pos):
        reduce_size = 0.000
        ( x, y ) = pos
        x = self.m_BlockWidth * x + reduce_size
        y = self.m_BlockWidth * y + reduce_size
        return ( x, y , self.m_PollWidth - reduce_size*2, self.m_PollWidth - reduce_size*2)

    def GetNWallRect( self, pos ):
        reduce_size = 0.000
        ( x, y ) = pos
        x1 = self.m_BlockWidth * x + self.m_PollWidth + reduce_size 
        y1 = self.m_BlockWidth * ( y + 1 )
        w1 = self.m_BlockWidth - self.m_PollWidth - reduce_size*2
        h1 = self.m_PollWidth
        return ( x1, y1, w1, h1 ) 

    def GetEWallRect( self, pos ):
        reduce_size = 0.000
        ( x, y ) = pos
        x1 = self.m_BlockWidth * (x + 1)
        y1 = self.m_BlockWidth * y + self.m_PollWidth + reduce_size
        w1 = self.m_PollWidth
        h1 = self.m_BlockWidth - self.m_PollWidth - reduce_size*2
        return ( x1, y1, w1, h1 ) 

    def GetSWallRect( self, pos ):
        reduce_size = 0.000
        ( x, y ) = pos
        x1 = self.m_BlockWidth * x + self.m_PollWidth + reduce_size
        y1 = self.m_BlockWidth * y
        w1 = self.m_BlockWidth - self.m_PollWidth - reduce_size*2
        h1 = self.m_PollWidth
        return ( x1, y1, w1, h1 ) 

    def GetWWallRect( self, pos ):
        reduce_size = 0.000
        ( x, y ) = pos
        x1 = self.m_BlockWidth * x
        y1 = self.m_BlockWidth * y + self.m_PollWidth + reduce_size
        w1 = self.m_PollWidth
        h1 = self.m_BlockWidth - self.m_PollWidth - reduce_size*2
        return ( x1, y1, w1, h1 ) 

    def MakePolls ( self ): 
        color = self.m_Colors [ 'Poll']
        polls = []
        ( w, h ) = self.m_MazeSize

        for y in range(0, h+1):
            for x in range(0, w+1):
                poll = self.GetPollRect( ( x, y ) ) 
                pos = ( poll [0], poll [1] )
                size = ( poll [2], poll [3] )
                canvas = self.Canvas
                xy = ( poll [0] + poll [ 2 ]/2, poll [1] + poll [ 3 ]/2)
                poll = canvas.AddRectangle ( pos, size, LineColor = color, FillColor = color, InForeground = False )
                self.Canvas.AddSquarePoint(xy, Color = color, Size = 2 )
                polls.append ( poll )

        # print len ( polls )
        return polls

    def AddWallObject ( self, wall ): 
        if not wall:
            self.m_Walls.append ( None ) 
            self.m_WallLines.append ( None ) 
            self.m_WallInfos.append ( None )
            self.m_WallPoints.append ( [ None, None ] )
            return

        canvas = self.Canvas
        pos = ( wall [0], wall [1] )
        size = ( wall [2], wall [3] )
        posc = ( wall [0] + wall[2] / 2, wall [1] + wall[3] / 2 )
        rs = 0.005
        if wall [ 2 ] > wall [ 3 ]:
            xy1 = ( wall [ 0 ] + rs, wall [ 1 ] + wall [ 3 ] / 2)
            xy2 = ( wall [ 0 ] + wall [ 2 ] - rs * 2, wall [1] + wall [ 3 ] / 2)
        else:
            xy1 = ( wall [ 0 ] + wall [ 2 ] / 2, wall [ 1 ] + rs )
            xy2 = ( wall [ 0 ] + wall [ 2 ] / 2, wall [1] + wall [ 3 ] - rs * 2 )

        wall = canvas.AddRectangle ( pos, size, LineColor = None, FillColor = None, InForeground = False ) 
        wall.Name = "%d"% ( len ( self.m_Walls ) )

        wallline = canvas.AddLine ( ( xy1, xy2 ), LineWidth = 2, LineColor = None, InForeground = False ) 
        wallline.Name = "%d"% ( len ( self.m_Walls ) )

        info = canvas.AddText ( '', posc, Size = 8, Color = 'White', Position = 'cc', InForeground = True )
        info.Hide ()

        point2 = canvas.AddPoint(posc, 'Yellow', Diameter = 4, InForeground = True)
        point2.Hide ()

        point = canvas.AddPoint(posc, 'Blue', Diameter = 4, InForeground = True)
        point.Hide ()

        self.m_Walls.append ( wall ) 
        self.m_WallLines.append ( wallline ) 
        self.m_WallInfos.append ( info )
        self.m_WallPoints.append ( [ point, 0 ] )
    
    def MakeWalls ( self ): 
        ( w, h ) = self.m_MazeSize

        for y in range(0, h):
            self.AddWallObject ( self.GetWWallRect ( ( 0, y ) ) )
            for x in range(0, w):
                self.AddWallObject ( self.GetSWallRect ( ( x, y ) ) )
                self.AddWallObject ( self.GetEWallRect ( ( x, y ) ) )
            self.AddWallObject ( None ) 

        y = h
        self.AddWallObject ( None ) 
        for x in range(0, w):
            self.AddWallObject ( self.GetSWallRect ( ( x, y ) ) )
            self.AddWallObject ( None ) 
        self.AddWallObject ( None ) 

    def MakeLookUpWall (self):
        # print("[",inspect.currentframe().f_lineno,"] RUN MakeLookUpWall")
        lookup = []
        ( w, h ) = self.m_MazeSize
        rcnt = ( w + 1 ) * 2

        for y in range(0, h):
            row = []
            for x in range(0, w):
                wn = rcnt * ( y+1 ) + x*2 + 1  
                we = rcnt * y + x*2 + 2 
                ws = rcnt * y + x*2 + 1 
                ww = rcnt * y + x*2 
                row.append ( ( wn, we, ws, ww ) )
            lookup.append ( row )
            
        return lookup


    ########################################################################
    # Methods for maze access
    ########################################################################
    def ClearAllWallInfos ( self, draw = True ):
        objs = self.m_WallInfos
        for obj in objs:
            if obj:
                obj.Hide ()

        if draw:
            self.Canvas.Draw ( )

    def DrawWallPoints ( self, index, type ):
        objs = self.m_WallPoints
        obj = objs [ index ] [ 0 ]
        draw = objs [ index ] [ 1 ]
        if obj and draw != type:
            if type==0:
                self.Canvas._ClearObjectScreen ( obj )
            elif type==1:
                obj.SetColor ( 'Blue' )
                self.Canvas._DrawObjectScreen ( obj )
            elif type==2:
                obj.SetColor ( 'Yellow' )
                self.Canvas._DrawObjectScreen ( obj )

            self.m_WallPoints [ index ] [ 1 ] = type

    def EnableAllWallInformation ( self, enable, draw = True ):
        objs = self.m_WallInfos
        for obj in objs:
            if obj:
                obj.Visible = enable 
        
        # if draw:
            # self.Canvas.Draw ( )

    def SetAllWallInformation ( self, infos ):
        objs = self.m_WallInfos
        for index in range ( len ( objs ) ) :
            if objs [ index ]:
                objs [ index ].SetText ( infos [ index ] )

    def GetAllWalls ( self ):
        return self.m_TypeWalls

    def ResetAllWall  ( self ):
        for index in range ( len ( self.m_TypeWalls ) ) :
            if self.m_TypeWalls [ index ] == WALL_NONE:
                self.m_TypeWalls [ index ] = WALL_UNKNOWN
            elif self.m_TypeWalls [ index ] == WALL_DETECTED:
                self.m_TypeWalls [ index ] = WALL_EXIST
        self.SetKnownWalls()

    def DetectedWall ( self, index, draw = True ):
        walls = self.m_Walls

        if self.m_TypeWalls [ index ] == WALL_UNKNOWN:
            self.m_TypeWalls [ index ] = WALL_NONE
            if draw:
                self.DrawWall ( index, draw ) 

        elif self.m_TypeWalls [ index ] == WALL_EXIST:
            self.m_TypeWalls [ index ] = WALL_DETECTED
            if draw:
                self.DrawWall ( index, draw ) 


    def GetWall ( self, index ):
        return self.m_TypeWalls [ index ]

    def SetWall ( self, index, wall, draw = True ):
        self.m_TypeWalls[ index ] = wall
        self.DrawWall ( index, draw ) 
        if draw:
            self.DrawWall ( index, draw ) 

    def GetWallIndex ( self, xy, nesw ):
        index = self.m_LookupWall [ xy [ 1 ] ] [ xy [ 0 ] ] [ nesw ]
        return index

    def GetWallXY ( self, xy, nesw ):
        index = self.m_LookupWall [ xy [ 1 ] ] [ xy [ 0 ] ] [ nesw ]
        return self.m_TypeWalls [ index ]
    
    def SetWallXY (self, xy, nesw, wall, draw = True):
        # print("[",inspect.currentframe().f_lineno,"] RUN SetWallXY")
        index = self.m_LookupWall [ int(xy [ 1 ]) ] [ xy [ 0 ] ] [ nesw ]
        self.m_TypeWalls [ index ] = wall
        if draw:
            self.DrawWall ( index, draw ) 

    def SetAllWalls (self, wall):
        self.m_TypeWalls = [ wall ] * len(self.m_Walls) 
        
    def SetKnownWalls(self):
        ( w, h ) = self.m_MazeSize
        self.SetWallXY( ( 0, 0 ), WALL_LU_E, WALL_MUST_EXIST, False )
        for y in range ( 0, h ):
            self.SetWallXY( ( 0, y ), WALL_LU_W, WALL_MUST_EXIST, False  )
            self.SetWallXY( ( w-1, y ), WALL_LU_E, WALL_MUST_EXIST, False  )
            
        for x in range ( 0, w ):
            self.SetWallXY( ( x, 0 ), WALL_LU_S, WALL_MUST_EXIST, False  )
            self.SetWallXY( ( x, h - 1 ), WALL_LU_N, WALL_MUST_EXIST, False  )


    ########################################################################
    # Methods for drawing
    ########################################################################
    def DrawWall ( self, index, draw = True ):
        type = self.m_TypeWalls [ index ]
        wall = self.m_Walls [ index ]
        line = self.m_WallLines [ index ]
        if not wall:
            return

        colors = self.m_Colors
        color = None 
        fcolor = None 
        lstyle = None
        fstyle = None
        if type == WALL_NONE:
            fcolor = color = colors [ 'Background'] 
            fstyle = lstyle = 'Solid'
        elif type == WALL_UNKNOWN:
            fcolor = color = colors [ 'WallUnknown'] 
            fstyle = lstyle = 'Solid'
        elif type == WALL_EXIST:
            fcolor = color = colors [ 'WallExist']
            fstule = lstyle = 'Solid'
        elif type == WALL_DETECTED:
            fcolor = color = colors [ 'WallDetected']
            fstyle = lstyle = 'Solid'
        elif type == WALL_MUST_EXIST:
            fcolor = color = colors [ 'WallMustExisted']
            fstyle = lstyle = 'Solid'
        else:
            self.Log ( "Unknown wall type" )
            return
        
        wall.SetLineColor ( color ) 
        wall.SetLineStyle ( lstyle ) 
        wall.SetFillColor ( fcolor )
        wall.SetFillStyle ( fstyle )
        line.SetLineColor ( color )
        line.SetLineStyle ( lstyle ) 

        if draw:
            self.Canvas._DrawObjectBackground ( line )
            self.Canvas._DrawObjectScreen ( line )
            self.Canvas._DrawObjectBackground ( wall )
            self.Canvas._DrawObjectScreen ( wall )

    def DrawAllWalls ( self, draw = True ):
        for index in range ( len ( self.m_TypeWalls ) ) :
            self.DrawWall( index, False ) 

        if draw:
            self.Canvas.Draw ( )

    def DrawMaze ( self ):
        self.DrawAllWalls ( False )
        # self.ClearAllWallInfos ( False ) 
        self.ResetMouse ()
        self.Canvas.ZoomToBB()

    def MovePoint ( self, p, l, angle ):
        ( x, y ) = p
        xo = x - l * sin ( angle )
        yo = y + l * cos ( angle )
        return ( xo, yo )

    def DrawMouse ( self, pc, angle, redraw = True, color = 'White' ):
        Canvas = self.Canvas
        (mw, mh) = self.m_MouseSize
        
        pl = self.MovePoint ( pc, mw/2, angle + radians ( 90 ) )
        pr = self.MovePoint ( pc, mw/2, angle - radians ( 90 ) )

        # obj1 = Canvas.AddPoint(pc, color, Diameter = 2, InForeground = False)
        # obj2 = Canvas.AddPoint(pl, 'Pink', Diameter = 2, InForeground = False)
        # obj3 = Canvas.AddPoint(pr, 'Red', Diameter = 2, InForeground = False)

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

                colors = self.m_Colors
                if not self.m_MousePoly:
                    self.m_MousePoly = Canvas.AddPolygon( 
                                    points, 
                                    LineWidth = 2, 
                                    LineColor = "Blue", 
                                    FillColor = "Blue",
                                    FillStyle = 'Solid',
                                    InForeground = True)                    
                    self.m_MousePoly.Hide ()
                else:
                    self.Canvas._ClearObjectScreen ( self.m_MousePoly )
                    ''' mouse color '''
                    self.m_MousePoly.SetPoints( points )
                    self.m_MousePoly.SetLineColor ('Red')
                    self.m_MousePoly.SetFillColor ('Red')
                    self.Canvas._DrawObjectScreen ( self.m_MousePoly )

        self.PanCanvasForObject ( self.m_MousePoly )

        if redraw:
            # self.Canvas._DrawObject ( self.m_MousePoly )
            # Canvas.Draw ()
            pass

        # self.m_MouseRoute.append( (obj1, obj2, obj3) )

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

    def PanCanvasForObject ( self, Object ):
        ViewPortWorld = N.array(( self.Canvas.PixelToWorld((0,0)),
                                  self.Canvas.PixelToWorld(self.Canvas.PanelSize) )
                                     )
        ViewPortBB = N.array( ( N.minimum.reduce(ViewPortWorld),
                              N.maximum.reduce(ViewPortWorld) ) )

        ( ( p1x, p1y ), ( p2x, p2y ) ) = Object.BoundingBox
        ( ( v1x, v1y ), ( v2x, v2y ) ) = ViewPortBB
        ( ( c1x, c1y ), ( c2x, c2y ) ) = self.Canvas.BoundingBox
        panw = ( v2x - v1x ) / 3
        panh = ( v2y - v1y ) / 3

        panx = pany = 0
        if p1x<v1x:
            panx = p1x-v1x-panw
            panmax = c1x - v1x
            if panx < panmax:
                panx = panmax
        if p2x>v2x:
            panx = p2x-v2x+panw
            panmax = c2x - v2x
            if panx > panmax:
                panx = panmax
        if p1y<v1y:
            pany = p1y-v1y-panh
            panmax = c1y - v1y
            if pany < panmax:
                pany = panmax
        if p2y>v2y:
            pany = p2y-v2y+panh
            panmax = c2y - v2y
            if pany > panmax:
                pany = panmax

        if panx or pany:
            self.Canvas.MoveImage( ( panx, pany ), 'World', ReDraw=False)

    def SetCursor ( self, enable, color = "Green" ):
        self.m_Cursor.Visible = enable
        self.m_Cursor.SetLineColor ( color ) 
        self.m_Cursor.SetLineStyle ( "Solid" ) 
        self.Canvas.Draw ()

    def SetCursorSize ( self, num ): 
        cw = self.m_BlockWidth / 2 * int ( num )
        self.m_CursorRect [ 1 ] = [ cw, cw ]
        self.m_Cursor.SetShape( self.m_CursorRect [ 0 ], self.m_CursorRect [ 1 ] )

    def MoveCursor ( self, xy ):
        xy = list ( xy ) 
        xy = [ xy [ 0 ] - self.m_CursorRect [ 1 ] [ 0 ] / 2, xy [ 1 ] - self.m_CursorRect [ 1 ] [ 1 ] / 2 ]
        self.m_CursorRect [ 0 ] = list ( xy ) 
        self.m_Cursor.SetPoint ( self.m_CursorRect [ 0 ] ) 
        self.Canvas.Draw ()

    ########################################################################
    # Methods for changing maze setting
    ########################################################################
    def GetMazeSettings ( self ): 
        settings = ( 
            # type, range, name, description
            ( 'MazeSize',   ( 4, 64 ),     'Maze size W,H',    'Width and height of Maze (4~64)' ),
            ( 'Integer',    ( 50, 300 ),   'Block Width',      'One Block width of maze (50~300mm)' ),
            ( 'Integer',    ( 4, 30 ),     'Wall thick',       'Thick of wall (4~30mm)' ),
            ( 'Position',   ( 1, 1 ),      'Start X,Y',        'X,Y for starting postion in maze' ),
            ( 'Position',   ( 0, 0 ),      'Target X,Y',       'X,Y for target postion in maze(0,0 is none)' ),
            ( 'Position',   ( 1, 1 ),      'Target area SX,SY',  'X,Y for start of target section in maze' ),
            ( 'Position',   ( 1, 1 ),      'Target area EX,EY',  'X,Y for end of target section in maze' ),
        )
        def CvrtPosition (x):
            if x == 255:
                return 0
            return ( x + 1 )
        values = (
            self.m_MazeSize [ 0 ],
            self.m_MazeSize [ 1 ],
            self.m_BlockWidth * 1000,
            self.m_PollWidth * 1000,
            CvrtPosition ( self.m_StartXY [ 0 ] ),
            CvrtPosition ( self.m_StartXY [ 1 ] ),
            CvrtPosition ( self.m_TargetXY [ 0 ] ),
            CvrtPosition ( self.m_TargetXY  [ 1 ] ),
            CvrtPosition ( self.m_TargetSection [ 0 ] [ 0 ] ),
            CvrtPosition ( self.m_TargetSection [ 0 ] [ 1 ] ),
            CvrtPosition ( self.m_TargetSection [ 1 ] [ 0 ] ),
            CvrtPosition ( self.m_TargetSection [ 1 ] [ 1 ] ),
        )
        return ( settings, values )

    def SaveMazeSetting ( self, values ):
        [   w, 
            h,
            bw,
            pw, 
            sx,
            sy,
            tx,
            ty,
            tssx,
            tssy,
            tsex,
            tsey
        ] = values

        def CvrtPosition (x):
            if x == 0:
                return 255
            return ( x - 1 )

        old_size = self.m_MazeSize
        old_block = self.m_BlockWidth
        old_poll = self.m_PollWidth
        self.m_MazeSize = ( w, h ) 
        self.m_BlockWidth = float ( bw ) / 1000
        self.m_PollWidth = float ( pw ) / 1000
        self.m_StartXY = ( CvrtPosition ( sx ), CvrtPosition ( sy ) )
        self.m_TargetXY = ( CvrtPosition ( tx ), CvrtPosition ( ty ) )
        self.m_TargetSection = ( ( CvrtPosition ( tssx ), CvrtPosition ( tssy ) ), ( CvrtPosition ( tsex ), CvrtPosition ( tsey ) ) )

        if ( old_size != self.m_MazeSize ):
            # init maze
            self.InitMaze ()
        self.DrawMaze ()

    ########################################################################
    # Methods for reading maze file
    ########################################################################

    # Get cell index from maze file index
    def GetCellPosFromFileIndex(self, idx, y_first):
        (w, h) = self.m_MazeSize
        if y_first:
            x = idx / h 
            y = idx % h 
            return ( x, y ) 
        else:
            x = idx % w 
            y = idx / w 
            return ( x, y ) 

    def SetMazeFromFileData ( self, y_first=False, wall = WALL_EXIST ): 
        maze = self.m_MazeData
        self.SetAllWalls( WALL_UNKNOWN )

        for idx in range ( len ( maze ) ) :
            xy = self.GetCellPosFromFileIndex ( idx, y_first )
            if maze [ idx ] & WALL_W: 
                self.SetWallXY ( xy, WALL_LU_W, wall, False )
            if maze [ idx ] & WALL_S: 
                self.SetWallXY ( xy, WALL_LU_S, wall, False )
            if maze [ idx ] & WALL_E:
                self.SetWallXY ( xy, WALL_LU_E, wall, False )
            if maze [ idx ] & WALL_N:
                self.SetWallXY ( xy, WALL_LU_N, wall, False )

        self.SetKnownWalls()

    def SetFileDataFromMaze ( self ):
        (w, h) = self.m_MazeSize

        FileData = array('B', ( 0 for x in range( w*h ) ) )

        for y in range ( h ): 
            for x in range ( w ):
                wall = 0
                wall_type = self.GetWallXY ( ( x, y ), WALL_LU_N )
                if wall_type > WALL_UNKNOWN:
                    wall = wall | WALL_N
                
                wall_type = self.GetWallXY ( ( x, y ), WALL_LU_E )
                if wall_type > WALL_UNKNOWN:
                    wall = wall | WALL_E

                wall_type = self.GetWallXY ( ( x, y ), WALL_LU_S )
                if wall_type > WALL_UNKNOWN:
                    wall = wall | WALL_S

                wall_type = self.GetWallXY ( ( x, y ), WALL_LU_W )
                if wall_type > WALL_UNKNOWN:
                    wall = wall | WALL_W

                FileData [ x + y * w ] = wall
        
        self.m_MazeFileData [calcsize("4sI13B256xB"):] = FileData
        self.m_MazeData = self.m_MazeFileData [calcsize("4sI13B256xB"):] 
        self.ToolBar.EnableTool(wx.ID_UNDO, False)
        self.ToolBar.EnableTool(wx.ID_REDO, False)
        self.ToolBar.EnableTool(wx.ID_SAVE, False)

    def ConvertDataOrder ( self, src ):
        (w, h) = self.m_MazeSize
        size = len ( src )
        des = array ( 'B', (0 for x in range(size) ) )

        for idx in range ( size ):
            x = idx / h 
            y = idx % h 
            des [ x + y * w ] = src [ idx ]
        return des

    def ReadMaze ( self, FileName, FileData ): 
        if len ( FileData ) < calcsize("4sI13B256xB"):
            print("[",inspect.currentframe().f_lineno,"] Failed to ReadMaze = ", len(FileData), " < ", calcsize("4sI13B256xB"))
            return False

        # Make buffer and write data to buffer
        (
            Sign,
            HeaderSize,
            Version,
            Width,
            Height,
            BlockWidth,
            WallThick,
            StartX,
            StartY,
            TargetX,
            TargetY,
            TargetSectionSX,
            TargetSectionSY,
            TargetSectionEX,
            TargetSectionEY,
            CheckSum
        ) = unpack_from( "4sI13B256xB", FileData, 0)

        if Sign != bytes("MAZE", "utf-8"):
            print("[",inspect.currentframe().f_lineno,"] Sign(", Sign, ") != MAZE")
            return False

        if HeaderSize+Width*Height != len ( FileData ):
            print("[",inspect.currentframe().f_lineno,"] HeaderSize+Width*Height(", HeaderSize + Width * Height, ") != len(", len(FileData), ")")
            return False

        CheckSum = 0
        for d in FileData [ : HeaderSize ]:
            CheckSum = CheckSum + d 
        CheckSum = CheckSum & 0xff 

        if CheckSum: 
            print("[",inspect.currentframe().f_lineno,"] Check Sum is False")
            return False

        old_size = self.m_MazeSize
        old_block = self.m_BlockWidth
        old_poll = self.m_PollWidth
        self.m_MazeSize                     = ( Width, Height )
        self.m_BlockWidth                   = float ( BlockWidth ) / 1000 
        self.m_PollWidth                    = float ( WallThick ) / 1000
        self.m_StartXY                      = ( StartX, StartY )
        self.m_TargetXY                     = ( TargetX, TargetY )
        self.m_TargetSection                = ( ( TargetSectionSX, TargetSectionSY ), ( TargetSectionEX, TargetSectionEY ) )

        self.m_MazeFileName = FileName 
        self.m_MazeFileData = FileData 
        self.m_MazeData = self.m_MazeFileData [calcsize("4sI13B256xB"):] 
        self.m_UnDoList = []
        self.m_UnDoIndex = 0

        if ( old_size != self.m_MazeSize ):
            # init maze
            self.InitMaze ()
        self.SetMazeFromFileData () 
        return True

    def ReadMazeBinary ( self, FileName, FileData ): 
        w = self.m_MazeSize [ 0 ]
        h = self.m_MazeSize [ 1 ]
        if len ( FileData ) == ( w * h ):
            FileData = self.ConvertDataOrder ( FileData )
            self.m_MazeFileName = FileName + "_"
            self.m_MazeFileData [calcsize("4sI13B256xB"):] = FileData
            self.m_MazeData = self.m_MazeFileData [calcsize("4sI13B256xB"):] 
            self.m_UnDoList = []
            self.m_UnDoIndex = 0
            self.SetMazeFromFileData () 
            return True
        return False

    def WriteMaze ( self ): 
        self.SetFileDataFromMaze ()

        # Build file header
        Sign = "MAZE"
        HeaderSize = calcsize ( "4sI13B256xB" )
        Version = 1
        Width           = self.m_MazeSize [ 0 ]
        Height          = self.m_MazeSize [ 1 ]
        BlockWidth      = int ( self.m_BlockWidth*1000 )
        WallThick       = int ( self.m_PollWidth*1000 )
        StartX          = self.m_StartXY [ 0 ]
        StartY          = self.m_StartXY [ 1 ]
        TargetX         = self.m_TargetXY [ 0 ]
        TargetY         = self.m_TargetXY [ 1 ]
        TargetSectionSX = self.m_TargetSection [ 0 ] [ 0 ]
        TargetSectionSY = self.m_TargetSection [ 0 ] [ 1 ]
        TargetSectionEX = self.m_TargetSection [ 1 ] [ 0 ]
        TargetSectionEY = self.m_TargetSection [ 1 ] [ 1 ]
        Information     = 0
        CheckSum        = 0

        # Make buffer and write header to buffer
        pack_into( "4sI13B256xB", self.m_MazeFileData, 0,
            bytes(Sign, "utf-8"),
            HeaderSize,
            Version,
            Width,
            Height,
            BlockWidth,
            WallThick,
            StartX,
            StartY,
            TargetX,
            TargetY,
            TargetSectionSX,
            TargetSectionSY,
            TargetSectionEX,
            TargetSectionEY,
            CheckSum
        )

        # Calculation check-sum and write it to buffer
        CheckSum = 0
        for d in self.m_MazeFileData [ 0 : HeaderSize ] : 
            CheckSum = CheckSum + d 
        CheckSum = 0x100 - ( CheckSum&0xff )
        self.m_MazeFileData [ HeaderSize-1  ] = CheckSum
        return True

    def FileNewMaze ( self ): 
        self.m_MazeFileName = self.m_Path + os.sep + "New.maz"
        self.m_MazeFileData = None 
        self.m_MazeData = None
        self.m_UnDoList = []
        self.m_UnDoIndex = 0

        # Build file header
        Sign = "MAZE"
        HeaderSize = calcsize ( "4sI13B256xB" )
        Version = 1
        Width           = self.m_MazeSize [ 0 ]
        Height          = self.m_MazeSize [ 1 ]
        BlockWidth      = int ( self.m_BlockWidth*1000 )
        WallThick       = int ( self.m_PollWidth*1000 )
        StartX          = self.m_StartXY [ 0 ]
        StartY          = self.m_StartXY [ 1 ]
        TargetX         = self.m_TargetXY [ 0 ]
        TargetY         = self.m_TargetXY [ 1 ]
        TargetSectionSX = self.m_TargetSection [ 0 ] [ 0 ]
        TargetSectionSY = self.m_TargetSection [ 0 ] [ 1 ]
        TargetSectionEX = self.m_TargetSection [ 1 ] [ 0 ]
        TargetSectionEY = self.m_TargetSection [ 1 ] [ 1 ]
        Information     = 0
        CheckSum        = 0

        # Make buffer and write header to buffer
        FileData = array ( 'B', (0 for x in range(HeaderSize) ) )
        pack_into("4sI13B256xB", FileData, 0,
            bytes(Sign, "utf-8"),       # 4s
            HeaderSize, # I
            Version,    # 13B..1
            Width,      # 13B..2
            Height,     # 13B..3
            BlockWidth, # 13B..4
            WallThick,  # 13B..5
            StartX,     # 13B..6
            StartY,     # 13B..7
            TargetX,    # 13B..8
            TargetY,    # 13B..9
            TargetSectionSX,    # 13B..10
            TargetSectionSY,    # 13B..11
            TargetSectionEX,    # 13B..12
            TargetSectionEY,    # 13B..13
            CheckSum    # B
        )

        # Calculation check-sum and write it to buffer
        CheckSum = 0
        for d in FileData: 
            CheckSum = CheckSum + d 
        CheckSum = 0x100 - ( CheckSum&0xff )
        FileData [ -1 ] = CheckSum

        # Adding data 
        DataSize = Width * Height
        FileData.extend( ( 0 for x in range(DataSize) ) )
        self.m_MazeFileData = FileData
        self.m_MazeData = FileData [calcsize("4sI13B256xB"):]
        self.SetFileName ()
        self.SetMazeFromFileData ()

    def FileSaveMaze ( self ):
        self.WriteMaze ()
        name = self.m_MazeFileName
        data = self.m_MazeFileData

        try:
            f = open(name, "wb")
            data.tofile ( f )
        except:
            msg = "Writing '" + name + "' failed!"
            dlg = wx.MessageDialog(self.m_Parent, msg, 'Save a file', wx.OK | wx.ICON_ERROR )
            dlg.ShowModal()
            dlg.Destroy()
        finally:
            f.close ()

        self.SetFileName ()
        self.m_UnDoList = []
        self.m_UnDoIndex = 0

    def FileSaveAsMaze ( self ):
        wildcard = "Maze files (*.maz)|*.maz|"     \
                   "All files (*.*)|*.*"
        dlg = wx.FileDialog(
            self, message="Save a file as",
            defaultDir=self.m_Path,
            defaultFile=self.m_MazeFileName,
            wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_CHANGE_DIR  | wx.FD_OVERWRITE_PROMPT 
            )

        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            self.m_MazeFileName = paths [ 0 ]
            self.FileSaveMaze ( )
        else:
            dlg.Destroy()
            return
        dlg.Destroy()

    def FileOpenMaze ( self, path = None ): 
        if not self.ConfirmSave ():
            return

        wildcard = "Maze files (*.maz)|*.maz|"     \
                   "All files (*.*)|*.*"
        if not path:
            dlg = wx.FileDialog(
                self, message="Choose a file",
                defaultDir=self.m_Path,
                defaultFile="",
                wildcard=wildcard,
                style=wx.FD_OPEN | wx.FD_CHANGE_DIR  
                )

            if dlg.ShowModal() == wx.ID_OK:
                paths = dlg.GetPaths()
                path = paths [ 0 ]
            else:
                dlg.Destroy()
                return
            dlg.Destroy()

        self.m_MazeFileName = path
        if self.m_Mouse.IsRunning ():
            return

        (w, h) = self.m_MazeSize
        try:
            size = os.path.getsize ( path )
            f = open(path, "rb")
        except:
            msg = "Openning '" + path + "' failed!"
            dlg = wx.MessageDialog(self.m_Parent, msg, 'Open a file', wx.OK | wx.ICON_ERROR )
            dlg.ShowModal()
            dlg.Destroy()
            return 0

        try:
            maze = array ( 'B' )
            maze.fromfile ( f, size ) 
        except:
            msg = "Reading '" + path + "' failed!"
            dlg = wx.MessageDialog(self.m_Parent, msg, 'Open a file', wx.OK | wx.ICON_ERROR )
            dlg.ShowModal()
            dlg.Destroy()
            f.close()
            return 0
        f.close()

        if self.ReadMaze ( path, maze ):
            self.DrawMaze ()
        elif self.ReadMazeBinary ( path, maze ):
            self.DrawMaze ()
        else:
            print("[",inspect.currentframe().f_lineno,"] Failed to ReadMaze")
            return
        self.SetFileName ()

    def ConfirmSave ( self ):
        if self.m_UnDoList and self.m_UnDoIndex != 0:
            msg = 'Save file "%s"' % self.m_MazeFileName
            dlg = wx.MessageDialog(self.m_Parent, msg, 'Save', wx.YES | wx.NO | wx.CANCEL | wx.ICON_WARNING )
            answer = dlg.ShowModal()
            dlg.Destroy()
            if answer == wx.ID_YES:
                self.FileSaveMaze ()
                return True
            if answer == wx.ID_CANCEL:
                return False
        return True

    def SetFileName ( self ):
        name = self.m_MazeFileName
        name = name.split ( '/' ) [-1]
        wx.FindWindowById ( ID_WINDOW_TOP_LEVEL, None ).SetTitle ( AppTitle + '(' + name + ')' )

    ########################################################################
    # Methods for others 
    ########################################################################

    def AddToolbarFile(self, tb):
        tsize = (24,24)
        bmp =  wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR, tsize)
        tb.AddTool(wx.ID_NEW, "New", bmp)
        self.Bind(wx.EVT_TOOL, self.OnToolClick, id=wx.ID_NEW)

        bmp = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, tsize)
        tb.AddTool(wx.ID_OPEN, "Open", bmp)
        self.Bind(wx.EVT_TOOL, self.OnToolClick, id=wx.ID_OPEN)

        bmp =  wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR, tsize)
        tb.AddTool(wx.ID_SAVE, "Save", bmp)
        self.Bind(wx.EVT_TOOL, self.OnToolClick, id=wx.ID_SAVE)
        tb.EnableTool(wx.ID_SAVE, False)

        bmp =  wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR, tsize)
        tb.AddTool(wx.ID_SAVEAS, "Save As", bmp)
        self.Bind(wx.EVT_TOOL, self.OnToolClick, id=wx.ID_SAVEAS)

        tb.AddSeparator()
        bmp =  wx.ArtProvider.GetBitmap(wx.ART_UNDO, wx.ART_TOOLBAR, tsize) 
        tb.AddTool(wx.ID_UNDO, "Undo", bmp)
        self.Bind(wx.EVT_TOOL, self.OnToolClick, id=wx.ID_UNDO)
        tb.EnableTool(wx.ID_UNDO, False)

        bmp =  wx.ArtProvider.GetBitmap(wx.ART_REDO, wx.ART_TOOLBAR, tsize)
        tb.AddTool(wx.ID_REDO, "Redo", bmp)
        self.Bind(wx.EVT_TOOL, self.OnToolClick, id=wx.ID_REDO)
        tb.EnableTool(wx.ID_REDO, False)

    def AddToolbarModeButtons(self, tb, Modes):
        tb.AddSeparator()
        self.ModesDict = {}
        tsize = (24,24)

        for Mode in Modes:
            tool = tb.AddRadioTool(wx.ID_ANY, "Test1", Mode[2])
            self.Bind(wx.EVT_TOOL, self.SetMode, tool)
            self.ModesDict[tool.GetId()] = ( Mode[1], Mode[0] )

        ch = wx.Choice ( tb, - 1, choices = "1 2 3 4 5 6 7 8".split(" ") )
        ch.SetSelection ( 0 )
        tool = tb.AddControl ( ch )
        self.Bind(wx.EVT_CHOICE, self.OnSetCursorSize, ch)

    def AddToolbarZoomButton(self, tb):
        tb.AddSeparator()
        bmp = wx.Bitmap ( "resource/fit.png" )
        tool = tb.AddTool(wx.ID_ANY, "Fit", bmp)
        self.Bind(wx.EVT_TOOL, self.ZoomToFit, tool)

    def BuildToolbar(self):
        TBFLAGS = ( wx.TB_HORIZONTAL
            | wx.NO_BORDER
            | wx.TB_FLAT
            )
        tb = wx.ToolBar(self, style=TBFLAGS)
        self.ToolBar = tb
        tb.SetToolBitmapSize((24,24))
        self.AddToolbarFile(tb)
        self.AddToolbarModeButtons(tb, self.Modes)
        self.AddToolbarZoomButton(tb)
        tb.Realize()

    def SetMode(self, event):
        self.EditMode = self.ModesDict[event.GetId()] [ 1 ]
        Mode = self.ModesDict[event.GetId()] [ 0 ]
        self.Canvas.SetMode(Mode)

        if self.EditMode == "Edit":
            print("Edit")
            self.SetCursor ( True, self.m_Colors [ 'WallExist'] )
        elif self.EditMode == "Erase":
            print("Erase")
            self.SetCursor ( True, self.m_Colors [ 'WallDetected'] )
        elif self.EditMode == "Start":
            print("start")
        elif self.EditMode == "Target":
            print("target")
        else:
            print("SetMode else")
            self.SetCursor ( False )
        self.Canvas.SetFocus()

    def OnSetCursorSize( self, event ):
        num = int ( event.GetString () )
        self.SetCursorSize ( num )

    def ZoomToFit(self,Event):
        self.Canvas.ZoomToBB()
        self.Canvas.SetFocus()

    def OnToolClick ( self, event ):
        id = event.GetId () 

        if id == wx.ID_OPEN:
            self.FileOpenMaze ()
        elif id == wx.ID_SAVE:
            self.FileSaveMaze  ( )
        elif id == wx.ID_NEW:
            self.FileNewMaze () 
            self.DrawMaze ()
        elif id == wx.ID_SAVEAS:
            self.FileSaveAsMaze () 
        elif id == wx.ID_UNDO:
            self.EditUndo () 
        elif id == wx.ID_REDO:
            self.EditRedo () 

    def RunPauseMouse(self, wait=True):
        self.m_Mouse.RunPause ( wait )

    def StopMouse(self, draw=True, wait=True):
        self.m_Mouse.Stop ( wait )
        if draw:
            self.ResetAllWall () 
            self.DrawMaze ()

    def EnableFastestFirstRun ( self, enable ):
        self.m_Mouse.SetEnableFastestFirstRun ( enable )

    def EnableRoutes ( self, enable ):
        self.m_Mouse.SetEnableRoutes  ( enable )

    def OnSize(self, event):
        pass

    def OnPaint(self, evt):
        pass

    def OnNCPaint(self, evt):
        pass

    def OnMove(self, event):
        frame = wx.FindWindowById ( ID_WINDOW_TOP_LEVEL, None )
        frame.SetStatusText("%.2f, %.2f"%tuple(event.Coords))
        # print 'drag', event.Dragging ()
        
        if  self.EditMode == "Edit":
            if event.Dragging ():
                if not self.ControlDown:
                    if self.ShiftDown:
                        self.EditClickedWall ( False )
                    else:
                        self.EditClickedWall ( True )

            self.MoveCursor ( event.Coords )

        elif  self.EditMode == "Erase":
            if event.Dragging ():
                if not self.ControlDown:
                    if self.ShiftDown:
                        self.EditClickedWall ( True )
                    else:
                        self.EditClickedWall ( False )

            self.MoveCursor ( event.Coords )

        event.Skip()

    def LeftDownEvent(self, event):
        if self.m_Mouse.IsRunning ():
            self.RunPauseMouse()
            self.MouseAutoPaused = True

        if self.EditMode == "Edit":
            xy = event.GetPosition()
            xy = self.Canvas.PixelToWorld ( xy )
            if not self.ControlDown:
                if self.ShiftDown:
                    self.EditClickedWall ( False )
                else:
                    self.EditClickedWall ( True )
            self.MoveCursor ( xy )

        elif self.EditMode == "Erase":
            xy = event.GetPosition()
            xy = self.Canvas.PixelToWorld ( xy )
            if not self.ControlDown:
                if self.ShiftDown:
                    self.EditClickedWall ( True )
                else:
                    self.EditClickedWall ( False )
            self.MoveCursor ( xy )

        elif self.EditMode == "Start":
            print("set start")

        elif self.EditMode == "Target":
            xy = event.GetPosition()
            xy = self.Canvas.PixelToWorld ( xy )
            self.SetTarget ( xy )

        self.Canvas._LeftDownEvent(event)
        self.Canvas.SetFocus() 

    def LeftUpEvent(self, event):
        self.Canvas._LeftUpEvent(event)

        if not self.m_Mouse.IsRunning () and self.MouseAutoPaused:
            self.RunPauseMouse()
            self.MouseAutoPaused = False

        self.Canvas.SetFocus() 

    def ShiftEditMode ( self, shift ):
        self.ShiftDown = shift
        if not self.ShiftDown:
            if self.EditMode == "Edit":
                self.SetCursor ( True, self.m_Colors [ 'WallExist'] )
            elif self.EditMode == "Erase":
                self.SetCursor ( True, self.m_Colors [ 'WallDetected'] )
        else:
            if self.EditMode == "Edit":
                self.SetCursor ( True, self.m_Colors [ 'WallDetected'] )
            elif self.EditMode == "Erase":
                self.SetCursor ( True, self.m_Colors [ 'WallExist'] )

    def ControlEditMode ( self, control ):
        self.ControlDown = control
        if self.ControlDown :
            if self.EditMode == "Edit" or self.EditMode == "Erase":
                self.Canvas.SetMode(self.Modes[5][1])
        else:
            if self.EditMode == "Edit" or self.EditMode == "Erase":
                self.Canvas.SetMode(self.Modes[0][1])

    def OnKeyDown ( self, event ):
        ShiftDown = event.ShiftDown()
        ControlDown = event.ControlDown()

        if ShiftDown != self.ShiftDown:
            self.ShiftEditMode ( ShiftDown )

        if ControlDown != self.ControlDown:
            self.ControlEditMode ( ControlDown )

        event.Skip ()

    def OnKeyUp ( self, event ):
        ShiftDown = event.ShiftDown()
        ControlDown = event.ControlDown()

        if ShiftDown != self.ShiftDown:
            self.ShiftEditMode ( ShiftDown )

        if ControlDown != self.ControlDown:
            self.ControlEditMode ( ControlDown )

        event.Skip ()

    def EditClickedWall ( self, enable ):
        BB = self.m_Cursor.BoundingBox
        for i in range ( len ( self.m_Walls ) ) :
            if self.m_Walls [i] and self.m_Walls [i].BoundingBox.Overlaps ( BB ) :
                self.EditWall ( i, enable )
                
    def SetTarget ( self, pt ):
        bw = self.m_BlockWidth
        pw = self.m_PollWidth
        pos = [ int ( ( pt [ 0 ] - pw/2 ) / bw ), int ( ( pt [ 1 ] - pw/2 ) / bw ) ]
        if self.m_TargetXY == pos:
            self.m_TargetXY = [ 255, 255 ]
        else:
            self.m_TargetXY = pos
        print("set target:", self.m_TargetXY)

    def SetTargetSection ( self, pt, start ):
        pos = ( int ( ( pt [ 0 ] - pw/2 ) / bw ), int ( ( pt [ 1 ] - pw/2 ) / bw ) )
        if start:
            self.m_TargetSection [ 0 ] = pos 
        else:
            self.m_TargetSection [ 1 ] = pos 

    def EditClickedWall_old ( self, pt, enable ):
        bw = self.m_BlockWidth
        cw = self.m_BlockWidth / 2
        pw = self.m_PollWidth
        
        def IsOverlaps ( rect1, rect2 ):
            ( sx1, sy1, ex1, ey1 ) = ( rect1 [ 0 ], rect1 [ 1 ], rect1 [ 0 ] + rect1 [ 2 ], rect1 [ 1 ] + rect1 [ 3 ] )
            ( sx2, sy2, ex2, ey2 ) = ( rect2 [ 0 ], rect2 [ 1 ], rect2 [ 0 ] + rect2 [ 2 ], rect2 [ 1 ] + rect2 [ 3 ] )
            if ( (ex1 >= sx2) and (sx1 <= ex2) and
                 (ey1 >= sy2) and (sy1 <= ey2) ):
                return True
            else:
                return False

        p = ( pt [ 0 ] - cw, pt [ 1 ] - cw )
        p = ( pt [ 0 ] + cw, pt [ 1 ] + cw )
        p = ( pt [ 0 ] + cw, pt [ 1 ] - cw )
        p = ( pt [ 0 ] - cw, pt [ 1 ] + cw )
        pos = ( int ( ( pt [ 0 ] - pw/2 ) / bw ), int ( ( pt [ 1 ] - pw/2 ) / bw ) )
        spot = ( pt [ 0 ] - cw, pt [ 1 ] - cw, cw*2, cw*2 )
        print(pos, spot)
        
        wall = self.GetNWallRect( pos )
        if IsOverlaps ( spot, wall ):
            self.EditWall ( self.GetWallIndex ( pos, WALL_LU_N ), enable )
        wall = self.GetEWallRect( pos )
        if IsOverlaps ( spot, wall ):
            self.EditWall ( self.GetWallIndex ( pos, WALL_LU_E ), enable )
        wall = self.GetSWallRect( pos )
        if IsOverlaps ( spot, wall ):
            self.EditWall ( self.GetWallIndex ( pos, WALL_LU_S ), enable )
        wall = self.GetWWallRect( pos )
        if IsOverlaps ( spot, wall ):
            self.EditWall ( self.GetWallIndex ( pos, WALL_LU_W ), enable )

    def EditUndo ( self ):
        undo = self.m_UnDoList
        undoindex = self.m_UnDoIndex

        if undoindex:
            undoindex = undoindex - 1
            ( wall, wall_type, new ) = undo [ undoindex ]
            self.SetWall ( wall, wall_type, True )

            self.ToolBar.EnableTool(wx.ID_REDO, True)
            print("undo", undoindex, wall)
            if undoindex:
                self.ToolBar.EnableTool(wx.ID_UNDO, True)
            else:
                self.ToolBar.EnableTool(wx.ID_UNDO, False)
                
            self.m_UnDoIndex = undoindex 
        
    def EditRedo ( self ):
        undo = self.m_UnDoList
        undoindex = self.m_UnDoIndex

        if undoindex < len ( undo ):
            ( wall, old, wall_type ) = undo [ undoindex ]
            self.SetWall ( wall, wall_type, True )
            undoindex = undoindex + 1

            print("redo", undoindex, wall)
            self.ToolBar.EnableTool(wx.ID_UNDO, True)
            if undoindex < len ( undo ):
                self.ToolBar.EnableTool(wx.ID_REDO, True)
            else:
                self.ToolBar.EnableTool(wx.ID_REDO, False)

            self.m_UnDoIndex = undoindex 

    def EditWall ( self, wall_index, enable ):
        undo = self.m_UnDoList
        undoindex = self.m_UnDoIndex
        old_wall = wall_type = self.GetWall ( wall_index )

        if undoindex < len ( undo ) :
            del undo [ undoindex: ] 

        if enable:
            if wall_type == WALL_UNKNOWN:
                wall_type = WALL_EXIST
            elif wall_type == WALL_NONE:
                wall_type = WALL_DETECTED
        else:
            if wall_type == WALL_EXIST:
                wall_type = WALL_UNKNOWN
            elif wall_type == WALL_DETECTED:
                wall_type = WALL_NONE

        if wall_type == old_wall:
            return

        undo.append( ( wall_index, old_wall, wall_type ) )
        undoindex = len ( undo ) 

        if undo:
            self.ToolBar.EnableTool(wx.ID_UNDO, True)
            self.ToolBar.EnableTool(wx.ID_REDO, False)
            self.ToolBar.EnableTool(wx.ID_SAVE, True)
        else:
            self.ToolBar.EnableTool(wx.ID_UNDO, False)
            self.ToolBar.EnableTool(wx.ID_REDO, False)
            self.ToolBar.EnableTool(wx.ID_SAVE, False)

        self.SetWall ( wall_index, wall_type, True )
        self.m_UnDoList = undo
        self.m_UnDoIndex = undoindex 

    def OnClose ( self ):
        ok = self.ConfirmSave ()
        if ok:
            self.StopMouse(draw=False)
            return True 
        return False

#-------------------------------------------------------------------------------
# Setting panel
#-------------------------------------------------------------------------------

class SettingPanel(wx.Panel):
    def __init__( self, parent, maze, ID=wx.ID_ANY ):
        wx.Panel.__init__ ( self, parent, ID )

        self.Log = wx.FindWindowById ( ID_WINDOW_LOG )
        if self.Log:
            self.Log = self.Log.Log

        self.Maze = wx.FindWindowById ( ID_WINDOW_MAZE )

        self.InitSettings ()

    def InitSettings ( self ):
        ( settings, values ) = self.Maze.GetMazeSettings ()
        self.Values = values
        ToResetLimit = []

        edit_limited = False
        values = list ( values )
        controls = []
        gs = wx.GridBagSizer ( 10, 10 )
        row = 0
        for ( type, limit, name, des ) in settings:

            sizer = wx.BoxSizer ( wx.HORIZONTAL )

            if type == 'MazeSize':
                self.MazeWidth = values [ 0 ]
                self.MazeHeight = values [ 1 ]

                edit = masked.NumCtrl (self,  value=values [ 0 ], min=limit [ 0 ], max=limit [ 1 ], limited=edit_limited, integerWidth=3, allowNegative=False)
                del values [ 0 ]
                controls.append ( edit )
                sizer.Add ( edit, 0, wx.ALIGN_LEFT )
                sizer.AddSpacer ( 5 )

            if type == 'Integer':
                pass

            if type == 'Position':
                _limit = ( limit [ 0 ], self.MazeWidth )
                ToResetLimit.append ( len ( controls ) )

                edit = masked.NumCtrl (self,  value=values [ 0 ], min=_limit [ 0 ], max=_limit [ 1 ], limited=edit_limited, integerWidth=3, allowNegative=False)
                del values [ 0 ]
                controls.append ( edit )
                sizer.Add ( edit, 0, wx.ALIGN_LEFT )
                sizer.AddSpacer ( 5 )

                limit = ( limit [ 1 ], self.MazeWidth )

            if type == 'Description':
                description =  wx.StaticText ( self, - 1, des ) 
                gs.Add ( description, ( row, 0 ), ( 1, 3 ), flag = wx.ALIGN_CENTRE_VERTICAL )
            else:
                edit = masked.NumCtrl (self,  value=values [ 0 ], min=limit [ 0 ], max=limit [ 1 ], limited=edit_limited, integerWidth=3, allowNegative=False)
                del values [ 0 ]
                controls.append ( edit )
                sizer.Add ( edit, 0, wx.ALIGN_LEFT )
                title =  wx.StaticText ( self, - 1, name ) 
                description =  wx.StaticText ( self, - 1, des ) 

                gs.Add ( title, ( row, 0 ), flag = wx.ALIGN_RIGHT | wx.ALIGN_CENTRE_VERTICAL )
                gs.Add ( sizer, ( row, 1 ), flag = wx.ALIGN_CENTRE_VERTICAL )
                gs.Add ( description, ( row, 2 ), flag = wx.ALIGN_CENTRE_VERTICAL )

            row = row + 1

        self.BtnApply = b = wx.Button ( self, -1, "Apply" )
        gs.Add ( b, ( row, 1 ), flag = wx.ALIGN_LEFT | wx.ALIGN_CENTRE_VERTICAL )
        self.Bind(wx.EVT_BUTTON, self.OnClickApply, b)

        s = wx.BoxSizer (wx.HORIZONTAL)
        s.Add ( gs, 1, wx.EXPAND | wx.ALL, 20 )
        self.SetSizer ( s )

        self.Bind(masked.EVT_NUM, self.OnChangedMazeWidth, controls [ 0 ] )
        self.Bind(masked.EVT_NUM, self.OnChangedMazeHeight, controls [ 1 ] )

        self.Controls = controls
        self.ToResetLimit = ToResetLimit 

    def LoadSettings ( self ):
        ( settings, values ) = self.Maze.GetMazeSettings ()
        values = list ( values )

        for Control in self.Controls:
            Control.SetValue ( values [ 0 ] )
            del values [ 0 ]

        # self.BtnApply.Enable ( False )
            
    def SetMax( self, max, IsHeight ):
        for index in self.ToResetLimit:
            self.Controls [ index+IsHeight ].SetMax ( max )

    def IsValueOk( self):
        for Control in self.Controls:
            if not Control.IsInBounds ():
                return False
        return True

    def SaveValue( self ):
        controls  = self.Controls
        values  = list ( self.Values )
        for index in range ( len ( values ) ):
            values [ index ] = controls [ index ].GetValue ()
        
        self.Maze.SaveMazeSetting ( values )

    def OnChangedMazeWidth ( self, event ):
        ctl = event.GetEventObject()
        value = ctl.GetValue()
        self.SetMax( value, 0 )

    def OnChangedMazeHeight ( self, event ):
        ctl = event.GetEventObject()
        value = ctl.GetValue()
        self.SetMax( value, 1 )

    def OnClickApply ( self, event ):
        if self.IsValueOk ():
            self.SaveValue ()
        else:
            msg = "Check bad values!"
            dlg = wx.MessageDialog(self, msg, 'Apply', wx.OK | wx.ICON_ERROR )
            dlg.ShowModal()
            dlg.Destroy()


#-------------------------------------------------------------------------------
# Control and Information Pannel 
ID_BUTTON_START     = 100
ID_BUTTON_STOP      = 101
ID_BUTTON_LOAD_MAZE = 102

class ControlPanel(wx.Panel):
    def __init__(self, parent, ID=wx.ID_ANY, style=wx.TAB_TRAVERSAL):
        wx.Panel.__init__(self, parent, ID, style=style)

        self.Log = wx.FindWindowById ( ID_WINDOW_LOG )
        if self.Log:
            self.Log = self.Log.Log

        maze = self.m_Maze = wx.FindWindowById ( ID_WINDOW_MAZE )

        self.m_Parent = parent
        path = os.getcwd()
        self.m_Path = os.path.join(path, "maze")

        gs = wx.FlexGridSizer ( 7, 1, 5, 5 )
        gs.AddGrowableCol(0)
        b = wx.Button ( self, ID_BUTTON_START, "&Run/Pause" )
        row = 0
        
        self.Bind(wx.EVT_BUTTON, self.OnClickRunPause, b)
        gs.Add ( b, 0, wx.EXPAND )
        row = row + 1
        gs.SetItemMinSize ( 0, 1, 50 )

        self.BtnStop = b = wx.Button ( self, ID_BUTTON_STOP, "&Stop" )
        self.BtnStop.Enable ( False )
        self.Bind(wx.EVT_BUTTON, self.OnClickStopMouse, b)
        gs.Add ( b, 0, wx.EXPAND )
        row = row + 1
        
        self.cbFirstRun = wx.CheckBox ( self, - 1, "Fastest First Run" )
        self.cbFirstRun.SetValue ( False )
        gs.Add ( self.cbFirstRun , 0, wx.EXPAND )
        maze.EnableFastestFirstRun ( False )
        row = row + 1

        self.cbDispRoutes = wx.CheckBox ( self, - 1, "Display Routes" )
        self.cbDispRoutes .SetValue ( True )
        maze.EnableRoutes ( True )
        gs.Add ( self.cbDispRoutes , 0, wx.EXPAND )
        row = row + 1
        gs.AddGrowableRow( row )

        self.tree = wx.TreeCtrl(self, wx.ID_ANY) 
        
        isz = MAZE_SIZE
        il = wx.ImageList(isz[0], isz[1])
        self.fldridx     = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        self.fldropenidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        self.fileidx     = il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))

        self.root = self.tree.AddRoot(self.m_Path)
        self.tree.SetItemData(self.root, None)
        self.tree.SetItemImage(self.root, self.fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root, self.fldropenidx, wx.TreeItemIcon_Expanded)

        self.tree.SetImageList(il)
        self.il = il
        
        gs.Add ( self.tree, 0, wx.EXPAND )
        row = row + 1

        b = wx.Button ( self, ID_BUTTON_LOAD_MAZE, "&Load maze lists" )
        self.Bind(wx.EVT_BUTTON, self.OnClickLoadMazeList, b)
        gs.Add ( b, 0, wx.EXPAND )
        row = row + 1

        self.SetSizer( gs )

        # self.Bind ( wx.EVT_LIST_ITEM_SELECTED, self.OnListBoxSelected, self.maze_list )
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, self.tree)
        self.Bind ( wx.EVT_CHECKBOX, self.OnEnableFirstRun, self.cbFirstRun )
        self.Bind ( wx.EVT_CHECKBOX, self.OnEnableRoutes, self.cbDispRoutes )

        self.LoadMazeList()

    def Setting(self):
        dlg = SettingDialog ( self, self.m_Maze )
        dlg.ShowModal ()

    def FilesInDir(self, path):
        filter_ext = '.maz'
        try:
            flist = os.listdir(path)
        except:
            msg = "'maze' directory is not fond. please make 'maze' directory!"
            dlg = wx.MessageDialog(self.m_Parent, msg, 'LoadMazeFile', wx.OK | wx.ICON_ERROR )
            dlg.ShowModal()
            dlg.Destroy()
            return

        for f in flist:
            next = os.path.join(path, f)
            if os.path.isdir(next):
                # directory
                self.FilesInDir ( next )
            else:
                # file
                ext = os.path.splitext(next)[-1]
                ext = ext.lower()
                if ext == filter_ext:
                    l = len ( self.m_Path )
                    self.maze_list.InsertStringItem (0, next [ l+1: ] )

    def AddFilesInDir(self, path, parent):
        if load_dir == True:
            return
        filter_ext = '.maz'
        try:
            flist = os.listdir(path)
        except:
            msg = "'maze' directory is not fond. please make 'maze' directory!"
            dlg = wx.MessageDialog(self.m_Parent, msg, 'LoadMazeFile', wx.OK | wx.ICON_ERROR )
            dlg.ShowModal()
            dlg.Destroy()
            return

        for f in flist:
            next = os.path.join(path, f)
            name = next.split (os.sep) [ -1 ]
            if os.path.isdir(next):
                # directory
                child = self.tree.AppendItem(parent, name)
                self.tree.SetItemData(child, None)
                self.tree.SetItemImage(child, self.fldridx, wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(child, self.fldropenidx, wx.TreeItemIcon_Expanded)

                self.AddFilesInDir ( next, child )
            else:
                # file
                ext = os.path.splitext(next)[-1]
                ext = ext.lower()
                if ext == filter_ext:
                    l = len ( self.m_Path )
                    item = self.tree.AppendItem ( parent, name )
                    self.tree.SetItemData(item, None)
                    self.tree.SetItemImage(item, self.fileidx, wx.TreeItemIcon_Normal)
                    self.tree.SetItemImage(item, self.fileidx, wx.TreeItemIcon_Selected)
                    # self.maze_list.InsertStringItem (0, next [ l+1: ] )

        self.tree.SortChildren(parent)

    def LoadMazeList(self):
        global load_dir
        self.AddFilesInDir(self.m_Path, self.root)
        self.tree.Expand(self.root)
        load_dir = True
        # (child, cookie) = self.tree.GetFirstChild(self.root)
        # if child.IsOk():
            # self.tree.Expand(child)

    def OnClickRunPause(self, event):
        maze = self.m_Maze
        self.cbFirstRun.Enable ( False )
        self.cbDispRoutes.Enable ( False )
        maze.RunPauseMouse()
        self.BtnStop.Enable ( True )
        self.tree.Enable ( False )

    def OnClickStopMouse(self, event):
        maze = self.m_Maze
        maze.StopMouse()
        self.cbFirstRun.Enable ( True )
        self.cbDispRoutes.Enable ( True )
        self.BtnStop.Enable ( False )
        self.tree.Enable ( True )
        
    def OnEnableFirstRun ( self, event ):
        maze = self.m_Maze
        maze.EnableFastestFirstRun ( event.IsChecked() )

    def OnEnableRoutes ( self, event ):
        maze = self.m_Maze
        print(event.IsChecked())
        maze.EnableRoutes ( event.IsChecked() )

    def OnClickSetting(self, event):
        self.Setting()

    def OnClickLoadMazeList(self, event):
        self.LoadMazeList()

    def OnSelChanged (self, event):
        self.item = event.GetItem()
        if self.item:
            name = self.tree.GetItemText( self.item )
            parent = self.item
            while parent.IsOk ():
                parent = self.tree.GetItemParent ( parent )
                if parent.IsOk ():
                    name = self.tree.GetItemText( parent ) + os.sep + name
            if os.path.isfile ( name ):
                self.m_Maze.FileOpenMaze(name)

    def OnListBoxSelected(self, event):
        sel = event.m_itemIndex
        path = os.path.join(self.m_Path, self.maze_list.GetItemText(sel))
        self.m_Maze.FileOpenMaze(path)

#-------------------------------------------------------------------------------
class MainPanel(wx.Notebook):
    def __init__ ( self, parent, ID = wx.ID_ANY ):
        wx.Notebook.__init__ ( self, parent, ID )
        maze = MazePanel ( self, ID_WINDOW_MAZE )
        self.Setting = setting = SettingPanel ( self, maze, ID_WINDOW_SETTING )

        self.AddPage ( maze, "Maze" )
        self.AddPage ( setting, "Setting" )
   
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def OnPageChanged(self, event):
        new = event.GetSelection()
        if new==1:
            self.Setting.LoadSettings ()

        event.Skip()
   
#-------------------------------------------------------------------------------
# log panel 
class LogPanel(wx.Panel):
    def __init__(self, parent, ID=wx.ID_ANY, style=wx.TAB_TRAVERSAL):
        print("[", inspect.currentframe().f_lineno, "] RUN LogPanel __init__")
        wx.Panel.__init__(self, parent, ID, style=style)

        sizer = wx.BoxSizer ( wx.HORIZONTAL )
        self.MsgWindow = wx.TextCtrl ( 
                self, wx.ID_ANY,
                style = (wx.TE_MULTILINE | wx.TE_READONLY | wx.SUNKEN_BORDER | wx.HSCROLL ) )
        sizer.Add ( self.MsgWindow, 1, wx.EXPAND )
        self.SetSizer ( sizer )
        
    def Log(self, text):
        self.MsgWindow.AppendText(text)
        if not text[-1] == "\n":
            self.MsgWindow.AppendText("\n")

#-------------------------------------------------------------------------------
# Frame
ID_WINDOW_TOP_LEVEL= 1
ID_WINDOW_MAZE     = 2 
ID_WINDOW_SETTING  = 3
ID_WINDOW_CONTROL  = 4
ID_WINDOW_LOG      = 5

ID_MENU_FILE_OPEN   = 100
ID_MENU_FILE_SETUP  = 101
ID_MENU_FILE_EXIT   = 102

FRAME_SIZE_X = 800
FRAME_SIZE_Y = 750
FRAME_SIZE = (FRAME_SIZE_X, FRAME_SIZE_Y)

class AppFrame(wx.Frame):
    def __init__(self, parent, title):
        # create frame
        frame = wx.Frame.__init__(self, parent, ID_WINDOW_TOP_LEVEL, title, size=FRAME_SIZE)

        # Prepare the menu bar
        menuBar = wx.MenuBar()

        # 1st menu from left
        # menu1 = wx.Menu()
        # menu1.Append(ID_MENU_FILE_OPEN, "&Open", "Open Maze")
        # menu1.Append(ID_MENU_FILE_SETUP, "&Setting", "Set up maze") 
        # menu1.Append(ID_MENU_FILE_EXIT, "E&xit", "Exit")
        # menuBar.Append(menu1, "&File")
        # self.SetMenuBar(menuBar)

        # create status bar
        self.m_status = self.CreateStatusBar(1)

        # create splitter
        sty = wx.BORDER_SIMPLE
        sp = wx.SplitterWindow ( self )

        log = LogPanel(sp, ID_WINDOW_LOG, style=sty)
        main = MainPanel ( sp )
        sp.SplitHorizontally(main, log, FRAME_SIZE_Y)
        sp.SetSashGravity ( 1 )
        sp.SetMinimumPaneSize(60)

        # set frame at center
        self.Center()

        # set event handler
        # self.Bind(wx.EVT_MENU, self.OpenFile, id=ID_MENU_FILE_OPEN)
        # self.Bind(wx.EVT_MENU, self.SetupMaze, id=ID_MENU_FILE_SETUP)
        # self.Bind(wx.EVT_MENU, self.CloseWindow, id=ID_MENU_FILE_EXIT)
        # self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind ( wx.EVT_CLOSE, self.OnCloseApp )

    def OpenFile(self, event):
        pass

    def SetupMaze(self, event):
        pass

    def CloseWindow(self, event):
        self.Close()
        
    def OnKeyDown(self, evt):
        keycode = evt.GetKeyCode()
        print("Frame KeyDown=", keycode)

    def PostInit(self):
        maze = wx.FindWindowById ( ID_WINDOW_MAZE, None )
        if maze:
            maze.PostInit ()

    def OnCloseApp(self, event):
        maze = wx.FindWindowById ( ID_WINDOW_MAZE, None )
        if maze:
            if maze.ConfirmSave ():
                maze.StopMouse (draw = False)
                event.Skip()

#-------------------------------------------------------------------------------
# Application
AppTitle = "GSDSim3 Micro Mouse Simulator"

# Program Start
class AppMain(wx.App):
    print("Program Start")
    def OnInit(self):
        frame = AppFrame(None, AppTitle)
        self.SetTopWindow(frame)
        frame.Show (True)
        frame.PostInit () 
        return True

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    app = AppMain(redirect=False)
    app.MainLoop()


