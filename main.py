import json
import re
import requests


def turn_on():
    result = requests.get("http://" + HEATER_IP + "/cm?cmnd=Power%20ON")
    data = json.loads(result.content)
    state = str(data['POWER'])
    if state.lower() == 'ON'.lower():
        return True
    else:
        return False


def turn_off():
    result = requests.get("http://" + HEATER_IP + "/cm?cmnd=Power%20OFF")
    data = json.loads(result.content)
    state = str(data['POWER'])
    if state.lower() == 'OFF'.lower():
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

def print_hi(name):

    temp = get_temp()
    print("t: "+str(temp))

    voltage = get_voltage()
    print("v: "+str(voltage))


if __name__ == '__main__':

    HEATER_IP = "192.168.0.118"

    print_hi('PyCharm')
