import os                       # Check filesystem
import Adafruit_MCP3008         # Interface with analogue-digital converter
import cPickle as pickle        # Read/write history
import datetime                 # Date/time stamps
import argparse                 # Command-line interface
import send_gmail               # Send status by email

# Software SPI configuration
CLK  = 18
MISO = 23
MOSI = 24
CS   = 25
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

# Data configuration
PLANTS = {'Money plant':{'id':0, 'environment':'normal'},
        'Avocado':{'id':1, 'environment':'normal'}}

ENVIRONMENTS = {'normal':{'dry':35, 'wet':50},
                'arid':{'dry':5, 'wet':35},
                'tropical':{'dry':45, 'wet':60}}

HISTORY_FILE = '/home/pi/plant/data/plant_history.bin'

EMAIL_TEMPLATE = '/home/pi/plant/resources/report.html'

def currentDate():
        return datetime.datetime.now().strftime('%d/%m/%Y %H:%M')

def checkPlant(id):
        reading = mcp.read_adc(id)
        min = float(56) # water
        max = 218 # air
        moisture = 100 - int(round( ((reading - min) / (max - min)) * 100 ))

        if moisture > 100:
                moisture = 100
        if moisture < 0:
                moisture = 0

        return moisture

def getStatus(environment, moisture):
        if moisture < ENVIRONMENTS[environment]['dry']:
                return 'dry'
        elif moisture < ENVIRONMENTS[environment]['wet']:
                return 'wet'
        else:
                return 'ok'

def storeData(plant, moisture):
        if os.path.exists(HISTORY_FILE):
                history_file = open(HISTORY_FILE, 'rb')
                previous_data = pickle.load(history_file)
                history_file.close()
                if plant in previous_data:
                        previous_data[plant].append([currentDate(), moisture])
                else:
                        previous_data[plant] = [ [currentDate(), moisture] ]
        else:
                previous_data = {}
                previous_data[plant] = [ [currentDate(), moisture] ]
        history_file = open(HISTORY_FILE, 'wb')
        pickle.dump(previous_data, history_file)
        history_file.close()

def readData():
        history_file = open(HISTORY_FILE, 'rb')
        data = pickle.load(history_file)
        return data

def monitor():
        for plant in PLANTS:
                moisture =  checkPlant(PLANTS[plant]['id'])
                status = getStatus(PLANTS[plant]['environment'], moisture)
                print '{} is {} ({}%)'.format(plant, status, moisture)
                storeData(plant, moisture)

def sendReport(recipients, data):
        template = open(EMAIL_TEMPLATE, 'rb')
        html = template.read()
        x = 0
        for plant in sorted(data):
                x = x + 1
                html = html.replace('^p{}_perc^'.format(x), '{}%'.format(data[plant][1]))
        send_gmail.sendAPI('gmurden22@gmail.com', recipients, 'Plant update', html)

def report(recipients):
        latest = {}
        data = readData()
        for plant in data:
                latest[plant] = data[plant][-1]
        sendReport(recipients, latest)

def cli():
        ap = argparse.ArgumentParser()
        ap.add_argument('-m', '--mode', required=False,
                help='\'monitor\' plants or \'report\' on status.')
        ap.add_argument('-e', '--email', required=False,
                help='Send notification to this email')
        args = vars(ap.parse_args())
        return args

if __name__ == '__main__':
        args = cli()
        if args['mode'] != None:
                if args['mode'] == 'report':
                        if args['email'] != None:
                                report(args['email'].replace(',', ';'))
                        else:
                                print 'Report mode specified, but no email provided. Specify an --email and try again'
                else:
                        monitor()
        else:
                print 'No mode selected. Specify either --monitor or --report.'