#!/bin/bash

#apt install -y dnsmasq hostapd python3-flask python3-requests git

if [ "$EUID" -ne 0 ]
  then echo "Please run with sudo/root"
  exit
fi

if [ "$1" == "--help" ]; then
    printf 'Usage:\t ./install.sh
     \t ./install.sh SSID PASSWORD
     \t ./install.sh --uninstall
     \t ./install.sh --help\n'
    exit
fi

MYSSID=ConnectToConnect
MYPWD=ConnectToConnect
SERVICE_NAME=turnkey.service
SERVICE_PATH=/etc/systemd/system/${SERVICE_NAME}
WORKDIR=`pwd`
EXEC_PATH=${WORKDIR}/startup.py

if [ "$1" == "--uninstall" ]; then
	echo "Uninstalling..."
	if [ -f $SERVICE_PATH ]; then
		systemctl stop $SERVICE_NAME
		systemctl disable $SERVICE_NAME
		rm $SERVICE_PATH
	fi
	exit
fi

if [ $# -ge 1 ]; then
    MYSSID=$1
    if [ $# -ge 2 ]; then
        if [ ${#2} -lt 8 ]; then
            echo "wpa key password must have at least 8 characters"
            exit 1
        fi
        MYPWD=$2
    fi
fi

systemctl disable systemd-resolved
systemctl stop hostapd dhcpcd dnsmasq
cp config/hostapd /etc/default/hostapd
cp config/dhcpcd.conf /etc/dhcpcd.conf
cp config/dnsmasq.conf /etc/dnsmasq.conf

echo "interface=wlan0
driver=nl80211
ssid=${MYSSID}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=${MYPWD}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP" > /etc/hostapd/hostapd.conf

SERVICE_CONTENT="[Unit]
Description=Turnkey Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/env python3 startup.py
WorkingDirectory=$WORKDIR

[Install]
WantedBy=multi-user.target"

if [ -f $SERVICE_PATH ]; then
    systemctl stop $SERVICE_NAME
	systemctl disable $SERVICE_NAME
fi
printf "$SERVICE_CONTENT" > $SERVICE_PATH

systemctl start hostapd dhcpcd dnsmasq
systemctl start $SERVICE_NAME
systemctl enable $SERVICE_NAME
