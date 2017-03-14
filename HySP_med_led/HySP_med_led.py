import pyfirmata
import time
import epix_framegrabber
from matplotlib import pylab,pyplot
import numpy


#from HySP_med_led import epix_framegrabber
test_mode = 1

if test_mode == 0:

    try:
        epix_framegrabber.Camera()
        epix_available = True
    except epix_framegrabber.CameraOpenError:
        epix_available = False




    #open the camera
    camera = epix_framegrabber.Camera()

    aa = camera.open(8, [2048, 1088],camera = "PhotonFocus",exposure = 10,frametime = 100.0)

    #camera.set_tap_configuration(2)

    # put the correct settings for camera, correct CLTap, bitdepth

    #create an array like this GOOD_PIX = numpy.zeros((x_size_image,y_size_image,LED))
    fig1 = pylab.figure()

    #for each LED

    #1. take a picture

    #2. if image int < somenumber 
    #if too bright -> while too bright decrease exposure
    #if too dim -> while 

    #3. once you find the right image , save it in GOOD_PIX

    #4. move to next LED




    # setting camera properties

    camera.set_tap_geometry(4)
    camera.set_pixel_clock(82)
    camera.set_pixel_format(10)
    #camera.set_pixel_size(10)
    camera.set_sensor_bit_depth(10)
    camera.set_gain(511)


    exposureTime = 5000        # 20ms, start exposure time for LED #21 (pin 43)              guessing, need to change later


    ledPins = [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43]      # ledTotal = 21, pin 29 dead
    ledOrder = [21, 0, 20, 19, 18, 10, 6, 16, 14, 12, 1, 13, 15, 5, 8, 11, 9, 2, 4, 3, 17]      # order: longest to shortest exposure time



    #Open Arduino with pyfirmata firmware. Remember to load "Firmata standard" to arduino using Arduino IDE
    try:
        board = pyfirmata.ArduinoDue('\\.\COM6')
    except Exception:
        print('error')

    #make sure all pins are down:
    for pin_num in range(0,len(ledPins)):
        board.digital[pin_num].write(0)


    for i in range(19,20):       # (0, 21) 0 to 20          testing with only 19, LED #3
        led = ledPins[ledOrder[i]]
        board.digital[led].write(1) #set pin up

        numGreaterThan = 1000      # fake/bogus number to satisfy the while loop

    #    while ( (numGreaterThan > 39) & (numGreaterThan < 77) ):
        while ( (numGreaterThan > 76) or (numGreaterThan < 40) ):        # want [40,76]
    
    
            f = pyplot.figure()
            ax = f.gca()
            f.show()




            camera.set_exposure(exposureTime)      
            #print(camera.cam.properties['ExposureTimeAbs'])        
    
            bb= camera.start_sequence_capture(1)
            cc = camera.get_image() # this is your picture
            #max = numpy.max(cc)
            #bb = numpy.array(aa)
            image_array = numpy.array(cc)

            ax.imshow(cc)
            f.canvas.draw()   
    
            # print(image_array)
        
            numGreaterThan = ( (image_array > 0) ).sum()  #this line makes sense in matlab, in python it has a different meaning           # image_array > 3964         10-19, >991, 1024       40-76, 	>3964, 4096    
            # correct: 1024x1024 = 1048576 when (image_array<4096)         correct: 0 when (image_array>4096)       
            # image doesn't show true colors?  0 when (image_array>3964)         1025487 when (image_array>0)
            print(numGreaterThan)



            # guessed algorithm for now, need to change later
            if numGreaterThan == 0:     # needed?
                exposureTime = 5        # edit later
            elif ( (numGreaterThan > 76) or (numGreaterThan < 40) ):
                exposureTime *= 1.004*numpy.exp(-0.002803*numGreaterThan)



        board.digital[led].write(0) #set pin down

    camera.close()
    # code outside while loop
    # save exposure time to array
    # save image to array 
# ADD CODE

