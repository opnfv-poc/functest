#!/usr/bin/env python

# Copyright (c) 2018 Orange and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

"""Ease deploying a single VM reachable via ssh

It offers a simple way to create all tenant network ressources + a VM for
advanced testcases (e.g. deploying an orchestrator).
"""

import logging
import tempfile
import time

import paramiko
from xtesting.core import testcase

from functest.core import tenantnetwork
from functest.utils import config


class VmReady1(tenantnetwork.TenantNetwork1):
    """Prepare a single VM (scenario1)

    It inherits from TenantNetwork1 which creates all network resources and
    prepares a future VM attached to that network.

    It ensures that all testcases inheriting from SingleVm1 could work
    without specific configurations (or at least read the same config data).
    """
    # pylint: disable=too-many-instance-attributes

    __logger = logging.getLogger(__name__)
    filename = '/home/opnfv/functest/images/cirros-0.4.0-x86_64-disk.img'
    visibility = 'private'
    extra_properties = None
    flavor_ram = 512
    flavor_vcpus = 1
    flavor_disk = 1
    flavor_alt_ram = 1024
    flavor_alt_vcpus = 1
    flavor_alt_disk = 1

    image_format = 'qcow2'

    def __init__(self, **kwargs):
        if "case_name" not in kwargs:
            kwargs["case_name"] = 'vmready1'
        super(VmReady1, self).__init__(**kwargs)
        self.orig_cloud = self.cloud
        self.image = None
        self.flavor = None

    def publish_image(self, name=None):
        """Publish image

        It allows publishing multiple images for the child testcases. It forces
        the same configuration for all subtestcases.

        Returns: image

        Raises: expection on error
        """
        assert self.cloud
        image = self.cloud.create_image(
            name if name else '{}-img_{}'.format(self.case_name, self.guid),
            filename=getattr(
                config.CONF, '{}_image'.format(self.case_name),
                self.filename),
            meta=getattr(
                config.CONF, '{}_extra_properties'.format(self.case_name),
                self.extra_properties),
            disk_format=getattr(
                config.CONF, '{}_image_format'.format(self.case_name),
                self.image_format),
            visibility=getattr(
                config.CONF, '{}_visibility'.format(self.case_name),
                self.visibility))
        self.__logger.debug("image: %s", image)
        return image

    def create_flavor(self, name=None):
        """Create flavor

        It allows creating multiple flavors for the child testcases. It forces
        the same configuration for all subtestcases.

        Returns: flavor

        Raises: expection on error
        """
        assert self.orig_cloud
        flavor = self.orig_cloud.create_flavor(
            name if name else '{}-flavor_{}'.format(self.case_name, self.guid),
            getattr(config.CONF, '{}_flavor_ram'.format(self.case_name),
                    self.flavor_ram),
            getattr(config.CONF, '{}_flavor_vcpus'.format(self.case_name),
                    self.flavor_vcpus),
            getattr(config.CONF, '{}_flavor_disk'.format(self.case_name),
                    self.flavor_disk))
        self.__logger.debug("flavor: %s", flavor)
        self.orig_cloud.set_flavor_specs(
            flavor.id, getattr(config.CONF, 'flavor_extra_specs', {}))
        return flavor

    def create_flavor_alt(self, name=None):
        """Create flavor

        It allows creating multiple alt flavors for the child testcases. It
        forces the same configuration for all subtestcases.

        Returns: flavor

        Raises: expection on error
        """
        assert self.orig_cloud
        flavor = self.orig_cloud.create_flavor(
            name if name else '{}-flavor_alt_{}'.format(
                self.case_name, self.guid),
            getattr(config.CONF, '{}_flavor_alt_ram'.format(self.case_name),
                    self.flavor_alt_ram),
            getattr(config.CONF, '{}_flavor_alt_vcpus'.format(self.case_name),
                    self.flavor_alt_vcpus),
            getattr(config.CONF, '{}_flavor_alt_disk'.format(self.case_name),
                    self.flavor_alt_disk))
        self.__logger.debug("flavor: %s", flavor)
        self.orig_cloud.set_flavor_specs(
            flavor.id, getattr(config.CONF, 'flavor_extra_specs', {}))
        return flavor

    def boot_vm(self, name=None, **kwargs):
        """Boot the virtual machine

        It allows booting multiple machines for the child testcases. It forces
        the same configuration for all subtestcases.

        Returns: vm

        Raises: expection on error
        """
        assert self.cloud
        vm1 = self.cloud.create_server(
            name if name else '{}-vm_{}'.format(self.case_name, self.guid),
            image=self.image.id, flavor=self.flavor.id,
            auto_ip=False, wait=True,
            network=self.network.id,
            **kwargs)
        vm1 = self.cloud.wait_for_server(vm1, auto_ip=False)
        self.__logger.debug("vm: %s", vm1)
        return vm1

    def run(self, **kwargs):
        """Boot the new VM

        Here are the main actions:
        - publish the image
        - create the flavor

        Returns:
        - TestCase.EX_OK
        - TestCase.EX_RUN_ERROR on error
        """
        status = testcase.TestCase.EX_RUN_ERROR
        try:
            assert self.cloud
            super(VmReady1, self).run(**kwargs)
            self.image = self.publish_image()
            self.flavor = self.create_flavor()
            self.result = 100
            status = testcase.TestCase.EX_OK
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception('Cannot run %s', self.case_name)
        finally:
            self.stop_time = time.time()
        return status

    def clean(self):
        try:
            assert self.orig_cloud
            assert self.cloud
            super(VmReady1, self).clean()
            self.cloud.delete_image(self.image.id)
            self.orig_cloud.delete_flavor(self.flavor.id)
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception("Cannot clean all ressources")


