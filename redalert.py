import serial
import time
import json, urllib2
from datetime import datetime

state = 0
ready = True
messageNumber = 0

display = serial.Serial("/dev/ttyUSB1", 9600)

def updateMessages():
    global messages
    global messageNumber

    messages = ['L  RED  ALERT  ']

def buildCommand(message):
    colour = message[0]
    message = message[1:]
    pcmd = "<BE>05<E><ID01><L1><PA><FA><MR><WC><FA><C%s>%s<E><ID01><BF>06" % (colour, message)
    check = 0;
    for i in range(0, len(pcmd)):
        check = check ^ ord(pcmd[i])
    print pcmd
    cmd = "<ID01><L1><PA><FA><MR><WC><FA><C%s>%s%s<E>" % (colour, message, ("%02x" % (check)).upper())
    print cmd
    return cmd

def updateDisplay():
    global ready
    global messageNumber
    global state
    global messages

    time.sleep(0.2)

    if display.inWaiting() > 2:
        serialData = display.read(display.inWaiting())

        if serialData == "ACK":
            state += 1
            ready = True
        else:
            state = 0
            ready = True
            print "Something didn't synchronise, hang on..."
            time.sleep(1.0)
            display.read(display.inWaiting()) #discard

        print serialData

    if ready:
        if state == 0:
            display.write("<ID01><BE>05<E>")
            ready = False
        elif state == 1:
            display.write(buildCommand(messages[messageNumber]))
            ready = False
        elif state == 2:
            display.write("<ID01><BF>06<E>")
            ready = False
        elif state == 3:
            print "%d: %s - updated" % (messageNumber, messages[messageNumber])
            time.sleep((1325.0 + (len(messages[messageNumber]) * 90.0)) / 900.0)
            messageNumber += 1
            ready = True
            if messageNumber >= len(messages):
                messageNumber = 0
            state = 0

if __name__ == "__main__":
    running = True
    updateMessages()
    while running:
        updateDisplay()

