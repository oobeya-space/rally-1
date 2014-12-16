# Copyright 2014: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from rally.benchmark.scenarios import base
from rally.benchmark.scenarios.sahara import utils
from rally.benchmark import types
from rally.benchmark import validation
from rally import consts
from rally import log as logging

LOG = logging.getLogger(__name__)


class SaharaClusters(utils.SaharaScenario):

    @types.set(flavor=types.FlavorResourceType,
               neutron_net=types.NeutronNetworkResourceType,
               floating_ip_pool=types.NeutronNetworkResourceType)
    @validation.flavor_exists('flavor')
    @validation.required_contexts("users", "sahara_image")
    @validation.number("node_count", minval=2, integer_only=True)
    @validation.required_services(consts.Service.SAHARA)
    @validation.required_openstack(users=True)
    @base.scenario(context={"cleanup": ["sahara"]})
    def create_and_delete_cluster(self, flavor, node_count, plugin_name,
                                  hadoop_version, floating_ip_pool=None,
                                  neutron_net=None, volumes_per_node=None,
                                  volumes_size=None, auto_security_group=None,
                                  security_groups=None, node_configs=None,
                                  cluster_configs=None):
        """Test the Sahara Cluster launch and delete commands.

        This scenario launches a Hadoop cluster, waits until it becomes
        'Active' and deletes it.

        :param flavor: The Nova flavor that will be for nodes in the
        created node groups
        :param node_count: The total number of instances in a cluster (>= 2)
        :param plugin_name: The name of a provisioning plugin
        :param hadoop_version: The version of Hadoop distribution supported by
        the specified plugin.
        :param floating_ip_pool: The floating ip pool name from which Floating
        IPs will be allocated. Sahara will determine automatically how to treat
        this depending on it's own configurations. Defaults to None because in
        some cases Sahara may work w/o Floating IPs.
        :param neutron_net: The id or name of a Neutron network that
        will be used for fixed IPs. This parameter is ignored when Nova Network
        is set up.
        :param volumes_per_node: The number of Cinder volumes that will be
        attached to every cluster node
        :param volumes_size: The size of each Cinder volume in GB
        :param auto_security_group: Boolean value. If set to True Sahara will
        create a Security Group for each Node Group in the Cluster
        automatically.
        :param security_groups: The list of security groups that will be used
        while creating VMs. If auto_security_group is set to True this list
        can be left empty.
        :param node_configs: The configs dict that will be passed to each Node
        Group
        :param cluster_configs: The configs dict that will be passed to the
        Cluster
        """

        image_id = self.context["tenant"]["sahara_image"]

        LOG.debug("Using Image: %s" % image_id)

        cluster = self._launch_cluster(
            flavor_id=flavor,
            image_id=image_id,
            node_count=node_count,
            plugin_name=plugin_name,
            hadoop_version=hadoop_version,
            floating_ip_pool=floating_ip_pool,
            neutron_net_id=neutron_net,
            volumes_per_node=volumes_per_node,
            volumes_size=volumes_size,
            auto_security_group=auto_security_group,
            security_groups=security_groups,
            node_configs=node_configs,
            cluster_configs=cluster_configs)

        self._delete_cluster(cluster)

    @types.set(flavor=types.FlavorResourceType)
    @validation.flavor_exists('flavor')
    @validation.required_services(consts.Service.SAHARA)
    @validation.required_contexts("users", "sahara_image")
    @validation.number("node_count", minval=2, integer_only=True)
    @base.scenario(context={"cleanup": ["sahara"]})
    def create_scale_delete_cluster(self, flavor, node_count, plugin_name,
                                    hadoop_version, deltas,
                                    floating_ip_pool=None, neutron_net_id=None,
                                    volumes_per_node=None, volumes_size=None,
                                    auto_security_group=None,
                                    security_groups=None, node_configs=None,
                                    cluster_configs=None):
        """Test the Sahara Cluster launch, scale and delete commands.

        This scenario launches a Hadoop cluster, waits until it becomes
        'Active'. Then a series of scale operations is applied. The scaling
        happens according to numbers listed in :param deltas. Ex. if
        deltas is set to [2, -2] it means that the first scaling operation will
        add 2 worker nodes to the cluster and the second will remove two.

        :param flavor: The Nova flavor that will be for nodes in the
        created node groups
        :param node_count: The total number of instances in a cluster (>= 2)
        :param plugin_name: The name of a provisioning plugin
        :param hadoop_version: The version of Hadoop distribution supported by
        the specified plugin.
        :param deltas: The list of integers which will be used to add or
        remove worker nodes from the cluster
        :param floating_ip_pool: The floating ip pool name from which Floating
        IPs will be allocated. Sahara will determine automatically how to treat
        this depending on it's own configurations. Defaults to None because in
        some cases Sahara may work w/o Floating IPs.
        :param neutron_net_id: The id of a Neutron network that
        will be used for fixed IPs. This parameter is ignored when Nova Network
        is set up.
        :param volumes_per_node: The number of Cinder volumes that will be
        attached to every cluster node
        :param volumes_size: The size of each Cinder volume in GB
        :param auto_security_group: Boolean value. If set to True Sahara will
        create a Security Group for each Node Group in the Cluster
        automatically.
        :param security_groups: The list of security groups that will be used
        while creating VMs. If auto_security_group is set to True this list
        can be left empty.
        :param node_configs: The configs dict that will be passed to each Node
        Group
        :param cluster_configs: The configs dict that will be passed to the
        Cluster
        """

        image_id = self.context["tenant"]["sahara_image"]

        LOG.debug("Using Image: %s" % image_id)

        cluster = self._launch_cluster(
            flavor_id=flavor,
            image_id=image_id,
            node_count=node_count,
            plugin_name=plugin_name,
            hadoop_version=hadoop_version,
            floating_ip_pool=floating_ip_pool,
            neutron_net_id=neutron_net_id,
            volumes_per_node=volumes_per_node,
            volumes_size=volumes_size,
            auto_security_group=auto_security_group,
            security_groups=security_groups,
            node_configs=node_configs,
            cluster_configs=cluster_configs)

        for delta in deltas:
            # The Cluster is fetched every time so that its node groups have
            # correct 'count' values.
            cluster = self.clients("sahara").clusters.get(cluster.id)

            if delta == 0:
                # Zero scaling makes no sense.
                continue
            elif delta > 0:
                self._scale_cluster_up(cluster, delta)
            elif delta < 0:
                self._scale_cluster_down(cluster, delta)

        self._delete_cluster(cluster)
