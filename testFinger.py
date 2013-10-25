from pyzfm20x import *
from hextobmp import *

def removeHeader(lista):
    newlist = []
    for row in lista:
        newlist.append(row[9:-2])
    return newlist

myAddress = 0xFFFFFFFF
myPassword = 0x00000000

notepadData = []
for i in range(32):
    notepadData.append(i)

def verifyPassword():
    print 'Verify Password',
    print 'ACK=%d' % board.verifyPassword(myPassword)

def setAddress():
    print 'Set new address',
    print 'ACK=%d, NewAddress=%d' % board.setAddress(0x12345678)

def getHWinfo():
    print 'Get HW info',
    ack, data = board.getHWinfo()
    print 'ACK=%d, Data=' % ack
    print data

def setSystemParameter(parameterNumber, data):
    print 'Set System Parameter',
    print 'ACK=%d' % board.setSystemParameter(parameterNumber, data)

def readSystemParameters():
    print 'Read System Parameters',
    ack, data = board.readSystemParameters()
    print 'ACK=%d, Data=' % ack
    print data

def getTemplateCount():
    print 'Get the number of templates stored in flash',
    print 'ACK=%d, Count=%d' % board.getTemplateCount()

def getImage():
    print 'Collect finger image',
    print 'ACK=%d' % board.getImage()

def uploadImage():
    getImage()
    print 'Upload finger image',
    ack, fingerImg = board.uploadImage()
    print 'ACK=%d' % ack
    removed =  removeHeader(fingerImg)
    print 'Finger image stored as ' + hextobmp.hexToBMP(removed, 'finger1')

def downloadImage():
    print 'Download finger image',

def generateChar(bufferID):
    print 'Generate char file from image',
    print 'ACK=%d' % board.image2Tz(bufferID)

def createModel():
    getImage()
    generateChar(1)
    getImage()
    generateChar(2)

    print 'Create Model template',
    print 'ACK=%d' % board.createModel()

def uploadChar():
    print 'Upload char template',
    ack, chrFile = board.uploadChar(1)
    print 'ACK=%d' % ack
    print chrFile

def downloadChar():
    print 'Download char template',

def storeTemplate():
    print 'Store finger template',
    ack, count = board.getTemplateCount()
    print 'ACK=%d' % board.store(count)

def loadChar():
    print 'Read finger template',
    print 'ACK=%d' % board.loadChar(1, 1)

def deleteFinger(fingerID, count):
    print 'Delete finger',
    print 'ACK=%d' % board.deleteChar(fingerID, count)
    getTemplateCount()

def empty():
    print 'Empty finger library',
    print 'ACK=%d' % board.empty()

def matchFinger():
    print 'Match finger',

def searchFinger():
    print 'Search finger library',
    print 'ACK=%d, PageID=%d, MatchScore=%d' % board.search(0,0,0)
    print board.search(1,0,0)

def getRandomCode():
    print 'Get Random code',
    print 'ACK=%d, Random=%d' % board.getRandomCode()

def writeNotepad():
    print 'Write Notepad',
    print 'ACK=%d' % board.writeNotepad(0, notepadData)

def readNotepad():
    print 'Read Notepad',
    ack, data = board.readNotepad(0)
    print 'ACK=%d\r\nData=' % ack
    print data

def fingerPresentTest():
    while not board.fingerPresent():
        continue
    print 'Finger detected'


def searchFingerTest():
    response = board.searchFinger()
    print response

def enrollTest():
    ack, count = board.getTemplateCount()
    print board.fingerEnroll(count)

    # FingerPresent test
    while not board.fingerPresent():
        continue
    print 'Finger detected'

    # Process to search for a fingerprint
    response = board.searchFinger()
    print response

board = pyzfm20x.ZFM20x('/dev/ttyACM0', baudrate=115200, address=myAddress, password=myPassword)
print board
verifyPassword()
uploadImage()
board.exit()
