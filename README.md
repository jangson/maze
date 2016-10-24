# Micro Mouse Simulator with python

2012년 쯤 지인의 추천으로 일본 Micro Mouse 동영상을 보고, 대학 시절 만들었던 마이크로 마우스가 생각나서 Python 언어로 제작한 Micro Mouse Simulator 프로그램이다. 두 바퀴 이동체의 방정식을 사용해서 물리적 이동과 시간 계산을 하고, 실제로 물리좌표에 그리는 방식을 사용하였다. wxPython FloatCanvas(http://wiki.wxpython.org/FloatCanvas) 모듈을 사용하여 floating point 좌표계를 사용하여 정밀하게 그리려다 보니, FloatCanvas 모듈의 드로잉 속도가 너무 느려서 Override 하여 조금 수정하여 사용하였다. 이로 인해 드로잉 속도는 빨라졌으나 확대 축소, 화면 이동, 드로잉 캔버스 이동 등에는 화면이 깨지는 현상이 발생할 수 있다. 독자적인 미로 파일 포멧을 만들고, 16x16 기본 크기와 32x32 half 미로를 지원하고, 미로 편집/저장을 지원한다.

* YouTube
  * [16x16 Maze Video] (https://www.youtube.com/watch?v=iUsBkwjv6jI)
  * [32x32 Maze Video] (https://www.youtube.com/watch?v=m84Ez6tAGA0)
* License
  * [GNU GPLv3]: http://www.gnu.org/licenses/gpl.html
