#!/usr/bin/python
import os
import sys
import subprocess
import time

#Willkommen heissen
print "Willkommen. Ich starte nun hoffentlich den DHCP-Server"
print "Mal sehen..."

#Server starten, damit die IP-Addressen bezogen werden koennen
os.system("sudo /etc/init.d/isc-dhcp-server start")

#lokale Zaehlvariable i und eine Schleife, um den Clients Zeit zu geben anzugehen
i = 1
while i<3:
	print i	
	time.sleep(1)
	i= i+1
	
#Hier kann der Nutzer entscheiden, ob er manuell eine Mac-Addresse herausfinden will
test = raw_input("Wollen Sie manuell ueberpruefen? ")

if test == "J":
	addresse = raw_input("Bitte geben sie die Ip ein: ")
if not test == "J":
	addresse = "192.168.1.2"
mac = subprocess.check_output(["arp %s" % (addresse)], shell=True)

print mac[100:117]
#print mac-address

#os.system("sudo /etc/init.d/isc-dhcp-server stop")
#config = open("/etc/dhcp/dhcpd.conf","w")


