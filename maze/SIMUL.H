// a¶¯a· ·¡•· ¤w¤ó
enum {
	GO18CM, GO13CM, GO9CM, LT45, RT45, LT90, RT90, LT180, RT180,
	LSTURN, RSTURN, GOBLOCK
};

//Èå ˆaº—Ã¡Ÿi ¸÷·
//Èå·¡ »¢»¥¥¡”a “aŸ¡‹¡ ˜¢…µA
//·©¸÷Ðe ˆaº—Ã¡Ÿi º“e ˆõ·¡ ÐsŸ¡¸â·¡”a.
enum {
        WFRONT =1, //¸å»¥¯¡· ˆaº—Ã¡
        WPATH45=1, //45•¡ ºÐ—¯¡· ˆaº—Ã¡
        WTURN45=2, //45•¡ Èå¯¡· ˆaº—Ã¡
        WTURN90=2, //90•¡ Èå¯¡· ˆaº—Ã¡
        WTURN135=3, //135•¡ Èå¯¡· ˆaº—Ã¡
        WTURN180=3 //180•¡ Èå¯¡· ˆaº—Ã¡
};

enum {

        //¼b® ¶áÃ¡µA¬á ·¡•·¯¡· ¶áÃ¡· ¥eÑÁ¦…
        eN      = 2, //¦‚½¢·a¡ ·¡•·¯¡
        eNE = 35,    //¦‚•·½¢·a¡,,
        eE  = 0,     //¶‘»¢·© ® ´ô“e ¤wÐ·
        eSE = 33,    //q•·
        eS  = -2,    //q
        eSW = -1,    //q¬á
        eW  = 0,     //¶‘»¢·© ® ´ô“e ¤wÐ·
        eNW = 1,     //¦‚¬á

        //Ñ©® ¶áÃ¡µA¬á ·¡•·¯¡· ¶áÃ¡· ¥eÑÁ¦…
	oN	= 0, 	//no move
	oNE	= 1,
	oE	= 34,
	oSE	= -1,
	oS	= 0, 	//no move
	oSW	= -35,
	oW	= -34,
	oNW	= -33,

        //¤wÐ· ˆt
        dN      = 0, //¦‚
        dNE = 2,     //¦‚•·
        dE      = 4, //•·
        dSE = 6,     //q•·
        dS      = 8, //q
        dSW = 10,    //q¬á
        dW      = 12,//¬á
        dNW = 14,    //¦‚¬á

        //Èå ˆt
        t0       = 0, //»¢»¥(Èå·¡ ´ô·q)
        tR45 = 2,     //µ¡Ÿe½¢ 45•¡
        tR90 = 4,     //µ¡Ÿe½¢ 90•¡
        tR135= 6,     //µ¡Ÿe½¢ 135•¡
        t180 = 8,     //180•¡
        tL135= 10,    //¶E½¢ 135•¡
        tL90 = 12,    //¶E½¢ 90•¡
        tL45 = 14     //¶E½¢ 45•¡
};

//SIMLULATION ˆ‚ÁA· ¸÷·
//MIRO, MOUSEŸi ”aº— ¬w­¢ ¤h·e ˆ‚ÁA·¡”a.
class SIMULATION : public MIRO, public MOUSE {

protected:
        int mpos, mdir; //¯©¹A  a¶¯a· ¶áÃ¡, ¤wÐ·

        int buffer[4][1024];  //´i‰¡Ÿ¡»q µe¬e¯¡· ˆa¬w a¶¯aŸi ¸á¸wÐa“e ¤áÌá
        int bp[5]; //ˆb ¤áÌá· (ÂA¬w¶á+1)·i ˆaŸ¡‹¡“e ¤áÌá Í¡·¥Èá
        int tracebuf[1024]; //‰w¡ Â¸â¯¡· ‰w¡ ¸÷¥¡Ÿi ¸á¸wÐa“e ¤áÌá
        int *tracer; //‰w¡ Â¸â¯¡· Í¡·¥Èá
        int target; // a¶¯a· ºÐ— ¡¢Îa¸ñ,
                    //»b  a¶¯a“e ·¡ ¸ñ·i Ð·Ð ºÐ—Ðe”a.
        int walldetline; //¥b· Ìe¥i¬å
                         //walldetline=NO_WALL ¡¡Ÿa“e ¥b·e ·¶“e ˆõ·a¡ ˆeº
                         //walldetline=XX_WALL ¡¡Ÿa“e ¥b·e ´ô“e ˆõ·a¡ ˆeº

        int goal; //£¡¡µA¬á· ¡¢Îa¸ñ

public:
        SIMULATION();  //¬—¬÷¸a
        ~SIMULATION(); //ÌaŠA¸a

        //£¡¡· ¶áÃ¡Ÿi ¬é¸÷
	void initwindow(int w_x, int w_y, int b_w, int w_w);

