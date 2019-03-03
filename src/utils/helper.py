#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import yaml
import shlex
import time
from pprint import pformat
import copy
from . import config, logger

CPU_IDLE_CHECK = "ssh -o StrictHostKeyChecking=no root@{node_name} top -bn1"
CPU_IDLE_CHECK_PIPE = "grep Cpu "

logger = logger.MyLogger.__call__().get_logger()


def execute_command(command):
    """
    Execute command
    :param command: command

    """
    output = ""
    try:
        output, err = subprocess.Popen(shlex.split(command)).communicate()
    except subprocess.CalledProcessError as err:
        logger.error("Failed to execute command {cmd} , err {err}".format(cmd=command, err=err))
    except Exception as err:
        logger.error("Failed to execute command {cmd} ,  err {err}".format(cmd=command, err=err))
    return output


def configuration_parser():
    """
    Parse the test yaml. First check the 'current_test' and update
    the dict SCALE_TEST_CONSTRAINTS with test constraints.
    """
    test_new_config = {}
    test_name = ""
    for key in config.TESTS_CONF.keys():
        yaml_obj = None
        test_name = key
        yaml_file = config.TESTS_CONF[key][0]
        config_dict = config.TESTS_CONF[key][1]

        with open(yaml_file, 'r') as stream:
            try:
                yaml_obj = yaml.load(stream)
            except yaml.YAMLError as exc:
                logger.error("Failed to read yaml file {yaml}, err: \n {err}".format(yaml=yaml_file, err=exc.message))
                exit(1)

        test_new_config = copy.deepcopy(config_dict)
        current_test = yaml_obj['current_test']
        test_new_config.update({'vm_offset': yaml_obj['constraints']['vm_offset']})
        test_new_config.update({'current_test': current_test})
        test_new_config['vm_yaml'] = yaml_obj['vm_yaml']
        test_new_config['oc_path'] = yaml_obj['general']['oc_path']
        test_new_config['virtctl_path'] = yaml_obj['general']['virtctl_path']
        test_new_config.update(yaml_obj['vm_info'])
        test_new_config.update(yaml_obj['constraints'])
    logger.info("For test {test_name} using this configration: \n {config}".format(
        test_name=test_name, config=pformat(test_new_config))
    )
    return test_new_config


def check_cpu_on_node(node_name):
    """
    Check CPU idle status on node. If idle is lower then 20%
    Wait till CPU idle is more then 20% again.
    :param node_name: node address (node_name)
    """
    idle_status = _get_cpu_idle_status(node_name)
    logger.info("idle status: %s", idle_status)
    while float(idle_status) < 20.0:
        logger.info("CPU usage is above 80% , current idle status: {idle_status}".format(idle_status=idle_status))
        time.sleep(10)
        idle_status = _get_cpu_idle_status(node_name)


def _get_cpu_idle_status(node_name):
    p1 = subprocess.Popen(shlex.split(CPU_IDLE_CHECK.format(node_name=node_name)), stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "Cpu"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    output = p2.communicate()[0]
    fields = output.strip().split()
    logger.info('out %s', output)
    return fields[7]

