from influxdb import InfluxDBClient

INFLUXDB_ADDRESS = '192.168.77.2'
INFLUXDB_USER = 'reporting'
INFLUXDB_PASSWORD = 'reporting123'
INFLUXDB_DATABASE = 'reporting'

influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8083, INFLUXDB_USER, INFLUXDB_PASSWORD, None)


if __name__ == '__main__':
    # {'key': 'LaCrosse-TX141W,channel=0,id=437126'}
    print('POC')
    temp = 0
    influxdb_client.switch_database(INFLUXDB_DATABASE)
    result = influxdb_client.query(("SELECT %s from %s ORDER by time DESC LIMIT 1") % ("temperature_C", "\"LaCrosse-TX141W\""))
    for measurement in result.get_points():
        temp = measurement['temperature_C']
        break
    print("temp: "+str(temp))


