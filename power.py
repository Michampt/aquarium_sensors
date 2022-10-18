from ssl import Options
import threading
import time
from prometheus_client import Gauge, Counter
import pexpect

class PowerDevice():
    def __init__(self, debug: bool = False, ip_addr: str = None, passw: str = None, user: str = None, device: str = None) -> None:
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
        self._ip_addr = ip_addr
        self._telnet = None
        self._user = user
        self._passw = passw
        self._device_name = device
        self._fan_load_num = 1
        self._heater_load_num = 2
        self._logged_in = False
    
    @property
    def fan_power_state(self) -> bool:
        return self._fan_power_on
        
    @property
    def heater_power_state(self) -> bool:
        return self._heater_power_on
        
    @property
    def pdu_ip(self) -> str:
        return self._ip_addr
    
    @property
    def logged_in(self) -> bool:
        return self._logged_in
    
    def check_power_states(self, loop: bool = True):
        while True:
            fan_state = self.get_load_state(self._fan_load_num).strip()
            heater_state = self.get_load_state(self._heater_load_num).strip()
            if fan_state == "on":
                self._fan_power_on = True
            elif fan_state == "off":
                self._fan_power_on = False
                
            if heater_state == "on":
                self._heater_power_on = True
            elif fan_state == "off":
                self._heater_power_on = False
                
            if not loop:
                False
                return
            
            time.sleep(30)
    
    def turn_heater_on(self):
        print("Turning heater on")
        self.set_load_state(self._heater_load_num, "on")
        self._heater_power_on = True
        self._heater_power_on_time_start = time.time()
        self.heater_power_on_counter.inc()
        self.heater_on_gauge.set(1)
        
        
    def turn_heater_off(self):
        print("Turning heater off")
        self.set_load_state(self._heater_load_num, "off")
        self._heater_power_on = False
        self.heater_power_on_time_length_gauge.set(time.time() - self._fan_power_on_time_start)
        self._heater_power_on_time_start = 0
        self.heater_on_gauge.set(0)
        
    def turn_fan_on(self):
        print("Turning fan on")
        self.set_load_state(self._fan_load_num, "on")
        self._fan_power_on = True
        self.fan_power_on_counter.inc()
        self._fan_power_on_time_start = time.time()
        self.fan_on_gauge.set(1)
        
    def turn_fan_off(self):
        print("Turning fan off")
        self.set_load_state(self._fan_load_num, "off")
        self._fan_power_on = False
        self.fan_power_on_time_length_gauge.set(time.time() - self._fan_power_on_time_start)
        self._fan_power_on_time_start = 0
        self.fan_on_gauge.set(0)
        
    def get_load_state(self, load_num):
        output = self.send_command(f"show load {load_num}", f"\({self._device_name}\)> ")
        output_lines = output.split("\n")
        state = ""
        for line in output_lines:
            if "State" in line.strip():
                state = line.split(":")[1].replace(" ", "")
        return state
    
    def set_load_state(self, load_num, state):
        self.send_command(f"load {load_num}", f"load \({load_num}\)> ")
        self.send_command(f"{state}", "proceed: ")
        self.send_command(f"yes", f"load \({load_num}\)> ")
        self.send_command(f"end", f"device \({self._device_name}\)> ")
        
    
    def send_command(self, command: str, expect: str) -> str:
        self._telnet.sendline(command)
        index = self._telnet.expect([expect, f"Farewell {self._user}", "Connection closed by foreign host.", "Quitting shell..."])
        if index == 0:
            return bytes(self._telnet.before).decode('ascii')
        elif index in [1, 2, 3]:
            self._logged_in = False
            self.telnet_login()
            self.connect_device()
            
    
    def telnet_login(self):
        print(f"Logging in as {self._user}")
        self._telnet.expect("login: ")
        self._telnet.sendline(self._user)
        self._telnet.expect("Password: ")
        self._telnet.sendline(self._passw)
        print(f"Awaiting login completion...")
        self._telnet.expect(f"{self._user}> ")
        self._logged_in = True
        print("Login successful")
        
    def connect_device(self):
        print(f"Connecting to device {self._device_name}")
        self.send_command(f"device {self._device_name}", f"device \({self._device_name}\)> ")
        self._logged_in = True

    # def read_fan_power_usage():
    #     usage_rt = smart_strip.children[fan_plug_num-1].emeter_realtime
    #     fan_power_usage_gauge.set(usage_rt)

    def init_power(self):
        try:
            print("Initializing power devices")
            
            print(f"Opening Telnet connection to {self.pdu_ip}")
            self._telnet = pexpect.spawn(f'telnet {self.pdu_ip}')
            self.telnet_login()
            self.connect_device()
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
