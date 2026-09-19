"""
Descubre el ESP32-WROOM-32U del subsistema hardware en la red local mediante el protocolo mDNS.

Implementa la función pública buscar_mdns() que busca el servicio mDNS definido en la constante SERVICIO_MDNS del módulo config.py en la red local. 
Una vez encuentra el servicio, devuelve la URI del dispositivo según el formato ws://IP:PUERTO, donde IP es la dirección IP del ESP32-WROOM-32U y PUERTO es el puerto del servicio mDNS.
En caso de no ser encontrado el dispositivo, devuelve None.

Librerias externas:
    - asyncio: Librería nativa de Python para trabajar de forma concurrente en el código.
    - websockets: Librería de Python empleada para la construcción de servidores y clientes WebSocket, de forma sencilla y robusta. 
    - json: Librería nativa de Python que permite codificar y decodificar datos en formato JSON.
    - threading: Librería nativa de Python que permite trabajar de forma concurrente mediante el uso de hilos.
    - time: Librería estándar de Python para trabajar con el tiempo y las fechas, utilizada para medir intervalos de tiempo y establecer tiempos de espera.
    - queue: Librería nativa de Python para manejar colas de forma segura trabajando en programas multihilos.
    - typing: Librería nativa de Python empleada para declarar los tipos de datos esperados en variables. 
    - config: Módulo propio del proyecto que centraliza la totalidad de las constantes destinadas a la configuración de la aplicación.

"""

import asyncio
import websockets
import json
import threading
import time
import queue
from typing import Callable, Optional
import config


