#!/bin/bash

printf "disable_ap.sh: stopping services...\n"
systemctl stop hostapd dnsmasq dhcpcd

printf "disable_ap.sh: loading disabled configuration files\n"
# disable the AP
sudo cp config/hostapd.disabled /etc/default/hostapd
sudo cp config/dhcpcd.conf.disabled /etc/dhcpcd.conf
sudo cp config/dnsmasq.conf.disabled /etc/dnsmasq.conf

printf "disable_ap.sh: loading wpa configuration\n"
# load wlan configuration
sudo cp wpa.conf /etc/wpa_supplicant/wpa_supplicant.conf

sleep 1
#systemctl daemon-reload
#sudo
