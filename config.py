"""
Almacena las constantes de configuración de la aplicación OlfaMetric.

Centraliza los valores de configuración en un solo lugar para facilitar su mantenimiento y modificación. 
Cambiar un valor en el presente módulo afectará al resto de la aplicación, implicando un cambio global en el comportamiento de la misma.

Secciones:
    - Comunicación: Constantes destinadas a la comunicación y el descubrimiento con el ESP32-WROOM-32U del subsistema hardware.
    - Configuración del olfatómetro: Constantes destinadas a la definición del olfatómetro y sus canales.
    - Configuración del protocolo: Constantes destinadas a limitar los valores máximos y mínimos de los parámetros configurables del protocolo de una sesión experimental.
    - Configuración de la caracterización: Constantes destinadas a definir los parámetros de la caracterización del olfatómetro.
    - Configuración hardware: Constantes que representan la configuración del hardware del olfatómetro.
    - Gráficas y buffers: Constantes destinadas a definir el tamaño de los buffers de datos y los límites de las gráficas.
    - Directorios y formatos: Constantes destinadas a definir los directorios y los formatos de tiempo empleados por la aplicación.
    - Colores de la UI: Constantes destinadas a la definición de los colores empleados por el widget de estado de conexión.

Librerias externas:
    - os: Librería estándar de Python para interactuar con el sistema operativo, utilizada para manejar rutas de archivos y directorios.
"""

import os 

#-----COMUNICACIÓN----------------------------------
# URI empleado por defecto para la conexión WebSocket con el ESP32-WROOM-32U del subsistema hardware.
URI_WEBSOCKET_DEFECTO = "ws://olfatometro.local:8765"
# Intervalo de actualización de la UI en milisegundos.
INTERVALO_DE_ACTUALIZACION_UI_MS = 100
# Intervalo de sondeo de las colas de mensajes recibidos, además de los mensajes de estado, en milisegundos.
INTERVALO_SONDEO_COLAS_RECIBIDOS_ESTADO_MS = 50
# Intervalo de sondeo de la cola de envío de mensajes al ESP32-WROOM-32U en milisegundos.
INTERVALO_SONDEO_COLA_ENVIO_S = 0.05
# Intervalo de reintento de reconexión entre software y ESP32-WROOM-32U automatica en segundos
RECONEXION_AUTOMATICA_S = 0.5
# Direccion del servicio DNS-SD a buscar en la red local para el descubrimiento del ESP32-WROOM-32U del subsistema hardware.
SERVICIO_MDNS = "_olfatometro._tcp.local."
# Tiempo máximo de espera para el cierre del hilo de búsqueda DNS-SD en segundos.
TIMEOUT_CIERRE_HILO_S = 3.0
# Tiempo máximo de espera para la búsqueda de DNS-SD en segundos.
TIMEOUT_SEGUNDOS_MDNS = 5
# Intervalo de ping al ESP32-WROOM-32U para comprobar la conectividad en segundos.
PING_INTERVAL_S = 10
# Tiempo máximo de espera para la respuesta al ping en segundos.
PING_TIMEOUT_S = 10
# Tiempo máximo de espera para la apertura (handshake) de la conexión WebSocket en segundos.
OPEN_TIMEOUT_S = 5

#-----CONFIGURACIÓN DEL OLFATÓMETRO---------------------------------------
# Número de canales del olfatómetro.
NUM_CANALES = 6
# Colores de los canales del olfatómetro.
COLORES_CANALES = ["Verde", "Negro", "Blanco", "Azul", "Amarillo", "Rojo"]
# Canal destinado a la desensibilización de estímulos olfativos.
CANAL_BLANCO = 2
# Velocidad de referencia de la fuente de aire en porcentaje.
PORCENTAJE_VELOCIDAD = 14

