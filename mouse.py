
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
import  threading
import  queue

import  wx
import  wx.lib.newevent
import  wx.lib.masked           as masked
import  wx.lib.rcsizer          as rcs

MAZE_SIZE           = ( 16, 16 )

USE_MOUSE_IMAGE = False
DRAW_MOUSE = True

MOUSE_CMD_PAUSE     = 2
MOUSE_CMD_STOP      = 10

MOUSE_SIZE      = ( 0.060, 0.080 )
MOUSE_CENTER    = ( 30, 40 )
MOUSE_L_WHEEL   = ( 2, 40 )
MOUSE_R_WHEEL   = ( 58, 40 )
        
#---------------------------------------------------------------------------
# MouseEnv 
#---------------------------------------------------------------------------

Directions = {
    'N'     :  0,
    'NE'    :  1,
    'E'     :  2,
    'SE'    :  3,
    'S'     :  4,
    'SW'    :  5,
    'W'     :  6,
    'NW'    :  7,
}

Turns = {
    'T0'    : 0,
    'TR45'  : 1,
    'TR90'  : 2,
    'TR135' : 3,
    'T180'  : 4,
    'TL135' : 5,
    'TL90'  : 6,
    'TL45'  : 7,
}
TSTOP = 8

class MouseEnv():
    def __init__(self, parent):

        # wheel and mouse size
        size = self.m_MouseSize = MOUSE_SIZE 
        self.wl = MOUSE_SIZE [ 0 ]

        # mouse velocity and acceleration
        self.vl = self.vr = 0.
        self.sl = self.sr = 0.

        # real mouse position and angle for movement calculation
        self.pc = [ 0., 0. ] 
        self.angle = radians ( 0. )

        # draw time 
        self.starttime = 0.
        self.currtime = 0.
        self.drawtime = 0.02
        self.drawedtime = 0.0
        self.FastestFirstRun = False
        self.EnableFastestFirstRun = False
        self.EnableRoutes = False

        # maze property 
        self.block = 0.180
        self.poll = 0.012
        self.MazeSize = MAZE_SIZE
        self.MazeStart = None
        self.MazeTarget = None
        self.MazeTargetSection = None 
        self.Walls = []
        self.WallMarks = []

        # mouse position(x, y), direction in maze
        self.mpos = 35
        self.mdir = 0

        # wall index 
        self.WallIndexEven = None 
        self.WallIndexOdd = None 

        # Fast run parameter
        self.FastMaxVelocity = 4.
        self.FastTurnVelocity = 1.
        self.FastAccel = 20.
        self.FastAccelBrake = -40.
        
    def GetEnv ( self ):
        pass
        settings = ( 
            # type, range or selection, name, description
            ( 'Selection',  ( "60*70", "30*35" ),  'Mouse Size', 'Size for classsic or half sized maze' ),
            ( 'Float',      ( 0.1, 20 ),   'First run speed',     'Mouse speed for first run' ),
            ( 'Float',      ( 0.1, 20 ),   'First digonal speed', 'Mouse speed for diagonal path of first run' ),
            ( 'Float',      ( 0.1, 20 ),   'Second run speed',    'Mouse speed for second run' ),
            ( 'Float',      ( 0.1, 20 ),   'Second digonal speed', 'Mouse speed for diagonal path of first run' ),
            ( 'Float',      ( 0.1, 20 ),   'Second turn speed',   'Mouse speed for turn of second run' ),
            ( 'Integer',    ( 50, 300 ),   'Stright weight',         'One Block width of maze (50~300mm)' ),
            ( 'Integer',    ( 50, 300 ),   'Diagonal weight',         'One Block width of maze (50~300mm)' ),
            ( 'Integer',    ( 50, 300 ),   'Diagonal weight',         'One Block width of maze (50~300mm)' ),
            ( 'Integer',    ( 50, 300 ),   'Trun 90 weight',         'One Block width of maze (50~300mm)' ),
            ( 'Integer',    ( 50, 300 ),   'Trun 135 weight',         'One Block width of maze (50~300mm)' ),
            ( 'Integer',    ( 50, 300 ),   'Trun 180 weight',         'One Block width of maze (50~300mm)' ),
        )

    def SetEnv ( self, maze_size, size, pos, angle, block, poll, start, target, target_section, drawtime = 0.04 ):
        self.MazeSize = maze_size
        self.m_MouseSize = size
        self.wl = size [ 0 ] 
        self.pc = self.position = pos
        self.angle = angle
        self.block = block
        self.poll = poll
        self.MazeStart = start 
        self.MazeTarget = target
        self.MazeTargetSection = target_section
        self.drawtime = drawtime
        self.MakeWallIndex()

    def SetFastRunParam ( self, v, tv, a, ab ):
        self.FastMaxVelocity = float ( v )
        self.FastTurnVelocity = float ( tv )
        self.FastAccel = float ( a )
        self.FastAccelBrake = float ( ab )

    def MakeWallIndex( self ):
        ( w, h ) = self.MazeSize
        self.WallIndexEven = []
        self.WallIndexOdd = []
        we = self.WallIndexEven
        wo = self.WallIndexOdd
        row = ( w + 1 ) * 2

        self.WallIndexOdd = {
            0: row,     # 'N'  
            1: 1,       # 'NE' 
            2: 0,       # 'E'  
            3: -row+1,  # 'SE' 
            4: -row,    # 'S'   
            5: -row-1,  # 'SW' 
            6: 0,       # 'W'  
            7: -1       # 'NW' 
        }
        self.WallIndexEven  = {
            0: 0,       # 'N'  
            1: row+1,   # 'NE' 
            2: 2,       # 'E'  
            3: 1,       # 'SE' 
            4: 0,       # 'S'   
            5: -1,      # 'SW' 
            6: -2,      # 'W'  
            7: row-1    # 'NW' 
        }

    def GetWallDir( self, widx, dir, turn ):
        ew = self.WallIndexEven
        ow = self.WallIndexOdd

        adir = ( dir + turn ) % 8
        if widx & 1:
            wall = widx + ow [ adir ] 
        else:
            wall = widx + ew [ adir ] 
        
        if widx == wall:
            return ( None, None )
        return ( wall, adir )

    def InitRun ( self ):
        self.vl = self.vr = 0.
        self.sl = self.sr = 0.
        self.currtime = self.starttime = self.drawdtime = time.time ()

#---------------------------------------------------------------------------
# MouseMotor
#---------------------------------------------------------------------------
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

