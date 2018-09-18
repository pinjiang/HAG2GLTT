//========================pps params and functions===============
#include <avr/pgmspace.h>
#include <stdio.h>
#include <AsyncDelay.h>
#include "RTClib.h"
// #include <DS1307RTC.h>
// #include <DS3231.h>
#include <Wire.h>

RTC_DS3231 rtcc;

const int rtcTimerIntPin = 3;
volatile bool rtcSet = false;
volatile bool rtcTriggered = false;
unsigned long preMillis;

//=========================light sensor params and functions==============================

static double diffUpEdgeThreshold = 0.5;
static double diffDownEdgeThreshold = -0.5;
static unsigned int slideWindow = 20;      /* 连续改变的次数 */
static double alpha = 1.0 / slideWindow;   /* 滤波器系数 */

volatile int lastAnalogValue = 0;  /* 保存上一个 Analog 输出 */
volatile double avgDiff = 0;               /* 平均的差分 */
//volatile unsigned long startTime;
volatile int currentLvl = 0;                /* 0 as Low aplitude, 1 as high aplitude */
const char *low = "low";
const char *high = "high";

unsigned long timeTmp = 0;
char comm = 'W';

volatile int errTmp = 0;  //统计次数,校准次数目前写死了，为100次
volatile int g2gTmp = 0;  //g2g时延测量次数，可写死，目前已放开

struct nowTime {
  int yy;   //记录电平变化的初始时间
  int mo;
  int dd;
  int hh;
  int mi;
  int sec;
  unsigned long milliSec;
  char *level;
} nt, a, b; //初次改变时间changingtime，即上一个的状态的stoptime,下一个状态的starttime

//==============================interrupt params and functions====================

#define analogPin A0

volatile int AnalogValue;

void getNowTime(struct nowTime &ntt) {
  DateTime now = rtcc.now();
  ntt.yy = now.year();
  ntt.mo = now.month();
  ntt.dd = now.day();
  ntt.hh = now.hour();
  ntt.mi = now.minute();
  ntt.sec = now.second();
  // ntt.milliSec = millis() - preMillis;
}

void displayNowTime(struct nowTime ntt) {
  char isoDateTime[20];
  //Serial.print(ntt.level);
  //snprintf(isoDateTime, sizeof(isoDateTime), ";%04d/%02d/%02d %02d:%02d:%02d.%03d", ntt.yy, ntt.mo, ntt.dd, ntt.hh, ntt.mi, ntt.sec, ntt.milliSec);
  snprintf(isoDateTime, sizeof(isoDateTime), "%02d:%02d:%02d.%03d", ntt.hh, ntt.mi, ntt.sec, ntt.milliSec);
  Serial.println(isoDateTime);
}

void LightSensor(int analogValue) {
  
  int diff = analogValue - lastAnalogValue;

  if ( ( avgDiff > -0.05 && avgDiff < 0.05 ) && diff != 0 ) {         /* 当滑窗平均差分值为0，瞬时差分值不为0，认为是变化开始 */
    // getNowTime(nt);
    nt.milliSec = millis() - preMillis; /* 记录当前时间 */
  } 
  
  avgDiff  = alpha * diff + (1 - alpha) * avgDiff;
  lastAnalogValue = analogValue;

  // Serial.print("avgDiff: ");
  // Serial.println(avgDiff);

  if ( currentLvl == 0 &&  avgDiff > diffUpEdgeThreshold ) {   /* 当前是低电平，滑窗平均差分值超过门限，认为上升沿突变成立 */
    nt.level = low;
    if (comm == 'R' && errTmp < 122) 
    {
      displayNowTime(nt);   /* 确认上一次记录时间为上升沿 */
      errTmp = errTmp + 1;
    }
    else if (comm == 'F')    // && g2gTmp < 1022
    {
      displayNowTime(nt);   /* 确认上一次记录时间为上升沿 */
      // g2gTmp = g2gTmp + 1;
    }
    currentLvl = 1;
  } else if ( currentLvl == 1 && avgDiff < diffDownEdgeThreshold ) {   /* 当前是高电平，滑窗平均差分值低于门限，认为下降沿突变成立 */
    nt.level = high;
    if (comm == 'R' && errTmp < 122) 
    {
      displayNowTime(nt);   /* 确认上一次记录时间为上升沿 */
      errTmp = errTmp + 1;
    }
    else if (comm == 'F')   // && g2gTmp < 1022
    {
      displayNowTime(nt);   /* 确认上一次记录时间为上升沿 */
      //g2gTmp = g2gTmp + 1;
    }
    currentLvl = 0;
  } else {
    delayMicroseconds(1200);  // 处理后必须等待一定时间，再次读取AnalogRead
  }
}

