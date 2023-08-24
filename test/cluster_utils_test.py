'''
' Unit tests of cluster_utils functionality.
'
' @file: cluster_utils_test.py
' @author: Abdullah Alotaibi
' @date: 18/03/2023
'
'''
import pytest
from pytest_mock import mocker
from kubernetes import client, config
from src.cluster_utils import KubeUtils

class TestKubeUtils:

  def test_set_properties_have_default_values(self, mocker):
    mocker.patch.object(config, 'load_kube_config', return_value=None)
    mocker.patch('kubernetes.client.CoreV1Api', return_value=None)

    kube_utils = KubeUtils()
    assert kube_utils.target_cluster == "default"
    assert kube_utils.rotate_after_days > 0
    assert kube_utils.rotate_after_days == 60
    assert not kube_utils.dry_mode
    assert kube_utils.wait_before_last_drain_seconds > 0

  def test_set_properties_assigns_given_settings(self, mocker):
    mocker.patch.object(config, 'load_kube_config', return_value=None)
    mocker.patch('kubernetes.client.CoreV1Api', return_value=None)

    kube_utils = KubeUtils(context="my-k8s-cluster", rotate_days=25, dry=True)
    assert kube_utils.target_cluster == "my-k8s-cluster"
    assert kube_utils.dry_mode
    assert kube_utils.rotate_after_days == 25