class MouseMotor(MouseEnv):
    def __init__(self, parent):
        MouseEnv.__init__ ( self, parent )

    #-----------------------------------------------------------------------
    # Methods for overriding
    #-----------------------------------------------------------------------
    def DrawMouse ( self, pc, angle, redraw = True, color = 'White' ):
        print("make this routine")
        pass

    #-----------------------------------------------------------------------
    # Methods for mouse movement 
    #-----------------------------------------------------------------------
    def _GetS ( self, v0, a, t ):
        s = v0 * t + 0.5 * a * t ** 2
        return s

    def _GetV ( self, v0, a, t ):
        v = v0 + a * t
        return v

    def GetMoveDistance ( self, dist, v0, v_max, v_end, a_inc, a_dec ):
        t_max = self.GetTimeByVelocity ( a_inc/5, v_max, v0 )
        t_max = 60
        t_limit = self.GetTimeByVelocity ( a_inc, v_max, v0 )
        
        t = self.GetTimeByAccel ( a_inc, dist, v0 )
        v = self._GetV ( v0, a_inc, t )
        if v <= v_end:
            return ( dist, 0, 0 )

        t = t_max / 2
        t_diff = t_max / 4
        while True:
            if t <= t_limit:
                s1 = self._GetS ( v0, a_inc, t )
                v1 = self._GetV ( v0, a_inc, t )
                s2 = 0
            else:
                s1 = self._GetS ( v0, a_inc, t_limit )
                v1 = self._GetV ( v0, a_inc, t_limit )
                s2 = self._GetS ( v1, 0, t - t_limit )

            if v1 > v_end:
                t3 = self.GetTimeByVelocity ( a_dec, v_end, v1 )
                s3 = self._GetS ( v1, a_dec, t3 )
            else:
                s3 = 0

            s = s1 + s2 + s3
            # print "diff", ( s - dist )
            if abs ( s - dist ) < 0.0001:
                return ( s1, s2, s3 )
            
            if ( s - dist ) < 0.:
                t = t + t_diff
            else:
                t = t - t_diff
            t_diff = t_diff / 2.
    
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
        while not self.FastestFirstRun:
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
        ( vc, vl, vr ) = self.GetV ( al, ar, dt )
        ( sc, sl, sr ) = self.GetS ( al, ar, dt )

        self.pc = pc
        self.angle = angle
        ( self.vl, self.vr ) = ( vl, vr )
        ( self.sl, self.sr ) = ( sl, sr )
        self.currtime = self.currtime + dt

        self.DrawMouse( pc, angle, 'Green' )
        
        if not self.FastestFirstRun:
            print("RT/T=%.3f,%.3f,A=%.1f,V=%.3f,%.3f,%.3f,S=%.0f" % ( 
                    ( time.time () - self.starttime ) * 1000, 
                    ( self.currtime - self.starttime ) * 1000, 
                    degrees ( self.angle ),
                    vc,vl,vr, 
                    sc * 1000
                    ))

    def GetTimeByAccel ( self, a, s, v0 ):
        if a<0:
            print("### Error accel is minus ###")
            exit ()
        if a == 0:
            t = s / v0
        else:
            t = ( -2 * v0 + sqrt( (2*v0)**2 + 8*a*s ) ) / ( 2 * a )
        return t

    def GetTimeByVelocity ( self, a, v, v0 ):
        t = ( v - v0 ) / a
        return t

    def GetAccelByTime ( self, t, s, v0 ):
        a = ( s - v0 * t ) * 2. / ( t**2. )
        return a

    def GetAccelByVelocity ( self, s, v, v0 ):
        a = ( v ** 2 - v0 ** 2 ) / ( 2 * s )
        return a 

    def MoveWithTimeDistance ( self, t, s ):
        a = self.GetAccelByTime ( t, s, self.vl ) 
        self.Move ( a, a, t) 

    def MoveWithAccelDistance ( self, a, s ):
        v0 = self.vl
        t = self.GetTimeByAccel ( a, s, v0 ) 
        self.Move ( a, a, t) 

    def MoveWithVelocityDistance ( self, v, s ):
        v0 = self.vl
        a = self.GetAccelByVelocity ( s, v, v0 ) 
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
        v0 = self.vl
        wl = self.wl
        r = self.block / 2.
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
        wl = self.wl
        angle = radians ( angle ) / 2 
        t = sqrt ( wl * angle / a )
        
        if right:
            al, ar = a, -a
        else:
            al, ar = -a, a

        self.Move ( al, ar, t) 
        self.Move ( -al, -ar, t) 


#---------------------------------------------------------------------------
# MouseGyroSensor 
#---------------------------------------------------------------------------
class MouseGyroSensor (MouseEnv):
    def __init__(self, parent):
        MouseEnv.__init__ ( self, parent )

    def GetAngle ():
        # integral voltage and get angle and return it
        pass

#---------------------------------------------------------------------------
# MouseOpticalSensor 
#---------------------------------------------------------------------------
# Wall index for lookup
WALL_LU_N   = 0
WALL_LU_E   = 1
WALL_LU_S   = 2
WALL_LU_W   = 3

class MouseOpticalSensor(MouseEnv):
    def __init__(self, parent):
        MouseEnv.__init__ ( self, parent )

    def DetectAllWalls ( self ):
        maze = self.m_Maze

        for wall in range ( len ( self.Walls ) ) :
            print(wall)
            maze.DetectedWall ( wall, True )
            if self.Walls [ wall ] < WALL_EXIST:
                self.Walls [ wall ] = WALL_NONE
            else:
                self.Walls [ wall ] = WALL_DETECTED

    def DetectWall ( self ):
        maze = self.m_Maze
        pos = self.mpos 
        dir = self.mdir 

        # detectable area 44~84(half block) when mouse height 80
        ( f, d ) = self.GetWallDir( pos, dir, Turns [ 'T0' ] )
        ( l, d ) = self.GetWallDir( pos, dir, Turns [ 'TL45' ] )
        ( r, d ) = self.GetWallDir( pos, dir, Turns [ 'TR45' ] )
        maze.DetectedWall ( f, True )
        maze.DetectedWall ( l, True )
        maze.DetectedWall ( r, True )

        if self.WallMarks [ f ]:
            maze.DrawWallPoints ( f, 0 ) 
            maze.DrawWallPoints ( f, self.WallMarks [ f ] ) 
        if self.WallMarks [ l ]:
            maze.DrawWallPoints ( l, 0 ) 
            maze.DrawWallPoints ( l, self.WallMarks [ l ] ) 
        if self.WallMarks [ r ]:
            maze.DrawWallPoints ( r, 0 ) 
            maze.DrawWallPoints ( r, self.WallMarks [ r ] ) 

        if self.Walls [ f ] < WALL_EXIST:
            self.Walls [ f ] = WALL_NONE
        else:
            self.Walls [ f ] = WALL_DETECTED

        if self.Walls [ l ] < WALL_EXIST:
            self.Walls [ l ] = WALL_NONE
        else:
            self.Walls [ l ] = WALL_DETECTED

        if self.Walls [ r ] < WALL_EXIST:
            self.Walls [ r ] = WALL_NONE
        else:
            self.Walls [ r ] = WALL_DETECTED


#---------------------------------------------------------------------------
# MouseBrain 
#---------------------------------------------------------------------------

# Wall type
WALL_NONE       = 0
WALL_UNKNOWN    = 1
WALL_EXIST      = 2
WALL_DETECTED   = 3
WALL_NO_MOVE    = 0xfe
WALL_MOVE       = 0xff
WALL_MAX_DIST   = 0xffff

MOVE_BLOCK      = 0
MOVE_HBLOCK     = 1
MOVE_LSTURN     = 2
MOVE_RSTURN     = 3
MOVE_BACK       = 4
MOVE_START      = 5
MOVE_STOP       = 6

