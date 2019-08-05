import sys
import os
import time
import shutil
import time
os.chdir('/home/pi/Documents/python')
import MPR121
import RPi.GPIO as GPIO
import ADS1x15 as Adafruit_ADS1x15
import random

sys.path.insert(0, "/home/pi/Documents/python")

#------------------------------------------------------------------------

LED1_pin = 4
LED2_pin= 5

amp_shutdown = 22

encoder1A = 6
encoder1B = 13
encoder2A = 23  #7 FOR RevA
encoder2B = 24  #12 FOR RevA

last_bank_select = 200 # FORCE READING
bankSelect = 0

MinimumDistance = 0
MaximumDistance = 500

rangingStartDelay = 0.1
startUpDelay = 0.3
shutDownDelay = 0.5
last_cc1 = 50000   
last_cc2 = 50000  
last_cc3 = 50000   
last_cc4 = 50000
last_cc5 = 50000   
last_cc6 = 50000     
last_cc7 = 50000   
last_cc8 = 50000     
last_cc1_select = 100             
movement_threshold = 10     #FOR CC Channels
hysterisis_threshold = 600   # FOR SWITCH FUNCTION
distanceChangeThreshold = 1
#number_banks = 16
count = 9999
last_distance11 = 0
count2 = 0
adc_scalar = 0.3774581965047371
lastLoopTime = time.time() * 1000
counter = 0


enc1_pos = 0
enc1_last_pos = 0
enc2_pos = 0
enc2_last_pos = 0
encoder1_armed = 0
encoder2_armed = 0
#----------------------------------------------------------------------------------
dst1 = "/tmp/samples/bank1"
dst2 = "/tmp/samples/bank2"


path1 = '/home/pi/Documents/samples/Bank1'
path2 = '/home/pi/Documents/samples/Bank2'
# CHECKS FOR FOLDERS IN PATH AND CREATES A LIST OF THEM
folders1 = []
files =  os.listdir(path1)
files.sort()
for name in files:
    full_path = os.path.join(path1, name)
    if os.path.isdir(full_path):
        folders1.append(full_path)
# CHECKS FOR FOLDERS IN PATH AND CREATES A LIST OF THEM
folders2 = []
files =  os.listdir(path2)
files.sort()
for name in files:
    full_path = os.path.join(path2, name)
    if os.path.isdir(full_path):
        folders2.append(full_path)
		
number_samples1  = len(folders1)
number_samples2 = len(folders2)

#----------------------------------------------------------------------------------
def sendMessage (message=''):
    os.system("echo '" + message + ";' | pdsend 3000")

def sendPot(channel, value):
    os.system("echo ' CC " + str(channel) + ' ' + str(value) + ";' | pdsend 3000") # CHANNELS 3 - 6

def noteOn(channel):
    os.system("echo ' ON " + str(channel) + ";' | pdsend 3000")

def sendButton(channel):
    os.system("echo ' BTN " + str(channel) + ";' | pdsend 3000")

def noteOff(channel):
    os.system("echo ' OFF " + str(channel) + ";' | pdsend 3000")

def LoopNum(channel):
    os.system("echo ' LOOP " + str(channel) + ";' | pdsend 3000")

def Bank1Update(channel):
    os.system("echo ' BANK1 " + str(channel) + ";' | pdsend 3000")

def Bank2Update(channel):
    os.system("echo ' BANK2 " + str(channel) + ";' | pdsend 3000")
        

#----------------------------------------------------------------------------------


def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)
# ----------------------------------------------------------------

def changeBank1(bank_number):
    src = folders1[bank_number]
    print (src)
    Bank1Update(bank_number)
    if os.path.islink(dst1) :
        os.unlink(dst1)
    os.symlink(src, dst1)
	
def changeBank2(loop_number):
    src = folders2[loop_number]
    print (src)
    Bank2Update(loop_number)
    if os.path.islink(dst2) :
        os.unlink(dst2)
    os.symlink(src, dst2)

	