class VmReady2(VmReady1):
    """Deploy a single VM reachable via ssh (scenario2)

    It creates new user/project before creating and configuring all tenant
    network ressources, flavors, images, etc. required by advanced testcases.

    It ensures that all testcases inheriting from SingleVm2 could work
    without specific configurations (or at least read the same config data).
    """

    __logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        if "case_name" not in kwargs:
            kwargs["case_name"] = 'vmready2'
        super(VmReady2, self).__init__(**kwargs)
        try:
            assert self.orig_cloud
            self.project = tenantnetwork.NewProject(
                self.orig_cloud, self.case_name, self.guid)
            self.project.create()
            self.cloud = self.project.cloud
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception("Cannot create user or project")
            self.cloud = None
            self.project = None

    def clean(self):
        try:
            super(VmReady2, self).clean()
            assert self.project
            self.project.clean()
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception("Cannot clean all ressources")


class SingleVm1(VmReady1):
    """Deploy a single VM reachable via ssh (scenario1)

    It inherits from TenantNetwork1 which creates all network resources and
    completes it by booting a VM attached to that network.

    It ensures that all testcases inheriting from SingleVm1 could work
    without specific configurations (or at least read the same config data).
    """
    # pylint: disable=too-many-instance-attributes

    __logger = logging.getLogger(__name__)
    username = 'cirros'
    ssh_connect_timeout = 60

    def __init__(self, **kwargs):
        if "case_name" not in kwargs:
            kwargs["case_name"] = 'singlevm1'
        super(SingleVm1, self).__init__(**kwargs)
        self.sshvm = None
        self.sec = None
        self.fip = None
        self.keypair = None
        self.ssh = None
        (_, self.key_filename) = tempfile.mkstemp()

    def prepare(self):
        """Create the security group and the keypair

        It can be overriden to set other rules according to the services
        running in the VM

        Raises: Exception on error
        """
        assert self.cloud
        self.keypair = self.cloud.create_keypair(
            '{}-kp_{}'.format(self.case_name, self.guid))
        self.__logger.debug("keypair: %s", self.keypair)
        self.__logger.debug("private_key: %s", self.keypair.private_key)
        with open(self.key_filename, 'w') as private_key_file:
            private_key_file.write(self.keypair.private_key)
        self.sec = self.cloud.create_security_group(
            '{}-sg_{}'.format(self.case_name, self.guid),
            'created by OPNFV Functest ({})'.format(self.case_name))
        self.cloud.create_security_group_rule(
            self.sec.id, port_range_min='22', port_range_max='22',
            protocol='tcp', direction='ingress')
        self.cloud.create_security_group_rule(
            self.sec.id, protocol='icmp', direction='ingress')

    def connect(self, vm1):
        """Connect to a virtual machine via ssh

        It first adds a floating ip to the virtual machine and then establishes
        the ssh connection.

        Returns:
        - (fip, ssh)
        - None on error
        """
        assert vm1
        fip = self.cloud.create_floating_ip(
            network=self.ext_net.id, server=vm1)
        self.__logger.debug("floating_ip: %s", fip)
        p_console = self.cloud.get_server_console(vm1)
        self.__logger.debug("vm console: \n%s", p_console)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        for loop in range(6):
            try:
                ssh.connect(
                    fip.floating_ip_address,
                    username=getattr(
                        config.CONF,
                        '{}_image_user'.format(self.case_name), self.username),
                    key_filename=self.key_filename,
                    timeout=getattr(
                        config.CONF,
                        '{}_vm_ssh_connect_timeout'.format(self.case_name),
                        self.ssh_connect_timeout))
                break
            except Exception:  # pylint: disable=broad-except
                self.__logger.debug(
                    "try %s: cannot connect to %s", loop + 1,
                    fip.floating_ip_address)
                time.sleep(10)
        else:
            self.__logger.error(
                "cannot connect to %s", fip.floating_ip_address)
            return None
        return (fip, ssh)

    def execute(self):
        """Say hello world via ssh

        It can be overriden to execute any command.

        Returns: echo exit codes
        """
        (_, stdout, _) = self.ssh.exec_command('echo Hello World')
        self.__logger.debug("output:\n%s", stdout.read())
        return stdout.channel.recv_exit_status()

    def run(self, **kwargs):
        """Boot the new VM

        Here are the main actions:
        - add a new ssh key
        - boot the VM
        - create the security group
        - execute the right command over ssh

        Returns:
        - TestCase.EX_OK
        - TestCase.EX_RUN_ERROR on error
        """
        status = testcase.TestCase.EX_RUN_ERROR
        try:
            assert self.cloud
            super(SingleVm1, self).run(**kwargs)
            self.result = 0
            self.prepare()
            self.sshvm = self.boot_vm(
                key_name=self.keypair.id, security_groups=[self.sec.id])
            (self.fip, self.ssh) = self.connect(self.sshvm)
            if not self.execute():
                self.result = 100
                status = testcase.TestCase.EX_OK
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception('Cannot run %s', self.case_name)
        finally:
            self.stop_time = time.time()
        return status

    def clean(self):
        try:
            assert self.orig_cloud
            assert self.cloud
            self.cloud.delete_floating_ip(self.fip.id)
            self.cloud.delete_server(self.sshvm, wait=True)
            self.cloud.delete_security_group(self.sec.id)
            self.cloud.delete_keypair(self.keypair.id)
            super(SingleVm1, self).clean()
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception("Cannot clean all ressources")


class SingleVm2(SingleVm1):
    """Deploy a single VM reachable via ssh (scenario2)

    It creates new user/project before creating and configuring all tenant
    network ressources and vms required by advanced testcases.

    It ensures that all testcases inheriting from SingleVm2 could work
    without specific configurations (or at least read the same config data).
    """

    __logger = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        if "case_name" not in kwargs:
            kwargs["case_name"] = 'singlevm2'
        super(SingleVm2, self).__init__(**kwargs)
        try:
            assert self.orig_cloud
            self.project = tenantnetwork.NewProject(
                self.orig_cloud, self.case_name, self.guid)
            self.project.create()
            self.cloud = self.project.cloud
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception("Cannot create user or project")
            self.cloud = None
            self.project = None

    def clean(self):
        try:
            super(SingleVm2, self).clean()
            assert self.project
            self.project.clean()
        except Exception:  # pylint: disable=broad-except
            self.__logger.exception("Cannot clean all ressources")