        //ºÐ—¯¡· Á¡‹¡ÑÁ ¸b´ó
	void initrunning(void);

        //¯¡£IA·¡­e  “·i Á¡‹¡ÑÁ
	void clearsimmap(void);

        //¡¢ÎaŸi £¡¡ˆa¶…•A· ¡¢Îa¡ ¬é¸÷
	void set_to_goal(int _walldetline);

        //¡¢ÎaŸi ¯¡¸b¸ñ·a¡ ¬é¸÷
	void set_to_home(int _walldetline);

        //£¡¡ˆa¶…•A¶…•A· 4¥b º—· Ðaa¡ ¬é¸÷
        //¡¢Îa¸ñ·i Àx·e ÒµA“e 4¥b ˆa¶…•A ˆa¸w ¹½·e
        //¸ñ·i ¡¢Îa¸ñ·a¡ ¬é¸÷
	void setgoal(int _goal);

        //ˆa¬w a¶¯aŸi Ìá›aŸ¡‹¡ ¸å· Á¡‹¡ÑÁ ¸b´ó
	void initspread(void);

        //bf· ¤áÌáµA¬á ˆa¬w a¶¯aŸi Ìá›aŸ±
        //bf=0, 1, 2, 3 : »b, 4ˆ· ¤áÌá ˆa¶…•A
        //ÐaaµA¬á ˆa¬w a¶¯aŸi Ìá›aŸ±
	void spread(int bf);

        //ÂA”eˆáŸ¡ »¡•¡Ÿi ‹aŸ±
	void makeshortmap(void);
        //ÂA”eˆáŸ¡ ‰w¡Ÿi Â¸øˆA
	void tracepath(void);

        //pos¶áÃ¡Ÿi dir¤wÐ··a¡ ·¡•·
	void moveposition(int &pos, int dir);

        //¶E½¢·a¡ ¯a¢—aÈå
	void lsturnning(void);

        //µ¡Ÿe½¢·a¡ ¯a¢—aÈå
	void rsturnning(void);

        //µe¬e¸a µ¡¤á¡—··i É·Ð ®ó‰A  a¶¯a
        //·¡•··i ¹A´á
        //EX> gsdii << GO18CM << LT45;
	SIMULATION &SIMULATION::operator<<(int cmd);

        //¡¢Îa¸ñµA •¡”iÐaµv“e»¡Ÿi ÁAÇa
	int chktarget(void);

        // a¶¯a ¶áÃ¡µA¬á ´|½¢ ¥b· ¶áÃ¡Ÿi ´è·q
	int get_fw_pos(void);

        // a¶¯a ¶áÃ¡µA¬á ¶E½¢ ¥b· ¶áÃ¡Ÿi ´è·q
	int get_lw_pos(void);

        // a¶¯a ¶áÃ¡µA¬á µ¡Ÿe½¢ ¥b· ¶áÃ¡Ÿi ´è·q
        int get_rw_pos(void);

        //¥b·i Ìe¥iÐe”a.
        //¯©¹A  a¶¯a· ¥b·i ­E¬á¡ Ìe¥iÐa“e žË¥‰Á •··©.
        //¯¡£IA·¡­eµA¬á“e ¯¡£IA·¡­e map(simmap)·
        //¥b¸÷¥¡Ÿi  a¶¯aˆa Ìe¥eÐe ¥b·i ¸á¸wÐe map(wallmap)
        //·a¡ ·ª´á—i·¥”a.
	void detectwall(void);

        //¡¢Îa¸ñ·i Ð·Ð ºÐ—Ði ˜, Ñe¸  a¶¯aˆa ·¡•·Ð´¡
        //Ði ¤wÐ··i ´è“e”a.
	int getcommand(void);

        //¡¢Îa¸ñ ˆa¸w¸aŸ¡µA •¡ÀbÐaµv“e»¡ ÁAÇaÐaµa
        //¡¢Îa¸ñ ˆa¸w¸aŸ¡ ¥b¸÷¥¡Ÿi ˆ—¯¥Ðe”a.
	void chkgoalborder(void);

        //ˆa¸w¹½·e ¡¢Îa¸ñ·i ¬é¸÷Ðe”a.
	void setbestgoal(void);

        // a¶¯a· ¶áÃ¡, ¤wÐ··i ÑÁ¡eµA Â‰b
	void putposition(int color);

        //‹¡¥¥ ÑÁ¡e ¡A­A»¡Ÿi ÑÁ¡eµA Â‰b
	void titlemassage(void);

        //¡A­A»¡ Â‰bÐq®
	void putmassage(int ln, char *str);

        //ºÐ—¡¡—aŸi ÑÁ¡eµA Â‰bÐe”a.
	void putracemode(int racing, int color);
};