class WSClient:
    """
    Representa el nodo cliente de la conexión WebSocket establecida entre ESP32-WROOM-32U 

    Atributos (de instancia):
        - uri: Dirección IP y puerto del dispositivo.
        - _on_estado: Callback para actualizar el estado de conexión en el widget correspondiente.
        - _reconectar: Tiempo en segundo entre reintentos de conexión automática.
        - _cola_envio: Cola segura para el envío de datos pendientes a ESP32-WROOM-32U.
        - _cola_recibidos: Cola segura de los mensajes recibidos del ESP32-WROOM-32U pendientes de envío a la App.
        - _loop: Bucle de eventos asíncrono donde corre la conexión WebSocket.
        - _hilo: Hilo de ejecución donde tiene lugar el bucle de eventos asíncrono.
        - _tarea_principal: Identificador de la tarea asíncrona ejecutada en un momento dado.
        - _activo: Bandera que refleja la activación o inactivación del hilo de fondo creado.
        - conectado: Bandera para reflejar la existencia de conexión entre Cliente (software) y Servidor (ESP32-WROOM-32U).

    """

    def __init__(
        self,
        uri:           str,
        on_estado:     Callable[[str], None],
        reconectar_s:  float = config.RECONEXION_AUTOMATICA_S,
    ):
        """
        Método constructor encargado de definir e inicializar todo objeto WSClient.
        
        Args: 
            - master: referencia al contenedor Frame del marco de representativo de cada WSClient.
            - resto de atributos de instancia ya mencionados en el comentario de la clase WSClient.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self._ws = None
        self.uri = uri
        self._on_estado = on_estado
        self._reconectar = reconectar_s

        self._cola_envio: queue.Queue = queue.Queue()   
        self._cola_recibidos: queue.Queue = queue.Queue()   
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._hilo: Optional[threading.Thread] = None
        self._tarea_principal: Optional[asyncio.Task] = None 
                                                                    
        self._activo = False
        self.conectado = False


    def iniciar(self):
        """
        Inicia el hilo de fondo asíncrono para la conexión WebSocket.

        Crea el hilo de ejecución asíncrono de fondo y define el estado activo del hilo (mediante la actualización de la respectiva bandera).
        En caso de que el hilo principal de Tkinter finalice su actividad, el hilo de fondo encargado de la conexión será cerrado automáticamente debido a la
        condición daemon.  

        Args:
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self._activo = True
        self._hilo   = threading.Thread(target=self._ejecutar_loop, daemon=True)
        self._hilo.start()


    def detener(self):
        """
        Detiene el hilo de fondo asíncrono encargado de la conexión WebSocket establecida entre software y ESP32-WROOM-32U.

        Actualiza la lógica de banderas a un estado inactivo del hilo asíncrono de fondo. Cierra el hilo de fondo y la corrutina en ejecución (ya sea una conexión establecida,
        un intento de conexión o en espera entre reintentos) en caso de que existan. Tras la solicitud de cierre del hilo asíncrono de fondo, se espera config.TIMEOUT_CIERRE_HILO_S
        para la finalización del mismo antes de volver a retomar el control, impidiendo la creación de un posible segundo hilo que compitiera por los mismos recursos.

        Args:
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self._activo = False
        self.conectado = False

        if self._loop and self._loop.is_running():
            
            if self._ws:
                asyncio.run_coroutine_threadsafe(self._ws.close(), self._loop)

            if self._tarea_principal and not self._tarea_principal.done():
                self._loop.call_soon_threadsafe(self._tarea_principal.cancel)

        if self._hilo and self._hilo.is_alive():
            self._hilo.join(timeout=config.TIMEOUT_CIERRE_HILO_S)


    def enviar(self, datos: dict):
        """
        Agrega un mensaje pasado como argumento a la cola de envíos pendientes al ESP32-WROOM-32U.

        Actualiza la cola de envíos pendientes por parte del software al ESP32-WROOM-32U, codificando el mensaje pasado como argumento en forma de diccionario, en un string
        JSON. El hilo principal de Tkinter puede llamar el método al emplear colas seguras como estructura de almacenamiento de mensajes.

        Args:
            - datos (dict): Diccionario con la información pendiente de enviar al ESP32-WROON-32U.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self._cola_envio.put_nowait(json.dumps(datos))


    def _ejecutar_loop(self):
        """
        Crea el bucle de eventos asíncrono empleado en el conexión WebSocket y lo asigna al hilo de fondo previamente creado.

        Tras la creación del bucle asíncrono de eventos, se le asigna la corrutina correspondiente. Ejecutándose de forma indefinida hasta que sea completa, 
        ya sea de forma natural (durante el intento de conexión o el tiempo entre reintentos) o mediante la cancelación forzosa al detener la conexión WebSocket.
        Cuando la tarea principal concurrente termina se elimina la referencia de la misma y se procede al cierre del bucle de eventos asíncrono empleado.

        Args:
            Ninguno.
        Return:
            Ninguno.
        Raises:
            - asyncio.CancelledError: Se dispara en el momento que se cancela la corrutina ejecutada en ese momento (_tarea_principal) al detener la conexión WebSocket.
            No realiza o ejecuta ninguna medida para la gestión del error, se limita a ignorar el error.

        """

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._tarea_principal = self._loop.create_task(self._ciclo_conexion())

        try:
            self._loop.run_until_complete(self._tarea_principal)

        except asyncio.CancelledError:
            pass

        finally:
            self._tarea_principal = None
            self._loop.close()


    async def _ciclo_conexion(self):
        """
        Bucle asíncrono indefinido que trata de conectar y organizar el intercambio de mensajes entre el software y el ESP32-WROON-32U.

        Actualiza el estado del widget de conexión a "conectando...", en el intento de una conexión WebSocket mediante la uri pasada como argumento al definir el objeto 
        WSClient. Para el establecimiento de conexión de plantea un máximo de config.OPEN_TIMEOUT_S para establecer el handshake entre cliente y servidor. Un vez establecida 
        se comprueba cada config.PING_INTERVAL_S el estado de conexión, en caso de no responder al primer ping se espera durante config.PING_TIMEOUT_S para dar por
        perdida la conexión. La conexión WebSocket actualiza el widget de estado y variables globales correspondientes, además de ejecutar concurrentemente las corrutinas 
        de enviar y recibir datos hasta que finalicen. En caso de que se cayera la conexión o se fuerce la detención de la conexión se actualizarían los variables globales 
        correspondientes, y se volvería a intentar el establecimiento de conexión _reconectar (config.RECONEXION_AUTOMATICA_S) segundos.

        Args:
            Ninguno.
        Return:
            Ninguno.
        Raises:
            - Exception: Se lanza ante un fallo en el intento o pérdida de conexión. Además de captura cualquier fallo proveniente de métodos llamados dentro del bloque
            try (_recibir). Estableciendo el estado de desconexión tanto a nivel lógico como visual.

        """

        while self._activo:
            self._on_estado("conectando")

            try:
                async with websockets.connect(self.uri, ping_interval=config.PING_INTERVAL_S, ping_timeout=config.PING_TIMEOUT_S, open_timeout=config.OPEN_TIMEOUT_S) as ws:
                    self._ws = ws
                    self.conectado = True
                    self._on_estado("conectado")
                    
                    await asyncio.gather(
                        self._recibir(ws),
                        self._enviar(ws),
                    )

            except Exception:
                self.conectado = False
                self._on_estado("desconectado")

            finally:
                self._ws = None

            if self._activo:
                await asyncio.sleep(self._reconectar)


    async def _recibir(self, ws):
        """
        Corrutina encargada de registrar los mensajes entrantes del ESP32-WROOM-32U.

        Por cada mensaje recibido de forma asíncrona del ESP32-WROOM-32U, deserializa la información contenida en del texto json y agrega el cálculo de la 
        latencia en la conexión en un diccionario Python, agregando el diccionario creado a la cola segura de datos recibidos pendientes de ser procesados por
        el hilo principal de Tkinter.

        Args:
            - ws (ClientConnection): conexión WebSocket realizada entre ESP32-WROOM-32U y software. 
        Return:
            Ninguno.
        Raises:
            - json.JSONDecodeError: Captura cualquier error producido durante la deserialización de los mensajes recibidos, descartando el mensaje problemático y 
            pasando al siguiente.

        """

        async for mensaje in ws:

            try:
                datos = json.loads(mensaje)
                datos["latencia"] = await self.calcular_latencia(ws)
                self._cola_recibidos.put_nowait(datos)

            except json.JSONDecodeError:
                pass
                

    async def _enviar(self, ws):
        """
        Corrutina encargada de enviar los mensajes generados por el software al ESP32-WROOM-32U.

        Tras config.INTERVALO_SONDEO_COLA_ENVIO_S segundos de espera no bloqueante, consume la cola de envíos pendientes generada por el hilo principal de Tkinter y
        envía el mensaje a través de la conexión WebSocket existente al nodo servidor. 

        Args:
            - ws (ClientConnection): conexión WebSocket realizada entre ESP32-WROOM-32U y software. 
        Return:
            Ninguno.
        Raises:
            - websockets.ConnectionClosed: Tiene lugar en el momento que se cierra la conexión WebSocket (por cualquier motivo relacionado), impidiendo el envío de mensajes al 
            ESP32-WROOM-32U. Provoca la salida de la misma función y deja gestionar la situación a funciones de major jerarquía, volviendo al intento de reconexión.
            - Exception: Captura cualquier error alternativo que tenga lugar en el procesado del envío de mensaje, ignorando el error y pasando al siguiente.

        """

        while True:
            await asyncio.sleep(config.INTERVALO_SONDEO_COLA_ENVIO_S)
            while not self._cola_envio.empty():

                try:
                    msg = self._cola_envio.get_nowait()
                    await ws.send(msg)

                except websockets.ConnectionClosed:
                    return
                
                except Exception:
                    pass
                    

    async def calcular_latencia(self, ws):
        """
        Corrutina encargada del cálculo de la latencia presente entre Cliente (software) y Servidor (ESP32-WROOM-32U) en la conexión WebSocket.

        Se registra el tiempo inicial en el que se envía el mensaje Ping y se espera a que se reciba una respuesta por parte del Servidor de la conexión WebSocket.
        Tras recibir respuesta, se registra el tiempo en el que el mensaje complementario Pong es recibido, y se calcula el tiempo transcurrido entre ambos registros.   

        Args:
            - ws (ClientConnection): conexión WebSocket realizada entre ESP32-WROOM-32U y software. 
        Return:
            - round((tiempo_pong - tiempo_ping)*1000,1) (float): Tiempo transcurrido entre Ping-Pong redondeado a decimales.
        Raises:
            Ninguno.

        """

        tiempo_ping = time.perf_counter()
        espera_pong = await ws.ping()
        await espera_pong
        tiempo_pong = time.perf_counter()
        
        return round((tiempo_pong - tiempo_ping)*1000,1)
