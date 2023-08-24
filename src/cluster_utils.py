'''
' A utility class for implementing in-cluster rotation steps for kubernetes nodes.
'
' @file: cluster_utils.py
' @author: Abdullah Alotaibi
' @date: 18/03/2023
'
'''
import os
import time
from datetime import datetime, timezone
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from log_helper import Logger

class KubeUtils():

  def __init__(self, context="default", rotate_days=60, dry=False):
    self._set_properties(context, rotate_days, dry)
    self._load_configuration()

  def scan_nodes(self):
    try:
      self._fetch_nodes()
      self._filter_candidate_nodes()

      return self.rotatable_nodes

    except ApiException as e:
      self.logger.error(" Exception when calling CoreV1Api resources: %s\n" % e)

  def process_nodes(self):
    try:
      for rotatable in self.rotatable_nodes:
        self._cordon_node(rotatable)
        self._drain_node(rotatable)
        self._terminate_recycled_node(rotatable)
    except ApiException as e:
      self.logger.error(" Exception when calling CoreV1Api resources: %s\n" % e)

  def run(self):
    # Run both filtering nodes, actual rotation.
    # Not intended to be the main procedure, which is
    # to run them seperated and wait in between for provider to provision replacements.
    self.scan_nodes()

    if len(self.rotatable_nodes) == 0:
        return

    self.process_nodes()

  def _set_properties(self, context, rotate_days, dry):
    self.node_list = []
    self.rotatable_nodes = []
    self.target_cluster = context or ""
    self.rotate_after_days = rotate_days
    self.dry_mode = dry
    if self.dry_mode:
      self.wait_before_last_drain_seconds = 5
    else:
      self.wait_before_last_drain_seconds = 60


  def _load_configuration(self):
    config.load_kube_config()
    self.api = client.CoreV1Api()
    self.logger = Logger.instance()

  def _fetch_nodes(self):
    current_context = config.list_kube_config_contexts()[1]["name"]
    self.logger.info(" Running on context: %s.", current_context)
    self.node_list = self.api.list_node().items

  def _filter_candidate_nodes(self):
    self.rotatable_nodes = []

    for node in self.node_list:
      created_at = node.metadata.creation_timestamp
      present = datetime.now(timezone.utc)
      delta = present - created_at

      if delta.days >= self.rotate_after_days:
        node_name = node.metadata.name
        labels = node.metadata.labels
        annotations = node.metadata.annotations
        self.logger.info(" Node %s was up since %s ..", node_name, created_at.date())
        self.logger.info(" Adding node '%s' for rotatation list.", node_name)
        self.rotatable_nodes.append({
          "name": node_name, "labels": labels, "annotations": annotations, "spec": node.spec
        })
    self.logger.info(" Total of %s nodes collected for rotation.", len(self.rotatable_nodes))

  def _cordon_node(self, node):
    node_name = node['name']
    self.logger.info(f" Cordoning node {node_name} ..")

    payload = { "spec": { "unschedulable": True } }
    if not self.dry_mode:
      response = self.api.patch_node(node_name, payload)
      if not response.spec.unschedulable:
        raise ApiException(f" Cordon operation for node {node_name} failed.")

    self.logger.info(f"Node '{node_name}' was cordoned successfully.")

  def _drain_node(self, node):
    node_name = node['name']
    self.logger.info(f" Collecting pods to evict on node: {node_name} ..")
    namespaces = self.api.list_namespace()

    eviction_body = lambda pod, namespace: client.V1Eviction(
      api_version= "policy/v1beta1",
      kind="Eviction",
      metadata=client.V1ObjectMeta(name=pod, namespace=namespace),
      delete_options=client.V1DeleteOptions(api_version="meta/v1", kind="DeleteOptions", grace_period_seconds=60)
    )

    pods_to_evict = []
    for ns in namespaces.items:
      ns_name = ns.metadata.name
      node_ns_pods = self.api.list_namespaced_pod(ns_name, field_selector=f"spec.nodeName={node_name}")
      if len(node_ns_pods.items) > 0:
        pods_to_evict.append(node_ns_pods.items)

    pods_count = sum([len(l) for l in zip(*pods_to_evict)])
    self.logger.info(f"{pods_count} pods will be evicted from node {node_name}.")
    for list in pods_to_evict:
      for pod in list:
        pod_name  = pod.metadata.name
        namespace = pod.metadata.namespace
        if not self.dry_mode:
          self.api.create_namespaced_pod_eviction(pod_name, namespace, eviction_body(pod_name, namespace))

    self.logger.info(f"Waiting for {self.wait_before_last_drain_seconds} seconds ..")
    time.sleep(self.wait_before_last_drain_seconds)

    self.logger.info(f"Issuing plain 'drain' command on node {node_name} for the final restoration.")
    if not self.dry_mode:
      os.system(f"kubectl drain --force --ignore-daemonsets --delete-emptydir-data {node_name}")

  def _terminate_recycled_node(self, node):
    # Here, we don't hardly terinmate `kubectl delete node`, but only signal them to
    # the cloud provider or operator for final termination.
    pass
