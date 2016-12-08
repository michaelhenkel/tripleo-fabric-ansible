# tripleo-fabric-ansible
This set of Ansible scripts prepares mutliple hosts to be used as KVM hosts for overcloud VMs.    

Functions:    
- setup OVS bridges per physical interface on the overcloud VMs    
- connect OVS bridges through VxLAN tunnels    
- define virsh networks per physical interface on the overcloud VMs    
- define virsh VMs as targets for the overcloud VMs    
- creates an instackenv.json file for openstack import on the undercloud VM    

Prerequisites:    
- Ansible 2.2 on the machine running the ansible scripts    
- python-pyroute2 on KVM hosts
- KVM hosts must be CentOS/RHEL >= 7.2 or Ubuntu >= 16.04    
- libvirtd on the KVM hosts must be configured to allow tcp connections without requiring TLS    

Known Restrictions:    
- Before running existing virsh VMs must be undefined    

# Get code:    
```
git clone https://github.com/michaelhenkel/tripleo-fabric-ansible
cd tripleo-fabric-ansible
```
# Configuration:    
```
➜  tripleo-fabric-ansible git:(master) ✗ cat inventory/hosts
[instack]
localhost ansible_user=root
# the host on which the resulting instackenv.json will be created. 
[kvm]
# this section contains all KVM hosts
# phy_int = interface used for the VxLAN connections
# id_rsa_path = path to key used for remote libvirtd connection
5b3s30 ansible_host=10.87.64.31 phy_int=l3 id_rsa_path=/root/.ssh/id_rsa
centos ansible_host=10.87.64.32 phy_int=l3 id_rsa_path=/home/stack/.ssh/id_rsa_virt_power
5b3s32 ansible_host=10.87.64.33 phy_int=l3 id_rsa_path=/root/.ssh/id_rsa
[kvm:vars]
ansible_user=root
```

The virsh VMs are defined in inventory/group_vars/kvm.yml
```
➜  tripleo-fabric-ansible git:(master) ✗ cat inventory/group_vars/kvm.yml
---
virtual_machines:
  - name: control # defines the ironic node name and must match the nova flavor used in tripleo
    count: 1 # specifies the number of virsh VMs PER KVM host 
             # example: 3 KVM hosts * 1 control = 3 control vms in ironic
  - name: compute
    count: 2 # example: 3 KVM hosts * 1 compute = 6 compute vms in ironic 
  - name: contrail-controller
    count: 1
  - name: contrail-analytics
    count: 1
  - name: contrail-analytics-database
    count: 1
```

The interface definition file must match the nic heat templates on the undercloud.    
For each interface of type phy or bridge an OVS bridge will be created.    
```
➜  tripleo-fabric-ansible git:(master) ✗ cat playbooks/vars/nics.yml
---
nics:
  - name: nic1             # nic index 
    vxlan_name: vxlan0     # vxlan interface which will be created for that bridge
    type: phy              # phy/bridge/vlan
    network: control_plane # tripleo network name
    br_name: brbm          # bridge name
    gateway: true          # no use atm 
    mcast_group: 239.0.0.1 # mcast group for the bridge
    vni: 42                # vxlan vni for the bridge
  - name: nic2
    vxlan_name: vxlan1
    type: phy
    network: internal_api
    br_name: br-int-api
    gateway: false
    mcast_group: 239.0.0.2
    vni: 43
  - name: nic3
    vxlan_name: vxlan2
    type: bridge
    br_name: br-mgmt
    mcast_group: 239.0.0.3
    vni: 44
  - name: nic4
    type: vlan
    id: 10
    network: external_api
  - name: nic5
    type: vlan
    id: 20
    network: storage
  - name: nic6
    type: vlan
    id: 30
    network: storage_mgmt
  - name: nic7
    type: vlan
    id: 40
    network: management
```
The above example adds 3 nics to the VM. nic 1 is assinged to the control_plane and nic 2 to the internal_api network.    
nic 3 is used to bind a linux bridge to it. On that bridge nic 4 to 6 are defined as vlan interfaces.    

Host network layout:    
```
+----------------------------------------------------------------------------+
|                                                                            |
|  KVM Host 5b3s30                                                           |
|                                                                            |
|    +---------------------------------------------------------------------+ |
|    |   OVERCLOUD VM                                                      | |
| +--+------------------------------------------------------------------+  | |
| |   OVERCLOUD VM                             +---+ +---+ +---+ +---+  |  | |
| |                                            |V10| |V20| |V30| |V40|  |  | |
| |                                            +---+ +---+ +---+ +---+  |  | |
| |      +----+                  +----+          +-----------------+    |  | |
| |      |eth0|                  |eth1|                |eth2|           +--+ |
| +---------+----------------------+----------------------+-------------+    |
|           |                      |                      |                  |
| +---------+-----------+ +--------+------------+ +-------+-------------+    |
| | nw:   control_plane | | nw:   internal_api  | | nw:   NA            |    |
| | br:   brbm          | | br:   br-int-api    | | br:   br-mgmt       |    |
| | vtep: vxlan0        | | vtep: vxlan1        | | vtep: vxlan2        |    |
| |                     | |                     | |                     |    |
| +----------+----------+ +----------+----------+ +----------+----------+    |
|            |                       |                       |               |
|            +-----------------------+-----------------------+               |
|                                 |eth0|                                     |
+----------------------------------------------------------------------------+
```

