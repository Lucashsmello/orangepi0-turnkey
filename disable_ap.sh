#!/bin/bash

systemctl stop hostapd dhcpcd dnsmasq
#systemctl stop NetworkManager

# enable the AP
sudo cp config/hostapd /etc/default/hostapd
sudo cp config/dhcpcd.conf /etc/dhcpcd.conf
sudo cp config/dnsmasq.conf /etc/dnsmasq.conf

nmcli radio wifi on
sleep 2
systemctl restart NetworkManager
sleep 2
