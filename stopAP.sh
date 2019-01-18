#!/bin/bash

systemctl stop hostapd
systemctl stop dhcpcd
systemctl stop dnsmasq
sleep 1
