import uuid
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware que garantiza un ID único para cada petición.

    - Si la petición incluye la cabecera ``X-Request-ID``, se usa ese valor.
    - En caso contrario se genera un UUID4.
    - El ID se almacena en ``request.state.request_id`` para uso interno.
    - El mismo ID se añade a la cabecera de respuesta para que el cliente pueda correlacionar logs.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        # NOTE: exponer el ID a los controladores evita búsquedas repetidas y mejora rendimiento.
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
