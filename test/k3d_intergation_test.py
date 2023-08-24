'''
' Integration test cases for script run on whole k3d cluster.
'
' @file: k3d_intergation_test.py
' @author: Abdullah Alotaibi
' @date: 06/04/2023
'
'''
import pytest
import subprocess
import time
import yaml
from kubernetes import client, config

class AutomatedIntegration:

  # defines pytest setup fixture to create a testing k3d cluster ..
  @pytest.fixture(scope='session')
  def k3d_cluster(self):
      _cluster_config = {
        "apiVersion": "k3d.io/v1alpha2",
        "kind": "Cluster",
        "metadata": { "name": "integration-test-cluster" },
        "servers": 1,
        "agents": 2
      }
      # create the k3d cluster.
      config.load_kube_config()
      kubectl_cmd = "kubectl apply -f -"
      cluster_yaml = yaml.dump(_cluster_config)
      subprocess.check_call(f"echo '{cluster_yaml}' | {kubectl_cmd}", shell=True)

      wait_for_cluster()
      yield

      # delete the k3d cluster after all tests are run.
      subprocess.check_call(
        f"echo '{cluster_yaml}' | {kubectl_cmd} --force --grace-period=0", shell=True
      )

  def test_delete_deployment(self, k3d_cluster):
    # delete the Kubernetes deployment object
    client.AppsV1Api().delete_namespaced_deployment(
        name="test-deployment",
        namespace="default",
        body=client.V1DeleteOptions(
            propagation_policy='Foreground',
            grace_period_seconds=5
        )
    )
    # assert that the deployment was deleted successfully
    with pytest.raises(client.rest.ApiException) as e:
        client.AppsV1Api().read_namespaced_deployment(name="test-deployment", namespace="default")
    assert e.value.status == 404

  def wait_for_cluster(self):
    max_retries = 10
    retry_interval = 5
    kubectl_cmd = "kubectl get nodes"

    for i in range(max_retries):
      try:
        subprocess.check_output(kubectl_cmd, shell=True)
        print("K3d cluster is ready!")
        return
      except subprocess.CalledProcessError as e:
        print(f"K3d cluster is not yet ready. Retrying in {retry_interval} seconds...")
        time.sleep(retry_interval)

    raise RuntimeError("Timed out waiting for the k3d cluster to be ready")
