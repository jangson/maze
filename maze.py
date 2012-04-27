
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
import  thread
from    scipy import integrate
import  numpy as N

import  wx
import  wx.lib.newevent
import  wx.lib.masked           as masked
import  wx.lib.rcsizer          as rcs
from    wx.lib.floatcanvas import FloatCanvas, Resources, GUIMode

import  mycanvas
import  mouse

#-------------------------------------------------------------------------------
# Maze Panel 
#-------------------------------------------------------------------------------

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

class MazePanel(mycanvas.NavCanvas):
    def __init__(self, parent, ID=wx.ID_ANY, style=wx.TAB_TRAVERSAL):
        mycanvas.NavCanvas.__init__(self, parent, -1, style=style, BackgroundColor = ( 20, 20, 20 ) )
        self.m_Parent = parent

        path = os.getcwd()
        self.m_Path = os.path.join(path, "maze")

        # mouse
        self.LoadMouseImage ()
        self.m_MousePoly = None
        self.m_MouseRoute = None
        self.m_MouseObject = None
        self.m_Mouse = mouse.Mouse(self) 

        # Init default maze variables
        self.m_Colors = NAZE_COLORS
        self.m_MazeSize = MAZE_SIZE
        self.m_BlockWidth = MAZE_BLOCK_WIDTH
        self.m_PollWidth  = MAZE_POLL_WIDTH
        self.m_StartXY = MAZE_START_POSITION
        self.m_TargetXY = MAZE_TARGET_POSITION
        self.m_TargetSection = MAZE_TARGET_SECTION

        # Initialize maze
        ( w, h ) = self.m_MazeSize
        self.m_MaxW = float(self.m_BlockWidth * w + self.m_PollWidth)
        self.m_MaxH = float(self.m_BlockWidth * h + self.m_PollWidth)
        self.m_Walls = None
        self.m_WallInfos = None
        self.m_WallPoints1 = None
        self.m_WallPoints2 = None
        self.m_LookupWall = None
        self.m_TypeWalls = None
        self.InitMaze ()

        # mouse
        size = MOUSE_SIZE
        way = self.m_BlockWidth - self.m_PollWidth  
        pos = ( way/2+self.m_PollWidth, way/2+self.m_PollWidth )

        self.m_MouseSize = size
        self.m_MousePos = pos
        self.m_MouseAngle = radians(0)

        # others
        self.MouseAutoPaused = False

        # Setup panel
        # self.Bind(wx.EVT_SIZE, self.OnSize)
        # self.Bind(wx.EVT_PAINT, self.OnPaint)
        # self.Bind(wx.EVT_NC_PAINT, self.OnNCPaint)
        self.Canvas.Bind(FloatCanvas.EVT_MOTION, self.OnMove) 
        self.Canvas.Bind ( wx.EVT_KEY_DOWN, self.OnKeyDown )
        self.Canvas.Bind ( wx.EVT_LEFT_DOWN, self.LeftDownEvent )
        self.Canvas.Bind ( wx.EVT_LEFT_UP, self.LeftUpEvent )
        

    def Log ( self, text ):
        log = wx.FindWindowById ( ID_WINDOW_TOP_LEVEL, None )
        log.Log ( text )
            

    ########################################################################
    # Methods for initialization
    ########################################################################
    def InitMaze ( self ):
        self.m_Polls = []
        self.m_Walls, self.m_LookupWall = [], []
        self.m_TypeWalls = []
        self.Canvas.InitAll()
        w = self.m_BlockWidth / 3
        color = self.m_Colors['MazeBorder']
        obj = self.Canvas.AddRectangle ( 
                ( 0, 0 ), 
                ( self.m_MaxW, self.m_MaxH ), 
                LineColor = color, 
                LineWidth = 1, 
                FillColor = None,
                InForeground = False
                )

        self.m_Polls = self.MakePolls ()
        self.m_Walls = []
        self.m_WallLines = []
        self.m_WallInfos = []
        self.m_WallPoints1 = []
        self.m_WallPoints2 = []
        self.MakeWalls ()
        self.m_LookupWall = self.MakeLookUpWall ()
        self.m_TypeWalls = [ WALL_UNKNOWN ] * len(self.m_Walls)  
        self.SetKnownWalls()
        self.InitMouse ()
        self.FileNewMaze () 

    def LoadMouseImage ( self, filename = "mouse.png" ):
        if USE_MOUSE_IMAGE:
            bmp = wx.Bitmap( filename )        
            img = bmp.ConvertToImage()
            self.m_MouseImage = img 

    def InitMouse ( self ):
        # if self.m_MousePoly:
            # Canvas.RemoveObject ( self.m_MousePoly )
            # self.m_MousePoly = None
            # 
        # if self.m_MouseObject:
            # Canvas.RemoveObject ( self.m_MouseObject )
            # self.m_MouseObject = None
            # 
        # if self.m_MouseRoute:
            # for objs in self.m_MouseRoute:
                # for obj in objs:
                    # Canvas.RemoveObject ( obj )
            # self.m_MouseRoute = []

        self.m_Mouse.InitMouse()

    def ResetMouse ( self ):
        mazesize = self.m_MazeSize
        start = self.m_StartXY
        target = self.m_TargetXY
        target_section = self.m_TargetSection

        if target [ 0 ] >= mazesize [ 0 ] or target [ 1 ] >= mazesize [ 1 ]:
            target = None

        self.m_Mouse.SetMouse(self.m_MousePos, self.m_MouseAngle, self.m_BlockWidth, self.m_PollWidth, start, target, target_section, drawtime = 0.04)

    def PostInit ( self ):
        self.DrawMaze ()
        pass


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
            self.m_WallPoints1.append ( None )
            self.m_WallPoints2.append ( None )
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
        self.m_WallPoints1.append ( point )
        self.m_WallPoints2.append ( point2 )
        wall.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.OnWallClick)
        wallline.Bind(FloatCanvas.EVT_FC_LEFT_DOWN, self.OnWallClick)
        
    
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
        objs = self.m_WallPoints1
        for obj in objs:
            if obj:
                obj.Hide ()
        objs = self.m_WallPoints2
        for obj in objs:
            if obj:
                obj.Hide ()
        objs = self.m_WallInfos
        for obj in objs:
            if obj:
                obj.Hide ()

        if draw:
            self.Canvas.Draw ( )

    def EnableWallPoints1 ( self, walls, enable, draw = True ):
        objs = self.m_WallPoints1
        for index in walls:
            if objs [ index ] :
                objs [ index ].Visible = enable 
        
        if draw:
            self.Canvas.Draw ( )

    def EnableWallPoints2 ( self, walls, enable, draw = True ):
        objs = self.m_WallPoints2
        for index in walls:
            if objs [ index ] :
                objs [ index ].Visible = enable 
        
        if draw:
            self.Canvas.Draw ( )

    def EnableAllWallInformation ( self, enable, draw = True ):
        objs = self.m_WallInfos
        for obj in objs:
            if obj:
                obj.Visible = enable 
        
        if draw:
            self.Canvas.Draw ( )

    def SetAllWallInformation ( self, infos ):
        objs = self.m_WallInfos
        for index in range ( len ( objs ) ) :
            if objs [ index ]:
                objs [ index ].SetText ( infos [ index ] )

    def GetAllWalls ( self ):
        return self.m_TypeWalls
    
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
        index = self.m_LookupWall [ xy [ 1 ] ] [ xy [ 0 ] ] [ nesw ]
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
        
        if wall:
            wall.SetLineColor ( color ) 
            wall.SetLineStyle ( lstyle ) 
            wall.SetFillColor ( fcolor )
            wall.SetFillStyle ( fstyle )
            line.SetLineColor ( color )
            line.SetLineStyle ( lstyle ) 
            # line.SetLineWidth ( 2 ) 

        if draw:
            self.Canvas._DrawObject ( line )
            self.Canvas._DrawObject ( wall )

    def DrawAllWalls ( self, draw = True ):
        for index in range ( len ( self.m_TypeWalls ) ) :
            self.DrawWall( index, False ) 

        if draw:
            self.Canvas.Draw ( )

    def DrawMaze ( self ):
        self.DrawAllWalls ( False )
        self.ClearAllWallInfos ( False ) 
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

        self.PanCanvasForObject ( self.m_MousePoly )

        if redraw:
            Canvas.Draw ()

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

    ########################################################################
    # Methods for changing maze setting
    ########################################################################
    def GetMaze ( self ): 
        maze_size = self.m_MazeSize
        wblock = self.m_BlockWidth * 1000
        wpoll = self.m_PollWidth * 1000
        mouse_pos = ( self.m_MousePos [ 0 ] * 1000, self.m_MousePos [ 1 ] * 1000 )
        mouse_size = ( self.m_MouseSize [ 0 ] * 1000, self.m_MouseSize [ 1 ] * 1000 )
        return ( maze_size,
                 wblock,
                 wpoll,
                 mouse_pos,
                 mouse_size )

    def SetMaze ( self, maze_size, wblock, wpoll, mouse_pos, mouse_size ): 
        self.m_MazeSize = maze_size
        self.m_BlockWidth = ( float ( wblock ) / 1000 )
        self.m_PollWidth  = ( float ( wpoll )  / 1000 )

        self.m_MousePos  = ( mouse_pos [ 0 ] / 1000, mouse_pos [ 1 ] / 1000 )
        self.m_MouseSize = ( float ( mouse_size [ 0 ] ) / 1000, float ( mouse_size [ 1 ] ) / 1000 )

        # init maze
        ( w, h ) = self.m_MazeSize
        self.m_MaxW = float(self.m_BlockWidth * w + self.m_PollWidth)
        self.m_MaxH = float(self.m_BlockWidth * h + self.m_PollWidth)

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

        if Sign != "MAZE":
            return False

        if HeaderSize+Width*Height != len ( FileData ):
            return False

        CheckSum = 0
        for d in FileData [ : HeaderSize ]:
            CheckSum = CheckSum + d 
        CheckSum = CheckSum & 0xff 

        if CheckSum: 
            return False

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
            return True
        return False

    def FileNewMaze ( self ): 
        self.m_MazeFileName = "New.maz"
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
        pack_into( "4sI13B256xB", FileData, 0,
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
        self.SetFileDataFromMaze ()
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
            return 0

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
            self.SetMazeFromFileData () 
            self.DrawMaze ()

        elif self.ReadMazeBinary ( path, maze ):
            self.SetMazeFromFileData () 
            self.DrawMaze ()
        else:
            return
        self.SetFileName ()

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
        tb.AddLabelTool(wx.ID_NEW, "New", bmp, shortHelp="New file", longHelp="")
        self.Bind(wx.EVT_TOOL, self.OnToolClick, id=wx.ID_NEW)

        bmp = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, tsize)
        tb.AddLabelTool(wx.ID_OPEN, "Open", bmp, shortHelp="Open file", longHelp="")
        self.Bind(wx.EVT_TOOL, self.OnToolClick, id=wx.ID_OPEN)

        bmp =  wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR, tsize)        
        tb.AddLabelTool(wx.ID_SAVE, "Save", bmp, shortHelp="Save file", longHelp="")
        self.Bind(wx.EVT_TOOL, self.OnToolClick, id=wx.ID_SAVE)
        tb.EnableTool(wx.ID_SAVE, False)

        bmp =  wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR, tsize)        
        tb.AddLabelTool(wx.ID_SAVEAS, "Save As", bmp, shortHelp="Save file as", longHelp="")
        self.Bind(wx.EVT_TOOL, self.OnToolClick, id=wx.ID_SAVEAS)

        tb.AddSeparator()
        bmp =  wx.ArtProvider.GetBitmap(wx.ART_UNDO, wx.ART_TOOLBAR, tsize)        
        tb.AddLabelTool(wx.ID_UNDO, "Undo", bmp, shortHelp="Undo", longHelp="")
        self.Bind(wx.EVT_TOOL, self.OnToolClick, id=wx.ID_UNDO)
        tb.EnableTool(wx.ID_UNDO, False)

        bmp =  wx.ArtProvider.GetBitmap(wx.ART_REDO, wx.ART_TOOLBAR, tsize)        
        tb.AddLabelTool(wx.ID_REDO, "Redo", bmp, shortHelp="Redo", longHelp="")
        self.Bind(wx.EVT_TOOL, self.OnToolClick, id=wx.ID_REDO)
        tb.EnableTool(wx.ID_REDO, False)

    def AddToolbarModeButtons(self, tb, Modes):
        tb.AddSeparator()
        self.ModesDict = {}
        for Mode in Modes:
            tool = tb.AddRadioTool(wx.ID_ANY, shortHelp=Mode[0], bitmap=Mode[2])
            self.Bind(wx.EVT_TOOL, self.SetMode, tool)
            self.ModesDict[tool.GetId()]=Mode[1]
        #self.ZoomOutTool = tb.AddRadioTool(wx.ID_ANY, bitmap=Resources.getMagMinusBitmap(), shortHelp = "Zoom Out")
        #self.Bind(wx.EVT_TOOL, lambda evt : self.SetMode(Mode=self.GUIZoomOut), self.ZoomOutTool)

    def AddToolbarZoomButton(self, tb):
        self.ZoomButton = wx.Button(tb, label="Fit", style=wx.BORDER_NONE)
        tb.AddControl(self.ZoomButton)
        self.ZoomButton.Bind(wx.EVT_BUTTON, self.ZoomToFit)

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

    def OnToolClick ( self, event ):
        print "Tool Clicked", event.GetId ()
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

    def StopMouse(self):
        self.m_Mouse.Stop ()
        self.SetMazeFromFileData () 
        self.DrawMaze ()

    def OnSize(self, event):
        pass

    def OnPaint(self, evt):
        pass

    def OnNCPaint(self, evt):
        pass

    def OnMove(self, event):
        frame = wx.FindWindowById ( ID_WINDOW_TOP_LEVEL, None )
        frame.SetStatusText("%.2f, %.2f"%tuple(event.Coords))
        event.Skip()
            
    def LeftDownEvent(self, event):
        if self.m_Mouse.IsRunning ():
            self.RunPauseMouse()
            self.MouseAutoPaused = True
        self.Canvas._LeftDownEvent(event)

    def LeftUpEvent(self, event):
        self.Canvas._LeftUpEvent(event)
        if not self.m_Mouse.IsRunning () and self.MouseAutoPaused:
            self.RunPauseMouse()
            self.MouseAutoPaused = False

    def OnKeyDown ( self, event ):
        print "key###"
        self.Canvas.KeyDownEvent( event )    
        event.Skip ()

    def EditUndo ( self ):
        undo = self.m_UnDoList
        undoindex = self.m_UnDoIndex

        if undoindex:
            undoindex = undoindex - 1
            ( wall, wall_type, new ) = undo [ undoindex ]
            self.SetWall ( wall, wall_type, True )

            self.ToolBar.EnableTool(wx.ID_REDO, True)
            print "undo", undoindex, wall
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

            print "redo", undoindex, wall
            self.ToolBar.EnableTool(wx.ID_UNDO, True)
            if undoindex < len ( undo ):
                self.ToolBar.EnableTool(wx.ID_REDO, True)
            else:
                self.ToolBar.EnableTool(wx.ID_REDO, False)

            self.m_UnDoIndex = undoindex 

    def EditWall ( self, wall_index ):
        undo = self.m_UnDoList
        undoindex = self.m_UnDoIndex
        old_wall = wall_type = self.GetWall ( wall_index )

        if undoindex < len ( undo ) :
            del undo [ undoindex: ] 

        if wall_type <= WALL_UNKNOWN:
            wall_type = WALL_EXIST
        else:
            wall_type = WALL_NONE

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

    def OnWallClick ( self, Object ):
        index = int ( Object.Name )
        self.EditWall ( index )

