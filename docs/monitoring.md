# Monitoring and Health Checks

CerCollettiva includes comprehensive monitoring and health check endpoints for production monitoring and alerting.

## Available Endpoints

### Health Check Endpoints

#### Basic Health Check
- **URL**: `/monitoring/health/`
- **Method**: GET
- **Description**: Basic application health check
- **Response**: JSON with status, timestamp, version, and uptime

```json
{
    "status": "healthy",
    "timestamp": "2025-08-30T13:00:00Z",
    "version": "1.0.0",
    "environment": "production",
    "uptime": "5 days, 2:30:15",
    "response_time_ms": 15.2
}
```

#### Database Health Check
- **URL**: `/monitoring/health/database/`
- **Method**: GET
- **Description**: Database connectivity and performance check
- **Response**: Database status with query performance metrics

```json
{
    "service": "database",
    "status": "healthy",
    "timestamp": "2025-08-30T13:00:00Z",
    "response_time_ms": 25.1,
    "query_time_ms": 12.5,
    "database": {
        "vendor": "sqlite",
        "version": "3.40.0"
    }
}
```

#### MQTT Broker Health Check
- **URL**: `/monitoring/health/mqtt/`
- **Method**: GET
- **Description**: MQTT broker connectivity status
- **Response**: MQTT broker status and configuration

```json
{
    "service": "mqtt",
    "status": "healthy",
    "timestamp": "2025-08-30T13:00:00Z",
    "response_time_ms": 18.3,
    "broker": {
        "name": "Production MQTT",
        "host": "mqtt.example.com",
        "port": 1883,
        "use_tls": true
    }
}
```

#### Cache Health Check
- **URL**: `/monitoring/health/cache/`
- **Method**: GET
- **Description**: Redis cache connectivity and performance
- **Response**: Cache operations performance

```json
{
    "service": "cache",
    "status": "healthy",
    "timestamp": "2025-08-30T13:00:00Z",
    "response_time_ms": 8.1,
    "operation_time_ms": 5.2,
    "backend": "redis"
}
```

#### System Resources Health Check
- **URL**: `/monitoring/health/system/`
- **Method**: GET
- **Description**: System resource utilization (CPU, Memory, Disk)
- **Response**: Detailed system metrics

```json
{
    "service": "system",
    "status": "healthy",
    "timestamp": "2025-08-30T13:00:00Z",
    "response_time_ms": 45.8,
    "metrics": {
        "cpu": {
            "percent": 25.5,
            "cores": 4
        },
        "memory": {
            "percent": 45.2,
            "available_gb": 2.8,
            "total_gb": 4.0
        },
        "disk": {
            "percent": 65.1,
            "free_gb": 15.2,
            "total_gb": 50.0
        }
    }
}
```

### Aggregated Status Endpoint

#### Status Overview
- **URL**: `/monitoring/status/`
- **Method**: GET
- **Description**: Aggregated status of all services
- **Query Parameters**: 
  - `detailed=true`: Include additional system information

```json
{
    "status": "healthy",
    "timestamp": "2025-08-30T13:00:00Z",
    "version": "1.0.0",
    "environment": "production",
    "services": {
        "database": {"status": "healthy"},
        "mqtt": {"status": "healthy"},
        "cache": {"status": "degraded"},
        "system": {"status": "healthy"}
    },
    "response_time_ms": 82.5
}
```

### Metrics Endpoint (Prometheus Compatible)

#### Prometheus Metrics
- **URL**: `/monitoring/metrics/`
- **Method**: GET
- **Description**: Prometheus-compatible metrics for monitoring systems
- **Content-Type**: `text/plain; version=0.0.4`

Sample metrics:
```
# HELP system_cpu_usage_percent CPU usage percentage
# TYPE system_cpu_usage_percent gauge
system_cpu_usage_percent 25.5

# HELP system_memory_usage_percent Memory usage percentage
# TYPE system_memory_usage_percent gauge
system_memory_usage_percent 45.2

# HELP app_active_plants_total Number of active plants
# TYPE app_active_plants_total gauge
app_active_plants_total 15
```

## Status Levels

The monitoring system uses three status levels:

- **`healthy`**: Service operating normally
- **`degraded`**: Service operational but with performance issues
- **`unhealthy`**: Service not operational or critical issues

## HTTP Status Codes

- **200 OK**: Service is healthy
- **207 Multi-Status**: Service is degraded but operational
- **503 Service Unavailable**: Service is unhealthy

## Integration with Monitoring Systems

### Docker Health Checks
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/monitoring/health/ || exit 1
```

### Kubernetes Liveness/Readiness Probes
```yaml
livenessProbe:
  httpGet:
    path: /monitoring/health/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /monitoring/status/
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Prometheus Configuration
```yaml
scrape_configs:
  - job_name: 'cercollettiva'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/monitoring/metrics/'
    scrape_interval: 30s
```

### Load Balancer Health Checks
Configure your load balancer to use `/monitoring/health/` as the health check endpoint.

## Performance Thresholds

The monitoring system uses the following performance thresholds:

### Database
- **Healthy**: Query time < 100ms
- **Degraded**: Query time 100-500ms
- **Unhealthy**: Query time > 500ms or connection failure

### Cache
- **Healthy**: Operation time < 50ms
- **Degraded**: Operation time 50-200ms
- **Unhealthy**: Operation time > 200ms or connection failure

### System Resources
- **CPU**:
  - Healthy: < 80%
  - Degraded: 80-95%
  - Unhealthy: > 95%

- **Memory**:
  - Healthy: < 80%
  - Degraded: 80-95%
  - Unhealthy: > 95%

- **Disk**:
  - Healthy: < 80%
  - Degraded: 80-95%
  - Unhealthy: > 95%

## Security Considerations

- Health check endpoints do not require authentication
- Detailed system information is only available via query parameters
- Sensitive configuration data is not exposed in responses
- All endpoints include cache-control headers to prevent caching