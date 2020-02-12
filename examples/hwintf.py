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


def exampleAllHosts(vlanList):
    """Simple example of how VLANHost can be used in a script"""
    # This is where the magic happens...
    hostList = []
    for eachVlan in vlanList:
        hostList.append(partial(VLANHost, vlan=int(eachVlan)))

    # Start a basic network using our VLANHost
    topo = SingleSwitchReversedTopo(k=5)
    # Pass new switch config to this as well
    net = Mininet(host=hostList, topo=topo)
    switch1 = net.switches[0]
    # We need to tag each of these ports with each vlan in vlanList

    # Once tagged, pass it back into net as new switch
    # net = Mininet(host=hostList, topo=topo, switch=switch1)
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
        if len(sys.argv) > 1:
            vlanList = []
            # sys.argv[0] is the program filename, slice it off
            # sys.argv[1] is the hw_intf_name, slice it off
            for element in sys.argv[2:]:
                vlanList.append(element)
    if len(sys.argv) >= 2:
        net = exampleAllHosts(vlanList)
        # net = exampleAllHosts(vlan=int(sys.argv[2]))

    switch = net.switches[0]
    _intf = Intf('s1-tagged', node=switch)
    info('*** Adding hardware interface', intfName, 'to switch',
         switch.name, '\n')
    _intf = Intf(intfName, node=switch)

    info('*** Note: you may need to reconfigure the interfaces for '
         'the Mininet hosts:\n', net.hosts, '\n')

    net.start()
    CLI(net)
    net.stop()