else:
    # grab the spectra for each LED
    led_spectra = numpy.zeros((24,3648)) #measured spectra
    dark_bkg = numpy.zeros((2,3648)) # position 0 is for 1 sec dark, pos 1 is for 5 sec dark
    wavelength = numpy.zeros((1,3648)) #corresponding wavelengths

    spectra_list = []
    spectra_list.append('Spectra\\365nm.txt')
    spectra_list.append('Spectra\\395nm-1sec.txt')
    spectra_list.append('Spectra\\420nm-1sec.txt')
    spectra_list.append('Spectra\\450mm.txt')
    spectra_list.append('Spectra\\470nm.txt')
    spectra_list.append('Spectra\\500nm.txt')
    spectra_list.append('Spectra\\520nm.txt')
    spectra_list.append('Spectra\\580nm.txt')
    spectra_list.append('Spectra\\635nm.txt')
    spectra_list.append('Spectra\\665nm.txt')
    spectra_list.append('Spectra\\680nm-1sec.txt')
    spectra_list.append('Spectra\\700nm-1sec.txt')
    spectra_list.append('Spectra\\730nm-1sec.txt')
    spectra_list.append('Spectra\\760nm-1sec.txt')
    spectra_list.append('Spectra\\780nm-1sec.txt')
    spectra_list.append('Spectra\\810nm-1sec.txt')
    spectra_list.append('Spectra\\830nm-1sec.txt')
    spectra_list.append('Spectra\\905nm-5sec.txt')
    spectra_list.append('Spectra\\940nm-5sec.txt')
    spectra_list.append('Spectra\\970nm-good.txt')
    spectra_list.append('Spectra\\1050nm-10sec.txt')

    #load dark spectra
    
    temp= numpy.loadtxt('Spectra\\dark.txt')
    dark_bkg[0,:]  = temp[:,1]
    temp = numpy.loadtxt('Spectra\\dark-5sec.txt')
    dark_bkg[1,:] = temp[:,1]

    #load wavelengths
    wavelength[0,:] = temp[:,0]
    f2 = pyplot.figure()
    ax2 = f2.gca()
    f2.show()
    for spec_data in range(0,len(spectra_list)):
        temp = numpy.loadtxt(spectra_list[0])

        led_spectra[spec_data,:] = temp[:,1]- (dark_bkg[0,:])
        ax2.plot(wavelength[0,:],led_spectra[spec_data,:])
        f2.canvas.draw()   


        









#bb = camera.start_sequence_capture(1)
#cc = camera.get_image() # this is your picture
#max = numpy.max(cc)
#bb = numpy.array(aa)


##plt.imshow(cc)

#f = pyplot.figure()
#ax = f.gca()
#f.show()


#ax.imshow(cc)
#f.canvas.draw()
#for i in range(0,3):
    
#    camera.set_exposure(10000*(10*i))    
#    #aa = camera.start_sequence_capture(1)

##    bb= camera.start_sequence_capture(1)
##    cc = camera.get_image() # this is your picture
##    max = numpy.max(cc)
##    ax.imshow(cc)
##    f.canvas.draw()
###    #bb = numpy.array(aa)




    #camera.close()
    #perfect image
    #->
    #GOOD_PIX[:,:,LEDnum] = perfect image
    ##fig1.imshow(cc)
    ##pylab.show()






#try:
#    board = pyfirmata.ArduinoDue('\\.\COM6')
#except Exception:
#    print('error')

#for i in range(22,25):  
    
##    #remember to put PIN down!! only one LED open at the time
#    board.digital[i].write(1)
#    time.sleep(1)
#    board.digital[i].write(0)



    





#"""
#This recipe opens a simple window in PyQt to poll the serial port for 
#data and print it out. Uses threads and a queue.

#DON'T FORGET TO SET SERIALPORT BEFORE RUNNING THIS CODE

#Here is an Arduino Sketch to use:
#    ***********
#void setup() {
#  Serial.begin(115200);
#}
#void loop() {
#  Serial.println("I blinked");
#  delay(1000);
#}
#    ***********
#This recipe depends on PyQt and pySerial. Qt 4 is world class code 
#and I like how it looks. PyQt is not completely open source, 
#but I think PySide is. Tested on Qt4.6 / Win 7 / Duemilanove

#Author: Dirk Swart, Ithaca, NY. 2011-05-20. www.wickeddevice.com

#Based on threads recipe by Jacob Hallen, AB Strakt, Sweden. 2001-10-17
#As adapted by Boudewijn Rempt, Netherlands. 2002-04-15

