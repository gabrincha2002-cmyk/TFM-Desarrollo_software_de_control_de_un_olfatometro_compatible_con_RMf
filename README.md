# OlfaMetric

Aplicación software de control de un olfatómetro compatible con RMf para el estudio de la epilepsia.

Prototipo desarrollado como TFM del Máster de Ingeniería Biomédica en la Universidad Internacional de Valencia (VIU), en colaboración con el departamento de Neuroingeniería Biomédica (nBio) del Instituto de Bioingeniería - Universidad Miguel Hernández (IB-UMH) de Elche.

## Funcionalidades 

A partir del firmware implementado y subsistema hardware diseñado en colaboración con el departamento nBio, el software es capaz de:
- Realizar un control manual inalámbrico sobre los diferentes canales integrados en el dispositivo desarrollado. 
- Configurar y ejecutar protocolos experimentales automatizados en cada sesión.
- Caracterizar los parámetros considerados de relevancia por cada canal en tiempo real.
- Informar al usuario de los procesos y acciones realizadas por pantalla.
- Generar informes de las sesiones experimentales realizadas en diferentes formatos (`.pdf`, `.xlsx` y `.csv`). Incluyendo un informe `.tsv` compatible con el estándar BIDS.

## Requisitos

 - Python versión 3.10 o superiores (probado en la versión 3.14.4)
 - Sistema operativo: Windows 11 (probado con versión 11 Pro) y Linux (probado con versión 26.04)
 - Red Wifi local accesible por ESP32-WROOM-32U y dispositivo propio
 - Hardware: olfatómetro controlado por ESP32-WROOM-32U desarrollado en colaboración con el Instituto de Bioingeniería de la Universidad Miguel Hernández de Elche

## Instalación

1. Descarga e instalación de Python en su versión 3.14.4 de 64 bits
2. Descarga/clona el repositorio GitHub actual en tu dispositivo
3. Crea (`python -m venv .venv`) y activa (Windows: `.venv\Scripts\activate`| Linux: `source .venv/bin/activate`) el correspondiente entorno virtual (`venv`) por consola (Opcional pero recomendado para mayor fidelidad con las comprobaciones realizadas)
4. Instalación de las dependencias necesarias en el entorno virtual activo (o en la carpeta global de la versión Python instalada si no se ha creado un `venv`) por consola: `pip install -r requirements.txt`


## Ejecución

1. Abre una ventana de comandos y navega hasta la carpeta del repositorio descargado/clonado
2. Activa el correspondiente entorno virtual - `venv` (si se ha creado con antelación): Windows --> `.venv\Scripts\activate`| Linux --> `source .venv/bin/activate`
3. Lanza la aplicación software: `python main.py`

## Arquitectura del proyecto

📁 OlfaMetric_v2
├── ⚙️ .gitattributes
├── ⚙️ .gitignore
├── 📄 requirements.txt
├── 📄 dependencias_entorno.txt
├── 📝 README.md
├── 🐍 config.py
├── 🐍 discovery.py
├── 🐍 main.py
├── 🐍 reports.py
├── 🐍 widgets.py
└── 🐍 ws_client.py

> La carpeta `archivos_generados/` (logs de sesión/consola e informes de análisis) se crea automáticamente en la primera ejecución y no se incluye en el repositorio.

## Manual de Usuario

1. Esperar la conexión automática del software con ESP32-WROOM-32U (emplear el botón "Buscar dispositivos" en caso de encontrar dificultades en la conexión automática) 
2. Introducir metadatos anonimizados de la sesión experimental
3. Introducir los odorantes a sus canales asociados
4. Caracterizar los parámetros de interés de cada canal
5. Configurar y ejecutar el protocolo experimental
6. Exportar el informe de la sesión experimental realiza en el formato de interés seleccionado

## Dependencias principales

- [customtkinter](https://github.com/tomschimansky/customtkinter) - Interfaz gráfica de usuario
- [websockets](https://websockets.readthedocs.io/en/stable/) - Conexión con el ESP32-WROOM-32U
- [zeroconf](https://github.com/python-zeroconf/python-zeroconf) - Descubrimiento del dispositivo en la red local
- [matplotlib](https://matplotlib.org) - Gráficas en tiempo real
- [reportLab](https://www.reportlab.com) - Generación de informes PDF
- [openpyxl](https://openpyxl.readthedocs.io/en/stable/) - Generación de informes Excel

## Autores y contacto

Estudiante - Gabriel Collado Santamaría (gabcolsan@gmail.com)
Directora TFT - Lilibeth Zambrano Martínez
Asesor Externo - Eduardo Fernández Jover

## Licencia
Todos los derechos reservados (pendiente de tramitar con la Universidad Miguel Hernández de Elche).