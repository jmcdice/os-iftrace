#!/usr/bin/env python 
# Joey <joey.mcdonald@nokia.com>

import argparse, os
from novaclient import client as nova_client
from keystoneclient.v2_0 import client as keystone_client

class InstanceInfo:

    def __init__(self, uuid):
        self._uuid = uuid
        self._creds = self.get_nova_creds()
        self._vm_info = nova_client.Client(2, **self._creds)
        self._keystone_creds = self.get_keystone_creds()
        self._keystone = keystone_client.Client(**self._keystone_creds)

    def get_vm_nova_info(self, uuid):
        self._vm_obj = self._vm_info.servers.get(uuid)
        self._vm_dic = self._vm_obj.to_dict()
        print self._vm_dic['name'], self._vm_dic['created'], self._vm_dic['status'], self._vm_dic['OS-EXT-SRV-ATTR:host']

    def get_keystone_creds(self):
        stack = dict(auth_url=os.environ.get('OS_AUTH_URL'),
                     username=os.environ.get('OS_USERNAME'),
                     tenant_name=os.environ.get('OS_TENANT_NAME'),
                     password=os.environ.get('OS_PASSWORD'),
                     endpoint_type=os.environ.get('OS_ENDPOINT_TYPE', 'publicURL'))
        return stack

    def get_nova_creds(self):
        try:
            sourced = os.environ['OS_USERNAME']
        except KeyError:
            print "Please source OpenStack admin credentials."
            sys.exit(errno.EPERM)

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
    nova_show = guest.get_vm_nova_info(uuid) 