MouseMoves = {
    'MOVE_BLOCK' : 0,
    'MOVE_HBLOCK': 1,
    'MOVE_LSTURN': 2,
    'MOVE_RSTURN': 3,
    'MOVE_BACK'  : 4,
    'MOVE_START' : 5,
    'MOVE_STOP'  : 6,
    'MOVE_NONE'  : 7,

    'F_T0'      : 30,
    'F_TL45'    : 31,
    'F_TL90'    : 32,
    'F_TL135'   : 33,
    'F_TL180'   : 34,
    'F_TR45'    : 35,
    'F_TR90'    : 36,
    'F_TR135'   : 37,
    'F_TR180'   : 38,
    'F_T0_STOP' : 39,

    'FD_T0'     : 40,
    'FD_TL45'   : 41,
    'FD_TL90'   : 42,
    'FD_TL135'  : 43,
    'FD_TR45'   : 45,
    'FD_TR90'   : 46,
    'FD_TR135'  : 47,
}

MAX_TURN_WEIGHT = 20

TurnsPriorityNormalPath = {
    'T0'    : 1,
    'TL45'  : 2,
    'TR45'  : 2,
    'T0_45' : 3,
    'TL90'  : 4,
    'TR90'  : 4,
    'TL135' : 5,
    'TR135' : 5,
    'T180'  : 5,
}

TurnsPriorityDiagonalPath = {
    'T0'    : 1,
    'T0_45' : 1,
    'TL90'  : 3,
    'TR90'  : 3,
    'TL45'  : 4,
    'TR45'  : 4,
    'TL135' : 5,
    'TR135' : 5,
    'T180'  : 5,
}

