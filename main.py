#! /usr/bin/python

import threading
import time
import argparse
from typing_extensions import Required
from prometheus_client import start_http_server
from power import PowerDevice
from temperature import TemperatureSensor


debug = False
ARGS = None

cold_threshold = 77.5
hot_threshold = 78.5
ideal_temp = 78.0


def init_prometheus_server():
    print("Starting prometheus metrics server")
    start_http_server(8080)
    print("Prometheus metrics available on port 8080 /metrics")
    
    
def temperature_reader_thread(ts: TemperatureSensor):
    while True:
        ts.read_temperature()
        time.sleep(5)
        

def temperature_management_thread(pd: PowerDevice, ts: TemperatureSensor):
    while True:
        if debug:
            print(f"Current Temp: {ts.current_temperature}")
        if pd.logged_in:
            if ts.current_temperature >= hot_threshold and not pd.fan_power_state:
                pd.turn_fan_on()
            if ts.current_temperature <= ideal_temp and pd.fan_power_state:
                pd.turn_fan_off()
            if ts.current_temperature >= ideal_temp and pd.heater_power_state:
                pd.turn_heater_off()
            if ts.current_temperature <= cold_threshold and not pd.heater_power_state:
                pd.turn_heater_on()
        else:
            print("Cannot perform any actions until logged in")
        time.sleep(5)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdu_ip_addr', required=True, help="IP Address of Tripp-Lite PDU")
    parser.add_argument('-u', '--username', required=True, help="Username for telnet to PDU")
    parser.add_argument('-p', '--password', required=True, help="Password for telnet PDU")
    parser.add_argument('-d', '--device', required=True, help="PDU Device Name")
    ARGS = parser.parse_args()
    try:
        print(f"Debug: {debug}")
        ts = TemperatureSensor(debug)
        pd = PowerDevice(debug, ARGS.pdu_ip_addr, ARGS.password, ARGS.username, ARGS.device)
        
        print("Starting saltwater sensor server")
        pd.init_power()
        
        print("Retrieving initital temperature")
        ts.read_temperature()
        
        print(f"Current temperature: {ts.current_temperature}")
        
        init_prometheus_server()
        
        temp_thread = threading.Thread(target=temperature_reader_thread, args=[ts])
        temp_thread.start()
        
        time.sleep(5)
        
        tm_thread = threading.Thread(target=temperature_management_thread, args=[pd, ts])
        tm_thread.start()
    except Exception as err:
        print(err)