#-------------------------------------------------------------------------------
# Setting dialog
class SettingDialog(wx.Dialog):
    def __init__(
        self, parent, maze, ID=-1, title="Settings", size=wx.DefaultSize, pos=wx.DefaultPosition, 
        style=wx.DEFAULT_DIALOG_STYLE,
        useMetal=False,
        ):
        wx.Dialog.__init__( self, parent, ID, title )
        
        # setting parameter
        self.m_Maze = maze;
        ( maze_size, wblock, wpoll, mouse_pos, mouse_size ) = self.m_Maze.GetMaze ()
        print maze_size, wblock, wpoll, mouse_pos, mouse_size
        
        # control 
        edit_limited = False

        gs = wx.GridSizer ( 6, 2 )

        t1 = wx.StaticText ( self, - 1, "Maze Size w, h(4~64)" )
        self.e_maze_w = e1 = masked.NumCtrl (self,  value = maze_size [ 0 ], min=4, max=64, limited=edit_limited, integerWidth=3, allowNegative=False)
        self.e_maze_h = e2 = masked.NumCtrl (self,  value = maze_size [ 1 ], min=4, max=64, limited=edit_limited, integerWidth=3, allowNegative=False)

        sizer = wx.BoxSizer ( wx.HORIZONTAL )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e1, wx.ALIGN_LEFT )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e2, wx.ALIGN_LEFT )
        gs.Add ( t1, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL )
        gs.Add ( sizer, 0, wx.ALIGN_CENTER_VERTICAL )

        t1 = wx.StaticText ( self, - 1, "Block width(50~300mm)" )
        self.e_block_w = e1 = masked.NumCtrl (self,  value=wblock, min=50, max=300, limited=edit_limited, integerWidth=3, allowNegative=False)

        sizer = wx.BoxSizer ( wx.HORIZONTAL )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e1, wx.ALIGN_LEFT )
        gs.Add ( t1, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL )
        gs.Add ( sizer, 0, wx.ALIGN_CENTER_VERTICAL )

        t1 = wx.StaticText ( self, - 1, "Poll width(4~30mm)" )
        self.e_poll_w = e1 = masked.NumCtrl (self,  value=wpoll, min=4, max=30, limited=edit_limited, integerWidth=3, allowNegative=False)

        sizer = wx.BoxSizer ( wx.HORIZONTAL )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e1, wx.ALIGN_LEFT )
        gs.Add ( t1, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL )
        gs.Add ( sizer, 0, wx.ALIGN_CENTER_VERTICAL )

        t1 = wx.StaticText ( self, - 1, "Mouse position x,y(50~300mm)" )
        self.e_mouse_x = e1 = masked.NumCtrl (self,  value=mouse_pos[0], min=50, max=300, limited=edit_limited, integerWidth=3, allowNegative=False)
        self.e_mouse_y = e2 = masked.NumCtrl (self,  value=mouse_pos[1], min=50, max=300, limited=edit_limited, integerWidth=3, allowNegative=False)

        sizer = wx.BoxSizer ( wx.HORIZONTAL )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e1, wx.ALIGN_LEFT )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e2, wx.ALIGN_LEFT )
        gs.Add ( t1, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL )
        gs.Add ( sizer, 0, wx.ALIGN_CENTER_VERTICAL )
        
        t1 = wx.StaticText ( self, - 1, "Mouse size w, h (20~300mm)" )
        self.e_mouse_w = e1 = masked.NumCtrl (self,  value=mouse_size[0], min=20, max=300, limited=edit_limited, integerWidth=3, allowNegative=False)
        self.e_mouse_h = e2= masked.NumCtrl (self,  value=mouse_size[1], min=20, max=300, limited=edit_limited, integerWidth=3, allowNegative=False)

        sizer = wx.BoxSizer ( wx.HORIZONTAL )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e1, wx.ALIGN_LEFT )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e2, wx.ALIGN_LEFT )
        gs.Add ( t1, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL )
        gs.Add ( sizer, 0, wx.ALIGN_CENTER_VERTICAL )
        
        b1 = wx.Button(self, wx.ID_OK)
        b2 = wx.Button(self, wx.ID_CANCEL)
        gs.Add ( b1, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL )
        gs.Add ( b2, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL )

        self.SetSizer( gs )

        self.Bind(wx.EVT_BUTTON, self.OnButton)
        
    def IsValueOk( self):
        if not self.e_maze_w.IsInBounds ():
            return False
        if not self.e_maze_h.IsInBounds ():
            return False
        if not self.e_block_w.IsInBounds ():        
            return False
        if not self.e_poll_w.IsInBounds ():
            return False
        if not self.e_mouse_x.IsInBounds ():
            return False
        if not self.e_mouse_y.IsInBounds ():
            return False
        if not self.e_mouse_w.IsInBounds ():
            return False
        if not self.e_mouse_h.IsInBounds ():
            return False
        return True
        
    def SetMaze (self):
        if not self.IsValueOk ():
            return False

        # ( maze_size, wblock, wpoll, mouse_pos, mouse_size ) = self.m_Maze.GetMaze ()
        self.m_Maze.SetMaze (
                    ( self.e_maze_w.GetValue (), self.e_maze_h.GetValue () ), 
                    self.e_block_w.GetValue (),
                    self.e_poll_w.GetValue (),
                    ( self.e_mouse_x.GetValue (), self.e_mouse_y.GetValue () ),
                    ( self.e_mouse_w.GetValue (), self.e_mouse_h.GetValue () )
                ) 
        return True

    def OnButton(self, evt):
        #print "Button=", evt.GetId (), wx.ID_OK
        if evt.GetId () == wx.ID_OK:
            if self.SetMaze ():
                evt.Skip ()
        else:
            evt.Skip ()

