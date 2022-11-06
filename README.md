# Temperature Sensor Tool

This is a personal project used to manage a saltwater tank's sensors + control different units via a managed PDU.

## Hardware
---

[Tripp-Lite PDU15NETLX](https://www.amazon.com/dp/B07CXBJ5MX?psc=1&ref=ppx_yo2ov_dt_b_product_details)  
[Temperature Sensor](https://www.amazon.com/dp/B087JQ6MCP?psc=1&ref=ppx_yo2ov_dt_b_product_details)  
[Aquarium Fans](https://www.amazon.com/dp/B085LM313D?psc=1&ref=ppx_yo2ov_dt_b_product_details)*  
[Fluval Heater](https://www.amazon.com/Fluval-Submersible-Glass-Aquarium-Heater/dp/B0027VMPXA/ref=sr_1_4?crid=3VIDA1WXOLMZT&keywords=fluval+heater&qid=1666112001&qu=eyJxc2MiOiIzLjkzIiwicXNhIjoiMy4zMCIsInFzcCI6IjIuOTUifQ%3D%3D&s=pet-supplies&sprefix=fluval+heate%2Cpets%2C149&sr=1-4)*  
[Raspberry Pi 4](https://www.amazon.com/Raspberry-Model-2019-Quad-Bluetooth/dp/B07TC2BK1X/ref=sr_1_3?keywords=raspberry+pi+4&qid=1666112024&qu=eyJxc2MiOiI2LjIxIiwicXNhIjoiNi4xNSIsInFzcCI6IjUuNTEifQ%3D%3D&sr=8-3&ufe=app_do%3Aamzn1.fos.18ed3cb5-28d5-4975-8bc7-93deae8f9840)**

\* Any fans or heater is fine  
\*\* Any Raspberry Pi will do

## Temperature Sensor Connection
---

I connected the sensor as such:
- 3.3v | pin 1
- ground | pin 6
- data | pin 7


```
# /boot/config.txt - Set dtoverlay
...
dtoverlay=w1-gpio
...
```

```
sudo modprobe w1-gpio
sudo modprobe w1-therm
```

The file to monitor: ```/sys/bus/w1/devices/28-000007602ffa/w1_slave```

## PDU
---
I have the PDU communicating over telnet, using pexpect. If you ONLY want to utilize the sensor, just comment out the corresponding code that starts the pdu comms / monitoring. Maybe I'll make it a flag some day.


## Getting Started

Set up an SNMP user with snmpv3 enabled. I used a passwordless user (not recommended)

If everything's connected up and you have a telnet username/pw for the PDU:  
``` python main.py --pdu_ip_addr <ip_address> -u <snmp_user>```


## Prometheus

The service comes with a prometheus server that you can scrape however you see fit.
If you'd like to utilize grafana, there is a grafana json file in /grafana

**Note**: The prometheus variables are based on a saltwater tank, so the names all start with saltwater. Feel free to change it as you see fit, but you'll need to update the dashboard as well.