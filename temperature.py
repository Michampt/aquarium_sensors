import glob
from prometheus_client import Gauge

class TemperatureSensor():
    def __init__(self, debug: bool = False) -> None:
        self._current_temperature = 0.0
        temp_sensor_base_dir = '/sys/bus/w1/devices/'
        temp_sensor_device_dir = glob.glob(temp_sensor_base_dir + '28*')[0]
        temp_sensor_device_file = temp_sensor_device_dir + '/w1_slave'
        self._temperature_device = temp_sensor_device_file
        self._debug = False
        self._temperature_counter = Gauge('saltwater_temperature', 'Temperature Gauge')
        
    @property
    def temp_device(self):
        return self._temperature_device
    
    @property
    def current_temperature(self):
        return self._current_temperature
    
    @current_temperature.setter
    def current_temperature(self, temp):
        self._current_temperature = temp
        
    def read_temp_raw(self) -> float:
        with open(self.temp_device, 'r') as temp_device_raw:
            lines = temp_device_raw.readlines()
            if lines[0].strip()[-3:] == 'YES':
                t = lines[1].find('t=')
                if t != -1:
                    temp_string = lines[1][t+2:]
                    temp_c = float(temp_string) / 1000.0
                    temp_f = temp_c * 9.0 / 5.0 + 32.0
                    return temp_f
                else:
                    return None
            else:
                return None
        
    def read_temperature(self):
        temp = self.read_temp_raw()
            
        if temp == None:
            raise Exception("Could not read temperature")
        
        if self._debug:
            print(f"Current Temp: {self.current_temperature}")
        
        self.current_temperature = temp
        self._temperature_counter.set(self.current_temperature)
        
        
                