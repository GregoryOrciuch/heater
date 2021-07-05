import json
import logging
import re
import smbus2
import bme280
from datetime import datetime, time
from time import sleep

import requests


def get_bme_temp():
    try:
        port = 1
        address = 0x76
        bus = smbus2.SMBus(port)

        calibration_params = bme280.load_calibration_params(bus, address)

        # the sample method will take a single reading and return a
        # compensated_reading object
        data = bme280.sample(bus, address, calibration_params)
        return round(data.temperature, 2)
    except IOError as e:
        log.error("Cannot communicate with BME, error: "+str(e))
        return 0.0


def write_state(state, device):
    with open(device+'_state.json', 'w') as outfile:
        json.dump(state, outfile)


def read_state(device):
    with open(device+'_state.json') as json_file:
        state = json.load(json_file)
        return state


def turn_on_device(device_ip, component, device):
    result = requests.get("http://" + device_ip + "/cm?cmnd="+component+"%20ON")
    data = json.loads(result.content)
    state = str(data[component])
    if state.lower() == 'ON'.lower():
        log.info("Turn-on OK: "+device_ip)
        state = {'turn-on-time': str(datetime.now().isoformat())}
        write_state(state,device)
        return True
    else:
        return False


def turn_off_device(device_ip, component, device):
    result = requests.get("http://" + device_ip + "/cm?cmnd="+component+"%20OFF")
    data = json.loads(result.content)
    state = str(data[component])
    if state.lower() == 'OFF'.lower():
        log.info("Turn-off OK: "+device_ip)
        state = {'turn-off-time': str(datetime.now().isoformat())}
        write_state(state, device)
        return True
    else:
        return False


def get_relay_state(device_ip, component):
    result = requests.get("http://" + device_ip + "/cm?cmnd="+component)
    data = json.loads(result.content)
    state = str(data[component])
    if state.lower() == 'ON'.lower():
        return True
    else:
        return False


def get_temp():
    result = requests.get("http://"+HEATER_IP+"/cm?cmnd=Status%2010")
    data = json.loads(result.content)
    temp = data['StatusSNS']['DS18B20']['Temperature']
    return temp


def get_voltage():
    result = requests.get("http://localhost:8080/munin", timeout=2)
    m = re.findall("volt.value \d+\.\d+", str(result.content))
    voltage = float(m[0].split()[1])
    return voltage


def test_procedure():
    try:
        state = read_state()
        if 'turn-on-time' in state:
            turn_on_time = datetime.fromisoformat(state['turn-on-time'])
            log.info("Last turn on time was: "+turn_on_time.isoformat())
        else:
            log.info("Turn on time was not found")
    except FileNotFoundError as e:
        log.info("Heater state was not found")

    try:
        state = read_state()
        if 'turn-off-time' in state:
            turn_off_time = datetime.fromisoformat(state['turn-off-time'])
            log.info("Last turn off time was: " + turn_off_time.isoformat())
        else:
            log.info("Turn off time was not found")
    except FileNotFoundError as e:
        log.info("Heater state was not found")

    temp = get_temp()
    log.info("t: "+str(temp))
    voltage = get_voltage()
    log.info("v: "+str(voltage))

    log.info("testing... turn on")
    was_on = turn_on_device(HEATER_IP, "POWER", "heater")
    if not was_on:
        raise Exception("Unable to turn on the heater")
    log.info("Sleeping 5 sec, and turn off...")
    sleep(5)

    was_off = turn_off_device(HEATER_IP, "POWER", "heater")
    if not was_off:
        raise Exception("Unable to turn off the heater")

    log.info("test is finished")


def operation():
    log.info("-------starting-------")
    temp = get_temp()
    log.info("t: " + str(temp))
    voltage = get_voltage()
    log.info("v: " + str(voltage))

    current_state_vent = get_relay_state(VENT_IP, "POWER1")
    if current_state_vent:
        log.info("vent:ON")
    else:
        log.info("vent:OFF")

    bme_temp = get_bme_temp()
    log.info("bme: " + str(bme_temp))
    if bme_temp > 36.0:
        log.info("Turning ON the Vent, temp over 36.0 C")
        turn_on_device(VENT_IP, "POWER1", "vent")

    if bme_temp < 35.0:
        log.info("Turning OFF the Vent, temp below 35.0 C")
        turn_off_device(VENT_IP, "POWER1", "vent")

    start = time(9)
    end = time(15)
    now_time = datetime.now().time()
    if start <= now_time <= end:
        log.info("we are in time range 9-15, can continue")
    else:
        log.info("Outside working time range 9-15, exiting")
        turn_off_device(HEATER_IP, "POWER", "heater")
        exit()

    current_state_heater = get_relay_state(HEATER_IP, "POWER")
    if current_state_heater:
        log.info("h:ON")
    else:
        log.info("h:OFF")

    if temp > 65:
        log.info("Temp above 65. Turn off.")
        turn_off_device(HEATER_IP, "POWER", "heater")
        exit()

    # if v>28.5 and v< 28.9, turn on the heater for next 30min
    try:
        state = read_state()
        if 'turn-on-time' in state:
            turn_on_time = datetime.fromisoformat(state['turn-on-time'])
            log.info("Last turn on time was: "+turn_on_time.isoformat())
            minutes_diff = (datetime.now() - turn_on_time).total_seconds() / 60.0
            if minutes_diff > HEATER_MAX_RUN_MIN:
                log.info("Heating time has passed")
                turn_off_device(HEATER_IP, "POWER", "heater")
            else:
                log.info("Doing nothing, should remain ON, but measure voltage. Minutes left: "+str(int(HEATER_MAX_RUN_MIN-minutes_diff)))
                if voltage < 28.1:
                    log.info("Voltage 28.1, turning off")
                    turn_off_device(HEATER_IP, "POWER", "heater")

        else:
            log.info("Turn on time was not found")

        if 'turn-off-time' in state:
            turn_off_time = datetime.fromisoformat(state['turn-off-time'])
            log.info("Last turn off time was: " + turn_off_time.isoformat())
            minutes_diff = (datetime.now() - turn_off_time).total_seconds() / 60.0
            if minutes_diff > HEATER_MAX_COOLDOWN_MIN:
                # turn on if voltage is good
                if voltage > 28.50:
                    log.info("heater was cooled down, voltage is good, turning on for min: "+str(HEATER_MAX_RUN_MIN))
                    turn_on_device(HEATER_IP, "POWER", "heater")
                else:
                    log.info("voltage not in desired range")
                    if current_state_heater:
                        log.info("heater found in ON state, turning off")
                        turn_off_device(HEATER_IP, "POWER", "heater")
            else:
                log.info("Cooldown time not met, doing nothing.")

        else:
            log.info("Turn off time was not found")

    except FileNotFoundError as e:
        log.info("Heater state was not found")

    log.info("-------end-------")


if __name__ == '__main__':
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    log = logging.getLogger()
    log.setLevel(logging.getLevelName('INFO'))

    logPath = "/var/log"
    fileName = "heater"
    fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
    fileHandler.setFormatter(logFormatter)
    log.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    log.addHandler(consoleHandler)

    VENT_IP = "192.168.0.119"
    HEATER_IP = "192.168.0.118"
    HEATER_MAX_RUN_MIN = 15
    HEATER_MAX_COOLDOWN_MIN = 1
    #test_procedure()
    operation()
