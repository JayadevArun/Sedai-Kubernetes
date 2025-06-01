from kubernetes import client, config
import time
import numpy as np
from sklearn.cluster import KMeans
import requests

config.load_kube_config()
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
batch_v1 = client.BatchV1Api()

PROMETHEUS_URL = "http://localhost:9090"

def query_prometheus(promql):
    response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": promql})
    result = response.json()["data"]["result"]
    return result

def get_node_utilization():
    nodes = v1.list_node().items
    usage_data = []

    cpu_query = '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
    mem_query = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'

    cpu_usage_map = {entry['metric']['instance'].split(":")[0]: float(entry['value'][1]) for entry in query_prometheus(cpu_query)}
    mem_usage_map = {entry['metric']['instance'].split(":")[0]: float(entry['value'][1]) for entry in query_prometheus(mem_query)}

    for node in nodes:
        name = node.metadata.name
        ip = node.status.addresses[0].address

        cpu_usage = cpu_usage_map.get(ip, 50.0)
        mem_usage = mem_usage_map.get(ip, 50.0)

        usage_data.append([cpu_usage, mem_usage, name])

    return np.array(usage_data)

def identify_underutilized_nodes():
    data = get_node_utilization()
    kmeans = KMeans(n_clusters=2, random_state=42).fit(data[:, :2])
    low_cluster = np.argmin(kmeans.cluster_centers_[:, 0] + kmeans.cluster_centers_[:, 1])
    return [data[i, 2] for i in range(len(data)) if kmeans.labels_[i] == low_cluster]

def is_system_pod(pod):
    if pod.metadata.namespace in ["kube-system", "kube-public", "kube-node-lease"]:
        return True
    if not pod.metadata.owner_references:
        return True
    for owner in pod.metadata.owner_references:
        if owner.kind == "DaemonSet":
            return True
    return False

def drain_node(node_name):
    print(f"Draining node {node_name}...")
    v1.patch_node(node_name, {"spec": {"unschedulable": True}})

    pods = v1.list_pod_for_all_namespaces(field_selector=f"spec.nodeName={node_name}").items
    for pod in pods:
        if is_system_pod(pod):
            print(f"Skipping system pod: {pod.metadata.name}")
            continue
        if "controller-revision-hash" in pod.metadata.labels:
            drain_statefulset_pod(pod)
        elif "job-name" in pod.metadata.labels:
            drain_job_pod(pod)
        else:
            print(f"Evicting pod {pod.metadata.name}")
            v1.delete_namespaced_pod(pod.metadata.name, pod.metadata.namespace)

def drain_statefulset_pod(pod):
    namespace = pod.metadata.namespace
    labels = pod.metadata.labels
    if "app" not in labels:
        print(f"Skipping StatefulSet pod {pod.metadata.name}, missing 'app' label.")
        return

    app_label = labels["app"]
    print(f"Evicting StatefulSet pod {pod.metadata.name}...")
    v1.delete_namespaced_pod(pod.metadata.name, namespace)

    while True:
        new_pods = v1.list_namespaced_pod(namespace, label_selector=f"app={app_label}").items
        if any(p.status.phase == "Running" for p in new_pods):
            break
        time.sleep(5)

def drain_job_pod(pod):
    namespace = pod.metadata.namespace
    job_name = pod.metadata.labels["job-name"]
    job = batch_v1.read_namespaced_job(job_name, namespace)

    if job.status.succeeded:
        print(f"Job {job_name} completed. Cleaning up.")
        batch_v1.delete_namespaced_job(job_name, namespace, propagation_policy="Foreground")
    else:
        print(f"Job {job_name} still running. Skipping.")

def apply_taint(node_name):
    taint = client.V1Taint(effect="NoSchedule", key="reshuffle", value="true")
    node = v1.read_node(node_name)
    if node.spec.taints is None:
        node.spec.taints = []
    node.spec.taints.append(taint)
    v1.patch_node(node_name, {"spec": {"taints": node.spec.taints}})
    print(f"Taint applied to {node_name}")

def reshuffle_workloads():
    underutilized_nodes = identify_underutilized_nodes()
    print(f"Underutilized nodes identified: {underutilized_nodes}")
    
    for node in underutilized_nodes:
        drain_node(node)
        apply_taint(node)

    print("AI-Based reshuffling complete!")

if __name__ == "__main__":
    reshuffle_workloads()
