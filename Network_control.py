#!/usr/bin/python
import os
import sys
import subprocess
import re
import paramiko
import time


#--------------------------------------
#Table of Content

#1) Basic functions
#2) DHCP-Server setup
#3) Controller functions
#4) Machine-User Interaction
#5) direct SSH-functions
#6) Client functions (indirect ssh)
#7) Main program
#--------------------------------------

#--------------------------------------------------------
#1) Basic functions for editing an manipulating texfiles
#--------------------------------------------------------

# a function to write a given text in a text file
def writeFile (text, direction):
	textfile = open(direction, "w")
	textfile.write(text)
	textfile.close()

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

#-----------------------------------------------
#2) functions that concern the DHCP-Server Setup
#-----------------------------------------------

# funtion to start or restart the DHCP server
def serverRestart ():
	os.system("sudo /etc/init.d/isc-dhcp-server stop")
	os.system("sudo /etc/init.d/isc-dhcp-server start")
	return

#a function to start the dhcp server
def serverStart ():
	os.system("sudo /etc/init.d/isc-dhcp-server start")
	return

# a function to stop the dhcp server
def serverStop():
	os.system("sudo /etc/init.d/isc-dhcp-server stop")
	return


#a function that sets up the DHCP-server with the right settings
def serverConfig():
	text = "subnet 192.168.%s.0 netmask 255.255.255.0 {\n  range 192.168.%s.2 192.168.%s.2;\n  option domain-name \"intnet\";\n  option broadcast-address 192.168.%s.255;\n  option subnet-mask 255.255.255.0;\n  interface enp0s3;\n  default-lease-time 5;\n  max-lease-time 7200;\n}\n" % (_box, _box, _box, _box)
	writeFile(text, "/etc/dhcp/dhcpd.conf")
	host("192.168.%s.254" % _box, "controller",getMac())
	return 


#a funtion to end the lease of the IP for the client
def leasesdelete ():
	leer =""
	writeFile(leer, "/var/lib/dhcp/dhcpd.leases")
	print "Die leases des DHCP-Servers wurden geloescht."
	return

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
	return

#a function, that waits till the client has got its IP
def wait4Client ():
	inti = 0
	clientip = ""
	ip = "192.168.%s.2" % _box
	while clientip != ip :
		leases = open ("/var/lib/dhcp/dhcpd.leases", "r")
		leasestext = leases.read()
		clientip = re.search(ip ,leasestext)
		try:
			clientip = clientip.group()

		except:
			print "Client ist noch nicht verbunden (Versuch %i/25)." % inti
		inti = inti + 1
		time.sleep(1)
		leases.close()
		if clientip == "192.168.%s.2" % _box:
			print "Der Client hat sich gerade verbunden."
		if inti >= 25:
			print "Ein Verbindungsaufbau war nicht moeglich (timeout)."
			serverStop()
			undo()
			sys.exit()
	return


#--------------------------------------------
#3) functions that happen on the Controller
#--------------------------------------------

#setting a static IP for the Controller
def controllerIP (boxnumber, cardname):
	copyDoc("/etc/network/interfaces", "/home/lucas/interfaces_SAFE")
	text="# interfaces(5) file used by ifup(8) and ifdown(8)\nauto lo\n\nauto %s\niface %s inet static\n\taddress 192.168.%s.254\n\tnetmask 255.255.255.0\n\tbroadcast 192.168.1.255\n" % (cardname,cardname,boxnumber)
	writeFile(text,"/etc/network/interfaces")
	restartNetDev("controller")
	print "Der Controller hat nun auch eine statische IP (192.168.%s.254)." % _box
	return
	
#a function to find out the Controller MAC (mac will be returned as a string)
def getMac ():
	ifconfigText = subprocess.check_output(["ifconfig"], shell=True)
	macObj = re.search(r"[0-9a-z][0-9a-z]:[0-9a-z][0-9a-z]:[0-9a-z][0-9a-z]:[0-9a-z][0-9a-z]:[0-9a-z][0-9a-z]:[0-9a-z][0-9a-z]", ifconfigText)
	mac = macObj.group()
	print "Die MAC-Addresse des Controllers ist: %s." % mac
	return mac

# a function to undo the changes on the controller
def undo ():
	copyDoc("/home/lucas/Schreibtisch/interfaces", "/etc/network/interfaces")
	time.sleep(2)
	subprocess.call("sudo /etc/init.d/isc-dhcp-server stop", shell= True)
	subprocess.call("sudo /etc/init.d/networking restart", shell= True)
	return

# a function wchich pingtests, if the Controller got its IP
def pingTest (ip):	
	ping = ""	
	pingText = subprocess.check_output(["ping %s -c 1" % ip], shell=True)
	pingObj = re.search(r"time=", pingText)
	try:	
		ping = pingObj.group()
		if ping != "":
			print "Alles mit %s hat geklappt! :-)" % ip
	except:
		print "Die IP %s ist in dem Subnetz des Controllers nicht vorhanden" % ip
#---------------------------------------------
#4) function for the machine-user-interaction
#---------------------------------------------

