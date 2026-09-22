from prometheus_client import Counter, Histogram


events_processed = Counter(
	"earthquake_events_processed_total",
	"Eventos procesados por la ingesta",
	["source"],
)
event_duration = Histogram(
	"earthquake_event_processing_seconds",
	"Duración del procesamiento de eventos",
	["source"],
)


def record_event_processed(source: str) -> None:
	"""Registra un evento procesado."""
	events_processed.labels(source=source).inc()


def record_event_duration(source: str, duration: float) -> None:
	"""Registra la duración del procesamiento."""
	event_duration.labels(source=source).observe(duration)
