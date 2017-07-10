#!/usr/bin/python

from __future__ import print_function
import time
import optparse
import sys
import subprocess
import os
import socket
import itertools
try:
	from netaddr import IPNetwork
except:
	print("\033[1m\033[91m[!]\033[0m Error: netaddr package not found. 'pip install netaddr' to use CIDR notation")

def main():

	## Define functions

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


	## Get Options

	parser = optparse.OptionParser()

	parser.add_option('-d', '--debug',
			dest="debug",
			default=False,
			action="store_true",
			help='display all pings, failed and successful',
			)
	parser.add_option('-l', '--list',
			dest="ip_file",
			default='',
			help='define a text file of one IP per line to ping',
			)
	parser.add_option('-n', '--hostnames',
			dest="hostnames",
			default=False,
			action="store_true",
			help='Attempt to resolve hostnames for successful pings',
			)
	parser.add_option('-r', '--reverse',
			dest="reverse",
			default=False,
			action="store_true",
			help='display failed pings instead of successful pings',
			)
	parser.add_option('-t', '--timeout',
			dest="timeout",
			default=200,
			help='define a ping timeout in miliseconds (default is 200)',
			)
	parser.add_option('-v', '--verbose',
			dest="verbose",
			default=False,
			action="store_true",
			help='include fping statistics for each ping',
			)
	parser.set_usage("""Usage: pingsweep [options] ip_range

Examples:
  pingsweep 10.0.0.0/24
  pingsweep 10.0.0.0-255
  pingsweep 10.0.0.0 10.0.0.255
		""")

	options, remainder = parser.parse_args()


	## Initialize variables

	verbose = options.verbose
	reverse = options.reverse
	timeout = options.timeout
	if not is_int(timeout):
		print_err("Invalid timeout '%s' - must be an integer" % timeout)
	elif int(timeout) < 50:
		print_err("Invalid timeout '%s' - minimum timeout is 50" % timeout)
	hostnames = options.hostnames
	debug = options.debug
	ip_file = options.ip_file
	begip = "none"
	endip = "none"
	ip_list = []


	## Handle extra arguments (only accepts exactly one or two extra arguments as IP addresses)

	if len(remainder) == 0:
		if ip_file == '':
			print_err("Please define IP range to ping")
		else:
			try:
				with open(ip_file, 'r') as f:
					for line in f:
						line = line.rstrip()
						if not line == "":
							if validate_ip(line):
								ip_list.append(line)
							else:
								print_err("Invalid IP list file format -- IP list file must have one valid IPv4 address per line with no leading or trailing spaces.")
			except:
				print_err("invalid file '%s'" % (ip_file))
	elif len(remainder) == 1:

		ipstring = remainder[0]
		if "/" in ipstring:
			ip_list = createiplist_cidr(ipstring)
		elif "-" in ipstring:
			ip_list = createiplist_dash(ipstring)
		else:
			print_err("invalid IP format")

	elif len(remainder) == 2:

		begip = remainder[0]
		endip = remainder[1]
		ip_list = createiplist_range(begip, endip)

	else:
		print_err("Invalid number of arguments")


	## If hosts list exceeds 256, prompt for confirmation

	if len(ip_list) > 256:
		if not are_you_sure(len(ip_list)):
			sys.exit()

	## Print selected options before starting the scan

	print("Starting ping sweep on %s through %s...\n" % (ip_list[0], ip_list[-1]))
		
	if verbose:
		print("\033[1m\033[34m[+]\033[0m Verbose option set\n")

	if timeout != 200:
		print("\033[1m\033[34m[+]\033[0m Timeout set to %s milliseconds\n" % (timeout))

	if reverse:
		print("\033[1m\033[34m[+]\033[0m Reverse option set - displaying failed pings\n")

	if hostnames:
		print("\033[1m\033[34m[+]\033[0m Hostnames option set - resolving hosts\n")

	if debug:
		print("\033[1m\033[34m[+]\033[0m Debug option set - displaying all pings\n")



	## Check if fping is installed

	check_requirements()



	## Begin scanning IP addresses by executing fping command on each IP

	print("Scan start: %s\n......" % (time.ctime()))
	success = 0
	for ip in ip_list:
		bash_string = "fping -a -c1 -t%s %s" % (timeout, ip)
		try:
			proc = subprocess.Popen(bash_string.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			output = proc.communicate()[0].split("\n")[0]
			if debug:
				if "1/1/0" in output:
					success += 1
				print(output)
			else:
				if reverse:
					if "1/0/100" in output:
						if verbose:
							print(output)
						else:
							print(output.split(" ",1)[0])
					else:
						success += 1
				else:
					if "1/1/0" in output:
						success += 1
						if hostnames:
							hostname = resolve(ip)
							if verbose:
								print(output, hostname)
							else:
								print(output.split(" ",1)[0], hostname)
						else:
							if verbose:
								print(output)
							else:
								print(output.split(" ",1)[0])
		except:
			print("\n\033[1m\033[91m[!]\033[0m Exiting...")
			print("Scan stopped at IP %s on %s" % (ip, time.ctime()))
			sys.exit()

	print("......\nSuccessful pings: \033[1m\033[92m%s/%s\033[0m (%s%s)" % (success, len(ip_list), (success * 100 / len(ip_list)), '%'))
	print("Scan finished at: %s" % (time.ctime()))

if __name__ == '__main__':
	main()
