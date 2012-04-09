
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
from    array import *
from    math  import *
import  re
import  thread

import  wx
import  wx.lib.newevent
import  wx.lib.masked           as masked
import  wx.lib.rcsizer          as rcs

import  mouse

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
WALL_EXIST      = 1
WALL_DETECTED   = 2

# Wall index for lookup
WALL_LU_W   = 0
WALL_LU_S   = 1
WALL_LU_E   = 2
WALL_LU_N   = 3

# Default mouse definition
MOUSE_SIZE      = ( 60, 80 )

NAZE_COLORS = {
        'Background'        : ( 20, 20, 20 ),
        'MazeBorder'        : 'Red',
        'Poll'              : 'Red',
        'WallExist'         : 'Green',
        'WallDetected'      : 'Red'
} 

#---------------------------------------------------------------------------
# Maze Panel 
# class Wall(wx.Window):
    # def __init__(self, parent, ID=wx.ID_ANY, style=wx.TAB_TRAVERSAL):
    


#---------------------------------------------------------------------------
# Maze Panel 
try:
    from floatcanvas import NavCanvas, FloatCanvas, Resources
except ImportError: # if it's not there locally, try the wxPython lib.
    from wx.lib.floatcanvas import NavCanvas, FloatCanvas, Resources
import wx.lib.colourdb
import time, random

