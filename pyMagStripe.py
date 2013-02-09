## pyMagStripe - a python Magnetic Card Reader/Writer Program.
## v 0.1
## Sean Colyer < sean @ colyer . name >
## Copyright 2010 Sean Colyer.
##This program is free software; you can redistribute it and/or
##modify it under the terms of the GNU General Public License
##as published by the Free Software Foundation; either version 2
##of the License, or (at your option) any later version.
##
##This program is distributed in the hope that it will be useful,
##but WITHOUT ANY WARRANTY; without even the implied warranty of
##MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##GNU General Public License for more details.
##
##You should have received a copy of the GNU General Public License
##along with this program; if not, write to the Free Software
##Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
##
## Outline:
## pyMagStripe.py -- provides the methods to interact with the serial magnetic card reader/writer
## pyMagStripGui.py  -- provides a wxPython front end


import serial, datetime

ESCAPE = 0X1B
RESET = 0x61
READ = 0x72             #[DATA] <ESC> [STATUS]
WRITE = 0X77            # <ESC> [STATUS]
WRITE_BLOCK = 0x73
WRITE_END = 0x3F
WRITE_END_ESC = 0x1C
COMM_TEST = 0x65        # <ESC> Y [ESC][0X79]
COMM_SUCCESS = 0x79
ALL_LED_OFF = 0x81
ALL_LED_ON = 0x82
GREEN_LED_ON = 0x83
YELLOW_LED_ON = 0x84
RED_LED_ON = 0x85
SENSOR_TEST = 0x86      #<ESC> 0 (<ESC> 30 == OK)
RAM_TEST = 0x87         #<ESC> 0 (<ESC> 30 == OK), A (<ESC> 41 == FAIL)
SET_LEADING_ZERO = 0x7A #ADD WITH 2 ARGS -- 00 THROUGH FF FOR TRACKS 1+3;2
                        #RESPONSE: <ESC> 0 (<ESC> 30 == OK), A (<ESC> 41 == FAIL)
CHECK_LEADING_ZERO = 0x6C # <ESC> 2 ARGS -- 00 THROUGH FF FOR TRACKS 1+3;2
ERASE_CARD = 0x63       #ADD SELECT BYTE: LAST 3 BITS LAST BIT == TRACK 1;  1-HOT Encoding of last 3 bits
                        #RESPONSE: <ESC> 0 (<ESC> 30 == OK), A (<ESC> 41 == FAIL)
ERASE_ALL_TRACKS = 0x07
SELECT_BPI = 0x62       #TRACK 2 ONLY
READ_RAW = 0X6D         #[RAWDATA]<ESC>[STATUS]
WRITE_RAW = 0X6E        #ADD [RAWDATA]
                        #RESPONSE: <ESC>[STATUS]
GET_DEV_MODEL = 0x74    #<ESC>[MODEL] S
GET_FIRMWARE = 0X76     #<ESC>[VERSION]
SET_BPC = 0x6F          #SETS BITS PER CHARACTER
                        #ADD [5-8][5-8][5-8]
                        #RESPONSE: <ESC>0X30[][][]
SET_HI_CO = 0x78        #<ESC>0
SET_LOW_CO = 0X79       #<ESC>0
GET_CO_STATUS = 0x64    #<ESC>H/L

