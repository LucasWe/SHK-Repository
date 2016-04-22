#!/usr/bin/python
import os
import sys
import subprocess
import re
import paramiko

#Die Einstellungen fuer die SSH verbindung
User = "lucas"
Passwort = "123456"
Schaddresse = "~/.ssh/id_rsa"
Hostname = "192.168.1.2"

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
	client.close()

#a function, that copies the Teilnehmers interface file to a local path
def getInterface (boxnumber, clientnumber):		
	client = paramiko.SSHClient()
	myKey = os.path.expanduser("~/.ssh/id_rsa")
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect("192.168.1.2", username="lucas", password="123456")
	print "Der Controller hat sich nun mit dem Teilnehmer verbunden."	
	sftp = client.open_sftp()
	sftp.get("/etc/network/interfaces", "/home/lucas/interfaces.%s.%s" % (boxnumber,clientnumber))
	sftp.close()
	client.close()

#a function, that changes the interface-file on the Controller to a static IP
#assuming that the network card is named enp0s3
#it also copies the interface file into a safety file
def changeInterfaceFile (boxnumber, clientnumber, cardname="enp0s3"):
	getInterface(boxnumber,clientnumber)	
	copyDoc("/home/lucas/interfaces.%s.%s" % (boxnumber,clientnumber), "/home/lucas/interfaces.%s.%s_SAFE" % (boxnumber,clientnumber))
	interface = open ("/home/lucas/interfaces.%s.%s" % (boxnumber,clientnumber), "w")
	text="# interfaces(5) file used by ifup(8) and ifdown(8)\nauto %s inet static\naddress 192.168.%s.%s\nnetmask 255.255.255.255.0\nbroadcast 192.168.1.255\n" % (cardname,boxnumber,clientnumber)
	interface.write(text)
	interface.close()
	putInterfaces(boxnumber, clientnumber)
	

#a function that copies back the Interface file
def putInterfaces (boxnumber, clientnumber):
	client = paramiko.SSHClient()
	myKey = os.path.expanduser("~/.ssh/id_rsa")
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect("192.168.1.2", username="lucas", password="123456")
	print "Der Controller hat sich nun mit dem Teilnehmer verbunden."
	sftp = client.open_sftp()
	sftp.put("/home/lucas/interfaces.%s.%s" % (boxnumber,clientnumber), "/home/lucas/interfaces")
	sftp.close()	
	
		
	client = paramiko.SSHClient()
	myKey = os.path.expanduser("~/.ssh/id_rsa")
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect("192.168.1.2", username="lucas", password="123456")
	print "Der Controller hat sich nun mit dem Teilnehmer verbunden."
	stdin, stdout, stderr = client.exec_command("sudo mv /home/lucas/interfaces /etc/network/interfaces")
	for line in stdout:
		print line.strip("\n")
	client.close()

#a function to remotely restart the network device of the client to activate any changes
def restartNetDev ():
	client = paramiko.SSHClient()
	myKey = os.path.expanduser("~/.ssh/id_rsa")
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect("192.168.1.2", username="lucas", password="123456")
	print "Der Controller hat sich nun mit dem Teilnehmer verbunden."	
	client.exec_command("/etc/init.d/networking restart")
	client.close()
	
	

#Here the main program is starting
#welcome()
#host("192.168.1.1", "controller",getMac())
#staticIP("1","1")

changeInterfaceFile ("1","3","enp0s3")


#this will return the former config to the DHCP Server
#copyDoc("/home/lucas/Schreibtisch/config 1.2", "/etc/dhcp/dhcpd.conf")

#Was passiert denn nun?

#configure the DHCP-Server, that it will give the Controller one static IP
#Server starten, damit die IP-Addressen bezogen werden koennen
#os.system("sudo /etc/init.d/isc-dhcp-server start")
