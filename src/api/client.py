#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml
import logging
import urllib3
from kubernetes import config as kube_config
from openshift.dynamic import DynamicClient
import src.utils.config as config
import src.utils.logger as logger

logger = logger.MyLogger.__call__().get_logger()


class Client(object):
    def __init__(self):
        urllib3.disable_warnings()
        try:
            self.dyn_client = DynamicClient(kube_config.new_client_from_config())
        except kube_config.ConfigException:
            logger.error("You need to be login to cluster")
            exit(1)
        except urllib3.exceptions.MaxRetryError:
            logger.error("You need to be login to cluster")
            exit(1)

    def get_num_of_kvm_devices_from_node(self):
        """
        Get from the first compute node the number of devices
        :return: int number of devices
        """
        label_selector = 'node-role.kubernetes.io/compute=true'
        v1_nodes = self.dyn_client.resources.get(api_version='v1', kind='Node').get(
            label_selector=label_selector).items
        return int(v1_nodes[0]['status']['capacity']['devices.kubevirt.io/kvm'])

    def get_ready_node_list(self, label_selector='node-role.kubernetes.io/compute=true'):
        """
        Return list of node in the desire state
        :return: List of nodes name
        """
        node_list = []
        v1_nodes = self.dyn_client.resources.get(api_version='v1', kind='Node').get(label_selector=label_selector).items
        for node in v1_nodes:
            for condition in node.status.conditions:
                if condition.reason == 'KubeletReady' and condition.status == 'True':
                    node_list.append(node.metadata.name)
        return node_list

    def add_namespace(self, ns_name):
        """
        Add namespace
        :param ns_name: namespace name
        """

        v1_ns = self.dyn_client.resources.get(api_version='v1', kind='Namespace')
        ns_body = {
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {'name': ns_name}
        }

        v1_ns.create(body=ns_body, namespace='default')
        logging.info("Namespace {ns} added".format(ns=ns_name))

    def get_vmis(self):
        """
        Return List with all the VMI objects
        :return: list
        """
        return self.dyn_client.resources.get(api_version='kubevirt.io/v1alpha3', kind='VirtualMachineInstance')

    def get_vmis_at_status(self, status):
        """
        Return List with all the VMIs in status
        VMI status: Running,Scheduling, Pending, Unknown, CrashLoopBackOff
        :return: list
        """
        return [vmi for vmi in self.get_vmis().get().items if vmi.status.phase == status]

    def update_vm_yaml(self, yaml_file, vm_name, constraints):
        """
        Get base VM yaml and update with name and constraints
        :param yaml_file: Path to yaml file
        :param vm_name: VM name to update the yaml
        :param constraints: dict with constraints for this VM:
                            like { 'nodeSelector': 'nodeName'}
        :return: updated yaml object
        """
        yaml_obj = None
        with open(yaml_file, 'r') as stream:
            try:
                yaml_obj = yaml.load(stream)
            except yaml.YAMLError as exc:
                logger.error("Failed to read yaml file {yaml}, err: \n {err}".format(yaml=yaml_file, err=exc.message))
                exit(1)
        yaml_obj['metadata']['name'] = vm_name
        if "node_selector" in constraints.keys():
            yaml_obj['spec']['template']['spec'].update({'nodeSelector': {'kubernetes.io/hostname': constraints['node_selector']}})
        if "running_state" in constraints.keys():
            yaml_obj['spec'].update({'running': constraints['running_state']})
        if "cpu" in constraints.keys():
            yaml_obj['spec']['domain'].update({'cpu': constraints['cpu']})
        if "memory" in constraints.keys():
            yaml_obj['spec']['resources']['requests'].update({'memory': constraints['memory']})
        return yaml_obj

    def create_vm(self, yaml_body, namespace='default'):
        """
        Create VM with given yaml
        :param yaml_body: yaml body
        :param namespace: namespace to create vm
        """
        v3_vms = self.dyn_client.resources.get(api_version='kubevirt.io/v1alpha3', kind='VirtualMachine')
        v3_vms.create(body=yaml_body, namespace=namespace)

    def get_vmis_status_summary(self):
        """
        Print amount of VMIs at each status
        :return dict with status: vmi amount
        """
        vmi_summary = {}
        logging.info("VMIs status:")
        logger.info("VMIs status:\n")

        for status in config.VMI_STATUS:
            num_of_vms = len(self.get_vmis_at_status(status))
            out_format = "{status} VMIs:  {amount_of_vms}".format(status=status, amount_of_vms=num_of_vms)
            logger.info(out_format)
            logging.info(out_format)
            vmi_summary.update({status:num_of_vms})
        return vmi_summary