class MouseBrain(MouseMotor, MouseOpticalSensor, MouseGyroSensor):
    def __init__(self, parent):
        MouseMotor.__init__ ( self, parent )
        MouseOpticalSensor.__init__ ( self, parent )

        self.DirsMap = []
        self.DistanceMap = []
        self.MouseBuffer = []
        self.CurrWeight = 0
        self.CurrDistance = 0

        self.MouseCnt = 0
        self.TracePosition = []
        self.TraceTurn = []
        self.TraceUnknown = []
        self.TraceUnknownAll = []

        self.RunCount = 0 # 1st, 1st return, 2st, 2st return

        self.MazeSize = MAZE_SIZE
        self.MazeStart = None
        self.MazeTarget = None
        self.MazeTargetSection = None
        self.MazeUnknownTarget = None
        self.MazeTargetDetermined = None

        self.FirstRunVelocity = 1.

    def InitDirsMap ( self, search_unknown ):
        maze = self.m_Maze
        self.MouseBuffer = []
        self.CurrWeight = 0
        self.DirsMap = []
        self.DistanceMap = []

        dirsmap = self.DirsMap
        for wall in self.Walls:
            self.DistanceMap.append ( WALL_MAX_DIST )

            if search_unknown:
                if wall <= WALL_EXIST:
                    dirsmap.append( WALL_MOVE )
                else:
                    dirsmap.append( WALL_NO_MOVE )
            else:
                if wall <= WALL_NONE:
                    dirsmap.append( WALL_MOVE )
                else:
                    dirsmap.append( WALL_NO_MOVE )

    def PushIMouse ( self, pos, dir, weight ):
        w = self.CurrWeight + weight
        buf = self.MouseBuffer
        buf.append ( ( w, pos, dir ) )
        self.DirsMap [ pos ] = dir 
        self.DistanceMap [ pos ] = w 

    def PopIMouse ( self ):
        cw = self.CurrWeight
        minidx = minw = WALL_MAX_DIST 
        buf = self.MouseBuffer

        while buf:
            for idx in range ( len ( buf ) ):
                ( w, p, d ) = buf [ idx ]
                if w == cw:
                    del buf [ idx ]
                    return ( p, d ) 
                if minw > w:
                    minw = w
                    minidx = idx

            if minw != WALL_MAX_DIST:
                self.CurrWeight = minw
                ( w, p, d ) = buf [ minidx ]
                del buf [ minidx ]
                return ( p, d ) 

        return ( None, None )

    def PushCanMove( self, pos, dir ):
        for turn in Turns:
            ( nextwall, nextdir ) = self.GetWallDir( pos, dir, Turns [ turn ] )
            
            if nextwall and self.DirsMap [ nextwall ] == WALL_MOVE:

                if turn == 'T0' and dir!=0 and dir!=2 and dir!=4 and dir!=6 :
                    turn = 'T0_45'
                turn_weight = TurnsPriorityDiagonalPath [ turn ]

                self.PushIMouse ( nextwall, nextdir, turn_weight )

    def RunIMouse ( self, pos, dir, target ):
        buf = self.MouseBuffer

        self.PushIMouse( pos, dir, 0 )

        while not target or pos != target:
            ( pos, dir ) = self.PopIMouse()
            if pos == None:
                break
            self.PushCanMove( pos, dir )

    def DrawDirsMap ( self ):
        NameOfDirections = {
            0: 'N',
            1: 'NE',
            2: 'E',
            3: 'SE',
            4: 'S',
            5: 'SW',
            6: 'W',
            7: 'NW',
            0xfe: '',
            0xff: 'X',
        }

        maze = self.m_Maze
        infos = []
        for dir in self.DirsMap:
            infos.append ( NameOfDirections [ dir ] )

        maze.SetAllWallInformation ( infos )
        maze.EnableAllWallInformation ( True )

    def DrawDistanceMap ( self ):
        maze = self.m_Maze
        infos = []
        for num in self.DistanceMap:
            if num < WALL_MAX_DIST:
                infos.append ( str ( num ) )
            else:
                infos.append ( '' )

        maze.SetAllWallInformation ( infos )
        maze.EnableAllWallInformation ( True )

    def DrawWallNum ( self ):
        maze = self.m_Maze
        walls = maze.GetAllWalls()
        infos = []
        for index in range ( len ( walls ) ) :
            infos.append ( "%d"%index )

        maze.SetAllWallInformation ( infos )
        maze.EnableAllWallInformation ( True )

    def InitAllTarget ( self ):
        maze = self.m_Maze

        # init start position
        start = maze.GetWallIndex ( self.MazeStart, WALL_LU_N )
        maze.DetectedWall ( start, True )
        self.Walls [ start ] = WALL_NONE

        start = maze.GetWallIndex ( self.MazeStart, WALL_LU_E )
        maze.DetectedWall ( start, True )
        self.Walls [ start ] = WALL_DETECTED

        # init target position
        if self.MazeTargetSection:
            ( ts, te ) = self.MazeTargetSection

            tpos = []

            for x in range ( ts [ 0 ], te [ 0 ]+1 ):
                xy = ( x, ts [ 1 ] )
                idx = maze.GetWallIndex ( xy, WALL_LU_S )
                tpos.append ( idx ) 

                xy = ( x, te [ 1 ] )
                idx = maze.GetWallIndex ( xy, WALL_LU_N )
                tpos.append ( idx ) 

            for y in range ( ts [ 1 ], te [ 1 ]+1 ):
                xy = ( ts [ 0 ], y ) 
                idx = maze.GetWallIndex ( xy, WALL_LU_W )
                tpos.append ( idx ) 

                xy = ( te [ 0 ], y ) 
                idx = maze.GetWallIndex ( xy, WALL_LU_E )
                tpos.append ( idx ) 

            for x in range ( ts [ 0 ], te [ 0 ]+1 ):
                for y in range ( ts [ 1 ], te [ 1 ]+1 ):
                    xy = ( x, y ) 

                    idx = maze.GetWallIndex ( xy, WALL_LU_N )
                    try:
                        tpos.index ( idx )
                    except ValueError:
                        maze.DetectedWall ( idx, True )
                        self.Walls [ idx ] = WALL_NONE

                    idx = maze.GetWallIndex ( xy, WALL_LU_E )
                    try:
                        tpos.index ( idx )
                    except ValueError:
                        maze.DetectedWall ( idx, True )
                        self.Walls [ idx ] = WALL_NONE

                    idx = maze.GetWallIndex ( xy, WALL_LU_S )
                    try:
                        tpos.index ( idx )
                    except ValueError:
                        maze.DetectedWall ( idx, True )
                        self.Walls [ idx ] = WALL_NONE

                    idx = maze.GetWallIndex ( xy, WALL_LU_W )
                    try:
                        tpos.index ( idx )
                    except ValueError:
                        maze.DetectedWall ( idx, True )
                        self.Walls [ idx ] = WALL_NONE

            self.MazeTargetDetermined = None
            self.MazeUnknownTarget = tpos
        
    def SetTarget ( self, target ):
        maze = self.m_Maze
        targets = self.MazeUnknownTarget
        self.MazeTargetDetermined = target
        for pos in targets: 
            if pos != target and ( maze.GetWall ( pos ) == WALL_UNKNOWN or maze.GetWall ( pos ) == WALL_EXIST ) :
                maze.DetectedWall ( pos, True )
                self.Walls [ pos ] = WALL_DETECTED

    def GetTarget ( self ):
        # if self.MazeTarget:
            # return self.MazeTarget

        if self.MazeTargetDetermined:
            return self.MazeTargetDetermined

        targets = self.MazeUnknownTarget
        min = WALL_MAX_DIST
        min_pos = WALL_MAX_DIST
        for pos in targets: 
            if self.DistanceMap [ pos ] < min:
                min = self.DistanceMap [ pos ]
                min_pos = pos
        # print "Target:", min_pos
        return min_pos

    def GetStart ( self ):
        maze = self.m_Maze
        return maze.GetWallIndex ( self.MazeStart, WALL_LU_N )

    def MakeDirsMap ( self, pos, dir, target = None, search_unknown = True ):
        self.InitDirsMap ( search_unknown ) 
        self.RunIMouse ( pos, dir, target )

    def ClearRoutes ( self ):
        self.WallMarks = [ 0 ] * len (self.Walls)

    def SetRoutes ( self, type ):
        if self.FastestFirstRun:
            return 
        if not self.EnableRoutes:
            return
        routes = self.TracePosition
        if not routes or len ( routes )<=1 :
            return

        # if type==1:
            # routes = routes [ :-2 ]
    
        for i in routes:
            self.WallMarks [ i ] = type

    def DrawRoutes ( self ):
        if self.FastestFirstRun:
            return 
        if not self.EnableRoutes:
            return

        for i in range ( len ( self.WallMarks ) ):
            self.m_Maze.DrawWallPoints ( i, self.WallMarks [ i ] ) 

    def ReDrawRoutes ( self ):
        if self.FastestFirstRun:
            return 
        if not self.EnableRoutes:
            return

        for i in range ( len ( self.WallMarks ) ):
            self.m_Maze.DrawWallPoints ( i, 0 ) 
            self.m_Maze.DrawWallPoints ( i, self.WallMarks [ i ] ) 

    def MakeFastRoute ( self, add_start=True, add_stop = True ):
        maze = self.m_Maze
        block = self.block
        diag = sqrt ( 2 ) * ( block / 2. )

        TurnSeqs = self.TurnSeqs = ( 
            ( ( 'F_T0',     'FD_T0'),       ( Turns [ 'T0' ], ) ),
                         
            ( ( 'F_TL180',  ''),            ( Turns [ 'TL45' ], Turns [ 'TL90' ], Turns [ 'TL45' ] ) ),
            ( ( 'F_TL135',  ''),            ( Turns [ 'TL45' ], Turns [ 'TL90' ] ) ),
            ( ( 'F_TL90',   'FD_TL45'),     ( Turns [ 'TL45' ], Turns [ 'TL45' ] ) ),
            ( ( 'F_TL45',   'FD_TL45'),     ( Turns [ 'TL45' ], ) ),
            ( ( '',         'FD_TL135'),    ( Turns [ 'TL90' ], Turns [ 'TL45' ] ) ),
            ( ( '',         'FD_TL90'),     ( Turns [ 'TL90' ], ) ),
                         
            ( ( 'F_TR180',  ''),            ( Turns [ 'TR45' ], Turns [ 'TR90' ], Turns [ 'TR45' ] ) ),
            ( ( 'F_TR135',  ''),            ( Turns [ 'TR45' ], Turns [ 'TR90' ] ) ),
            ( ( 'F_TR90',   'FD_TR45'),     ( Turns [ 'TR45' ], Turns [ 'TR45' ] ) ),
            ( ( 'F_TR45',   'FD_TR45'),     ( Turns [ 'TR45' ], ) ),
            ( ( '',         'FD_TR135'),    ( Turns [ 'TR90' ], Turns [ 'TR45' ] ) ),
            ( ( '',         'FD_TR90'),     ( Turns [ 'TR90' ], ) ),
        )
        if self.block == 0.180:
            TurnDistance = {
                'F_T0'      : ( block, 0 ),
                'F_TL45'    : ( -0.05,  0.0788 ),
                'F_TL90'    : ( -0.024, block-0.024 ),
                'F_TL135'   : ( -0.075, 0),
                'F_TL180'   : ( -0.06,  block-0.06 ),
                'F_TR45'    : ( -0.05,  0.0788 ),
                'F_TR90'    : ( -0.024, block-0.024 ),
                'F_TR135'   : ( -0.075, 0),
                'F_TR180'   : ( -0.06,  block-0.06 ),

                'FD_T0'     : ( diag, 0 ),
                'FD_TL45'   : ( -0.049 , block-0.049 ),
                'FD_TL90'   : ( -diag/2-0.05, diag/2-0.05 ),
                'FD_TL135'  : ( -diag, block-0.075),
                'FD_TR45'   : ( -0.049 , block-0.049 ),
                'FD_TR90'   : ( -diag/2-0.05, diag/2-0.05 ),
                'FD_TR135'  : ( -diag, block-0.075),
            }
        else:
            TurnDistance = {
                'F_T0'      : ( block, 0 ),
                'F_TL45'    : ( -0.05/2,  0.0788/2 ),
                'F_TL90'    : ( -0.024/2, block-0.024/2 ),
                'F_TL135'   : ( -0.075/2, 0),
                'F_TL180'   : ( -0.06/2,  block-0.06/2 ),
                'F_TR45'    : ( -0.05/2,  0.0788/2 ),
                'F_TR90'    : ( -0.024/2, block-0.024/2 ),
                'F_TR135'   : ( -0.075/2, 0),
                'F_TR180'   : ( -0.06/2,  block-0.06/2 ),

                'FD_T0'     : ( diag, 0 ),
                'FD_TL45'   : ( -0.049/2 , block-0.049/2 ),
                'FD_TL90'   : ( -diag/2-0.05/2, diag/2-0.05/2 ),
                'FD_TL135'  : ( -diag, block-0.075/2),
                'FD_TR45'   : ( -0.049/2 , block-0.049/2 ),
                'FD_TR90'   : ( -diag/2-0.05/2, diag/2-0.05/2 ),
                'FD_TR135'  : ( -diag, block-0.075/2),
            }
        self.TurnDistance = TurnDistance

        def GetTurn ( diagonal ):

            for ( turn, seq ) in TurnSeqs:

                # print "seq, turns", seq, turns [ 0 : len ( seq ) ]

                if list ( seq ) == turns [ 0 : len ( seq ) ]:

                    # print "turn,turns=", turn [ diagonal ], turns 

                    if not turn [ diagonal ]:
                        print("### direction error ###")
                        print("diagonal=%d, turn=%s" % ( diagonal, turn [ diagonal ] ))
                        self.Running = False
                        self.Started = False
                        exit ()

                    if turns [ 0 ] == Turns [ 'T0' ]:
                        count = 0
                        while turns and turns [ 0 ] == Turns [ 'T0' ] and IsKnownWall ( routes, count+1 ) :
                            del turns [ 0 ]
                            count = count + 1
                        if count:
                            return ( turn [ diagonal ], count, diagonal )
                        else:
                            return ( None, 0, diagonal )
                    else:
                        if turn  [ diagonal ] == 'FD_TL45' or turn  [ diagonal ] == 'FD_TR45':
                            count = 1
                        else:
                            count = len ( seq )
                        del turns [ 0 : count ]

                        new_diagonal = diagonal ^ ( MouseMoves [ turn [ diagonal ] ] & 1 )
                        
                        if IsKnownWalls ( routes, count ):
                            return ( turn [ diagonal ], count, new_diagonal )
                        else:
                            return ( None, 0, diagonal )

            print('### Did not get turn ###')
            return ( None, 0, diagonal )

        def IsKnownWall ( routes, count ):
            if len ( routes ) < (count+1):
                return False
            pos = routes [ count ]
            if maze.GetWall ( pos ) == WALL_UNKNOWN or maze.GetWall ( pos ) == WALL_EXIST :
                return False
            return True

        def IsKnownWalls ( routes, count ):
            if len ( routes ) < (count+1):
                return False
            for pos in routes [ 0:count+1 ]:
                if maze.GetWall ( pos ) == WALL_UNKNOWN or maze.GetWall ( pos ) == WALL_EXIST :
                    return False
            return True

        routes = self.TracePosition
        routes.reverse ()
        turns = self.TraceTurn
        turns.reverse ()
        target = routes [ 0 ]
        moves = []
        diagonal = 0 
        distance = 0
        pre_dist = 0
        post_dist = 0

        if add_start:
            post_dist = block / 2
            moves.append ( [ 'F_T0',  post_dist, routes [ 0 ] ] )
        else:
            post_dist = 0
            moves.append ( [ 'F_T0',  post_dist, routes [ 0 ] ] )
            
        turn_appended = False
        if add_stop:
            dirmap = self.DirsMap
            target = pos = routes [ -1 ]
            dir = dirmap [ pos ]

            # print "### target position:", pos, dir
            # added the last turn for stop
            if dir == Directions [ 'NE' ] or dir == Directions [ 'SW' ]: 
                if not pos & 1:
                    ( new_target, new_dir ) = self.GetWallDir( pos, dir, Turns [ 'TR45' ] )
                    turns.append ( Turns [ 'TR45'] )
                    routes.append ( new_target )
                    turn_appended = True
                else:
                    ( new_target, new_dir ) = self.GetWallDir( pos, dir, Turns [ 'TL45' ] )
                    turns.append ( Turns [ 'TL45'] )
                    routes.append ( new_target )
                    turn_appended = True

            elif dir == Directions [ 'NW' ] or dir == Directions [ 'SE' ] :
                if not pos & 1:
                    ( new_target, new_dir) = self.GetWallDir( pos, dir, Turns [ 'TL45' ] )
                    turns.append ( Turns [ 'TL45'] )
                    routes.append ( new_target )
                    turn_appended = True
                else:
                    ( new_target, new_dir) = self.GetWallDir( pos, dir, Turns [ 'TR45' ] )
                    turns.append ( Turns [ 'TR45'] )
                    routes.append ( new_target )
                    turn_appended = True
            else:
                    ( new_target, new_dir) = self.GetWallDir( pos, dir, Turns [ 'T0' ] )
                    if maze.GetWall ( new_target ) == WALL_NONE:
                        turns.append ( Turns [ 'T0'] )
                        routes.append ( new_target )
                        turn_appended = True

        while turns:

            ( turn, count, diagonal ) = GetTurn ( diagonal )
            
            if not turn:
                if len ( moves ) == 1 and moves [ -1 ] [ 1 ] < block:
                    return None
                break
 
            # if not IsKnownWalls ( routes, count ):
                # print '### Some routes is unknown ###'
                # if len ( moves ) == 1 and moves [ -1 ] [ 1 ] < block:
                    # return None
                # return moves
            del routes [ 0 : count ]

            if turn == 'F_T0':
                if moves [ -1 ] [ 0 ] != 'F_T0':
                        print("### direction error ###")
                        print("diagonal=%d, turn=%s" % ( diagonal, turn [ diagonal ] ))
                        self.Running = False
                        self.Started = False
                        exit ()

                moves [ -1 ] [ 1 ] = moves [ -1 ] [ 1 ] + block * count
                moves [ -1 ] [ 2 ] = routes [ 0 ] 

            elif turn == 'FD_T0':
                if moves [ -1 ] [ 0 ] != 'FD_T0':
                        print("### direction error ###")
                        print("diagonal=%d, turn=%s" % ( diagonal, turn [ diagonal ] ))
                        self.Running = False
                        self.Started = False
                        exit ()

                moves [ -1 ] [ 1 ] = moves [ -1 ] [ 1 ] + diag * count
                moves [ -1 ] [ 2 ] = routes [ 0 ] 
            else:

                pre_dist = TurnDistance [ turn ] [ 0 ]
                post_dist = TurnDistance [ turn ] [ 1 ]

                if moves:
                    moves [ -1 ] [ 1 ] = moves [ -1 ] [ 1 ] + pre_dist
                moves.append ( [ turn, post_dist, routes [ 0 ] ] )
                moves.append ( [ ( lambda d : d and 'FD_T0' or 'F_T0' ) ( diagonal ), post_dist, routes [ 0 ] ] )

        # target = self.TracePosition = routes
        if add_stop:

            if moves [ -1 ] [ 0 ] != 'F_T0':
                print("### direction error ###")
                print("diagonal=%d, turn=%s" % ( diagonal, turn [ diagonal ] ))
                self.Running = False
                self.Started = False
                exit ()

            if turn_appended and not maze.GetWall ( new_target ) == WALL_NONE:
                ### FIXME ###
                print("Quickly stop")
                moves [ -1 ] [ 0 ] = 'F_T0_STOP'
                moves [ -1 ] [ 1 ] = moves [ -1 ] [ 1 ] - block/2
                moves.append ( [ 'MOVE_BACK', 0, target ] )
            else:
                moves [ -1 ] [ 0 ] = 'F_T0_STOP'
                moves [ -1 ] [ 1 ] = moves [ -1 ] [ 1 ] + block/2
                moves.append ( [ 'MOVE_BACK', 0, routes [ 0 ] ] )

        # print "moves", moves
        #self.DrawDirsMap ()
        return moves

    def TraceRoute ( self, start, target ): #, add_stop=False ):
        maze = self.m_Maze
        dirmap = self.DirsMap
        routes = self.TracePosition

        self.TracePosition = []
        self.TraceTurn = []
        self.TraceUnknown = []

        routes = []
        route_dirs = []
        route_turns = []
        route_unknown = []

        pos = start
        dir = dirmap [ pos ]


        routes.append ( pos )
        route_dirs.append ( dir ) 

        while pos != target:
            ( npos, bdir ) = self.GetWallDir( pos, dir, Turns [ 'T180' ] )
            ndir = dirmap [ npos ]

            route_turns.append ( ( ( dir - ndir ) + 8 ) % 8 )
            routes.append ( npos )
            route_dirs.append ( ndir ) 

            if maze.GetWall ( npos ) == WALL_UNKNOWN or maze.GetWall ( npos ) == WALL_EXIST:
                route_unknown.append ( npos )

            dir = ndir
            pos = npos
        
        self.TracePosition = routes
        self.TraceTurn = route_turns 
        self.TraceUnknown = route_unknown

    def DoMove ( self, cmd, distance = 0 ):
        block = self.block

        if cmd == MouseMoves [ 'MOVE_BLOCK' ] :
            self.MoveWithAccelDistance ( 0, block )
        elif cmd == MouseMoves [ 'MOVE_HBLOCK' ] :
            self.MoveWithAccelDistance ( 0, block/2 )
        elif cmd == MouseMoves [ 'MOVE_LSTURN' ]:
            self.MoveTurn90 ( False )
        elif cmd == MouseMoves [ 'MOVE_RSTURN' ] : 
            self.MoveTurn90 ( True )
        elif cmd == MouseMoves [ 'MOVE_BACK' ] :
            self.MoveTurnInPlace ( 180, 3, False )
        elif cmd == MouseMoves [ 'MOVE_START' ] :
            self.MoveWithVelocityDistance ( self.FirstRunVelocity, block/2 )
        elif cmd == MouseMoves [ 'MOVE_STOP' ] :
            self.MoveWithVelocityDistance  ( 0, block/2 )

        # fast moves
        elif cmd == MouseMoves [ 'F_T0' ]:
            s1, s2, s3 = self.GetMoveDistance ( distance, self.vl, self.FastMaxVelocity, self.FastTurnVelocity, self.FastAccel, self.FastAccelBrake )
            self.MoveWithAccelDistance ( self.FastAccel, s1 )
            if s2:
                self.MoveWithAccelDistance ( 0, s2 )
            if s3:
                self.MoveWithVelocityDistance  ( self.FastTurnVelocity, s3 )
        
        elif cmd == MouseMoves [ 'F_T0_STOP' ]:
            print("#0", distance)
            s1, s2, s3 = self.GetMoveDistance ( distance, self.vl, self.FastMaxVelocity, 0, self.FastAccel, self.FastAccelBrake )
            print("#1")
            self.MoveWithAccelDistance ( self.FastAccel, s1 )
            if s2:
                print("#2")
                self.MoveWithAccelDistance ( 0, s2 )
            if s3:
                print("#3")
                self.MoveWithVelocityDistance  ( 0, s3 )
            print("#4")
            self.mdir = ( self.mdir + Turns [ 'T180'] ) % 8

        elif cmd == MouseMoves [ 'FD_T0' ]:
            s1, s2, s3 = self.GetMoveDistance ( distance, self.vl, self.FastMaxVelocity, self.FastTurnVelocity, self.FastAccel, self.FastAccelBrake )
            self.MoveWithAccelDistance ( self.FastAccel, s1 )
            if s2:
                self.MoveWithAccelDistance ( 0, s2 )
            if s3:
                self.MoveWithVelocityDistance  ( self.FastTurnVelocity, s3 )

        elif cmd == MouseMoves [ 'F_TL45' ]:
            self.MoveTurnAccel ( 45, False )
            self.mdir = ( self.mdir + Turns [ 'TL45'] ) % 8
        elif cmd == MouseMoves [ 'F_TL90' ]:
            self.MoveTurnAccel ( 90, False )
            self.mdir = ( self.mdir + Turns [ 'TL90'] ) % 8
        elif cmd == MouseMoves [ 'F_TL135' ]:
            self.MoveTurnAccel ( 135, False )
            self.mdir = ( self.mdir + Turns [ 'TL135'] ) % 8
        elif cmd == MouseMoves [ 'F_TL180' ]:
            self.MoveTurnAccel ( 180, False )
            self.mdir = ( self.mdir + Turns [ 'T180'] ) % 8

        elif cmd == MouseMoves [ 'F_TR45' ]:
            self.MoveTurnAccel ( 45, True )
            self.mdir = ( self.mdir + Turns [ 'TR45'] ) % 8
        elif cmd == MouseMoves [ 'F_TR90' ]:
            self.MoveTurnAccel ( 90, True )
            self.mdir = ( self.mdir + Turns [ 'TR90'] ) % 8
        elif cmd == MouseMoves [ 'F_TR135' ]:
            self.MoveTurnAccel ( 135, True  )
            self.mdir = ( self.mdir + Turns [ 'TR135'] ) % 8
        elif cmd == MouseMoves [ 'F_TR180' ]:
            self.MoveTurnAccel ( 180, True )
            self.mdir = ( self.mdir + Turns [ 'T180'] ) % 8

        elif cmd == MouseMoves [ 'FD_TL45' ]:
            self.MoveTurnAccel ( 45, False )
            self.mdir = ( self.mdir + Turns [ 'TL45'] ) % 8
        elif cmd == MouseMoves [ 'FD_TL90' ]:
            self.MoveTurnAccel ( 90, False )
            self.mdir = ( self.mdir + Turns [ 'TL90'] ) % 8
        elif cmd == MouseMoves [ 'FD_TL135' ]:
            self.MoveTurnAccel ( 135, False )
            self.mdir = ( self.mdir + Turns [ 'TL135'] ) % 8

        elif cmd == MouseMoves [ 'FD_TR45' ]:
            self.MoveTurnAccel ( 45, True )
            self.mdir = ( self.mdir + Turns [ 'TR45'] ) % 8
        elif cmd == MouseMoves [ 'FD_TR90' ]:
            self.MoveTurnAccel ( 90, True )
            self.mdir = ( self.mdir + Turns [ 'TR90'] ) % 8
        elif cmd == MouseMoves [ 'FD_TR135' ]:
            self.MoveTurnAccel ( 135, True )
            self.mdir = ( self.mdir + Turns [ 'TR135'] ) % 8

    def DoMoveTurn ( self, turn ):
        add_angle = 0
        stop = False
        if turn == TSTOP:
            self.DoMove ( MouseMoves [ 'MOVE_STOP' ] )
            self.DoMove ( MouseMoves [ 'MOVE_BACK' ] )
            stop = True
            turn = Turns [ 'T180' ]

        elif turn == Turns [ 'T0'   ]:
            self.DoMove ( MouseMoves [ 'MOVE_BLOCK' ] )
        
        elif turn == Turns [ 'TL45' ]:
            self.DoMove ( MouseMoves [ 'MOVE_LSTURN' ] )
            add_angle = -1

        elif turn == Turns [ 'TR45' ]:
            self.DoMove ( MouseMoves [ 'MOVE_RSTURN' ] )
            add_angle = 1

        elif turn == Turns [ 'TL90' ]:
            print("DoMoveDir: TL90")

        elif turn == Turns [ 'TR90' ]:
            print("DoMoveDir: TR90")

        elif turn == Turns [ 'TL135']:
            self.DoMove ( MouseMoves [ 'MOVE_STOP' ] )
            self.DoMove ( MouseMoves [ 'MOVE_BACK' ] )
            self.DoMove ( MouseMoves [ 'MOVE_START' ] )
            add_angle = -1
            stop = True

        elif turn == Turns [ 'TR135']:
            self.DoMove ( MouseMoves [ 'MOVE_STOP' ] )
            self.DoMove ( MouseMoves [ 'MOVE_BACK' ] )
            self.DoMove ( MouseMoves [ 'MOVE_START' ] )
            add_angle = 1
            stop = True

        elif turn == Turns [ 'T180' ]:
            self.DoMove ( MouseMoves [ 'MOVE_STOP' ] )
            self.DoMove ( MouseMoves [ 'MOVE_BACK' ] )
            self.DoMove ( MouseMoves [ 'MOVE_START' ] )
            stop = True
        
        ( mpos, mdir ) = self.GetWallDir( self.mpos, self.mdir, turn )
        mdir = ( mdir + add_angle + 8 ) % 8
        self.mdir = mdir
        if not stop:
            self.mpos = mpos

    def RunToTarget ( self, search_unknown ):
        maze = self.m_Maze
        target =None

        self.DoMove ( MOVE_START )
        while self.mpos != target:
            self.GetCommnad ()

            self.DetectWall ()
            self.MakeDirsMap ( self.mpos, self.mdir, target, search_unknown )
            target = self.GetTarget ()
            # self.DrawDirsMap ()
            # self.DrawDistanceMap ()

            trace_start = target 
            trace_target = self.mpos
            self.TraceRoute ( trace_start, trace_target )
            self.ClearRoutes () 
            self.SetRoutes ( 1 ) 
            self.DrawRoutes () 

            route_dirs = self.TraceTurn
            turn = route_dirs [ -1 ]

            if turn == Turns [ 'T0' ]:
                moves = self.MakeFastRoute ( False, False )
                pre_dist = 0
                while moves and moves [ -1 ] [ 0 ] != 'F_T0':
                    pre_dist = self.TurnDistance [ moves [ -1 ] [ 0 ] ] [ 0 ]
                    del moves [ -1 ]

                # if moves and ( len ( moves ) > 1 or ( moves [ 0 ] [ 1 ] > self.block ) ) :
                if moves:
                    moves [ -1 ] [ 1 ] = moves [ -1 ] [ 1 ] - pre_dist
                    for move in moves:
                        self.GetCommnad ()
                        self.DoMove ( MouseMoves [ move [ 0 ] ], move [ 1 ] )
                        # self.Running = False
                        self.mpos = move [ 2 ]
                else:
                    self.DoMoveTurn ( turn ) 
            else:
                self.DoMoveTurn ( turn ) 

        self.SetTarget ( target )

        self.ClearRoutes () 
        self.DrawRoutes () 
        self.DetectWall ()
        self.DoMoveTurn ( TSTOP )
        
    def GetVisitPosition ( self ):
        min = WALL_MAX_DIST
        min_pos = WALL_MAX_DIST
        for pos in self.TraceUnknown:
            if self.DistanceMap [ pos ] < min:
                min = self.DistanceMap [ pos ]
                min_pos = pos
        # print "Will visit:", min_pos
        return min_pos

    def RunForSearch ( self, spos, sdir, tpos ):
        maze = self.m_Maze
        Found = False

        self.DoMove ( MOVE_START )
        while self.mpos != spos:
            self.GetCommnad ()

            self.DetectWall ()

            #====== Search shortest route
            if not Found:
                self.MakeDirsMap ( spos, sdir, tpos, True )
                # self.DrawDirsMap ()
                # self.DrawDistanceMap ()

                trace_start = tpos 
                trace_target = spos 
                self.TraceRoute ( trace_start, trace_target )
                self.ClearRoutes () 
                self.SetRoutes ( 2 ) 
                # print self.TracePosition

                if not self.TraceUnknown:
                    print("############### found #################")
                    Found = True

            if Found:
                search_unknown = False
            else:
                search_unknown = True

            #====== Go to unknown position 
            self.MakeDirsMap ( self.mpos, self.mdir, None, search_unknown )

            if Found:
                target = spos
            else:
                target = self.GetVisitPosition ()

            trace_start = target 
            trace_target = self.mpos
            self.TraceRoute ( trace_start, trace_target )
            self.SetRoutes ( 1 ) 
            self.DrawRoutes () 
            route_dirs = self.TraceTurn
            turn = route_dirs [ -1 ]

            if False:
                moves = self.MakeFastRoute ( False, True )
                if moves:
                    for move in moves:
                        self.GetCommnad ()
                        self.DoMove ( MouseMoves [ move [ 0 ] ], move [ 1 ] )
                        # self.Running = False
                        self.mpos = move [ 2 ]
            else:
                if turn == Turns [ 'T0' ]:
                    moves = self.MakeFastRoute ( False, False )
                    pre_dist = 0
                    while moves and moves [ -1 ] [ 0 ] != 'F_T0':
                        pre_dist = self.TurnDistance [ moves [ -1 ] [ 0 ] ] [ 0 ]
                        del moves [ -1 ]

                    if moves:
                        moves [ -1 ] [ 1 ] = moves [ -1 ] [ 1 ] - pre_dist
                        for move in moves:
                            self.GetCommnad ()
                            self.DoMove ( MouseMoves [ move [ 0 ] ], move [ 1 ] )
                            # self.Running = False
                            self.mpos = move [ 2 ]
                    else:
                        self.DoMoveTurn ( turn ) 
                else:
                    self.DoMoveTurn ( turn ) 

        self.ClearRoutes () 
        self.DrawRoutes () 
        self.DoMoveTurn ( TSTOP )

    def RunFastestToHome ( self, spos, sdir, tpos ):
        maze = self.m_Maze

        self.DoMove ( MOVE_START )
        while self.mpos != tpos:
            self.GetCommnad ()

            self.MakeDirsMap ( self.mpos, self.mdir, tpos, False )

            self.TraceRoute ( tpos, self.mpos )
            self.ClearRoutes () 
            self.SetRoutes ( 1 ) 
            self.DrawRoutes () 
            route_dirs = self.TraceTurn
            turn = route_dirs [ -1 ]

            if turn == Turns [ 'T0' ]:
                moves = self.MakeFastRoute ( False, False )
                pre_dist = 0
                while moves and moves [ -1 ] [ 0 ] != 'F_T0':
                    pre_dist = self.TurnDistance [ moves [ -1 ] [ 0 ] ] [ 0 ]
                    del moves [ -1 ]

                if moves:
                    moves [ -1 ] [ 1 ] = moves [ -1 ] [ 1 ] - pre_dist
                    for move in moves:
                        self.GetCommnad ()
                        self.DoMove ( MouseMoves [ move [ 0 ] ], move [ 1 ] )
                        # self.Running = False
                        self.mpos = move [ 2 ]
                else:
                    self.DoMoveTurn ( turn ) 
            else:
                self.DoMoveTurn ( turn ) 

        self.DoMoveTurn ( TSTOP )
        self.ReDrawRoutes ()

    def RunFastest( self, spos, sdir, tpos, add_stop ):
        maze = self.m_Maze

        # print "RunFastest###", spos, sdir, tpos
        self.MakeDirsMap ( spos, sdir, tpos, False )
        self.TraceRoute ( tpos, spos )
        self.ClearRoutes () 
        self.SetRoutes ( 2 ) 
        self.DrawRoutes () 

        add_start = True
        moves = self.MakeFastRoute ( add_start, add_stop )

        for move in moves:
            # print move
            self.GetCommnad ()
            self.DoMove ( MouseMoves [ move [ 0 ] ], move [ 1 ] )
            # self.Running = False

        if add_stop:
            self.mpos = moves [ -1 ] [ 2 ]
        else:
            self.mpos = tpos

        self.ReDrawRoutes ()
        # print 'RunFastest: last position', self.mpos

    def GetCommnad ( self ):
        if self.Running:
            if self.CmdQueue.empty ():
                return True

        while True:
            cmd = self.CmdQueue.get ()
            if cmd:
                if cmd == MOUSE_CMD_STOP:
                    self.StopMouse ()
                elif cmd == MOUSE_CMD_PAUSE:
                    if self.Running:
                        self.Running = False
                    else:
                        self.Running = True
                        self.currtime = self.starttime = self.drawdtime = time.time ()
                        break
        return True
        
    def MouseMain ( self ):
        maze = self.m_Maze

        self.Walls = maze.GetAllWalls()
        self.WallMarks = [ 0 ] * len (self.Walls)
        self.InitAllTarget ()
        start = self.GetStart ()
        # print "MouseMain: start", start
        self.mpos = start
        self.mdir = Directions [ 'N' ]
        # self.DetectAllWalls ()

        print("############### First Running #################")
        self.FastestFirstRun = self.EnableFastestFirstRun
        self.InitRun ()
        self.SetFastRunParam ( 4, self.FirstRunVelocity , 10, -20 )
        self.RunToTarget ( True )
        if not self.FastestFirstRun:
            time.sleep ( 1 )

        print("############### Search shortest path #################")
        self.InitRun ()
        self.SetFastRunParam ( 4, self.FirstRunVelocity , 10, -20 )
        self.RunForSearch ( start, 0, self.GetTarget () ) 
        if not self.FastestFirstRun:
            time.sleep ( 1 )

        self.FastestFirstRun = False
        while ( 1 ):
            print("############### Second running #################")
            self.InitRun ()
            self.SetFastRunParam ( 4, 2, 20, -40 )
            self.RunFastest( self.mpos, self.mdir, self.GetTarget (), True )
            time.sleep ( 1 )

            print("############### Second comming back home #################")
            self.InitRun ()
            self.SetFastRunParam ( 4, 1, 10, -20 )
            self.RunFastestToHome ( self.mpos, self.mdir, start )
            # self.RunFastest( self.mpos, self.mdir, start, True )
            time.sleep ( 1 )
            self.Running = False

        self.Running = False
        self.Started = False

    def StopMouse ( self ):
        self.ClearRoutes () 
        self.DrawRoutes () 
        self.Running = False
        self.Started = False
        exit ()

