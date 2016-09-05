import RPi.GPIO as GPIO
import smbus
import time
from Adafruit_LED_Backpack import SevenSegment

# Create display instance on default I2C address (0x70) and bus number.
display = SevenSegment.SevenSegment()

# Initialize the display. Must be called once before using the display.
display.begin()

# Keep track of the colon being turned on or off.
colon = False

GPIO.setmode(GPIO.BCM)

GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)

from lxml import html
from requests.exceptions import HTTPError
import requests

########################################## LCD ##########################################
# Define some device parameters
I2C_ADDR  = 0x3f # I2C device address
LCD_WIDTH = 16   # Maximum characters per line

# Define some device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

LCD_BACKLIGHT  = 0x08  # On
#LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100 # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

#Open I2C interface
#bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
bus = smbus.SMBus(1) # Rev 2 Pi uses 1
##################################################################################################


def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off 
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(E_DELAY)
  
def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = the data
  # mode = 1 for data
  #        0 for command

  bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
  bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

  # High bits
  bus.write_byte(I2C_ADDR, bits_high)
  lcd_toggle_enable(bits_high)

  # Low bits
  bus.write_byte(I2C_ADDR, bits_low)
  lcd_toggle_enable(bits_low)
  
def lcd_string(message,line):
  # Send string to display

  message = message.ljust(LCD_WIDTH," ")

  lcd_byte(line, LCD_CMD)

  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)
	
def lcd_toggle_enable(bits):
  # Toggle enable
  time.sleep(E_DELAY)
  bus.write_byte(I2C_ADDR, (bits | ENABLE))
  time.sleep(E_PULSE)
  bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
  time.sleep(E_DELAY)
  
FirstRunState = True

SearchGroup = 0 # Group number of the search team
SearchTeamA = 0 # 
SearchTeamB = 0

TestNumber = 0 # incument value every time loop is run for debug

ChangeSearchTeam = 0

TotalTeams = 0

TeamName = ""
TeamScore = ""
TeamGroup = ""

def LoadData():
	for i in range(0,5):
		try:
			GrabScores = requests.get('http://108.47.111.137/ArduinoSportsScores/GrabFootball.php')
					
			page = requests.get('http://108.47.111.137/ArduinoSportsScores/FootballTable.php')
			tree = html.fromstring(page.content)

			TeamName = tree.xpath('//td[@id="TeamName"]/text()')
			TeamScore = tree.xpath('//td[@id="TeamScore"]/text()')
			TeamGroup = tree.xpath('//td[@id="TeamGroup"]/text()')

			print 'Team: ', TeamName
			print 'Score: ', TeamScore
			print 'Group: ', TeamGroup
			
			for x in range(0,TotalTeams):
				if TeamGroup[x] == TeamGroup[SearchTeamA] and x is not SearchTeamA:
					SearchTeamB = x
					break
					
		except requests.exceptions.Timeout:
			print 'Error'
			time.sleep(1)
		except requests.exceptions.TooManyRedirects:
			print 'Error'
			time.sleep(1)
		except requests.exceptions.RequestException as e:
			print 'Error'
			print e
			time.sleep(1)

lcd_init()  # initialize lcd
# LoadData() #Load all web data once for team selecting

while True:  
	input_state = GPIO.input(18)
	RunStatus = GPIO.input(24)
	
	if RunStatus == False or FirstRunState == True:
		LCD_BACKLIGHT = 0x00  # Off
		try:
			GrabScores = requests.get('http://108.47.111.137/ArduinoSportsScores/GrabFootball.php')
				
			page = requests.get('http://108.47.111.137/ArduinoSportsScores/FootballTable.php')
			tree = html.fromstring(page.content)

			TeamName = tree.xpath('//td[@id="TeamName"]/text()')
			TeamScore = tree.xpath('//td[@id="TeamScore"]/text()')
			TeamGroup = tree.xpath('//td[@id="TeamGroup"]/text()')

			print 'Team: ', TeamName
			print 'Score: ', TeamScore
			print 'Group: ', TeamGroup
					
			if not TeamName:
				str1 = "No current games found"
				str2 = ""
				lcd_string(str1,LCD_LINE_1)
				lcd_string(str2,LCD_LINE_2)
			
				display.clear()
				display.print_float(int(0), decimal_digits=0, justify_right=False)
				display.print_float(int(0), decimal_digits=0, justify_right=True)
				display.set_colon(colon)
			else:
				for x in range(0,TotalTeams):
					if TeamGroup[x] == TeamGroup[SearchTeamA] and x is not SearchTeamA:
						SearchTeamB = x
						break
				str1 = "H: " + TeamName[SearchTeamA]
				str2 = "A: " + TeamName[SearchTeamB]
						
				lcd_string(str1,LCD_LINE_1)
				lcd_string(str2,LCD_LINE_2)
			
				display.clear()
				display.print_float(int(TeamScore[SearchTeamA]), decimal_digits=0, justify_right=False)
				display.print_float(int(TeamScore[SearchTeamB]), decimal_digits=0, justify_right=True)
				display.set_colon(colon)
			display.write_display()
			
			TestNumber = TestNumber + 1
			
			print 'Test: ', TestNumber
			
		except requests.exceptions.Timeout:
			print 'Error'
			time.sleep(1)
		except requests.exceptions.TooManyRedirects:
			print 'Error'
			time.sleep(1)
		except requests.exceptions.RequestException as e:
			print 'Error'
			print e
			time.sleep(1)
		FirstRunState = False
		time.sleep(2)
	else:
		LCD_BACKLIGHT  = 0x08  # On
		TotalTeams = len(TeamName)
		if input_state == False:
			ChangeSearchTeam = ChangeSearchTeam + 1
			SearchTeamA = ChangeSearchTeam
			print 'Button Pressed'
			print 'Team Index'
			print ChangeSearchTeam
			if ChangeSearchTeam == TotalTeams:
				ChangeSearchTeam = 0
				SearchTeamA = ChangeSearchTeam
			time.sleep(0.1)
		
		if not TeamName:
			str1 = "No current games found"
			str2 = ""
			lcd_string(str1,LCD_LINE_1)
			lcd_string(str2,LCD_LINE_2)
			
			display.clear()
			display.print_float(int(0), decimal_digits=0, justify_right=False)
			display.print_float(int(0), decimal_digits=0, justify_right=True)
			display.set_colon(colon)
		else:
			for x in range(0,TotalTeams):
				if TeamGroup[x] == TeamGroup[SearchTeamA] and x is not SearchTeamA:
					SearchTeamB = x
					break
				
			str1 = "H: " + TeamName[SearchTeamA]
			str2 = "A: " + TeamName[SearchTeamB]
					
			lcd_string(str1,LCD_LINE_1)
			lcd_string(str2,LCD_LINE_2)
		display.write_display()