//=========================================
//
// ALGORISM ROUTINE FOR GSD-II SIMULATION
//
//      HYUN-JUN KIM HI-TECH LAB.
//      HOSEO UNIVERSITY. 1997.1.6
//=========================================

#include <dos.h>
#include <stdio.h>
#include <graphics.h>
#include <iostream.h>
#include <process.h>
#include <math.h>
#include "graphii.h"
#include "simul.h"

SIMULATION::SIMULATION() : MIRO(), MOUSE()
{
}

SIMULATION::~SIMULATION()
{
}

void SIMULATION::initwindow(int w_x, int w_y, int b_w, int w_w)
{
	flag=0;

	setMIRO(w_x, w_y, b_w, w_w);
	sethome(w_x, w_y, b_w, w_w);

	titlemassage();
}

void SIMULATION::initrunning()
{
	flag=0;

	cleardevice();
	setMIRO(win_x, win_y, bw, ww);
	sethome(win_x, win_y, bw, ww);

	titlemassage();

	mdir=0;
	mpos=2;
}

void SIMULATION::clearsimmap()
{
	initwallmap(simmap);

	for(int i=0;i<34*17;i++) {
		if(simmap[i]==XX_WALL) simmap[i]=NO_WALL;
	}
}

void SIMULATION::set_to_goal(int _walldetline)
{
	target=goal;
	walldetline=_walldetline;
}

void SIMULATION::set_to_home(int _walldetline)
{
	target=2;
	walldetline=_walldetline;
}

void SIMULATION::setgoal(int _goal)
{
	goal=_goal;
}

void SIMULATION::initspread()
{
	int i;

	for(i=0;i<34*17;i++) {
		if(wallmap[i]<=walldetline) dirmap[i]=MAPREF;
			else dirmap[i]=MAPREF-1;
	}

	bp[0]=bp[1]=bp[2]=bp[3]=0;

	buffer[0][bp[0]++]=mpos;
	buffer[0][bp[0]++]=mdir;
}

