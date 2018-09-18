//========================pps params and functions===============

#include <avr/pgmspace.h>
#include <stdio.h>
#include <GNSS_Clock.h>
#include <AsyncDelay.h>
#include <TinyGPS++.h>
#include <SoftwareSerial.h>
#include <Time.h>

#include "RTClib.h"
//#include <DS1307RTC.h>
#include <Wire.h>

RTC_DS3231 rtcc;
TinyGPSPlus gps;

#define DS1307_I2C_ADDRESS 0x68
#define DS3231_ADDRESS  0x68
const int rtcTimerIntPin = 3;

static const int RXPin = 10, TXPin = 11;
SoftwareSerial gnss = SoftwareSerial(RXPin, TXPin); // Refer to serial devices logically

const int ppsPin = 2;
const int LED_Pin = 7;
char buffer[85];
volatile bool ppsTriggered = false;
volatile bool ppsInterrupt = false;
volatile bool rtcTriggered = false;
volatile bool rtcInterrupt = false;
volatile bool rtcSet = false;
unsigned long preMillis;
volatile int state = 0;

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

/**********************************************************************************
    Callback for GPS PPS Interrrupt

 ********************************************************************************** */
void ppsCallback(const GNSS_Clock __attribute__((unused)) &clock) {
  ppsTriggered = true;
}

/***********************************************************************************


 ********************************************************************************** */
void gnssHardwareReset() {
  Serial.write("gnssHardwareReset()");
  // Empty input buffer
  while (gnss.available())
    gnss.read();

  AsyncDelay timeout;
  timeout.start(10000, AsyncDelay::MILLIS);
  while (!timeout.isExpired()) {
    while (gnss.available()) {
      char c = gnss.read();
      if (gnss_clock.process(c))
        return;
    }
  }
}

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

void sqw() {
  Wire.beginTransmission(DS3231_ADDRESS);
  //Wire.write(0x07);
  Wire.write(0x0E);
  Wire.write(0x10);
  Wire.endTransmission();
}

void sqwOff() {
  Wire.beginTransmission(DS1307_I2C_ADDRESS);
  Wire.write(0x0E);
  Wire.write(0x00);
  Wire.endTransmission();
}

void rtc_interrupt ()
{
  preMillis = millis();
  rtcTriggered = true;
  //Serial.println("rtc Triggered");
}  // end of rtc_interrupt

//sync RTC
void checkRTCset()
{
  DateTime now = rtcc.now();
  //if ((now.hour() == 0 && now.minute() == 0 && now.second() == 0 && now.year() < 2010) || now.year() == 2165)
  if ( now.year() != 2018)
  {
    Serial.println("*** RTC TIME NOT SET. ***");
    Serial.println();
  } else {
    rtcSet = true;
    Serial.println("RTC TIME SET.");
    Serial.println();
  }
}

void setRTCfromGPS()
{
  Serial.println("Setting RTC from GPS");
  Serial.println();
  if (gps.date.isValid() && gps.time.isValid())
  {
    //rtcc.adjust(DateTime(tm.tm_year, tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min, tm.tm_sec));
    rtcc.adjust(DateTime(gps.date.year(), gps.date.month(), gps.date.day(), gps.time.hour() + 8, gps.time.minute(), gps.time.second()));
    Serial.println("RTC set from GPS");
  } else {
    Serial.println("No GPS fix yet. Can't set RTC yet.");
  }
}

//====================LED============
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

//==============================setup funtion===================
void setup() {

  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(LED_Pin, OUTPUT);
  gnss.begin(9600);
  delay(50);
  Wire.begin();
  if (! rtcc.begin()) {
    Serial.println("Couldn't find RTC");
    while (1);
  }

  if (rtcc.lostPower()) {
    Serial.println("RTC lost power, lets set the time!");
    // following line sets the RTC to the date & time this sketch was compiled
    rtcc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    // This line sets the RTC with an explicit date & time, for example to set
    // January 21, 2014 at 3am you would call:
    // rtc.adjust(DateTime(2014, 1, 21, 3, 0, 0));
  }

  /*if (! rtcc.isrunning()) {
    Serial.println("RTC is NOT running!");
    }*/
  checkRTCset();
  //setSyncProvider(rtcc.get);   // the function to get the time from the RTC
  /*if (timeStatus() != timeSet) {
    Serial.println("Unable to sync with the RTC");
    } else {
    Serial.println("RTC has set the system time");
    }*/
  sqw();
  pinMode (rtcTimerIntPin, INPUT);
  Serial.println("rtc set done...");

  Serial.println("Resetting GNSS module ...");
  gnssHardwareReset();
  Serial.println("... done");

  // Compatibility mode off
  MicroNMEA::sendSentence(gnss, "$PNVGNME,2,7,1");

  // Clear the list of messages which are sent.
  MicroNMEA::sendSentence(gnss, "$PORZB");

  // Send RMC and GGA messages.
  MicroNMEA::sendSentence(gnss, "$PORZB,RMC,1,GGA,1");

  pinMode(ppsPin, INPUT);
  gnss_clock.begin(buffer, sizeof(buffer), ppsPin);
  gnss_clock.set1ppsCallback(ppsCallback);
  ppsInterrupt = true;
  Serial.println("end of setup()");
}


//============================main loop===============================
void loop() {

  //Serial.println(ppsTriggered);
  if (rtcSet) {
    if (ppsInterrupt) {
      gnss_clock.set1ppsCallback(NULL);
      ppsInterrupt = false;
    } else if (!rtcInterrupt && !ppsTriggered) {
      Serial.println("rtc interrupt opened....");
      attachInterrupt (digitalPinToInterrupt (rtcTimerIntPin), rtc_interrupt, RISING);
      rtcInterrupt = true;
    }
  } else {
    while (!ppsTriggered && gnss.available() > 0) {
      gps.encode(gnss.read());
    }
  }

  if (rtcTriggered) {
    rtcTriggered = false;
    LEDControl();
  }

  if (ppsTriggered) {  //pps中断已触发
    ppsTriggered = false;
    //Serial.println("ppsTriggered");
    if (! rtcSet) {
      setRTCfromGPS();
      checkRTCset();
    }
  }
}


