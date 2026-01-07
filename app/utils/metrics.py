"""Prometheus metrics for observability."""
from prometheus_client import Counter, Histogram, Gauge
from typing import Optional

# Message counters
messages_received_total = Counter(
    'messages_received_total',
    'Total number of messages received',
    ['source', 'type']
)

messages_sent_total = Counter(
    'messages_sent_total',
    'Total number of messages sent',
    ['destination', 'status']
)

messages_failed_total = Counter(
    'messages_failed_total',
    'Total number of failed messages',
    ['source', 'destination', 'error_type']
)

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# External API metrics
external_api_requests_total = Counter(
    'external_api_requests_total',
    'Total external API requests',
    ['service', 'status']
)

external_api_duration_seconds = Histogram(
    'external_api_duration_seconds',
    'External API request duration',
    ['service']
)

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['service']
)

# Active connections
active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