Network layout:
```
+----------+  +----------+  +----------+
| KVM Host |  | KVM Host |  | KVM Host |
| 5b3s30   |  | centos   |  | 5b3s31   |
|          |  |          |  |          |
|  +----+  |  |  +----+  |  |  +----+  |
|  |eth0|  |  |  |eth0|  |  |  |eth0|  |
+----+-----+  +----+-----+  +-----+----+
     |             |              |
+----+-------------+--------------+----+
|               IP FABRIC              |
+--------------------------------------+
```

# Run    
```
➜  tripleo-fabric-ansible git:(master) ✗ ansible-playbook -i inventory playbooks/environment_creator.yml
```

# Result
```
➜  tripleo-fabric-ansible git:(master) ✗ ll /tmp/instackenv.json
-rw-r--r--  1 mhenkel  935    38K Dec  7 22:06 /tmp/instackenv.json
```

The instackenv.json file must be copied to the undercloud VM and imported with    
```
openstack baremetal import instackenv.json
```
after that ironic should have all nodes registered:
```
[stack@instack ~]$ ironic node-list
+--------------------------------------+-----------------------------------------+---------------+-------------+--------------------+-------------+
| UUID                                 | Name                                    | Instance UUID | Power State | Provisioning State | Maintenance |
+--------------------------------------+-----------------------------------------+---------------+-------------+--------------------+-------------+
| 81fd154e-2a03-4561-a339-345f53a9f1bb | control_1_at_5b3s30                     | None          | power off   | available          | False       |
| 42b2006b-8c94-4e4c-b8be-7e35183d6c73 | compute_1_at_5b3s30                     | None          | power off   | available          | False       |
| 8fe1ba2e-9c11-482f-bced-5bba5a26f5ab | compute_2_at_5b3s30                     | None          | power off   | available          | False       |
| a9e64fd1-e62f-4fb5-bb61-d1dae765e8fc | contrail-controller_1_at_5b3s30         | None          | power off   | available          | False       |
| adea96c8-e3ec-4f69-ba16-d56830d59d77 | contrail-analytics_1_at_5b3s30          | None          | power off   | available          | False       |
| 34905810-6c9b-4f71-8b00-a56b09a8a73f | contrail-analytics-database_1_at_5b3s30 | None          | power off   | available          | False       |
| eb6a5ccc-15b5-4dca-bcb5-6553f42c2767 | control_1_at_centos                     | None          | power off   | available          | False       |
| 6f0b629f-3909-446a-b46c-270c00d5fbb4 | compute_1_at_centos                     | None          | power off   | available          | False       |
| 949ee869-e35a-480d-82b1-cb6e260d2154 | compute_2_at_centos                     | None          | power off   | available          | False       |
| 3f6e48d9-43d7-42df-bc04-9a5ed81301c1 | contrail-controller_1_at_centos         | None          | power off   | available          | False       |
| 5c22cfd1-1ca1-48dc-9245-059786034267 | contrail-analytics_1_at_centos          | None          | power off   | available          | False       |
| 8bd2c6c9-08af-426c-a30e-0c33877089d8 | contrail-analytics-database_1_at_centos | None          | power off   | available          | False       |
| fda9b876-f210-46e4-81d6-981bc798bd9f | control_1_at_5b3s32                     | None          | power off   | available          | False       |
| 3efed294-f6d7-4ade-ab50-714346e2f8ad | compute_1_at_5b3s32                     | None          | power off   | available          | False       |
| 6bd0a12b-6d0a-4a9a-9dc5-25a98d215598 | compute_2_at_5b3s32                     | None          | power off   | available          | False       |
| bd52e355-15d6-4e2b-af44-a731c2f49ca2 | contrail-controller_1_at_5b3s32         | None          | power off   | available          | False       |
| 729988c0-90b2-497b-8c9c-de70ad3dc4ca | contrail-analytics_1_at_5b3s32          | None          | power off   | available          | False       |
| a6dfe15a-e26a-49d4-ac24-03059c5eca14 | contrail-analytics-database_1_at_5b3s32 | None          | power off   | available          | False       |
+--------------------------------------+-----------------------------------------+---------------+-------------+--------------------+-------------+
```
Picking a node shows the associated profile:
```
[stack@instack ~]$ openstack baremetal node show a6dfe15a-e26a-49d4-ac24-03059c5eca14 -c properties
+------------+---------------------------------------------------------------------------------------------------------------+
| Field      | Value                                                                                                         |
+------------+---------------------------------------------------------------------------------------------------------------+
| properties | {u'memory_mb': u'16384', u'cpu_arch': u'x86_64', u'local_gb': u'50', u'cpus': u'4', u'capabilities':          |
|            | u'profile:contrail-analytics-database,cpu_vt:true,cpu_hugepages:true,boot_option:local'}                      |
+------------+---------------------------------------------------------------------------------------------------------------+
```
