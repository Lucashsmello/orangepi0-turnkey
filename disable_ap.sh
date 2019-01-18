#!/bin/bash

systemctl stop hostapd
systemctl stop dhcpcd
systemctl stop dnsmasq

# disable the AP
sudo cp config/hostapd.disabled /etc/default/hostapd
sudo cp config/dhcpcd.conf.disabled /etc/dhcpcd.conf
sudo cp config/dnsmasq.conf.disabled /etc/dnsmasq.conf

# load wlan configuration
sudo cp wpa.conf /etc/wpa_supplicant/wpa_supplicant.conf

systemctl daemon-reload
#sudo reboot now
