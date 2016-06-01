#!/usr/bin/env python 
#
# Trace the hosting network stack for a particular VM in openstack.
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

    def get_vm_info(self, uuid):
        self._vm_obj = self._vm_info.servers.get(uuid)
        self._dump = self._vm_obj.to_dict()
        #print json.dumps(self._dump, indent=4)

    def get_interface_list(self, uuid):
        self._neutron = neutron_client.Client(endpoint_url=self._neutron_api, token=self._keystone.auth_token)
        ports = self._neutron.list_ports(device_id=uuid).get('ports', [])
        #print json.dumps(ports, indent=4)
        for port in ports:
            print "Port ID: %s" % port['id'][:11]
            print "Network ID: %s" % port['network_id']
            print "Subnet ID: %s" % port['fixed_ips'][0]['subnet_id']
            print "Mac Address: %s" % port['mac_address']
            print "IP Address: %s\n" % port['fixed_ips'][0]['ip_address']
            

    def get_keystone_creds(self):
        stack = dict(auth_url=os.environ.get('OS_AUTH_URL'),
                     username=os.environ.get('OS_USERNAME'),
                     tenant_name=os.environ.get('OS_TENANT_NAME'),
                     password=os.environ.get('OS_PASSWORD'),
                     endpoint_type=os.environ.get('OS_ENDPOINT_TYPE', 'publicURL'))
        return stack


    def get_nova_creds(self):
        d = {}
        d['username'] = os.environ['OS_USERNAME']
        d['api_key'] = os.environ['OS_PASSWORD']
        d['auth_url'] = os.environ['OS_AUTH_URL']
        d['project_id'] = os.environ['OS_TENANT_NAME']
        return d


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Attempt to debug a guest VM interface.')
    parser.add_argument('--uuid', dest='instance', help='UUID for a specified running VM')
    args = parser.parse_args()

    uuid = args.instance

    guest = InstanceInfo(uuid)
    #blob = guest.get_vm_info(uuid)
    blob = guest.get_interface_list(uuid)
