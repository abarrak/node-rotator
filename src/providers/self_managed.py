'''
' On perimese kubernetes implementation of abstract provider.
'
' @file: oci.py
' @author: Abdullah Alotaibi
' @date: 18/03/2023
'
'''
import time
import oci
from .abstract import AbstractProvider

'''
' This provider is used when the cluster is managed manually in terms of nodes,
' Such as on-prem servers pool, virtualization, etc.
'''
class SelfManaged(AbstractProvider):
  def expand_cluster_for_rotation(self):
    self.logger.info(f'Need to increase the cluster size by {self.scale_factor} nodes more ..')
    self.logger.info(f'Do nothing, leave it for operator of the cluster beforehand.')
    pass

  def resize_cluster_after_rotation(self):
    self.logger.info(f'Now need to remove the older {self.scale_factor} nodes.')
    self.logger.info(f'Do nothing, For the operator of the cluster afterward.')
    pass

  def _load_configuration(self, **kwargs):
    ...