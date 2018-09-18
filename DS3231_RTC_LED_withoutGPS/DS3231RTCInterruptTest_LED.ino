#include <Time.h>
#include <Wire.h>
#include "RTClib.h"
//#include <DS3231.h>

RTC_DS3231 rtcc;

const int rtcTimerIntPin = 3;
bool flag = false;
unsigned long preMillis;
const int LED_Pin = 7;
volatile int state = 0;
volatile bool rtcSet = false;


struct nowTime {
  int yy;   //记录电平变化的初始时间
  int mo;
  int dd;
  int hh;
  int mi;
  int sec;
  unsigned long milliSec;
  String level;
} nt;

void getNowTime(struct nowTime &ntt) {
  DateTime now = rtcc.now();
  ntt.yy = now.year();
  ntt.mo = now.month();
  ntt.dd = now.day();
  ntt.hh = now.hour();
  ntt.mi = now.minute();
  ntt.sec = now.second();
  ntt.milliSec = millis() - preMillis;
}

void displayNowTime(struct nowTime ntt) {
  char isoDateTime[30];
  Serial.print(ntt.level);
  snprintf(isoDateTime, sizeof(isoDateTime), ";%04d/%02d/%02d %02d:%02d:%02d.%03dZ", ntt.yy, ntt.mo, ntt.dd, ntt.hh, ntt.mi, ntt.sec, ntt.milliSec);
  //Serial.print("Date/time: ");
  Serial.println(isoDateTime);
}

void LEDControl() {
  if (state == 0) {
    getNowTime(nt);   //get the current time
    nt.level = "high";
    digitalWrite(LED_Pin, HIGH);   // turn the LED on (HIGH is the voltage level)
    displayNowTime(nt);
    state = 1;
    //delay(1000);
  }
  else {
    getNowTime(nt);// wait for a second
    nt.level = "low";
    digitalWrite(LED_Pin, LOW);    // turn the LED off by making the voltage LOW
    displayNowTime(nt);
    state = 0;
    //delay(1000);
  }
}

void checkRTCset()
{
  DateTime now = rtcc.now();
  //if ((now.hour() == 0 && now.minute() == 0 && now.second() == 0 && now.year() < 2010) || now.year() == 2165)
  //if ((now.month() == 0 && now.day() == 0 && now.year() < 2010) || now.year() == 2165)
  if (now.year() != 2018)
  {
    rtcSet = false;
    Serial.println("*** RTC TIME NOT SET. ***");
    Serial.println();
  } else {
    rtcSet = true;
    Serial.println("RTC TIME SET.");
    Serial.println();
  }
}

void rtc_interrupt(void)
{
 // Serial.println("rtc interrupted");
  preMillis = millis();
  flag = true;
}

void setup(void)
{
  Serial.begin(115200);
  while (!Serial); // for Leonardo/Micro/Zero

  if (! rtcc.begin()) {
    Serial.println("Couldn't find RTC");
    while (1);
  }

  if (rtcc.lostPower()) {
    Serial.println("RTC lost power, lets set the time!");
    // following line sets the RTC to the date & time this sketch was compiled
    rtcc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }
  checkRTCset();

 /* if (timeStatus() != timeSet)
    Serial.println("Unable to sync with the RTC");
  else
    Serial.println("RTC has set the system time");*/

  // enable the 1 Hz output
  rtcc.writeSqwPinMode (DS3231_SquareWave1Hz);

  pinMode(LED_Pin, OUTPUT);    // onboard LED
  pinMode(rtcTimerIntPin, INPUT);
  attachInterrupt (digitalPinToInterrupt (rtcTimerIntPin), rtc_interrupt, RISING);
  Serial.println("end of setup()");

  //digitalClockDisplay();
}

void loop(void)
{
  //digitalClockDisplay();
  Serial.println("Unable to sync with the RTC");
  if (flag) {
    LEDControl();
    /*digitalWrite(LED_BUILTIN, HIGH);    // flash the led
      digitalClockDisplay();              // this just prints time to serial port
      delay(500);                         // wait a little bit
      digitalWrite(LED_BUILTIN, LOW);     // turn off led*/
    flag =  false;                      // clear the flag until timer sets it again
  }
}

/*void digitalClockDisplay()
  {
  // do something
  }*/