class MazePanel(NavCanvas.NavCanvas):
    def __init__(self, parent, ID=wx.ID_ANY, style=wx.TAB_TRAVERSAL):
        NavCanvas.NavCanvas.__init__(self, parent, -1, style=style, BackgroundColor = ( 20, 20, 20 ) )


        # Init default maze variables
        self.m_Parent = parent
        self.m_Colors = NAZE_COLORS
        self.m_MazeSize = ( 16, 16 )
        self.m_BlockWidth = 180   # 180 milimeter
        self.m_PollWidth  = 12    # Real size is 12 mm

        # Initialize maze
        ( w, h ) = self.m_MazeSize
        self.m_MaxW = float(self.m_BlockWidth * w + self.m_PollWidth)
        self.m_MaxH = float(self.m_BlockWidth * h + self.m_PollWidth)
        self.m_Walls = None
        self.m_LookupWall = None
        self.m_TypeWalls = None
        self.m_MazeFile = array ( 'B', (0 for x in range ( self.m_MazeSize [0] * self.m_MazeSize [1] )))
        self.InitMaze ()

        # mouse
        self.m_Mouse = mouse.Mouse(self) 
        size = MOUSE_SIZE
        way = self.m_BlockWidth - self.m_PollWidth  
        pos = ( way/2+self.m_PollWidth, way/2+self.m_PollWidth )

        self.m_MouseSize = size
        self.m_MousePosInit = self.m_MousePos = pos
        self.m_MouseAngle = radians(0)
        self.m_Mouse.SetMousePos ( self.m_MousePos  ) 
        self.m_Mouse.SetMouseSize ( self.m_MouseSize  ) 
        self.m_MouseImage = None
        self.m_MouseObject = None
        self.InitMouse () 

        # Setup panel
        # self.Bind(wx.EVT_SIZE, self.OnSize)
        # self.Bind(wx.EVT_PAINT, self.OnPaint)
        # self.Bind(wx.EVT_NC_PAINT, self.OnNCPaint)

        # screen scale
        self.m_Redraw = True;
        self.m_Scale = None
        
    def Log ( self, text ):
        log = wx.FindWindowById ( ID_WINDOW_TOP_LEVEL, None )
        log.Log ( text )
            
    ########################################################################
    # Methods for initialization
    ########################################################################
    def InitMouse ( self ):
        self.m_MousePos = self.m_MousePosInit
        pass
        
    def InitMaze ( self ):
        self.m_Polls = []
        self.m_Walls, self.m_LookupWall = [], []
        self.m_TypeWalls = []
        self.m_MouseObject = None
        self.Canvas.InitAll()
        w = self.m_BlockWidth / 3
        color = self.m_Colors['MazeBorder']
        self.Canvas.AddRectangle ( 
                ( 0, 0 ), 
                ( self.m_MaxW, self.m_MaxH ), 
                LineColor = color, 
                LineWidth = 1, 
                FillColor = None )

        self.m_Polls = self.MakePolls ()
        ( self.m_Walls, self.m_LookupWall ) = self.MakeWalls ()
        self.m_TypeWalls = [ WALL_NONE ] * len(self.m_Walls)  
        self.SetKnownWall()

    def LoadMouseImage ( self, filename = "mouse.png" ):
        size = self.m_MouseSize 
        bmp = wx.Bitmap( filename )        
        img = bmp.ConvertToImage()
        img.Rescale ( size [ 0 ] , size [ 1 ] )
        self.m_MouseImage = img 
        
    # This methos have to call after all class initialzed because DrawMouse() required it
    def PostInit ( self ):
        self.LoadMouseImage ()
        self.DrawMaze ()

    ########################################################################
    # Methods for Making wall, poll
    ########################################################################
    # Get cell index from maze file index
    def GetCellPosFromFileIndex(self, idx):
        (w, h) = self.m_MazeSize
        x = idx / h 
        y = idx % h 
        return ( x, y ) 

    # Change maze x, y to screen x, y
    def GetDrawXY(self, pos):
        ( x, y ) = pos
        return ( x, y )

    def MakePoll(self, pos):
        [x, y] = self.GetDrawXY ( pos ) # change to screen position 
        x = self.m_BlockWidth * x
        y = self.m_BlockWidth * y
        return ( x, y , self.m_PollWidth, self.m_PollWidth)

    def MakeNorthWall( self, pos ):
        [x, y] = self.GetDrawXY ( pos ) # change to screen position 
        x1 = self.m_BlockWidth * x + self.m_PollWidth
        y1 = self.m_BlockWidth * ( y + 1 )
        w1 = self.m_BlockWidth - self.m_PollWidth
        h1 = self.m_PollWidth
        return ( x1, y1, w1, h1 ) 

    def MakeEastWall( self, pos ):
        [x, y] = self.GetDrawXY ( pos ) # change to screen position 
        x1 = self.m_BlockWidth * (x + 1)
        y1 = self.m_BlockWidth * y + self.m_PollWidth
        w1 = self.m_PollWidth
        h1 = self.m_BlockWidth - self.m_PollWidth
        return ( x1, y1, w1, h1 ) 

    def MakeSouthWall( self, pos ):
        [x, y] = self.GetDrawXY ( pos ) # change to screen position 
        x1 = self.m_BlockWidth * x + self.m_PollWidth
        y1 = self.m_BlockWidth * y
        w1 = self.m_BlockWidth - self.m_PollWidth
        h1 = self.m_PollWidth
        return ( x1, y1, w1, h1 ) 

    def MakeWestWall( self, pos ):
        [x, y] = self.GetDrawXY ( pos ) # change to screen position 
        x1 = self.m_BlockWidth * x
        y1 = self.m_BlockWidth * y + self.m_PollWidth
        w1 = self.m_PollWidth
        h1 = self.m_BlockWidth - self.m_PollWidth
        return ( x1, y1, w1, h1 ) 

    def MakeWSENWalls ( self, pos ):
        return (
                self.MakeWestWall (pos),
                self.MakeSouthWall (pos),
                self.MakeEastWall (pos),
                self.MakeNorthWall (pos) )

    def MakePolls ( self ): 
        color = self.m_Colors [ 'Poll']
        polls = []
        ( w, h ) = self.m_MazeSize

        for y in range(0, h+1):
            for x in range(0, w+1):
                poll = self.MakePoll( ( x, y ) ) 
                pos = ( poll [0], poll [1] )
                size = ( poll [2], poll [3] )
                canvas = self.Canvas
                polls.append ( canvas.AddRectangle ( pos, size, LineColor = color, FillColor = color ) )

        # print len ( polls )
        return polls

    def MakeWalls ( self ): 
        walls = []
        lookup_walls = []
        ( w, h ) = self.m_MazeSize
        for y in range(0, h):
            for x in range(0, w):
                # Get W,S,E,N walls 
                wall_WSEN = self.MakeWSENWalls ( ( x, y ) ) 

                # Add W,S,E,N walls except added wall and make lookup table
                lookup = []
                for wall in wall_WSEN: 
                    try: # checking exist wall
                        w_idx = walls.index ( wall ) 
                        lookup.append ( w_idx )
                        continue
                    except:
                        pos = ( wall [0], wall [1] )
                        size = ( wall [2], wall [3] )
                        canvas = self.Canvas
                        walls.append ( canvas.AddRectangle ( pos, size, LineColor = None, FillColor = None ) )
                        lookup.append ( len ( walls ) - 1 )
                
                lookup_walls.append ( lookup )

        return ( walls, lookup_walls )


    ########################################################################
    # Methods for maze access
    ########################################################################
    # Get cell index from cell x, y position
    def GetCellIndex(self, pos):
        ( x, y ) = pos
        ( w, h ) = self.m_MazeSize
        return x + y * w

    def GetWall ( self, pos, type ):
        idx_wall_wsen = self.m_LookupWall [ self.GetCellIndex ( pos ) ] 
        return self.m_TypeWalls [ idx_wall_wsen [ type ] ]

    def SetWall (self, pos, type, wall, draw = False):
        idx_wall = self.m_LookupWall [ self.GetCellIndex ( pos ) ] 
        self.m_TypeWalls [ idx_wall[type] ] = wall

    def SetAllWall (self, type):
        self.m_TypeWalls = [ type ] * len(self.m_Walls) 
        
    def SetKnownWall(self):
        ( w, h ) = self.m_MazeSize
        for y in range ( 0, h ):
            self.SetWall( ( 0, y ), WALL_LU_W, WALL_DETECTED )
            self.SetWall( ( w-1, y ), WALL_LU_E, WALL_DETECTED )
            
        for x in range ( 0, w ):
            self.SetWall( ( x, 0 ), WALL_LU_S, WALL_DETECTED )
            self.SetWall( ( x, h - 1 ), WALL_LU_N, WALL_DETECTED )


    ########################################################################
    # Methods for drawing
    ########################################################################
    def DrawWall ( self, wall, type, redraw = True ):
        colors = self.m_Colors
        color = None 
        fcolor = None 
        lstyle = None
        fstyle = None
        if type == WALL_NONE:
            pass
        elif type == WALL_EXIST:
            color = colors [ 'WallExist']
            lstyle = 'Solid'
        elif type == WALL_DETECTED:
            fcolor = color = colors [ 'WallDetected']
            fstyle = lstyle = 'Solid'
        else:
            self.Log ( "Unknown wall type" )
            return
        
        wall.SetLineColor ( color ) 
        wall.SetLineStyle ( lstyle ) 
        wall.SetFillColor ( fcolor )
        wall.SetFillStyle ( fstyle )

        if redraw:
            self.Canvas.Draw ( )

    def DrawAllWalls ( self, redraw = True ):
        walls = self.m_Walls
        for idx in range ( len ( self.m_TypeWalls ) ) :
            self.DrawWall( walls [ idx ], self.m_TypeWalls[ idx ], False ) 

        if redraw:
            self.Canvas.Draw ( )

    def DrawMouse( self, pos, angle, redraw = True ):
        img = self.m_MouseImage
        if not img:
            return

        pos = ( self.m_MousePos [ 0 ], self.m_MousePos [ 1 ] + 5 )

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

        self.m_MousePos = pos

        if redraw:
            self.Canvas.Draw ( )

    def DrawMaze ( self ):
        self.InitMouse ()
        self.DrawAllWalls ( False )
        self.DrawMouse ( self.m_MousePos, self.m_MouseAngle, False )
        self.Canvas.ZoomToBB()

    def DrawUpdatedWall(self, dc, x, y):
        self.DrawWall ( x, y, self.GetWallData(x, y) )

    ########################################################################
    # Methods for changing maze setting
    ########################################################################
    def GetMaze ( self ): 
        return ( self.m_MazeSize,
                 self.m_BlockWidth,
                 self.m_PollWidth,
                 self.m_MousePosInit,
                 self.m_MouseSize )

    def SetMaze ( self, maze_size, wblock, wpoll, mouse_pos, mouse_size ): 
        self.m_MazeSize = maze_size
        self.m_BlockWidth = wblock 
        self.m_PollWidth  = wpoll 

        self.m_MousePosInit = mouse_pos
        self.m_MouseSize = mouse_size

        # init maze
        ( w, h ) = self.m_MazeSize
        self.m_MaxW = float(self.m_BlockWidth * w + self.m_PollWidth)
        self.m_MaxH = float(self.m_BlockWidth * h + self.m_PollWidth)

        self.InitMaze ()
        self.DrawMaze () 

    ########################################################################
    # Methods for reading maze file
    ########################################################################
    def SetMazeFromFileData ( self, maze ): 
        self.SetAllWall( WALL_NONE )

        for idx in range ( len ( maze ) ) :
            pos = self.GetCellPosFromFileIndex ( idx )
            if maze [ idx ] & WALL_W: 
                self.SetWall ( pos, WALL_LU_W, WALL_EXIST )
            if maze [ idx ] & WALL_S: 
                self.SetWall ( pos, WALL_LU_S, WALL_EXIST )
            if maze [ idx ] & WALL_E:
                self.SetWall ( pos, WALL_LU_E, WALL_EXIST )
            if maze [ idx ] & WALL_N:
                self.SetWall ( pos, WALL_LU_N, WALL_EXIST )

        self.SetKnownWall()

    def LoadMazeFile ( self, path ): 
        (w, h) = self.m_MazeSize
        try:
            f = open(path, "rb")
        except:
            msg = "Openning '" + path + "' failed!"
            dlg = wx.MessageDialog(self.m_Parent, msg, 'LoadMazeFile', wx.OK | wx.ICON_ERROR )
            dlg.ShowModal()
            dlg.Destroy()
            return 0

        try:
            maze = array ( 'B' )
            maze.fromfile ( f, w * h ) 
        except:
            msg = "Reading '" + path + "' failed!"
            dlg = wx.MessageDialog(self.m_Parent, msg, 'LoadMazeFile', wx.OK | wx.ICON_ERROR )
            dlg.ShowModal()
            dlg.Destroy()
            f.close()
            return 0
        f.close()

        if len ( maze ) != w * h:
            msg = "File size is so short. check maze file!"
            dlg = wx.MessageDialog(self.m_Parent, msg, 'LoadMazeFile', wx.OK | wx.ICON_ERROR )
            dlg.ShowModal()
            dlg.Destroy()
        else:
            name = path.replace ( '\\', '/' )
            name = name.split ( '/' ) [-1]
            wx.FindWindowById ( ID_WINDOW_TOP_LEVEL, None ).SetTitle ( AppTitle + '(' + name + ')' )
            #print maze
            self.SetMazeFromFileData ( maze ) 
            self.DrawMaze ()
            self.m_MazeFile = maze

    ########################################################################
    # Methods for others 
    ########################################################################
    def OnSize(self, event):
        pass

    def OnPaint(self, evt):
        pass

    def OnNCPaint(self, evt):
        pass


