//=============================================
//
// MAIN ROUTINE FOR GSD-II SIMULATION, VER 2.0
//
//      HYUN-JUN KIM HI-TECH LAB.
//      HOSEO UNIVERSITY. 1997.1.6
//=============================================

#include <iostream.h>
#include <dos.h>
#include <conio.h>
#include <process.h>
#include <graphics.h>
#include "graphii.h"
#include "simul.h"

SIMULATION GSDII;

void running()
{
	int racemode=0;

	GSDII.initrunning();
	GSDII.setspeed(10);
	GSDII.setgoal(289);
	GSDII.set_to_goal(XX_WALL);
	GSDII.putracemode(racemode, 0xc);

	GSDII << GO9CM;

	while(1) {

		if(kbhit()) {
			if(getch()==27) return;
		}

		GSDII.detectwall();
		GSDII.tracepath();

		switch(GSDII.getcommand()) {
			case t0:
				GSDII << GO18CM;
			break;
			case tL45:
				GSDII << LSTURN;
			break;
			case tR45:
				GSDII << RSTURN;
			break;
			default:
				GSDII << GO9CM << LT180 << GO9CM;
			break;
		}

		if(GSDII.chktarget()) {

			GSDII << GO9CM << LT180;
			delay(2000);

			GSDII.putracemode(racemode, 0);
			racemode++;
			GSDII.putracemode(racemode, 0xc);

			if(racemode==14) break;

			if(racemode&1) GSDII.set_to_home(XX_WALL);
				else GSDII.set_to_goal(NO_WALL);


			GSDII << GO9CM;

		}

		if(racemode==0) GSDII.chkgoalborder();
	}
}

void loadfile()
{
	char fname[20];

	closegr();

	cout << "\n\n Type filename: ";
	cin >> fname;

	initgr();

	GSDII.clearsimmap();
	GSDII.initrunning();

	if(GSDII.loadmaze(fname)==0) {
		setcolor(0xc);
		GSDII.putmassage(20, "file not found !!");
		cout << '\x7';
		delay(500);
		setcolor(0x0);
		GSDII.putmassage(20, "file not found !!");
	}
}

void main(int arg_num, char *arg[])
{
	initgr();

	GSDII.initwindow(0, 0, 29, 3);

	if(arg_num>1) {
		if(!GSDII.loadmaze(arg[1])) {
			closegr();
			cout << "File not found !!!!";
			return;
		}
	}

	while(1) {
		switch(getch()) {

			case 27: closegr(); return;

			case 'R':
			case 'r':
				running();
			break;

			case 'L':
			case 'l': loadfile();
			break;

		}
	}
}
