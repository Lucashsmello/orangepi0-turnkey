#!/bin/bash

systemctl stop hostapd dhcpcd dnsmasq
#systemctl stop NetworkManager
nmcli radio wifi off
rfkill unblock wlan

# enable the AP
sudo cp config/hostapd /etc/default/hostapd
sudo cp config/dhcpcd.conf /etc/dhcpcd.conf
sudo cp config/dnsmasq.conf /etc/dnsmasq.conf

systemctl restart dhcpcd dnsmasq
sleep 1
systemctl restart hostapd

#sudo reboot now