#-----CONFIGURACIÓN DEL PROTOCOLO-------
# Tiempo máximo para la desensibilización de un protocolo de estimulación experimental.
VALOR_MAX_TIEMPO_DESENSIBILIZACION = 120
# Tiempo mínimo para la desensibilización de un protocolo de estimulación experimental.
VALOR_MIN_TIEMPO_DESENSIBILIZACION = 10 
# Tiempo máximo para la exposición de un protocolo de estimulación experimental.
VALOR_MAX_TIEMPO_EXPOSICION = 30
# Tiempo mínimo para la exposición de un protocolo de estimulación experimental.
VALOR_MIN_TIEMPO_EXPOSICION = 3
# Número máximo de ciclos de un protocolo de estimulación experimental.
VALOR_MAX_CICLOS = 10
# Número mínimo de ciclos de un protocolo de estimulación experimental.
VALOR_MIN_CICLOS = 1
# Intervalo de tiempo máximo entre ciclos de un mismo protocolo de estimulación experimental.
VALOR_MAX_INTERVALO_CICLOS = 120
# Intervalo de tiempo mínimo entre ciclos de un mismo protocolo de estimulación experimental.
VALOR_MIN_INTERVALO_CICLOS = 10

#-----CONFIGURACIÓN DE LA CARACTERIZACIÓN-------------------------
# Parámetros de interés a caracterizar. 
PARAMETROS_CARACTERIZACION = [
    ("flujo", "Flujo (ml/min)"),
    ("concentracion", "Concentración (µg/m³)"),
    ("velocidad", "Velocidad (rpm)"),
    ("latencia", "Latencia (ms)")
]
# Tiempo máximo de caracterización del olfatómetro en segundos.
VALOR_MAXIMO_TIEMPO_CARACTERIZACION = 300
# Registro de muestras por segundo de los parámetros de interés durante la caracterización del olfatómetro.
MUESTRAS_POR_SEGUNDO_CARACTERIZACION = 10
# Frecuencia de caracterización del los parámetros de interés del olfatómetro.
MUESTREO_CARACTERIZACION= 1 / MUESTRAS_POR_SEGUNDO_CARACTERIZACION

#-----CONFIGURACIÓN HARDWARE-----------------------------------------------------------
# Posiciones lógicas asociadas a los canales del olfatómetro. 
# Aquellas posiciones lógicas negativas corresponden a posiciones físicas que no están asociadas a ningún canal del olfatómetro.
POSICIONES_CANALES = {2: 0, 0: 200, 1: 400, 3: 600, 4: 800, 5: 1000, -1: 1200, -2: 1400}
# Número de pasos entre posiciones lógicas consecutivas de los canales del olfatómetro.
# PASOS_POR_CANAL = 200

#-----GRÁFICAS Y BUFFERS------------
# Tamaño del buffer de las gráficas de caracterización del software.
TAMANO_BUFFER_GRAFICAS = 61
# Tiempo de las gráficas de caracterización del software en segundos.
TIEMPO_GRAFICAS = 61
# Límites de los valores de los parámetros de interés durante la caracterización del olfatómetro.
LIMITESY = {"velocidad": [0,10000],
            "flujo": [0,500],
            "concentracion": [0,500],
            "latencia": [0,1000]
            }

#-----DIRECTORIOS Y FORMATOS----------------------------------------------------------------
# Directorio del donde se ubica la aplicación software.
DIRECTORIO_DEL_PROYECTO = os.path.dirname(os.path.abspath(__file__))
# Directorio destinado al alamcenamiento de los archivos generados por la aplicación software.
DIRECTORIO_ARCHIVOS_TEMPORALES = os.path.join(DIRECTORIO_DEL_PROYECTO, "archivos_generados")
# Formato de loa hora empleado por el software.
FORMATO_HORA = "%H:%M:%S"
# Formato de la fecha y hora empleado por el softeware.
FORMATO_TIMESTAMP = "%d-%m-%Y %H:%M:%S"

#-----COLORES DE LA UI------------------
# Color empleado por el widget de estado de conexión para indicar la correcta conexión entre ESP32-WROOM-32U y el software.
COLOR_ESTADO_OK = "#7deb7d"
# Color empleado por el widget de estado de conexión para indicar el intento de conexión entre ESP32-WROOM-32U y el software.
COLOR_ESTADO_CONECTANDO = "#f0c060"
# Color empleado por el widget de estado de conexión para indicar la inexistente conexión entre ESP32-WROOM-32U y el software.
COLOR_ESTADO_DESCONECTADO = "#fa8989"



