import subprocess
from subprocess import PIPE
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

PIID=None
SSID_LIST = []

def stopAP(): #hotspot
    print("Stopping AP...")
    subprocess.run(['systemctl', "stop", "hostapd", "dnsmasq", "dhcpcd"],check=True)
    subprocess.run(['nmcli','radio', 'wifi', 'on'],check=True)
    time.sleep(1)

def startAP(): #hotspot
    subprocess.run('nmcli radio wifi off'.split(),check=True)
    subprocess.run('rfkill unblock wlan'.split(),check=True)
    subprocess.run(['systemctl', "restart", "hostapd", "dnsmasq", "dhcpcd"], check=True)

def getIPAddress():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ipaddress = s.getsockname()[0]
    s.close()
    return ipaddress

scanSSIDs_CMD='nmcli -f SSID device wifi list'.split()
def scanSSIDs(ntries=1):
    global scanSSIDs_CMD
    while(ntries>0):
        ssid_list = []
        try:
            get_ssid_list = subprocess.check_output(scanSSIDs_CMD,encoding='utf8')
        except Exception as ex:
            ntries-=1
            if(ntries==0):
                print("Could not scan for ssid: "+str(ex))
                return None
            time.sleep(1)
            continue            

        get_ssid_list=get_ssid_list.splitlines()[1:]
        for line in get_ssid_list:
            line=line.strip('\n').strip()
            if line=='--': continue
            ssid_list.append(line)
        print(ssid_list)
        #ssid_list = sorted(list(set(ssid_list)))
        if(len(ssid_list)>0):
            return ssid_list
        ntries-=1
        if(ntries==0):
            break
        time.sleep(1)

    return None

def getssid(ntries=1):
    global SSID_LIST
    if len(SSID_LIST) <= 0:
        l=scanSSIDs(ntries)
        if(not(l is None)):
            SSID_LIST=l
    return SSID_LIST


def id_generator(size=6, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

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
    global SSID_LIST

    stopAP()
    SSID_LIST=[]
    getssid(ntries=5)
    check_cred_cmd=['nmcli', 'device', 'wifi', 'connect', ssid, 'password', password] # if successul, this automatically saves configuration
    print("running: %s" % " ".join(check_cred_cmd))
    for _ in range(5):
        try:
            P = subprocess.run(check_cred_cmd, check=True)
            print("Credentials are OK")
            return True
        except subprocess.CalledProcessError as e:
            print(">>>"+str(e))
        time.sleep(1)
    print("Credentials are not OK")
    return False

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

"""
def saveWiFiConfig(ssid,pwd):
    cmd='nmcli con add con-name "turnkey" type wifi ifname wlan0 ssid "%s" -- wifi-sec.key-mgmt wpa-psk wifi-sec.psk "%s" ipv4.method auto' % (ssid,pwd)
    subprocess.run(cmd.split(), check=True)
"""

@app.route('/signin', methods=['POST'])
def signin():
    #email = request.form['email']
    ssid = request.form['ssid']
    password = request.form['password']

    pwd = 'psk="' + password + '"'
    if password == "":
        pwd = "key_mgmt=NONE" # If open AP

    #print(ssid, password)
    valid_psk = check_cred(ssid, password) # this will interrupt AP.
    if not valid_psk:
        startAP() # Restart services
        # User will not see this because they will be disconnected but we need to break here anyway
        return render_template('index.html', message="Wrong password!")

    #saveWiFiConfig(ssid, pwd) 
    #stopAP()
    print("Disabling AP hotspot...")
    subprocess.run(["./disable_ap.sh"])
    print("AP hostspot disabled.")
    writeStatus({'status':'disconnected'})
    startup()
        
    piid = getPIID()
    return render_template('index.html', message="Please wait 2 minutes to connect. Then your IP address will show up at <a href='https://snaptext.live/{}'>snaptext.live/{}</a>.".format(piid,piid))

def wificonnected():
    print("Checking wifi connection...")
    result = subprocess.check_output(['iw', 'dev','wlan0','link'], encoding='utf8')
    print(">>"+str(result))
    #matches = re.findall(r'\"(.+?)\"', result.split(b'\n')[0].decode('utf-8'))
    #if len(matches) > 0:
    if not("Not connected" in result):
        print("Got connected on wlan0")
        return True
    return False

@app.route('/scan', methods=['POST'])
def route_scan():
    global SSID_LIST
    stopAP()
    SSID_LIST=[]
    getssid(ntries=5)
    startAP()
    return render_template('index.html', message="hello")

def writeStatus(s):
    with open('status.json', 'w') as f:
        f.write(json.dumps(s))    

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

def getCurrentStatus():
    s = {'status':'disconnected'}
    if not os.path.isfile('status.json'):
        writeStatus(s)
    else:
        s = json.load(open('status.json'))
    return s

def startup():
    s=getCurrentStatus()

    # check connection
    if wificonnected():
        s['status'] = 'connected'
    else:
        if s['status'] == 'connected' or s['status']=='hostapd':
            s['status'] = 'disconnected'

    writeStatus(s)
    if s['status'] == 'disconnected':
        print("Enabling AP hotspot...")
        stopAP()
        getssid(ntries=3)
        subprocess.run(["./enable_ap.sh"], check=True)
        s['status'] = 'hostapd'
        writeStatus(s)
    elif s['status'] == 'connected':
        ipaddress=getIPAddress()
        # alert user on snaptext
        r = requests.post("https://snaptext.live",data=json.dumps({"message":"Your Pi is online at {}".format(ipaddress),"to":getPIID(),"from":"Pi Turnkey"}))
        print(r.json())
        subprocess.call("./startup.sh")

    print("Current status: %s" % s['status'])
    return s['status']

def main():
    piid=getPIID()
        #subprocess.Popen("./expand_filesystem.sh")
        #time.sleep(300)
    print(piid)
    status=startup()
    if status=='disconnected' or status=='hostapd':
        app.run(host="0.0.0.0", port=80, threaded=True)

if __name__=="__main__":
    main()
