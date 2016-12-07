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
➜  tripleo-fabric-ansible git:(master) ✗ cat hosts
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
  - name: control # defines the ironic node name and must match the nova flavor used
    count: 1 # specifies the number of virsh VMs PER KVM host 
             # (in this example: 3 KVM hosts * 1 control = 3 control node vms in ironic)
  - name: compute
    count: 2
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