void SIMULATION::spread(int bf)
{
	int ipos, idir;

#define pushpos(pos, wgt) buffer[(bf+wgt)%4][bp[(bf+wgt)%4]++]=pos
#define pushdir(dir, wgt) buffer[(bf+wgt)%4][bp[(bf+wgt)%4]++]=dir

	idir=buffer[bf][--bp[bf]];
	ipos=buffer[bf][--bp[bf]];

	if(dirmap[ipos]!=MAPREF) return;

	dirmap[ipos]=idir;

	if(ipos&1) {

	// ODD position
		switch(idir) {

			case dN:
			case dS:
				closegr();
				cout << "error ODD position !!";
				exit(0);
			break;

			case dE:

				//Front
				if(dirmap[ipos+oE]==MAPREF) {
					pushpos(ipos+oE, WFRONT);
					pushdir(dE, WFRONT);
				}

				//Left 45
				if(dirmap[ipos+oNE]==MAPREF) {
					pushpos(ipos+oNE, WTURN45);
					pushdir(dNE, WTURN45);
				}

				//Right 45
				if(dirmap[ipos+oSE]==MAPREF) {
					pushpos(ipos+oSE, WTURN45);
					pushdir(dSE, WTURN45);
				}

				//Left135
				if(dirmap[ipos+oNW]==MAPREF) {
					pushpos(ipos+oNW, WTURN135);
					pushdir(dNW, WTURN135);
				}

				//Right 135
				if(dirmap[ipos+oSW]==MAPREF) {
					pushpos(ipos+oSW, WTURN135);
					pushdir(dSW, WTURN135);
				}

				//Back
				if(dirmap[ipos+oW]==MAPREF) {
					pushpos(ipos+oW, WTURN180);
					pushdir(dW, WTURN180);
				}

			break;

			case dW:

				//Front
				if(dirmap[ipos+oW]==MAPREF) {
					pushpos(ipos+oW, WFRONT);
					pushdir(dW, WFRONT);
				}

				//Left 45
				if(dirmap[ipos+oSW]==MAPREF) {
					pushpos(ipos+oSW, WTURN45);
					pushdir(dSW, WTURN45);
				}

				//Right 45
				if(dirmap[ipos+oNW]==MAPREF) {
					pushpos(ipos+oNW, WTURN45);
					pushdir(dNW, WTURN45);
				}

				//Left135
				if(dirmap[ipos+oSE]==MAPREF) {
					pushpos(ipos+oSE, WTURN135);
					pushdir(dSE, WTURN135);
				}

				//Right 135
				if(dirmap[ipos+oNE]==MAPREF) {
					pushpos(ipos+oNE, WTURN135);
					pushdir(dNE, WTURN135);
				}

				//Back
				if(dirmap[ipos+oE]==MAPREF) {
					pushpos(ipos+oE, WTURN180);
					pushdir(dE, WTURN180);
				}

			break;

			case dNE:

				//Front ;45-degree path
				if(dirmap[ipos+oNE]==MAPREF) {
					pushpos(ipos+oNE, WPATH45);
					pushdir(dNE, WPATH45);
				}

				//Right 45
				if(dirmap[ipos+oE]==MAPREF) {
					pushpos(ipos+oE, WTURN45);
					pushdir(dE, WTURN45);
				}

				//Left 90
				if(dirmap[ipos+oNW]==MAPREF) {
					pushpos(ipos+oNW, WTURN90);
					pushdir(dNW, WTURN90);
				}

				//Right 90
				if(dirmap[ipos+oSE]==MAPREF) {
					pushpos(ipos+oSE, WTURN90);
					pushdir(dSE, WTURN90);
				}

				//Left 135
				if(dirmap[ipos+oW]==MAPREF) {
					pushpos(ipos+oW, WTURN135);
					pushdir(dW, WTURN135);
				}

				//Back
				if(dirmap[ipos+oSW]==MAPREF) {
					pushpos(ipos+oSW, WTURN180);
					pushdir(dSW, WTURN180);
				}

			break;

			case dSE:

				//Front ;45-degree path
				if(dirmap[ipos+oSE]==MAPREF) {
					pushpos(ipos+oSE, WPATH45);
					pushdir(dSE, WPATH45);
				}

				//Left 45
				if(dirmap[ipos+oE]==MAPREF) {
					pushpos(ipos+oE, WTURN45);
					pushdir(dE, WTURN45);
				}

				//Left 90
				if(dirmap[ipos+oNE]==MAPREF) {
					pushpos(ipos+oNE, WTURN90);
					pushdir(dNE, WTURN90);
				}

				//Right 90
				if(dirmap[ipos+oSW]==MAPREF) {
					pushpos(ipos+oSW, WTURN90);
					pushdir(dSW, WTURN90);
				}

				//Right 135
				if(dirmap[ipos+oW]==MAPREF) {
					pushpos(ipos+oW, WTURN135);
					pushdir(dW, WTURN135);
				}

				//Back
				if(dirmap[ipos+oNW]==MAPREF) {
					pushpos(ipos+oNW, WTURN180);
					pushdir(dNW, WTURN180);
				}

			break;

			case dSW:

				//Front ;45-degree path
				if(dirmap[ipos+oSW]==MAPREF) {
					pushpos(ipos+oSW, WPATH45);
					pushdir(dSW, WPATH45);
				}

				//Right 45
				if(dirmap[ipos+oW]==MAPREF) {
					pushpos(ipos+oW, WTURN45);
					pushdir(dW, WTURN45);
				}

				//Left 90
				if(dirmap[ipos+oSE]==MAPREF) {
					pushpos(ipos+oSE, WTURN90);
					pushdir(dSE, WTURN90);
				}

				//Right 90
				if(dirmap[ipos+oNW]==MAPREF) {
					pushpos(ipos+oNW, WTURN90);
					pushdir(dNW, WTURN90);
				}

				//Left 135
				if(dirmap[ipos+oE]==MAPREF) {
					pushpos(ipos+oE, WTURN135);
					pushdir(dE, WTURN135);
				}

				//Back
				if(dirmap[ipos+oNE]==MAPREF) {
					pushpos(ipos+oNE, WTURN180);
					pushdir(dNE, WTURN180);
				}

			break;

			case dNW:

				//Front ;45-degree path
				if(dirmap[ipos+oNW]==MAPREF) {
					pushpos(ipos+oNW, WPATH45);
					pushdir(dNW, WPATH45);
				}

				//Left 45
				if(dirmap[ipos+oW]==MAPREF) {
					pushpos(ipos+oW, WTURN45);
					pushdir(dW, WTURN45);
				}

				//Left 90
				if(dirmap[ipos+oSW]==MAPREF) {
					pushpos(ipos+oSW, WTURN90);
					pushdir(dSW, WTURN90);
				}

				//Right 90
				if(dirmap[ipos+oNE]==MAPREF) {
					pushpos(ipos+oNE, WTURN90);
					pushdir(dNE, WTURN90);
				}

				//Right 135
				if(dirmap[ipos+oE]==MAPREF) {
					pushpos(ipos+oE, WTURN135);
					pushdir(dE, WTURN135);
				}

				//Back
				if(dirmap[ipos+oSE]==MAPREF) {
					pushpos(ipos+oSE, WTURN180);
					pushdir(dSE, WTURN180);
				}

			break;

		}

	} else {

	// EVEN position
		switch(idir) {

			case dE:
			case dW:
				closegr();
				cout << "error EVEN position !!";
				exit(0);
			break;

			case dN:

				//Front
				if(dirmap[ipos+eN]==MAPREF) {
					pushpos(ipos+eN, WFRONT);
					pushdir(dN, WFRONT);
				}

				//Left 45
				if(dirmap[ipos+eNW]==MAPREF) {
					pushpos(ipos+eNW, WTURN45);
					pushdir(dNW, WTURN45);
				}

				//Right 45
				if(dirmap[ipos+eNE]==MAPREF) {
					pushpos(ipos+eNE, WTURN45);
					pushdir(dNE, WTURN45);
				}

				//Left 135
				if(dirmap[ipos+eSW]==MAPREF) {
					pushpos(ipos+eSW, WTURN135);
					pushdir(dSW, WTURN135);
				}

				//Right 135
				if(dirmap[ipos+eSE]==MAPREF) {
					pushpos(ipos+eSE, WTURN135);
					pushdir(dSE, WTURN135);
				}

				//Back
				if(dirmap[ipos+eS]==MAPREF) {
					pushpos(ipos+eS, WTURN180);
					pushdir(dS, WTURN180);
				}

			break;

			case dS:

				//Front
				if(dirmap[ipos+eS]==MAPREF) {
					pushpos(ipos+eS, WFRONT);
					pushdir(dS, WFRONT);
				}

				//Left 45
				if(dirmap[ipos+eSE]==MAPREF) {
					pushpos(ipos+eSE, WTURN45);
					pushdir(dSE, WTURN45);
				}

				//Right 45
				if(dirmap[ipos+eSW]==MAPREF) {
					pushpos(ipos+eSW, WTURN45);
					pushdir(dSW, WTURN45);
				}

				//Left 135
				if(dirmap[ipos+eNE]==MAPREF) {
					pushpos(ipos+eNE, WTURN135);
					pushdir(dNE, WTURN135);
				}

				//Right 135
				if(dirmap[ipos+eNW]==MAPREF) {
					pushpos(ipos+eNW, WTURN135);
					pushdir(dNW, WTURN135);
				}

				//Back
				if(dirmap[ipos+eN]==MAPREF) {
					pushpos(ipos+eN, WTURN180);
					pushdir(dN, WTURN180);
				}

			break;

			case dNE:

				//Front ;45-degree path
				if(dirmap[ipos+eNE]==MAPREF) {
					pushpos(ipos+eNE, WPATH45);
					pushdir(dNE, WPATH45);
				}

				//Left 45
				if(dirmap[ipos+eN]==MAPREF) {
					pushpos(ipos+eN, WTURN45);
					pushdir(dN, WTURN45);
				}

				//Left 90
				if(dirmap[ipos+eNW]==MAPREF) {
					pushpos(ipos+eNW, WTURN90);
					pushdir(dNW, WTURN90);
				}

				//Right 90
				if(dirmap[ipos+eSE]==MAPREF) {
					pushpos(ipos+eSE, WTURN90);
					pushdir(dSE, WTURN90);
				}

				//Right 135
				if(dirmap[ipos+eS]==MAPREF) {
					pushpos(ipos+eS, WTURN135);
					pushdir(dS, WTURN135);
				}

				//Back
				if(dirmap[ipos+eSW]==MAPREF) {
					pushpos(ipos+eSW, WTURN180);
					pushdir(dSW, WTURN180);
				}

			break;

			case dSE:

				//Front ;45-degree path
				if(dirmap[ipos+eSE]==MAPREF) {
					pushpos(ipos+eSE, WPATH45);
					pushdir(dSE, WPATH45);
				}

				//Right 45
				if(dirmap[ipos+eS]==MAPREF) {
					pushpos(ipos+eS, WTURN45);
					pushdir(dS, WTURN45);
				}

				//Left 90
				if(dirmap[ipos+eNE]==MAPREF) {
					pushpos(ipos+eNE, WTURN90);
					pushdir(dNE, WTURN90);
				}

				//Right 90
				if(dirmap[ipos+eSW]==MAPREF) {
					pushpos(ipos+eSW, WTURN90);
					pushdir(dSW, WTURN90);
				}

				//Left 135
				if(dirmap[ipos+eN]==MAPREF) {
					pushpos(ipos+eN, WTURN135);
					pushdir(dN, WTURN135);
				}

				//Back
				if(dirmap[ipos+eNW]==MAPREF) {
					pushpos(ipos+eNW, WTURN180);
					pushdir(dNW, WTURN180);
				}

			break;

			case dSW:

				//Front ;45-degree path
				if(dirmap[ipos+eSW]==MAPREF) {
					pushpos(ipos+eSW, WPATH45);
					pushdir(dSW, WPATH45);
				}

				//Left 45
				if(dirmap[ipos+eS]==MAPREF) {
					pushpos(ipos+eS, WTURN45);
					pushdir(dS, WTURN45);
				}

				//Left 90
				if(dirmap[ipos+eSE]==MAPREF) {
					pushpos(ipos+eSE, WTURN90);
					pushdir(dSE, WTURN90);
				}

				//Right 90
				if(dirmap[ipos+eNW]==MAPREF) {
					pushpos(ipos+eNW, WTURN90);
					pushdir(dNW, WTURN90);
				}

				//Right 135
				if(dirmap[ipos+eN]==MAPREF) {
					pushpos(ipos+eN, WTURN135);
					pushdir(dN, WTURN135);
				}

				//Back
				if(dirmap[ipos+eNE]==MAPREF) {
					pushpos(ipos+eNE, WTURN180);
					pushdir(dNE, WTURN180);
				}

			break;

			case dNW:

				//Front ;45-degree path
				if(dirmap[ipos+eNW]==MAPREF) {
					pushpos(ipos+eNW, WPATH45);
					pushdir(dNW, WPATH45);
				}

				//Right 45
				if(dirmap[ipos+eN]==MAPREF) {
					pushpos(ipos+eN, WTURN45);
					pushdir(dN, WTURN45);
				}

				//Left 90
				if(dirmap[ipos+eSW]==MAPREF) {
					pushpos(ipos+eSW, WTURN90);
					pushdir(dSW, WTURN90);
				}

				//Right 90
				if(dirmap[ipos+eNE]==MAPREF) {
					pushpos(ipos+eNE, WTURN90);
					pushdir(dNE, WTURN90);
				}

				//Left 135
				if(dirmap[ipos+eS]==MAPREF) {
					pushpos(ipos+eS, WTURN135);
					pushdir(dS, WTURN135);
				}

				//Back
				if(dirmap[ipos+eSE]==MAPREF) {
					pushpos(ipos+eSE, WTURN180);
					pushdir(dSE, WTURN180);
				}

			break;

		}
	}

}

