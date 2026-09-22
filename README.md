# Earthquake Events Platform

Plataforma desacoplada para consumir eventos sísmicos de USGS, almacenarlos en MongoDB, actualizar métricas horarias y generar reportes con Airflow.

## Arquitectura


## Ejecución

1. Copiar `.env.example` a `.env`.
2. Ajustar `API_PUBLIC_PORT`, `AIRFLOW_PORT` o `MONGO_PUBLIC_PORT` si esos puertos ya están ocupados.
3. Ejecutar `docker compose up --build`.
4. Consultar Swagger en `http://localhost:8000/docs` o en el valor configurado en `API_PUBLIC_PORT`.
5. Consultar Airflow en `http://localhost:8080` o en el valor configurado en `AIRFLOW_PORT`, con las credenciales `AIRFLOW_ADMIN_*`.

`API_HOST` y `API_PORT` controlan la escucha de Uvicorn dentro del contenedor; `API_PUBLIC_PORT` controla el puerto de Windows. La colección de Postman usa su propia variable `base_url`, cuyo valor predeterminado es `http://localhost:8000`; actualízala si cambias `API_PUBLIC_PORT`.


## Dependencias y entorno local

El proyecto usa `pyproject.toml` como manifiesto y `uv.lock` para reproducir la resolución exacta de dependencias. `uv` como gestor

```bash
uv sync
uv run pytest
uv run python -m compileall -q src ingestion.py airflow tests
```

## Endpoints

- `GET /health`: estado de la API y MongoDB.
- `GET /live`: comprueba que el proceso de la API está activo.
- `GET /ready`: comprueba que la API puede conectarse a MongoDB.
- `GET /earthquakes`: eventos con `skip`, `limit`, `min_magnitude`, `start_date`, `end_date`, `sort_by` y `order`.
- `GET /metrics`: métricas por ventana UTC `YYYY-MM-DDTHH`.
- `GET /reports`: reportes horarios persistidos.
- `GET /prometheus`: métricas técnicas de FastAPI.

La ruta `/prometheus` se usa para evitar el conflicto entre el endpoint funcional `/metrics` exigido por la prueba y el endpoint de instrumentación de Prometheus.

## Levantar la infraestructura con Docker
   ```bash
   docker compose up --build -d
   ```
   - La API estará disponible en `http://localhost:<API_PUBLIC_PORT>/docs`.
   - Airflow estará disponible en `http://localhost:<AIRFLOW_PORT>` (credenciales admin en `.env`).
**Verificar que el DAG se haya cargado** en la UI de Airflow y que la primera ejecución (programada cada hora) se complete sin errores.
**Ejecutar la suite de pruebas contra la base de datos real (opcional)**:
   ```bash
   uv run pytest -q
   ```
**Detener la infraestructura**:
   ```bash
   docker compose down
   ```

## Diseño de datos

* `earthquakes` usa `event_id` como índice único. 
* La ingesta usa `replace_one(..., upsert=True)`, por lo que repetir una respuesta de USGS no crea duplicados. Tras insertar o actualizar un evento, se recalcula únicamente su ventana UTC mediante agregación de MongoDB.

* `metrics` tiene una fila por ventana horaria y contiene cantidad, promedio, máximo y distribución (`<3`, `3-5`, `5-7`, `>=7`). 
* `hourly_reports` tiene una fila por hora cerrada y conserva las tres ubicaciones más frecuentes, extrayendo el texto posterior a `of`.

## Validación local

La colección Postman está en `postman/earthquake-api.postman_collection.json`.