#---------------------------------------------------------------------------
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

#---------------------------------------------------------------------------
# Control and Information Pannel 
ID_BUTTON_START     = 10
ID_BUTTON_STOP      = 20
ID_BUTTON_SETTING   = 30
ID_BUTTON_LOAD_MAZE = 40
wildcard = "Maze files (*.maz)|*.maz|"     \
           "All files (*.*)|*.*"

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

    def OpenMaze(self, path = None):
        if not path:
            dlg = wx.FileDialog(
                self, message="Choose a file",
                defaultDir=self.m_Path,
                defaultFile="",
                wildcard=wildcard,
                style=wx.OPEN | wx.CHANGE_DIR
                )

            if dlg.ShowModal() == wx.ID_OK:
                paths = dlg.GetPaths()
                self.m_Maze.LoadMazeFile ( paths [ 0 ] )

            dlg.Destroy()
        else:
            self.m_Maze.LoadMazeFile ( path )

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
        print "run/pause"
        maze = self.m_Maze
        maze.DrawMouse ( ( 30, 200 ), radians ( 0 ) )
        
    def OnClickStopMouse(self, event):
        maze = self.m_Maze
        maze.DrawMouse ( ( 30, 300 ), radians ( 45 ) )
        print "stop mouse"

    def OnClickSetting(self, event):
        self.Setting()

    def OnClickLoadMazeList(self, event):
        self.LoadMazeList()

    def OnListBoxSelected(self, event):
        sel = event.m_itemIndex
        path = os.path.join(self.m_Path, self.maze_list.GetItemText(sel))
        self.OpenMaze(path)

    def OnCloseApp(self, event):
        evt = wx.CloseEvent(wx.wxEVT_CLOSE_WINDOW)
        wx.PostEvent(self.GetParent().GetParent(), evt)
    


#---------------------------------------------------------------------------
# Control and Information Pannel 
class LogPanel(wx.Panel):
    def __init__(self, parent, ID=wx.ID_ANY, style=wx.TAB_TRAVERSAL):
        wx.Panel.__init__(self, parent, ID, style=style)

        sizer = wx.BoxSizer ( wx.HORIZONTAL )
        self.MsgWindow = wx.TextCtrl ( 
                self, wx.ID_ANY,
                style = (wx.TE_MULTILINE | wx.TE_READONLY | wx.SUNKEN_BORDER | wx.HSCROLL ) )
        sizer.Add ( self.MsgWindow, 1, wx.EXPAND )
        self.SetSizer ( sizer )
        

#---------------------------------------------------------------------------
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
        wnd.OpenMaze ()

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

#---------------------------------------------------------------------------
# Application
AppTitle = "GSDSim3 Micro Mouse Simulator"

class AppMain(wx.App):
    def OnInit(self):
        frame = AppFrame(None, AppTitle)
        self.SetTopWindow(frame)
        frame.Show(True)
        frame.panel_maze.PostInit ( )
        return True

#---------------------------------------------------------------------------
if __name__ == '__main__':
    app = AppMain(redirect=False)
    app.MainLoop()


