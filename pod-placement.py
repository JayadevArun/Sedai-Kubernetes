from kubernetes import client, config  # type: ignore

try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()

v1 = client.CoreV1Api()

print(f"{'Pod Name':<70}{'Node Name':<20}{'Namespace':<20}")
print("-" * 110)

pods = v1.list_pod_for_all_namespaces(watch=False)
for pod in pods.items:
    print(f"{pod.metadata.name:<70}{pod.spec.node_name:<20}{pod.metadata.namespace:<20}")
    