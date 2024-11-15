from kubernetes import client, config  # type: ignore
import numpy as np # type: ignore

try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()

v1 = client.CustomObjectsApi()

pod_metrics = v1.list_namespaced_custom_object(
    group="metrics.k8s.io", version="v1beta1", namespace="default", plural="pods"
)

def calculate_stats(data):
    avg = np.mean(data)
    max_val = np.max(data)
    p99 = np.percentile(data, 99)
    return avg, max_val, p99

c_usages = []
m_usages = []

print("Pod-wise CPU and Memory Usage Stats:\n")

for pod in pod_metrics['items']:
    pod_name = pod['metadata']['name']
    pod_namespace = pod['metadata']['namespace']
    pod_cpu_usages = []
    pod_memory_usages = []

    for container in pod['containers']:
        c_usage = int(container['usage']['cpu'].rstrip('n')) / 1e6
        m_usage = int(container['usage']['memory'].rstrip('Ki')) / 1024

        pod_cpu_usages.append(c_usage)
        pod_memory_usages.append(m_usage)

    c_usages.extend(pod_cpu_usages)
    m_usages.extend(pod_memory_usages)

    print(f"Pod: {pod_name}, Namespace: {pod_namespace}")
    print(f"  CPU Usage: {np.mean(pod_cpu_usages):.2f}m (Avg), {np.max(pod_cpu_usages):.2f}m (Max)")
    print(f"  Memory Usage: {np.mean(pod_memory_usages):.2f} MiB (Avg), {np.max(pod_memory_usages):.2f} MiB (Max)\n")

cpu_avg, cpu_max, cpu_p99 = calculate_stats(c_usages)
memory_avg, memory_max, memory_p99 = calculate_stats(m_usages)

print("Overall Cluster CPU and Memory Usage Stats:")
print(f"  CPU Usage : Avg: {cpu_avg:.2f}m, Max: {cpu_max:.2f}m, P99: {cpu_p99:.2f}m")
print(f"  Memory Usage : Avg: {memory_avg:.2f} MiB, Max: {memory_max:.2f} MiB, P99: {memory_p99:.2f} MiB")