def encoder1ChangeA(channel): 
    global enc1_pos
    global encoder1_armed
    GPIO_B = GPIO.input(encoder1B)
    #print("A.FALLING - B " +    str(GPIO_B))
    if encoder1_armed == 1:                   # IF ALREADY ARMED ------------
        if not GPIO_B:                  # AND OTHER PIN IS ALREADY LOW
            enc1_pos -= 1                    # DECCREMENT COUNTER
            encoder1_armed = 0
            #print("TRIGGERED DOWN")
    else:                               # IF NOT ARMED ----------------
        encoder1_armed = 0
        if GPIO_B :                     # IF OTHER PIN IS HIGH
            encoder1_armed = 2        # ARM ENCODER
            #print("armed UP")           

def encoder1ChangeB(channel): 
    global enc1_pos
    global encoder1_armed

    GPIO_A = GPIO.input(encoder1A)
    #print("B.FALLING - A " +    str(GPIO_A))
    if encoder1_armed == 2:                   # IF ALREADY ARMED ------------
        if not GPIO_A:                  # AND OTHER PIN IS ALREADY LOW
            enc1_pos += 1                    # INCREMENT COUNTER
            encoder1_armed = 0
            #print("TRIGGERED UP")
    else:                               # IF NOT ARMED ----------------
        encoder1_armed = 0
        if GPIO_A :                     # IF OTHER PIN IS HIGH
            encoder1_armed = 1        # ARM ENCODER
            #print("armed DOWN")           
#--------------------------------------------------------------------------
def encoder2ChangeA(channel): 
    global enc2_pos
    global encoder2_armed
    GPIO_B = GPIO.input(encoder2B)
    #print("A.FALLING - B " +    str(GPIO_B))
    if encoder2_armed == 1:                   # IF ALREADY ARMED ------------
        if not GPIO_B:                  # AND OTHER PIN IS ALREADY LOW
            enc2_pos -= 1                    # DECCREMENT COUNTER
            encoder2_armed = 0
            #print("TRIGGERED DOWN")
    else:                               # IF NOT ARMED ----------------
        encoder2_armed = 0
        if GPIO_B :                     # IF OTHER PIN IS HIGH
            encoder2_armed = 2        # ARM ENCODER
            #print("armed UP")           

def encoder2ChangeB(channel): 
    global enc2_pos
    global encoder2_armed

    GPIO_A = GPIO.input(encoder2A)
    #print("B.FALLING - A " +    str(GPIO_A))
    if encoder2_armed == 2:                   # IF ALREADY ARMED ------------
        if not GPIO_A:                  # AND OTHER PIN IS ALREADY LOW
            enc2_pos += 1                    # INCREMENT COUNTER
            encoder2_armed = 0
            #print("TRIGGERED UP")
    else:                               # IF NOT ARMED ----------------
        encoder2_armed = 0
        if GPIO_A :                     # IF OTHER PIN IS HIGH
            encoder2_armed = 1        # ARM ENCODER
            #print("armed DOWN")  
    
