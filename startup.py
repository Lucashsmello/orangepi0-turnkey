import subprocess
import signal
import string
import random
import re
import json
import time
import os
import socket
import requests

from flask import Flask, request, send_from_directory, jsonify, render_template, redirect
app = Flask(__name__, static_url_path='')

currentdir = os.path.dirname(os.path.abspath(__file__))
os.chdir(currentdir)


def scanSSIDs():
    ssid_list = []
    try:
        get_ssid_list = subprocess.check_output(('iw', 'dev', 'wlan0', 'scan', 'ap-force'))
    except Exception as ex:
        print("Could not scan for ssid")
        return None
		
    ssids = get_ssid_list.splitlines()
    for s in ssids:
        s = s.strip().decode('utf-8')
        if s.startswith("SSID"):
            a = s.split(": ")
            try:
                ssid_list.append(a[1])
            except:
                pass
    print(ssid_list)
    ssid_list = sorted(list(set(ssid_list)))
    return ssid_list

SSID_LIST = []
def getssid():
    global SSID_LIST
    if len(SSID_LIST) <= 0:
        l=scanSSIDs()
        if(not(l is None)):
            SSID_LIST=l
    return SSID_LIST


def id_generator(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

wpa_conf = """country=GB
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
network={
    ssid="%s"
    %s
}"""

wpa_conf_default = """country=GB
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
"""



@app.route('/')
def Index():
    piid = getPIID()
    return render_template('index.html', ssids=getssid(), message="Once connected you'll find IP address @ <a href='https://snaptext.live/{}' target='_blank'>snaptext.live/{}</a>.".format(piid,piid))

# Captive portal when connected with iOS or Android
@app.route('/generate_204')
def redirect204():
    return redirect("http://192.168.4.1", code=302)

@app.route('/hotspot-detect.html')
def applecaptive():
    return redirect("http://192.168.4.1", code=302)

# Not working for Windows, needs work!
@app.route('/ncsi.txt')
def windowscaptive():
    return redirect("http://192.168.4.1", code=302)

def check_cred(ssid, password):
    '''Validates ssid and password and returns True if valid and False if not valid'''
    wpadir = currentdir + '/wpa/'
    testconf = wpadir + 'test.conf'
    wpalog = wpadir + 'wpa.log'
    wpapid = wpadir + 'wpa.pid'

    if not os.path.exists(wpadir):
        os.mkdir(wpadir)

    for _file in [testconf, wpalog, wpapid]:
        if os.path.exists(_file):
            os.remove(_file)

    # Generate temp wpa.conf
    result = subprocess.check_output(['wpa_passphrase', ssid, password])
    with open(testconf, 'w') as f:
        f.write(result.decode('utf-8'))

    def stop_ap(stop):
        if stop:
            # Services need to be stopped to free up wlan0 interface
            print(subprocess.check_output(['systemctl', "stop", "hostapd", "dnsmasq", "dhcpcd"]))
        else:
            print(subprocess.check_output(['systemctl', "restart", "dnsmasq", "dhcpcd"]))
            time.sleep(15)
            print(subprocess.check_output(['systemctl', "restart", "hostapd"]))

    # Sentences to check for
    fail = "pre-shared key may be incorrect"
    success = "WPA: Key negotiation completed"

    stop_ap(True)

    result = subprocess.check_output(['wpa_supplicant',
                                      "-Dnl80211",
                                      "-iwlan0",
                                      "-c/" + testconf,
                                      "-f", wpalog,
                                      "-B",
                                      "-P", wpapid])

    checkwpa = True
    while checkwpa:
        with open(wpalog, 'r') as f:
            content = f.read()
            if success in content:
                valid_psk = True
                checkwpa = False
            elif fail in content:
                valid_psk = False
                checkwpa = False
            else:
                continue

    # Kill wpa_supplicant to stop it from setting up dhcp, dns
    with open(wpapid, 'r') as p:
        pid = p.read()
        pid = int(pid.strip())
        os.kill(pid, signal.SIGTERM)

    stop_ap(False) # Restart services
    return valid_psk

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/signin', methods=['POST'])
def signin():
    #email = request.form['email']
    ssid = request.form['ssid']
    password = request.form['password']

    pwd = 'psk="' + password + '"'
    if password == "":
        pwd = "key_mgmt=NONE" # If open AP

    print(ssid, password)
    valid_psk = check_cred(ssid, password)
    if not valid_psk:
        # User will not see this because they will be disconnected but we need to break here anyway
        return render_template('ap.html', message="Wrong password!")

    writeWPAconf(wpa_conf % (ssid, pwd))
    writeStatus({'status':'disconnected'})
    subprocess.Popen(["./disable_ap.sh"])
    piid = getPIID()
    return render_template('index.html', message="Please wait 2 minutes to connect. Then your IP address will show up at <a href='https://snaptext.live/{}'>snaptext.live/{}</a>.".format(piid,piid))

def wificonnected():
    result = subprocess.check_output(['iwconfig', 'wlan0'])
    matches = re.findall(r'\"(.+?)\"', result.split(b'\n')[0].decode('utf-8'))
    if len(matches) > 0:
        print("got connected to " + matches[0])
        return True
    return False

@app.route('/scan', methods=['POST'])
def route_scan():
    global SSID_LIST
    r=subprocess.call("./stopAP.sh")
    SSID_LIST=scanSSIDs()
    r=subprocess.call("./startAP.sh")
    return render_template('index.html', message="hello")

def writeWPAconf(conf):
    with open('wpa.conf', 'w') as f:
        f.write(conf)

def writeStatus(s):
    with open('status.json', 'w') as f:
        f.write(json.dumps(s))    

PIID=None
def getPIID():
    global PIID
    if(PIID is None):
        if os.path.isfile('pi.id'):
            with open('pi.id', 'r') as f:
                PIID=f.read().strip()
        else:
            with open('pi.id', 'w') as f:
                PIID=id_generator()
                f.write(PIID)
    return PIID

if __name__ == "__main__":
    piid=getPIID()
        #subprocess.Popen("./expand_filesystem.sh")
        #time.sleep(300)
    print(piid)
    # get status
    s = {'status':'disconnected'}
    if not os.path.isfile('status.json'):
        writeStatus(s)
    else:
        s = json.load(open('status.json'))

    # check connection
    if wificonnected():
        s['status'] = 'connected'
    if not wificonnected():
        if s['status'] == 'connected': # Don't change if status in status.json is hostapd
            s['status'] = 'disconnected'

    writeStatus(s)
    if s['status'] == 'disconnected':
        s['status'] = 'hostapd'
        writeStatus(s)
        writeWPAconf(wpa_conf_default)
        subprocess.call("./enable_ap.sh")
    elif s['status'] == 'connected':
        # get ip address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ipaddress = s.getsockname()[0]
        s.close()

        # alert user on snaptext
        r = requests.post("https://snaptext.live",data=json.dumps({"message":"Your Pi is online at {}".format(ipaddress),"to":piid,"from":"Pi Turnkey"}))
        print(r.json())
        subprocess.Popen("./startup.sh")
        while True:
            time.sleep(60000)
    else:
        app.run(host="0.0.0.0", port=80, threaded=True)
