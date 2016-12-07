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

# Usage
Get code:    
```
git clone https://github.com/michaelhenkel/tripleo-fabric-ansible
cd tripleo-fabric-ansible
```
Configuration:    
```
➜  inventory git:(master) ✗ cat hosts
[instack]
localhost ansible_user=root
[kvm]
5b3s30 ansible_host=10.87.64.31 vms=5 phy_int=l3 id_rsa_path=/root/.ssh/id_rsa
centos ansible_host=10.87.64.32 vms=5 phy_int=l3 id_rsa_path=/home/stack/.ssh/id_rsa_virt_power
5b3s32 ansible_host=10.87.64.33 vms=5 phy_int=l3 id_rsa_path=/root/.ssh/id_rsa
[undercloud]
192.168.122.27
[kvm:vars]
ansible_user=root
```
[instack]
localhost ansible_user=root -> the host on which the resulting instackenv.json will be created.

[kvm] -> this section contains all KVM hosts    
5b3s30 ansible_host=10.87.64.31 phy_int=l3 id_rsa_path=/root/.ssh/id_rsa
  |                     |           |                 |
  V                     V           V                 V
