#!/usr/bin/env python
# -*- coding: utf-8 -*-


#  scenarios
SINGLE_NODE = "single_node"
MULTI_NODE = "multi_node"
OCP_SCHEDULING = "ocp_scheduling"


# virtctl
VIRTCTL_ACTION = "{virtctl_path} {action} {vm_name} -n {namespace}"


# general
OC_PATH = "/usr/bin/oc"
VIRTCTL_PATH = "/usr/bin/virtctl"
DELAY = 30  # delay between X running VMs
NUMBER_OF_VMS_IN_INTERVAL = 10
VMI_STATUS = ["Running", "Scheduling", "Pending", "Unknown", "CrashLoopBackOff"]
TEST_SCALE = "scale"
LOG_FILE = "/tmp/enduranceRunner.log"

# test info
SCALE_TEST_CONSTRAINTS = {
    'node': None,    # for single single
    'vm_yaml': "../../manifests/cirros_vm.yaml",
    'oc_path': "/usr/bin/oc",
    'virtctl_path': "/usr/bin/virtctl",
    'current_test': SINGLE_NODE,
    'node_selector': True,
    'running_state': False,
    'vm_cpu': None,
    'vm_memory': None,
    'max_number_of_vm_per_node': 110,
    'ocp_scheduling_total_vms': 1100,  # for ocp scheduling
    'delay_between_intervals': DELAY,
    'number_of_vms_in_interval': NUMBER_OF_VMS_IN_INTERVAL,
    'vm_lifecycle_action_list': 'stop',
    'vm_lifecycle_number_of_vms': 1,
    'vm_offset': 0
}


TESTS_CONF = {
    TEST_SCALE: ["conf/scale_test.yaml", SCALE_TEST_CONSTRAINTS]
}


