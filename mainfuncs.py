import sys
import itertools
import socket
import subprocess
import os

def print_err(desc):
	print("\033[1m\033[91m[!]\033[0m Error: %s" % desc)
	print("Use '-h' option for help menu")
	sys.exit()

def check_requirements():
	try:
		FNULL = open(os.devnull, 'w')
		subprocess.call(["fping", "-v"], stdout=FNULL, stderr=subprocess.STDOUT)
	except OSError as e:
		if e.errno == os.errno.ENOENT:
			print_err("fping is not installed. Please install fping and run again. Exiting...")
		else:
			raise
			sys.exit()

def is_int(rawvar):
	try:
		int(rawvar)
		return True
	except ValueError:
		return False

def validate_ip(ip):
	a = ip.split('.')
	if len(a) != 4:
		return False
	for x in a:
		if not x.isdigit():
			return False
		i = int(x)
		if i < 0 or i > 255:
			return False
	return True

def createiplist_cidr(ipstring):
	iplist = []
	try:
		for ip in IPNetwork(ipstring):
			iplist.append(ip)
	except:
		print_err("invalid CIDR notation")
	return iplist

def createiplist_dash(input_string):
	iplist = []
	try:
		octets = input_string.split('.')
		chunks = [map(int, octet.split('-')) for octet in octets]
		ranges = [range(c[0], c[1] + 1) if len(c) == 2 else c for c in chunks]

		for address in itertools.product(*ranges):
			iplist.append('.'.join(map(str, address)))
	except:
		print_err("invalid dash notation")
	return iplist

def createiplist_range(begip, endip):
	ip_list = []

	try:
		start = list(map(int, begip.split(".")))
		end = list(map(int, endip.split(".")))
		
		if begip == endip:
			if start[3] == 0:
				end[3] = 255
		
		if end[0] > start[0] or (end[0] == start[0] and end[1] > start[1]) or (end[0] == start[0] and end[1] == start[1] and end[2] > start[2]) or (end[0] == start[0] and end[1] == start[1] and end[2] == start[2] and end[3] >= start[3]):
			temp = start

			ip_list.append(begip)
			while temp != end:
				start[3] += 1
				for i in (3, 2, 1):
					if temp[i] == 256:
						temp[i] = 0
						temp[i-1] += 1
				ip_list.append(".".join(map(str, temp)))

			return ip_list
		else:
			print_err("The second IP must be greater than or equal to the first IP.")
	except:
		print_err("invalid range notation")

def are_you_sure(numOfHosts):
	valid = {"yes": True, "y": True, "ye": True,
		"no": False, "n": False}

	while True:
		sys.stdout.write("Ping %s hosts? [Y/n] " % numOfHosts)
		choice = raw_input().lower()
		if choice == '':
			return valid["yes"]
		elif choice in valid:
			return valid[choice]
		else:
			sys.stdout.write("Please respond with 'yes' or 'no' "
					"(or 'y' or 'n').\n")

def resolve(ip):
	try:
		hostname = socket.gethostbyaddr(ip)[0]
		return hostname
	except:
		return ''