#PS: This code is provided with no warranty, express or implied. It is 
#meant to demonstrate a concept only, not for actual use. 
#Code is in the public domain.
#"""
#__author__ = 'Dirk Swart, Doudewijn Rempt, Jacob Hallen'

#import sys, time, threading, random, Queue
#from PyQt5 import QtGui, QtCore as qt
#import serial

#SERIALPORT = 'COM6'

#class GuiPart(QtGui.QMainWindow):

#    def __init__(self, queue, endcommand, *args):
#        QtGui.QMainWindow.__init__(self, *args)
#        self.setWindowTitle('Arduino Serial Demo')
#        self.queue = queue
#        # We show the result of the thread in the gui, instead of the console
#        self.editor = QtGui.QTextEdit(self)
#        self.setCentralWidget(self.editor)
#        self.endcommand = endcommand    
        
#    def closeEvent(self, ev):
#        self.endcommand()

#    def processIncoming(self):
#        """
#        Handle all the messages currently in the queue (if any).
#        """
#        while self.queue.qsize():
#            try:
#                msg = self.queue.get(0)
#                # Check contents of message and do what it says
#                # As a test, we simply print it
#                self.editor.insertPlainText(str(msg))
#            except Queue.Empty:
#                pass

#class ThreadedClient:
#    """
#    Launch the main part of the GUI and the worker thread. periodicCall and
#    endApplication could reside in the GUI part, but putting them here
#    means that you have all the thread controls in a single place.
#    """
#    def __init__(self):
#        # Create the queue
#        self.queue = Queue.Queue()

#        # Set up the GUI part
#        self.gui=GuiPart(self.queue, self.endApplication)
#        self.gui.show()

#        # A timer to periodically call periodicCall :-)
#        self.timer = qt.QTimer()
#        qt.QObject.connect(self.timer,
#                           qt.SIGNAL("timeout()"),
#                           self.periodicCall)
#        # Start the timer -- this replaces the initial call to periodicCall
#        self.timer.start(100)

#        # Set up the thread to do asynchronous I/O
#        # More can be made if necessary
#        self.running = 1
#        self.thread1 = threading.Thread(target=self.workerThread1)
#        self.thread1.start()

#    def periodicCall(self):
#        """
#        Check every 100 ms if there is something new in the queue.
#        """
#        self.gui.processIncoming()
#        if not self.running:
#            root.quit()

#    def endApplication(self):
#        self.running = 0

#    def workerThread1(self):
#        """
#        This is where we handle the asynchronous I/O. 
#        Put your stuff here.
#        """
#        while self.running:
#            #This is where we poll the Serial port. 
#            #time.sleep(rand.random() * 0.3)
#            #msg = rand.random()
#            #self.queue.put(msg)
#            ser = serial.Serial(SERIALPORT, 115200)
#            msg = ser.readline();
#            if (msg):
#                self.queue.put(msg)
#            else: pass  
#            ser.close()

##rand = random.Random()
#root = QtGui.QApplication(sys.argv)
#client = ThreadedClient()
#sys.exit(root.exec_())

##import sys
##import glob
##import serial


##def serial_ports():
##    """ Lists serial port names

##        :raises EnvironmentError:
##            On unsupported or unknown platforms
##        :returns:
##            A list of the serial ports available on the system
##    """
##    if sys.platform.startswith('win'):
##        ports = ['COM%s' % (i + 1) for i in range(256)]
##    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
##        # this excludes your current terminal "/dev/tty"
##        ports = glob.glob('/dev/tty[A-Za-z]*')
##    elif sys.platform.startswith('darwin'):
##        ports = glob.glob('/dev/tty.*')
##    else:
##        raise EnvironmentError('Unsupported platform')

##    result = []
##    for port in ports:
##        try:
##            s = serial.Serial(port)
##            s.close()
##            result.append(port)
##        except (OSError, serial.SerialException):
##            pass
##    return result


##if __name__ == '__main__':
##    print(serial_ports())

##def main():

##    app = QtGui.QApplication(sys.argv)
##    ex = captureFrames()
##    app.aboutToQuit.connect(ex.closing_sequence)
##    sys.exit(app.exec_())


##if __name__ == '__main__':
##    main()