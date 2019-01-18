#!/bin/bash

systemctl daemon-reload
systemctl restart hostapd
systemctl restart dhcpcd
systemctl restart dnsmasq