class pyMagStripe():
    def __init__(self):
        self.serial = None
        return

    def scan(self):
        """scan for available ports. return a list of tuples (num, name)"""
        available = []
        for i in range(256):
            try:
                s = serial.Serial(i)
                available.append( (i, s.portstr))
                s.close()   # explicit close 'cause of delayed GC in java
            except serial.SerialException:
                pass
        return available

    def connect(self,port,timeout = None):
        self.openSerial(port,timeout)
        try:
            if self.serial.isOpen():
                if self.serial is not None:
                    if self.initializeReader() is not -1:
                        return True
            self.closeSerial()
            return False
        except:
            self.closeSerial()
            return False

    def openSerial(self,port,timeout):
        try:
            self.serial = serial.Serial(port,timeout=timeout,writeTimeout=timeout)
            print "Opened on port",port,self.serial.portstr
            return
        except:
            self.serial = None
            print "Can't open COM port ",port
            return -1
    def closeSerial(self):
        try:
            if self.serial != None:
                self.serial.write(chr(ESCAPE)+chr(RESET))
                self.serial.close()
                self.serial = None
        except:
            self.serial = None
            return
    def initializeReader(self):
        try:
            self.serial.write(chr(ESCAPE)+chr(RESET))
            self.serial.write(chr(ESCAPE)+chr(COMM_TEST))
            if hex(ord(self.serial.read(2)[1])) == hex(COMM_SUCCESS):
                print "Successful communication test"
            else:
                print "Unsuccessful communication test. Closing serial conection."
                self.closeSerial()
                return -1
            self.serial.write(chr(ESCAPE)+chr(RESET))
        except Exception as e:
            print e
            print "Unsuccessful communication test. Closing serial conection."
            self.closeSerial()
            return -1

    def read(self):
        try:
            self.serial.write(chr(ESCAPE) + chr(RESET))
            self.serial.write(chr(ESCAPE)+chr(READ))
            char = self.serial.read(1)
            prev = char
            string = ""
            attempts = 100
            while (ord(prev) != ESCAPE or ord(char) < 0x30 or ord(char) > 0x3F):
                string += char
                prev = char
                char = self.serial.read(1)
                attempts -= 1
            self.serial.write(chr(ESCAPE) + chr(RESET))

            track1pos = string.find( chr(0x1) )
            track2pos = string.find (chr (0x2) )
            track3pos = string.find (chr (0x3) )
            track1 = string[track1pos:track2pos]
            track2 = string[track2pos:track3pos]
            track3 = string[track3pos:-1]
            if track1.find( chr(WRITE_END)) == -1:
                track1 = ""
            else:
                track1 = track1[2:track1.find(chr(WRITE_END))]
            if track2.find( chr(WRITE_END)) == -1:
                track2 = ""
            else:
                track2 = track2[2:track2.find(chr(WRITE_END))]
            if track3.find( chr(WRITE_END)+chr(WRITE_END)) == -1:
                track3 = ""
            else:
                track3 = track3[2:track3.find(chr(WRITE_END))]
            return track1,track2,track3

        except Exception as e:
            print e
            print "Exception raised while reading from the card. Closing serial connection."
            self.closeSerial()
            return -1,-1,-1

    def write(self, track1, track2, track3):
        try:
            testData = chr(ESCAPE) + chr(0x01)
            if track1 != None:
                testData = testData + track1
            testData = testData + chr(ESCAPE) + chr(0x02)
            if track2 != None:
                testData = testData + track2
            testData = testData + chr(ESCAPE) + chr(0x03)
            if track3 != None:
                testData = testData + track3
            
            self.serial.write(chr(ESCAPE) + chr(RESET))
            self.serial.write(chr(ESCAPE) + chr(WRITE))
            self.serial.write(chr(ESCAPE) + chr(WRITE_BLOCK))
            self.serial.write(testData)
            self.serial.write(chr(WRITE_END) + chr(WRITE_END_ESC))
            self.serial.read(1)
            status = self.serial.read(1)
            self.serial.write(chr(ESCAPE) + chr(RESET))
        except Exception as e:
            print e
            print "Exception raised while writing to the card. Closing Serial connection."
            self.closeSerial()
            return -1

    def erase(self):
        try:
            self.serial.write(chr(ESCAPE) + chr(RESET))
            self.serial.write(chr(ESCAPE) + chr(ERASE_CARD) + chr(ERASE_ALL_TRACKS))
            self.serial.read(1)
            return self.serial.read(1)
        except Exception as e:
            print e
            print "Exception raised while erasing"
            self.closeSerial(self.serial)
            return -1
            
    def writeToFile(self,fileName,result):
        results = open(fileName,'a')
        results.write(str(datetime.datetime.now()))
        results.write('\n')
        results.write(result)
        results.write('\n\n')
        results.close()

if __name__ == '__main__':
    print "pyMagStripe"
    self = pyMagStripe()
    if self.connect(self.scan()[-1][1],10):
        track1, track2, track3 = self.read()
        self.write(track1,track2,track3)
        self.writeToFile('results', track1 + " " + track2 + " " + track3)
    self.closeSerial()

