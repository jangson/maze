#define WORD unsigned int
#define BYTE unsigned char

//Îa¯¡Ði ¥b· ÑwÈ
enum {
        SOLID_WALL, //­¢·¡ À¶¡»¥ ¥b
        EMPTY_WALL  //­¢·¡ §¥ ¥b
};

//¥b»¡•¡ ¬w· ¥b•A·¡Èáˆa ˆa»¡“e ˆt
enum {
        NO_WALL = 0, //¥b·¡ ´ô·q
        XX_WALL = 3, //¥b·¡ ·¶“e»¡ ´ô“e»¡ ¡¡Ÿe”a.
                     //»b, Ìe¥iÐa»¡ ´g·e ¥b
        YES_WALL = 6, //¥b·¡ ·¶·q
        MAPREF = 0xff //¤wÐ·»¡•¡µA¬á ˆa¬w a¶¯aˆa
                      //¶‘»¢·©® ·¶“e ¶áÃ¡Ÿi aÈa…”a.
};

//£¡¡µA ‰Åe–E ˆ‚ÁA
class MIRO {

protected:
        //£¡¡· ¹ÁÃb ÂA¬w”e· ¶áÃ¡ win_x, win_y
        //bw: Ðe §i¢· Í¢
        //ww: ¥b· –A
        int win_x, win_y, bw, ww;

        //¯¡£IA·¡­eÐi ¥b¸÷¥¡Ÿi ¸á¸wÐa“e ¥b»¡•¡
	BYTE simmap[34*17];

        //Ñe¸  a¶¯aˆa ´i‰¡·¶“e ¥b¸÷¥¡Ÿi ¸á¸wÐa“e
        //¥b»¡•¡
	BYTE wallmap[34*17];

        //ÂA”eˆáŸ¡ µe¬e—w·i ¶áÐe ¤wÐ·»¡•¡
	BYTE dirmap[34*17];

public:
        MIRO(); //¬—¬÷¸a
        ~MIRO(); //ÌaŠA¸a

        //£¡¡· Á¡‹¡ˆt(¶áÃ¡, ¥b· Í¢, §i¢· Í¢)·i ¬é¸÷Ða‰¡ ÑÁ¡eµA Îa¯¡
	void setMIRO(int w_x,int w_y, int b_w, int w_w);

        //£¡¡· ˆa¸w¸aŸ¡Ÿi ¬é¸÷Ða“e Ðq®
	void setboder(char *map, int spos, int delta);

        //£¡¡· ¥b»¡•¡Ÿi Á¡‹¡ÑÁ
        //ˆa¸w¸aŸ¡ ·¡¶A· ¥b·e ¡¡Ÿa“e ¥b·a¡ Á¡‹¡ÑÁ
	void initwallmap(char *map);

        //£¡¡· Í©·i ÑÁ¡eµA ‹aaº‘
	void drawpole(void);

        //pos¶áÃ¡µA type Ñw· ¥b·i ÑÁ¡eµA ‹aaº‘
        //type: SOLID_WALL: ­¢·¡ À¶¡»¥ ¥b
		//      EMPTY_WALL: ­¢·¡ §¥ ¥b
	void putwall(int pos, int type);

        //¥b»¡•¡ mapŸi typeÑwÈ· ¥b·a¡ ÑÁ¡eµA ‹iŸ±
	void drawmaze(char *map, int type);

        //¤wÐ·»¡•¡Ÿi ‹aaº“e Ðq®(¬á§ažË¥)
	void _putdirmap(int evencolor, int oddcolor);
        //¤wÐ·»¡•¡Ÿi ‹aaº“e Ðq®
	void putdirmap(void);
        //¥b»¡•¡Ÿi ‹aaº“e Ðq®(¬á§ažË¥)
	void _putwallmap(int evencolor, int oddcolor);
        //¥b»¡•¡Ÿi ‹aaº“e Ðq®
	void putwallmap(void);

        //¥b»¡•¡ Ìa·©·i ·ª´á—i·±(ÑÂ¸w¸a '.MAZ'Ìa·©)
	int loadmaze(char *filename);
};

// a¶¯a Â‰bµA ‰Åe–E ˆ‚ÁA
class MOUSE {

protected:
        int flag; //Ñe¸  a¶¯aˆa Îa¯¡–A´á ·¶·a¡e flag=1
                  //Îa¯¡–A´á ·¶»¡ ´g·a¡e flag=0
        double x, y, dir; // a¶¯a· ¶áÃ¡, ¤wÐ·
                          //·¡“e ‹aœÏ¢¬wµA Îa¯¡–A“e  a¶¯a·
                          //¶áÃ¡(ÑÁ¡e¬w· x, y), ¤wÐ·(0-360•¡)·¡”a.
        double oldx, oldy; //·¡¸å·  a¶¯a· ¶áÃ¡
        int speed; // a¶¯aˆa ¶‘»¢·¡“e ­¢•¡
        int mloc[6]; // a¶¯a· ­A ¢»¡¸ñ· ¹ÁÎa
        char image[(13+7)/8*13*4+6]; // a¶¯aˆa Îa¯¡–I »¡¸ñ·
                                     //¤‰wÑÁ¡e·i ¸á¸wÐi ¥e®

public:
        MOUSE(); //¬—¬÷¸a
        ~MOUSE(); //ÌaŠA¸a

        // a¶¯aŸi Á¡‹¡ ¶áÃ¡¡ ¬é¸÷
	void sethome(int w_x, int w_y, int b_w, int w_w);

        // a¶¯a· ­¢•¡Ÿi ¬é¸÷
	void setspeed(int _speed);

        // a¶¯aŸi dist eÇq dir¤wÐ··a¡ ·¡•·
	void movemouse(double dist);

        // a¶¯a· ¤wÐ··i ÒA¸å
        //ÑÁ¡e¬wµA“e ¥eÑÁ ´ô·q
	void turnmouse(double angle);

        // a¶¯aŸi ÑÁ¡eµA Îa¯¡
	void putmouse(void );

        // a¶¯aŸi ÑÁ¡eµA¬á »¡¶‰¡,  a¶¯a ¶áÃ¡· ¤‰wÑÁ¡e·i ¥¢Š
	void erasemouse(void);

        //dist eÇq· ˆáŸ¡Ÿi ·©¸÷ˆe‰b·a¡  a¶¯aŸi ·¡•·
	void running(double dist);

        //angle eÇq· ˆb•¡Ÿi ·©¸÷ˆe‰b·a¡  a¶¯aŸi ÒA¸å
	void turnning(double angle);
};

void initgr(void);  //‹aœÏ¢ ¡¡—a¡ Á¡‹¡ÑÁ
void closegr(void); //‹aœÏ¢ ¡¡—aŸi ”h·q