void SIMULATION::makeshortmap()
{
	initspread();
	//putdirmap();

	while(1) {
		while(bp[0]) spread(0);
		while(bp[1]) spread(1);
		while(bp[2]) spread(2);

		if(dirmap[target]!=MAPREF) return;
		while(bp[3]) {
			if(dirmap[target]!=MAPREF) return;
			spread(3);
		}
	}
}

#define GO_18CM 16
#define GO_13CM 18

void SIMULATION::tracepath()
{
	int ipos,curdir, olddir;

	makeshortmap();

	tracer=tracebuf;
	ipos=target;
	curdir=dirmap[ipos];

	while(ipos!=mpos) {

		olddir=curdir;
		curdir=dirmap[ipos];
		olddir=(olddir-curdir)&0xf;
		*tracer++=olddir;

		switch(curdir) {
			case dN:
				*tracer++=GO_18CM;
				if(ipos&1) ipos+=oS;
					else ipos+=eS;
			break;

			case dNE:
				*tracer++=GO_13CM;
				if(ipos&1) ipos+=oSW;
					else ipos+=eSW;
			break;

			case dE:
				*tracer++=GO_18CM;
				if(ipos&1) ipos+=oW;
					else ipos+=eW;
			break;

			case dSE:
				*tracer++=GO_13CM;
				if(ipos&1) ipos+=oNW;
					else ipos+=eNW;
			break;

			case dS:
				*tracer++=GO_18CM;
				if(ipos&1) ipos+=oN;
					else ipos+=eN;
			break;

			case dSW:
				*tracer++=GO_13CM;
				if(ipos&1) ipos+=oNE;
					else ipos+=eNE;
			break;

			case dW:
				*tracer++=GO_18CM;
				if(ipos&1) ipos+=oE;
					else ipos+=eE;

			break;

			case dNW:
				*tracer++=GO_13CM;
				if(ipos&1) ipos+=oSE;
					else ipos+=eSE;
			break;

		}
	}

	olddir=curdir;
	curdir=dirmap[ipos];
	olddir=(olddir-curdir)&0xf;
	*tracer=olddir;
}

