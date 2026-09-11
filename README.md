<div align="center">

  <h1>observability-lgtm-stack</h1>
  <p><strong>Enterprise LGTM Observability Stack (Grafana, Mimir, Tempo, Loki, Prometheus, Alloy) & OKE Telemetry</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Visualization-Grafana_10-F46800?style=flat-square&logo=grafana&logoColor=white" alt="Grafana" />
    <img src="https://img.shields.io/badge/Metrics-Mimir_%2B_Prometheus-E6522C?style=flat-square&logo=prometheus&logoColor=white" alt="Metrics" />
    <img src="https://img.shields.io/badge/Logs-Grafana_Loki_3-FF7800?style=flat-square&logo=grafana&logoColor=white" alt="Loki" />
    <img src="https://img.shields.io/badge/Tracing-Grafana_Tempo_2-326CE5?style=flat-square&logo=opentelemetry&logoColor=white" alt="Tempo" />
    <img src="https://img.shields.io/badge/Agent-Grafana_Alloy-00557F?style=flat-square&logo=grafana&logoColor=white" alt="Alloy" />
    <img src="https://img.shields.io/badge/Orchestration-Oracle_OKE-F80000?style=flat-square&logo=oracle&logoColor=white" alt="OKE" />
    <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License" />
  </p>

</div>

---

### Overview

`observability-lgtm-stack` provides an end-to-end, enterprise-grade telemetry platform unifying **Logs, Metrics, and Distributed Traces** (the three pillars of observability).

Designed to bridge local control-plane inspection with cloud-native Kubernetes workloads on **Oracle Container Engine for Kubernetes (OKE)**, this repository delivers:
1. **Unified Docker Compose Control Plane:** Pre-wired instances of Grafana, Prometheus, Mimir, Loki, Tempo, and Grafana Alloy.
2. **Native Cross-Correlation (The Holy Grail of SRE):**
   - **Trace-to-Logs:** Inspect a span in Tempo and jump directly to the exact application logs in Loki matching the `trace_id`.
   - **Trace-to-Metrics:** Jump from high-latency traces directly into RED service graphs in Mimir/Prometheus.
3. **OKE DaemonSet Telemetry:** Production Kubernetes manifests deploying **Grafana Alloy** as a DaemonSet across OKE worker nodes to collect container logs from `/var/log/pods`, cAdvisor node metrics, and OTLP traces.
4. **Automated Dashboard Bootstrapping:** Python automation script utilizing Grafana's REST API to immediately provision production dashboards upon startup.

---

### End-to-End Telemetry Architecture

```mermaid
graph TD
    subgraph OKECluster ["Oracle Cloud Infrastructure (OCI) // OKE Cluster"]
        Apps[Fintech Microservices / Workloads] -->|OTLP Traces :4317| AlloyNode[Grafana Alloy DaemonSet]
        NodePods["/var/log/pods/*/*.log"] -->|Pod Logs File Match| AlloyNode
        Kubelet["cAdvisor / Kubelet Metrics :10250"] -->|Node Metrics Scrape| AlloyNode
    end

    subgraph ObservabilityHost ["LGTM Stack Engine (Docker Compose)"]
        AlloyNode -->|Remote Push OTLP Traces| Tempo[Grafana Tempo :3200]
        AlloyNode -->|Remote Push Structured Logs| Loki[Grafana Loki :3100]
        AlloyNode -->|Remote Write TSDB Metrics| Mimir[Grafana Mimir :9009]
        Prometheus[Prometheus Server :9090] -->|Remote Write| Mimir

        Mimir -->|Metrics Source| Grafana[Grafana Portal :3000]
        Loki -->|Log Streams Source| Grafana
        Tempo -->|Trace Queries Source| Grafana
    end

    Grafana -.->|Trace-to-Logs Correlation| Loki
    Grafana -.->|Trace-to-Metrics Correlation| Mimir
```

---

### Service Matrix & Port Allocations

| Service | Container Name | Host Port | Protocol / Purpose |
| :--- | :--- | :--- | :--- |
| **Grafana** | `lgtm-grafana` | `3000` | Web UI & Visualization Dashboard |
| **Prometheus** | `lgtm-prometheus` | `9090` | Real-time metric scraping & remote_write |
| **Mimir** | `lgtm-mimir` | `9009` | High-scale long-term Prometheus storage |
| **Loki** | `lgtm-loki` | `3100` | Microsecond LogQL log aggregation |
| **Tempo** | `lgtm-tempo` | `3200` | TraceQL query interface |
| **Tempo OTLP (gRPC)** | `lgtm-tempo` | `4317` | OpenTelemetry gRPC trace receiver |
| **Tempo OTLP (HTTP)** | `lgtm-tempo` | `4318` | OpenTelemetry HTTP trace receiver |
| **Grafana Alloy** | `lgtm-alloy` | `12345` | Alloy Agent pipeline health & UI |

---

### Quickstart: Local Control-Plane (Docker)

#### 1. Launch the LGTM Stack

```bash
# Clone the repository
git clone https://github.com/NeoScraids/observability-lgtm-stack.git
cd observability-lgtm-stack

# Launch all unified containers
docker compose up -d
```

Verify that all services are healthy:

```bash
docker compose ps
```

#### 2. Bootstrap Production Dashboards

Execute the included Python automation script to verify Grafana readiness and import pre-configured dashboards:

```bash
python scripts/bootstrap_dashboards.py
```

#### 3. Access Grafana

Navigate to [http://localhost:3000](http://localhost:3000) in your web browser:
- **Default Username:** `admin`
- **Default Password:** `admin`
- **Pre-configured Data Sources:** `Mimir` (Default), `Loki`, `Tempo`, `Prometheus`.

---

### Deploying Telemetry Agent to Oracle Kubernetes Engine (OKE)

To extract live node logs, container traces, and cluster metrics from an active OKE cluster into this observability stack:

#### 1. Configure Target Endpoints
Edit `k8s-oke/alloy-daemonset.yaml` with your accessible host endpoints:

```yaml
env:
  - name: TEMPO_ENDPOINT
    value: "tempo.your-observability-domain.com:4317"
  - name: LOKI_ENDPOINT
    value: "http://loki.your-observability-domain.com:3100/loki/api/v1/push"
  - name: MIMIR_ENDPOINT
    value: "http://mimir.your-observability-domain.com:9009/api/v1/push"
```

#### 2. Apply Manifests with `kubectl`

```bash
# Create dedicated namespace and RBAC permissions
kubectl apply -f k8s-oke/rbac.yaml

# Deploy the Alloy Agent ConfigMap (River configuration)
kubectl apply -f k8s-oke/configmap-alloy.yaml

# Deploy Alloy DaemonSet across all worker nodes
kubectl apply -f k8s-oke/alloy-daemonset.yaml
```

Verify agent rollout across all cluster nodes:

```bash
kubectl get pods -n observability -o wide
```

---

### Dashboards Included

1. **`Cluster & Node Infrastructure Overview` (`cluster-overview`):**
   - Live CPU Utilization (%) per node instance
   - RAM memory saturation and available memory tracking
   - Network I/O throughput (Rx/Tx) grouped by Kubernetes Namespace
2. **`RED Metrics & Distributed Tracing Correlator` (`red-metrics-traces`):**
   - Rate (Requests per second) calculated from span metrics
   - Errors (% Failure rate over total invocations)
   - Duration (p95 latency histograms)
   - Embedded Loki log streams with click-to-trace deep linking

---

### License

Distributed under the MIT License. Developed and maintained by [Brandon Mendieta](https://github.com/NeoScraids).
