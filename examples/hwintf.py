#!/usr/bin/python

"""
This example shows how to add an interface (for example a real
hardware interface) to a network after the network is created.
"""

import re
import sys

from mininet.cli import CLI
from mininet.log import setLogLevel, info, error
from mininet.net import Mininet
from mininet.link import Intf
from mininet.topo import SingleSwitchReversedTopo, Topo
from mininet.util import quietRun
from mininet.node import Host


class VLANHost(Host):
    "Host connected to VLAN interface"

    def config(self, vlan=100, **params):
        """Configure VLANHost according to (optional) parameters:
           vlan: VLAN ID for default interface"""

        r = super(VLANHost, self).config(**params)

        intf = self.defaultIntf()
        # remove IP from default, "physical" interface
        self.cmd('ifconfig %s inet 0' % intf)
        # create VLAN interface
        self.cmd('vconfig add %s %d' % (intf, vlan))
        # assign the host's IP to the VLAN interface
        self.cmd('ifconfig %s.%d inet %s' % (intf, vlan, params['ip']))
        # update the intf name and host's intf map
        newName = '%s.%d' % (intf, vlan)
        # update the (Mininet) interface to refer to VLAN interface name
        intf.name = newName
        # add VLAN interface to host's name to intf map
        self.nameToIntf[newName] = intf

        return r


hosts = {'vlan': VLANHost}


def exampleAllHosts(vlan):
    """Simple example of how VLANHost can be used in a script"""
    # This is where the magic happens...
    host = partial(VLANHost, vlan=vlan)
    # vlan (type: int): VLAN ID to be used by all hosts

    # Start a basic network using our VLANHost
    topo = SingleSwitchReversedTopo(k=5)
    net = Mininet(host=host, topo=topo)
    return net


def checkIntf(intf):
    "Make sure intf exists and is not configured."
    config = quietRun('ifconfig %s 2>/dev/null' % intf, shell=True)
    if not config:
        error('Error:', intf, 'does not exist!\n')
        exit(1)
    ips = re.findall(r'\d+\.\d+\.\d+\.\d+', config)
    if ips:
        error('Error:', intf, 'has an IP address,'
              'and is probably in use!\n')
        exit(1)


if __name__ == '__main__':
    import sys
    from functools import partial

    setLogLevel('info')
    # try to get hw intf from the command line; by default, use eth1
    intfName = sys.argv[1] if len(sys.argv) > 1 else 'enp3s0f1'
    info('*** Connecting to hw intf: %s' % intfName)

    info('*** Checking', intfName, '\n')
    checkIntf(intfName)

    info('*** Creating network\n')
    if len(sys.argv) >= 2:
        net = exampleAllHosts(vlan=int(sys.argv[2]))
    else:
        net = Mininet(topo=SingleSwitchReversedTopo(k=1))

    switch = net.switches[0]
    info('*** Adding hardware interface', intfName, 'to switch',
         switch.name, '\n')
    _intf = Intf(intfName, node=switch)

    info('*** Note: you may need to reconfigure the interfaces for '
         'the Mininet hosts:\n', net.hosts, '\n')

    net.start()
    CLI(net)
    net.stop()
