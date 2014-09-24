import serial
import time
import json, urllib2
from datetime import datetime, timedelta
import os
from subprocess import check_output

state = 0
ready = True
messageNumber = 0
redAlertActive = False
oldMessage = ""
oldStatus = False

display = serial.Serial("/dev/ttyUSB1", 9600)

def updateMessages():
    global messages
    global messageNumber
    global oldMessage
    global oldStatus

    with open("messages.txt") as f:
        try:
            messages = f.readlines()
            messages = [m.strip() for m in messages]
            h = urllib2.urlopen("http://57north.co/spaceapi")
            spaceapi = json.load(h)
            if spaceapi['state']['open'] != oldStatus or spaceapi['state']['message'] != oldMessage:
                print "'%s'" % spaceapi['state']['message']
                print "'%s'" % oldMessage
                os.system('espeak "%s %s the space with the message %s"' % (spaceapi['state']['trigger_person'], "opened" if spaceapi['state']['open'] else "closed", spaceapi['state']['message']))
                oldMessage = spaceapi['state']['message']
                oldStatus = spaceapi['state']['open']
            messages.append("I" + check_output(["/usr/bin/mpc","current","-f","%artist% - %title%","-h","10.0.100.7"])[:-1])
            messages.append("E%s" % ("OPEN" if spaceapi['state']['open'] else "CLOSED",))
            messages.append("I" + spaceapi['state']['message'])
#            messages.append("CThe temperature is %s <U29>" % (spaceapi['sensors']['temperature'][0]['value'],))
#            messages.append("EThe humidity is %s %%" % (spaceapi['sensors']['humidity'][0]['value'],))
            if messageNumber >= len(messages):
                messageNumber = 0
            return True
        except KeyboardInterrupt:
            messages = ["Perror"]
            return False
    return False

def redAlert():
    return "<ID01><L1><PA><FA><MR><WC><FA><CL>  RED  ALERT  77<E>"

def buildCommand(message):
    if len(message) < 2:
        message = "Pmissing"
    colour = message[0]
    message = message[1:]
    pcmd = "<BE>05<E><ID01><L1><PA><FE><MA><WC><FC><C%s>%s<E><ID01><BF>06" % (colour, message)
    check = 0;
    for i in range(0, len(pcmd)):
        check = check ^ ord(pcmd[i])
    print "checksum on " + repr(pcmd)
    cmd = "<ID01><L1><PA><FE><MA><WC><FC><C%s>%s%s<E>" % (colour, message, ("%02x" % (check)).upper())
    print "command sent " + repr(cmd)
    return cmd

def updateDisplay():
    global ready
    global messageNumber
    global state
    global messages
    global redAlertActive

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
            if os.path.exists('/home/ormiret/redalert.txt'):
                display.write(redAlert())
            else:
                display.write(buildCommand(messages[messageNumber]))
            ready = False
        elif state == 2:
            display.write("<ID01><BF>06<E>")
            if os.path.exists('/home/ormiret/redalert.txt'):
                os.system('cvlc /home/ormiret/thing.mp4 &')
                while os.path.exists('/home/ormiret/redalert.txt'):
                    pass
                os.system('killall vlc')
            ready = False
        elif state == 3:
            print "%d: %s - updated" % (messageNumber, messages[messageNumber])
            time.sleep((1325.0 + (len(messages[messageNumber]) * 90.0)) / 900.0)
            messageNumber += 1
            ready = True
            if messageNumber >= len(messages):
                messageNumber = 0
                updateMessages()
            state = 0

if __name__ == "__main__":
    running = True
    updateMessages()
    while running:
        updateDisplay()

