global localid, running, last, uptime, life, state, last_state, presses
from machine import Pin, Timer, SoftSPI
import max7219_8digit
import neopixel
import utime as time
import machine
import json
from ota import OTAUpdater
version = 2
firmware_url = "https://github.com/ticktock509/rm5-tagdecoder/"
print('version', version)
ota_updater = OTAUpdater(firmware_url, "main.py", version)

print('loading...')
state = 'loading'
last_state = 'off'
localid = 'picow_kp3x4a'
start = time.time()
uptime = time.time() - start
hbstart = time.time()
life = time.time()
running = False
testing = True
startup = True
last = 0
pwr = machine.Pin(16, Pin.OUT)
pwr.value(1)

p = machine.Pin(17)
pix = neopixel.NeoPixel(p,6)
#order = R,G,B
green = (0,255,0)
blue = (0,0,255)
red = (255,0,0)
yellow = (100,150,0)
white = (255,255,255)
off = (0,0,0)
spi = SoftSPI(baudrate=100000, polarity=1, phase=0, sck=Pin(6), mosi=Pin(7), miso=Pin(0))
ss = Pin(5, Pin.OUT)
display = max7219_8digit.Display(spi, ss)
presses = ''
ip = nic.ifconfig()[0]
print('id:',localid,'ip:',ip)
print()

SEND_online = "wlan_sf/status/"+localid
TOPIC = "wlan_sf/"+localid
KP = b"wlan_sf/"+localid+"/kp"
STATE = b"wlan_sf/"+localid+"/state"
led = machine.Pin('LED', machine.Pin.OUT)
pix.fill(off)
pix.write()

def flash():
    pix.fill(white)
    pix.write()
    time.sleep(1/500)
    pix.fill(off)
    pix.write()
    time.sleep(1/500)
    
def InitKeypad():
    for row in range(0,4):
        for col in range(0,3):
            row_pins[row].low()
    ready = {'id':localid, 'ip':ip,'comment':'ready'}
    ready = json.dumps(ready)
    c.publish(SEND_online, ready)


#def PollKeypad(timer):
def PollKeypad():
    key = None
    for row in range(4):
        for col in range(3):
            # Set the current row to high
            row_pins[row].high()
            # Check for key pressed events
            if col_pins[col].value() == KEY_DOWN:
                key = KEY_DOWN
            if col_pins[col].value() == KEY_UP:
                key = KEY_UP
            row_pins[row].low()
            if key == KEY_DOWN:
                #display.WriteLine("                ",2)
                #display.WriteLine("Key Pressed = "+ keys[row][col],2)                
                #print('key pressed: '+ keys[row][col],'Row: '+str(row), 'Col: '+str(col))
                last_key_press = keys[row][col]
                return(last_key_press)
    return('') 

def sub_cb(topic, msg):
    global life, running, state, presses
    life = time.time()
    led.on()
    topic = topic.decode('utf-8')
    m_decode=str(msg.decode("utf-8","ignore"))
    print('Incoming: ', m_decode)
    if not running:
        running = True
        state = 'firsthold'
    if m_decode == 'ping':
        #print('ping')
        led.off()
        return
    elif 'display:' in m_decode:
        presses = m_decode.split(':')[1]
        display.write(presses)
        display.post()
    elif m_decode == 'reset':
        machine.reset()
    elif m_decode == 'ready':
        state = 'ready'
    elif m_decode == 'error':
        state = 'error'
    elif m_decode == 'hold':
        state = 'hold'
    elif m_decode == 'off':
        state = 'off'
    elif m_decode == 'correct':
        state = 'correct'
    elif m_decode == 'wrong':
        state = 'wrong'


def correct():
    for x in range(10):
        pix.fill(green)
        pix.write()
        time.sleep(1/500)
        pix.fill(off)
        pix.write()
        time.sleep(1/500)
        
def wrong():
    for x in range(10):
        pix.fill(red)
        pix.write()
        time.sleep(1/500)
        pix.fill(off)
        pix.write()
        time.sleep(1/500)        

def heartbeat(t):
    try:
        online = {'id':localid, 'ip':ip,'comment':'hb'}
        online = json.dumps(online)
        c.publish(SEND_online, online)
    except OSError:
        data = 'heartbeat: reboot now, error cant send data- - not rebooting here'
        print('hearbeat:'+data) if testing else []    
    
