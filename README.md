# alerta_monitoring

# Uptime Monitoring System

Este proyecto implementa un sistema de monitorización automática de disponibilidad (Uptime) para páginas web.

El objetivo es detectar caídas, errores HTTP o lentitud en servicios web de forma automática, registrar el histórico y facilitar una respuesta rápida del equipo técnico.

## Funcionalidades

- Comprobación periódica de URLs
- Detección de errores HTTP (404, 500, 503, etc.)
- Medición de tiempos de respuesta
- Registro histórico en base de datos
- Generación de informe diario
- Preparado para alertas automáticas

## Tecnologías utilizadas

- Python
- GitHub Actions
- SQLite
- Requests

## URLs de prueba

- https://www.google.com
- https://www.wikipedia.org
- https://httpstat.us/404
- https://httpstat.us/500
- https://httpstat.us/503

## Ejecución local

```bash
pip install -r requirements.txt
python monitor.py
