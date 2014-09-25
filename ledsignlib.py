import serial
from time import sleep
from Queue import Queue

display = serial.Serial("/dev/ttyUSB1", 9600)

def buildPacketHeader(payload, id = 0x01):
    packet = "<ID%02x>" % id
    packet += payload
    
    checksum = 0
    for byte in (payload):
        checksum ^= ord(byte)
    
    packet += ("%02x" % checksum).upper()
    # terminator
    packet += "<E>"
    
    return packet

def pageContentPayload(message, line = 1, page = 'A', lead = 'A', display = 'A', wait = 'F', lag = 'A'):
    payload = "<L%s><P%s><F%s><M%s><W%s><F%s>%s" % (line, page, lead, display, wait, lag, message)
    return payload

def graphicBlockPayload(data, page = 'A', block = 1):
    payload = "<G%s%s>%s" % (page, block, data)
    return payload

blockWidth = 32
blockHeight = 8
numUnits = 4
unitWidth = 8
pixelsPerByte = 4
bytes = (blockWidth * blockHeight) / pixelsPerByte

packetQueue = Queue()

def send(packet):
    global display, packetQueue
    
    while not packetQueue.empty():
        display.write(packetQueue.get())
    
    packet = buildPacketHeader(packet)
    print(repr(packet) + " queued")
    packetQueue.put(packet)


def run():
    while True:
        sleep(0.2)
        if display.inWaiting():
            msg = display.read(display.inWaiting())
            if msg == 'ACK':
                display.write(packetQueue.get())
            else:
                print "Got a %s" % msg
