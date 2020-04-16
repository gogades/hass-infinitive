# Infinitive Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Hey!  This integration started when I purchased a new home. It's HVAC is a Bryant unit.  Sure enough, I bought a house with one of the 5% of units that isn't compatible with Nest thermostats, or any other type of smart thermostat for that matter.  The Bryant/Carrier units like mine use a proprietary serial protocol called Infinity to communicate with the thermostat.  I started my research on potential options for automation and found the Infinitive project.  I had wanted to dig deeper into python so an HA integration with Infinitive seemed like the perfect opportunity.  Below are the steps to get you started...

## Installation Steps:

 1. Buy a Raspberry Pi (Don’t forget to get a micro SD card for it). I'm running mine on a Pi Zero with no issues.
[Here's the Pi Zero I purchased](https://www.amazon.com/gp/product/B072N3X39J/)
2. Buy a RS-485 USB adapter 11 for the Raspberry Pi.
[Here's the RS-485 USB adapter I purchased](https://www.amazon.com/gp/product/B076WVFXN8/)
3. Buy some wire. I think 14/2 romex wire is what I used.  You should be able to pick it up at your local hardware store.  You need enough to reach from your HVAC unit system board to the location of your RS-485 adapter.
4. Flash the latest Lite version of Raspbian to your SD card - Try [Belana Etcher](https://www.balena.io/etcher/) if you need an application that can write the Raspbian image to the SD card.
5. Setup Raspbian install to have a static IP on your network.
6. Once the Pi is on your network, running the folowing: 

```apt-get install git
apt-get install golang-go
export GOPATH = /root/go
go get github.com/Will1604/infinitive
go build github.com/Will1604/infinitive
```

7. Place this file at /etc/systemd/system/infinitive.service:
*Note:  if your RS-485 adapter does not show up as /dev/ttyUSB0 please adjust the file below to reflect the proper device name*

```
[Unit]
Description=Infinitive Service
After=network.target
StartLimitIntervalSec=0
[Service]
Type=simple
Restart=always
RestartSec=1
User=root
ExecStart=/root/go/bin/infinitive -httpport=8080 -serial=/dev/ttyUSB0
[Install]
WantedBy=multi-user.target
```
8. After the infinitive.service file has been created run the following:
```
systemctl enable infinitive
systemctl start infinitive
```
9. Run ```systemctl status infinitive``` to ensure that the service is running.
10. If all went well you should be able to browse to **http://[rasbperry_pi_IP]:8080** and be presented with the Infinitive web interface.

## PLEASE KILL POWER TO YOUR HVAC UNIT WHILE YOU'RE WORKING ON IT.
11. Using the thermostat wire, connect one end to the RS-485 adapter as shown in the pictures below.
- Green wire connects to the A port
- Yellow wire connect to the B port
![Pi RS-485 adapter connection](https://raw.githubusercontent.com/mww012/mww012.github.io/master/32cd71b515e2ae1436048976d6f6e33c6790abd7.jpeg)![RS-485 adapter detail](https://raw.githubusercontent.com/mww012/mww012.github.io/master/708F50C1-0CBF-4CE7-87A8-468409863C49.jpeg)
![Carrier/Bryant system board](https://raw.githubusercontent.com/mww012/mww012.github.io/master/E11C5752-1FD6-4E68-A898-A77C1B9C6B9B.jpeg)
## POWER CAN BE TURNED BACK ON TO THE HVAC UNIT FOR TESTING

12. At this point you can check the Infinitive web interface and ensure that it's populating with the data.  If it's not please reach out and I'll try to help where I can.

13. Install and setup HACS if you don't already have it.  Here's a link to the [HACS Install Process](https://hacs.xyz/docs/installation/prerequisites).

14. Open the HACS page in Home Assitant, click the Settings tab.

15. Add ```https://github.com/mww012/hass-infinitive.git``` as an ```integration``` under Custom Repositories.

16. Click the Integrations tab and search for "infinitive".  Click on the Infinitive integration, then click Install.

17. Add this to your configuration.yaml and restart:
```
climate:
  - platform: infinitive
  host: [Raspberry Pi IP]
  port: 8080
```

18. Restart Home Assistant.

19. Your HVAC unit should show up in Home Assistant with entity_id climate.infinitive_thermostat.  Good job!

If any problems arise please feel free to open an issue.