#-------------------------------------------------------------------------------
# Control and Information Pannel 
ID_BUTTON_START     = 10
ID_BUTTON_STOP      = 20
ID_BUTTON_SETTING   = 30
ID_BUTTON_LOAD_MAZE = 40

class ControlPanel(wx.Panel):
    def __init__(self, parent, maze, ID=wx.ID_ANY, style=wx.TAB_TRAVERSAL):
        wx.Panel.__init__(self, parent, ID, style=style)

        self.m_Parent = parent
        self.m_Maze = maze
        path = os.getcwd()
        self.m_Path = os.path.join(path, "maze")

        gs = wx.FlexGridSizer ( 5, 1 )
        b = wx.Button ( self, ID_BUTTON_START, "&Run/Pause mouse" )
        
        self.Bind(wx.EVT_BUTTON, self.OnClickRunPause, b)
        gs.Add ( b, 0, wx.EXPAND )
        gs.SetItemMinSize ( 0, 1, 50 )

        b = wx.Button ( self, ID_BUTTON_STOP, "&Stop mouse" )
        self.Bind(wx.EVT_BUTTON, self.OnClickStopMouse, b)
        gs.Add ( b, 0, wx.EXPAND )

        b = wx.Button ( self, ID_BUTTON_SETTING, "&Setting" )
        self.Bind(wx.EVT_BUTTON, self.OnClickSetting, b)
        gs.Add ( b, 0, wx.EXPAND )

        self.maze_list = wx.ListCtrl(self, -1, style = wx.LC_REPORT | wx.LC_NO_HEADER | wx.LC_SINGLE_SEL | wx.LC_SORT_ASCENDING )
        # self.maze_list.SetColumnWidth ( 0, wx.LIST_AUTOSIZE ) 
        self.maze_list.InsertColumn ( 0, "" )
        self.maze_list.SetColumnWidth ( 0, 200 )
        gs.Add ( self.maze_list, 0, wx.EXPAND )

        b = wx.Button ( self, ID_BUTTON_LOAD_MAZE, "&Load maze lists" )
        self.Bind(wx.EVT_BUTTON, self.OnClickLoadMazeList, b)
        gs.Add ( b, 0, wx.EXPAND )

        gs.AddGrowableCol(0)
        gs.AddGrowableRow(3)

        self.SetSizer( gs )

        self.Bind ( wx.EVT_LIST_ITEM_SELECTED, self.OnListBoxSelected, self.maze_list )
        self.Bind ( wx.EVT_KEY_DOWN, self.OnKeyDown )
        self.Bind ( wx.EVT_CLOSE, self.OnCloseApp )

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
            return;

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

    def LoadMazeList(self):
        self.maze_list.DeleteAllItems()
        self.FilesInDir(self.m_Path)
        self.maze_list.GetItemCount ()
        self.maze_list.SetItemState(0,
                wx.LIST_STATE_FOCUSED|wx.LIST_STATE_SELECTED, 
                wx.LIST_STATE_FOCUSED|wx.LIST_STATE_SELECTED)

    def OnKeyDown(self, event):
        keycode = event.GetKeyCode()
        print "KeyDown=", keycode

        if keycode == wx.WXK_ESCAPE:
           self.CloseApp(None) 
        
        # if keycode == 'r' or keycode == 'R':
            # self.OnClickRunStop(self, None)
