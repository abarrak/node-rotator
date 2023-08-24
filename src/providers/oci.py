'''
' Oracle cloud implementation of abstract provider.
'
' @file: oci.py
' @author: Abdullah Alotaibi
' @date: 18/03/2023
'
'''
import time
import oci
import re
from oci.container_engine.models import UpdateNodePoolDetails, UpdateNodePoolNodeConfigDetails
from .abstract import AbstractProvider

class OCIProvider(AbstractProvider):

  def expand_cluster_for_rotation(self):
    # Increase the current cluster by replacement nodes before rotation :)
    node_pool = self._get_node_pool()
    current_size = node_pool.node_config_details.size
    new_size = current_size + self.scale_factor

    if new_size > current_size:
      self.logger.info(f' Scaling up the node pool to {new_size} nodes.')
      if not self.dry_mode:
        response = self.client.update_node_pool(
          node_pool_id=node_pool.id,
          update_node_pool_details=UpdateNodePoolDetails(
            node_config_details=UpdateNodePoolNodeConfigDetails(size=new_size)
          )
        )
        self._check_call_result(response)

      self.logger.info(f" Waiting {self.provision_wait} sec for provision operation to finalize..")
      time.sleep(self.provision_wait)

  def resize_cluster_after_rotation(self):
    # Get the current node pool size and node list.
    node_pool = self._get_node_pool()
    current_size = node_pool.node_config_details.size
    new_size = current_size - self.scale_factor

    # Scale down the node pool by deleting older nodes.
    while current_size > new_size and self.rotatable_nodes:
      node = self.rotatable_nodes.pop(-1)
      if not self.dry_mode:
        self.logger.info(f" Terminating node '%s' ..", node["name"])
        response = self.client.delete_node(
          node_pool_id=node_pool.id,
          node_id=node["spec"].provider_id,
          is_decrement_size=True,
          is_force_deletion_after_override_grace_duration=True
        )
        self._check_call_result(response)
        current_size -= 1

    self.logger.info(f" Waiting {self.provision_wait} sec for scale operation to finalize..")
    time.sleep(self.provision_wait)
    self.logger.info(f' Successfully scaled down the node pool to {current_size} nodes.')

  def _load_configuration(self, **kwargs):
    config = oci.config.from_file()
    self.client = oci.container_engine.ContainerEngineClient(config)
    self.node_pool_filter = "non-autoscaler"

    self.cluster_id = kwargs['oci_cluster_id']
    # assign compartment from args or infer it from node annotations.
    inferred_comp_id = self.rotatable_nodes[0]["annotations"]["oci.oraclecloud.com/compartment-id"]
    self.compartment_id = kwargs['oci_compartment_id'] or inferred_comp_id

    if not self.compartment_id:
      raise AttributeError("provider 'compartment_id' is missing.")
    if not self.cluster_id:
      raise AttributeError("provider 'cluster_id' is missing.")

    self.logger.info(f' Passed configurations: compartment: %s ', self.compartment_id)
    self.logger.info(f' Passed configurations: cluster: %s ', self.cluster_id)


  def _get_node_pool(self):
    response = self.client.list_node_pools(
      compartment_id=self.compartment_id,
      cluster_id=self.cluster_id
    )
    self._check_call_result(response)

    node_pool = [np for np in response.data if np.name.startswith(self.node_pool_filter)][0]
    name = node_pool.name
    size = node_pool.node_config_details.size
    self.logger.info(f' Processing node pool: %s which have %s nodes currently.', name, size)

    return node_pool

  def _check_call_result(self, response):
    success_code = re.compile("^20[0-9]$")
    if not success_code.match(str(response.status)):
      raise ConnectionError(response.data)
