# Endurance
Repository for endurance (Scale, Performance) testing on KubeVirt.

## Scale testing 
In order to run scale test you need to use the conf/scale_test.yaml
Test options:
1. Scenarios (current_test parameter): 
- single_node: Load single openshift node with configure number of VMS
- multi_node: Load all compute nodes in openshift cluster, use threads to load parallel nodes
- ocp_scheduling: Load VMs use openshift scheduler 
- [TBD: Node by Node]

2. VM yaml: you can choose form manifests, or add your vm yaml
3. General: set oc and virtctl path
4. VM info: 
   node_selector: Use openshift node selector to run VM on specific node (True/False).  
   running_state: Set Running to true means it will start at create (True/False).
   vm_cpu: VM CPU
   vm_memory: VM Memory
5. Constraints:
    vm_offset: From which index to start VM (default '0')
    vm_lifecycle_action_list: After the scale test reach his target we can run VM life cycle actions: start, stop, restart
    vm_lifecycle_number_of_vms: Amount of VM to do the life cycle actions
    node: Specify on which node to run like: 'cnv-executor-ipinto-node1.example.com'
    max_number_of_vm_per_node: Man of VM to run on Node 
    number_of_vms_in_interval: We load with intervals and sleep between them set the nuber of VM per interval.
    delay_between_intervals: Sleep time in seconds
    ocp_scheduling_total_vms: Max number of VMs to run with openshift scheduler 


## install
Run setup.py