# 
        # if keycode == 's' or keycode == 'S':
            # self.OnClickSetting(self, None)

    def OnClickRunPause(self, event):
        maze = self.m_Maze
        maze.RunPauseMouse()
        
    def OnClickStopMouse(self, event):
        maze = self.m_Maze
        maze.StopMouse()

    def OnClickSetting(self, event):
        self.Setting()

    def OnClickLoadMazeList(self, event):
        self.LoadMazeList()

    def OnListBoxSelected(self, event):
        sel = event.m_itemIndex
        path = os.path.join(self.m_Path, self.maze_list.GetItemText(sel))
        self.m_Maze.FileOpenMaze(path)

    def OnCloseApp(self, event):
        evt = wx.CloseEvent(wx.wxEVT_CLOSE_WINDOW)
        wx.PostEvent(self.GetParent().GetParent(), evt)
    


#-------------------------------------------------------------------------------
# log panel 
class LogPanel(wx.Panel):
    def __init__(self, parent, ID=wx.ID_ANY, style=wx.TAB_TRAVERSAL):
        wx.Panel.__init__(self, parent, ID, style=style)

        sizer = wx.BoxSizer ( wx.HORIZONTAL )
        self.MsgWindow = wx.TextCtrl ( 
                self, wx.ID_ANY,
                style = (wx.TE_MULTILINE | wx.TE_READONLY | wx.SUNKEN_BORDER | wx.HSCROLL ) )
        sizer.Add ( self.MsgWindow, 1, wx.EXPAND )
        self.SetSizer ( sizer )
        

