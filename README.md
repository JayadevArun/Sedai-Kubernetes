#  Compact Feature for Resource Reshuffling in Kubernetes

A smart, automated solution to dynamically identify underutilized nodes and intelligently reshuffle workloads in Kubernetes clusters using **Prometheus**, **KMeans Clustering**, and **Kubernetes-native operations** like **drain**, **cordon**, **taints**, and **tolerations**.

---

##  Overview

In modern cloud environments, Kubernetes has become the standard for orchestrating containerized workloads. However, one persistent challenge remains: **efficient resource utilization**. Fragmented workloads and underutilized nodes lead to:

- Increased infrastructure costs 
- Wasted energy consumption 
- Degraded cluster performance 

This project introduces a **Compact Feature for Resource Reshuffling**, which enhances Kubernetes' native scheduling and resource allocation mechanisms by automatically identifying and draining underutilized nodes, redistributing workloads intelligently across the cluster.

---

##  Objectives

-  **Identify Underutilized Nodes**  
  Use KMeans clustering to analyze CPU and memory metrics from Prometheus to detect inefficient nodes.

-  **Automate Workload Redistribution**  
  Use `kubectl drain`, `cordon`, and eviction APIs to safely move workloads off underutilized nodes.

-  **Preserve Stateful Workloads**  
  Detect StatefulSets and Jobs and handle them gracefully during redistribution to maintain data integrity and continuity.

-  **Apply Taints and Tolerations**  
  Prevent rescheduling on drained nodes using Kubernetes taints until they're ready.

-  **Evaluate Performance**  
  Measure improvements in resource usage, response times, and overall efficiency pre- and post-reshuffle.

-  **Contribute to the Community**  
  Provide a replicable, scalable approach to dynamic workload management in Kubernetes.
