'''
' Base provdier class for cloud engines responsible for adding and removing nodes to cluster.
'
' @file: abstract.py
' @author: Abdullah Alotaibi
' @date: 25/03/2023
'
'''
from __future__ import annotations
from abc import ABCMeta, abstractmethod
from log_helper import Logger

class AbstractProvider():

  def __init__(self, nodes_list, provision_time=300, dry=False, **kwargs):
    self.dry_mode = dry
    self.logger = Logger.instance()

    self.scale_factor = len(nodes_list)
    self.rotatable_nodes = nodes_list
    self.provision_wait = provision_time

    self._load_configuration(**kwargs)

  @abstractmethod
  def expand_cluster_for_rotation(self):
    pass

  @abstractmethod
  def resize_cluster_after_rotation(self):
    pass

  @abstractmethod
  def _load_configuration(self):
    pass
