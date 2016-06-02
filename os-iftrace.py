#!/usr/bin/env python 
#
# Trace the hosting network stack for a particular VM.
#
# Joey <joey.mcdonald@nokia.com>

import argparse
import logging
import json
import os

from novaclient import client as nova_client
from neutronclient.v2_0 import client as neutron_client
from prettytable import PrettyTable
from keystoneclient.v2_0 import client as keystone_client

logging.basicConfig(date_fmt='%m-%d %H:%M', level=logging.CRITICAL)
LOG = logging.getLogger('InstanceInfo')

class InstanceInfo:

    def __init__(self, uuid):
        self._uuid = uuid
        self._creds = self.get_nova_creds()
        self._vm_info = nova_client.Client(2, **self._creds)
        self._keystone_creds = self.get_keystone_creds()
        self._keystone = keystone_client.Client(**self._keystone_creds)
        self._neutron_api = self._keystone.service_catalog.url_for(service_type='network', endpoint_type='internalURL')
        self._neutron = neutron_client.Client(endpoint_url=self._neutron_api, token=self._keystone.auth_token)

    def get_vm_nova_info(self, uuid):
        self._vm_obj = self._vm_info.servers.get(uuid)
        self._vm_dic = self._vm_obj.to_dict()
        self._vm_keys = ['name', 'created', 'status', 'OS-EXT-SRV-ATTR:host']
	table = PrettyTable(['VM Name', 'Created', 'Health/Status', 'Compute'])
        table.add_row([self._vm_dic['name'], self._vm_dic['created'], self._vm_dic['status'], 
		       self._vm_dic['OS-EXT-SRV-ATTR:host']])
        return table

    def get_vm_port_info(self, uuid):
        self._ports = self._neutron.list_ports(device_id=uuid).get('ports', [])
	table = PrettyTable(['Port ID', 'Network', 'Subnet', 'Mac Address', 'IP Address'])
        for port in self._ports:
            table.add_row([port['id'][:11], port['network_id'], port['fixed_ips'][0]['subnet_id'], 
			   port['mac_address'], port['fixed_ips'][0]['ip_address']]) 

        return table

    def get_hosting_compute(self, uuid):
        self._vm_obj = self._vm_info.servers.get(uuid)
        self._vm_dic = self._vm_obj.to_dict()
        #print json.dumps(self._vm_dic, indent=4)
        return self._vm_dic['OS-EXT-SRV-ATTR:host']

    def get_vm_port_path(self, uuid):
        self._compute = guest.get_hosting_compute(uuid)
        self._ports = self._neutron.list_ports(device_id=uuid).get('ports', [])
        table = PrettyTable(['Compute', 'Mac Address', 'IP Address', 'Tap Interface', 'Linux Bridge', 'Veth0', 'Veth1'])
        for port in self._ports:
            self._id = port['id'][:11]
	    self._mac = port['mac_address']
	    self._ip = port['fixed_ips'][0]['ip_address']
            table.add_row([self._compute, self._mac, self._ip, 'tap'+self._id, 'qbr'+self._id, 'qvb'+self._id, 'qvo'+self._id])

        return table

    def get_keystone_creds(self):
        stack = dict(auth_url=os.environ.get('OS_AUTH_URL'),
                     username=os.environ.get('OS_USERNAME'),
                     tenant_name=os.environ.get('OS_TENANT_NAME'),
                     password=os.environ.get('OS_PASSWORD'),
                     endpoint_type=os.environ.get('OS_ENDPOINT_TYPE', 'publicURL'))
        return stack

    def get_nova_creds(self):
        creds = {}
        creds['username'] = os.environ['OS_USERNAME']
        creds['api_key'] = os.environ['OS_PASSWORD']
        creds['auth_url'] = os.environ['OS_AUTH_URL']
        creds['project_id'] = os.environ['OS_TENANT_NAME']
        return creds


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Attempt to debug a guest VM interface.')
    parser.add_argument('--uuid', dest='instance', help='UUID for a specified running VM')
    args = parser.parse_args()
    uuid = args.instance

    guest = InstanceInfo(uuid)

    # Get nova information
    nova_show = guest.get_vm_nova_info(uuid) 
    #print nova_show 
   
    # Get neutron information
    net_show = guest.get_vm_port_info(uuid)
    # print net_show

    path_show = guest.get_vm_port_path(uuid)
    print path_show
