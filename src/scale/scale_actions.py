#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from threading import Thread
import src.utils.config as config
import src.utils.helper as helper
import src.api.client as client
import src.utils.logger as logger

logger = logger.MyLogger.__call__().get_logger()


class ScaleExecutor(object):
    """
    This executor implements different scale options and actions during testing.
    """

    def __init__(self, scale_test_constraints=config.SCALE_TEST_CONSTRAINTS):
        self.base_vm_name = "cnv-scale-vm-"
        self.base_ns_name = "cnv-scale-ns-"
        self.vm_name_list = []
        self.action_list = ["start", "stop", "restart"]
        self.constraints = scale_test_constraints
        self.vm_yaml = scale_test_constraints['vm_yaml']
        self.start_vms = []
        self.stop_vms = []
        self.restart_vms = []
        self.client = client.Client()
        self.node_list = self.client.get_ready_node_list()

    def scale_out_with_openshift_scheduling(self, number_of_vms):
        """
        Scale out with openshift scheduler.
        Create new namespace according to kvm limit on node.
        (If limit is 110 and number of vms is 550 we will have 5 namespaces)
        :param number_of_vms: Total number of VM to scale out
        """
        logger.info(
            "Run ocp scheduling scale out with:\n number of vms :{number_of_vms}".format(number_of_vms=number_of_vms)
        )
        ns_counter = 1
        ns_name = "{ns_name}{counter}".format(ns_name=self.base_ns_name, counter=ns_counter)
        self.client.add_namespace(ns_name)
        max_kvm_devices = self.client.get_num_of_kvm_devices_from_node()
        for i in range(0, number_of_vms):
            if i % max_kvm_devices == 0:
                ns_name = "{ns_name}{counter}".format(ns_name=self.base_ns_name, counter=ns_counter)
                self.client.add_namespace(ns_name)
            vm_name = "{vm}{counter}".format(vm=self.base_vm_name, counter=i)
            self.add_vm(i, ns_name, vm_name)

    def add_vm(self, index, ns_name, vm_name):
        """
        Add VM and run it with virtctl
        :param index: VM index
        :param ns_name: Namespace name
        :param vm_name: VM name
        :return:
        """
        self.vm_name_list.append('{vm_name},{namespace}'.format(vm_name=vm_name, namespace=ns_name))
        self.client.create_vm(
            yaml_body=self.client.update_vm_yaml(
                yaml_file=self.vm_yaml, vm_name=vm_name,
                constraints=self.constraints
            ),
            namespace=ns_name
        )
        if not self.constraints["running_state"]:
            helper.execute_command(
                config.VIRTCTL_ACTION.format(
                    virtctl_path=config.VIRTCTL_PATH, action=self.action_list[0], vm_name=vm_name, namespace=ns_name
                )
            )
        time.sleep(1)
        if index > 0 and index % config.NUMBER_OF_VMS_IN_INTERVAL == 0:
            time.sleep(config.DELAY)
            self.client.get_vmis_status_summary()

    def _handle_threads(self, thread_info_list):
        """
        Get list with threads info and execute threads
        :param thread_info_list:
        """
        threads = []
        for args in thread_info_list:
            t = Thread(target=self.scale_up_one_node, kwargs=args)
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def scale_out_nodes_ramp_up(self, nodes_list, number_of_vms_per_node):
        """
        Scale out node by node (compute node list) with give number of VMs.
        :param nodes_list: Compute node list on cluster
        :param number_of_vms_per_node: number of vms per node (TBD: max is 250)
        """

        logger.info(
            "Run multi nodes scale out with:\n number of vms in node:{number_of_vms}".format(
                number_of_vms=number_of_vms_per_node
            )
        )
        ns_counter = 1
        pool_size = 1
        thread_pool = []
        if len(nodes_list) > 10:
            pool_size = len(nodes_list) / 10
            logger.debug("pool size: %s", pool_size)
        for node_name in nodes_list:
            ns_name = "{ns_name}{counter}".format(ns_name=self.base_ns_name, counter=ns_counter)
            ns_counter += 1
            thread_args = {
                'ns_name': ns_name,
                'number_of_vms_per_node': number_of_vms_per_node,
                'node_name': node_name
            }
            thread_pool.append(thread_args)
            if len(thread_pool) == pool_size:
                self._handle_threads(thread_info_list=thread_pool)
                thread_pool = []

    def scale_up_one_node(self, ns_name, number_of_vms_per_node, node_name=None):
        """
        Scale up one node
        :param node_name: Node name if none use the first node in compute nodes
        :param ns_name: Namespace name
        :param number_of_vms_per_node: Number of VM per node
        """
        logger.info("Enter single node: ns:{ns}  number of vms:{number_of_vms_per_node}  node_name:{node_name}".format(
            ns=ns_name, number_of_vms_per_node=number_of_vms_per_node, node_name=node_name
        ))
        self.client.add_namespace(ns_name)
        node_name = node_name if node_name is not None else self.node_list[0]
        self.constraints.update({'node_selector': node_name})
        logger.info(
            "Run single node scale up with:\n namespace:{ns}\n node:{node}\n number of vms:{number_of_vms}".format(
                ns=ns_name,
                number_of_vms=self.constraints['max_number_of_vm_per_node'],
                node=node_name)
        )
        for i in range(int(self.constraints['vm_offset']), number_of_vms_per_node):
            vm_name = "{vm}{counter}".format(vm=self.base_vm_name, counter=i)
            self.add_vm(i, ns_name, vm_name)
            helper.check_cpu_on_node(node_name=node_name)
        self.client.get_vmis_status_summary()
        helper.check_cpu_on_node(node_name=node_name)

    def vm_lifecycle(self, action, num_of_vms):
        """
        For given vm list execute vm lifecycle action: Start, Stop, Restart
        :param action: Action: Start, Stop, Restart
        :param num_of_vms: List size
        """
        err = "VM life cycle action: Action {action} requires that will be a least {vms}"
        vm_list = []

        if action not in self.action_list:
            logger.error("VM life cycle action:  Action {action} is not in list {action_list}".format(
                action_list=self.action_list, action=action
            )
            )
            return

        if action == self.action_list[0]:  # start action
            if len(self.stop_vms) >= num_of_vms:
                vm_list = self.stop_vms
            else:
                logger.error(err.format(action=action, vms=self.stop_vms))
        else:
            if len(self.vm_name_list) >= num_of_vms:
                vm_list = self.vm_name_list[0: num_of_vms]
            else:
                logger.error(err.format(action=action, vms=self.vm_name_list))
        for entity in vm_list:
            vm_name = entity.split(",")[0]
            ns_name = entity.split(",")[1]
            helper.execute_command(
                config.VIRTCTL_ACTION.format(
                    virtctl_path=config.VIRTCTL_PATH, action=action, vm_name=vm_name, namespace=ns_name
                )
            )
            time.sleep(1)
            eval("self.{action}_vms".format(action=action)).append(
                '{vm_name},{namespace}'.format(vm_name=vm_name, namespace=ns_name)
            )
        logger.info(eval("self.{action}_vms".format(action=action)))

    def execute(self):
        """
        Run the scenarios according to the constraints configure in the yaml.
        """
        # single node scale up
        if self.constraints['current_test'] == config.SINGLE_NODE:
            ns_name = "{ns_name}{counter}".format(ns_name=self.base_ns_name, counter=1)
            self.scale_up_one_node(
                ns_name=ns_name,
                number_of_vms_per_node=int(self.constraints['max_number_of_vm_per_node']),
                node_name=self.constraints['node'])
        # multi nodes scale out
        if self.constraints['current_test'] == config.MULTI_NODE:
            self.scale_out_nodes_ramp_up(
                nodes_list=self.node_list,
                number_of_vms_per_node=int(self.constraints['max_number_of_vm_per_node'])
            )
        # ocp scheduling scale out
        if self.constraints['current_test'] == config.OCP_SCHEDULING:
            self.scale_out_with_openshift_scheduling(number_of_vms=self.constraints['total_vms'])
        # vm lifecycle
        count = 0
        action_list_ = self.constraints['vm_lifecycle_action_list']
        if action_list_:
            num_of_vms = int(self.constraints['vm_lifecycle_number_of_vms'])
            while self.client.get_vmis_at_status(config.VMI_STATUS[0]) < int(num_of_vms) and count <= 10:
                time.sleep(60)
                count += 1
            for action in action_list_.split(","):
                self.vm_lifecycle(action=action, num_of_vms=num_of_vms)