#---------------------------------------------------------------------------
# Mouse 
#---------------------------------------------------------------------------
class Mouse(MouseBrain):
    def __init__(self, parent):
        MouseBrain.__init__ ( self, parent )

        self.m_Maze = parent
        self.Canvas = parent.Canvas

        self.Started = False
        self.Running = False
        self.CmdQueue = queue.Queue(5)

    #-----------------------------------------------------------------------
    # Methods for draw mouse 
    #-----------------------------------------------------------------------
    def InitMouse(self):
        self.m_MousePoly = None
        self.m_MouseObject = None

    def SetMouse( self, maze_size, size, pos, angle, block, poll, start, target, target_section, drawtime = 0.04 ):
        Canvas = self.Canvas
        self.SetEnv ( maze_size, size, pos, angle, block, poll, start, target, target_section, drawtime = 0.04 )
        self.DrawMouse ( pos, angle, color = 'White' )

    def DrawMouse ( self, pc, angle, redraw = True, color = 'White' ):
        self.m_Maze.DrawMouse ( pc, angle, redraw, color ) 

    #-----------------------------------------------------------------------
    # Methods for AI 
    #-----------------------------------------------------------------------
    def RunPause(self, wait = False):
        if not self.Started:
            self.MouseStart ()
            self.Started = True
        else:
            self.Pause ( wait )

    def MouseStart(self):
        self.Running = True
        threading._start_new_thread ( self.MouseMain, () )

    def Pause(self, wait = False):
        run = self.IsRunning ()
        self.CmdQueue.put ( MOUSE_CMD_PAUSE )
        if wait:
            while ( run == self.IsRunning () ):
                time.sleep ( 0.01 )

    def Stop(self, wait):
        if self.Started:
            cnt = 30
            self.CmdQueue.put ( MOUSE_CMD_STOP )
            while cnt and self.Started:
                time.sleep ( 0.1 )
                cnt = cnt - 1

            if wait:
                while ( self.IsStarted () ):
                    time.sleep ( 0.01 )

    def SetEnableFastestFirstRun ( self, enable ):
        self.EnableFastestFirstRun = enable 

    def SetEnableRoutes ( self, enable ):
        self.EnableRoutes = enable 

    def IsRunning(self):
        return self.Running

    def IsStarted(self):
        return self.Started
    


