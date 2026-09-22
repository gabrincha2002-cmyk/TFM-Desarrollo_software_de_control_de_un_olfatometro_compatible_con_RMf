"""
Main.py es el módulo principal del software desarrollado, coordina el resto de módulos propios elaborados para:
    - Generar la interfaz gráfica de la aplicación.
    - Coordina la conexión WebSocket y el descubrimiento mediante mDNS con el ESP32-WROOM-32U.
    - Coordinar la lógica del protocolo experimental.
    - Coordinar la lógica, registrar y graficar los datos obtenidos de la caracterización.
    - Registrar el historial completo de la sesión experimental.
    - Completa la generación de informes.

Librerías externas:
    - json: Librería nativa de Python que permite codificar y decodificar datos en formato JSON.
    - CTkToolTip: Librería externa de Python empleada para generar ventanas emergente de ayuda.
    - customtkinter: Librería gráfica actualizada basada en la librería estándar de Python tkinter.
    - tkinter: LIbrería gráfica nativa de Python empleada para crear interfaces de usuario.
    - time: Librería estándar de Python para trabajar con el tiempo y las fechas, utilizada para medir intervalos de tiempo y establecer tiempos de espera.
    - os: Librería estándar de Python para interactuar con el sistema operativo, utilizada para manejar rutas de archivos y directorios.
    - datetime: Módulo nativo de Python empleado en la manipulación y operación de fechas y horas.
    - matplotlib: Librería nativa de Python que permite la creación de gráficos 2D y 3D.
    - collections: Librería nativa de Python que posibilita el manejo de estructuras de datos más optimizas respecto a las tradicionalmente usadas en Python.
    - numpy: Librería externa de Python destinada al cálculo numérico y computación científica.
    - queue: Librería nativa de Python para manejar colas de forma segura trabajando en programas multihilos.
    - threading: Librería nativa de Python que permite trabajar de forma concurrente mediante el uso de hilos.
    - random: Librería nativa de Python que posibilita la generación de valores numéricos y selecciones de forma aleatoria.
    - ws_client: Módulo propio del proyecto encargado de establecer la conexión WebSocket con el ESP32-WROOM-32U.
    - widgets: Módulo propio del proyecto que centraliza las clases de widgets reutilizables en la lógica y GUI.
    - config: Módulo propio del proyecto que centraliza la totalidad de las constantes destinadas a la configuración de la aplicación.
    - reports: Módulo propio del proyecto encargado de la configuración y generación de informes de sesión en diferentes formatos de interés.
    - discovery: Módulo propio del proyecto responsable del descubrimiento del ESP32-WROOM-32U en la red local mediante mDNS.

"""

import json
from CTkToolTip import CTkToolTip
import customtkinter as ctk
from tkinter import messagebox
import time
import datetime
import os
import matplotlib as mpl 
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import collections
import numpy as np
import queue
import threading
import random
from ws_client import WSClient
from widgets import Canal, SpinboxCTk, Consola
import reports
import discovery
import config


# Establecimiento de modo y color de la GUI.
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")  