void SIMULATION::moveposition(int &pos, int dir)
{
	switch(dir) {
		case dN:
			if(pos&1) pos+=oN;
				else pos+=eN;
		break;
		case dNE:
			if(pos&1) pos+=oNE;
				else pos+=eNE;
		break;
		case dE:
			if(pos&1) pos+=oE;
				else pos+=eE;
		break;
		case dSE:
			if(pos&1) pos+=oSE;
				else pos+=eSE;
		break;
		case dS:
			if(pos&1) pos+=oS;
				else pos+=eS;
		break;
		case dSW:
			if(pos&1) pos+=oSW;
				else pos+=eSW;
		break;
		case dW:
			if(pos&1) pos+=oW;
				else pos+=eW;
		break;
		case dNW:
			if(pos&1) pos+=oNW;
				else pos+=eNW;
		break;
	}
}

void SIMULATION::lsturnning()
{
	int 	cnt=(double)bw*M_PI/4/2;
	double 	_angle=-90./cnt;

	double _dir=fmod(dir-90., 360.);
	double _x = x + M_SQRT2 * (double)bw/2 * sin( (dir-45.)/180.*M_PI );
	double _y = y - M_SQRT2 * (double)bw/2 * cos( (dir-45.)/180.*M_PI );

	double basex = x + (double)bw/2 * sin( (dir-90.)/180.*M_PI );
	double basey = y - (double)bw/2 * cos( (dir-90.)/180.*M_PI );

	while(cnt--) {

		oldx=x; oldy=y;
		erasemouse();

		x = basex + (double)bw/2 * sin( fmod(dir+_angle+90., 360.)/180.*M_PI );
		y = basey - (double)bw/2 * cos( fmod(dir+_angle+90., 360.)/180.*M_PI );

		turnmouse(_angle);
		movemouse(0);
	}

	oldx=x; oldy=y;
	erasemouse();
	x=_x; y=_y;
	dir=_dir;
	movemouse(0);
}