#-------------------------------------------------------------------------------
# Frame
ID_WINDOW_TOP_LEVEL= 1
ID_WINDOW_CONTROL  = 10

ID_MENU_FILE_OPEN   = 100
ID_MENU_FILE_SETUP  = 101
ID_MENU_FILE_EXIT   = 102

frame_size_x = 800
frame_size_y = 750

class AppFrame(wx.Frame):
    def __init__(self, parent, title):
        # create frame
        frame = wx.Frame.__init__(self, parent, ID_WINDOW_TOP_LEVEL, title, size=(frame_size_x, frame_size_y))

        # Prepare the menu bar
        menuBar = wx.MenuBar()

        # 1st menu from left
        menu1 = wx.Menu()
        menu1.Append(ID_MENU_FILE_OPEN, "&Open", "Open Maze")
        menu1.Append(ID_MENU_FILE_SETUP, "&Setting", "Set up maze") 
        menu1.Append(ID_MENU_FILE_EXIT, "E&xit", "Exit")
        menuBar.Append(menu1, "&File")
        self.SetMenuBar(menuBar)

        # create status bar
        self.m_status = self.CreateStatusBar(1)

        # create splitter
        sty = wx.BORDER_SIMPLE
        splitter_main = wx.SplitterWindow(self, -1)

        splitter = wx.SplitterWindow(splitter_main, -1)
        panel_log = LogPanel(splitter_main, -1, style=sty)
        splitter_main.SplitHorizontally(splitter, panel_log, frame_size_y)
        splitter_main.SetSashGravity ( 1 )
        splitter_main.SetMinimumPaneSize(60)
        self.LogPanel = panel_log

        
        # create panel
        panel_maze = MazePanel(splitter, -1, style= ( sty | wx.FULL_REPAINT_ON_RESIZE ) )
        panel_ctl = ControlPanel(splitter, panel_maze, ID_WINDOW_CONTROL, style=sty)
        splitter.SplitVertically(panel_maze, panel_ctl, frame_size_x)
        splitter.SetSashGravity ( 1 )
        splitter.SetMinimumPaneSize(180)
        self.panel_maze = panel_maze 

        # set frame at center
        self.Center()

        # set event handler
        self.Bind(wx.EVT_MENU, self.OpenFile, id=ID_MENU_FILE_OPEN)
        self.Bind(wx.EVT_MENU, self.SetupMaze, id=ID_MENU_FILE_SETUP)
        self.Bind(wx.EVT_MENU, self.CloseWindow, id=ID_MENU_FILE_EXIT)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def OpenFile(self, event):
        wnd = wx.FindWindowById ( ID_WINDOW_CONTROL, self )
        self.panel_maze.FileOpenMaze ()

    def SetupMaze(self, event):
        wnd = wx.FindWindowById ( ID_WINDOW_CONTROL, self )
        wnd.Setting ()

    def CloseWindow(self, event):
        self.Close()
    
    def Log(self, text):
        self.LogPanel.MsgWindow.AppendText(text)
        if not text[-1] == "\n":
            self.LogPanel.MsgWindow.AppendText("\n")
        print text
        
    def OnKeyDown(self, evt):
        keycode = evt.GetKeyCode()
        print "Frame KeyDown=", keycode

#-------------------------------------------------------------------------------
# Application
AppTitle = "GSDSim3 Micro Mouse Simulator"

class AppMain(wx.App):
    def OnInit(self):
        frame = AppFrame(None, AppTitle)
        self.SetTopWindow(frame)
        frame.Show(True)
        frame.panel_maze.PostInit ( )
        return True

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    app = AppMain(redirect=False)
    app.MainLoop()


