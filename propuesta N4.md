## Arquitectura de Datos para Analítica Avanzada y Machine Learning (Azure Native)

## 1. Pincipio general
Para no saturar la base de datos operativa (**MongoDB**), separaremos completamente la capa **transaccional (OLTP)** de la **analítica (OLAP)**. 

Mientras FastAPI y MongoDB se encargan de la ingesta en tiempo real y de responder a las peticiones inmediatas de la app, los eventos se enviarán de forma paralela hacia un **Lakehouse en Azure** (basado en arquitectura Medallion: *Bronze, Silver y Gold*). De esta forma garantizamos consultas analíticas ultrarrápidas sobre millones de registros históricos, procesamiento de archivos Parquet y generación de datasets listos para Machine Learning.

---

## 2. Componentes de la Solución en Azure

| Capa / Necesidad | Servicio Azure | ¿Por qué lo elegimos? |
| :--- | :--- | :--- |
| **Ingesta Streaming** | **Azure Event Hubs** | Recibe el flujo continuo de eventos sísmicos desde el servicio de ingesta con latencia mínima. Es compatible con la API de Kafka. |
| **Persistencia Operativa** | **MongoDB** | Maneja la capa transaccional rápida (escrituras y lecturas inmediatas de la API). |
| **Procesamiento Streaming → Parquet** | **Event Hubs Capture** | Escribe automáticamente los eventos crudos a archivos **Parquet** en el Data Lake sin necesidad de mantener un proceso complejo consumiendo memoria. |
| **Almacenamiento del Lakehouse** | **ADLS Gen2 + Delta Lake** | Almacena los archivos Parquet organizados en capas. Delta Lake nos da transacciones ACID, versionado de datos (*time travel*) y rendimiento optimizado. |
| **Procesamiento Analítico** | **Azure Databricks** *(o Synapse Spark)* | Procesa los archivos Parquet/Delta en near real-time, calcula agregados complejos y genera los datasets analíticos. |
| **Data Warehouse / Consultas SQL** | **Azure Synapse SQL Serverless** | Permite tirar consultas SQL directo sobre los archivos Parquet/Delta en el Lake sin necesidad de mover los datos. |
| **ML & Feature Store** | **Azure Machine Learning + MLflow** | Guarda las características (*features*) derivadas de los sismos, gestiona los experimentos y registra los modelos entrenados. |
| **Dashboards Históricos** | **Power BI** | Se conecta a Synapse / Delta Lake para analizar tendencias, patrones geográficos y volumen histórico. |
| **Dashboards en Tiempo Real** | **Azure Managed Grafana + WebSockets** | Visualiza el flujo de sismos en tiempo real a medida que ingresan, junto con las métricas de salud del sistema. |
| **Orquestación Batch** | **Apache Airflow** | Ejecuta las tareas programadas: re-cálculo diario de métricas, limpieza de datos y reentrenamiento periódico de modelos. |

---

## 3. Flujo de Datos

```
[USGS API] -> [Servicio Ingesta] ---> [MongoDB (Operativo / OLTP)]
                    |
                    +------------> [Azure Event Hubs]
                                         |
                                         v (Event Hubs Capture)
                              [ADLS Gen2 - Zona Bronze (Parquet Raw)]
                                         |
                            [Azure Databricks / Spark]
                                         |
                                         v
                              [ADLS Gen2 - Zona Silver (Delta Lake)]
                                         |
                            [Azure Databricks / Spark]
                                         |
                                         v
                              [ADLS Gen2 - Zona Gold (Delta / Features)]
                                         |
             +---------------------------+---------------------------+
             |                                                       |
             v                                                       v
   [Power BI / Synapse SQL]                                  [Azure ML / MLflow]
(Dashboards Analíticos Históricos)                      (Entrenamiento de Modelos ML)
```

---

## 4. Respuesta a los Requerimientos del Reto

### A. Separación entre capas transaccionales y analíticas
* **Capa Transaccional (OLTP):** MongoDB almacena los eventos crudos y las métricas inmediatas para que FastAPI responda en milisegundos.
* **Capa Analítica (OLAP):** Los datos se replican hacia **Azure Data Lake Storage Gen2 (ADLS Gen2)** en formato columnar (**Parquet / Delta Lake**). Las consultas pesadas de analítica e historia corren aquí sin impactar a la base de datos operativa.

### B. Procesamiento de archivos Parquet en near real-time
* **Event Hubs Capture** guarda automáticamente los eventos entrantes en formato **Parquet** dentro de la zona *Bronze* del Data Lake.
* Un *job* de **Spark Structured Streaming** en Azure Databricks lee estos Parquet a medida que van llegando, limpia las coordenadas/magnitudes y actualiza la zona *Silver* en formato **Delta Lake**.

### C. Generación de datasets analíticos para Machine Learning
* En la zona *Gold* construimos el dataset final. Calculamos variables derivadas (distancia entre sismos, aceleración de eventos en una misma falla, promedios móviles de profundidad, etc.).
* Estas variables se registran en el **Feature Store de Azure Machine Learning**, permitiendo entrenar modelos (por ejemplo, para predecir réplicas o clasificar zonas de alto riesgo) usando datos versionados con **MLflow**.

### D. Dashboards históricos vs. Tiempo real
* **Histórico (Tendencias):** **Power BI** se conecta mediante Synapse SQL a las tablas Gold en Delta Lake para mostrar tendencias mensuales, mapas de calor por país y distribuciones acumuladas.
* **Tiempo Real:** **FastAPI** expone un canal **WebSocket** que empuja los nuevos sismos a **Azure Managed Grafana** (o Grafana Live), mostrando alertas y mapas activos al instante.

### E. Estrategia de almacenamiento para gran volumen histórico
Aplicamos una estrategia de **almacenamiento por capas (Tiering) en ADLS Gen2**:
1. **Bronze (Raw):** Parquet sin modificar. Se almacena en *Cool Tier* con retención de 30 días.
2. **Silver (Enriched):** Datos limpios y estructurados en Delta Lake. Se conserva en *Hot Tier* para procesamiento frecuente.
3. **Gold (Curated):** Agregados históricos e indicadores. Los datos de más de 1 año se mueven automáticamente a *Archive Tier* (almacenamiento más economico), manteniendo disponible la capacidad de consultarlos si es necesario.

## 5. MLOps y Data Ops en Azure  
### MLOps
- **Azure Machine Learning + MLflow**: registro de experimentos, versionado de modelos y despliegues automáticos.  
- **Feature Store** de Azure ML: gestión de características derivadas del Lakehouse (capa Gold).  
- **Airflow → Azure Databricks**: transforma datos *Silver* → *Gold* y entrena modelos, guardando artefactos en MLflow.  
### Data Ops
- **Event Hubs Capture** → **Parquet** en ADLS Gen2 (capa Bronze).  
- **Delta Lake** (capa Silver) con validación de calidad y *time‑travel*.  
- **Azure Data Factory / Synapse Pipelines**: orquesta ETL/ELT, carga incremental y movimientos entre capas (Bronze → Silver → Gold).  
- **Política de retención y tiering** en ADLS Gen2: *Cool* (30 días), *Hot* (1‑2 años) y *Archive* (> 1 año).  
> **Resultado:** datos limpios y versionados llegan a los pipelines de entrenamiento en tiempo real, mientras que la transformación y carga se gestionan de forma automática y reproducible.