hbtimer = Timer(period=30000, mode=Timer.PERIODIC, callback=heartbeat)

c = MQTTClient(localid, "192.168.87.90")
c.set_callback(sub_cb)

try:
    c.connect()
except OSError:
    data = 'c.connect(): unable to connect to mqtt server'
    print(data)
    time.sleep(.5)
   
try:
    c.subscribe(TOPIC)
except OSError:
    data = 'c.subscribe(): unable to subscribe'
    print(data)
    time.sleep(.5)
    
online = {'id':localid, 'ip':ip,'comment':'online'}
online = json.dumps(online)
data = 'Online: '+online
print(data)

try:
    c.publish(SEND_online, online)
except OSError:
    data = 'on Online Publish: cant publish right now'
    print(data)
    time.sleep(.5)

checkerror = False

# CONSTANTS
KEY_UP   = const(0)
KEY_DOWN = const(1)

keys = [['1', '2', '3'], ['4', '5', '6'], ['7', '8', '9'], ['*', '0', '#']]

# RPi Pico pin assignments
rows = [8,10,11,9]
cols = [12,13,14]
 #* The Raspberry Pi Pico pin connections for matrix keypad:
 #* R1 pin of keypad to RPi Pico GPIO8
 #* R2 pin of keypad to RPi Pico GPIO9
 #* R3 pin of keypad to RPi Pico GPIO10
 #* R4 pin of keypad to RPi Pico GPIO11
 #* C1 pin of keypad to RPi Pico GPIO12
 #* C2 pin of keypad to RPi Pico GPIO13
 #* C3 pin of keypad to RPi Pico GPIO14
 #* C4 pin of keypad to RPi Pico GPIO15

# Set pins for rows as outputs
row_pins = [Pin(pin_name, mode=Pin.OUT) for pin_name in rows]

# Set pins for columns as inputs
col_pins = [Pin(pin_name, mode=Pin.IN, pull=Pin.PULL_DOWN) for pin_name in cols]
pix.fill(red)
pix.write()        

ota_updater.download_and_install_update_if_available()


while not running:
    try:
        c.check_msg()
    except OSError:
        if not checkerror:
            print('not running: check message error') if testing else []
        if checkerror:
            time.sleep(.5)
        checkerror = True
    last = time.time() - life
    if not last_state == state:
        c.publish(STATE, state)
        last_state = state
    if state == 'correct':
        correct()
    elif state == 'wrong':
        wrong()
    elif state == 'hold':
        pix.fill(yellow)
        pix.write()
    elif state == 'error':
        pix.fill(red)
        pix.write()
    elif state == 'ready':
        pix.fill(blue)
        pix.write()
    elif state == 'off':
        pix.fill(off)
        pix.write()

    if last > 60:
        state = 'error'
        data = str(uptime)+ ' too old, time to reboot'
        print(data) if testing else []
        if last > 90:
            #machine.reset()
            print('tried to reset()')

checkerror = False
pix.fill(yellow)
pix.write()

while running:
    if startup:
        startup = False    
        # Initialize and set all the rows to low
        print('init keypad')
        InitKeypad()
        time.sleep(2)
        last_item = -1
        print('starting')
    uptime = time.time() - start
    last = time.time() - life
    if(last > 60):
        print('last',last)
        state = 'error'
        if last > 90:
            #machine.reset()
            print('tried to reset()')

    time.sleep_ms(10)
    if state == 'ready':
        item = PollKeypad()
        if not item == last_item:
            if not item == '':
                print('item',item)
                c.publish(KP, str(item))                
            last_item = item
    try:
        c.check_msg()
    except OSError:
        if not checkerror:
            print('check message error')
        if checkerror:
            time.sleep(.5)
        checkerror = True
    if not last_state == state:
        last_state = state
        c.publish(STATE, state)
    if state == 'correct':
        correct()
    elif state == 'wrong':
        wrong()
    elif state == 'hold':
        pix.fill(yellow)
        pix.write()
    elif state == 'error':
        pix.fill(red)
        pix.write()
    elif state == 'ready':
        pix.fill(blue)
        pix.write()
    elif state == 'off':
        pix.fill(off)
        pix.write()        

    
c.disconnect()