void SIMULATION::rsturnning()
{
	int 	cnt=(double)bw*M_PI/4/2;
	double 	_angle=90./cnt;

	double _dir=fmod(dir+90., 360.);
	double _x = x + M_SQRT2 * (double)bw/2 * sin( (dir+45.)/180.*M_PI );
	double _y = y - M_SQRT2 * (double)bw/2 * cos( (dir+45.)/180.*M_PI );

	double basex = x + (double)bw/2 * sin( (dir+90.)/180.*M_PI );
	double basey = y - (double)bw/2 * cos( (dir+90.)/180.*M_PI );

	while(cnt--) {

		oldx=x; oldy=y;
		erasemouse();

		x = basex + (double)bw/2 * sin( fmod(dir+_angle-90., 360.)/180.*M_PI );
		y = basey - (double)bw/2 * cos( fmod(dir+_angle-90., 360.)/180.*M_PI );

		turnmouse(_angle);
		movemouse(0);
	}

	oldx=x; oldy=y;
	erasemouse();
	x=_x; y=_y;
	dir=_dir;
	movemouse(0);
}

SIMULATION &SIMULATION::operator<<(int cmd)
{

	switch(cmd) {

		case GOBLOCK:
			if(mdir==dN || mdir==dE || mdir==dS || mdir==dW) {
				running(bw);
			} else {
				running(bw*M_PI);
			}
			putposition(0);
			moveposition(mpos, mdir);
			putposition(0xf);
		break;

		case GO18CM:
			running(bw);
			putposition(0);
			moveposition(mpos, mdir);
			putposition(0xf);;
		break;

		case GO13CM:
			running(bw*M_PI);
			putposition(0);
			moveposition(mpos, mdir);
			putposition(0xf);;
		break;

		case GO9CM:
			running(bw/2);
		break;

		case LT45:
			turnning(-45);
			putposition(0);
			mdir=(mdir-2)&0xf;
			putposition(0xf);;
		break;

		case RT45:
			turnning(45);
			putposition(0);
			mdir=(mdir+2)&0xf;
			putposition(0xf);;
		break;

		case LT90:
			turnning(-90);
			putposition(0);
			mdir=(mdir-4)&0xf;
			putposition(0xf);;
		break;

		case RT90:
			turnning(90);
			putposition(0);
			mdir=(mdir+4)&0xf;
			putposition(0xf);;

		break;
		case LT180:
			turnning(-180);
			putposition(0);
			mdir=(mdir-8)&0xf;
			putposition(0xf);;
		break;

		case RT180:
			turnning(180);
			putposition(0);
			mdir=(mdir+8)&0xf;
			putposition(0xf);;
		break;

		case LSTURN:
			lsturnning();
			putposition(0);
			moveposition(mpos, (mdir-2)&0xf);
			mdir=(mdir-4)&0xf;
			putposition(0xf);;
		break;

		case RSTURN:
			rsturnning();
			putposition(0);
			moveposition(mpos, (mdir+2)&0xf);
			mdir=(mdir+4)&0xf;
			putposition(0xf);;
		break;
		//case LDIAG:
		//case RDIAG:
	}
	return *this;
}

