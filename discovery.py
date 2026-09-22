"""
Descubre el ESP32-WROOM-32U del subsistema hardware en la red local mediante los protocolos mDNS/DNS-SD.

Implementa la función pública buscar_mdns() que busca el servicio DNS-SD definido en la constante SERVICIO_MDNS del módulo config.py en la red local.
Una vez encuentra el servicio, devuelve la URI del dispositivo según el formato ws://IP:PUERTO, donde IP es la dirección IP del ESP32-WROOM-32U y PUERTO es el puerto del servicio DNS-SD.
En caso de no ser encontrado el dispositivo, devuelve None.

Librerias externas:
    - time: Librería estándar de Python para trabajar con el tiempo y las fechas, utilizada para medir intervalos de tiempo y establecer tiempos de espera.
    - zeroconf: Librería externa para la implementación de los protocolos mDNS/DNS-SD en Python, utilizada para descubrir servicios en la red local.
    - config: Módulo propio del proyecto que centraliza la totalidad de las constantes destinadas a la configuración de la aplicación.

"""

import time
import zeroconf as zc
import config

def buscar_mdns():
    """
    Descubre el ESP32-WROOM-32U del subsistema hardware anunciado en la red local mediante el protocolo DNS-SD y resuelve la URI mediante mDNS.

    A partir de la creación de un objeto ServiceBrowser de la librería zeroconf y la clase Oyente, busca un servicio DNS-SD en la red local que coincida con el definido
    en la constante contenida en el módulo config.py SERVICIO_MDNS. La función espera un total de TIMEOUT_SEGUNDOS_MDNS segundos y comprueba si el hilo interno de zeroconf
    ha encontrado el dispositivo hasta un total de 10 veces por segundo, bloqueando brevemente el hilo que la ha llamado durante 100 milisegundos. Cuando el servicio es 
    encontrado, la función add_service de la clase Oyente se dispara de forma automática y se obtienen tanto su IP como el puerto asociado. 

    Args: 
        Ninguno.
    Return:
        f'ws://{direccion_controlador["ip"]}:{direccion_controlador["puerto"]}' (str): URI del dispositivo encontrado en la red local según el formato ws://IP:PUERTO, donde IP 
        es la dirección IP del ESP32-WROOM-32U y PUERTO es el puerto del servicio DNS-SD.
        None: Se devuelve Nulo/None si no se encuentra el dispositivo en la red local.
    Raises:
        Ninguno.

    """

    # Diccionario de la función encargado de almacenar la IP y puerto asociados al dispositivo encontrado.
    direccion_controlador = {"ip": None, "puerto" : None}

    class Oyente:
        """
        Representa el oyente necesario para la búsqueda de servicios en la red local mediante protocolo DNS-SD de Zeroconf. El motor hilo de Zeroconf
        llama a la función contenida add_service, y en caso de encontrarse un servicio coincidente al definido actualiza el diccionario externo
        direccion_controlador con la IP y puerto asociado al dispositivo encontrado mediante mDNS.

        Atributos:
            Ninguno.

        """
        
        def add_service(self, zconf, tipo, nombre):
            """
            Función callback que extrae la IP y puerto asociados de la información obtenida del dispositivo encontrado del servicio buscado.

            A partir del objeto Zeroconf que llama a la clase Oyente y el tipo de servicio y nombre del dispositivo buscado, actualiza el diccionario con la IP y puerto
            asociados del dispositivo encontrado.

            Args:
                -self: referencia a la clase Oyente.
                -zconf (Zeroconf): Objeto Zeroconf que llama a la  clase Oyente.
                -tipo (str): Tipo del servicio en búsqueda en la red local.
                -nombre (str): Nombre específico del dispositivo buscado.
            Return:
                Ninguno.
            Raises:
                Ninguno.

            """
            # Se emplea la función nativa get_service de zeroconf para buscar el servicio pasado como argumento en la red local
            info =zconf.get_service_info(tipo,nombre)

            if info:
                # Se actualizan los valores del diccionario con la IP y puerto del dispositivo encontrado.
                direccion_controlador["ip"] = info.parsed_addresses()[0]
                direccion_controlador["puerto"] = info.port


        def remove_service(self, zconf, tipo, nombre):
            """
            Función callback para eliminar un servicio. No es empleado para esta búsqueda.
            """
            pass


        def update_service(self, zconf, tipo, nombre):
            """
            Función callback para actualizar un servicio. No es empleado para esta búsqueda.
            """
            pass

    zconf = zc.Zeroconf()

    # Instanciación y definición del buscador de servicios config.SERVICIO_MDNS, con el objetivo de mantener el objeto en memoria durante la búsqueda mediante
    # DNS-SD, evitando su eliminación.
    _buscador = zc.ServiceBrowser(zconf, config.SERVICIO_MDNS, Oyente())
        
    tiempo_inicio = time.time()

    # Bucle de consulta de la búsqueda de dispositivo en la red local. Se comprueba cada 100 milisegundos si el dispositivo a sido encontrado (si el diccionario
    # ha sido actualizado con una IP). Tras 5 segundos finaliza la búsqueda DNS-SD.
    while direccion_controlador["ip"] is None and time.time() - tiempo_inicio < config.TIMEOUT_SEGUNDOS_MDNS:
        time.sleep(0.1)

    # Se detiene la búsqueda y se cierra el socket de red empleado para liberar recursos y realizar un cierre limpio de Zeroconf.
    _buscador.cancel()  
    zconf.close()

    # Se devuelve el str con la URI correspondiente del dispositivo encontrado en la red local, y devolviendo None en caso contrario.
    if direccion_controlador["ip"]:
        return f'ws://{direccion_controlador["ip"]}:{direccion_controlador["puerto"]}' 
    return None
        
