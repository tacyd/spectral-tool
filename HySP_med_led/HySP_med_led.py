import pyfirmata
import time
import epix_framegrabber
from matplotlib import pylab,pyplot
import numpy
import tifffile as TiffFile
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QFormLayout, QVBoxLayout,QFileDialog
from pandas import DataFrame
import sys
from os import path as ospath
from time import sleep

#build a QApplication for opening windows
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    
    parent_QWidget = QWidget()
#from HySP_med_led import epix_framegrabber
test_mode =0

if test_mode == 0:

    try:
        epix_framegrabber.Camera()
        epix_available = True
    except epix_framegrabber.CameraOpenError:
        epix_available = False




    #open the camera
    camera = epix_framegrabber.Camera()

    aa = camera.open(10, [2048, 1088],camera = "PhotonFocus",exposure = 10,frametime = 100.0)

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
    pixel_bits = 10
    camera.set_tap_geometry(4)
    camera.set_pixel_clock(82)
    camera.set_pixel_format(pixel_bits)
    #camera.set_pixel_size(10)
    camera.set_sensor_bit_depth(pixel_bits)
    camera.set_gain(511)


    exposureTime = 20000    #minimum 11000    # 20ms, start exposure time for LED #21 (pin 43)              guessing, need to change later


    #ledPins = [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43]      # ledTotal = 21, pin 29 dead
    ledPins = [22, 23, 24, 25, 26, 27, 28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43]      # ledTotal = 21, pin 29 dead
    ledOrder = [21, 0, 20, 19, 18, 10, 6, 16, 14, 12, 1, 13, 15, 5, 8, 11, 9, 2, 4, 3, 17]      # order: longest to shortest exposure time

    

    #Open Arduino with pyfirmata firmware. Remember to load "Firmata standard" to arduino using Arduino IDE
    try:
        board = pyfirmata.ArduinoDue('\\.\COM6')
    except Exception:
        print('error')
    print('Initializing Arduino')
    #make sure all pins are down:
    for pin_num in range(0,21):
        board.digital[ledPins[pin_num]].write(0)


    #initialize final image array
    final_hyperspectral_array = numpy.zeros((21,1088,2048))
    #final_hyperspectral_array = numpy.zeros((21,1024,1024))
    #initialize final exposure array
    final_exposure_time_array = numpy.zeros((21,1))
    show_images = 2
    print('Running Acquisition')
    if show_images==1 or show_images==2:
        #will use blit to make plotting faster
        fig, ax = pyplot.subplots(1, 1)
        #f = pyplot.figure()
        ax.set_aspect('equal')
        ax.hold(True)
        pyplot.show(False)
        pyplot.draw()
        #background = fig.canvas.copy_from_bbox(ax.bbox)
        first_image = 0
    for i in range(0,len(ledPins)):       # (0, 21) 0 to 20          testing with only 19, LED #3
        #led = ledPins[ledOrder[i]]
        led = ledPins[i]
        board.digital[led].write(1) #set pin up
        print('Led',i,'-Pin-',led)
        numGreaterThan = 1000      # fake/bogus number to satisfy the while loop

        threshold_value = .97* 2**16 #this eventually is converted to 16 bits by epix_framegrabber.camera.get_image()
    #    while ( (numGreaterThan > 39) & (numGreaterThan < 77) ):
        #while ( (numGreaterThan > 76) or (numGreaterThan < 40) ):        # want [40,76]
        
            #f.show()
        while ( numGreaterThan > 20 or numGreaterThan == 0):

            camera.set_exposure(exposureTime)      
            #print(camera.cam.properties['ExposureTimeAbs'])        
    
            bb= camera.start_sequence_capture(1)
            time.sleep(exposureTime/1000000)
            cc = camera.get_image() # this is your picture
            time.sleep(0.05)
            #max = numpy.max(cc)
            #bb = numpy.array(aa)
            image_array = numpy.array(cc)
            if show_images==1:
                if first_image == 0:
                    image_handle = ax.imshow(image_array)
                    image_handle.autoscale()
                    fig.canvas.draw()   
                else:
                    background_image = fig.canvas.copy_from_bbox(ax.bbox)
                    fig.canvas.restore_region(background_image)
                    image_handle.set_array(image_array)
                    fig.draw_artist(ax)
                    fig.canvas.blit(ax.bbox)
    
            # print(image_array)
            
            numGreaterThan = ( (image_array > threshold_value) ).sum()       # image_array > 3964         10-19, >991, 1024       40-76, 	>3964, 4096    
            # correct: 1024x1024 = 1048576 when (image_array<4096)         correct: 0 when (image_array>4096)       
            # image doesn't show true colors?  0 when (image_array>3964)         1025487 when (image_array>0)
            # it's a grayscale image? what true colors should be there?
            print('Pixels oversaturated', numGreaterThan,'-Max Value-',numpy.max(image_array))



            # guessed algorithm for now, need to change later
            if numGreaterThan == 0:    # this means the image is too dim

                #now: the max value will be proportional to the exposure. If 
                max_val = numpy.max(image_array)
                max_bits = 65535 # 16 bit

                #then ideal exposure time is proportional to max_bits, current exposure is proportional to max_val
                # exposureTime / max_bits = current_exposureTime/max_val
                exposureTime = exposureTime* max_bits/max_val
                #exposureTime = exposureTime * 1.05# increase exposure 5%

            elif numGreaterThan > 19: # this means image is too bright
                #problem: if the image is largely saturated then exposure time explodes very close to zero. 
                #exposureTime *= 1.004*numpy.exp(-0.0002803*numGreaterThan) # decrease exposure 

                if numGreaterThan > 1000:
                    exposureTime = exposureTime/2
                elif numGreaterThan < 1000 and numGreaterThan > 500:
                    exposureTime = exposureTime * .80 #decrease exposure 20%
                elif numGreaterThan < 500 and numGreaterThan > 100:
                    exposureTime = exposureTime * .90 #decrease exposure 10%
                elif numGreaterThan < 100 :
                    exposureTime = exposureTime * .95 #decrease exposure 20%
            print('Exposure value', exposureTime)

            if exposureTime > 10000000:
                print('reached max exposure time for camera')
                break
        #at this point image_array contains the image we want
        final_hyperspectral_array[i,:,:] = numpy.copy(image_array)
        final_exposure_time_array[i] = numpy.copy(exposureTime)
        if show_images==2:
            if first_image == 0:
                image_handle = ax.imshow(image_array)
                image_handle.autoscale()
                fig.canvas.draw()   
            else:
                background_image = fig.canvas.copy_from_bbox(ax.bbox)
                fig.canvas.restore_region(background_image)
                image_handle.set_array(image_array)
                fig.draw_artist(ax)
                fig.canvas.blit(ax.bbox)
    
        #reset exposureTime to some reasonable time
        exposureTime = 20000 
        image_array = image_array*0

        board.digital[led].write(0) #set pin down

    print('Acquiring corresponding Dark')
    # acquire a 10 dark images for each exposure and save the average
    final_dark_images_array = numpy.zeros_like(final_hyperspectral_array)
    final_corrected_images = numpy.zeros_like(final_hyperspectral_array)
    for dark_exposure in range(0,21):
        camera.set_exposure(final_exposure_time_array[dark_exposure])      
        #print(camera.cam.properties['ExposureTimeAbs'])    
        #dark_images_temp = numpy.zeros((10, 2048,1088))   
        for frame_num in range(0,10):
            bb= camera.start_sequence_capture(1)
            time.sleep(0.03+final_exposure_time_array[dark_exposure]/1000000)
            cc = camera.get_image() # this is your picture
            time.sleep(0.05)
            if frame_num == 0:
                dark_images_temp = numpy.array(cc)
            else:
                dark_images_temp = dark_images_temp+ numpy.array(cc)
        #save average dark
        final_dark_images_array[dark_exposure,:,:] = dark_images_temp/10
        
        #subtract background
        diff_image = final_hyperspectral_array[dark_exposure,:,:]-final_dark_images_array[dark_exposure,:,:]
        #fix negative values
        diff_image[diff_image<0]  = 0
        #correct images for exposure and dark. (Intensity - Dark) / Exposure
        corrected_image = numpy.divide(diff_image, final_exposure_time_array[dark_exposure]/1000)
        corrected_image[corrected_image<0] = 0
        final_corrected_images[dark_exposure,:,:] =numpy.copy(corrected_image)
        #final_corrected_images[dark_exposure,:,:] = numpy.divide((final_hyperspectral_array[dark_exposure,:,:]-final_dark_images_array[dark_exposure,:,:]),final_exposure_time_array[dark_exposure]/1000)
    final_corrected_images = numpy.divide( (2**16-1)*final_corrected_images, numpy.max(final_corrected_images))
    camera.close()

    print('Saving..')
    # code outside while loop
    # save exposure time to array
    list_vector = ['LED Number']
    #for led_num in range(0, final_exposure_time_array.shape[0]):
    #    list_vector.append('Led-num-' + str(led_num))

    output_csv = DataFrame(final_exposure_time_array, index = None, columns = list_vector) #format the .csv file


    fileName_save, _ = QFileDialog.getSaveFileName(parent_QWidget,"Save data as..") #get input file name and directory
    root_name, filetype = ospath.splitext(fileName_save)
    filetype = '.tiff'
    newfilename = root_name + '-LED_exposure.csv'
    print('-exposure values..')
    output_csv.to_csv(newfilename) # save csv file with exposures
    print('-raw images..')
    for lambda_num in range(0,final_hyperspectral_array.shape[0]):
        newfilename = root_name + '-LED'+(str(lambda_num)).zfill(3) + filetype
        temp_data = numpy.copy( final_hyperspectral_array[lambda_num,:,:])
        TiffFile.imsave(newfilename, numpy.uint16( temp_data ), software='HySP')

    print('-dark images..')
    for lambda_num in range(0,final_dark_images_array.shape[0]):
        newfilename = root_name + '-Dark'+(str(lambda_num)).zfill(3) + filetype
        temp_data = numpy.copy( final_dark_images_array[lambda_num,:,:])
        TiffFile.imsave(newfilename, numpy.uint16( temp_data ), software='HySP')

    print('-corrected images..')
    for lambda_num in range(0,final_corrected_images.shape[0]):
        newfilename = root_name + '-Corrected'+(str(lambda_num)).zfill(3) + filetype
        temp_data = numpy.copy( final_corrected_images[lambda_num,:,:])
        TiffFile.imsave(newfilename, numpy.uint16( temp_data ), software='HySP')

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
    spectra_list.append('Spectra\\450nm.txt')
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
    #
    window_len = 11
    for spec_data in range(0,len(spectra_list)):
        temp = numpy.loadtxt(spectra_list[spec_data])
        #smooth
        x1 = temp[:,1]
        x1[x1<0] = 0
        s=numpy.r_[x1[window_len-1:0:-1],x1,x1[-1:-window_len:-1]]
        s[s<0] = 0
        w=numpy.ones(window_len,'d')
        y=numpy.convolve(w/w.sum(),s,mode='valid')
        y[y<0] = 0
        bkg_subtracted = y[:-(window_len-1)]- (y[0]*dark_bkg[1,:]/dark_bkg[1,0])
        bkg_subtracted[bkg_subtracted<0] = 0
        led_spectra[spec_data,:] = bkg_subtracted / numpy.max(bkg_subtracted)
        ax2.plot(wavelength[0,:],led_spectra[spec_data,:])
        print('plot', spec_data)
    f2.show()


        









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