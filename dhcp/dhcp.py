"""
DhcpLeasesParser: Parser class based on PyParsing to parse a dhcpd.leases file
to extract leases and lease attributes.

The format of the lease file is found in the dhcpd.leases(5) manual page,
or at the following URL: http://linux.die.net/man/5/dhcpd.leases

The default location of the DHCP leases file is: /var/lib/dhcp/dhcpd.leases

Dependencies:
python-pyparsing

Copyright 2015 coruja
SPDX-License-Identifier: GPL-2.0
"""
from pyparsing import (nums, hexnums, alphanums, Suppress, Combine, Word,
                       Literal, oneOf, ZeroOrMore, Group, QuotedString, Dict,
                       Optional, restOfLine)
import datetime
import time
import re
import logging

logger = logging.getLogger(__name__)

IPV4ADDR_RE = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"

class DhcpLeasesParser(object):
    """ The parser class based on PyParsing to parse a dhcpd.leases file """
    def __init__(self, leases_filename):
        self.leases_filename = leases_filename
        self.leases = ""
        self.ips = set()
        self.count_tot = 0
        self.count_parsed = 0
        self.hosts = []
        self.lease_def = self._setup()
        self.extras = ('starts', 'ends', 'cltt')
        # Keep track of duplicate entries that canbe found in the leases file
        # as this might be an indicator that a DUT is behaving strangely
        self.dups = set()

    def _setup(self):
        """ Define the grammar used in the leases file """
        lbrace, rbrace, semi = map(Suppress, '{};')
        ipaddr = Combine(Word(nums) + ('.' + Word(nums)) * 3)

        macaddr = Combine(Word(hexnums, exact=2) + \
                  (':' + Word(hexnums, exact=2)) * 5)

        hwtype = Word(alphanums)
        comment = '#' + Optional(restOfLine)

        yyyymmdd = Combine((Word(nums, exact=4) | Word(nums, exact=2)) +
                           ('/' + Word(nums, exact=2)) * 2)

        hhmmss = Combine(Word(nums, exact=2) + \
                 (':' + Word(nums, exact=2)) * 2)

        dateref = (oneOf(list("0123456"))("weekday") + yyyymmdd("date") +
                   hhmmss("time"))

        def _utc2localtime(tokens):
            """ Converts UTC date and time to local time """
            utctime = datetime.datetime.strptime("%(date)s %(time)s" % tokens,
                                                 "%Y/%m/%d %H:%M:%S")
            localtime = utctime - datetime.timedelta(0, time.timezone, 0)
            tokens["utcdate"], tokens["utctime"] = tokens["date"], tokens["time"]
            tokens["localdate"], tokens["localtime"] = str(localtime).split()
            del tokens["date"]
            del tokens["time"]
        dateref.setParseAction(_utc2localtime)

        # The start and end time value of a DHCP Lease
        starts = Literal("starts") + dateref + semi
        ends = Literal("ends") + (dateref | Literal("never")) + semi
        # TSTP (Time Sent To Partner)
        tstp = Literal("tstp") + dateref + semi
        # TSFP (Time Sent From Partner)
        tsfp = Literal("tsfp") + dateref + semi
        # ATSFP (Actual Time Sent from the Failover Partner)
        atsfp = Literal("atsfp") + dateref + semi
        # CLTT (Client Last Transaction Time)
        cltt = Literal("cltt") + dateref + semi
        hdw = (Literal("hardware") + hwtype("type") +
              macaddr("mac") + semi)
        uid = Literal("uid") + QuotedString('"', escChar='\\') + semi

        bind_state = Literal('active') \
            | Literal('free') \
            | Literal('backup') \
            | Literal('expired') \
            | Literal('abandoned')
        bind = Literal('binding') + Suppress('state') + bind_state + semi

        nextbind = Literal('next') + bind
        clienthostname = Literal("client-hostname") + QuotedString('"') + semi

        # Put the grammar together to define a lease definition
        leasestmt = (starts | ends | tstp | tsfp | atsfp | cltt |
                          hdw | uid | bind | nextbind |
                          clienthostname)
        leasedef = (Literal("lease") + ipaddr("ipaddress") + lbrace +
                    Dict(ZeroOrMore(Group(leasestmt))) + rbrace)

        leasedef.ignore(comment)
        return leasedef

    def parse(self):
        """ Open, read and parse the contents of the leases file """
        with open(self.leases_filename, 'rb') as leasesf:
            leases_ls = leasesf.readlines()
        self.leases = ''.join(leases_ls)

        self.count_tot = 0
        for line in leases_ls:
            if not line.startswith('#'):
                if re.findall(r'lease\s+' + IPV4ADDR_RE + '\s+', line, re.DOTALL):
                    ip_addr = re.search(IPV4ADDR_RE, line).group(0)
                    self.count_tot += 1
                    if ip_addr in self.ips:
                        self.dups.add(ip_addr)
                    self.ips.add(ip_addr)

        self.count_parsed = 0
        for lease in self.lease_def.searchString(self.leases):
            do_append = True
            #print lease.dump()
            # Each lease must have an IP address
            if ('ipaddress' not in lease or
               'binding' not in lease or
               lease['binding'] != 'active'):
                continue
            # There can be existing hosts with same ipaddress but other
            # lease attributes. The implicit behaviour here is that later
            # leases for the same IP address will supersede earlier ones
            host = self.get_host_by_ip(lease.ipaddress)
            if host is None:
                host = {'ip_addr': lease.ipaddress}
            else:
                # if the host entry already exists, just update
                do_append = False
            # If a MAC address has been found, save it in dict
            if 'hardware' in lease and 'mac' in lease['hardware']:
                host['mac_addr'] = lease.hardware.mac
            else:
                host['mac_addr'] = ''
            # If a hostname for the client is available, save it in dict
            if 'client-hostname' in lease:
                host['client_hostname'] = lease['client-hostname']
            else:
                host['client_hostname'] = ''
            # Add some extra paramaters in dict
            for el in self.extras:
                if el in lease:
                    host[el] = (lease[el]['localdate'],
                                lease[el]['localtime'])
                else:
                    host[el] = ('', '')
            if do_append:
                self.hosts.append(host)
            self.count_parsed += 1

    def get_host_by_ip(self, ip):
        for host in self.hosts:
            if host['ip_addr'] == ip:
                return host
        return None

    def get_hosts(self):
        """ Returns a list of active leases/hosts """
        return self.hosts

    def get_leases(self):
        """ Returns a list of all lease entries """
        return self.ips

if __name__ == "__main__":
    import sys
    # Parse the given dhcpd.leases file for active leases
    lease_parser = DhcpLeasesParser(sys.argv[1])
    lease_parser.parse()
    # Returns the list of active hosts/leases
    res = lease_parser.get_hosts()
    print res
    print "Found %d lease entries in file" % lease_parser.count_tot
    print "Parsed %d active leases" % lease_parser.count_parsed
    print "Found %d unique leases" % len(res)
    print "duplicates:"
    print lease_parser.dups

