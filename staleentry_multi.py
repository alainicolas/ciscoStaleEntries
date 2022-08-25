import yaml
import jinja2
import csv
from genie.testbed import load
from unicon.core.errors import ConnectionError
from concurrent.futures import ThreadPoolExecutor,as_completed
import os
import logging
from pyats.log import ScreenHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(ScreenHandler())

with open("./templates/list_ip.yaml", "r") as file:
    list_ip = yaml.load(file, Loader=yaml.FullLoader)

# Where's the folder with my templates (or my folders, if multiple)
template_loader = jinja2.FileSystemLoader(searchpath="./templates")

# Instance of the Environment class. Gives the loader (above), optionally parameters like
# block strings, variable strings etc.
template_env = jinja2.Environment(loader=template_loader)

# Which file is my template
template = template_env.get_template("testbed.tpl")

# We give the template two lists:
# - list_ip: the IP of our devices
# - range(len(list_ip)), the id (from 0 to the max device) that will be used in device.name to make it unique
testbed = load(template.render(list_ip_id = zip(list_ip, range(len(list_ip)))))


def stale(device):
    if device.type != "linux":
        with open(f'./outputs/stale-entries-log.txt', 'a') as logfile:
            try:
                device.connect(learn_hostname=True,
                               init_exec_commands=[],
                               init_config_commands=[],
                               log_stdout=False)
                print(f'-- {device.hostname} - {device.connections.vty.ip} --')
            except ConnectionError:
                # print("-- ERROR --")
                print(f" -- Cant't connect to : {device.connections.vty.ip} --")
                logfile.write(f" -- Cant't connect to : {device.connections.vty.ip} --")
                logfile.write('\n')
                # print(f"  Can't connect to {device.connections.vty.ip}")
                #continue

            # print(f'-- {device.hostname} - {device.connections.vty.ip} --')

        with open(f'./outputs/stale-entries.txt', 'a') as file:
                suppeer = device.execute("show forwarding distribution peer-id |  grep \"Vlan: 1\"")
                sdkpeer = device.execute("slot 1 sh hardware  internal  tah  sdk vxlan sw-tables | grep \"key:ip\"")
                peerid = device.execute("slot 1 sh hardware internal tah sdk vxlan sw-tables | grep \"Peer-id is\"")
                suppeerdb = []
                sdkpeerdb = []
                sdkpeeriddb = []
                reverseip = [0,0,0,0]
                sanity = True

                #Adding entry in file stale-entries.txt
                #file.write(str(device.hostname))
                #file.write('\n')

                #Filling SUP Peer DB
                for line in suppeer.splitlines():
                    suppeerdb.append(line.split())

                #Filling SDK Peer DB
                for line in sdkpeer.splitlines():
                    sdkpeerdb.append(line.split())

                #Filling the SDK peer ID DB
                for line in peerid.splitlines():
                    sdkpeeriddb.append(line.split())

                #Translating SDK DEC peer in a 4 digits HEX peer id
                for peer in sdkpeeriddb:
                    myhex = "0x" + str(hex(int(peer[6])))[-2:]
                    peer[6] = myhex

                #Translating SUP peer in a 4 digits HEX peer id
                for peer in suppeerdb:
                    if len(peer[10]) == 3:
                        value = peer[10][:2] + '0' + peer[10][2:]
                        peer[10] = value

                #Translating reverse IP addresses in SDK Peer DB
                for peer in sdkpeerdb:
                    i = 3
                    for byte in peer[1].split("."):
                        reverseip[i] = byte
                        i = i-1
                    peer[1] = str(reverseip[0] + "." + reverseip[1] + "." + reverseip[2] + "." + reverseip[3])

                #Checking if the peer in SUP is in SDK with any() function
                for peer in suppeerdb:
                    if not any(peer[7] in sdkpeer for sdkpeer in sdkpeerdb):
                        #print("Peer " + peer[7] + " is in SUP but not in SDK at entry " + peer[10])
                        file.write("Device : " + str(device.hostname) + " - Peer " + peer[7] + " is in SUP but not in SDK at entry " + peer[10])
                        file.write('\n')
                        sanity = False

                #Checking if there is a stale entry
                for peerid in sdkpeeriddb:
                    if not any(peerid[6] in suppeer for suppeer in suppeerdb):
                        if peerid[6] not in ("0xfd","0xfe","0xff" ):
                            #print("Entry " + peerid[6] + " exists in SDK but not in SUP.")
                            file.write("Device : " + str(device.hostname) + " - Entry " + peerid[6] + " exists in SDK but not in SUP.")
                            file.write('\n')
                            sanity = False

                #if (sanity):
                    #file.write("All entries are clean.")
                    #file.write('\n')

                #file.write('\n')


        #print('Device ' + device.hostname + ' DONE.')
        #print('')
        device.disconnect()


try:
    # max_worker define the number of simultaneous connection
    with ThreadPoolExecutor(max_workers=8) as t:
        try:
            threads = []
            for device in testbed.devices.values():
                    threads.append(t.submit(stale,device))

            # return out when a thread is completed
            #for out in as_completed(threads):

                #output = out.result()
        # Need to shutdown properly the thread and save the excel file on Ctrl+C
        # Required if audit must be stopped before all devices have been audited
        except KeyboardInterrupt:
            logger.info("Keyboard Interrupt Received. Stopping all thread")
            t.shutdown(wait=False, cancel_futures=True)
            raise
finally:
    print("Stale checking done.")