void rtc_interrupt ()
{
  preMillis = millis();
  rtcTriggered = true;
}  // end of rtc_interrupt

//sync RTC
void checkRTCset()
{
  DateTime now = rtcc.now();
  getNowTime(nt);
  displayNowTime(nt);
  //if ((now.hour() == 0 && now.minute() == 0 && now.second() == 0 && now.year() < 2010) || now.year() == 2165)
  //if ((now.month() == 0 && now.day() == 0 && now.year() < 2010) || now.year() == 2165)
  if (now.year() != 2018)
  {
    rtcSet = false;
    Serial.println("*** RTC TIME NOT SET. ***");
    Serial.println();
  } else {
    rtcSet = true;
    //Serial.println("RTC TIME SET.");
    //Serial.println();
  }
}

//==============================setup funtion===================
void setup() {

  // put your setup code here, to run once:
  Serial.begin(115200);
  Wire.begin();
  if (! rtcc.begin()) {
    Serial.println("Couldn't find RTC");
    while (1);
  }

  rtcc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  /*if(rtcc.lostPower()) {
    Serial.println("RTC lost power, lets set the time!");
    rtcc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }*/
  
  checkRTCset();

  rtcc.writeSqwPinMode(DS3231_SquareWave1Hz);
  pinMode (rtcTimerIntPin, INPUT);
  //Serial.println("now, open rtc Interrupt....");
  attachInterrupt (digitalPinToInterrupt (rtcTimerIntPin), rtc_interrupt, RISING);
}

bool adjustThresholdFlag = false;
//============================main loop===============================
void loop() {
  // analogRead(analogPin);

  if (Serial.available() > 0) {
    comm =  Serial.read(); // read the incoming byte:
  }
   
 if ( comm == 'F' || comm == 'R') { //时延测试
    //Serial.println("Start Latency Test");
    if (rtcSet) {
      if (rtcTriggered) {
        rtcTriggered = false;
        getNowTime(nt);
      }
    }
    AnalogValue = analogRead(analogPin);
    LightSensor(AnalogValue);  //计算高低电平起始时间，并保存测量结果
  } else if ( comm == 'A' ) { //手动授时
    //Serial.println(comm);
    if (!rtcSet) {
      Serial.println("now,set RTC time manually......");
      //rtcc.adjust(DateTime(2018, 2, 6, 10, 46, 10));
      rtcc.adjust(DateTime(F(__DATE__), F(__TIME__)));
      checkRTCset();
      Serial.println("RTC time setted manually!!!!");
    }
    comm == 'W';
  } else if ( comm == 'S' ) { //时间清零
    if (rtcSet) {
      Serial.println("now,reset the RTC time......");
      rtcc.adjust(DateTime(2000, 0, 0, 0, 0, 0));
      checkRTCset();
      Serial.println("RTC time resetted!!!!");
    }
    comm == 'W';
  } else if ( comm == 'W' ) {
    // Serial.println("Waiting for Commands");
  } else {
    Serial.print("Unknown Command ");
    Serial.println(comm);
  }
}