#a function that asks the user for the boxnumber an the number of connected odroids
def getBoxNumber ():
	box = ""	
	while box == "":	
		print "Die Nummer der Box kann von 0 bis 9 gehen."
		boxnumber = raw_input("Bitte geben sie die Nummer der Box ein (default= 1): ")
		inti = 0
		while inti <= 9:
			if boxnumber == "%i" % inti:
				box=boxnumber
			inti = inti +1
	return box

def getClientNumber():
	client = ""	
	while client == "":	
		print "Die Anzahl der Odroids kann von 1 bis 64 gehen."
		clientnum = raw_input("Bitte geben sie die Anzahl der angeschlossenen Odroids an: ")
		inti = 1
		while inti <= 64:
			if clientnum == "%i" % inti:
				client = clientnum
	
			inti = inti +1
		if inti == 65:
			print "Die angegebene Nummer ist zu gross."
	return client
	
#Willkommen heissen
def welcome ():
	print "Willkommen. Dieses Programm wird nun zuallererst den DHCP-Server konfigurieren."
	print "Mal sehen..."
	print "Danach wird einem Netzwerkteilnehmer eine statische IP zugewiesen."
	return

#--------------------------------------------------
#5) functions that use the ssh connection directly
#--------------------------------------------------


#opening an ssh client with the global veriables set above

def openClient (ip, user, ppassword):
	try:	
		client = paramiko.SSHClient()
		client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		client.connect(ip, username= user, password= ppassword)
		#print "Ein neuer SSH-Client wurde geoeffnet."
	except:
		print "Connection refused. Nochmal versuchen. Client war wohl noch nicht verbunden."
		undo()
	return client

#a function, that copies the Teilnehmers interface file to a local path
def getInterface (ip, user, password, boxnumber, clientnumber):
	client = openClient(ip, user, password)
	sftp = client.open_sftp()
	sftp.get("/etc/network/interfaces", "/home/lucas/interfaces.%s.%s" % (boxnumber,clientnumber))
	sftp.close()
	client.close()
	return

#a function that copies the Interface file back to the client
def putInterfaces (ip, user, password, boxnumber, clientnumber):
	client = openClient(ip, user, password)
	sftp = client.open_sftp()
	sftp.put("/home/lucas/interfaces.%s.%s" % (boxnumber,clientnumber), "/home/lucas/interfaces")
	sftp.close()
	client.close()

	client = client = openClient(ip , user, password)
	stdin, stdout, stderr = client.exec_command("echo %s | sudo -S -- mv /home/lucas/interfaces /etc/network/interfaces" % _password)
	client.close()
	return

#------------------------------------------------------------------------------------
#6) functions, which happen only on the Client Odroid (also using ssh, but indirect)
#------------------------------------------------------------------------------------

#a function, that changes the interface-file on the Controller to a static IP
#assuming that the network card is named enp0s3
#it also copies the interface file into a safety file
def changeInterfaceFile (ip, user, password, boxnumber, clientnumber, cardname="enp0s3"):
	getInterface(ip, user, password, boxnumber,clientnumber)
	copyDoc("/home/lucas/interfaces.%s.%s" % (boxnumber,clientnumber), "/home/lucas/interfaces.%s.%s_SAFE" % (boxnumber,clientnumber))
	interface = open ("/home/lucas/interfaces.%s.%s" % (boxnumber,clientnumber), "w")
	text="# interfaces(5) file used by ifup(8) and ifdown(8)\nauto lo\n\nauto %s\niface %s inet static\n\taddress 192.168.%s.%s\n\tnetmask 255.255.255.0\n\tbroadcast 192.168.1.255\n" % (cardname,cardname,boxnumber,clientnumber)
	interface.write(text)
	interface.close()
	putInterfaces(ip, user, password, boxnumber, clientnumber)
	return

#a function to remotely restart the network device of the client to activate any changes
#wich device is restartet depends on the given string
def restartNetDev (name):
	if name == "client":
		client = openClient ("192.168.%s.2" % _box, _user, _password)
		client.exec_command("echo %s | sudo -S -- /etc/init.d/networking restart" % _password)
		print "Die Netzwerkkarte von 192.168.%s.2 wird nun neu gestartet." % _box
		#somehow it needs some short time to restart, otherweise if the client is closed
		#immediatly the natwork device won't restart properly
		time.sleep(1)
		client.close()
	if name == "controller":
		os.system("sudo /etc/init.d/networking restart")
		print "Die Netzwerkkarte des Controllers wurde neugestartet."
	return


#-------------------------------------
#7) Here the main program is starting
#-------------------------------------

#Die Einstellungen fuer die SSH verbindung
_user = "lucas"
_password = "123456"
_box = "1"
_odroid = "1"
_client = "1"

start = time.time()
leasesdelete()
welcome()
_box = getBoxNumber()
print _box
_client = getClientNumber()
print _client

serverConfig()
serverStart()
wait4Client()

changeInterfaceFile ("192.168.%s.2" % _box, "lucas", "123456", _box, _odroid,"enp0s3")
restartNetDev("client")

pingTest("192.168.%s.%s" % (_box, _odroid))

serverStop()
leasesdelete()
controllerIP(_box,"enp0s3")

end = time.time()
deltaT = end - start
print "Die Zeit fuer einen Odroid betrug %i Sekunden." % deltaT



#this will return the former config to the DHCP Server
#copyDoc("/home/lucas/Schreibtisch/config 1.2", "/etc/dhcp/dhcpd.conf")


