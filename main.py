#! /usr/bin/python

import threading
import time
import argparse
import logging
from prometheus_client import start_http_server
from power import PowerDevice
from temperature import TemperatureSensor

debug = False
logger = None
ARGS = None

cold_threshold = 77.5
hot_threshold = 78.5
ideal_temp = 78.0


def init_prometheus_server():
    logger.info("Starting prometheus metrics server")
    start_http_server(8080)
    logger.info("Prometheus metrics available on port 8080 /metrics")
    
    
def temperature_reader_thread(ts: TemperatureSensor):
    while True:
        ts.read_temperature()
        time.sleep(5)


def temperature_management_thread(pd: PowerDevice, ts: TemperatureSensor):
    while True:
        if ts.current_temperature >= hot_threshold and not pd.fan_power_state:
            pd.turn_fan_on()
        if ts.current_temperature <= ideal_temp and pd.fan_power_state:
            pd.turn_fan_off()
        if ts.current_temperature >= ideal_temp and pd.heater_power_state:
            pd.turn_heater_off()
        if ts.current_temperature <= cold_threshold and not pd.heater_power_state:
            pd.turn_heater_on()
        time.sleep(5)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdu_ip_addr', required=True, help="IP Address of Tripp-Lite PDU")
    parser.add_argument('-u', '--username', required=True, help="Username for telnet to PDU")
    parser.add_argument('--debug', required=False, help="Debug", default=False)
    ARGS = parser.parse_args()
    try:
        debug = ARGS.debug
        if debug:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO

        logging.basicConfig(level=log_level, format='%(module)s %(levelname)s %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        logger = logging.getLogger('swsensors')
        
        ts = TemperatureSensor()
        pd = PowerDevice(ARGS.pdu_ip_addr, ARGS.username)
        
        logger.info("Starting Saltwater Sensor Server")
        pd.init_power()
    
        logger.info(f"Temperature Thresholds")
        
        logger.info(f"High: {hot_threshold}")
        logger.info(f"Low: {cold_threshold}")
        logger.info(f"Ideal: {ideal_temp}")
        
        logger.info("Retrieving Current Temperature")
        ts.read_temperature()
    
        logger.info(f"Current Temperature: {ts.current_temperature}")
        
        init_prometheus_server()
        
        temp_thread = threading.Thread(target=temperature_reader_thread, args=[ts])
        temp_thread.start()
        
        time.sleep(5)
        
        tm_thread = threading.Thread(target=temperature_management_thread, args=[pd, ts])
        tm_thread.start()
    except Exception as err:
        logging.error(err)
