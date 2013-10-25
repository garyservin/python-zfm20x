import serial
from commands import *

class ZFM20x(object):
    """A fingerprint reader class"""

    packageSizeDict = [32, 64, 128, 256]
    imgBufferSize = 36864
    chrBufferSize = 512

    def __init__(self, port, baudrate=57600, name=None, address=0xFFFFFFFF, password=0x00000000):
        self.sp = serial.Serial(port, baudrate)
        self.name = name
        if not self.name:
            self.name = port
        self.address = address
        self.password = password
        info = self.getHWinfo()
        self.databaseCount = info['fingerDatabase']
        self.secureLevel = info['secureLevel']
        self.packageSize = info['packageSize']
        self.productType = info['productType']
        self.version = info['version']
        self.manufacturer = info['manufacturer']
        self.sensor = info['sensor']
        self.baudrate = info['baudrate']

    def __str__(self):
        ack, templateCount = self.getTemplateCount()
        return "Fingerprint reader %s on %s\
        \r\nFinger Database: %d\
        \r\nDatabase used: %d\
        \r\nSecure Level: %d\
        \r\nAddress: %s\
        \r\nPackage Size: %d\
        \r\nBaudrate: %d\
        \r\nProduct Type: %s\
        \r\nVersion: %s\
        \r\nManufacturer: %s\
        \r\nSensor: %s\r\n" % (self.name, self.sp.port, self.databaseCount, templateCount, self.secureLevel, hex(self.address), self.packageSizeDict[self.packageSize], self.baudrate*9600, self.productType, self.version, self.manufacturer, self.sensor)

    def bytes_available(self):
        return self.sp.inWaiting()

    def exit(self):
        """Call this to exit cleanly."""
        if hasattr(self, 'sp'):
            self.sp.close()

    def read(self):
        """ Read one byte from the device """
        return ord(self.sp.read())

    def write(self, data):
        """ Write one byte to the device """
        self.sp.write(chr(data & 0xFF))

    def writePacket(self, packetType, packet):
        """ Write a packet to the sensor """
        message = []
        length = len(packet) + 2

        message.append((FINGERPRINT_STARTCODE >> 8) & 0xFF)
        message.append((FINGERPRINT_STARTCODE) & 0xFF)
        message.append((self.address >> 24) & 0xFF)
        message.append((self.address >> 16) & 0xFF)
        message.append((self.address >> 8) & 0xFF)
        message.append((self.address) & 0xFF)
        message.append((packetType) & 0xFF)
        message.append((length >> 8) & 0xFF)
        message.append((length) & 0xFF)

        chksum = message[6] + message[7] + message[8]
        for i in range(length - 2):
            message.append(packet[i] & 0xFF)
            chksum = chksum + packet[i]

        message.append((chksum >> 8) & 0xFF)
        message.append((chksum) & 0xFF)

        for data in message:
            self.write(data)

    def getReply(self):
        """ Get a reply from the sensor """
        reply = []
        # Header (2) + Address (4) + Pkg id (1) + Length (2)
        for _ in range(9):
            reply.append(self.read())

        length = (reply[7] << 8) + reply[8] - 2
        # Data (length bytes)
        for _ in range(length):
            reply.append(self.read())

        # Checksum (2 bytes)
        for _ in range(2):
            reply.append(self.read())

        return reply

    def getPackageSizeBytes(self):
        return self.packageSizeDict[self.packageSize]

    def verifyPassword(self, password):
        packet = [FINGERPRINT_VERIFYPASSWORD]
        for i in range(4):
            packet.append((password >> (3 - i)) & 0xFF)
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK
        else:
            return reply[9]

    def setPassword(self, password):
        """ Set a new password for the current device"""
        packet = [FINGERPRINT_SETPASSWORD]
        for i in range(4):
            packet.append((password >> (8 * (3 - i))) & 0xFF)
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)

        #TODO Test without breaking the module
        reply = self.getReply()
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK
        else:
            return reply[9]

    def setAddress(self, newAddress):
        """ Set a new address for the current device"""
        packet = [FINGERPRINT_SETADDR]
        for i in range(4):
            packet.append((newAddress >> (8 * (3 - i))) & 0xFF)
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        newAddress = (reply[10] << 24) + (reply[11] << 16) + (reply[12] << 8) + reply[13]
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            self.address = newAddress
            return FINGERPRINT_OK, newAddress
        else:
            return reply[9]

    def setSystemParameter(self, parameterNumber, content):
        packet = [FINGERPRINT_SETSYSPARA, parameterNumber, content]
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK
        else:
            return reply[9]

    def readSystemParameters(self):
        """ Read system parameters"""
        packet = [FINGERPRINT_READSYSPARA]
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        sysPara = {'statusRegister':((reply[10] << 8) + reply[11]),
                   'sysIdentifier':((reply[12] << 8) + reply[13]),
                   'fingerLibSize':((reply[14] << 8) + reply[15]),
                   'securityLevel':((reply[16] << 8) + reply[17]),
                   'deviceAddress':hex((reply[18] << 24) + (reply[19] << 16) + (reply[20] << 8) + reply[21]),
                   'dataPacketSize':self.packageSizeDict[(reply[22] << 8) + reply[23]],
                   'baudRate':((reply[24] << 8) + reply[25])*9600}
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK, sysPara
        else:
            return reply[9], {}

    def readContList(self):
        packet = [FINGERPRINT_READCONTLIST]
        pass

    def getTemplateCount(self):
        """ Get the number of templates in flash"""
        packet = [FINGERPRINT_TEMPLATECOUNT]
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        templateCount = (reply[10] << 8) + reply[11]
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK, templateCount
        else:
            return reply[9]

    def getHWinfo(self):
        """ Get Hardware information"""
        data = []
        packet = [FINGERPRINT_GETHWINFO, 0x00]
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()

        for _ in range(4):
            data.append(self.getReply())

        fingerDatabase = (data[0][13] << 8) + data[0][14]
        secureLevel = (data[0][15] << 8) + data[0][16]
        address = hex((data[0][17] << 24) + (data[0][18] << 16) + (data[0][19] << 8) + data[0][20])
        packageSize = ((data[0][21] << 8) + data[0][22])
        baudrate = ((data[0][23] << 8) + data[0][24])
        productType = ''
        version = ''
        manufacturer = ''
        sensor = ''

        for i in range(37,45):
            productType = productType + chr(data[0][i])
        for i in range(45,53):
            version = version + chr(data[0][i])
        for i in range(53,61):
            manufacturer = manufacturer + chr(data[0][i])
        for i in range(61,69):
            sensor = sensor + chr(data[0][i])

        info = {'fingerDatabase':fingerDatabase,
                'secureLevel':secureLevel,
                'address':address,
                'packageSize':packageSize,
                'baudrate':baudrate,
                'productType':productType,
                'version':version,
                'manufacturer':manufacturer,
                'sensor':sensor
                }

        return info

        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK, info
        else:
            return reply[9]

    def getImage(self):
        """ Get finger image and save to ImageBuffer in the module """
        packet = [FINGERPRINT_GETIMAGE]
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK
        else:
            return reply[9]

    def uploadImage(self):
        """ Upload image from ImageBugffer in module to host
        The module sends the image divided in packages of packageSize. By default it
        sends 288 packages of 128 bytes (plus the header for each one)
        """
        packet = [FINGERPRINT_UPIMG]
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            fingerImg = []
            # TODO change static 288 to depend on packageSize
            for _ in range(self.imgBufferSize/self.getPackageSizeBytes()):
                # TODO add a timeout
                fingerImg.append(self.getReply())
            return FINGERPRINT_OK, fingerImg
        else:
            return reply[9]

    def downloadImage(self):
        """ Download image from host to ImageBugffer in module """
        packet = [FINGERPRINT_DOWNIMG]
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK
        else:
            return reply[9]

    def image2Tz(self, bufferID):
        """ Generate a char file from finger image and store it in Charbuffer1/2"""
        packet = [FINGERPRINT_IMAGE2TZ, bufferID]
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK
        else:
            return reply[9]

    def createModel(self):
        """ Create a new model for the finger
        Get two char images stored in charBuffer1 and CharBuffer2,
        generate a model and store it bith in Charbuffer1 and CharBuffer2
        """
        packet = [FINGERPRINT_REGMODEL]
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK
        else:
            return reply[9]

    def uploadChar(self, bufferID):
        """ Upload a char file from bufferId in module to host
        The module sends the char file divided in packages of packageSize. By default it
        sends 4 packages of 128 bytes (plus the header for each one)
        """
        packet = [FINGERPRINT_UPCHAR, bufferID]
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            chrFile = []
            for _ in range(self.charBufferSize/self.getPackageSizeBytes()):
                chrFile.append(self.getReply())
            return FINGERPRINT_OK, chrFile
        else:
            return reply[9]

    def downloadChar(self, bufferID):
        packet = [FINGERPRINT_DOWNCHAR, bufferID]
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK
        else:
            return reply[9]

    def store(self, pageID):
        """ Store a finger model to flash with pageID"""
        packet = [FINGERPRINT_STORE, 0x01]
        for i in range(2):
            packet.append((pageID >> (8 * (1 - i))) & 0xFF)
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK
        else:
            return reply[9]

    def loadChar(self, bufferID, pageID):
        """ Load char file from flash to bufferID"""
        packet = [FINGERPRINT_LOADCHAR, bufferID]
        for i in range(2):
            packet.append((pageID >> (8 * (1 - i))) & 0xFF)
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK
        else:
            return reply[9]

    def deleteChar(self, pageID, countBytes):
        packet = [FINGERPRINT_DELCHAR]
        for i in range(2):
            packet.append((pageID >> (8 * (1 - i))) & 0xFF)
        for i in range(2):
            packet.append((countBytes >> (8 * (1 - i))) & 0xFF)
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK
        else:
            return reply[9]

    def empty(self):
        """ Empty finger ID database"""
        packet = [FINGERPRINT_EMPTY]
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK
        else:
            return reply[9]

    def match(self):
        """ Match two char files stored in CharBuffer1 and CharBuffer2"""
        packet = [FINGERPRINT_MATCH]
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        matchScore = (reply[10] << 8) + reply[11]
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK, matchScore
        else:
            return reply[9]

    def search(self, bufferID, startPage, pageNumber):
        packet = [FINGERPRINT_SEARCH, bufferID]
        for i in range(2):
            packet.append((startPage >> (8 * (1 - i))) & 0xFF)
        for i in range(2):
            packet.append((pageNumber >> (8 * (1 - i))) & 0xFF)
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        pageID = (reply[10] << 8) + reply[11]
        matchScore = (reply[12] << 8) + reply[13]
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK, pageID, matchScore
        else:
            return reply[9]

    def highSpeedSearch(self, bufferID, startPage, pageNumber):
        packet = [FINGERPRINT_SEARCH, bufferID]
        for i in range(2):
            packet.append((startPage >> (8 * (1 - i))) & 0xFF)
        for i in range(2):
            packet.append((pageNumber >> (8 * (1 - i))) & 0xFF)
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        pageID = (reply[10] << 8) + reply[11]
        matchScore = (reply[12] << 8) + reply[13]
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK, pageID, matchScore
        else:
            return reply[9], 0, 0

    def getRandomCode(self):
        """ Get Random Code from device"""
        packet = [FINGERPRINT_GETRANDOMCODE]
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        randomNumber = (reply[10] << 24) + (reply[11] << 16) + (reply[12] << 8) + reply[13]
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK, randomNumber
        else:
            return reply[9], -1

    def writeNotepad(self, pageNumber, data):
        packet = [FINGERPRINT_WRITENOTE]
        for byte in data:
            packet.append(byte)
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK
        else:
            return reply[9]

    def readNotepad(self, pageNumber):
        packet = [FINGERPRINT_READNOTE, pageNumber]
        self.writePacket(FINGERPRINT_COMMANDPACKET, packet)
        reply = self.getReply()
        data = []
        for i in range(10, 42):
            data.append(reply[i])
        if reply[6] == FINGERPRINT_ACKPACKET and reply[9] == FINGERPRINT_OK:
            return FINGERPRINT_OK, data
        else:
            return reply[9]

    def intToHexList(self, intList):
        response = []
        for data in intList:
            response.append(hex(data))
        return response

    ### High level libraries
    def searchFinger(self):
        """ Wrapper function that gets a finger image and search for it in the database"""
        # First we get the image
        #ack = self.getImage()
        #if ack != FINGERPRINT_OK:
        #    return ack
        # Convert image to char
        ack = self.image2Tz(0)
        if ack != FINGERPRINT_OK:
            return ack
        # Start a highspeed search
        ack, pageID, matchScore = self.highSpeedSearch(0, 0x00, 0x03E9)
        if ack != FINGERPRINT_OK:
            return ack
        return pageID, matchScore

    def fingerPresent(self):
        ack = self.getImage()
        if ack != FINGERPRINT_OK:
            return False
        return True

    def fingerFound(self):
        ack = self.image2Tz(0)
        if ack != FINGERPRINT_OK:
            return ack
        # Start a highspeed search
        ack, pageID, matchScore = self.highSpeedSearch(0, 0x00, 0x03E9)
        if ack != FINGERPRINT_OK:
            return -1
        return pageID

    def fingerEnroll(self, fingerID):
        """
        Enroll a new finger with id = fingerID
        ### Process to enroll a finger
        0- select an id
        1- getImage
        2- image2Tz(buffer1)
        3- getImage (until no finger present)
        4- getImage (again same finger)
        5- image2Tz(buffer2)
        6- createModel
        7- storeModel
        """

        print 'Enrolling..'

        print 'Waiting for valid finger...'
        while not self.fingerPresent():
            # TODO add a timeout
            continue

        # 2- image2Tz(buffer1)
        if self.image2Tz(1) != FINGERPRINT_OK:
            return -1

        # 3- getImage (until no finger present)
        print 'Please remove your finger...'
        while self.fingerPresent():
            # TODO add a timeout
            continue

        # 4- getImage (again same finger)
        print 'Please put the same finger...'
        while not self.fingerPresent():
            # TODO add a timeout
            continue

        # 5- image2Tz(buffer2)
        if self.image2Tz(2) != FINGERPRINT_OK:
            return -2

        # 6- createModel
        print 'Creating a model...'
        if self.createModel() != FINGERPRINT_OK:
            # TODO add a timeout
            return -3

        # 7- storeModel
        print 'Storing model...'
        if self.store(fingerID) != FINGERPRINT_OK:
            return -4

        return fingerID
