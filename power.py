import threading
import time
from prometheus_client import Gauge, Counter
from power_snmp import PowerSNMP

class PowerDevice():
    def __init__(self, debug: bool = False, ip_addr: str = None, user: str = None) -> None:
        self._fan_power_on = False
        self._heater_power_on = False
        self.fan_power_usage_gauge = Gauge('saltwater_fan_power_usage', 'Fan Power Usage')
        self.fan_power_on_counter = Counter('saltwater_fan_power_on_count', 'Fan Power On')
        self.fan_power_on_time_length_gauge = Gauge('saltwater_fan_power_on_length', 'Fan Power On Length')
        self.fan_on_gauge = Gauge('saltwater_fan_on', "Fan Power State")
        self.heater_power_usage_gauge = Gauge('saltwater_heater_power_usage', 'Heater Power Usage')
        self.heater_power_on_counter = Counter('saltwater_heater_power_on_count', 'Heater Power On')
        self.heater_power_on_time_length_gauge = Gauge('saltwater_heater_power_on_length', 'Heater Power On Length')
        self.heater_on_gauge = Gauge('saltwater_heater_on', "Heater Power State")
        self._heater_power_on_time_start = 0
        self._fan_power_on_time_start = 0
        self._debug = debug
        self._snmp = PowerSNMP(ip_addr, user)
        self._outlet_state_oid = "1.3.6.1.4.1.850.1.1.3.2.3.3.1.1.4.1"
        self._outlet_command_oid = "1.3.6.1.4.1.850.1.1.3.2.3.3.1.1.6.1"
        self._fan_state_oid = f'{self._outlet_state_oid}.1'
        self._fan_command_oid = f'{self._outlet_command_oid}.1'
        self._heater_state_oid = f'{self._outlet_state_oid}.2'
        self._heater_command_oid = f'{self._outlet_command_oid}.2'
    
    @property
    def fan_power_state(self) -> bool:
        return self._fan_power_on
        
    @property
    def heater_power_state(self) -> bool:
        return self._heater_power_on
    
    def check_power_states(self, loop: bool = True):
        while True:
            fan_state = self.get_load_state(self._fan_state_oid)
            heater_state = self.get_load_state(self._heater_state_oid)
            if fan_state == 2:
                self._fan_power_on = True
            elif fan_state == 1:
                self._fan_power_on = False
                
            if heater_state == 2:
                self._heater_power_on = True
            elif fan_state == 1:
                self._heater_power_on = False
                
            if not loop:
                False
                return
            
            time.sleep(30)
    
    def turn_heater_on(self):
        print("Turning heater on")
        self.set_load_state(self._heater_command_oid, "on")
        self._heater_power_on = True
        self._heater_power_on_time_start = time.time()
        self.heater_power_on_counter.inc()
        self.heater_on_gauge.set(1)
        
        
    def turn_heater_off(self):
        print("Turning heater off")
        self.set_load_state(self._heater_command_oid, "off")
        self._heater_power_on = False
        self.heater_power_on_time_length_gauge.set(time.time() - self._fan_power_on_time_start)
        self._heater_power_on_time_start = 0
        self.heater_on_gauge.set(0)
        
    def turn_fan_on(self):
        print("Turning fan on")
        self.set_load_state(self._fan_command_oid, "on")
        self._fan_power_on = True
        self.fan_power_on_counter.inc()
        self._fan_power_on_time_start = time.time()
        self.fan_on_gauge.set(1)
        
    def turn_fan_off(self):
        print("Turning fan off")
        self.set_load_state(self._fan_command_oid, "off")
        self._fan_power_on = False
        self.fan_power_on_time_length_gauge.set(time.time() - self._fan_power_on_time_start)
        self._fan_power_on_time_start = 0
        self.fan_on_gauge.set(0)
        
    def get_load_state(self, oid):
        output = self._snmp.get(oid)
        print(output[oid])
        return output[oid]
    
    def set_load_state(self, oid, state):
        if state == "on":
            value = 2
        elif state == "off":
            value = 1
        output = self._snmp.set(oid, value)
        return output

    # def read_fan_power_usage():
    #     usage_rt = smart_strip.children[fan_plug_num-1].emeter_realtime
    #     fan_power_usage_gauge.set(usage_rt)

    def init_power(self):
        try:
            print("--Loading current power states--")
            self.check_power_states(False)
            print("")
            print(f"Fan: {self.fan_power_state}")
            print(f"Heater: {self.heater_power_state}")
            print("")
            
            changed_initial_state = False
            if self.fan_power_state:
                self.turn_fan_off()
                changed_initial_state = True
            if self.heater_power_state:
                self.turn_heater_off()
                changed_initial_state = True
            
            if changed_initial_state:
                print("--Loading new power states--")
                print(f"Fan: {self.fan_power_state}")
                print(f"Heater: {self.heater_power_state}")
                print("")
                
            threading.Thread(target=self.check_power_states).start()
                
        except Exception as e:
            print(e)
            raise Exception("Error initializing power devices")
