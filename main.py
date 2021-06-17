import json
import re
from datetime import datetime
from time import sleep

import requests


def write_state(state):
    with open('heater_state.json', 'w') as outfile:
        json.dump(state, outfile)


def read_state():
    with open('heater_state.json') as json_file:
        state = json.load(json_file)
        return state

def turn_on():
    result = requests.get("http://" + HEATER_IP + "/cm?cmnd=Power%20ON")
    data = json.loads(result.content)
    state = str(data['POWER'])
    if state.lower() == 'ON'.lower():
        print("Turn-on OK.")
        state = {'turn-on-time': str(datetime.now().isoformat())}
        write_state(state)
        return True
    else:
        return False


def turn_off():
    result = requests.get("http://" + HEATER_IP + "/cm?cmnd=Power%20OFF")
    data = json.loads(result.content)
    state = str(data['POWER'])
    if state.lower() == 'OFF'.lower():
        print("Turn-off OK.")
        state = {'turn-off-time': str(datetime.now().isoformat())}
        write_state(state)
        return True
    else:
        return False


def get_relay_state():
    result = requests.get("http://" + HEATER_IP + "/cm?cmnd=Power")
    data = json.loads(result.content)
    state = str(data['POWER'])
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
    result = requests.get("http://localhost:8080/munin")
    m = re.findall("volt.value \d+\.\d+", str(result.content))
    voltage = float(m[0].split()[1])
    return voltage


def test_procedure():
    try:
        state = read_state()
        if 'turn-on-time' in state:
            turn_on_time = datetime.fromisoformat(state['turn-on-time'])
            print("Last turn on time was: "+turn_on_time.isoformat())
        else:
            print("Turn on time was not found")
    except FileNotFoundError as e:
        print("Heater state was not found")

    try:
        state = read_state()
        if 'turn-off-time' in state:
            turn_off_time = datetime.fromisoformat(state['turn-off-time'])
            print("Last turn off time was: " + turn_off_time.isoformat())
        else:
            print("Turn off time was not found")
    except FileNotFoundError as e:
        print("Heater state was not found")


    temp = get_temp()
    print("t: "+str(temp))
    voltage = get_voltage()
    print("v: "+str(voltage))

    print("testing... turn on")
    was_on = turn_on()
    if not was_on:
        raise Exception("Unable to turn on the heater")
    print("Sleeping 5 sec, and turn off...")
    sleep(5)

    was_off = turn_off()
    if not was_off:
        raise Exception("Unable to turn off the heater")

    print("test is finished")


def operation():
    temp = get_temp()
    print("t: " + str(temp))
    voltage = get_voltage()
    print("v: " + str(voltage))

    current_state = get_relay_state()
    if current_state:
        print("h:ON")
    else:
        print("h:OFF")

    # if v>28.5 and v< 28.9, turn on the heater for next 30min
    try:
        state = read_state()
        if 'turn-on-time' in state:
            turn_on_time = datetime.fromisoformat(state['turn-on-time'])
            print("Last turn on time was: "+turn_on_time.isoformat())
            minutes_diff = (datetime.now() - turn_on_time).total_seconds() / 60.0
            if minutes_diff > HEATER_MAX_RUN_MIN:
                print("Heating time has passed")
                turn_off()
            else:
                print("Doing nothing, should remain ON")
                turn_on()
        else:
            print("Turn on time was not found")

        if 'turn-off-time' in state:
            turn_off_time = datetime.fromisoformat(state['turn-off-time'])
            print("Last turn off time was: " + turn_off_time.isoformat())
            minutes_diff = (datetime.now() - turn_off_time).total_seconds() / 60.0
            if minutes_diff > HEATER_MAX_COOLDOWN_MIN:
                # turn on if voltage is good
                if voltage > 28.50:
                    print("heater was cooled down, voltage is good, turning on for min: "+str(HEATER_MAX_RUN_MIN))
                    turn_on()
                else:
                    print("voltage not in desired range")
            else:
                print("Cooldown time not met, doing nothing.")

        else:
            print("Turn off time was not found")

    except FileNotFoundError as e:
        print("Heater state was not found")



if __name__ == '__main__':

    HEATER_IP = "192.168.0.118"
    HEATER_MAX_RUN_MIN = 5
    HEATER_MAX_COOLDOWN_MIN = 1
    #test_procedure()
    operation()
