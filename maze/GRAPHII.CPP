//===============================================
//
// GRAPHIC ROUTINE FOR GSD-II SIMULATION, VER 2.0
//
//      HYUN-JUN KIM HI-TECH LAB.
//      HOSEO UNIVERSITY. 1997.1.6
//===============================================

#include <fstream.h>
#include <graphics.h>
#include <math.h>
#include <conio.h>
#include <dos.h>
#include "graphii.h"

void initgr(void)
{
	int gd=VGA, gm=VGAHI;
	initgraph(&gd, &gm, "");
}

void closegr(void)
{
	closegraph();
}

MIRO::MIRO()
{
	initwallmap(simmap);

	for(int i=0;i<34*17;i++) {
		if(simmap[i]==XX_WALL) simmap[i]=NO_WALL;
	}
}

MIRO::~MIRO()
{
}

void MIRO::setMIRO(int w_x, int w_y, int b_w, int w_w)
{
	win_x=w_x; win_y=w_y;
	bw=b_w; ww=w_w;

	initwallmap(wallmap);

	drawpole();
	drawmaze(wallmap, SOLID_WALL);
	drawmaze(simmap, EMPTY_WALL);
}

void MIRO::setboder(char *map, int spos, int delta)
{
	int i=16;

	while(i--) { map[spos]=YES_WALL; spos+=delta; }
}

void MIRO::initwallmap(char *map)
{
	int i;

	for(i=0;i<34*17;i++) map[i]=XX_WALL;

	setboder(map, 32, 34);
	setboder(map, 34*16+1, 2);
	setboder(map, 0, 34);
	setboder(map, 1, 2);
	map[2]=NO_WALL;
	map[35]=YES_WALL;
}

void MIRO::drawpole(void)
{
	int i,j;

	setfillstyle(SOLID_FILL, 0xb);

	for(i=0;i<17;i++) {

		for(j=0;j<17;j++) {
			bar(win_x+bw*i, win_y+bw*j,win_x+bw*i+ww, win_y+bw*j+ww);
		}

	}
}

void MIRO::putwall(int pos, int type)
{
	int x, y;


	setcolor(0x9);
	setfillstyle(SOLID_FILL, 0x9);

	if(pos&1) {

		//odd position
		x=win_x+bw*(pos/34);
		y=win_y+bw*(15-pos%34/2);
		if(type==EMPTY_WALL) {
			rectangle(x, y+ww+1, x+ww, y+bw-1);
		} else bar(x, y+ww+1, x+ww, y+bw-1);

	} else {

		//even position
		x=win_x+bw*(pos/34);
		y=win_y+bw*(16-pos%34/2);
		if(type==EMPTY_WALL) {
			rectangle(x+ww+1, y, x+bw-1, y+ww);
		} else bar(x+ww+1, y, x+bw-1, y+ww);
	}
}

void MIRO::drawmaze(char *map, int type)
{
	int i;

	for(i=0;i<34*17;i++) {
		if(map[i]==YES_WALL) putwall(i, type);
	}

}

void MIRO::_putdirmap(int evencolor, int oddcolor)
{
	int pos;
	int x, y;
	char s[][3]={"N","NE","E","SE","S","SW","W","NW"};
	char far *backgr;


	for(pos=0;pos<34*17;pos++) {

		if(dirmap[pos]>14 && dirmap[pos]!=MAPREF) continue;

		if(pos&1) {

			//odd position
			setcolor(oddcolor);
			x=win_x+bw*(pos/34)+ww+4;
			y=win_y+bw*(15-pos%34/2)+ww+8;
		} else {

			//even position
			setcolor(evencolor);
			x=win_x+bw*(pos/34)+ww+8;
			y=win_y+bw*(16-pos%34/2)-9;
		}

		if(dirmap[pos]==MAPREF) outtextxy(x, y, "MR");
			else outtextxy(x,y,s[dirmap[pos]>>1]);
	}
}

void MIRO::putdirmap(void)
{
	_putdirmap(2, 4);
	getch();
	_putdirmap(0, 0);
}

