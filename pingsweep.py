#!/usr/bin/python

from __future__ import print_function
import time
import optparse
import sys
import subprocess
import os
import socket
import itertools
import mainfuncs
try:
	from netaddr import IPNetwork
except:
	print("\033[1m\033[91m[!]\033[0m Error: netaddr package not found. 'pip install netaddr' to use CIDR notation")

def main():


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
	if not mainfuncs.is_int(timeout):
		mainfuncs.print_err("Invalid timeout '%s' - must be an integer" % timeout)
	elif int(timeout) < 50:
		mainfuncs.print_err("Invalid timeout '%s' - minimum timeout is 50" % timeout)
	hostnames = options.hostnames
	debug = options.debug
	ip_file = options.ip_file
	begip = "none"
	endip = "none"
	ip_list = []


	## Handle extra arguments (only accepts exactly one or two extra arguments as IP addresses)

	if len(remainder) == 0:
		if ip_file == '':
			mainfuncs.print_err("Please define IP range to ping")
		else:
			try:
				with open(ip_file, 'r') as f:
					for line in f:
						line = line.rstrip()
						if not line == "":
							if mainfuncs.validate_ip(line):
								ip_list.append(line)
							else:
								mainfuncs.print_err("Invalid IP list file format -- IP list file must have one valid IPv4 address per line with no leading or trailing spaces.")
			except:
				mainfuncs.print_err("invalid file '%s'" % (ip_file))
	elif len(remainder) == 1:

		ipstring = remainder[0]
		if "/" in ipstring:
			ip_list = mainfuncs.createiplist_cidr(ipstring)
		elif "-" in ipstring:
			ip_list = mainfuncs.createiplist_dash(ipstring)
		else:
			mainfuncs.print_err("invalid IP format")

	elif len(remainder) == 2:

		begip = remainder[0]
		endip = remainder[1]
		ip_list = mainfuncs.createiplist_range(begip, endip)

	else:
		mainfuncs.print_err("Invalid number of arguments")


	## If hosts list exceeds 256, prompt for confirmation

	if len(ip_list) > 256:
		if not mainfuncs.are_you_sure(len(ip_list)):
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

	mainfuncs.check_requirements()



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
							hostname = mainfuncs.resolve(ip)
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