# ----------------------------------------------------------------

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED1_pin, GPIO.OUT)
GPIO.setup(LED2_pin, GPIO.OUT)
GPIO.setup(amp_shutdown, GPIO.OUT)
GPIO.setup(encoder1A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(encoder1B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(encoder2A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(encoder2B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(encoder1A, GPIO.FALLING, callback=encoder1ChangeA, bouncetime=500) 
GPIO.add_event_detect(encoder1B, GPIO.FALLING, callback=encoder1ChangeB, bouncetime=500) 
GPIO.add_event_detect(encoder2A, GPIO.FALLING, callback=encoder2ChangeA, bouncetime=500) 
GPIO.add_event_detect(encoder2B, GPIO.FALLING, callback=encoder2ChangeB, bouncetime=500) 

# ----------------------------------------------------------------


cap = MPR121.MPR121()
cap.begin()

adc = Adafruit_ADS1x15.ADS1115(0x48)

# SETUP PORT BEFORE SENSOR DELAY



bank1_select = random.randint(0,number_samples1-1)
enc1_pos = bank1_select
enc1_last_pos = enc1_pos
changeBank1(bank1_select)
Bank1Update(bank1_select)

bank2_select = random.randint(0,number_samples2-1)
changeBank2(bank2_select)
Bank2Update(bank2_select)
enc2_pos = bank2_select
enc2_last_pos = enc2_pos

GPIO.output(LED1_pin, GPIO.HIGH)
GPIO.output(LED2_pin, GPIO.HIGH)
GPIO.output(amp_shutdown, GPIO.HIGH)
'''
time.sleep(10) #wait for connect
# ----------------------------------------------------------------
last_cc1 = 50000   
last_cc2 = 50000   
last_cc2_select = 100             
movement_threshold = 200      
hysterisis_threshold = 600
number_banks = 8 - 1 #ONE LESS DUE TO ZERO BANK
count = 9999
'''
last_touched = cap.touched()

try:

    while True:

		#------------------------------------------------------------------------
        current_touched = cap.touched()
        
        for i in range(12):
            pin_bit = 1 << i
            if current_touched & pin_bit and not last_touched & pin_bit:
                print('{0} on'.format(i+1))
                noteOn (i+1) # NOTE ON

            if not current_touched & pin_bit and last_touched & pin_bit:
                print('{0}    off!'.format(i+1))
                noteOff (i+1) # NOTE OFF
            
        last_touched = current_touched        ## CAP SENSE RESET AND DEBUG
		#------------------------------------------------------------------------

        
        if counter % 4 == 0: 
            current_cc1 = adc.read_adc(0, 1)
            if abs(last_cc1 - current_cc1) > hysterisis_threshold :
                last_cc1 = current_cc1
                pot1 = int(current_cc1 * adc_scalar)
                sendPot ( 1, pot1) # 0 = CH 16
                print('POT 1 : ' + str(pot1))

        elif counter % 4 == 1: 
            current_cc2 = adc.read_adc(1, 1) # 1 - 26418
            if abs(last_cc2 - current_cc2) > movement_threshold :
                last_cc2 = current_cc2
                pot2 = int(current_cc2 * adc_scalar)
                sendPot ( 2, pot2) # 0 = CH 16
                print('POT 2 : ' + str(pot2))
                            
        elif counter % 4 == 2: 
            current_cc3 = adc.read_adc(2, 1) # 1 - 26418                        
            if abs(last_cc3 - current_cc3) > movement_threshold :
                last_cc3 = current_cc3
                pot3 = int(current_cc3 * adc_scalar)
                sendPot ( 3, pot3)
                print('POT 3 : ' + str(pot3))
                            
        elif counter % 4 == 3: 
            current_cc4 = adc.read_adc(3, 1) # 1 - 26418            
            if abs(last_cc4 - current_cc4) > movement_threshold :
                last_cc4 = current_cc4
                #volume = int(pow( (last_cc4 + 2000) / 300.0 , 2) )
                pot4 = int(current_cc4 * adc_scalar)
                sendPot ( 4, pot4)
                print('POT 4 : ' + str(pot4))
             
 

        counter += 1
        if counter > 3:
            counter = 0
		#------------------------------------------------------------------------

        if enc1_pos != enc1_last_pos:
                    
            if enc1_pos >= number_samples1:
                enc1_pos = enc1_pos - number_samples1

            if enc1_pos < 0 :
                enc1_pos = enc1_pos + number_samples1

            print("ENCODER 1 pos={}".format(enc1_pos))
            enc1_last_pos = enc1_pos
            
            bank1_select = enc1_pos
            last_bank1_select = bank1_select
            changeBank1(bank1_select)
            Bank1Update(bank1_select)
        #------------------------------------------------------------------------

        if enc2_pos != enc2_last_pos:
                    
            if enc2_pos >= number_samples2:
                enc2_pos = enc2_pos - number_samples2

            if enc2_pos < 0 :
                enc2_pos = enc2_pos + number_samples2

            print("ENCODER 2 pos={}".format(enc2_pos))
            enc2_last_pos = enc2_pos
            
            bank2_select = enc2_pos
            last_bank2_select = bank2_select
            changeBank2(bank2_select)
            Bank2Update(bank2_select)


        ## LOOP DELAY
        time.sleep(0.01)    
    
#------------------------------------------------------------------------
 

except KeyboardInterrupt:
    # clean up
    print("See you Soon")
finally:    
    GPIO.output(amp_shutdown, GPIO.LOW)
    GPIO.output(LED1_pin, GPIO.LOW)
    GPIO.output(LED2_pin, GPIO.LOW)
    if os.path.islink(dst1) :
        os.unlink(dst1)
    if os.path.islink(dst2) :
        os.unlink(dst2)
