#!/usr/bin/python
import os
import sys
import subprocess
import re
import paramiko

#Willkommen heissen
def welcome ():	
	print "Willkommen. Ich starte nun hoffentlich den DHCP-Server"
	print "Mal sehen..."

# funtion to start or restart the DHCP server
def serverStart ():
	os.system("sudo /etc/init.d/isc-dhcp-server stop")
	os.system("sudo /etc/init.d/isc-dhcp-server start")

#a function to find out the Controller MAC (mac will be returned as a string)
def getMac ():
	ifconfigText = subprocess.check_output(["ifconfig"], shell=True)
	macObj = re.search(r"[0-9a-z][0-9a-z]:[0-9a-z][0-9a-z]:[0-9a-z][0-9a-z]:[0-9a-z][0-9a-z]:[0-9a-z][0-9a-z]:[0-9a-z][0-9a-z]", ifconfigText)
	mac = macObj.group()
	print "Die MAC-Addresse des Controllers ist: %s." % mac
	return mac

#a function to safe the config of the DHCP-Server
def saveConfig (digits=50):	
	print "Die Config-Datei wird nun gespeichert."	
	copyDoc("/etc/dhcp/dhcpd.conf","/etc/dhcp/dhcpd_SAFE.conf",digits)

#a function to copy a text document (digits therefore is like the velocity of the Process)
def copyDoc (readDocAddress, writeDocAddress, digits=50):
	print "%s wird nun in das Dokument %s kopiert." % (readDocAddress, writeDocAddress)	
	readDoc = open(readDocAddress,"r")
	writeDoc = open(writeDocAddress,"w")	
	while 1:
		text= readDoc.read(digits)
		if text == "":
			break
		writeDoc.write(text)
	writeDoc.close()
	readDoc.close()
	
#a function to give a device a static IP from the DHCP
def host (ip, name, mac):
	print "Wir werden nun die Config aendern und eine Einstellung vornehmen."
	#at first the config is saved in /etc/dhcp/dhcpd_SAFE.conf
	saveConfig()
	
	#Now we change read the current config	
	config = open("/etc/dhcp/dhcpd.conf","r")	
	print "Dem Geraet mit der MAC %s soll nun die IP %s\ngegeben werden." % (mac, ip)
	givenText = config.read()
	config.close()
	
	#Now we read the config and test if the is free and if true we add the new "host"-party
	if givenText.find(mac)==-1:	
		config = open("/etc/dhcp/dhcpd.conf","w")	
		newText = "\nhost %s {\n   hardware ethernet %s;\n   fixed-address %s;\n}" %(name, 			mac, ip)	
		Text = givenText+newText
		config.write(Text)
		config.close()
		serverStart()
		print "Die config ist nun geaendert und die IP wurde vergeben.\nDer Server wurde neu gestartet."
	elif not givenText.find(mac)==-1:
		print "Die MAC-Addresse ist bereits einer IP zugeordnet.\nDie Config wurde nicht geaendert."

#a function to open a ssh to another client
def sshConnect (name="id_rsa"):
	client = paramiko.SSHClient()
	myKey = os.path.expanduser("~/.ssh/%s" % name)
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	#client.connect("192.168.1.2", username="lucas", key_filename=myKey)
	client.connect("192.168.1.2", username="lucas", password="123456")
	print "Der Controller hat sich nun mit dem Teilnehmer verbunden."
	stdin, stdout, stderr = client.exec_command("ifconfig")
	for line in stdout:
		print line.strip("\n")
	client.close()
	

#Here the main program is starting
#welcome()
#host("192.168.1.1", "controller",getMac())
sshConnect("id_rsa")


#this will return the former config to the DHCP Server
#copyDoc("/home/lucas/Schreibtisch/config 1.2", "/etc/dhcp/dhcpd.conf")



#configure the DHCP-Server, that it will give the Controller one static IP
#Server starten, damit die IP-Addressen bezogen werden koennen
#os.system("sudo /etc/init.d/isc-dhcp-server start")