void MIRO::_putwallmap(int evencolor, int oddcolor)
{
	int pos;
	int x, y;

	for(pos=0;pos<34*17;pos++) {

		if(pos&1) {

			//odd position
			setcolor(oddcolor);
			x=win_x+bw*(pos/34)+ww+4;
			y=win_y+bw*(15-pos%34/2)+ww+8;
		} else {

			//even position
			setcolor(evencolor);
			x=win_x+bw*(pos/34)+ww+8;
			y=win_y+bw*(16-pos%34/2)-9;
		}

		switch(wallmap[pos]) {
			case YES_WALL: outtextxy(x, y, "yes");
			break;
			case XX_WALL: outtextxy(x, y, "xx");
			break;
			case NO_WALL: outtextxy(x, y, "no");
			break;
		}
	}
}

void MIRO::putwallmap(void)
{
	_putwallmap(2, 4);
	getch();
	_putwallmap(0, 0);
}

int MIRO::loadmaze(char *filename)
{
	int i;
	char mirodata;

	for(i=0;i<34*17;i++) simmap[i]=NO_WALL;

	ifstream maze(filename, ios::binary);

	if(maze.fail()) {
		initwallmap(simmap);

		for(int i=0;i<34*17;i++) {
			if(simmap[i]==XX_WALL) simmap[i]=NO_WALL;
		}

		maze.close();
		return 0;

	}

	for(i=0;i<256;i++) {
		if(!maze.get(mirodata)) break;

		//North
		if(mirodata&1) simmap[i*2+(int)(i/16)*2+2]=YES_WALL;

		//East
		if(mirodata&2) simmap[i*2+(int)(i/16)*2+35]=YES_WALL;

		//South
		if(mirodata&4) simmap[i*2+(int)(i/16)*2]=YES_WALL;

		//West
		if(mirodata&8) simmap[i*2+(int)(i/16)*2+1]=YES_WALL;
	}

	maze.close();
	drawmaze(simmap, EMPTY_WALL);

	return 1;
}

MOUSE::MOUSE()
{
	speed=10;
	flag=0;
}

MOUSE::~MOUSE()
{
}

void MOUSE::sethome(int w_x, int w_y, int b_w, int w_w)
{
	x=w_x+w_w+(double)((b_w-w_w)/2);
	y=w_y+w_w+(double)((b_w-w_w)/2)+b_w*15;
	dir=0.;
	movemouse(0);
}

void MOUSE::setspeed(int _speed)
{
	speed=_speed;
}

void MOUSE::movemouse(double dist)
{
	oldx=x;
	oldy=y;
	x=x+dist * sin( dir/180.*M_PI );
	y=y-dist * cos( dir/180.*M_PI );

	mloc[0]= x+5 * sin( dir/180.*M_PI );
	mloc[1]= y-5 * cos( dir/180.*M_PI );

	mloc[2]= x+5 * sin( (dir+120.)/180.*M_PI );
	mloc[3]= y-5 * cos( (dir+120.)/180.*M_PI );

	mloc[4]= x+5 * sin( (dir-120.)/180.*M_PI );
	mloc[5]= y-5 * cos( (dir-120.)/180.*M_PI );

	putmouse();
	delay(speed);
}

void MOUSE::turnmouse(double angle)
{
	dir=fmod(dir+angle, 360.);
}

void MOUSE::putmouse(void)
{
	erasemouse();

	putpixel(x, y, 0x7);

	getimage(x-6, y-6, x+6, y+6, image);
	setcolor(0xf);
	setfillstyle(SOLID_FILL, 5);
	fillpoly(3, mloc);
	flag=1;
}

void MOUSE::erasemouse(void )
{
	if(!flag) return;
	putimage(oldx-6, oldy-6, image, COPY_PUT);
	flag=0;
}

void MOUSE::running(double dist)
{
	double i=0;

	while(1) {
		i+=5;


		if(i>=dist) break;
		movemouse(5);
	}

	movemouse(dist-(i-5));
}

void MOUSE::turnning(double angle)
{

	double i=0;
	double next_dir;


	next_dir=fmod(dir+angle, 360.);

	if(angle<0) {
		while(1) {
			i-=5;
			if(i<=angle) break;
			dir=i;
			movemouse(0);
		}
	}

	if(angle>0) {
		while(1) {
			i+=5;
			if(i>=angle) break;
			dir=i;
			movemouse(0);
		}
	}

	dir=next_dir;
	movemouse(0);
}

