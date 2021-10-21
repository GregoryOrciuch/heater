from influxdb import InfluxDBClient

INFLUXDB_ADDRESS = '192.168.77.2'
INFLUXDB_USER = 'reporting'
INFLUXDB_PASSWORD = 'reporting123'
INFLUXDB_DATABASE = 'reporting'

influxdb_client = InfluxDBClient(INFLUXDB_ADDRESS, 8083, INFLUXDB_USER, INFLUXDB_PASSWORD, None)


if __name__ == '__main__':
    print('MQTT to InfluxDB bridge is running')
    result = influxdb_client.query("SHOW SERIES")

    print(result)
