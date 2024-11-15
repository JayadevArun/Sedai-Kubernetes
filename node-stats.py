from kubernetes import client, config  # type: ignore
import numpy as np # type: ignore

try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()

v1 = client.CustomObjectsApi()

node_metrics = v1.list_cluster_custom_object(
    group="metrics.k8s.io", version="v1beta1", plural="nodes"
)

def calculate_stats(data):
    avg = np.mean(data)
    max_val = np.max(data)
    p99 = np.percentile(data, 99)
    return avg, max_val, p99

c_usages = []
m_usages = []

print("Node-wise CPU and Memory Usage Stats:\n")

for node in node_metrics['items']:
    c_usage = int(node['usage']['cpu'].rstrip('n')) / 1e6  # Convert to millicores
    m_usage = int(node['usage']['memory'].rstrip('Ki')) / 1024  # Convert to MiB

    c_usages.append(c_usage)
    m_usages.append(m_usage)

    print(f"Node: {node['metadata']['name']}")
    print(f"  CPU Usage: {c_usage:.2f}m")
    print(f"  Memory Usage: {m_usage:.2f} MiB\n")

cpu_avg, cpu_max, cpu_p99 = calculate_stats(c_usages)
memory_avg, memory_max, memory_p99 = calculate_stats(m_usages)

print("Overall Cluster CPU and Memory Usage Stats:")
print(f"  CPU Usage (millicores): Avg: {cpu_avg:.2f}m, Max: {cpu_max:.2f}m, P99: {cpu_p99:.2f}m")
print(f"  Memory Usage (MiB): Avg: {memory_avg:.2f} MiB, Max: {memory_max:.2f} MiB, P99: {memory_p99:.2f} MiB")
