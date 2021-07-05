import smbus2
import bme280

try:
    port = 1
    address = 0x76
    bus = smbus2.SMBus(port)

    calibration_params = bme280.load_calibration_params(bus, address)

    # the sample method will take a single reading and return a
    # compensated_reading object
    data = bme280.sample(bus, address, calibration_params)

    # the compensated_reading class has the following attributes
    #print(data.id)
    #print(data.timestamp)
    #print(data.temperature)
    #print(data.pressure)
    #print(data.humidity)

    # there is a handy string representation too
    #print(data)

    print("temp "+str(round(data.temperature, 3)))
    print("pres "+str(round(data.pressure, 3)))
    print("hum "+str(round(data.humidity, 3)))

except Exception as e:
    print("error:"+str(e))
