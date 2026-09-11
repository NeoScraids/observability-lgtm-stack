# observability-lgtm-stack

Stack de observabilidad con Grafana, Prometheus, Mimir, Tempo, Loki y Alloy. Todo en Docker Compose, listo para levantar con un comando. Incluye manifiestos de Kubernetes para desplegar Alloy como DaemonSet en clusters OKE y un script de Python para crear dashboards automaticamente.

## Que incluye

- **Docker Compose** con 6 servicios preconfigurados y conectados entre si
- **Correlacion cruzada** ya configurada en Grafana: desde una traza en Tempo podes saltar al log en Loki y a la metrica en Mimir
- **Manifiestos de OKE** para desplegar Alloy en cada nodo del cluster y recolectar logs de pods, metricas de cAdvisor y trazas OTLP
- **Script de bootstrap** que crea dashboards via la API de Grafana

## Servicios y puertos

| Servicio | Puerto | Para que |
| :--- | :--- | :--- |
| Grafana | `3000` | Dashboards, alertas, explorador |
| Prometheus | `9090` | Scraping de metricas |
| Mimir | `9009` | Almacenamiento a largo plazo de metricas (compatible con Prometheus) |
| Loki | `3100` | Logs, consultas LogQL |
| Tempo | `3200` | Trazas distribuidas, TraceQL |
| Tempo OTLP | `4317`/`4318` | Receptor de trazas OpenTelemetry (gRPC/HTTP) |
| Alloy | `12345` | UI del agente de telemetria |

## Inicio rapido

```bash
git clone https://github.com/NeoScraids/observability-lgtm-stack.git
cd observability-lgtm-stack

# Levantar todo
docker compose up -d
docker compose ps

# Crear dashboards
python scripts/bootstrap_dashboards.py
```

Grafana queda en [http://localhost:3000](http://localhost:3000) (`admin` / `admin`). Los data sources (Mimir, Loki, Tempo, Prometheus) ya vienen configurados.

## Despliegue en OKE

Para capturar telemetria de un cluster real de Oracle Kubernetes Engine:

1. Editar los endpoints en `k8s-oke/alloy-daemonset.yaml` (apuntarlos a donde tengas el stack)
2. Aplicar los manifiestos:

```bash
kubectl apply -f k8s-oke/rbac.yaml
kubectl apply -f k8s-oke/configmap-alloy.yaml
kubectl apply -f k8s-oke/alloy-daemonset.yaml

kubectl get pods -n observability -o wide
```

## Dashboards incluidos

- **Cluster & Node Overview**: CPU, memoria, red por nodo
- **RED Metrics + Tracing**: Rate/Errors/Duration con links a trazas en Tempo y logs en vivo de Loki

## Por que

En el trabajo monte un stack similar para los clusters de OKE. Este repo es la version generica que puedo compartir sin exponer datos internos y que me sirve para probar configuraciones nuevas antes de llevarlas a produccion.

## Licencia

MIT