class App(ctk.CTk):
    """
    Es la clase principal de la aplicación que define la GUI y gestiona la totalidad del software.

    Es la encargada de definir y configurar la totalidad de la interfaz gráfica de usuario del software de control desarrollado. Por otro lado, coordina la 
    conexión realizada del módulo ws_client.py, mediante el procesamiento de los datos recibidos y enviados al mismo módulo. Adicionalmente permite la 
    posibilidad de recurrir al descubrimiento local mediante mDNS a través del módulo discovery.py en caso de tener dificultades en realizar la conexión 
    con el ESP32-WROOM-32U. La gestión de la lógica de protocolos  experimentales y caracterización de parámetros también son responsabilidades de la clase App; 
    a través del control de tiempos, banderas y comandos respecto el ESP32-WROOM-32U. Por último, almacena el conjunto de datos registrado durante la sesión 
    experimental, generando a partir de los métodos definidos en el módulo reports.py el formato de interés correspondiente.


    Atributos (de instancia):
        - colores_canales: Colores asociados a los canales del olfatómetro.
        - posicion_valvula: Posición actual de la válvula selectora de canales.
        - fase_actual: Fase actual de la sesión experimental.
        - posiciones_canales: Posiciones asociadas a cada uno de los canales del olfatómetro.
        - tiempo_grafica_flujo: Buffer temporal de la gráfica de caracterización de flujo en tiempo real.
        - tiempo_grafica_concentracion: Buffer temporal de la gráfica de caracterización de concentración en tiempo real.
        - tiempo_grafica_latencia: Buffer temporal de la gráfica de caracterización de latencia en tiempo real.
        - tiempo_grafica_velocidad: Buffer temporal de la gráfica de caracterización de velocidad en tiempo real.
        - buffer_grafica_flujo: Buffer con los registro de caracterización de flujo a representar en tiempo real.
        - buffer_grafica_concentracion: Buffer con los registro de caracterización de concentración a representar en tiempo real.
        - buffer_grafica_latencia: Buffer con los registro de caracterización de latencia a representar en tiempo real.
        - buffer_grafica_velocidad: Buffer con los registro de caracterización de velocidad a representar en tiempo real.
        - historial_sesion: Historial completo con todos los datos obtenidos durante la realización de la sesión.
        - ultimos_datos_telemetria: Último dato obtenido por la telemetría al detener un canal.
        - historial_caracterizacion: Conjunto de valores caracterizados de cada parámetro por canal en una sesión experimental.
        - segundos_restantes_protocolo: Tiempo restante para la finalización de la fase actual del protocolo.
        - segundos_restantes_velocidad: Tiempo restante para la finalización de la caracterización de la velocidad.
        - segundos_restantes_flujo: Tiempo restante para la finalización de la caracterización del flujo.
        - segundos_restantes_concentracion: Tiempo restante para la finalización de la caracterización de la concentración.
        - segundos_restantes_latencia: Tiempo restante para la finalización de la caracterización de la latencia.
        - tiempo_guardado: Tiempo activo transcurrido hasta la pausa de un canal.
        - canales_protocolo: Canales participantes en el protocolo.
        - after_activo: Identificador de la función pendiente de ejecución.
        - canal_activo: Canal actualmente activo.
        - canal_anterior: Canal anteriormente activado.
        - canal_siguiente: Canal siguiente a activar.
        - sv_canal_activo: StringVar correspondiente al canal actual activo.
        - sv_canal_anterior: StringVar correspondiente al canal anteriormente activado.
        - sv_canal_siguiente: StringVar correspondiente al siguiente canal a activar.
        - protocolo_activo: Bandera de estado de protocolo activo.
        - protocolo_pausado: Bandera de estado del protocolo pausado.
        - orden_protocolo: Listado de canales con el orden del protocolo establecido.
        - callbacks_pendientes_posicion_valvula: Listado de funciones pendientes de ejecutar tras alcanzar la posición de válcula correspondiente.
        - canal_esperando_posicion: Canal con la posición a alcanzar por la rotación de la válvula.
        - canal_caracterizacion: Canal seleccionado para caracterizar.
        - caracterizacion_flujo_parado: Bandera de estado de la pausa de la caracterización de flujo.
        - caracterizacion_concentracion_parado: Bandera de estado de la pausa de la caracterización de concentración.
        - caracterizacion_latencia_parado: Bandera de estado de la pausa de la caracterización de latencia.
        - caracterizacion_velocidad_parado: Bandera de estado de la pausa de la caracterización de velocidad.
        - caracterizando_flujo: Bandera de estado del transcurso de la caracterización de flujo.
        - caracterizando_concentracion: Bandera de estado del transcurso de la caracterización de concentración.
        - caracterizando_latencia: Bandera de estado del transcurso de la caracterización de latencia.
        - caracterizando_velocidad: Bandera de estado del transcurso de la caracterización de velocidad.
        - buffer_caracterizacion_flujo: Buffer reutilizable con el conjunto de valores de flujo caracterizados de un canal.
        - buffer_caracterizacion_concentracion: Buffer reutilizable con el conjunto de valores de concentración caracterizados de un canal.
        - buffer_caracterizacion_latencia: Buffer reutilizable con el conjunto de valores de latencia caracterizados de un canal.
        - buffer_caracterizacion_velocidad: Buffer reutilizable con el conjunto de valores de velocidad caracterizados de un canal.
        - contador_flujo: Indexador del buffer temporal de flujo.
        - contador_concentracion: Indexador del buffer temporal de concentracion.
        - contador_latencia: Indexador del buffer temporal de latencia.
        - contador_velocidad: Indexador del buffer temporal de velocidad.
        - after_caracterizacion_flujo: Identificador de la función pendiente para el temporizador de caracterización del flujo.
        - after_caracterizacion_concentracion: Identificador de la función pendiente para el temporizador de caracterización de la concentración.
        - after_caracterizacion_latencia: Identificador de la función pendiente para el temporizador de caracterización de la latencia.
        - after_caracterizacion_velocidad: Identificador de la función pendiente para el temporizador de caracterización de la velocidad.
        - ruta_archivo_temporal: Ruta del directorio de archivos temporales.
        - _cola_estado: Cola segura entre hilos para la actualización del widget de estado de conexión.
        - ws_client: Cliente de la conexión WebSocket.

    """


    def __init__(self):
        """
        Método constructor encargado de definir e inicializar todo objeto App.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        super().__init__()
        """
        Constructor heredado de la clase correspondiente a la ventana principal de CustomTkinter, para la generación de la ventana donde se implementará la GUI
        de la aplicación de control software.

        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        # Configuración básica de la ventana de la aplicación software.
        self.title("OlfaMetric")
        self.geometry("1920x1080")
        self.protocol("WM_DELETE_WINDOW", self._cerrar_aplicacion)

        # Atributos de instancia.
        self.colores_canales = config.COLORES_CANALES
        self.posicion_valvula = 0
        self.fase_actual = None
        self.posiciones_canales = config.POSICIONES_CANALES
        self.tiempo_grafica_flujo = list(range(config.TIEMPO_GRAFICAS))
        self.tiempo_grafica_concentracion = list(range(config.TIEMPO_GRAFICAS))
        self.tiempo_grafica_latencia = list(range(config.TIEMPO_GRAFICAS))
        self.tiempo_grafica_velocidad = list(range(config.TIEMPO_GRAFICAS))
        self.olores = []
        self.historial_sesion= []
        self.ultimos_datos_telemetria = {}
        self.historial_caracterizacion = {}
        self._cola_estado= queue.Queue()
        self.buffer_grafica_flujo = collections.deque([np.nan]*config.TAMANO_BUFFER_GRAFICAS, maxlen=config.TAMANO_BUFFER_GRAFICAS)
        self.buffer_grafica_concentracion = collections.deque([np.nan]*config.TAMANO_BUFFER_GRAFICAS,maxlen=config.TAMANO_BUFFER_GRAFICAS)
        self.buffer_grafica_latencia = collections.deque([np.nan]*config.TAMANO_BUFFER_GRAFICAS,maxlen=config.TAMANO_BUFFER_GRAFICAS)
        self.buffer_grafica_velocidad = collections.deque([np.nan]*config.TAMANO_BUFFER_GRAFICAS,maxlen=config.TAMANO_BUFFER_GRAFICAS)

        # Creación del directorio de archivos temporales en la ruta predefina en config.py (si procede).
        os.makedirs(config.DIRECTORIO_ARCHIVOS_TEMPORALES, exist_ok=True)
        self.ruta_archivo_temporal = os.path.join(config.DIRECTORIO_ARCHIVOS_TEMPORALES, "historial_sesion.jsonl")

        # Apertura para la escritura posterior de documentos temporales. 
        with open(self.ruta_archivo_temporal, "w", encoding = "utf-8"):
            pass

        self.segundos_restantes_protocolo = 0
        self.segundos_restantes_velocidad = 0
        self.segundos_restantes_flujo = 0
        self.segundos_restantes_concentracion = 0
        self.segundos_restantes_latencia = 0
        self.tiempo_guardado = None
        self.canales_protocolo = []
        self.after_activo = None
        self.canal_activo= None
        self.canal_anterior= None
        self.canal_siguiente= None
        self.sv_canal_activo = ctk.StringVar(value="Ninguno")
        self.sv_canal_anterior = ctk.StringVar(value="Ninguno")
        self.sv_canal_siguiente = ctk.StringVar(value="Ninguno")
        self.protocolo_activo = False
        self.protocolo_pausado = False
        self.orden_protocolo = None
        self.callbacks_pendientes_posicion_valvula = []
        self.canal_esperando_posicion = None
        self.canal_caracterizacion = None
        self.caracterizacion_velocidad_parado = False
        self.caracterizacion_flujo_parado = False
        self.caracterizacion_concentracion_parado = False
        self.caracterizacion_latencia_parado = False
        self.caracterizando_velocidad        = False
        self.caracterizando_flujo            = False
        self.caracterizando_concentracion    = False
        self.caracterizando_latencia         = False
        self.buffer_caracterizacion_velocidad = []
        self.buffer_caracterizacion_flujo = []
        self.buffer_caracterizacion_concentracion = []
        self.buffer_caracterizacion_latencia = []
        self.contador_velocidad = 0
        self.contador_flujo = 0
        self.contador_concentracion = 0
        self.contador_latencia = 0
        self.after_caracterizacion_velocidad = None
        self.after_caracterizacion_flujo = None
        self.after_caracterizacion_concentracion = None
        self.after_caracterizacion_latencia = None
        self.after__actualizar_graficas = None

        #Evaluación temporal de actualización de widgets de la UI (con time.perf_counter()) 
        #self.tiempos_actualizacion = {"iniciar_protocolo": [], "parar_canal": [], "generacion_informe": [], "_reiniciar_protocolo": [], "_reiniciar_caracterizacion_general": [], "buscar_dispositivos_mdns": []}
        #self.t0_actualizacion_iniciar_protocolo = 0
        #self.t0_actualizacion_parar_canal = 0
        #self.t0_actualizacion_generacion_informe = 0
        #self.t0_actualizacion__reiniciar_protocolo = 0
        #self.t0_actualizacion__reiniciar_caracterizacion_general = 0
        #self.t0_actualizacion_buscar_dispositivos_mdns = 0

        # Cliente WebSocket para establecer conexión con el controlador ESP32-WROOM-32U.
        self.ws_client = WSClient(
        uri        = config.URI_WEBSOCKET_DEFECTO, 
        on_estado  = self._on_estado_ws,
        )

        # Definición de numero de filas y columnas, además de las correspondientes dimensiones que conforman la GUI.
        self.grid_rowconfigure(0, weight=0) # Fila Cabecera
        self.grid_rowconfigure(1, weight=1) # Fila 1: Canales, Cacarterización, Protocolo y Estado
        self.grid_rowconfigure(2, weight=1) # Fila 2: Canales, Cacarterización, Protocolo y Estado
        self.grid_rowconfigure(3, weight=0) # Fila Consola y Fila 3: Protocolo y Estado

        self.grid_columnconfigure(0, weight=2)  # Columna de Canales y Cabecera (2/3)
        self.grid_columnconfigure(1, weight=1)  # Columnas de Protocolo y Estado (1/3)

        # Inicio de conexión con ESP32-WROOM-32U.
        self.ws_client.iniciar()

        self._procesar_cola_ws()

        self._crear_ui()

        self._procesar_estado_ws()

        self._tiempo_sesion()



    def _cerrar_aplicacion(self):
        """
        Cierra la aplicación de control software de forma segura.

        Presenta un mensaje en una ventana flotante para confirmar el cierre de la aplicación. Tras su confirmación, se procede a la detención de todos los canales
        (como medida de seguridad), la vuelta de la válvula a la posicio´n de reposo y la detención de la conexión WebSocket con el ESP32-WROOM-32U.

        Atributos (de instancia):
            - l_color_canal (CTkLabel): Etiqueta con el color del canal correspondiente.
            - e_color_canal (CTkEntry): Bloque de texto para la introducción del nombre del odorante presente en el canal (si procede).
            - sv_tiempo_activo (CTkStringVar): String variable encargado de representar el tiempo activo del canal.
            - l_tiempo_act_canal (CTkLabel): Etiqueta del tiempo activo del canal.
            - b_activar_canal (CTkButton): Botón correspondiente a la activación del canal.
            - b_parar_canal (CTkButton): Botón correspondiente al detenimiento del canal.
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """
        
        if messagebox.askokcancel("Cerrar OlfaMetric", "¿Está seguro de que desea salir de la aplicación?"):
            self.ws_client.enviar({"cmd": "parar_todos"})
            self.ws_client.enviar({"cmd": "rotar", "canal": config.CANAL_BLANCO, "pasos": -self.posicion_valvula})
            self.ws_client.detener()
            self.destroy()


    def _asignar_tooltip_spinbox(self, spinbox: SpinboxCTk, mensaje_entry: str, mensaje_incrementar: str = "Incrementar valor", mensaje_decrementar: str = "Decrementar valor"):
        """
        Asigna un mensaje flotante a un objeto SpinBoxCTk.

        Asigna mensajes flotantes a cada elementos del SpinBoxCTk para facilitar el uso del software al usuario.

        Args: 
            - spinbox (SpinboxCTk): Objeto spinbox seleccionado para la asignación de mensajes flotantes.
            - mensaje_entry (str): Mensaje flotante correspondiente al objeto CTkEntry del SpinBoxCTk pasado.
            - mensaje_incrementar (str): Mensaje flotante correspondiente al objeto CTkButton asociado al incremento del SpinBoxCTk pasado.
            - mensaje_decrementar (str): Mensaje flotante correspondiente al objeto CTkButton asociado al decremento del SpinBoxCTk pasado.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """
        
        spinbox._tooltip =[
        CTkToolTip(spinbox.e_spinbox, message=mensaje_entry, delay=0.5, font=ctk.CTkFont(size=12)),
        CTkToolTip(spinbox.b_decrementar, message=mensaje_decrementar, delay=0.5, font=ctk.CTkFont(size=12)),
        CTkToolTip(spinbox.b_incrementar, message=mensaje_incrementar, delay=0.5, font=ctk.CTkFont(size=12)),
        ]


    def _procesar_cola_ws(self):
        """
        Procesa la cola de mensajes recibidos por el Client WebSocket.

        Mientras la cola de mensajes recibidos no se encuentre vacía, trata de clasificar cada uno de los contenidos y procesarlos con su 
        correspondiente función. Si durante el el procesamiento o clasificación de los mesajes tiene lugar algún error o situación 
        desconocida muestra un mensaje de aviso por consola. Por último vuelve a reagendarse tras config.INTERVALO_SONDEO_COLAS_RECIBIDOS_ESTADO_MS
        milisegundos para gestionar el resto de mensajes recibidos.

        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            excepcion: Salta en cualquier caso de error producido durante el procesamiento y clasificación de mensajes (claves inesperadas, valor numérico 
            fuera de rango, inexistecia de widgets, etc.).

        """
        
        try:

            while not self.ws_client._cola_recibidos.empty():
                datos = self.ws_client._cola_recibidos.get_nowait()

                if "ack" in datos or datos.get("tipo") == "config":
                    self._datos_ack(datos)
    
                elif "log" in datos:
                    self._datos_log(datos)

                elif "canal" in datos and "estado" in datos:
                    self._datos_telemetria(datos)
                
                else:
                    self.consola.registro(f"[Ws_client] Mensaje recibido desconocido: {datos}")

        except Exception as excepcion:
            self.consola.registro(f"Error procesando cola en el protocolo WebSocket: {excepcion}", nivel="ERROR")

        finally:
            self.after(config.INTERVALO_SONDEO_COLAS_RECIBIDOS_ESTADO_MS, self._procesar_cola_ws) 

    
    def _crear_ui(self):
        """
        Genera la interfaz gráfica de usuario de la aplicación de control software desarrollada.

        Integra los widgets propios e incluidos en la librería de CustomTkinter destinados a la creación de la GUI propia del sofware. Se divide 
        en las secciones de: Cabecera, Consola, Canales, Caracterización, Protocolo y Estado.

        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        # Cabecera
        self.f_cabecera = ctk.CTkFrame(self,fg_color="#1e1e1e",border_color="#4a4c4e", border_width=1, corner_radius=10)  
        self.f_cabecera.grid(row=0,column=0,sticky="nsew",columnspan=2) 
        self.f_cabecera.grid_columnconfigure((0,1), weight=1) 
        self.f_cabecera.grid_rowconfigure(0, weight=1)

        self.l_titulo = ctk.CTkLabel(self.f_cabecera,text="OlfaMetric",corner_radius=10,
                                  text_color="#0f7780", font=ctk.CTkFont(size=60, overstrike=False, weight="bold"))
        self.l_titulo.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        self.l_estado_conexion = ctk.CTkLabel(self.f_cabecera,text="○ Desconectado",fg_color="#1e1e1e",text_color="#fa8989",
                                     font=ctk.CTkFont(size=18,weight="bold"))
        self.l_estado_conexion.grid(row=0, column=1,padx=30, pady=10, sticky="en") 
        
        self.b_buscar_dispositivos = ctk.CTkButton(self.f_cabecera, text="Buscar dispositivos", fg_color="#1e1e1e",
                                                 text_color="#828282",corner_radius=10,border_width=1,
                                                  command=self.iniciar_busqueda_mdns,font=ctk.CTkFont(size=14, weight="bold"))
        self.b_buscar_dispositivos.grid(row=0, column=1, padx=10, pady=(0,5), sticky="es")
        CTkToolTip(self.b_buscar_dispositivos, message="Haz clic para buscar dispositivos compatibles en la red local.", delay=0.5, justify="left", wraplength=300)


        # Consola
        self.f_consola = ctk.CTkFrame(self, fg_color="#1e1e1e",border_color="#4a4c4e", border_width=1, corner_radius=10, height=100)
        self.f_consola.grid(row=3,column=0,columnspan=1,padx=5,pady=(5,10),sticky="ew")
        self.consola= Consola(self.f_consola)
        self.consola.grid(row=0,column=0,padx=10,pady=(10,5),sticky="ew")


        # Tabview Canales-Caracterización
        self.tv_canales_caracterizacion = ctk.CTkTabview(master=self, fg_color="transparent",border_color="#4a4c4e", border_width=1, corner_radius=10, width=450)
        self.tv_canales_caracterizacion.grid(row=1,column=0,padx=5,pady=10,sticky="nsew", rowspan=2)
        self.tv_canales_caracterizacion.add("Canales")
        self.tv_canales_caracterizacion.add("Caracterización")
        self.tv_canales_caracterizacion._segmented_button.configure(text_color="#ffffff", border_width=1, corner_radius=10, width = 200,height =30, font=ctk.CTkFont(size=20, weight="bold"))
        self.tv_canales_caracterizacion.tab("Canales").grid_columnconfigure(0, weight=1)
        self.tv_canales_caracterizacion.tab("Caracterización").grid_columnconfigure(0, weight=1)

        self.tv_canales_caracterizacion.set("Canales")


        # Canales
        self.f_canales = ctk.CTkScrollableFrame(self.tv_canales_caracterizacion.tab("Canales"),fg_color="transparent") 
        self.f_canales.grid(row=0,column=0,padx=5,pady=10,sticky="nsew",rowspan=2)
        self.tv_canales_caracterizacion.tab("Canales").grid_rowconfigure(0, weight=1)
        self.tv_canales_caracterizacion.tab("Canales").grid_columnconfigure(0, weight=1)
        self.f_canales.grid_columnconfigure(0, weight=1)
        self.f_canales.grid_columnconfigure(1, weight=1)

        self.cuadros_canales = []
        for i in range(0,6):
            columna = i//3
            fila = i%3
            cuadro_canal= Canal(self.f_canales,color_canal=self.colores_canales[i],num_canal=i,registro=self.consola.registro, actualizar_canal=self.actualizar_canales)
            cuadro_canal.grid(row=fila+1, column=columna, padx=10, pady=10, sticky="nsew")
            # Actualiza el CTkComboBox presente en la sección Caracterización tras escribir.
            cuadro_canal.e_olor_canal.bind("<FocusOut>", lambda e: self.actualizar_comb_canales_caracterizacion())
            self.cuadros_canales.append(cuadro_canal)
        # La entrada de texto del canal destinado a la desensibilización, ya que no puede tener odorante.
        self.cuadros_canales[self.colores_canales.index("Blanco")].e_olor_canal.destroy()  


        # Caracterización.
        self.f_caracterizacion_scroll = ctk.CTkScrollableFrame(self.tv_canales_caracterizacion.tab("Caracterización"), fg_color="transparent")
        self.f_caracterizacion_scroll.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        self.tv_canales_caracterizacion.tab("Caracterización").grid_rowconfigure(0, weight=1)
        self.tv_canales_caracterizacion.tab("Caracterización").grid_columnconfigure(0, weight=1)
        self.f_caracterizacion_scroll.grid_columnconfigure(0, weight=1)
        self.f_caracterizacion_scroll.grid_columnconfigure(1, weight=1)  

        self.f_caracterizacion_canales_tiempo = ctk.CTkFrame(self.f_caracterizacion_scroll, fg_color="transparent", width=30, height=15, corner_radius=10 ,border_width=0)
        self.f_caracterizacion_canales_tiempo.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        sv_canales_caracterizacion = ctk.StringVar(value="Canal a caracterizar")

        self.comb_canales_caracterizacion = ctk.CTkComboBox(self.f_caracterizacion_canales_tiempo, values=[],
                                             width=180, height=36, text_color="#ffffff",command=self.seleccionar_caracterizacion,dropdown_fg_color="#0a5f70", variable=sv_canales_caracterizacion)
        self.comb_canales_caracterizacion.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        CTkToolTip(self.comb_canales_caracterizacion, message="Seleccione una canal con olor predefinido para caracterizar", delay=0.5, font=ctk.CTkFont(size=12))

        self.l_tiempo_caracterizacion = ctk.CTkLabel(self.f_caracterizacion_canales_tiempo, text="Tiempo:", text_color="#458B8D", font=ctk.CTkFont(size=14, weight="bold"))
        self.l_tiempo_caracterizacion.grid(row=0, column=1, padx=0, pady=5, sticky="e")

        self.e_tiempo_caracterizacion = SpinboxCTk(self.f_caracterizacion_canales_tiempo, valor=30, valor_min=1, valor_max=config.VALOR_MAXIMO_TIEMPO_CARACTERIZACION, escalon=1, width=60, height=15)
        self.e_tiempo_caracterizacion.grid(row=0, column=2, padx=0, pady=5, sticky="w")
        self._asignar_tooltip_spinbox(self.e_tiempo_caracterizacion, mensaje_entry="Introduzca el tiempo de la duración (en segundos) de la fase de Caracterización (tanto induvidual como general)")

        self.f_botones_caracterizacion_general = ctk.CTkFrame(self.f_caracterizacion_scroll, fg_color="transparent", width=30, height=15, corner_radius=10 ,border_width=0)
        self.f_botones_caracterizacion_general.grid(row=0, column=1, padx=15, pady=5, sticky="e")

        # Iniciar caracterización.
        self.b_iniciar_caracterizacion_general = ctk.CTkButton(self.f_botones_caracterizacion_general, text="Inicio General", text_color="#ffffff", fg_color= "#85ad75", width= 10, height=15,
                                                   hover_color="#488f51", border_color="#006400", border_width=1, corner_radius=10,command=self.iniciar_caracterizacion_general,font=ctk.CTkFont(size=18, weight="bold"))
        self.b_iniciar_caracterizacion_general.grid(row=0, column=0, ipadx=0, padx=5, pady=5, sticky="wsne")
        CTkToolTip(self.b_iniciar_caracterizacion_general, message="Haz clic para iniciar la caracterización de los cuatro parámetros a la vez.", delay=0.5, justify="left", wraplength=300)

        # Reiniciar caracterización.
        self.b__reiniciar_caracterizacion_general = ctk.CTkButton(self.f_botones_caracterizacion_general, text="Reinicio General", text_color="#ffffff", fg_color= "#C7BE19" , width=10, height=15,
                                                   hover_color="#9da31e", border_color="#F6F04F", border_width= 1, corner_radius=10,command=self._consultar__reiniciar_caracterizacion_general,font=ctk.CTkFont(size=18, weight="bold"))
        self.b__reiniciar_caracterizacion_general.grid(row=0, column=1, ipadx=0, padx=5, pady=5, sticky="wsne")
        CTkToolTip(self.b__reiniciar_caracterizacion_general, message="Haz clic para reiniciar la caracterización de los cuatro parámetros a la vez.", delay=0.5, justify="left", wraplength=300)

        # Parar caracterización.
        self.b__parar_caracterizacion_general = ctk.CTkButton(self.f_botones_caracterizacion_general, text="Parada General", text_color="#ffffff", fg_color= "#f56a6a", width=10, height=15,
                                                   hover_color="#ee4242", border_color="#ff0000", border_width= 1, corner_radius=10,command=self._consultar__parar_caracterizacion_general,font=ctk.CTkFont(size=18, weight="bold"))
        self.b__parar_caracterizacion_general.grid(row=0, column=2, ipadx=0 ,padx=5, pady=5, sticky="wsne")
        CTkToolTip(self.b__parar_caracterizacion_general, message="Haz clic para detener la caracterización de los cuatro parámetros a la vez.", delay=0.5, justify="left", wraplength=300)

        # Caracaterización velocidad.
        self.l_caracterizacion_velocidad = ctk.CTkLabel(self.f_caracterizacion_scroll, text="Velocidad", text_color="#458B8D", font=ctk.CTkFont(size=20, weight="bold"))
        self.l_caracterizacion_velocidad.grid(row=1, column=0, padx=60, pady=0, sticky="ws")

        # Gráfica en tiempo real - velocidad.
        mpl.rcParams["axes.labelsize"] = 16
        fig_velocidad = Figure(figsize=(10,5),dpi=60)
        self.ax_velocidad = fig_velocidad.add_subplot(111)
        self.ax_velocidad.set_xlim(0,int(self.e_tiempo_caracterizacion.get()))
        self.ax_velocidad.set_ylim(config.LIMITESY["velocidad"][0],config.LIMITESY["velocidad"][1]) 
        self.ax_velocidad.set_xlabel("Tiempo (s)")
        self.ax_velocidad.set_ylabel("Velocidad (m/s)")
        self.ax_velocidad.plot(self.tiempo_grafica_velocidad,list(self.buffer_grafica_velocidad)[::-1])
        fig_velocidad.set_facecolor("#242424")  
        self.ax_velocidad.set_facecolor("#242424")
        self.ax_velocidad.tick_params(colors = "#ffffff") 
        self.ax_velocidad.xaxis.label.set_color("#ffffff")  
        self.ax_velocidad.yaxis.label.set_color("#ffffff")  
        self.ax_velocidad.spines['bottom'].set_color('#ffffff')  
        self.ax_velocidad.spines['left'].set_color('#ffffff')  
        self.ax_velocidad.spines['top'].set_color('#ffffff')  
        self.ax_velocidad.spines['right'].set_color('#ffffff') 
        fig_velocidad.tight_layout()
        self.canvas_velocidad = FigureCanvasTkAgg(fig_velocidad, master=self.f_caracterizacion_scroll)
        self.canvas_velocidad.get_tk_widget().grid(row=2, column=0, padx=10, pady=0, sticky="nesw")
        self.canvas_velocidad.draw()

        self.f_botones_caracterizacion_velocidad = ctk.CTkFrame(self.f_caracterizacion_scroll, fg_color="transparent", width=75, height=15, corner_radius=10,border_width=1)
        self.f_botones_caracterizacion_velocidad.grid(row=1, column=0, padx=10, pady=0, sticky="se")
        self.f_botones_caracterizacion_velocidad.grid_columnconfigure(0, weight=1)
        self.f_botones_caracterizacion_velocidad.grid_columnconfigure(1, weight=1)
        self.f_botones_caracterizacion_velocidad.grid_columnconfigure(2, weight=1)

        # Iniciar caracterización velocidad.
        self.b_iniciar_caracterizacion_velocidad = ctk.CTkButton(self.f_botones_caracterizacion_velocidad, text="▶", text_color = "#ffffff", fg_color="#85ad75", width=25, height=15, 
        hover_color="#488f51", border_color="#006400", border_width=1, corner_radius=5,command=self.iniciar_caracterizacion_velocidad,font=ctk.CTkFont(size=24, weight="bold"))
        self.b_iniciar_caracterizacion_velocidad.grid(row=0, column=0, ipadx = 0, padx=0, pady=0, sticky="nswe")
        CTkToolTip(self.b_iniciar_caracterizacion_velocidad, message="Iniciar caracterizacion de velocidad", delay=0.5, font=ctk.CTkFont(size=12))

        # Reiniciar caracterización velocidad.
        self.b_reiniciar_caracterizacion_velocidad = ctk.CTkButton(self.f_botones_caracterizacion_velocidad, text="↻" , text_color = "#ffffff", fg_color="#C7BE19",width=25, height=15,
                                                   hover_color="#9da31e", border_color="#CFC61B", border_width=1, corner_radius=5,command=self.reiniciar_caracterizacion_velocidad,font=ctk.CTkFont(size=24, weight="bold"))
        self.b_reiniciar_caracterizacion_velocidad.grid(row=0, column=1, ipadx = 0, padx=0, pady=0, sticky="nswe")
        CTkToolTip(self.b_reiniciar_caracterizacion_velocidad, message="Reiniciar caracterizacion de velocidad", delay=0.5, font=ctk.CTkFont(size=12))

        # Parar caracterización velocidad.
        self.b_parar_caracterizacion_velocidad = ctk.CTkButton(self.f_botones_caracterizacion_velocidad, text="◼", text_color = "#ffffff",width=25, height=15, 
        fg_color="#f56a6a", hover_color = "#ee4242", border_color="#ff0000",corner_radius=5,border_width=1, command=self.parar_caracterizacion_velocidad,font=ctk.CTkFont(size=24, weight="bold"))
        self.b_parar_caracterizacion_velocidad.grid(row=0, column=2, ipadx = 0 ,padx=0, pady=0, sticky="nswe")
        CTkToolTip(self.b_parar_caracterizacion_velocidad, message="Detener el caracterizacion de velocidad ya iniciado", delay=0.5, font=ctk.CTkFont(size=12))

        # Caracterización flujo.
        self.l_caracterizacion_flujo = ctk.CTkLabel(self.f_caracterizacion_scroll, text="Flujo", text_color="#458B8D", font=ctk.CTkFont(size=20, weight="bold"))
        self.l_caracterizacion_flujo.grid(row=1, column=1, padx=60, pady=0, sticky="ws")

        # Gráfica en tiempo real - flujo.
        fig_flujo = Figure(figsize=(10,5),dpi=60)
        self.ax_flujo = fig_flujo.add_subplot(111)
        self.ax_flujo.set_xlim(0,int(self.e_tiempo_caracterizacion.get()))
        self.ax_flujo.set_ylim(config.LIMITESY["flujo"][0],config.LIMITESY["flujo"][1])  
        self.ax_flujo.set_xlabel("Tiempo (s)")
        self.ax_flujo.set_ylabel("Flujo (ml/min)")
        self.ax_flujo.plot(self.tiempo_grafica_flujo,self.buffer_grafica_flujo)
        fig_flujo.set_facecolor('#242424')  
        self.ax_flujo.set_facecolor("#242424")  
        self.ax_flujo.tick_params(colors = "#ffffff") 
        self.ax_flujo.xaxis.label.set_color("#ffffff")  
        self.ax_flujo.yaxis.label.set_color("#ffffff")  
        self.ax_flujo.spines['bottom'].set_color('#ffffff')  
        self.ax_flujo.spines['left'].set_color('#ffffff')  
        self.ax_flujo.spines['top'].set_color('#ffffff')  
        self.ax_flujo.spines['right'].set_color('#ffffff')  
        fig_flujo.tight_layout()
        self.canvas_flujo = FigureCanvasTkAgg(fig_flujo, master=self.f_caracterizacion_scroll)
        self.canvas_flujo.get_tk_widget().grid(row=2, column=1, padx=10, pady=0, sticky="nsew")
        self.canvas_flujo.draw()

        self.f_botones_caracterizacion_flujo = ctk.CTkFrame(self.f_caracterizacion_scroll, fg_color="transparent", width=75, height=15, corner_radius=10,border_width=1)
        self.f_botones_caracterizacion_flujo.grid(row=1, column=1, padx=10, pady=0, sticky="se")
        self.f_botones_caracterizacion_flujo.grid_columnconfigure(0, weight=1)
        self.f_botones_caracterizacion_flujo.grid_columnconfigure(1, weight=1)
        self.f_botones_caracterizacion_flujo.grid_columnconfigure(2, weight=1)

        # Iniciar caracterización flujo.
        self.b_iniciar_caracterizacion_flujo = ctk.CTkButton(self.f_botones_caracterizacion_flujo, text="▶", text_color = "#ffffff", fg_color="#85ad75", width=25, height=15, 
        hover_color="#488f51", border_color="#006400", border_width=1, corner_radius=5,command=self.iniciar_caracterizacion_flujo,font=ctk.CTkFont(size=24, weight="bold"))
        self.b_iniciar_caracterizacion_flujo.grid(row=0, column=0, ipadx = 0, padx=0, pady=0, sticky="nswe")
        CTkToolTip(self.b_iniciar_caracterizacion_flujo, message="Iniciar caracterizacion de flujo", delay=0.5, font=ctk.CTkFont(size=12))
       
        # Reiniciar caracterización flujo.
        self.b_reiniciar_caracterizacion_flujo = ctk.CTkButton(self.f_botones_caracterizacion_flujo, text="↻" , text_color = "#ffffff", fg_color="#C7BE19",width=25, height=15,
                                                   hover_color="#9da31e", border_color="#CFC61B", border_width=1, corner_radius=5,command=self.reiniciar_caracterizacion_flujo,font=ctk.CTkFont(size=24, weight="bold"))
        self.b_reiniciar_caracterizacion_flujo.grid(row=0, column=1, ipadx = 0, padx=0, pady=0, sticky="nswe")
        CTkToolTip(self.b_reiniciar_caracterizacion_flujo, message="Reiniciar caracterizacion de flujo", delay=0.5, font=ctk.CTkFont(size=12))

        # Parar caracterización flujo.
        self.b_parar_caracterizacion_flujo = ctk.CTkButton(self.f_botones_caracterizacion_flujo, text="◼", text_color = "#ffffff",width=25, height=15, 
        fg_color="#f56a6a", hover_color = "#ee4242", border_color="#ff0000",corner_radius=5,border_width=1, command=self.parar_caracterizacion_flujo,font=ctk.CTkFont(size=24, weight="bold"))
        self.b_parar_caracterizacion_flujo.grid(row=0, column=2, ipadx = 0 ,padx=0, pady=0, sticky="nswe")
        CTkToolTip(self.b_parar_caracterizacion_flujo, message="Detener el caracterizacion de flujo ya iniciado", delay=0.5, font=ctk.CTkFont(size=12))
        
        # Caracterización concentración.
        self.l_caracterizacion_concentracion = ctk.CTkLabel(self.f_caracterizacion_scroll, text="Concentración", text_color="#458B8D", font=ctk.CTkFont(size=20, weight="bold"))
        self.l_caracterizacion_concentracion.grid(row=3, column=0, padx=60, pady=0, sticky="ws")

        # Gráfica en tiempo real - concentración.
        fig_concentracion = Figure(figsize=(10,5),dpi=60)
        self.ax_concentracion = fig_concentracion.add_subplot(111)
        self.ax_concentracion.set_xlim(0,int(self.e_tiempo_caracterizacion.get()))
        self.ax_concentracion.set_ylim(config.LIMITESY["concentracion"][0],config.LIMITESY["concentracion"][1])  
        self.ax_concentracion.set_xlabel("Tiempo (s)")
        self.ax_concentracion.set_ylabel("Índice VOC")
        self.ax_concentracion.plot(self.tiempo_grafica_concentracion,self.buffer_grafica_concentracion)
        fig_concentracion.set_facecolor('#242424')  
        self.ax_concentracion.set_facecolor("#242424")  
        self.ax_concentracion.tick_params(colors = "#ffffff") 
        self.ax_concentracion.xaxis.label.set_color("#ffffff") 
        self.ax_concentracion.yaxis.label.set_color("#ffffff")  
        self.ax_concentracion.spines['bottom'].set_color('#ffffff')  
        self.ax_concentracion.spines['left'].set_color('#ffffff')  
        self.ax_concentracion.spines['top'].set_color('#ffffff')  
        self.ax_concentracion.spines['right'].set_color('#ffffff')  
        fig_concentracion.tight_layout()
        self.canvas_concentracion = FigureCanvasTkAgg(fig_concentracion, master=self.f_caracterizacion_scroll)
        self.canvas_concentracion.get_tk_widget().grid(row=4, column=0, padx=10, pady=0, sticky="nsew")
        self.canvas_concentracion.draw()

        self.f_botones_caracterizacion_concentracion = ctk.CTkFrame(self.f_caracterizacion_scroll, fg_color="transparent", width=75, height=15, corner_radius=10,border_width=1)
        self.f_botones_caracterizacion_concentracion.grid(row=3, column=0, padx=10, pady=0, sticky="se")
        self.f_botones_caracterizacion_concentracion.grid_columnconfigure(0, weight=1)
        self.f_botones_caracterizacion_concentracion.grid_columnconfigure(1, weight=1)
        self.f_botones_caracterizacion_concentracion.grid_columnconfigure(2, weight=1)

        # Iniciar caracterización concentración.
        self.b_iniciar_caracterizacion_concentracion = ctk.CTkButton(self.f_botones_caracterizacion_concentracion, text="▶", text_color = "#ffffff", fg_color="#85ad75", width=25, height=15, 
        hover_color="#488f51", border_color="#006400", border_width=1, corner_radius=5,command=self.iniciar_caracterizacion_concentracion,font=ctk.CTkFont(size=24, weight="bold"))
        self.b_iniciar_caracterizacion_concentracion.grid(row=0, column=0, ipadx = 0, padx=0, pady=0, sticky="nswe")
        CTkToolTip(self.b_iniciar_caracterizacion_concentracion, message="Iniciar caracterizacion de concentración", delay=0.5, font=ctk.CTkFont(size=12))
       
        # Reiniciar caracterización concentración.
        self.b_reiniciar_caracterizacion_concentracion = ctk.CTkButton(self.f_botones_caracterizacion_concentracion, text="↻" , text_color = "#ffffff", fg_color="#C7BE19",width=25, height=15,
                                                   hover_color="#9da31e", border_color="#CFC61B", border_width=1, corner_radius=5,command=self.reiniciar_caracterizacion_concentracion,font=ctk.CTkFont(size=24, weight="bold"))
        self.b_reiniciar_caracterizacion_concentracion.grid(row=0, column=1, ipadx = 0, padx=0, pady=0, sticky="nswe")
        CTkToolTip(self.b_reiniciar_caracterizacion_concentracion, message="Reiniciar caracterizacion de concentración", delay=0.5, font=ctk.CTkFont(size=12))

        # Parar caracterización concentración.
        self.b_parar_caracterizacion_concentracion = ctk.CTkButton(self.f_botones_caracterizacion_concentracion, text="◼", text_color = "#ffffff",width=25, height=15, 
        fg_color="#f56a6a", hover_color = "#ee4242", border_color="#ff0000",corner_radius=5,border_width=1, command=self.parar_caracterizacion_concentracion,font=ctk.CTkFont(size=24, weight="bold"))
        self.b_parar_caracterizacion_concentracion.grid(row=0, column=2, ipadx = 0 ,padx=0, pady=0, sticky="nswe")
        CTkToolTip(self.b_parar_caracterizacion_concentracion, message="Detener el caracterizacion de concentración ya iniciado", delay=0.5, font=ctk.CTkFont(size=12))

        # Caracterización latencia.
        self.l_caracterizacion_latencia = ctk.CTkLabel(self.f_caracterizacion_scroll, text="Latencia", text_color="#458B8D", font=ctk.CTkFont(size=20, weight="bold"))
        self.l_caracterizacion_latencia.grid(row=3, column=1, padx=60, pady=0, sticky="ws")

        # Gráfica en tiempo real - latencia.
        fig_latencia = Figure(figsize=(10,5),dpi=60)
        self.ax_latencia = fig_latencia.add_subplot(111)
        self.ax_latencia.set_xlim(0,int(self.e_tiempo_caracterizacion.get()))
        self.ax_latencia.set_ylim(config.LIMITESY["latencia"][0],config.LIMITESY["latencia"][1])  
        self.ax_latencia.set_xlabel("Tiempo (s)")
        self.ax_latencia.set_ylabel("Latencia (ms)")
        self.ax_latencia.plot(self.tiempo_grafica_latencia,self.buffer_grafica_latencia)
        fig_latencia.set_facecolor('#242424') 
        self.ax_latencia.set_facecolor("#242424")  
        self.ax_latencia.tick_params(colors = "#ffffff") 
        self.ax_latencia.xaxis.label.set_color("#ffffff")  
        self.ax_latencia.yaxis.label.set_color("#ffffff")  
        self.ax_latencia.spines['bottom'].set_color('#ffffff') 
        self.ax_latencia.spines['left'].set_color('#ffffff')  
        self.ax_latencia.spines['top'].set_color('#ffffff')  
        self.ax_latencia.spines['right'].set_color('#ffffff')  
        fig_latencia.tight_layout()
        self.canvas_latencia = FigureCanvasTkAgg(fig_latencia, master=self.f_caracterizacion_scroll)
        self.canvas_latencia.get_tk_widget().grid(row=4, column=1, padx=10, pady=0, sticky="nsew")
        self.canvas_latencia.draw()

        self.f_botones_caracterizacion_latencia = ctk.CTkFrame(self.f_caracterizacion_scroll, fg_color="transparent", width=75, height=15, corner_radius=10,border_width=1)
        self.f_botones_caracterizacion_latencia.grid(row=3, column=1, padx=10, pady=0, sticky="se")
        self.f_botones_caracterizacion_latencia.grid_columnconfigure(0, weight=1)
        self.f_botones_caracterizacion_latencia.grid_columnconfigure(1, weight=1)
        self.f_botones_caracterizacion_latencia.grid_columnconfigure(2, weight=1)

        # Iniciar caracterización latencia.
        self.b_iniciar_caracterizacion_latencia = ctk.CTkButton(self.f_botones_caracterizacion_latencia, text="▶", text_color = "#ffffff", fg_color="#85ad75", width=25, height=15, 
        hover_color="#488f51", border_color="#006400", border_width=1, corner_radius=5,command=self.iniciar_caracterizacion_latencia,font=ctk.CTkFont(size=24, weight="bold"))
        self.b_iniciar_caracterizacion_latencia.grid(row=0, column=0, ipadx = 0, padx=0, pady=0, sticky="nswe")
        CTkToolTip(self.b_iniciar_caracterizacion_latencia, message="Iniciar caracterizacion de latencia", delay=0.5, font=ctk.CTkFont(size=12))
       
        # Reiniciar caracterización latencia.
        self.b_reiniciar_caracterizacion_latencia = ctk.CTkButton(self.f_botones_caracterizacion_latencia, text="↻" , text_color = "#ffffff", fg_color="#C7BE19",width=25, height=15,
                                                   hover_color="#9da31e", border_color="#CFC61B", border_width=1, corner_radius=5,command=self.reiniciar_caracterizacion_latencia,font=ctk.CTkFont(size=24, weight="bold"))
        self.b_reiniciar_caracterizacion_latencia.grid(row=0, column=1, ipadx = 0, padx=0, pady=0, sticky="nswe")
        CTkToolTip(self.b_reiniciar_caracterizacion_latencia, message="Reiniciar caracterizacion de latencia", delay=0.5, font=ctk.CTkFont(size=12))

        # Parar caracterización latencia.
        self.b_parar_caracterizacion_latencia = ctk.CTkButton(self.f_botones_caracterizacion_latencia, text="◼", text_color = "#ffffff",width=25, height=15, 
        fg_color="#f56a6a", hover_color = "#ee4242", border_color="#ff0000",corner_radius=5,border_width=1, command=self.parar_caracterizacion_latencia,font=ctk.CTkFont(size=24, weight="bold"))
        self.b_parar_caracterizacion_latencia.grid(row=0, column=2, ipadx = 0 ,padx=0, pady=0, sticky="nswe")
        CTkToolTip(self.b_parar_caracterizacion_latencia, message="Detener el caracterizacion de latencia ya iniciado", delay=0.5, font=ctk.CTkFont(size=12))

        # Llamamiento para el inicio del bucle de actualización de gráficas de caracterización.
        self._actualizar_graficas()

        # TabView Protocolo-Estado.
        self.tv_prot_est = ctk.CTkTabview(master=self, fg_color="transparent",border_color="#4a4c4e", border_width=1, corner_radius=10, width=400)
        self.tv_prot_est.grid(row=1,column=1,padx=5,pady=10,sticky="nsew", rowspan=3)
        self.tv_prot_est.add("Protocolo")
        self.tv_prot_est.add("Estado")
        self.tv_prot_est._segmented_button.configure(text_color="#ffffff", border_width=1, corner_radius=10, width = 200,height =30, font=ctk.CTkFont(size=20, weight="bold"))
        self.tv_prot_est.tab("Protocolo").grid_columnconfigure(0, weight=1)
        self.tv_prot_est.tab("Estado").grid_columnconfigure(0, weight=1)
        self.tv_prot_est.set("Protocolo")

        # Protocolo. 
        # Número de ciclos .
        self.l_num_ciclos = ctk.CTkLabel(self.tv_prot_est.tab("Protocolo"), text="Número de ciclos", font=ctk.CTkFont(size=14,weight="bold"))
        self.l_num_ciclos.grid(row=0, column=0, padx=10, pady=(10,2), sticky="we", rowspan=1)
        self.e_num_ciclos =SpinboxCTk(self.tv_prot_est.tab("Protocolo"), valor= 3, valor_max=config.VALOR_MAX_CICLOS, valor_min=config.VALOR_MIN_CICLOS)
        self.e_num_ciclos.grid(row=1, column=0, padx=5, pady=(4,2), sticky="n")
        self._asignar_tooltip_spinbox(self.e_num_ciclos, mensaje_entry="Introduzca el número de ciclos de exposición y desensibilización que se realizarán durante el protocolo.\nCada ciclo consiste en un período de exposición seguido de un período de desensibilización.")

        # Intervalo entre ciclos.
        self.l_intervalo_ciclos = ctk.CTkLabel(self.tv_prot_est.tab("Protocolo"), text="Intervalo entre ciclos (en sec)", font=ctk.CTkFont(size=14,weight="bold"))
        self.l_intervalo_ciclos.grid(row=2, column=0, padx=10, pady=(4,2), sticky="we", rowspan=1)
        self.e_intervalo_ciclos =SpinboxCTk(self.tv_prot_est.tab("Protocolo"), valor= 60, valor_max=config.VALOR_MAX_INTERVALO_CICLOS, valor_min=config.VALOR_MIN_INTERVALO_CICLOS)
        self.e_intervalo_ciclos.grid(row=3, column=0, padx=5, pady=(4,2), sticky="n")
        self._asignar_tooltip_spinbox(self.e_intervalo_ciclos, mensaje_entry="Introduzca el intervalo entre ciclos del protocolo (en segundos).")

        # Tiempo de exposición.
        self.l_tiempo_exposicion = ctk.CTkLabel(self.tv_prot_est.tab("Protocolo"), text="Exposición (en sec)", font=ctk.CTkFont(size=14,weight="bold"))
        self.l_tiempo_exposicion.grid(row=4, column=0, padx=10, pady=(4,2), sticky="we")
        self.e_tiempo_exposicion = SpinboxCTk(self.tv_prot_est.tab("Protocolo"), valor=3, valor_max=config.VALOR_MAX_TIEMPO_EXPOSICION, valor_min=config.VALOR_MIN_TIEMPO_EXPOSICION)
        self.e_tiempo_exposicion.grid(row=5, column=0, padx=5, pady=(4,2), sticky="n")
        self._asignar_tooltip_spinbox(self.e_tiempo_exposicion, mensaje_entry="Introduzca el tiempo de exposición (en segundos) de los odorantes introducidos en el protocolo.")

        # Tiempo de desensibilización.
        self.l_tiempo_desensibilizacion = ctk.CTkLabel(self.tv_prot_est.tab("Protocolo"), text="Desensibilización (en sec)", font=ctk.CTkFont(size=14,weight="bold"))
        self.l_tiempo_desensibilizacion.grid(row=6, column=0, padx=10, pady=(4,2), sticky="we")
        self.e_tiempo_desensibilizacion = SpinboxCTk(self.tv_prot_est.tab("Protocolo"), valor=30, valor_max=config.VALOR_MAX_TIEMPO_DESENSIBILIZACION, valor_min=config.VALOR_MIN_TIEMPO_DESENSIBILIZACION)
        self.e_tiempo_desensibilizacion.grid(row=7, column=0, padx=5, pady=(4,2), sticky="n")
        self._asignar_tooltip_spinbox(self.e_tiempo_desensibilizacion, mensaje_entry="Introduzca el tiempo de desensibilización (en segundos) entre los odorantes introducidos en el protocolo para la limpieza de los canales y reposo del paciente.")

        # Orden de los canales.
        self.l_orden_canales = ctk.CTkLabel(self.tv_prot_est.tab("Protocolo"), text="Orden de los canales", font=ctk.CTkFont(size=14,weight="bold"))
        self.l_orden_canales.grid(row=8, column=0, padx=10, pady=(30,5), sticky="n")
        self.cb_secuencial = ctk.CTkCheckBox(self.tv_prot_est.tab("Protocolo"), text="Secuencial", font=ctk.CTkFont(size=14))
        self.cb_secuencial.grid(row=9, column=0, padx=40, pady=(4,2), sticky="w")
        # Por defecto el orden de los canales en el protocolo experimental es secuencial.
        self.cb_secuencial.select() 
        self.cb_aleatorio = ctk.CTkCheckBox(self.tv_prot_est.tab("Protocolo"), text="Aleatorio", font=ctk.CTkFont(size=14))
        self.cb_aleatorio.grid(row=9, column=0, padx=40, pady=(4,2), sticky="e")
        CTkToolTip(self.cb_aleatorio, message="Seleccione esta opción para que los odorantes se presenten en un orden aleatorio durante el protocolo.", delay=0.5, font=ctk.CTkFont(size=12))
        CTkToolTip(self.cb_secuencial, message="Seleccione esta opción para que los odorantes se presenten en un orden secuencial durante el protocolo.", delay=0.5, font=ctk.CTkFont(size=12))
    
        # Iniciar protocolo.
        self.b_iniciar_protocolo = ctk.CTkButton(self.tv_prot_est.tab("Protocolo"), text="▶", text_color = "#ffffff", fg_color="#85ad75", width=15, height=20, 
        hover_color="#488f51", border_color="#006400", border_width=1, corner_radius=10,command=self.iniciar_protocolo,font=ctk.CTkFont(size=34, weight="bold"))
        self.b_iniciar_protocolo.grid(row=18, column=0, padx=50, pady=(60,5), sticky="w")
        CTkToolTip(self.b_iniciar_protocolo, message="Inicio del protocolo configurado", delay=0.5, font=ctk.CTkFont(size=12))

        # Reiniciar protocolo.
        self.b__reiniciar_protocolo = ctk.CTkButton(self.tv_prot_est.tab("Protocolo"), text="↻" , text_color = "#ffffff", fg_color="#C7BE19",width=15, height=20, 
                                                   hover_color="#9da31e", border_color="#F6F04F", border_width=1, corner_radius=10,command=self._consulta__reiniciar_protocolo,font=ctk.CTkFont(size=34, weight="bold"))
        self.b__reiniciar_protocolo.grid(row=18, column=0, padx=10, pady=(60,5), sticky="n")
        CTkToolTip(self.b__reiniciar_protocolo, message="Reinicio del protocolo configurado", delay=0.5, font=ctk.CTkFont(size=12))

        # Parar protocolo.
        self.b__parar_protocolo = ctk.CTkButton(self.tv_prot_est.tab("Protocolo"), text="◼", text_color = "#ffffff",width=15, height=20, 
        fg_color="#f56a6a", hover_color = "#ee4242", border_color="#ff0000",corner_radius=10,border_width=1, command=self._consulta__parar_protocolo,font=ctk.CTkFont(size=34, weight="bold"))
        self.b__parar_protocolo.grid(row=18, column=0, padx=50, pady=(60,5), sticky="e")
        CTkToolTip(self.b__parar_protocolo, message="Parada del protocolo configurado ya iniciado", delay=0.5, font=ctk.CTkFont(size=12))

        # Estado.
        self.l_fecha = ctk.CTkLabel(self.tv_prot_est.tab("Estado"), text=f"Fecha y hora: {time.strftime(config.FORMATO_TIMESTAMP, time.localtime())}", font=ctk.CTkFont(size=14, weight="bold"))
        self.l_fecha.grid(row=0, column=0, padx=10, pady=(20,5), sticky="n")

        self.tiempo_inicio_sesion = time.time()  

        # Duracion de la sesión.
        self.duracion_sesion= ctk.StringVar(value="Duración de sesión: 00:00:00")  
        self.l_duracion_sesion = ctk.CTkLabel(self.tv_prot_est.tab("Estado"), textvariable=self.duracion_sesion, font=ctk.CTkFont(size=14, weight="bold"))
        self.l_duracion_sesion.grid(row=1, column=0, padx=10, pady=(20,5), sticky="n")

        # Identificador de la sesión (anonimizado).
        self.l_id_sesion = ctk.CTkLabel(self.tv_prot_est.tab("Estado"), text="ID de sesión: ", font=ctk.CTkFont(size=14, weight="bold"))
        self.l_id_sesion.grid(row=4, column=0, padx=71, pady=(20,5), sticky="w")

        self.e_id_sesion= ctk.CTkEntry(self.tv_prot_est.tab("Estado"), placeholder_text="introduzca identificador", font=ctk.CTkFont(size=14))
        self.e_id_sesion.grid(row=4, column=0, padx=71, pady=(20,5), sticky="e")
        CTkToolTip(self.e_id_sesion, message="Introduzca un identificador único anonimizado para la sesión experimental. Este identificador se utilizará para generar el informe de la sesión y para guardar los datos asociados a esta sesión.", delay=0.5, font=ctk.CTkFont(size=12))

        # Identificador de paciente (anonimizado).
        self.l_id_paciente = ctk.CTkLabel(self.tv_prot_est.tab("Estado"), text="ID de paciente: ", font=ctk.CTkFont(size=14, weight="bold"))
        self.l_id_paciente.grid(row=5, column=0, padx=65, pady=(20,5), sticky="w")

        self.e_id_paciente= ctk.CTkEntry(self.tv_prot_est.tab("Estado"), placeholder_text="introduzca identificador", font=ctk.CTkFont(size=14))
        self.e_id_paciente.grid(row=5, column=0, padx=65, pady=(20,5), sticky="e")
        CTkToolTip(self.e_id_paciente, message="Introduzca un identificador único anonimizado para el paciente. Este identificador se utilizará para generar el informe de la sesión y para guardar los datos asociados a esta sesión.", delay=0.5, font=ctk.CTkFont(size=12))

        # Canal anterior.
        self.l_canal_anterior, self.l_canal_anterior_valor = self._crear_pareja_estado(
            self.tv_prot_est.tab("Estado"), fila=7, texto="Canal anterior: ", stringvar=self.sv_canal_anterior)

        # Canal activo.
        self.l_canal_activo, self.l_canal_activo_valor = self._crear_pareja_estado(
            self.tv_prot_est.tab("Estado"), fila=8, texto="Canal activo: ", stringvar=self.sv_canal_activo)

        # Canal siguiente.
        self.l_canal_siguiente, self.l_canal_siguiente_valor = self._crear_pareja_estado(
            self.tv_prot_est.tab("Estado"), fila=9, texto="Canal siguiente: ", stringvar=self.sv_canal_siguiente)

        # Latencia en tiempo real.
        self.sv_latencia_canal= ctk.StringVar(value="0 ms")
        self.l_latencia_canal, self.l_valor_latencia_canal = self._crear_pareja_estado(
            self.tv_prot_est.tab("Estado"), fila=11, texto="Latencia: ", stringvar=self.sv_latencia_canal)  

        # Generar informe.
        self.b_generar_informe = ctk.CTkButton(self.tv_prot_est.tab("Estado"), text="Generar informe de sesión", fg_color="#5172a4",text_color="#ffffff",
                                       corner_radius=10,border_width=1, border_color="#6ba2f4",command=self.generar_informe,
                                       font=ctk.CTkFont(size=18, weight="bold"))
        self.b_generar_informe.grid(row=13, column=0, padx=31, pady=(30,5), sticky="n")
        CTkToolTip(self.b_generar_informe, message="Genera un informe de la sesión experimental actual en formato PDF, Excel o CSV.\n El informe incluirá los datos de la sesión, los resultados de caracterización, además de los historiales completos de caracterización y sesión.", delay=0.5, font=ctk.CTkFont(size=12))

    
    def _crear_pareja_estado(self, tabview, fila, texto, stringvar, pady=(20,5)):
        """
        Genera una pareja de objetos CTkLabel actualizable.

        Crea en la correspondiete fila de una sección de específica de un objeto Tabview pasado, una pareja CTkLabel equivalente a etiqueta-valor.
        Destinado al registro y actualización en tiempo real de una variable de interés en el software.
        
        Args: 
            - tabview (TabViewCTk): Sección del objeto TabViewCTk donde generar la pareja de objetos.
            - fila (int): Ubicación dentro de la sección especificada para la generación de par.
            - texto (str): Texto asociado a la etiqueta del par generado.
            - stringvar (StringVarCTk): StringVarCTk con el valor a actualizar.
            - pady (tupla(int,int)): Dimensiones del marco contenedro del par generado.
        Return:
            - etiqueta (CTkLabel): Etiqueta del valor representado.
            - valor (CTkLabel): CTkLabel representativo del valor del StringVarCTk asociado.
        Raises:
            Ninguno.

        """

        contenedor = ctk.CTkFrame(tabview, fg_color="transparent")
        contenedor.grid(row=fila, column=0, pady=pady, sticky="n")

        etiqueta = ctk.CTkLabel(contenedor, text=texto, font=ctk.CTkFont(size=14, weight="bold"))
        etiqueta.pack(side="left")

        valor = ctk.CTkLabel(contenedor, textvariable=stringvar, font=ctk.CTkFont(size=14))
        valor.pack(side="left", padx=(4, 0))

        return etiqueta, valor


    def _construir_datos_informe(self):
        """
        Genera el objeto DatosInforme con los datos correspondientes de la sesión experimental realizada.

        Asocia cada atributo del objeto DatosInforme al valor de una variable global con información relativa a la sesión experimental.
        
        Args: 
            Ninguno.
        Return:
            - reports.DatosInforme(...) (DatosInforme): Objeto DatosInforme con todos los datos generados en la sesión experimental.
        Raises:
            Ninguno.

        """

        return reports.DatosInforme(
                id_sesion = self.e_id_sesion.get(),
                id_paciente = self.e_id_paciente.get(),
                duracion_sesion = self.duracion_sesion.get(),
                tiempo_inicio_sesion = float(self.tiempo_inicio_sesion),
                num_ciclos = self.e_num_ciclos.get(),
                tiempo_exposicion = self.e_tiempo_exposicion.get(),
                tiempo_desensibilizacion = self.e_tiempo_desensibilizacion.get(),
                intervalo_ciclos = self.e_intervalo_ciclos.get(),
                tiempo_caracterizacion = self.e_tiempo_caracterizacion.get(),
                historial_sesion = self.historial_sesion,
                historial_caracterizacion = self.historial_caracterizacion,
                colores_canales = self.colores_canales,
        )

    
    def generar_informe(self):
        """
        Genera el informe de la sesión experimental realizada en el formato de interés.

        A partir de la ventana flotante generada, se consulta al usuario el formato de interés deseado. Tras su selección se procede al llamamiento del método de generación
        del formato correspondiente, eliminado a su vez el archivo de guardado temporal.
        
        Args: 
            Ninguno.
        Return:
            - reports.DatosInforme(...) (DatosInforme): Objeto DatosInforme con todos los datos generados en la sesión experimental.
        Raises:
            Ninguno.

        """

        # Evalucion del software.
        # Marca de tiempo para medir la duración de la generación del informe.
        #self.t0_actualizacion_generacion_informe = time.perf_counter()  

        formatos = [('PDF','*.pdf'),('Excel', '*.xlsx'),('CSV','*.csv')]

        ruta = ctk.filedialog.asksaveasfilename(title='Guardar informe de sesión',
                                                filetypes=formatos, defaultextension=".pdf",
                                                  initialfile=f'Informe_OlfaMetric_{self.e_id_sesion.get()}_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}')
        
        if not ruta:
            self.consola.registro("Generación de informe cancelada. No se ha seleccionado ninguna ruta de guardado.", nivel="AVISO")
            return
        
        datos= self._construir_datos_informe()

        self.consola.registro(f'Generando informe en {ruta}....')

        if ruta.endswith('.pdf'):

            try:
                reports.generar_pdf(ruta, datos)
                self.consola.registro(f"InformePDF generado correctamente en {ruta}")
                if self.ruta_archivo_temporal and os.path.exists(self.ruta_archivo_temporal):
                    self.consola.registro(f"Archivo temporal eliminado de: {self.ruta_archivo_temporal}")
                    os.remove(self.ruta_archivo_temporal)  
                    
            except Exception as e:
                import traceback
                self.consola.registro(f'Error al generar informe PDF: {e}', nivel = "ERROR")
                self.consola.registro(traceback.format_exc(), nivel="ERROR")

        elif ruta.endswith('.xlsx'):

            try:
                reports.generar_excel(ruta, datos)
                self.consola.registro(f"Informe Excel generado correctamente en {ruta}")
                if self.ruta_archivo_temporal and os.path.exists(self.ruta_archivo_temporal):
                    self.consola.registro(f"Archivo temporal eliminado de: {self.ruta_archivo_temporal}")
                    os.remove(self.ruta_archivo_temporal)  
                    
            except Exception as e:
                self.consola.registro(f'Error al generar informe Excel: {e}', nivel = "ERROR")

        elif ruta.endswith('.csv'):

            try:
                reports.generar_csv(ruta, datos)
                self.consola.registro(f"Informe CSV generado correctamente en {ruta}")
                if self.ruta_archivo_temporal and os.path.exists(self.ruta_archivo_temporal):
                    self.consola.registro(f"Archivo temporal eliminado de: {self.ruta_archivo_temporal}")
                    os.remove(self.ruta_archivo_temporal) 
                    
            except Exception as e:
                self.consola.registro(f'Error al generar informe CSV: {e}', nivel = "ERROR")


        # Evaluación del software.
        #self.update_idletasks()
        #diferencia_temporal = time.perf_counter() - self.t0_actualizacion_generacion_informe
        #self.tiempos_actualizacion ["generacion_informe"].append(diferencia_temporal)
        #self.t0_actualizacion_generacion_informe = 0
        #print(f"Tiempo de actualización de la UI al generar informe: {diferencia_temporal} segundos")




    def iniciar_busqueda_mdns(self):
        """
        Comienza la búsqueda del ESP32-WROOM-32U mediante mDNS en la red local.

        Tras deshabilitar el correspondiente botón de búsqueda, llama al método encargado de resolver la URI del ESP32-WROOM-32U en un hilo secundario para evitar
        el bloqueo del hilo principal tkinter en el que corre la aplicación. En función del resultado en la búsqueda de la URI, ejecuta lo antes posible el método relativo 
        a la conexión con el dispositivo; o informa del fracaso en el intento de actualización.
        de la URI.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        # Evaluación del software.
        #self.t0_actualizacion_buscar_dispositivos_mdns = time.perf_counter()  # Marca de tiempo para medir la duración de la búsqueda de dispositivos.

        self.consola.registro("Buscando dispositivos en la red...")

        # Se deshabilita el botón para evitar reintentos de búsqueda local de dispositivos. 
        self.b_buscar_dispositivos.configure(state="disabled")


        def _hilo_busqueda_mdns():
            """
            Conecta el dispositivo con la URI encontrada, o informa de fallo en la búsqueda mediante mDNS.

            En función de obtener o no la URI resuelta del dispositivo: conecta el software de control con el nuevo identificador o informa al usuario del fallo de la búsqueda realizada.

            Args:
                Ninguno.
            Return:
                Ninguno.
            Raises:
                Ninguno.

            """

            uri = discovery.buscar_mdns()

            if uri:
                self.after(0,self._conectar_dispositivo_encontrado, uri)
            else:
                self.after(0, self._informar_no_encontrado)

        threading.Thread(target=_hilo_busqueda_mdns, daemon=True).start()

        # Evaluación del software.
        #self.update_idletasks()
        #diferencia_temporal = time.perf_counter() - self.t0_actualizacion_buscar_dispositivos_mdns
        #self.tiempos_actualizacion ["buscar_dispositivos_mdns"].append(diferencia_temporal)
        #self.t0_actualizacion_buscar_dispositivos_mdns = 0
        #print(f"Tiempo de actualización de la UI al buscar dispositivos MDNS: {diferencia_temporal} segundos")


    def _informar_no_encontrado(self):
        """
        Informa al usuario del fracaso en la búsqueda del dispositivo en la red local.

        Muestra un mensaje por consola del fracaso en la actualización de la URI del dispositivo en la red local, actualiza el widget de estado de conexión
        y rehabilita el botón de búsqueda.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.consola.registro(f'No se encontró ningún dispositivo', nivel = "AVISO")
        self.l_estado_conexion.configure(text="✕ Error",text_color="#fa8989")
        self.b_buscar_dispositivos.configure(state="normal")


    def _conectar_dispositivo_encontrado(self,uri):
        """
        Conecta el software de control con el ESP32-WROOM-32U a través de la nueva URI encontrada.

        Muestra por consola al usuario del éxito de la búsqueda del dispositivo en la red local y detiene la coneción WebScoket existente para iniciar una nueva con la
        URI actualizada. 
        
        Args: 
            - uri (str): URI actualizada del dispositivo encontrado mediante mDNS.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """
        
        self.consola.registro(f'Dispositivo encontrado: {uri}')
        self.ws_client.detener()
        self.ws_client.uri = uri
        self.ws_client.iniciar()

        
    def _tiempo_sesion(self): 
        """
        Calcula la duración y fecha actual de la sesión experimental realizada.

        A partir de la comparación con el tiempo inicial registrado calcula la duración de la sesión experimental y representa la fecha exacta de realización de la misma.
        Se autoreagenda tras un segundo, formado un bucle para actualizar ambos cálculos mientras la aplicación siga abierta.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        tiempo = time.strftime(config.FORMATO_HORA, time.gmtime(time.time()-self.tiempo_inicio_sesion))
        self.duracion_sesion.set(f"Duración de sesión: {tiempo}")

        tiempo_local = time.strftime(config.FORMATO_TIMESTAMP, time.localtime())
        self.l_fecha.configure(text=f"Fecha y hora: {tiempo_local}")

        self.after(1000, self._tiempo_sesion)


    def actualizar_comb_canales_caracterizacion(self):
        """
        Actualiza el CTkComboBox encargado de la selección del canal a caracterizar.

        Incluye en el CTkComboBox los canales con un odorante asociado, además del correpondiente canal destina a la desenbilización.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        valores = [canal.e_olor_canal.get() for canal in self.cuadros_canales if canal.e_olor_canal.get()] 
        valores.append("Canal Blanco")
        self.comb_canales_caracterizacion.configure(values=valores)


    def _bloquear_botones(self,bloquear):
        """
        Deshabilita todos los botones de acción y widgets de la aplicación software que no sean indispensables durante la ejecución del protocolo. 

        Deshabilita todos los botones y widgets accionables presentes en la aplicación a expección del destinado a parar el protocolo para garantizar la seguridad 
        del paciente y posibilitar la parada si fuera necesaria.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        if bloquear:
            
            # Cabecera.
            self.b_buscar_dispositivos.configure(state="disabled")

            # Protocolo.
            self.e_num_ciclos.b_decrementar.configure(state="disabled")
            self.e_num_ciclos.e_spinbox.configure(state="disabled")
            self.e_num_ciclos.b_incrementar.configure(state="disabled")
            self.e_intervalo_ciclos.b_decrementar.configure(state="disabled")
            self.e_intervalo_ciclos.e_spinbox.configure(state="disabled")
            self.e_intervalo_ciclos.b_incrementar.configure(state="disabled")
            self.e_tiempo_exposicion.b_decrementar.configure(state="disabled")
            self.e_tiempo_exposicion.e_spinbox.configure(state="disabled")
            self.e_tiempo_exposicion.b_incrementar.configure(state="disabled")
            self.e_tiempo_desensibilizacion.b_decrementar.configure(state="disabled")
            self.e_tiempo_desensibilizacion.e_spinbox.configure(state="disabled")
            self.e_tiempo_desensibilizacion.b_incrementar.configure(state="disabled")
            self.cb_aleatorio.configure(state="disabled")
            self.cb_secuencial.configure(state="disabled")
            self.b_iniciar_protocolo.configure(state="disabled")
            self.b__reiniciar_protocolo.configure(state="disabled")
            
            # Estado.
            self.e_id_sesion.configure(state="disabled")
            self.e_id_paciente.configure(state="disabled")
            self.b_generar_informe.configure(state="disabled")

            # Canales.
            for canal in self.cuadros_canales:
                if canal.e_olor_canal.winfo_exists():
                    canal.e_olor_canal.configure(state="disabled")
            self._actualizar_bloqueo_canales_manual()

            #caracterizacion.
            self.comb_canales_caracterizacion.configure(state="disabled")
            self.b_iniciar_caracterizacion_general.configure(state="disabled")
            self.b__reiniciar_caracterizacion_general.configure(state="disabled")
            self.b__parar_caracterizacion_general.configure(state="disabled")

            self.b_iniciar_caracterizacion_velocidad.configure(state="disabled")
            self.b_reiniciar_caracterizacion_velocidad.configure(state="disabled")
            self.b_parar_caracterizacion_velocidad.configure(state="disabled")
            self.b_iniciar_caracterizacion_flujo.configure(state="disabled")
            self.b_reiniciar_caracterizacion_flujo.configure(state="disabled")
            self.b_parar_caracterizacion_flujo.configure(state="disabled")
            self.b_iniciar_caracterizacion_concentracion.configure(state="disabled")
            self.b_reiniciar_caracterizacion_concentracion.configure(state="disabled")  
            self.b_parar_caracterizacion_concentracion.configure(state="disabled")
            self.b_iniciar_caracterizacion_latencia.configure(state="disabled")
            self.b_reiniciar_caracterizacion_latencia.configure(state="disabled")
            self.b_parar_caracterizacion_latencia.configure(state="disabled")


        else:

            # Cabecera.
            self.b_buscar_dispositivos.configure(state="normal")

            # Protocolo.
            self.e_num_ciclos.b_decrementar.configure(state="normal")
            self.e_num_ciclos.e_spinbox.configure(state="normal")
            self.e_num_ciclos.b_incrementar.configure(state="normal")
            self.e_intervalo_ciclos.b_decrementar.configure(state="normal")
            self.e_intervalo_ciclos.e_spinbox.configure(state="normal")
            self.e_intervalo_ciclos.b_incrementar.configure(state="normal")
            self.e_tiempo_exposicion.b_decrementar.configure(state="normal")
            self.e_tiempo_exposicion.e_spinbox.configure(state="normal")
            self.e_tiempo_exposicion.b_incrementar.configure(state="normal")
            self.e_tiempo_desensibilizacion.b_decrementar.configure(state="normal")
            self.e_tiempo_desensibilizacion.e_spinbox.configure(state="normal")
            self.e_tiempo_desensibilizacion.b_incrementar.configure(state="normal")
            self.cb_aleatorio.configure(state="normal")
            self.cb_secuencial.configure(state="normal")
            self.b_iniciar_protocolo.configure(state="normal")
            self.b__reiniciar_protocolo.configure(state="normal")
            
            # Estado.
            self.e_id_sesion.configure(state="normal")
            self.e_id_paciente.configure(state="normal")
            self.b_generar_informe.configure(state="normal")

            # Canales.
            for canal in self.cuadros_canales:
                if canal.e_olor_canal.winfo_exists():
                    canal.e_olor_canal.configure(state="normal")
            self._actualizar_bloqueo_canales_manual()

            # Caracterizacion.
            self.comb_canales_caracterizacion.configure(state="normal")
            self.b_iniciar_caracterizacion_general.configure(state="normal")
            self.b__reiniciar_caracterizacion_general.configure(state="normal")
            self.b__parar_caracterizacion_general.configure(state="normal")

            self.b_iniciar_caracterizacion_velocidad.configure(state="normal")
            self.b_reiniciar_caracterizacion_velocidad.configure(state="normal")
            self.b_parar_caracterizacion_velocidad.configure(state="normal")
            self.b_iniciar_caracterizacion_flujo.configure(state="normal")
            self.b_reiniciar_caracterizacion_flujo.configure(state="normal")
            self.b_parar_caracterizacion_flujo.configure(state="normal")
            self.b_iniciar_caracterizacion_concentracion.configure(state="normal")
            self.b_reiniciar_caracterizacion_concentracion.configure(state="normal")  
            self.b_parar_caracterizacion_concentracion.configure(state="normal")
            self.b_iniciar_caracterizacion_latencia.configure(state="normal")
            self.b_reiniciar_caracterizacion_latencia.configure(state="normal")
            self.b_parar_caracterizacion_latencia.configure(state="normal")


    def iniciar_protocolo(self):
        """
        Inicia o reanuda la ejecución del protocolo experimental configurado. 

        En funcion de si había un protocolo en curso con anterioridad iniciará o reanudará su ejecución. En caso de que no lo hubiera se comienza activando la bandera de
        estado activo correspondiente y se recogen aquellos canales que vayan a participar en el protocolo experimental (todos aquellos con odorante y el canal destinado a la
        desensibilización). Tras la comprobación de la correcta configuración introducida por el usuario, muestra un mensaje informativo por consola, deshabilita los elementos
        acccionables del software (menos el botón de pausa/para de emergencia) y llama al método siguiente para comenzar con la exposición de odorante.
        En cambio, si el protocolo ya había comenzado y se encuentra detenido, comprueba la fase en la que se encuentra, asigna el tiempo registrado en la parar como el
        tiempo de partida activando el correspondiente canal y continua el temporizador detenido. 
        
        Args: 
            Ninguno.
        Return:
            return: Todos aquellos return empleados se utilizan para salir del método y evitar el consumo de recursos innecesarios.
        Raises:
            Ninguno.

        """

        # Evaluación software.
        #self.t0_actualizacion_iniciar_protocolo = time.perf_counter()  # Marca el tiempo de inicio del protocolo para la actualización de la UI

        if self.protocolo_activo:
            # Reanudación de protocolo.
            if self.protocolo_pausado:
                self.protocolo_pausado = False
                self.consola.registro("Reanudando protocolo...")
                self.b_iniciar_protocolo.configure(state ="disabled")
                self.b__reiniciar_protocolo.configure(state = "disabled")

                if self.fase_actual == "Exposición":
                    canal = self.canales_protocolo[self.indice_canal_protocolo]
                    canal.activar_canal(tiempo_inicial = self.tiempo_guardado)
                    self.tiempo_guardado = None
                    self._periodo_exposicion(canal, self.segundos_restantes_protocolo)

                if self.fase_actual == "Desensibilización":
                    canal_desensibilizacion = self.cuadros_canales[config.CANAL_BLANCO]
                    canal_desensibilizacion.activar_canal(tiempo_inicial = self.tiempo_guardado)
                    self.tiempo_guardado = None
                    self._periodo_desensibilizacion(self.segundos_restantes_protocolo)

                if self.fase_actual == "Intervalo":
                    self.canal_activo = None
                    self.sv_canal_activo.set("Ninguno")
                    self.sv_canal_anterior.set("Ninguno")
                    self.sv_canal_siguiente.set("Ninguno")
                    self._periodo_intervalo(self.segundos_restantes_protocolo)

            else:
                self.consola.registro("Ya hay un protocolo activo", nivel="AVISO")

            return
        
        else:
            self.protocolo_activo= True
            canales_con_olor = []

        for canal in self.cuadros_canales:
            if canal.e_olor_canal.get() != "":
                canales_con_olor.append(canal)

        # Validación de configuración correcta.
        if not canales_con_olor:
            self.consola.registro("No hay ningún canal con olor introducido. Introduzca al menos un olor en uno de los canales para iniciar el protocolo", nivel="AVISO")
            self.protocolo_activo= False
            return
        
        self.consola.registro(f"{self.e_num_ciclos.get()}")
        if self.e_num_ciclos.get() <= 0 or self.e_num_ciclos.valor.get().strip() == "" :
            self.consola.registro("El número de ciclos no está definido o es negativo. Defina al menos un ciclo para iniciar el protocolo", nivel="AVISO")
            self.protocolo_activo= False
            return

        if self.e_tiempo_exposicion.get() <= 0 or self.e_tiempo_exposicion.valor.get().strip() == "" :
            self.consola.registro("El tiempo de exposición no está definido o es negativo. Introduzca la duración del periodo de exposición para iniciar el protocolo", nivel="AVISO")
            self.protocolo_activo= False
            return

        if self.e_tiempo_desensibilizacion.get() <= 0 or self.e_tiempo_desensibilizacion.valor.get().strip() == "" :
            self.consola.registro("El tiempo de desensibilización no está definido o es negativo. Introduzca la duración del periodo de desensibilización para iniciar el protocolo", nivel="AVISO")
            self.protocolo_activo= False
            return

        if self.cb_aleatorio.get() == 0 and self.cb_secuencial.get() == 0:
            self.consola.registro("No se ha seleccionado el orden de los canales. Seleccione un orden para iniciar el protocolo", nivel="AVISO")
            self.protocolo_activo= False
            return

        if self.cb_aleatorio.get() == 1 and self.cb_secuencial.get() == 1:
            self.consola.registro("No se pueden seleccionar ambos órdenes de canal a la vez. Seleccione un orden para iniciar el protocolo", nivel="AVISO")
            self.protocolo_activo= False
            return

        if self.e_intervalo_ciclos.get() < 0 or self.e_intervalo_ciclos.valor.get().strip() == "":
            self.consola.registro("El intervalo entre ciclos no está definido o es negativo. Introduzca la duración del intervalo entre ciclos para iniciar el protocolo", nivel="AVISO")
            self.protocolo_activo= False
            return

        else:
            self.ciclo_actual = 1
            self.indice_canal_protocolo = 0
            self.segundos_restantes_protocolo = 0
            self.tiempo_guardado = None
            self.fase_actual = None

            if self.cb_aleatorio.get() == 1:
                self.orden_protocolo = "aleatorio"
                self.canales_protocolo = random.sample(canales_con_olor, len(canales_con_olor))
                
            else:
                self.orden_protocolo = "secuencial"
                self.canales_protocolo = list(canales_con_olor)

        # Inicio de protocolo.
        self.consola.registro(f"Iniciando protocolo {self.orden_protocolo} en {len(self.canales_protocolo)} canales: { [olor.e_olor_canal.get() for olor in self.canales_protocolo] }")
        self._bloquear_botones(bloquear=True)
        self._iniciar_exposicion()

        # Evaluación software.
        #self.update_idletasks()
        #diferencia_temporal = time.perf_counter() - self.t0_actualizacion_iniciar_protocolo
        #self.tiempos_actualizacion ["iniciar_protocolo"].append(diferencia_temporal)
        #self.t0_actualizacion_iniciar_protocolo = 0
        #print(f"Tiempo de actualización de la UI al iniciar protocolo: {diferencia_temporal} segundos")


    def _iniciar_exposicion(self):
        """
        Inicia la exposición del paciente al odorante de un canal. 

        Actualiza la bandera de fase a la fase de exposición e informa por consola del estado actual del protocolo en ejecución. Tras ejecutar la activación del canal,
        almacena la función con el temporizador de la exposición como callback a la espera de confirmación de que la válvula haya alcanzado la posición correcta. O en caso
        de ya encontarse la válvula en la posición de destino comienza el temporizador de exposición.
        Por cada llamamiento a la función se comprueba si el ciclo del protocolo ha finalizado para comenzar con el periodo de descanso entre ciclos, de no ser así 
        continua con el siguiente canal con odorante.
        
        Args: 
            Ninguno.
        Return:
            return: Es empleado salir del método y evitar el consumo de recursos innecesarios.
        Raises:
            Ninguno.

        """

        if self.indice_canal_protocolo >= len(self.canales_protocolo):
            self._iniciar_intervalo()
            return
        
        canal = self.canales_protocolo[self.indice_canal_protocolo]
        
        self.fase_actual = "Exposición"
        self.consola.registro(f"Ciclo {self.ciclo_actual}/{self.e_num_ciclos.get()} Iniciando exposición en canal {canal.e_olor_canal.get()} durante {self.e_tiempo_exposicion.get()} segundos")
        canal.activar_canal()

        if canal.num_canal == self.canal_esperando_posicion:
            self.callbacks_pendientes_posicion_valvula.append((canal.num_canal, self._periodo_exposicion, (canal, int(self.e_tiempo_exposicion.get()))))

        else:
            self._periodo_exposicion(canal, int(self.e_tiempo_exposicion.get()))


    def _periodo_exposicion(self, canal, segundos_restantes):
        """
        Temporizador del periodo de exposición a un odorante. 

        Si el temporizador no ha llegado a 0, autoreagenda su llamada actualizando tiempo restante tras un segundo.
        Si transcurre finalmente el tiempo marcado por el protocolo, el canal se detiene y comienza la fase de desensibilización.
        En caso de que el protocolo haya sido pausado se limita a almacenar los segundos restantes de exposición al odorante, saliendo de forma seguida del mismo.
        
        Args: 
            - canal (Canal): Canal con el odorante a exponer.
            - segundos_restantes (int): Tiempo restante de exposición.
        Return:
            return: Es empleado salir del método y evitar el consumo de recursos innecesarios.
        Raises:
            Ninguno.

        """

        if self.protocolo_pausado:
            self.segundos_restantes_protocolo = segundos_restantes
            return
        
        if segundos_restantes > 0:
            self.segundos_restantes_protocolo = segundos_restantes
            self.after_activo = self.after(1000, lambda: self._periodo_exposicion(canal, segundos_restantes - 1))

        else:
            canal.parar_canal()
            self._iniciar_desensibilizacion()

    
    def _iniciar_desensibilizacion(self):
        """
        Inicia la desensibilización de odorante y limpieza del canal. 

        Se actualiza la bandera de estado de fase a fase de desensibilización e informa por consola al usuario del inicio del periodo de desensibilización. Se activa el
        correspondiente canal destinado a la desensibilización, comprobando la posición de la válvula y añadiendo la función con el temporizador de desensibilización
        como callback o llamándola directamente.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.fase_actual = "Desensibilización"
        self.consola.registro(f"Ciclo {self.ciclo_actual}/{self.e_num_ciclos.get()} Iniciando desensibilización durante {self.e_tiempo_desensibilizacion.get()} segundos")
    
        canal_desensibilizacion = self.cuadros_canales[config.CANAL_BLANCO]
        canal_desensibilizacion.activar_canal()

        if canal_desensibilizacion.num_canal == self.canal_esperando_posicion:
            self.callbacks_pendientes_posicion_valvula.append((canal_desensibilizacion.num_canal, self._periodo_desensibilizacion, (int(self.e_tiempo_desensibilizacion.get()),)))

        else:
            self._periodo_desensibilizacion(int(self.e_tiempo_desensibilizacion.get()))


    def _periodo_desensibilizacion(self, segundos_restantes):
        """
        Temporizador del periodo de desensibilización a un odorante y limpieza de canales. 

        Si el temporizador no ha llegado a 0, autoreagenda su llamada actualizando tiempo restante tras un segundo.
        Si transcurre finalmente el tiempo marcado por el protocolo, el canal se detiene y comienza la fase de exposición con el siguiente canal con odorante.
        En caso de que el protocolo haya sido pausado se limita a almacenar los segundos restantes de desensibilización, saliendo de forma seguida del mismo.
        
        Args: 
            - segundos_restantes (int): Tiempo restante de desensibilización.
        Return:
            return: Es empleado salir del método y evitar el consumo de recursos innecesarios.
        Raises:
            Ninguno.

        """

        if self.protocolo_pausado:
            self.segundos_restantes_protocolo = segundos_restantes
            return
        
        if segundos_restantes > 0:
            self.segundos_restantes_protocolo = segundos_restantes
            self.after_activo = self.after(1000, lambda: self._periodo_desensibilizacion(segundos_restantes - 1))

        else:
            self.cuadros_canales[config.CANAL_BLANCO].parar_canal()
            self.indice_canal_protocolo += 1
            self._iniciar_exposicion()


    def _iniciar_intervalo(self):
        """
        Inicia la fase de intervalo entre ciclos del protocolo. 

        Cambia la bandera de fase a la fase de intervalo, reasigna a valores iniciales las diferentes variables globales para el comienzo del nuevo ciclo y comienza
        el temporizador de espera entre ciclos. Adicionalemtne actualiza el número de ciclo actual del protocolo ejecutado, en caso de ser mayor al definido, lo finaliza.
        
        Args: 
            Ninguno.
        Return:
            return: Es empleado salir del método y evitar el consumo de recursos innecesarios.
        Raises:
            Ninguno.

        """

        self.ciclo_actual += 1
        if self.ciclo_actual > int(self.e_num_ciclos.get()):
            self._finalizar_protocolo()
            return
        
        self.fase_actual = "Intervalo"
        self.indice_canal_protocolo = 0
        self.sv_canal_activo.set("Ninguno")
        self.sv_canal_anterior.set("Ninguno")
        self.sv_canal_siguiente.set("Ninguno")
        self.canal_activo = None
        self.consola.registro(f"Pausa entre ciclos durante: {self.e_intervalo_ciclos.get()} segundos. Ciclo siguiente: {self.ciclo_actual}/{self.e_num_ciclos.get()}")
        self._periodo_intervalo(int(self.e_intervalo_ciclos.get()))


    def _periodo_intervalo(self, segundos_restantes):
        """
        Temporizador del periodo de intervalo entre ciclos del mismo protocolo. 

        Si el temporizador no ha llegado a 0, autoreagenda su llamada actualizando tiempo restante tras un segundo.
        Si transcurre finalmente el tiempo marcado por el protocolo, se inicia la fase de exposición con el primer canal con odorante.
        En caso de que el protocolo haya sido pausado se limita a almacenar los segundos restantes de espera entre ciclos, saliendo de forma seguida del mismo.
        
        Args: 
            Ninguno.
        Return:
            return: Es empleado salir del método y evitar el consumo de recursos innecesarios.
        Raises:
            Ninguno.

        """

        if self.protocolo_pausado:
            self.segundos_restantes_protocolo = segundos_restantes
            return
        if segundos_restantes > 0:
            self.segundos_restantes_protocolo = segundos_restantes
            self.after_activo = self.after(1000, lambda: self._periodo_intervalo(segundos_restantes - 1))

        else:
            self._iniciar_exposicion()


    def _finalizar_protocolo(self):
        """
        Finaliza correctamente el protocolo ejecutado. 

        Se calcula el movimiento necesario para posicionar la válvula en el canal asociado de reposo asociado a la limpieza y desensibilización.
        Tras ello, se actualizan todas las variables globales y banderas de estado a su estado inicial, rehabilitando los botones y widgets accionales del software.
        El usuario es informado por consola de la finalización del protocolo ejecutado.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        pasos_home = self.posiciones_canales[config.CANAL_BLANCO]-self.posicion_valvula
        self.ws_client.enviar({"cmd": "rotar", "canal": config.CANAL_BLANCO, "pasos": pasos_home})
        self.posicion_valvula = config.POSICIONES_CANALES[config.CANAL_BLANCO]
        self.protocolo_activo = False
        self.protocolo_pausado = False
        self.fase_actual = None
        self._bloquear_botones(bloquear=False)
        self.consola.registro("Protocolo finalizado")


    def _consulta__reiniciar_protocolo(self):
        """
        Consulta al usuario el reinicio del protocolo. 

        A partir de la respuesta obtenida de la ventana emergente generada con la consulta de reinicio del protocolo, se procede a aceptar o cancelar el reinicio del mismo.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """
        respuesta = messagebox.askyesno("Reiniciar protocolo", "¿Está seguro de que desea reiniciar el protocolo? Se perderá el progreso de la actual sesion experimental.")

        if respuesta:
            self._reiniciar_protocolo()
            self.consola.registro("Reiniciando protocolo...")

        else:
            self.consola.registro("Reinicio de protocolo cancelado")

    
    def _reiniciar_protocolo(self):
        """
        Reinicia el protocolo ya iniciado. 

        Primeramente cancela las funciones callbacks pendientes relativas a la temporización del periodo exposición y desensibilización, sea cual fuere 
        ejecución programada activa además de las posibles activaciones pendientes de canales. Reinicia con ello el cronómetro asociado de cada canal. junto 
        con el resto de banderas de estado y variables globales a sus valores por defecto. Por último mueve la válvula a la posición del canal de reposo e 
        informa al usuario con un mensaje por consola desbloqueando los elementos accionables.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        # Evaluación software.
        #self.t0_actualizacion__reiniciar_protocolo = time.perf_counter()  # Marca el tiempo de inicio del reinicio del protocolo para la actualización de la UI

        self._cancelar_espera_posicion_valvula(self._periodo_exposicion)
        self._cancelar_espera_posicion_valvula(self._periodo_desensibilizacion)

        for canal in self.cuadros_canales:
            self._cancelar_activacion_pendiente(canal)

        for canal in self.canales_protocolo:
            canal.resetear__cronometro()

        if self.after_activo:
            self.after_cancel(self.after_activo)
            self.after_activo = None

        self.protocolo_activo = False
        self.protocolo_pausado = False
        pasos_home = self.posiciones_canales[config.CANAL_BLANCO]-self.posicion_valvula
        self.ws_client.enviar({"cmd": "rotar", "canal": config.CANAL_BLANCO, "pasos": pasos_home})
        self.posicion_valvula = config.POSICIONES_CANALES[config.CANAL_BLANCO]
        self.canal_activo = None
        self.fase_actual = None
        self.segundos_restantes_protocolo = 0
        self.tiempo_guardado = None
        self.indice_canal_protocolo = None
        self.ciclo_actual = 1
        self.canales_protocolo = []
        self._bloquear_botones(bloquear=False)
        self.sv_canal_activo.set("Ninguno")
        self.sv_canal_anterior.set("Ninguno")
        self.sv_canal_siguiente.set("Ninguno")
        self.consola.registro("Protocolo reiniciado")

        # Evaluación software.
        #self.update_idletasks()
        #diferencia_temporal = time.perf_counter() - self.t0_actualizacion__reiniciar_protocolo
        #self.tiempos_actualizacion ["_reiniciar_protocolo"].append(diferencia_temporal)
        #self.t0_actualizacion__reiniciar_protocolo = 0
        #print(f"Tiempo de actualización de la UI al reiniciar protocolo: {diferencia_temporal} segundos")
        

    def _consulta__parar_protocolo(self):
        """
        Consulta al usuario la parada del protocolo. 

        A partir de la respuesta obtenida de la ventana emergente generada con la consulta de pausa/parada del protocolo, se procede a aceptar o cancelar la 
        parada del mismo.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        respuesta = messagebox.askyesno("Parar protocolo", "¿Está seguro de que desea parar el protocolo? Se pausará el actual progreso de la sesión experimental y podrá reanudarlo posteriormente.")

        if respuesta:
            self.consola.registro("Parando protocolo...")
            self._parar_protocolo()

        else:
            self.consola.registro("Parada de protocolo cancelada")


    def _parar_protocolo(self):
        """
        Detiene el protocolo en curso. 

        Comienza actualizando la bandera de estado asociada a la pausa del protocolo y cancelando las funciones de temporizadores pendientes de ser ejecutadas, además de
        las activaciones que estuvieran pendientes. Se desbloquean aquellos botones de acción de control general del protocolo y guarda el tiempo activo correspondiente
        de los procesos exposición y desensibilización en el momento de la parada.
        Finaliza informando de la parada al usuario por consola.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.protocolo_pausado = True

        self._cancelar_espera_posicion_valvula(self._periodo_exposicion)
        self._cancelar_espera_posicion_valvula(self._periodo_desensibilizacion)

        self.b_iniciar_protocolo.configure(state="normal")
        self.b__reiniciar_protocolo.configure(state="normal")

        if self.fase_actual == "Exposición" or self.fase_actual == "Desensibilización":
            self.tiempo_guardado = datetime.datetime.strptime(self.canal_activo.sv_tiempo_activo.get().split()[2], config.FORMATO_HORA)
        
        for canal in self.cuadros_canales:
            self._cancelar_activacion_pendiente(canal)

            # Evaluación software.
            #diferencia_temporal = canal.parar_canal()
            #self.tiempos_actualizacion["parar_canal"].append(diferencia_temporal)
        
        self.consola.registro("Protocolo parado")

        if self.after_activo:
            self.after_cancel(self.after_activo)
            self.after_activo = None

        # Evaluación software.
        #self.update_idletasks()
        #diferencia_temporal = time.perf_counter() - self.t0_actualizacion__reiniciar_protocolo
        #self.tiempos_actualizacion ["_reiniciar_protocolo"].append(diferencia_temporal)
        #self.t0_actualizacion__reiniciar_protocolo = 0
        #print(f"Tiempo de actualización de la UI al reiniciar protocolo: {diferencia_temporal} segundos")

    
    def iniciar_caracterizacion_velocidad(self):
        """
        Inicia o reanuda la caracterización del parámetro de velocidad. 

        A partir de la selección del canal a caracterizar, deshabilita la totalidad de los elementos accionables del software a excepción de la parada.
        Actualiza las variables globales y banderas de esto implicadas en el registro de la caracterización y que posteriormente se emplearán para su representación 
        en tiempo real. Agrega el tiempo de inicio, la duración y el olor del canal a caracterizar, prosiguiendo con su activación y, en caso de que no estuviera
        situada la válvula deja en espera el inicio del temporizador.
        En caso de reanudar una caracterizaicón ya comenzada, actualiza la bandera de estado de parada y vuelve a activar el canal con el tiempo restante almacenado.
        
        Args: 
            Ninguno.
        Return:
            - return: Es empleado para salir del método ante la introducción de valores de tiempo de caracterización incompatible. 
        Raises:
            Ninguno.

        """

        if self.canal_caracterizacion is not None:
            self._actualizar_bloqueo_canales_manual()

            if not self.caracterizacion_velocidad_parado and not self.caracterizando_velocidad:
                if int(self.e_tiempo_caracterizacion.get()) > 0 and self.e_tiempo_caracterizacion.valor.get().strip()!= "":
                    self.caracterizando_velocidad = True
                    self.consola.registro("Iniciando caracterizacion de velocidad...")
                    tiempo_caracterizacion_segundos=int(self.e_tiempo_caracterizacion.get())*config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION
                    self.tiempo_grafica_velocidad = collections.deque((i * (1/config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION) for i in range(tiempo_caracterizacion_segundos)), maxlen=tiempo_caracterizacion_segundos)
                    self.buffer_grafica_velocidad = collections.deque([np.nan]*len(self.tiempo_grafica_velocidad), maxlen=len(self.tiempo_grafica_velocidad))
                    self.contador_velocidad = 0
                    self.buffer_caracterizacion_velocidad.clear()
                    self.b_iniciar_caracterizacion_velocidad.configure(state="disabled")
                    self.b_reiniciar_caracterizacion_velocidad.configure(state="disabled")
                    num_canal = self.canal_caracterizacion.num_canal

                    if num_canal not in self.historial_caracterizacion:
                        self.historial_caracterizacion[num_canal] = {}

                    self.historial_caracterizacion[num_canal].setdefault("tiempo_inicio", time.time())
                    self.historial_caracterizacion[num_canal].setdefault("duracion", self.e_tiempo_caracterizacion.get())
                    self.historial_caracterizacion[num_canal].setdefault("olor", self.canal_caracterizacion.e_olor_canal.get() if self.canal_caracterizacion.e_olor_canal.winfo_exists() else "----")

                    if not self.caracterizando_flujo and not self.caracterizando_concentracion and not self.caracterizando_latencia:
                        self.canal_caracterizacion.activar_canal()

                    if num_canal == self.canal_esperando_posicion:
                        self.callbacks_pendientes_posicion_valvula.append((num_canal, self._periodo_caracterizacion_velocidad, (self.canal_caracterizacion, self.e_tiempo_caracterizacion.get())))

                    else:
                        self._periodo_caracterizacion_velocidad(self.canal_caracterizacion, self.e_tiempo_caracterizacion.get())
                else:
                    self.consola.registro("El tiempo de caracterización no puede ser negativo, igual a 0 o estar vacío")
                    return

            else:
                self.caracterizacion_velocidad_parado = False
                self.consola.registro("Reanudando caracterizacion de velocidad...")
                self.consola.registro(f"Tiempo guardado: {self.segundos_restantes_velocidad}")        
                self.canal_caracterizacion.activar_canal()
                self._periodo_caracterizacion_velocidad(self.canal_caracterizacion, self.segundos_restantes_velocidad)
                
        else:
            self.consola.registro("No hay ningún canal seleccionado para caracterizar. Seleccione un canal para iniciar el caracterizacion de velocidad", nivel="AVISO")
            

    def _periodo_caracterizacion_velocidad(self, canal_caracterizacion, segundos_restantes):
        """
        Temporizador del periodo de caracterización de la velocidad. 

        Si el temporizador no ha llegado a 0, autoreagenda su llamada actualizando tiempo restante tras un segundo. Por cada iteración se almacena el valor en la variable 
        global para tener una referencia globalmente conocida. Si transcurre finalmente el tiempo marcado por el protocolo, el canal caracterizado se detiene y 
        comienza la parada de la caracterización de la velocidad.
        
        
        Args: 
            - canal_caracterizacion (Canal): Canal seleccionado a caracterizar.
            - segundos_restantes (int): Tiempo restante de caracterización.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.segundos_restantes_velocidad = segundos_restantes

        if segundos_restantes > 0:
            self.consola.registro(f"caracterizacion de velocidad en curso... Tiempo restante: {self.segundos_restantes_velocidad}s")
            self.after_caracterizacion_velocidad = self.after(1000, lambda: self._periodo_caracterizacion_velocidad(canal_caracterizacion, segundos_restantes - 1))

        else:
            
            if canal_caracterizacion is not None:
                canal_caracterizacion.parar_canal()

            else:
                self.consola.registro("No hay ningún canal seleccionado para caracterizar.", nivel="AVISO")

            self.parar_caracterizacion_velocidad()


    def reiniciar_caracterizacion_velocidad(self):
        """
        Reinicia la caracterización de velocidad ya iniciada. 

        Cancela las funciones de activación del canal caracterizado y temporizador del parámetro velocidad, además de las funciones de activación pendiente.
        En caso de que la varible global tenga un canal caracterizando asociado se procede a la detención del mismo. Adicionalmente se reinician visual y lógicamnete
        la gráfica de velocidad representada en tiempo real. Finalmente de informa por consola al usuario del reinicio y se reahabilitan los componentes previamente
        bloqueados.
        
        Args: 
            Ninguno.
        Return:
            - return: Es empleado para salir del método ante la introducción de valores de tiempo de caracterización incompatible.
        Raises:
            Ninguno.

        """

        self._cancelar_espera_posicion_valvula(self._periodo_caracterizacion_velocidad)

        if self.canal_caracterizacion is not None:
            self._cancelar_activacion_pendiente(self.canal_caracterizacion)

        self.caracterizando_velocidad = False
        self.caracterizacion_velocidad_parado = False
        self.segundos_restantes_velocidad = 0
        self.contador_velocidad = 0
        self.tiempo_guardado = None

        if self.after_caracterizacion_velocidad:
            self.after_cancel(self.after_caracterizacion_velocidad)
            self.after_caracterizacion_velocidad = None

        if self.canal_caracterizacion is not None:
            self.canal_caracterizacion.parar_canal()

        else:
            self.consola.registro("No hay ningún canal seleccionado para caracterizar. Seleccione un canal para iniciar el caracterizacion de velocidad.", nivel="AVISO")

        self.buffer_caracterizacion_velocidad.clear()

        if int(self.e_tiempo_caracterizacion.get()) <= 0 or self.e_tiempo_caracterizacion.valor.get().strip() == "":
            self.consola.registro("El tiempo de caracterización no puede ser negativo, igual a 0 o estar vacío")
            return
        
        tiempo_caracterizacion_segundos=int(self.e_tiempo_caracterizacion.get())*config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION
        self.tiempo_grafica_velocidad = collections.deque((i * (1/config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION) for i in range(tiempo_caracterizacion_segundos)), maxlen=tiempo_caracterizacion_segundos)
        self.buffer_grafica_velocidad = collections.deque([np.nan]*len(self.tiempo_grafica_velocidad), maxlen=len(self.tiempo_grafica_velocidad))

        self.ax_velocidad.clear()
        self.ax_velocidad.set_xlabel("Tiempo (s)")
        self.ax_velocidad.set_ylabel("Velocidad (m/s)")
        self.ax_velocidad.set_xlim(0,int(self.e_tiempo_caracterizacion.get()))
        self.ax_velocidad.set_ylim(config.LIMITESY["velocidad"][0],config.LIMITESY["velocidad"][1]) 
        self.ax_velocidad.tick_params(colors = "#ffffff") 
        self.ax_velocidad.xaxis.label.set_color("#ffffff") 
        self.ax_velocidad.yaxis.label.set_color("#ffffff")  
        self.ax_velocidad.spines['bottom'].set_color('#ffffff') 
        self.ax_velocidad.spines['left'].set_color('#ffffff')  
        self.ax_velocidad.spines['top'].set_color('#ffffff') 
        self.ax_velocidad.spines['right'].set_color('#ffffff')  
        self.canvas_velocidad.draw()

        self.b_iniciar_caracterizacion_velocidad.configure(state="normal")
        self._actualizar_bloqueo_canales_manual()
        self.consola.registro("Caracterizacion de velocidad reiniciado")

    
    def parar_caracterizacion_velocidad(self):
        """
        Detiene o finaliza la caracterización del parámetro velocidad en curso. 

        Comienza cancelando aquellas ejecuciones pendientes relativas al temporizador asociado al parámetro de velocidad y activación del canal caracterizado (si estuviera
        en proceso). Posteriormente detiene el canal caracterizado y rehabilita los botones de iniciar/reiniciar_caracterizacion_velocidad. Informa por último de los 
        segundos restantes por caracterizar el parámetro de velocidad del canal seleccionado.
        En caso de haber finalizado el tiempo de caracterización del parámetro de velocidad, se almacenan los datos contenidos en los buffer temporales de velocidad
        para la posterior generación de la sección historial de caracterización y subsección de resultados caracterización del informe de la sesión experimental.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        if self.caracterizando_velocidad:
            self._cancelar_espera_posicion_valvula(self._periodo_caracterizacion_velocidad)
            self.caracterizacion_velocidad_parado = True
            
            if self.after_caracterizacion_velocidad:
                self.after_cancel(self.after_caracterizacion_velocidad)
                self.after_caracterizacion_velocidad = None

            if self.canal_caracterizacion is not None:
        
                if not self.caracterizacion_flujo_parado and not self.caracterizacion_concentracion_parado and not self.caracterizacion_latencia_parado:
                    self._cancelar_activacion_pendiente(self.canal_caracterizacion)
                    self.canal_caracterizacion.parar_canal()
            else:
                self.consola.registro("No hay ningún canal seleccionado para caracterizar. Seleccione un canal para iniciar el caracterizacion de velocidad.", nivel="AVISO")

            self.b_iniciar_caracterizacion_velocidad.configure(state="normal")
            self.b_reiniciar_caracterizacion_velocidad.configure(state="normal")

            if self.segundos_restantes_velocidad > 0:
                self.consola.registro(f"Caracterizacion de velocidad parado con {self.segundos_restantes_velocidad} segundos restantes")

            else:

                if self.canal_caracterizacion is not None:
                    num_canal = self.canal_caracterizacion.num_canal

                    if num_canal not in self.historial_caracterizacion:
                        self.historial_caracterizacion[num_canal] = {}
                        self.historial_caracterizacion[num_canal]["olor"] = self.canal_caracterizacion.e_olor_canal.get() or self.canal_caracterizacion.color_canal

                    self.historial_caracterizacion[num_canal]["velocidad"] = list(self.buffer_caracterizacion_velocidad)
                    self.caracterizando_velocidad = False
                    self.caracterizacion_velocidad_parado = False
                    self.consola.registro("Caracterizacion de velocidad finalizado")

                else:
                    self.consola.registro("No se pudieron guardar las métricas de caracterizacion: No hay ningún canal seleccionado para caracterizar.", nivel="AVISO")

            self._actualizar_bloqueo_canales_manual()

        else:
            self.consola.registro("No hay ningún caracterizacion de velocidad activo. Seleccione un canal y pulse iniciar para comenzar el caracterizacion de velocidad.", nivel="AVISO")


    
    def iniciar_caracterizacion_flujo(self):
        """
        Inicia o reanuda la caracterización del parámetro de flujo. 

        A partir de la selección del canal a caracterizar, deshabilita la totalidad de los elementos accionables del software a excepción de la parada.
        Actualiza las variables globales y banderas de esto implicadas en el registro de la caracterización y que posteriormente se emplearán para su representación 
        en tiempo real. Agrega el tiempo de inicio, la duración y el olor del canal a caracterizar, prosiguiendo con su activación y, en caso de que no estuviera
        situada la válvula deja en espera el inicio del temporizador.
        En caso de reanudar una caracterizaicón ya comenzada, actualiza la bandera de estado de parada y vuelve a activar el canal con el tiempo restante almacenado.
        
        Args: 
            Ninguno.
        Return:
            - return: Es empleado para salir del método ante la introducción de valores de tiempo de caracterización incompatible.
        Raises:
            Ninguno.

        """

        if self.canal_caracterizacion is not None:
            self._actualizar_bloqueo_canales_manual()

            if not self.caracterizacion_flujo_parado and not self.caracterizando_flujo:

                if int(self.e_tiempo_caracterizacion.get()) > 0 and self.e_tiempo_caracterizacion.valor.get().strip() != "":
                    self.caracterizando_flujo = True
                    self.consola.registro("Iniciando caracterizacion de flujo...")
                    tiempo_caracterizacion_segundos=int(self.e_tiempo_caracterizacion.get())*config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION
                    self.tiempo_grafica_flujo = collections.deque((i * (1/config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION) for i in range(tiempo_caracterizacion_segundos)), maxlen=tiempo_caracterizacion_segundos)
                    self.buffer_grafica_flujo = collections.deque([np.nan]*len(self.tiempo_grafica_flujo), maxlen=len(self.tiempo_grafica_flujo))
                    self.contador_flujo = 0
                    self.buffer_caracterizacion_flujo.clear()
                    self.b_iniciar_caracterizacion_flujo.configure(state="disabled")
                    self.b_reiniciar_caracterizacion_flujo.configure(state="disabled")
                    num_canal = self.canal_caracterizacion.num_canal

                    if num_canal not in self.historial_caracterizacion:
                        self.historial_caracterizacion[num_canal] = {}

                    self.historial_caracterizacion[num_canal].setdefault("tiempo_inicio", time.time())
                    self.historial_caracterizacion[num_canal].setdefault("duracion", self.e_tiempo_caracterizacion.get())
                    self.historial_caracterizacion[num_canal].setdefault("olor", self.canal_caracterizacion.e_olor_canal.get() if self.canal_caracterizacion.e_olor_canal.winfo_exists() else self.canal_caracterizacion.color_canal)

                    if not self.caracterizando_velocidad and not self.caracterizando_concentracion and not self.caracterizando_latencia:
                        self.canal_caracterizacion.activar_canal()

                    if num_canal == self.canal_esperando_posicion:
                        self.callbacks_pendientes_posicion_valvula.append((num_canal, self._periodo_caracterizacion_flujo, (self.canal_caracterizacion, self.e_tiempo_caracterizacion.get())))

                    else:
                        self._periodo_caracterizacion_flujo(self.canal_caracterizacion, self.e_tiempo_caracterizacion.get())

                else:
                    self.consola.registro("El tiempo de caracterización no puede ser negativo, igual a 0 o estar vacío")
                    return
                
            else:
                self.caracterizacion_flujo_parado = False
                self.consola.registro("Reanudando caracterizacion de flujo...")
                self.consola.registro(f"Tiempo guardado: {self.segundos_restantes_flujo}")
                self.canal_caracterizacion.activar_canal()
                self._periodo_caracterizacion_flujo(self.canal_caracterizacion, self.segundos_restantes_flujo)
                
        else:
            self.consola.registro("No hay ningún canal seleccionado para caracterizar. Seleccione un canal para iniciar el caracterizacion de flujo", nivel="AVISO")
            
        
    def _periodo_caracterizacion_flujo(self, canal_caracterizacion, segundos_restantes):
        """
        Temporizador del periodo de caracterización de flujo. 

        Si el temporizador no ha llegado a 0, autoreagenda su llamada actualizando tiempo restante tras un segundo. Por cada iteración se almacena el valor en la variable 
        global para tener una referencia globalmente conocida. Si transcurre finalmente el tiempo marcado por el protocolo, el canal caracterizado se detiene y 
        comienza la parada de la caracterización de flujo.
        
        
        Args: 
            - canal_caracterizacion (Canal): Canal seleccionado a caracterizar.
            - segundos_restantes (int): Tiempo restante de caracterización.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.segundos_restantes_flujo = segundos_restantes

        if segundos_restantes > 0:
            self.consola.registro(f"caracterizacion de flujo en curso... Tiempo restante: {self.segundos_restantes_flujo}s")
            self.after_caracterizacion_flujo = self.after(1000, lambda: self._periodo_caracterizacion_flujo(canal_caracterizacion, segundos_restantes - 1))

        else:

            if canal_caracterizacion is not None:
                canal_caracterizacion.parar_canal()

            else:
                self.consola.registro("No hay ningún canal seleccionado para caracterizar. Seleccione un canal para iniciar el caracterizacion de flujo.", nivel="AVISO")

            self.parar_caracterizacion_flujo()


    def reiniciar_caracterizacion_flujo(self):
        """
        Reinicia la caracterización de flujo ya iniciada. 

        Cancela las funciones de activación del canal caracterizado y temporizador del parámetro flujo, además de las funciones de activación pendiente.
        En caso de que la varible global tenga un canal caracterizando asociado se procede a la detención del mismo. Adicionalmente se reinician visual y lógicamnete
        la gráfica de flujo representada en tiempo real. Finalmente de informa por consola al usuario del reinicio y se reahabilitan los componentes previamente
        bloqueados.
        
        Args: 
            Ninguno.
        Return:
            - return: Es empleado para salir del método ante la introducción de valores de tiempo de caracterización incompatible.
        Raises:
            Ninguno.

        """

        self._cancelar_espera_posicion_valvula(self._periodo_caracterizacion_flujo)

        if self.canal_caracterizacion is not None:
            self._cancelar_activacion_pendiente(self.canal_caracterizacion)

        self.caracterizando_flujo = False
        self.caracterizacion_flujo_parado = False
        self.segundos_restantes_flujo = 0
        self.contador_flujo = 0
        self.tiempo_guardado = None

        if self.after_caracterizacion_flujo:
            self.after_cancel(self.after_caracterizacion_flujo)
            self.after_caracterizacion_flujo = None

        if self.canal_caracterizacion is not None:
            self.canal_caracterizacion.parar_canal()

        else:
            self.consola.registro("No hay ningún canal seleccionado para caracterizar. Seleccione un canal para iniciar el caracterizacion de flujo.", nivel="AVISO")

        self.buffer_caracterizacion_flujo.clear()

        if int(self.e_tiempo_caracterizacion.get()) <= 0 or self.e_tiempo_caracterizacion.valor.get().strip() == "":
            self.consola.registro("El tiempo de caracterización no puede ser negativo, igual a 0 o estar vacío")
            return

        tiempo_caracterizacion_segundos=int(self.e_tiempo_caracterizacion.get())*config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION
        self.tiempo_grafica_flujo = collections.deque((i * (1/config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION) for i in range(tiempo_caracterizacion_segundos)), maxlen=tiempo_caracterizacion_segundos)
        self.buffer_grafica_flujo = collections.deque([np.nan]*len(self.tiempo_grafica_flujo), maxlen=len(self.tiempo_grafica_flujo))

        self.ax_flujo.clear()
        self.ax_flujo.set_xlim(0,int(self.e_tiempo_caracterizacion.get()))
        self.ax_flujo.set_ylim(config.LIMITESY["flujo"][0],config.LIMITESY["flujo"][1])  
        self.ax_flujo.set_xlabel("Tiempo (s)")
        self.ax_flujo.set_ylabel("Flujo (ml/min)")
        self.ax_flujo.tick_params(colors = "#ffffff") 
        self.ax_flujo.xaxis.label.set_color("#ffffff") 
        self.ax_flujo.yaxis.label.set_color("#ffffff") 
        self.ax_flujo.spines['bottom'].set_color('#ffffff')  
        self.ax_flujo.spines['left'].set_color('#ffffff')  
        self.ax_flujo.spines['top'].set_color('#ffffff')  
        self.ax_flujo.spines['right'].set_color('#ffffff')  
        self.canvas_flujo.draw()

        self.b_iniciar_caracterizacion_flujo.configure(state="normal")
        self._actualizar_bloqueo_canales_manual()
        self.consola.registro("caracterizacion de flujo reiniciado")

    
    def parar_caracterizacion_flujo(self):
        """
        Detiene o finaliza la caracterización del parámetro flujo en curso. 

        Comienza cancelando aquellas ejecuciones pendientes relativas al temporizador asociado al parámetro de flujo y activación del canal caracterizado (si estuviera
        en proceso). Posteriormente detiene el canal caracterizado y rehabilita los botones de iniciar/reiniciar_caracterizacion_flujo. Informa por último de los 
        segundos restantes por caracterizar el parámetro de flujo del canal seleccionado.
        En caso de haber finalizado el tiempo de caracterización del parámetro de flujo, se almacenan los datos contenidos en los buffer temporales de flujo
        para la posterior generación de la sección historial de caracterización y subsección de resultados caracterización del informe de la sesión experimental.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        if self.caracterizando_flujo:
            self._cancelar_espera_posicion_valvula(self._periodo_caracterizacion_flujo)
            self.caracterizacion_flujo_parado = True

            if self.after_caracterizacion_flujo:
                self.after_cancel(self.after_caracterizacion_flujo)
                self.after_caracterizacion_flujo = None

            if self.canal_caracterizacion is not None:

                if not self.caracterizacion_velocidad_parado and not self.caracterizacion_concentracion_parado and not self.caracterizacion_latencia_parado:
                    self._cancelar_activacion_pendiente(self.canal_caracterizacion)
                    self.canal_caracterizacion.parar_canal()

            else:
                self.consola.registro("No hay ningún canal seleccionado para caracterizar. Seleccione un canal para iniciar el caracterizacion de flujo.", nivel="AVISO")

            self.b_iniciar_caracterizacion_flujo.configure(state="normal")
            self.b_reiniciar_caracterizacion_flujo.configure(state="normal")

            if self.segundos_restantes_flujo > 0:
                self.consola.registro(f"caracterizacion de flujo parado con {self.segundos_restantes_flujo} segundos restantes")
        
            else:

                if self.canal_caracterizacion is not None:
                    num_canal = self.canal_caracterizacion.num_canal

                    if num_canal not in self.historial_caracterizacion:
                        self.historial_caracterizacion[num_canal] = {}
                        self.historial_caracterizacion[num_canal]["olor"] = self.canal_caracterizacion.e_olor_canal.get() or self.canal_caracterizacion.color_canal

                    self.historial_caracterizacion[num_canal]["flujo"] = list(self.buffer_caracterizacion_flujo)
                    self.caracterizando_flujo = False
                    self.caracterizacion_flujo_parado = False
                    self.consola.registro("caracterizacion de flujo finalizado")

                else:
                    self.consola.registro("No se pudieron guardar las métricas de caracterizacion: No hay ningún canal seleccionado para caracterizar.", nivel="AVISO")

            self._actualizar_bloqueo_canales_manual()

        else:
            self.consola.registro("No hay ningún caracterizacion activo. Seleccione un canal y pulse iniciar para comenzar el caracterizacion de flujo.", nivel="AVISO")

    def iniciar_caracterizacion_concentracion(self):
        """
        Inicia o reanuda la caracterización del parámetro de concentración. 

        A partir de la selección del canal a caracterizar, deshabilita la totalidad de los elementos accionables del software a excepción de la parada.
        Actualiza las variables globales y banderas de esto implicadas en el registro de la caracterización y que posteriormente se emplearán para su representación 
        en tiempo real. Agrega el tiempo de inicio, la duración y el olor del canal a caracterizar, prosiguiendo con su activación y, en caso de que no estuviera
        situada la válvula deja en espera el inicio del temporizador.
        En caso de reanudar una caracterizaicón ya comenzada, actualiza la bandera de estado de parada y vuelve a activar el canal con el tiempo restante almacenado.
        
        Args: 
            Ninguno.
        Return:
            - return: Es empleado para salir del método ante la introducción de valores de tiempo de caracterización incompatible.
        Raises:
            Ninguno.

        """

        if self.canal_caracterizacion is not None:
            self._actualizar_bloqueo_canales_manual()

            if not self.caracterizacion_concentracion_parado and not self.caracterizando_concentracion:

                if int(self.e_tiempo_caracterizacion.get()) > 0 and self.e_tiempo_caracterizacion.valor.get().strip() != "":
                    self.caracterizando_concentracion = True
                    self.consola.registro("Iniciando caracterizacion de concentración...")
                    tiempo_caracterizacion_segundos=int(self.e_tiempo_caracterizacion.get())*config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION
                    self.tiempo_grafica_concentracion = collections.deque((i * (1/config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION) for i in range(tiempo_caracterizacion_segundos)), maxlen=tiempo_caracterizacion_segundos)
                    self.buffer_grafica_concentracion = collections.deque([np.nan]*len(self.tiempo_grafica_concentracion), maxlen=len(self.tiempo_grafica_concentracion))
                    self.contador_concentracion = 0
                    self.buffer_caracterizacion_concentracion.clear()
                    self.b_iniciar_caracterizacion_concentracion.configure(state="disabled")
                    self.b_reiniciar_caracterizacion_concentracion.configure(state="disabled")
                    num_canal = self.canal_caracterizacion.num_canal

                    if num_canal not in self.historial_caracterizacion:
                        self.historial_caracterizacion[num_canal] = {}

                    self.historial_caracterizacion[num_canal].setdefault("tiempo_inicio", time.time())
                    self.historial_caracterizacion[num_canal].setdefault("duracion", self.e_tiempo_caracterizacion.get())
                    self.historial_caracterizacion[num_canal].setdefault("olor", self.canal_caracterizacion.e_olor_canal.get() if self.canal_caracterizacion.e_olor_canal.winfo_exists() else self.canal_caracterizacion.color_canal)

                    if not self.caracterizando_flujo and not self.caracterizando_velocidad and not self.caracterizando_latencia:
                        self.canal_caracterizacion.activar_canal()

                    if num_canal == self.canal_esperando_posicion:
                        self.callbacks_pendientes_posicion_valvula.append((num_canal, self._periodo_caracterizacion_concentracion, (self.canal_caracterizacion, self.e_tiempo_caracterizacion.get())))

                    else:
                        self._periodo_caracterizacion_concentracion(self.canal_caracterizacion, self.e_tiempo_caracterizacion.get())

                else:
                    self.consola.registro("El tiempo de caracterización no puede ser negativo, igual a 0 o estar vacío")
                    return

            else:
                self.caracterizacion_concentracion_parado = False
                self.consola.registro("Reanudando caracterizacion de concentración...")
                self.consola.registro(f"Tiempo guardado: {self.segundos_restantes_concentracion}")
                self.canal_caracterizacion.activar_canal()
                self._periodo_caracterizacion_concentracion(self.canal_caracterizacion, self.segundos_restantes_concentracion)

        else:
            self.consola.registro("No hay ningún canal seleccionado para caracterizar. Seleccione un canal para iniciar el caracterizacion de concentración", nivel="AVISO")
            
        
    def _periodo_caracterizacion_concentracion(self, canal_caracterizacion, segundos_restantes):
        """
        Temporizador del periodo de caracterización de concentración. 

        Si el temporizador no ha llegado a 0, autoreagenda su llamada actualizando tiempo restante tras un segundo. Por cada iteración se almacena el valor en la variable 
        global para tener una referencia globalmente conocida. Si transcurre finalmente el tiempo marcado por el protocolo, el canal caracterizado se detiene y 
        comienza la parada de la caracterización de concentración.
        
        
        Args: 
            - canal_caracterizacion (Canal): Canal seleccionado a caracterizar.
            - segundos_restantes (int): Tiempo restante de caracterización.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.segundos_restantes_concentracion = segundos_restantes

        if segundos_restantes > 0:
            self.consola.registro(f"caracterizacion de concentración en curso... Tiempo restante: {self.segundos_restantes_concentracion}s")
            self.after_caracterizacion_concentracion = self.after(1000, lambda: self._periodo_caracterizacion_concentracion(canal_caracterizacion, segundos_restantes - 1))

        else:

            if canal_caracterizacion is not None:
                canal_caracterizacion.parar_canal()

            else:
                self.consola.registro("No hay ningún canal seleccionado para caracterizar. Seleccione un canal para iniciar el caracterizacion de concentración.", nivel="AVISO")

            self.parar_caracterizacion_concentracion()


    def reiniciar_caracterizacion_concentracion(self):
        """
        Reinicia la caracterización de concentración ya iniciada. 

        Cancela las funciones de activación del canal caracterizado y temporizador del parámetro concentración, además de las funciones de activación pendiente.
        En caso de que la varible global tenga un canal caracterizando asociado se procede a la detención del mismo. Adicionalmente se reinician visual y lógicamnete
        la gráfica de concentración representada en tiempo real. Finalmente de informa por consola al usuario del reinicio y se reahabilitan los componentes previamente
        bloqueados.
        
        Args: 
            Ninguno.
        Return:
            - return: Es empleado para salir del método ante la introducción de valores de tiempo de caracterización incompatible.
        Raises:
            Ninguno.

        """

        self._cancelar_espera_posicion_valvula(self._periodo_caracterizacion_concentracion)

        if self.canal_caracterizacion is not None:
            self._cancelar_activacion_pendiente(self.canal_caracterizacion)

        self.caracterizando_concentracion = False
        self.caracterizacion_concentracion_parado = False
        self.segundos_restantes_concentracion = 0
        self.contador_concentracion = 0
        self.tiempo_guardado = None

        if self.after_caracterizacion_concentracion:
            self.after_cancel(self.after_caracterizacion_concentracion)
            self.after_caracterizacion_concentracion = None

        if self.canal_caracterizacion is not None:
            self.canal_caracterizacion.parar_canal()

        else:
            self.consola.registro("No hay ningún canal seleccionado para caracterizar. Seleccione un canal para iniciar el caracterizacion de concentración.", nivel="AVISO")

        self.buffer_caracterizacion_concentracion.clear()

        if int(self.e_tiempo_caracterizacion.get()) <= 0 or self.e_tiempo_caracterizacion.valor.get().strip() == "":
            self.consola.registro("El tiempo de caracterización no puede ser negativo, igual a 0 o estar vacío")
            return

        tiempo_caracterizacion_segundos=int(self.e_tiempo_caracterizacion.get())*config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION
        self.tiempo_grafica_concentracion = collections.deque((i * (1/config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION) for i in range(tiempo_caracterizacion_segundos)), maxlen=tiempo_caracterizacion_segundos)
        self.buffer_grafica_concentracion = collections.deque([np.nan]*len(self.tiempo_grafica_concentracion), maxlen=len(self.tiempo_grafica_concentracion))

        self.ax_concentracion.clear()
        self.ax_concentracion.set_xlim(0,int(self.e_tiempo_caracterizacion.get()))
        self.ax_concentracion.set_ylim(config.LIMITESY["concentracion"][0],config.LIMITESY["concentracion"][1]) 
        self.ax_concentracion.set_xlabel("Tiempo (s)")
        self.ax_concentracion.set_ylabel("Índice VOC")
        self.ax_concentracion.tick_params(colors = "#ffffff") 
        self.ax_concentracion.xaxis.label.set_color("#ffffff") 
        self.ax_concentracion.yaxis.label.set_color("#ffffff") 
        self.ax_concentracion.spines['bottom'].set_color('#ffffff') 
        self.ax_concentracion.spines['left'].set_color('#ffffff')  
        self.ax_concentracion.spines['top'].set_color('#ffffff')  
        self.ax_concentracion.spines['right'].set_color('#ffffff')  
        self.canvas_concentracion.draw()

        self.b_iniciar_caracterizacion_concentracion.configure(state="normal")
        self._actualizar_bloqueo_canales_manual()
        self.consola.registro("caracterizacion de concentración reiniciado")


    def parar_caracterizacion_concentracion(self):
        """
        Detiene o finaliza la caracterización del parámetro concentración en curso. 

        Comienza cancelando aquellas ejecuciones pendientes relativas al temporizador asociado al parámetro de concentración y activación del canal caracterizado (si estuviera
        en proceso). Posteriormente detiene el canal caracterizado y rehabilita los botones de iniciar/reiniciar_caracterizacion_concentracion. Informa por último de los 
        segundos restantes por caracterizar el parámetro de concentración del canal seleccionado.
        En caso de haber finalizado el tiempo de caracterización del parámetro de concentración, se almacenan los datos contenidos en los buffer temporales de concentración
        para la posterior generación de la sección historial de caracterización y subsección de resultados caracterización del informe de la sesión experimental.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        if self.caracterizando_concentracion:
            self._cancelar_espera_posicion_valvula(self._periodo_caracterizacion_concentracion)
            self.caracterizacion_concentracion_parado = True

            if self.after_caracterizacion_concentracion:
                self.after_cancel(self.after_caracterizacion_concentracion)
                self.after_caracterizacion_concentracion = None

            if self.canal_caracterizacion is not None:

                if not self.caracterizacion_flujo_parado and not self.caracterizacion_velocidad_parado and not self.caracterizacion_latencia_parado:
                    self._cancelar_activacion_pendiente(self.canal_caracterizacion)
                    self.canal_caracterizacion.parar_canal()

            else:
                self.consola.registro("No hay ningún canal seleccionado para caracterizar. Seleccione un canal para iniciar el caracterizacion de concentración.", nivel="AVISO")

            self.b_iniciar_caracterizacion_concentracion.configure(state="normal")
            self.b_reiniciar_caracterizacion_concentracion.configure(state="normal")

            if self.segundos_restantes_concentracion > 0:
                self.consola.registro(f"caracterizacion de concentración parado con {self.segundos_restantes_concentracion} segundos restantes")

            else:

                if self.canal_caracterizacion is not None:
                    num_canal = self.canal_caracterizacion.num_canal

                    if num_canal not in self.historial_caracterizacion:
                        self.historial_caracterizacion[num_canal] = {}
                        self.historial_caracterizacion[num_canal]["olor"] = self.canal_caracterizacion.e_olor_canal.get() or self.canal_caracterizacion.color_canal

                    self.historial_caracterizacion[num_canal]["concentracion"] = list(self.buffer_caracterizacion_concentracion)
                    self.caracterizando_concentracion = False
                    self.caracterizacion_concentracion_parado = False
                    self.consola.registro("caracterizacion de concentración finalizado")

                else:
                    self.consola.registro("No se pudieron guardar las métricas de caracterizacion: No hay ningún canal seleccionado para caracterizar.", nivel="AVISO")

            self._actualizar_bloqueo_canales_manual()

        else:
            self.consola.registro("No hay ningún caracterizacion activo. Seleccione un canal y pulse iniciar para comenzar el caracterizacion de concentración.", nivel="AVISO")


    def iniciar_caracterizacion_latencia(self):
        """
        Inicia o reanuda la caracterización del parámetro de latencia. 

        A partir de la selección del canal a caracterizar, deshabilita la totalidad de los elementos accionables del software a excepción de la parada.
        Actualiza las variables globales y banderas de esto implicadas en el registro de la caracterización y que posteriormente se emplearán para su representación 
        en tiempo real. Agrega el tiempo de inicio, la duración y el olor del canal a caracterizar, prosiguiendo con su activación y, en caso de que no estuviera
        situada la válvula deja en espera el inicio del temporizador.
        En caso de reanudar una caracterizaicón ya comenzada, actualiza la bandera de estado de parada y vuelve a activar el canal con el tiempo restante almacenado.
        
        Args: 
            Ninguno.
        Return:
            - return: Es empleado para salir del método ante la introducción de valores de tiempo de caracterización incompatible.
        Raises:
            Ninguno.

        """

        if self.canal_caracterizacion is not None:
            self._actualizar_bloqueo_canales_manual()

            if not self.caracterizacion_latencia_parado and not self.caracterizando_latencia:
                if int(self.e_tiempo_caracterizacion.get()) > 0 and self.e_tiempo_caracterizacion.valor.get().strip() != "":
                    self.caracterizando_latencia = True
                    self.consola.registro("Iniciando caracterizacion de latencia...")
                    tiempo_caracterizacion_segundos=int(self.e_tiempo_caracterizacion.get())*config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION
                    self.tiempo_grafica_latencia = collections.deque((i * (1/config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION) for i in range(tiempo_caracterizacion_segundos)), maxlen=tiempo_caracterizacion_segundos)
                    self.buffer_grafica_latencia = collections.deque([np.nan]*len(self.tiempo_grafica_latencia), maxlen=len(self.tiempo_grafica_latencia))
                    self.contador_latencia = 0
                    self.buffer_caracterizacion_latencia.clear()
                    self.b_iniciar_caracterizacion_latencia.configure(state="disabled")
                    self.b_reiniciar_caracterizacion_latencia.configure(state="disabled")
                    num_canal = self.canal_caracterizacion.num_canal

                    if num_canal not in self.historial_caracterizacion:
                        self.historial_caracterizacion[num_canal] = {}

                    self.historial_caracterizacion[num_canal].setdefault("tiempo_inicio", time.time())
                    self.historial_caracterizacion[num_canal].setdefault("duracion", self.e_tiempo_caracterizacion.get())
                    self.historial_caracterizacion[num_canal].setdefault("olor", self.canal_caracterizacion.e_olor_canal.get() if self.canal_caracterizacion.e_olor_canal.winfo_exists() else self.canal_caracterizacion.color_canal)

                    if not self.caracterizando_flujo and not self.caracterizando_concentracion and not self.caracterizando_velocidad:
                        self.canal_caracterizacion.activar_canal()

                    if num_canal == self.canal_esperando_posicion:
                        self.callbacks_pendientes_posicion_valvula.append((num_canal, self._periodo_caracterizacion_latencia, (self.canal_caracterizacion, self.e_tiempo_caracterizacion.get())))

                    else:
                        self._periodo_caracterizacion_latencia(self.canal_caracterizacion, self.e_tiempo_caracterizacion.get())

                else:
                    self.consola.registro("El tiempo de caracterización no puede ser negativo, igual a 0 o estar vacío")
                    return  

            else:
                self.caracterizacion_latencia_parado = False
                self.consola.registro("Reanudando caracterizacion de latencia...")
                self.consola.registro(f"Tiempo guardado: {self.segundos_restantes_latencia}")
                self.canal_caracterizacion.activar_canal()
                self._periodo_caracterizacion_latencia(self.canal_caracterizacion, self.segundos_restantes_latencia)

        else:
            self.consola.registro("No hay ningún canal seleccionado para caracterizar. Seleccione un canal para iniciar el caracterizacion de latencia", nivel="AVISO")
            

    def _periodo_caracterizacion_latencia(self, canal_caracterizacion, segundos_restantes):
        """
        Temporizador del periodo de caracterización de latencia. 

        Si el temporizador no ha llegado a 0, autoreagenda su llamada actualizando tiempo restante tras un segundo. Por cada iteración se almacena el valor en la variable 
        global para tener una referencia globalmente conocida. Si transcurre finalmente el tiempo marcado por el protocolo, el canal caracterizado se detiene y 
        comienza la parada de la caracterización de latencia.
        
        
        Args: 
            - canal_caracterizacion (Canal): Canal seleccionado a caracterizar.
            - segundos_restantes (int): Tiempo restante de caracterización.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.segundos_restantes_latencia = segundos_restantes

        if segundos_restantes > 0:
            self.consola.registro(f"caracterizacion de latencia en curso... Tiempo restante: {self.segundos_restantes_latencia}s")
            self.after_caracterizacion_latencia = self.after(1000, lambda: self._periodo_caracterizacion_latencia(canal_caracterizacion, segundos_restantes - 1))

        else:

            if canal_caracterizacion is not None:
                canal_caracterizacion.parar_canal()

            else:
                self.consola.registro("No hay ningún canal seleccionado para caracterizar. Seleccione un canal para iniciar el caracterizacion de latencia.", nivel="AVISO")

            self.parar_caracterizacion_latencia()


    def reiniciar_caracterizacion_latencia(self):
        """
        Reinicia la caracterización de latencia ya iniciada. 

        Cancela las funciones de activación del canal caracterizado y temporizador del parámetro latencia, además de las funciones de activación pendiente.
        En caso de que la varible global tenga un canal caracterizando asociado se procede a la detención del mismo. Adicionalmente se reinician visual y lógicamnete
        la gráfica de latencia representada en tiempo real. Finalmente de informa por consola al usuario del reinicio y se reahabilitan los componentes previamente
        bloqueados.
        
        Args: 
            Ninguno.
        Return:
            - return: Es empleado para salir del método ante la introducción de valores de tiempo de caracterización incompatible.
        Raises:
            Ninguno.

        """

        self._cancelar_espera_posicion_valvula(self._periodo_caracterizacion_latencia)

        if self.canal_caracterizacion is not None:
            self._cancelar_activacion_pendiente(self.canal_caracterizacion)

        self.caracterizando_latencia = False
        self.caracterizacion_latencia_parado = False
        self.segundos_restantes_latencia = 0
        self.contador_latencia = 0
        self.tiempo_guardado = None

        if self.after_caracterizacion_latencia:
            self.after_cancel(self.after_caracterizacion_latencia)
            self.after_caracterizacion_latencia = None

        if self.canal_caracterizacion is not None:
            self.canal_caracterizacion.parar_canal()

        else:
            self.consola.registro("No hay ningún canal seleccionado para caracterizar. Seleccione un canal para iniciar el caracterizacion de latencia.", nivel="AVISO")

        self.buffer_caracterizacion_latencia.clear()

        if int(self.e_tiempo_caracterizacion.get()) <= 0 or self.e_tiempo_caracterizacion.valor.get().strip()== "":
            self.consola.registro("El tiempo de caracterización no puede ser negativo, igual a 0 o estar vacío")
            return

        tiempo_caracterizacion_segundos=int(self.e_tiempo_caracterizacion.get())*config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION
        self.tiempo_grafica_latencia = collections.deque((i * (1/config.MUESTRAS_POR_SEGUNDO_CARACTERIZACION) for i in range(tiempo_caracterizacion_segundos)), maxlen=tiempo_caracterizacion_segundos)
        self.buffer_grafica_latencia = collections.deque([np.nan]*len(self.tiempo_grafica_latencia), maxlen=len(self.tiempo_grafica_latencia))

        self.ax_latencia.clear()
        self.ax_latencia.set_xlim(0,int(self.e_tiempo_caracterizacion.get()))
        self.ax_latencia.set_ylim(config.LIMITESY["latencia"][0],config.LIMITESY["latencia"][1]) 
        self.ax_latencia.set_xlabel("Tiempo (s)")
        self.ax_latencia.set_ylabel("Latencia (ms)")
        self.ax_latencia.tick_params(colors = "#ffffff") 
        self.ax_latencia.xaxis.label.set_color("#ffffff") 
        self.ax_latencia.yaxis.label.set_color("#ffffff")
        self.ax_latencia.spines['bottom'].set_color('#ffffff') 
        self.ax_latencia.spines['left'].set_color('#ffffff') 
        self.ax_latencia.spines['top'].set_color('#ffffff') 
        self.ax_latencia.spines['right'].set_color('#ffffff')  
        self.canvas_latencia.draw()

        self.b_iniciar_caracterizacion_latencia.configure(state="normal")
        self._actualizar_bloqueo_canales_manual()
        self.consola.registro("caracterizacion de latencia reiniciado")


    def parar_caracterizacion_latencia(self):
        """
        Detiene o finaliza la caracterización del parámetro latencia en curso. 

        Comienza cancelando aquellas ejecuciones pendientes relativas al temporizador asociado al parámetro de latencia y activación del canal caracterizado (si estuviera
        en proceso). Posteriormente detiene el canal caracterizado y rehabilita los botones de iniciar/reiniciar_caracterizacion_latencia. Informa por último de los 
        segundos restantes por caracterizar el parámetro de latencia del canal seleccionado.
        En caso de haber finalizado el tiempo de caracterización del parámetro de latencia, se almacenan los datos contenidos en los buffer temporales de latencia
        para la posterior generación de la sección historial de caracterización y subsección de resultados caracterización del informe de la sesión experimental.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        if self.caracterizando_latencia:
            self._cancelar_espera_posicion_valvula(self._periodo_caracterizacion_latencia)
            self.caracterizacion_latencia_parado = True

            if self.after_caracterizacion_latencia:
                self.after_cancel(self.after_caracterizacion_latencia)
                self.after_caracterizacion_latencia = None

            if self.canal_caracterizacion is not None:

                if not self.caracterizacion_flujo_parado and not self.caracterizacion_concentracion_parado and not self.caracterizacion_velocidad_parado:
                    self._cancelar_activacion_pendiente(self.canal_caracterizacion)
                    self.canal_caracterizacion.parar_canal()

            else:
                self.consola.registro("No hay ningún canal seleccionado para caracterizar. Seleccione un canal para iniciar el caracterizacion de latencia.", nivel="AVISO")

            self.b_iniciar_caracterizacion_latencia.configure(state="normal")
            self.b_reiniciar_caracterizacion_latencia.configure(state="normal")

            if self.segundos_restantes_latencia > 0:
                self.consola.registro(f"caracterizacion de latencia parado con {self.segundos_restantes_latencia} segundos restantes")
        
            else:

                if self.canal_caracterizacion is not None:
                    num_canal = self.canal_caracterizacion.num_canal

                    if num_canal not in self.historial_caracterizacion:
                        self.historial_caracterizacion[num_canal] = {}
                        self.historial_caracterizacion[num_canal]["olor"] = self.canal_caracterizacion.e_olor_canal.get() or self.canal_caracterizacion.color_canal

                    self.historial_caracterizacion[num_canal]["latencia"] = list(self.buffer_caracterizacion_latencia)
                    self.caracterizando_latencia = False
                    self.caracterizacion_latencia_parado = False
                    self.consola.registro("caracterizacion de latencia finalizado")

                else:
                    self.consola.registro("No se pudieron guardar las métricas de caracterizacion: No hay ningún canal seleccionado para caracterizar.", nivel="AVISO")

            self._actualizar_bloqueo_canales_manual()

        else:
            self.consola.registro("No hay ningún caracterizacion activo. Seleccione un canal y pulse iniciar para comenzar el caracterizacion de latencia.", nivel="AVISO")


    def iniciar_caracterizacion_general(self):
        """
        Inicia o reanuda la caracterización de todos los parámetros simultáneamente. 

        Realiza la llamada de la función de inicio de caracterización de cada parámetro.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.iniciar_caracterizacion_velocidad()
        self.iniciar_caracterizacion_flujo()
        self.iniciar_caracterizacion_concentracion()
        self.iniciar_caracterizacion_latencia()


    def _consultar__reiniciar_caracterizacion_general(self):
        """
        Consulta al usuario el reinicio de la caracterización general. 

        En caso de que la caracterización de cualquier parámetro este en curso y el usuario trate de realizar un reinicio general, genera una ventana emergente
        consultando la confirmación del reinicio solicitado. Dependiendo de la respuesta obtenida ejecuta el reinicio global de la caracterización de parámetros
        o cancela la solicitud.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        if self.caracterizando_velocidad or self.caracterizando_flujo or self.caracterizando_concentracion or self.caracterizando_latencia:
            respuesta = messagebox.askyesno("Reiniciar caracterizacion general", "¿Está seguro de que desea reiniciar el caracterizacion general? Se reiniciará el caracterizacion de todos los canales y se perderán los datos de la actual sesión experimental.")

            if respuesta:
                self.consola.registro("Reiniciando caracterizacion general...")
                self._reiniciar_caracterizacion_general()
                self.consola.registro("Caracterizacion general reiniciado.")

            else:
                self.consola.registro("Reinicio de caracterizacion general cancelado.")

        else:
            self.consola.registro("No hay ningún caracterizacion activo. Seleccione un canal y pulse iniciar para comenzar el caracterizacion.", nivel="AVISO")


    def _reiniciar_caracterizacion_general(self):
        """
        Reinicia la caracterización general ya iniciada. 

        Realiza la llamada de la función de reinicio de caracterización de cada parámetro.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        # Evaluación software.
        #self.t0_actualizacion__reiniciar_caracterizacion_general = time.perf_counter()

        self.reiniciar_caracterizacion_velocidad()
        self.reiniciar_caracterizacion_flujo()
        self.reiniciar_caracterizacion_concentracion()
        self.reiniciar_caracterizacion_latencia()

        # Evaluación software.
        #self.update_idletasks()
        #diferencia_temporal = time.perf_counter() - self.t0_actualizacion__reiniciar_caracterizacion_general
        #self.tiempos_actualizacion ["_reiniciar_caracterizacion_general"].append(diferencia_temporal)
        #self.t0_actualizacion__reiniciar_caracterizacion_general = 0
        #print(f"Tiempo de actualización de la UI al reiniciar caracterización general: {diferencia_temporal} segundos")


    def _consultar__parar_caracterizacion_general(self):
        """
        Consulta al usuario la parada de la caracterización general en curso. 

        En caso de que la caracterización de cualquier parámetro este en curso y el usuario trate de realizar una parada general, genera una ventana emergente
        consultando la confirmación de la pausa solicitada. Dependiendo de la respuesta obtenida ejecuta la parada global de la caracterización de parámetros
        o cancela la solicitud.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        if self.caracterizando_velocidad or self.caracterizando_flujo or self.caracterizando_concentracion or self.caracterizando_latencia:
            respuesta = messagebox.askyesno("Parar caracterizacion general", "¿Está seguro de que desea parar el caracterizacion general? Se pausará el caracterizacion de todos los canales y se podrá reanudar más tarde.")

            if respuesta:
                self.consola.registro("Parando caracterizacion general...")
                self._parar_caracterizacion_general()
                self.consola.registro("caracterizacion general parado.")

            else:
                self.consola.registro("Parada de caracterizacion general cancelada.")

        else:
            self.consola.registro("No hay ningún caracterizacion activo. Seleccione un canal y pulse iniciar para comenzar el caracterizacion.", nivel="AVISO")


    def _parar_caracterizacion_general(self):
        """
        Para la caracterización general en curso. 

        Realiza la llamada de la función de parada de caracterización de cada parámetro.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.parar_caracterizacion_velocidad()
        self.parar_caracterizacion_flujo()
        self.parar_caracterizacion_concentracion()
        self.parar_caracterizacion_latencia()

    
    def seleccionar_caracterizacion(self,nombre_canal):
        """
        Comprueba y define el canal seleccionado a caracterizar. 

        Reinicia las variables y búfferes necesarios para la correcta caracterización del canal seleccionado y cambio visual del software. 
        Por último actualiza la variable asociada al canal caracterizado.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        if not self._caracterizacion_activo():

            if nombre_canal != 'Ninguno':
                self.contador_concentracion = 0
                self.contador_flujo = 0
                self.contador_velocidad = 0
                self.contador_latencia = 0
                self.buffer_grafica_concentracion =  collections.deque([np.nan]*config.TAMANO_BUFFER_GRAFICAS,maxlen=config.TAMANO_BUFFER_GRAFICAS)
                self.buffer_grafica_flujo =  collections.deque([np.nan]*config.TAMANO_BUFFER_GRAFICAS,maxlen=config.TAMANO_BUFFER_GRAFICAS)
                self.buffer_grafica_latencia =  collections.deque([np.nan]*config.TAMANO_BUFFER_GRAFICAS,maxlen=config.TAMANO_BUFFER_GRAFICAS)
                self.buffer_grafica_velocidad =  collections.deque([np.nan]*config.TAMANO_BUFFER_GRAFICAS,maxlen=config.TAMANO_BUFFER_GRAFICAS)
                self.consola.registro(f'Canal seleccionado para caracterizar: {nombre_canal}')

                for canal in self.cuadros_canales:
                    if canal.e_olor_canal.get() == nombre_canal or canal.l_color_canal.cget("text") == nombre_canal:
                        self.canal_caracterizacion = canal

            else:
                self.consola.registro(f'No se ha seleccionado ningún canal para caracterizar')

        else:   
            self.comb_canales_caracterizacion.configure(state = "disabled")
        
                
    def _caracterizacion_activo(self):
        """
        Comprueba si se está realizando la caracterización de algún parámetro. 
        
        Args: 
            Ninguno.
        Return:
            - self.caracterizando_velocidad or self.caracterizando_flujo or self.caracterizando_concentracion or self.caracterizando_latencia (booleano): Confirma
            o desmiente que se esté realizando la caracterización de algún parámetro.
        Raises:
            Ninguno.

        """

        return (self.caracterizando_velocidad or self.caracterizando_flujo or
                self.caracterizando_concentracion or self.caracterizando_latencia)


    def _cancelar_espera_posicion_valvula(self, funcion_periodo_en_espera):
        """
        Cancela la función callback pendiente pasada como argumento. 

        Se recorre la lista de tuplas en busca de la función con el mismo nombre que el pasado como argumento, generando nuevamente la misma sin la función
        especificada.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.callbacks_pendientes_posicion_valvula = [
            (num_canal, funcion, argumentos) for num_canal, funcion, argumentos in self.callbacks_pendientes_posicion_valvula
            if funcion != funcion_periodo_en_espera
        ]


    def _actualizar_bloqueo_canales_manual(self):
        """
        Bloquea o desbloquea los widgets accionables de todos los marcos de los canales. 

        En caso de que el protocolo experimental o la caracterización de algún canal esté teniendo lugar, los botones asociados a los diferentes marcos
        de los canales son bloqueados como medida de seguridad. En cualquier caso contrario, son desbloqueados.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        if self.protocolo_activo or self._caracterizacion_activo():

            for canal in self.cuadros_canales:
                canal.b_activar_canal.configure(state="disabled")
                canal.b_parar_canal.configure(state="disabled")
        else:

            for canal in self.cuadros_canales:
                canal.b_activar_canal.configure(state="normal")
                canal.b_parar_canal.configure(state="normal")


    def _cancelar_activacion_pendiente(self, canal):
        """
        Cancela la función callback de activación pendiente del canal pasado como argumento. 

        Se recorre la lista de tuplas en busca de que la función asociada sea aquella destinada a completar la activación solicitada y coincida el canal con el pasado como
        argumento. Generando la lista de tuplas nuevamente pero sin este registro, evitando cualquier activación no deseada.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.callbacks_pendientes_posicion_valvula = [
            (num_canal, funcion, argumentos) for num_canal, funcion, argumentos in self.callbacks_pendientes_posicion_valvula
            if not (funcion == self._completar_activacion_canal and num_canal == canal.num_canal)
        ]


    def _completar_activacion_canal(self, canal):
        """
        Completa la activación del canal pasado como argumento. 

        Tras la recepción del mensaje de posición alcanzada por la válvula, se envía el comando de activación de la fuente de aire correspondiente
        y se confirma la activación del canal.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.ws_client.enviar({"cmd": "activar", "canal": canal.num_canal, "velocidad_%": config.PORCENTAJE_VELOCIDAD})
        canal.confirmar_activacion()


    def _actualizar_graficas(self):
        """
        Actualiza las gráficas de los parámetros caracterizados en tiempo real. 

        Por cada parámetro caracterizado, si es la primera vez que se van a representar datos se genera la gráfica correspondiente con el primer valor, y en sucesivas
        iteraciones actualiza la gráfica con los valores específicos del tiempo y parámetro registrados hasta el momento. Configurando en todo momento el aspecto visual 
        y configuración invariables de la gráfica. Por último, se autoreagenda tras config.INTERVALO_DE_ACTUALIZACION_UI_MS para la representación de los valores de cada 
        parámetro caracterizado en tiempo real.
        
        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        if self.caracterizando_velocidad and not self.caracterizacion_velocidad_parado:

            if not self.ax_velocidad.lines:
                self.ax_velocidad.clear()
                self.ax_velocidad.plot(self.tiempo_grafica_velocidad, self.buffer_grafica_velocidad)

            else: 
                self.ax_velocidad.lines[0].set_data(self.tiempo_grafica_velocidad, self.buffer_grafica_velocidad)

            self.ax_velocidad.set_xlim(0,int(self.e_tiempo_caracterizacion.get()))
            self.ax_velocidad.set_ylim(config.LIMITESY["velocidad"][0],config.LIMITESY["velocidad"][1])  
            self.ax_velocidad.set_xlabel("Tiempo (s)")
            self.ax_velocidad.set_ylabel("Velocidad (m/s)")
            self.ax_velocidad.tick_params(colors = "#ffffff") 
            self.ax_velocidad.xaxis.label.set_color("#ffffff")  
            self.ax_velocidad.yaxis.label.set_color("#ffffff")  
            self.canvas_velocidad.draw()

        if self.caracterizando_flujo and not self.caracterizacion_flujo_parado:

            if not self.ax_flujo.lines:
                self.ax_flujo.clear()
                self.ax_flujo.plot(self.tiempo_grafica_flujo, self.buffer_grafica_flujo)

            else: 
                self.ax_flujo.lines[0].set_data(self.tiempo_grafica_flujo, self.buffer_grafica_flujo)

            self.ax_flujo.set_xlim(0,int(self.e_tiempo_caracterizacion.get()))
            self.ax_flujo.set_ylim(config.LIMITESY["flujo"][0],config.LIMITESY["flujo"][1]) 
            self.ax_flujo.set_xlabel("Tiempo (s)")
            self.ax_flujo.set_ylabel("Flujo (ml/min)")
            self.ax_flujo.tick_params(colors = "#ffffff") 
            self.ax_flujo.xaxis.label.set_color("#ffffff") 
            self.ax_flujo.yaxis.label.set_color("#ffffff") 
            self.canvas_flujo.draw()

        if self.caracterizando_concentracion and not self.caracterizacion_concentracion_parado:

            if not self.ax_concentracion.lines:
                self.ax_concentracion.clear()
                self.ax_concentracion.plot(self.tiempo_grafica_concentracion, self.buffer_grafica_concentracion)

            else: 
                self.ax_concentracion.lines[0].set_data(self.tiempo_grafica_concentracion, self.buffer_grafica_concentracion)

            self.ax_concentracion.set_xlim(0,int(self.e_tiempo_caracterizacion.get()))
            self.ax_concentracion.set_ylim(config.LIMITESY["concentracion"][0],config.LIMITESY["concentracion"][1])  
            self.ax_concentracion.set_xlabel("Tiempo (s)")
            self.ax_concentracion.set_ylabel("Índice VOC")
            self.ax_concentracion.tick_params(colors = "#ffffff") 
            self.ax_concentracion.xaxis.label.set_color("#ffffff")  
            self.ax_concentracion.yaxis.label.set_color("#ffffff")
            self.canvas_concentracion.draw()

        if self.caracterizando_latencia and not self.caracterizacion_latencia_parado:

            if not self.ax_latencia.lines:
                self.ax_latencia.clear()
                self.ax_latencia.plot(self.tiempo_grafica_latencia, self.buffer_grafica_latencia)

            else: 
                self.ax_latencia.lines[0].set_data(self.tiempo_grafica_latencia, self.buffer_grafica_latencia)

            self.ax_latencia.set_xlim(0,int(self.e_tiempo_caracterizacion.get()))
            self.ax_latencia.set_ylim(config.LIMITESY["latencia"][0],config.LIMITESY["latencia"][1]) 
            self.ax_latencia.set_xlabel("Tiempo (s)")
            self.ax_latencia.set_ylabel("Latencia (ms)")
            self.ax_latencia.tick_params(colors = "#ffffff") 
            self.ax_latencia.xaxis.label.set_color("#ffffff") 
            self.ax_latencia.yaxis.label.set_color("#ffffff")  
            self.canvas_latencia.draw()
            
        self.after__actualizar_graficas = self.after(config.INTERVALO_DE_ACTUALIZACION_UI_MS, self._actualizar_graficas)


    def _calcular_posicion_valvula(self, num_canal_actual, num_canal_final):
        """
        Calcula el movimiento necesario para ubicar la válvula en su posición final. 

        Calcula la diferencia entre las posiciones pasadas como argumento, actualizando la variable con la posición actual de la válvula a
        la posición de destino.
        
        Args: 
            - num_canal_actual (int): Canal asociado a la posición actual de la válvula. 
            - num_canal_final (int): Canal asociado a la posición de destino a colocar la válvula.
        Return:
            - movimiento (int): Cantidad de pasos a realizar por la válvula hasta llegar a su canal de destino.
        Raises:
            Ninguno.

        """

        movimiento = self.posiciones_canales[num_canal_final] - self.posiciones_canales[num_canal_actual]
        self.posicion_valvula = self.posicion_valvula + movimiento

        return movimiento
        
   
    def actualizar_canales(self,num_canal,accion):
        """
        Gestiona la activación y parada de todo canal. 

        A partir del canal y acción asociada pasados como argumentos, se procede a la correspondiente activación o parada del mismo. En el caso de la activación, primeramente 
        se calcula los pasos necesarios en la válvula para pasar de la posición actual a la de destino. Se detiene aquel canal que estuviera activo, informando por consola
        al usuario del cambio y se actualiza el nuevo canal activo (el asociado a la posición de destino). Con la actualización de los widgets de la sección Estado, se envía
        la acción necesaria al ESP32-WROOM-32U mediante el cliente WebSocket creado, se establece el canal en espera con el de destino y se agrega la función complementaria
        para finalizar su activación como callback pendiente.
        Para la desactivación de un canal activo, se comienza cancelando cualquier acción de activación pendiente del canal pasado. Actualiza variables globales y widgets 
        de estado, registrando en el historial de sesión los últimos datos obtenidos por telemetría de dicho canal para completar el informe de sesión generado. 
        Por último, envía la acción de parada del canal al ESP32-WROOM-32U y; en caso de no se estuviera ejecutando un protocolo, calcula y rota la válvula los pasos 
        necesarios para volver a la posición de reposo asociada al canal destinado a la limpieza y desensibilización.
        
        Args: 
            - num_canal (int): Canal asociado a la posición actual de la válvula. 
            - accion (str): Canal asociado a la posición de destino a colocar la válvula.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        if accion== "activar":
            pasos = self._calcular_posicion_valvula(self.canal_activo.num_canal if self.canal_activo else config.CANAL_BLANCO, num_canal)
            
            if self.canal_activo != None and self.canal_activo.num_canal != num_canal:
                self.consola.registro(f"Se ha activado el canal {num_canal} ({self.cuadros_canales[num_canal].e_olor_canal.get() if self.cuadros_canales[num_canal].e_olor_canal.get() else ''}) mientras el canal {self.canal_activo.num_canal} ({self.cuadros_canales[self.canal_activo.num_canal].e_olor_canal.get() if self.cuadros_canales[self.canal_activo.num_canal].e_olor_canal.get() else ''}) estaba activo. Se detiene el canal {self.canal_activo.num_canal} ({self.cuadros_canales[self.canal_activo.num_canal].e_olor_canal.get() if self.cuadros_canales[self.canal_activo.num_canal].e_olor_canal.get() else ''}).", nivel="AVISO")
                self.canal_activo.parar_canal()

            self.canal_activo = self.cuadros_canales[num_canal]

            if self.canal_activo.e_olor_canal.winfo_exists() and self.canal_activo.e_olor_canal.get():
                self.sv_canal_activo.set(f"Canal {self.canal_activo.e_olor_canal.get()}")

            if self.canal_activo.e_olor_canal.winfo_exists() and self.canal_activo.e_olor_canal.get() == "":
                self.sv_canal_activo.set(f"Canal ----")

            if not self.canal_activo.e_olor_canal.winfo_exists():
                self.sv_canal_activo.set(f"Canal Blanco")

            if self.protocolo_activo:

                if self.sv_canal_activo.get() == "Canal Blanco":
                    self.sv_canal_anterior.set(f"Canal {self.canales_protocolo[self.indice_canal_protocolo].e_olor_canal.get()}" if self.indice_canal_protocolo >=0 else "Ninguno")
                    self.sv_canal_siguiente.set(f"Canal {self.canales_protocolo[self.indice_canal_protocolo + 1].e_olor_canal.get()}" if self.indice_canal_protocolo+1 < len(self.canales_protocolo)  else "Ninguno")

                else:
                    self.sv_canal_anterior.set(f"Canal Blanco" if self.indice_canal_protocolo - 1 >= 0 else "Ninguno")
                    self.sv_canal_siguiente.set(f"Canal Blanco" if self.indice_canal_protocolo + 1 <= len(self.canales_protocolo)  else "Ninguno")      
            
            self.ws_client.enviar({"cmd": "rotar", "canal": num_canal, "pasos": pasos})
            self.canal_esperando_posicion = num_canal
            self.callbacks_pendientes_posicion_valvula.append((num_canal, self._completar_activacion_canal, (self.cuadros_canales[num_canal],)))

        if accion== "parar":
            self._cancelar_activacion_pendiente(self.cuadros_canales[num_canal])

            if self.canal_esperando_posicion == num_canal:
                self.canal_esperando_posicion = None

            if self.canal_activo is not None and self.canal_activo.num_canal == num_canal:
                ultima_telemetria = self.ultimos_datos_telemetria.get(num_canal, {})
                self.historial_sesion.append({
                            "timestamp" : time.time(),
                            "canal" : self.canal_activo.num_canal,
                            "olor" : self.canal_activo.e_olor_canal.get()
                            if self.canal_activo.e_olor_canal.winfo_exists() else "",
                            "estado" : "inactivo" ,
                            "flujo" :ultima_telemetria.get("flujo", 0.0),
                            "velocidad_motor" : ultima_telemetria.get("velocidad_motor", 0.0),
                            "concentracion" : ultima_telemetria.get("concentracion", 0.0),
                            "latencia" : ultima_telemetria.get("latencia", 0),
                            "modo": ultima_telemetria.get("modo","----")
                })

                if not self.protocolo_activo:
                    pasos = self._calcular_posicion_valvula(self.canal_activo.num_canal if self.canal_activo else config.CANAL_BLANCO, config.CANAL_BLANCO)
                    self.ws_client.enviar({"cmd": "rotar", "canal": num_canal, "pasos": pasos})
                    self.canal_activo = None
                    self.sv_canal_activo.set("Ninguno")

            self.ws_client.enviar({"cmd": "parar", "canal": num_canal})
            

    def _datos_telemetria(self, datos: dict):
        """
        Procesa los datos obtenidos de telemetría. 

        Por cada vez que es llamada almacena los datos pasados como argumento como última telemetería obtenida para generar posteriormente si es necesario, los datos del 
        canal correspondiente en el momento que es detenido. Posteriormente se agregan ciertos parámetros de los datos obtenidos en el historial completo de la sesión y 
        en el archivo .jsonl temporal previamente creado. Adicionalmente se actualizan los bufferes destinados a la gráfica en tiempo real y temporales para la construcción
        del histoial de caracterización. Por último se actualiza la etiqueta de Estado que refleja la latencia existente en la conexión WebSocket.
        
        Args: 
            - datos (dict): Datos obtenidos por telemetría. 
        Return:
            Ninguno.
        Raises:
            - Exception: Se lanza cuando no puede obtenerse el odorante a un canal asociado, definiendo un valor nulo para el parámetro de olor.

        """
       
        num_canal = datos.get("canal", -1)
        
        if num_canal >= 0:
            self.ultimos_datos_telemetria[num_canal] = dict(datos)

        if self.canal_activo is not None and num_canal == self.canal_activo.num_canal:

            try:
                olor = self.canal_activo.e_olor_canal.get()

            except Exception:
                olor = ""
            
            datos_con_hist = dict(datos)
            datos_con_hist["timestamp"] = time.time()
            datos_con_hist["olor"] = olor
            datos_con_hist["modo"] = "Protocolo" if self.protocolo_activo else "Caracterizacion" if self._caracterizacion_activo() else "Manual"
            self.historial_sesion.append(datos_con_hist)
   
            with open(self.ruta_archivo_temporal, "a", encoding="utf-8") as archivo_temporal:
                json.dump(datos_con_hist, archivo_temporal, ensure_ascii=False)
                archivo_temporal.write("\n")
                
        if self.canal_caracterizacion is not None and num_canal == self.canal_caracterizacion.num_canal:

            if self.caracterizando_flujo and not self.caracterizacion_flujo_parado:
                self.buffer_grafica_flujo[self.contador_flujo]=(datos.get("flujo", 0.0))
                self.contador_flujo += 1
                self.buffer_caracterizacion_flujo.append(datos["flujo"])

            if self.caracterizando_concentracion and not self.caracterizacion_concentracion_parado:
                self.buffer_grafica_concentracion[self.contador_concentracion]=(datos.get("concentracion", 0.0))
                self.contador_concentracion += 1
                self.buffer_caracterizacion_concentracion.append(datos["concentracion"])

            if self.caracterizando_latencia and not self.caracterizacion_latencia_parado:
                self.buffer_grafica_latencia[self.contador_latencia]=(datos.get("latencia", 0.0))
                self.contador_latencia += 1
                self.buffer_caracterizacion_latencia.append(datos["latencia"])

            if self.caracterizando_velocidad and not self.caracterizacion_velocidad_parado:
                self.buffer_grafica_velocidad[self.contador_velocidad] = (datos.get("velocidad_motor", 0.0))
                self.contador_velocidad += 1
                self.buffer_caracterizacion_velocidad.append(datos["velocidad_motor"])

        self._actualizar_latencia_estado(datos)


    def _actualizar_latencia_estado(self, datos):
        """
        Actualiza el valor del StringVarCTk asociado a la etiqueta latencia. 
        
        Args: 
            - datos (dict): Datos obtenidos por telemetría. 
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.sv_latencia_canal.set(f"{datos.get('latencia',0)} ms")
                    

    def _datos_ack(self, datos: dict):
        """
        Procesa todos aquellos datos de confirmación (ACK) provenientes del ESP32-WROOM-32U. 

        Accede a diferentes parámetros de los datos recibidos para evaluar el cumplimiento de la acción enciada. Tras la comprobación de la correcta ejecución de la 
        acción de rotación previamente enviada, extrae los argumentos y función asociados al canal donde se encuentra situada la válvula y, ejecuta la misma 
        (ya sean temporizadores de parámetros o completar la activación). Adicionalmente la lista de tuplas con las funciones callbacks pendientes es generada nuevamente 
        sin los datos de la función recientemente llamada. Por último, refleja el estado de la acción solicitada por consola al usuario.
        
        Args: 
            - datos (dict): Datos obtenidos por telemetría. 
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        accion = datos.get("ack", "desconocida")
        canal_accion = datos.get("canal", "desconocido")
        estado_accion = datos.get("ok", "desconocido")
        estado_en_cola = datos.get("en_cola", "desconocido")

        if accion == "rotar" and estado_accion is True and not estado_en_cola:

            if self.canal_esperando_posicion == canal_accion:
                self.canal_esperando_posicion = None

            funciones_callbacks = [
                (funcion, argumentos) for num_canal, funcion, argumentos in self.callbacks_pendientes_posicion_valvula
                if num_canal == canal_accion
            ]

            if funciones_callbacks:
                self.callbacks_pendientes_posicion_valvula = [
                    (num_canal, funcion, argumentos) for num_canal, funcion, argumentos in self.callbacks_pendientes_posicion_valvula
                    if num_canal != canal_accion
                ]

                for funcion, argumentos in funciones_callbacks:
                    funcion(*argumentos)

        if estado_accion == True:
            estado_accion = "correctamente"

        else: 
            estado_accion = "incorrectamente"

        if canal_accion == config.CANAL_BLANCO:
            self.consola.registro(f"[ESP32] Acción '{accion}' en canal {canal_accion} (Canal Blanco) recibida y {'en colada' if estado_en_cola else 'ejecutada'} {estado_accion}.")

        else:
            self.consola.registro(f"[ESP32] Acción '{accion}' en canal {canal_accion} ({self.cuadros_canales[int(canal_accion)].e_olor_canal.get() if self.cuadros_canales[int(canal_accion)].e_olor_canal.get() else "Sin olor definido"}) recibida y {"en colada" if estado_en_cola else "ejecutada"} {estado_accion}.")


    def _datos_log(self, datos: dict):
        """
        Procesa todos aquellos datos de log provenientes del ESP32-WROOM-32U (si los hay). 
        
        Args: 
            - datos (dict): Datos obtenidos por telemetría. 
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        nivel_mensaje = datos.get("nivel", "INFO").upper()
        mensaje = datos.get("log", "(sin contenido)")
        self.consola.registro(f"[ESP32] {mensaje}", nivel=nivel_mensaje)
    

    def _on_estado_ws(self, estado: str):
        """
        Agrega el estado de conexión WebSocket a actualizar en la cola segura. 
        
        Args: 
            - estado (str): Estado de conexión a actualizar. 
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self._cola_estado.put_nowait(estado)


    def _procesar_estado_ws(self):
        """
        Procesa y refleja el estado de la conexión WebSocket. 

        Mientras la cola del estado de conexión no esté vacía, extrae el elemento que entró el primero y comprueba el estado. Informa por consola al usuario y en caso 
        de que estuviera un protocolo o caracterización activo, intenta detener todos los canales y advertir al usuario por consola como medida de seguridad. A su vez, 
        actualiza visualmente el widget del estado de conexión correspondiente y desbloquea el botón destinado a búsqueda mediante mDNS en caso de que no haya ningún
        proceso activo. Finalmente se autoreagenda cada config.INTERVALO_SONDEO_COLAS_RECIBIDOS_ESTADO_MS milisegundos, volviendo a procesar el estado de conexión pendiente.
        
        Args: 
            Ninguno. 
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        textos = {
            "conectando":    ("◌ Conectando…",  config.COLOR_ESTADO_CONECTANDO),
            "conectado":     ("● Conectado",    config.COLOR_ESTADO_OK),
            "desconectado":  ("○ Desconectado", config.COLOR_ESTADO_DESCONECTADO),
        }

        try:

            while not self._cola_estado.empty():
                estado=self._cola_estado.get_nowait()

                if estado == "conectado":
                    self.consola.registro("Conexión establecida con el ESP32", nivel="INFO")

                elif estado == "desconectado":
                    self.consola.registro(f"Sin conexión con el ESP32. Reintentando en {config.RECONEXION_AUTOMATICA_S} s…", nivel="ERROR")

                    if (self.protocolo_activo and not self.protocolo_pausado) or self._caracterizacion_activo() or self.canal_activo is not None:
                        self.ws_client.enviar({"cmd": "parar_todos"})
                        self.consola.registro("COMPRUEBE QUE EL SISTEMA ESTÁ APAGADO. SI NO ES ASÍ, PULSE LA SETA DE EMERGENCIA.", nivel="AVISO")

                texto, color = textos.get(estado, ("○ Desconectado", "#fa8989"))
                self.after(0, lambda texto=texto, color=color: self.l_estado_conexion.configure(text=texto, text_color=color))
                bloqueo_por_proceso = (self.protocolo_activo and not self.protocolo_pausado) or self._caracterizacion_activo() or self.canal_activo is not None

                if estado in ("conectado", "desconectado", "error") and not bloqueo_por_proceso:
                    self.after(0, lambda: self.b_buscar_dispositivos.configure(state="normal"))

        finally:
            self.after(config.INTERVALO_SONDEO_COLAS_RECIBIDOS_ESTADO_MS, self._procesar_estado_ws)

# Ejecuta el main.py y por consiguiente la aplicación de control software.
if __name__ == "__main__":  
    # Instancia la calse App, y se ejecuta todo lo contenido en su constructor.
    app = App()
    # Arranca el bucle de eventos / filo principal de Tkinter.
    app.mainloop()