int SIMULATION::chktarget(void)
{
	if(mpos==target) return 1;
	return 0;
}

int SIMULATION::get_fw_pos(void)
{
	int _pos=mpos;

	moveposition(_pos, mdir);

	return _pos;
}

int SIMULATION::get_lw_pos(void)
{
	int _pos=mpos;

	moveposition(_pos, (mdir-2)&0xf);

	return _pos;
}

int SIMULATION::get_rw_pos(void)
{
	int _pos=mpos;

	moveposition(_pos, (mdir+2)&0xf);

	return _pos;
}

void SIMULATION::detectwall(void)
{
	int fw, lw, rw;

	fw=get_fw_pos();
	lw=get_lw_pos();
	rw=get_rw_pos();

	wallmap[fw]=simmap[fw];
	wallmap[lw]=simmap[lw];
	wallmap[rw]=simmap[rw];

	if(wallmap[fw]==YES_WALL) putwall(fw, SOLID_WALL);
	if(wallmap[lw]==YES_WALL) putwall(lw, SOLID_WALL);
	if(wallmap[rw]==YES_WALL) putwall(rw, SOLID_WALL);
}

int SIMULATION::getcommand(void)
{
	return *tracer;
}

void SIMULATION::chkgoalborder(void)
{
	if(mpos==252 || mpos==253 || mpos==255 || mpos==256 || mpos==286
		|| mpos==290 || mpos==321 || mpos==323) setbestgoal();
}

