#!/bin/bash

systemctl stop hostapd
systemctl stop dhcpcd
systemctl stop dnsmasq

# enable the AP
sudo cp config/hostapd /etc/default/hostapd
sudo cp config/dhcpcd.conf /etc/dhcpcd.conf
sudo cp config/dnsmasq.conf /etc/dnsmasq.conf

# load wlan configuration
sudo cp wpa.conf /etc/wpa_supplicant/wpa_supplicant.conf

systemctl daemon-reload
./startAP.sh

#sudo reboot now
