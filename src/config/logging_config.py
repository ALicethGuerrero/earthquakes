import sys
import structlog
import logging

def configure_logging() -> None:
    """Configura el registro estructurado global.

    Utiliza ``structlog`` para generar logs en formato JSON que incluyen
    una marca de tiempo, nivel, nombre del logger y el mensaje. La configuración
    se aplica una sola vez al iniciar la aplicación.
    """
    # Configuración básica del registro estándar – necesaria para que structlog delegue.
    # NOTE: importante para rendimiento porque force=True evita configuraciones previas.
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
        force=True,
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