void SIMULATION::setbestgoal(void)
{
	wallmap[252]=simmap[252]=YES_WALL;
	wallmap[253]=simmap[253]=YES_WALL;
	wallmap[255]=simmap[255]=YES_WALL;
	wallmap[256]=simmap[256]=YES_WALL;
	wallmap[286]=simmap[286]=YES_WALL;
	wallmap[290]=simmap[290]=YES_WALL;
	wallmap[321]=simmap[321]=YES_WALL;
	wallmap[323]=simmap[323]=YES_WALL;

	wallmap[mpos]=simmap[mpos]=NO_WALL;

	if(mpos!=252) putwall(252, SOLID_WALL);
	if(mpos!=253) putwall(253, SOLID_WALL);
	if(mpos!=255) putwall(255, SOLID_WALL);
	if(mpos!=256) putwall(256, SOLID_WALL);
	if(mpos!=286) putwall(286, SOLID_WALL);
	if(mpos!=290) putwall(290, SOLID_WALL);
	if(mpos!=321) putwall(321, SOLID_WALL);
	if(mpos!=323) putwall(323, SOLID_WALL);

	wallmap[254]=NO_WALL;
	wallmap[287]=NO_WALL;
	wallmap[288]=NO_WALL;
	wallmap[289]=NO_WALL;

	goal=mpos;
	moveposition(goal, mdir);
	target=goal;
}

void SIMULATION::putposition(int color)
{
	char s[20];
	char *d[8]={"N", "NE", "E", "SE", "S", "SW", "W", "NW"};

	setcolor(color);

	sprintf(s, "position:%d", mpos);
	putmassage(23, s);

	sprintf(s, "direction:%s", d[mdir>>1]);
	putmassage(24, s);
}

void SIMULATION::titlemassage()
{
	setcolor(0xd);
	putmassage(0, "--------------");
	putmassage(1, "MICRO MOUSE");
	putmassage(2, "SIMULATOR V2.0");
	putmassage(3, "FOR GSD-II");
	putmassage(4, "--------------");

	setcolor(0xe);
	putmassage(6, "PROGRAMED BY");
	putmassage(7, "HYUN-JUN KIM");
	putmassage(8, "ELECTRONICS 94");
	putmassage(9, "HOSEO UNIVERSITY");

	setcolor(0xb);
	putmassage(11, "-----------------");
	putmassage(12, "     Using Key");
	putmassage(13, "-----------------");
	putmassage(14, "ESC: Stopping run");
	putmassage(15, "    &Exit program");
	putmassage(16, "R  : Running");
	putmassage(17, "L  : Loading maze");
	putmassage(18, "-----------------");
}

void SIMULATION::putracemode(int racing, int color)
{
	char s[20];

	setcolor(color);

	sprintf(s, "%dst running", (racing>>1)+1);
	putmassage(20, s);

	if(racing&1) {
		putmassage(21, "Going to HOME !!");
	} else {
		putmassage(21, "Going to GOAL !!");
	}
}

void SIMULATION::putmassage(int ln, char *str)
{
	outtextxy(bw*16+win_x+10, win_y+10+10*ln, str);
}

