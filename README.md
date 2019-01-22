# Orange Pi Turnkey

Have you ever wanted to setup a Orange Pi Zero *without having to SSH or attach a keyboard* to add your WiFi credentials? This is particularly useful when you are making a Pi that needs to be deployed somewhere where supplying the credentials via SSH or attaching a keyboard isn't an option.

# Usage 

Once you boot the Pi, wait about 1 minute to start up the web server. Then you will see a WiFi AP named "ConnectToConnect" (password same). Connect to it and your browser should automatically redirect you to a sign-in page. If not, navigate to `192.168.4.1` where you'll see a login form. 

<p align="center">
  <img src="https://user-images.githubusercontent.com/6550035/36927004-9dd66774-1e2f-11e8-941a-aa192005b2d6.png"/>
</p>

When the WiFi credentials are entered onto the login form, the Pi will modify its internal NetworkManager configuration to conform to them so that it will be connected to the net. The Pi will then reboot itself using those WiFi credentials. If the credentials are not correct, then the Pi will reboot back into the AP mode to allow you to re-enter them again.

Once connected, you can recieve a message with the LAN IP for your Pi at https://snaptext.live (the specific URL will be given to you when you enter in the credentials to the form).

# How does it work?

When the Pi starts up it runs a Python script, `startup.py`. This script first checks if the Pi is online (by looking output of `iw dev wlan0 link`). If the Pi is online, the script sets the status as "connected" (saved to disk in `status.json`).

If the Pi is not online, it will start the AP mode (`hostapd` and `dnsmasq`) and the web server bind to port 80 at `192.168.4.1`.
On Orangepi Zero, scanning SSIDs is only possible when AP mode is off. Therefore, any re-scan will turn off AP mode and disconnect user. But this should last for only about 5 seconds. Credentials are checked using command `nmcli device wifi connect %s password %s`.  

Scanning SSID: `nmcli -f SSID device wifi list` after `nmcli radio wifi on` or `nmcli device wifi rescan`.

# Instructions to install

The following are the step-by-step instructions for how I create the turnkey image.

## 1. Flash Raspbian Stretch Lite
Use ARMBIAN Bionic (https://www.armbian.com/orange-pi-zero/).

## 2. Install libraries onto the Orange Pi Zero

SSH into your Pi using Ethernet, as you will have to disable the WiFi connection when you install `hostapd`.

### Basic libraries

```
$ sudo apt-get update
$ sudo apt-get dist-upgrade -y
$ sudo apt-get install -y dnsmasq hostapd python3-flask python3-requests git
```

### Download turnkey

```
$ git clone https://github.com/Lucashsmello/orangepi0-turnkey.git
```

### Run install script (TODO)

To install:
```
$ cd orangepi0-turnkey.git
$ ./install.sh
```

To uninstall:
```
$ ./install.sh --uninstall
```

The `install.sh` script runs all below commands automatically. The `install.sh` script is enough, just reboot pi now. If you want to install manually, follow below instructions.

### Disable systemd-resolved
We will use dnsmasq instead of systemd-resolved
```
$ sudo systemctl disable systemd-resolved
$ sudo systemctl restart dnsmasq
```


### Install Hostapd

```
$ sudo systemctl stop dnsmasq && sudo systemctl stop hostapd

$ echo 'interface wlan0
static ip_address=192.168.4.1/24' | sudo tee --append /etc/dhcpcd.conf

$ sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig  
$ sudo systemctl daemon-reload
$ sudo systemctl restart dhcpcd

$ echo 'interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h' | sudo tee --append /etc/dnsmasq.conf

$ echo 'interface=wlan0
driver=nl80211
ssid=ConnectToConnect
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=ConnectToConnect
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP' | sudo tee --append /etc/hostapd/hostapd.conf

$ echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' | sudo tee --append /etc/default/hostapd

$ sudo systemctl start hostapd && sudo systemctl start dnsmasq
```

### Add `pi` to sudoers

Add `pi` to the sudoers, so that you can run sudo commands without having to be root (so that all the paths to your programs are unchanged).

```
$ sudo visudo
```

Then add this line:

```
pi      ALL=(ALL:ALL) ALL
```

(_Sidenote:_ I save an image `intermediate.img` at this point so its easy to go back)


### Startup server on boot

Open up the `rc.local`

```
$ sudo nano /etc/rc.local
```

And add the following line before `exit 0`:

```
/usr/bin/sudo /usr/bin/python3 /PATH/TO/raspberry-pi-turnkey/startup.py &
```
Probably `/PATH/TO` is `/root` or `/home/pi`


### Reboot pi

```
$ sudo reboot
```

# License 

MIT
