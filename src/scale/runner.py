#!/usr/bin/env python
# -*- coding: utf-8 -*-

from src.utils import helper
import src.scale.scale_actions as executor
import src.utils.logger as logger

logger = logger.MyLogger.__call__().get_logger()


def test_pool(node_name,ns_name,number_of_vms_per_node):
    import time
    print ("enter test pool with %s %s %s", ns_name,node_name, number_of_vms_per_node )
    for i in range(0, 10):
        print i
        time.sleep(1)

def runner():
    logger.info(' -------------------------')
    logger.info(' ----- Started -----------')
    test_conf = helper.configuration_parser()
    scale_executor = executor.ScaleExecutor(scale_test_constraints=test_conf)
    scale_executor.execute()


def main():
    runner()


if __name__ == "__main__":
    main()
