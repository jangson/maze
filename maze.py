
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

# .maz file format description
# Using one byte per block. Bit description is below.
#           | Known |  wall |
#           | 1  / 0| 1 / 0 |
# bits      7 6 5 4 3 2 1 0
#           +-+-+-+-+-+-+-+-+
# direction |W|S|E|N|W|S|E|N|
#           +-+-+-+-+-+-+-+-+

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

WALL_N = 1
WALL_E = 2
WALL_S = 4
WALL_W = 8
WALL_N_D = 0x10
WALL_E_D = 0x20
WALL_S_D = 0x40
WALL_W_D = 0x80

#---------------------------------------------------------------------------
# Maze Panel 
class MazePanel(wx.Panel):
    def __init__(self, parent, ID=wx.ID_ANY, style=wx.TAB_TRAVERSAL):
        wx.Panel.__init__(self, parent, -1, style=style)

        # Init maze variable
        self.m_Parent = parent
        self.m_XCnt = 16
        self.m_YCnt = 16
        self.m_BlockWidth = 180   # 180 milimeter
        self.m_PollWidth  = 12    # Real size is 12 mm
        self.m_MaxW = float(self.m_BlockWidth * self.m_XCnt + self.m_PollWidth)
        self.m_MaxH = float(self.m_BlockWidth * self.m_YCnt + self.m_PollWidth)
        
        self.m_Maze = array ( 'B', (0 for x in range ( self.m_XCnt * self.m_YCnt )))
        self.SetKnownWall()
        self.m_MazeLoad = self.m_Maze

        ## Init Mouse
        self.m_Mouse = mouse.Mouse(self) 
        way = self.m_BlockWidth - self.m_PollWidth  
        self.m_MousePos = ( way/2+self.m_PollWidth, way/2+self.m_PollWidth )
        self.m_Mouse.SetMousePosMM ( self.m_MousePos  ) 

        # Setup panel
        self.SetBackgroundColour ( wx.Colour ( 0, 0, 0 ) ) 
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def SetMaze ( self, maze_size, wblock, wpoll, mouse_pos, mouse_size ): 
        self.m_XCnt = maze_size [ 0 ]
        self.m_YCnt = maze_size [ 1 ]
        self.m_BlockWidth = wblock 
        self.m_PollWidth  = wpoll 

        self.m_MaxW = float(self.m_BlockWidth * self.m_XCnt + self.m_PollWidth)
        self.m_MaxH = float(self.m_BlockWidth * self.m_YCnt + self.m_PollWidth)
        # self.m_Maze = array ( 'B', (0 for x in range ( self.m_XCnt * self.m_YCnt )))
        self.SetKnownWall()

        self.m_MousePos = mouse_pos

        self.m_Mouse.SetMousePosMM ( self.m_MousePos  ) 
        self.m_Mouse.SetMouseSize ( mouse_size )
        self.Refresh ()

    def GetMaze ( self ): 
        return ( ( self.m_XCnt, self.m_YCnt ),
                 self.m_BlockWidth,
                 self.m_PollWidth,
                 self.m_MousePos,
                 self.m_Mouse.GetMouseSize() )

    def LoadMaze ( self, path ): 
        try:
            f = open(path, "rb")
        except:
            msg = "Openning '" + path + "' failed!"
            dlg = wx.MessageDialog(self.m_Parent, msg, 'LoadMaze', wx.OK | wx.ICON_ERROR )
            dlg.ShowModal()
            dlg.Destroy()
            return 0

        try:
            maze = array ( 'B' )
            maze.fromfile(f, self.m_XCnt*self.m_YCnt)
        except:
            msg = "Reading '" + path + "' failed!"
            dlg = wx.MessageDialog(self.m_Parent, msg, 'LoadMaze', wx.OK | wx.ICON_ERROR )
            dlg.ShowModal()
            dlg.Destroy()
            return 0
        f.close()

        if len ( maze ) != self.m_XCnt*self.m_YCnt:
            msg = "File size is so short. check maze file!"
            dlg = wx.MessageDialog(self.m_Parent, msg, 'LoadMaze', wx.OK | wx.ICON_ERROR )
            dlg.ShowModal()
            dlg.Destroy()
        else:
            name = path.replace ( '\\', '/' )
            name = name.split ( '/' ) [-1]
            wx.FindWindowById ( ID_WINDOW_TOP_LEVEL, None ).SetTitle ( AppTitle + '(' + name + ')' )
            self.m_MazeLoad = maze
            self.m_Maze = maze
            self.SetKnownWall()
            self.Refresh ()

    def DrawPoll(self, dc, x, y):
        dc.SetPen(wx.RED_PEN)
        dc.SetBrush(wx.RED_BRUSH)
        x = self.m_BlockWidth * x
        y = self.m_BlockWidth * y
        dc.DrawRectangle(x, y, self.m_PollWidth, self.m_PollWidth)

    def ClearWallData(self, x, y, wall):
        idx = x * self.m_YCnt + y
        self.m_Maze [ idx ] = self.m_Maze [ idx ] & ( ~wall )  

    def SetWallData(self, x, y, wall):
        idx = x * self.m_YCnt + y
        self.m_Maze [ idx ] = self.m_Maze [ idx ] | wall  

    def GetWallData(self, x, y):
        return self.m_Maze [ x * self.m_YCnt + y ] 

    def SetKnownWall(self):
        for y in range ( 0, self.m_YCnt ):
            self.SetWallData ( 0, y, WALL_W_D | WALL_W )
            self.SetWallData ( self.m_XCnt-1, y, WALL_E_D | WALL_E )
            
        for x in range ( 0, self.m_XCnt ):
            self.SetWallData ( x, 0, WALL_S_D | WALL_S )
            self.SetWallData ( x, self.m_YCnt-1, WALL_N_D | WALL_N )

    def GetScreenXY(self, x, y):
        return [ x, self.m_YCnt - y - 1 ]

    def DrawWall(self, dc, x, y, wall):
        [x, y] = self.GetScreenXY ( x, y ) 

        found = 0

        if wall & WALL_N:
            if wall & WALL_N_D:
                found = 1
            x = self.m_BlockWidth * x + self.m_PollWidth
            y = self.m_BlockWidth * y
            w = self.m_BlockWidth - self.m_PollWidth
            h = self.m_PollWidth

        elif wall & WALL_E:
            if wall & WALL_E_D:
                found = 1
            x = self.m_BlockWidth * (x + 1)
            y = self.m_BlockWidth * y + self.m_PollWidth
            w = self.m_PollWidth
            h = self.m_BlockWidth - self.m_PollWidth

        elif wall & WALL_S:
            if wall & WALL_S_D:
                found = 1
            x = self.m_BlockWidth * x + self.m_PollWidth
            y = self.m_BlockWidth * (y + 1)
            w = self.m_BlockWidth - self.m_PollWidth
            h = self.m_PollWidth

        elif wall & WALL_W:
            if wall & WALL_W_D:
                found = 1
            x = self.m_BlockWidth * x
            y = self.m_BlockWidth * y + self.m_PollWidth
            w = self.m_PollWidth
            h = self.m_BlockWidth - self.m_PollWidth

        else:
            return

        if found:
            dc.SetPen(wx.RED_PEN)
            dc.SetBrush(wx.RED_BRUSH)
        else:
            dc.SetPen(wx.GREEN_PEN)
            dc.SetBrush(wx.TRANSPARENT_BRUSH)

        dc.DrawRectangle(x, y, w, h)

    def DrawUpdatedWall(self, dc, x, y):
        self.DrawWall ( x, y, self.GetWallData(x, y) )
        
    def DrawAllWall ( self, dc ):
        (w, h) = dc.GetSize();
        scaleX = float(float(w)/self.m_MaxW)
        scaleY = float(float(h)/self.m_MaxH)
        #print "scale ", (scaleX, scaleY)
        dc.SetUserScale(min(scaleX, scaleY), min(scaleX, scaleY))

        for x in range(0, self.m_XCnt+1):
            for y in range(0, self.m_YCnt+1):
                self.DrawPoll(dc, x, y)

        for x in range(0, self.m_XCnt):
            for y in range(0, self.m_YCnt):
                self.DrawWall ( dc, x, y, self.GetWallData ( x, y ) & (WALL_N_D|WALL_N) )
                self.DrawWall ( dc, x, y, self.GetWallData ( x, y ) & (WALL_W_D|WALL_W) )
                if x == self.m_XCnt-1:
                    self.DrawWall ( dc, x, y, self.GetWallData ( x, y ) & (WALL_E_D|WALL_E) )
                if y == 0:
                    self.DrawWall ( dc, x, y, self.GetWallData ( x, y ) & (WALL_S_D|WALL_S) )

        self.m_Mouse.DrawMouse ( dc ) 

    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.Clear()
        self.DrawAllWall( dc )


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

        t1 = wx.StaticText(self, -1, "Maze Size w, h(4~64)", style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)
        self.e_maze_w = e1 = masked.NumCtrl (self,  value = maze_size [ 0 ], min=4, max=64, limited=edit_limited, integerWidth=2, allowNegative=False)
        self.e_maze_h = e2 = masked.NumCtrl (self,  value = maze_size [ 1 ], min=4, max=64, limited=edit_limited, integerWidth=2, allowNegative=False)

        sizer = wx.BoxSizer ( wx.HORIZONTAL )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e1, wx.ALIGN_LEFT )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e2, wx.ALIGN_LEFT )
        gs.Add ( t1, 0, wx.EXPAND )
        gs.Add ( sizer, 0, wx.EXPAND )

        t1 = wx.StaticText(self, -1, "Block width(50~300mm)", style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
        self.e_block_w = e1 = masked.NumCtrl (self,  value=wblock, min=50, max=300, limited=edit_limited, integerWidth=3, allowNegative=False)

        sizer = wx.BoxSizer ( wx.HORIZONTAL )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e1, wx.ALIGN_LEFT )
        gs.Add ( t1, 0, wx.EXPAND )
        gs.Add ( sizer, 0, wx.EXPAND )

        t1 = wx.StaticText(self, -1, "Poll width(4~30mm)", style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
        self.e_poll_w = e1 = masked.NumCtrl (self,  value=wpoll, min=4, max=30, limited=edit_limited, integerWidth=2, allowNegative=False)

        sizer = wx.BoxSizer ( wx.HORIZONTAL )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e1, wx.ALIGN_LEFT )
        gs.Add ( t1, 0, wx.EXPAND )
        gs.Add ( sizer, 0, wx.EXPAND )

        t1 = wx.StaticText(self, -1, "Mouse position x,y(50~300mm)", style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
        self.e_mouse_x = e1 = masked.NumCtrl (self,  value=mouse_pos[0], min=50, max=300, limited=edit_limited, integerWidth=3, allowNegative=False)
        self.e_mouse_y = e2 = masked.NumCtrl (self,  value=mouse_pos[1], min=50, max=300, limited=edit_limited, integerWidth=3, allowNegative=False)

        sizer = wx.BoxSizer ( wx.HORIZONTAL )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e1, wx.ALIGN_LEFT )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e2, wx.ALIGN_LEFT )
        gs.Add ( t1, 0, wx.EXPAND )
        gs.Add ( sizer, 0, wx.EXPAND )
        
        t1 = wx.StaticText(self, -1, "Mouse size w, h (20~300mm)", style = wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE )
        self.e_mouse_w = e1 = masked.NumCtrl (self,  value=mouse_size[0], min=20, max=300, limited=edit_limited, integerWidth=3, allowNegative=False)
        self.e_mouse_h = e2= masked.NumCtrl (self,  value=mouse_size[1], min=20, max=300, limited=edit_limited, integerWidth=3, allowNegative=False)

        sizer = wx.BoxSizer ( wx.HORIZONTAL )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e1, wx.ALIGN_LEFT )
        sizer.AddSpacer ( 10 )
        sizer.Add ( e2, wx.ALIGN_LEFT )
        gs.Add ( t1, 0, wx.EXPAND )
        gs.Add ( sizer, 0, wx.EXPAND )
        
        b1 = wx.Button(self, wx.ID_OK)
        b2 = wx.Button(self, wx.ID_CANCEL)
        gs.Add ( b1, 0, wx.EXPAND )
        gs.Add ( b2, 0, wx.EXPAND )

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
                self.m_Maze.LoadMaze ( paths [ 0 ] )

            dlg.Destroy()
        else:
            self.m_Maze.LoadMaze ( path )

    def Setting(self):
        dlg = SettingDialog ( self, self.m_Maze )
        dlg.ShowModal ()

    def FilesInDir(self, path):
        filter_ext = '.maz'
        try:
            flist = os.listdir(path)
        except:
            msg = "'maze' directory is not fond. please make 'maze' directory!"
            dlg = wx.MessageDialog(self.m_Parent, msg, 'LoadMaze', wx.OK | wx.ICON_ERROR )
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
        self.maze_list.ClearAll ()
        self.maze_list.InsertColumn ( 0, "" )
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
        print "RunStop" 
        
    def OnClickStopMouse(self, event):
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

        
        # create panel
        panel_maze = MazePanel(splitter, -1, style= ( sty | wx.FULL_REPAINT_ON_RESIZE ) )
        panel_ctl = ControlPanel(splitter, panel_maze, ID_WINDOW_CONTROL, style=sty)
        splitter.SplitVertically(panel_maze, panel_ctl, frame_size_x)
        splitter.SetSashGravity ( 1 )
        splitter.SetMinimumPaneSize(180)

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
        return True

#---------------------------------------------------------------------------
if __name__ == '__main__':
    app = AppMain(redirect=False)
    app.MainLoop()


