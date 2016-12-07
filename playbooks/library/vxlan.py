#!/usr/bin/python

from pyroute2 import IPDB
from ansible.module_utils.basic import *

def main():
  fields = {
    "ifname": {"required": True, "type": "str"},
    "mcast_group": {"required": True, "type": "str"},
    "vxlan_link": {"required": True, "type": "str"},
    "vni": {"required": True, "type": "str"},
    "state": {
       "default": "present", 
       "choices": ['present', 'absent'],  
       "type": 'str' 
    },
  }
  module = AnsibleModule(argument_spec=fields)
  #response = {"interface": " already exists"}
  #response = {"interface": module.params['ifname'] }
  #module.exit_json(changed=False, meta=response)
  ip = IPDB()
  if module.params['state'] == 'present':
    if module.params['ifname'] in ip.by_name.keys():
      response = {"interface": module.params['ifname'] + " already exists"}
      module.exit_json(changed=False, meta=response)
    else:
      with ip.create(ifname=module.params['ifname'],
        kind='vxlan',
        vxlan_link=ip.interfaces[module.params['vxlan_link']],
        vxlan_id=int(module.params['vni']),
        vxlan_group=module.params['mcast_group'],
	vxlan_ttl=16) as i:
        i.up()
      response = {"interface": module.params['ifname'] + " created"}
      module.exit_json(changed=False, meta=response)


if __name__ == '__main__':  
  main()
