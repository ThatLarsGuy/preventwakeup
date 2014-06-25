#!/usr/bin/env python2
import sys
import os
import subprocess
import logging
import logging.handlers

file_name = '/home/me/prevent_wakeup.log'

logger = logging.getLogger('PreventWakeUp')
handler = logging.handlers.RotatingFileHandler(file_name, maxBytes=50000, backupCount=1)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

logger.info('----------------------------------------------')

#Check the ACPI wakeup list and , if required, disable the provided trigger by writing it to /proc/acpi/wakeup
def enforce_not_wakeup_trigger(trigger):
	#eg: cat /proc/acpi/wakeup
	proc = subprocess.Popen(["cat", "/proc/acpi/wakeup"],stdout=subprocess.PIPE)
	while True:
		line = proc.stdout.readline()
		if line != '': #Continue while there's more output to parse
			if line.startswith(trigger)  and  'enabled' in line.rstrip():
				logger.info('Disabling wakeup trigger:' + trigger)
				#eg: echo LID > /proc/acpi/wakeup
				#subprocess.call(["sh", "-c", "'echo LID > /proc/acpi/wakeup'"])
				text_file = open("/proc/acpi/wakeup", "w")
				text_file.write(trigger)
				text_file.close()
		else:
			break

def get_lid_status():
	#eg: cat /proc/acpi/button/lid/LID/state
	proc = subprocess.Popen(["cat", "/proc/acpi/button/lid/LID/state"],stdout=subprocess.PIPE)
	while True:
		line = proc.stdout.readline()
		if line != '': #Continue while there's more output to parse
			if 'closed' in line.rstrip():
				logger.info('LID Status: closed (' + line.rstrip() + ')')
				return 'closed'
			else:
				logger.info('LID Status: open (' + line.rstrip() + ')')
				return 'open'
		else:
			break

def get_AC_status():
	#eg: acpi
	proc = subprocess.Popen(["acpi"],stdout=subprocess.PIPE)
	while True:
		line = proc.stdout.readline()
		if line != '': #Continue while there's more output to parse
			if 'Discharging' in line.rstrip():
				logger.info('AC Status: battery (' + line.rstrip() + ')')
				return 'battery'
			else:
				logger.info('AC Status: AC (' + line.rstrip() + ')')
				return 'AC'
		else:
			break


#Check for RTC wakeup jobs, that can be scheduled to bring your computer out of suspend/hibernate
def check_for_rtc_wakeup_alarms():
	#eg: cat /sys/class/rtc/rtc0/wakealarm
	proc = subprocess.Popen(["cat", "/sys/class/rtc/rtc0/wakealarm"],stdout=subprocess.PIPE)
	while True:
		line = proc.stdout.readline()
		if line != '': #Continue while there's more output to parse
			logger.info('RTC WakeAlarm: ' + line.rstrip() )
		else:
			break


def get_X_idle_time():
	#eg: xprintidle
	os.environ["DISPLAY"] = ":0.0"
	proc = subprocess.Popen(["xprintidle"],stdout=subprocess.PIPE)
	line = proc.stdout.readline().rstrip()
	logger.info('X Idle Time: ' + line.rstrip() )
	return(int(line.rstrip())/1000 )

#####  MAIN ######

enforce_not_wakeup_trigger('LID')
enforce_not_wakeup_trigger('SLPB')
enforce_not_wakeup_trigger('IGBE')
enforce_not_wakeup_trigger('EXP2')
enforce_not_wakeup_trigger('XHCI')
enforce_not_wakeup_trigger('EHC1')
enforce_not_wakeup_trigger('EHC2')
enforce_not_wakeup_trigger('HDEF')

check_for_rtc_wakeup_alarms()

idle_seconds = get_X_idle_time()
lid_status = get_lid_status()
ac_status = get_AC_status()

if (lid_status == 'closed'  or  idle_seconds > 600)  and  ac_status == 'battery':
	logger.warning('Initiating suspend - lid_status: ' + lid_status + ' - idle_seconds:' + str(idle_seconds) + ' - ac_status: ' + ac_status)
	try:
		subprocess.call(["/usr/sbin/pm-suspend"])
	except Exception, e:
		logger.error(e)


