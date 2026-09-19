"""
Contiene la definición de los widgets de creación propia empleados en la creación de la GUI del software.

Define las clases reutilizables en la GUI correspondientes a los canales del olfatómetro (Canal), los objetos SpinBox para la introducción de valores por parte del usuario (SpinBoxCTk),
y la consola por donde se informa al usuario de las diferentes acciones y procesos del software (Consola). 

Clases:
    - Canal: Define el marco representativo de cada canal físico del olfatómetro. Presenta relación en la lógica de activación y desactivación de los canales
    con la clase App incluida en el módulo main.py.
    - SpinBoxCTk: Define un selector para la introducción de valores numéricos por parte del usuario.
    - Consola: Define el bloque de texto que registra y muestra por pantalla mensajes al usuario los procesos y acciones realizadas.

Librerias externas:
    - os: Librería estándar de Python para interactuar con el sistema operativo, utilizada para manejar rutas de archivos y directorios.
    - customtkinter: Librería gráfica actualizada basada en la librería estándar de Python tkinter.
    - CTkToolTip: Librería externa de Python empleada para generar ventanas emergente de ayuda.
    - datetime: Módulo integrado en Python para el empleo de fechas y horas en el código.
    - logging: Módulo nativo de Python para el registro de eventos, errores y mensajes informativos para el usuario.
    - config: Módulo propio del proyecto que centraliza la totalidad de las constantes destinadas a la configuración de la aplicación.

"""

import os
import customtkinter as ctk 
from CTkToolTip import CTkToolTip
import datetime
import logging
import config



class Canal(ctk.CTkFrame):
    """
    Es la representación visual y controlador lógico de un canal físico del olfatómetro diseñado dentro del software. 

    Se encuentra contenido en un Frame, englobando objetos CTkButton, CTkTextbox, CTkLabel y CTkStringVar; dando como resultado el marco representativo de
    cada canal. La función de controlador es realizada sobre los procesos de activación y desactivación del propio canal, requiriendo de las funciones de
    "activar_canal" y "confirmar_activacion" para el envío del comando de rotación y activación de la fuente de aire al ESP32-WROOM-32U. Y por otro lado, la
    función "parar_canal", completando la desactivación y deteniendo la fuente de aire mediante un comando al ESP32-WROOM-32U.

    Atributos (de instancia):
        - color_canal (str): Color del canal correspondiente a representar.
        - num_canal (int): Número identificador del canal correspondiente a representar.
        - actualizar_canal (callback), (opcional): Callback de la función actualizar_canales del módulo main.py, para el envío de comandos y notificación al resto de la App.
        - registro (callback), (opcional): Callback del objeto Consola para informar por pantalla al usuario.
        - after__cronometro (str): Identificador del proceso after pendiente correspondiente al cronómetro.
        - estado_canal (booleano): Bandera para reflejar el estado activo de un canal.
        - _tiempo_inicial_pendiente (time.time): Almacena el tiempo exacto al iniciar el proceso de activación de un canal y emplearlo posteriormente para el 
         cálculo del cronómetro en "confirmar_activacion".

    """

    def __init__(self, master, color_canal, num_canal, registro=None, actualizar_canal=None):
        """
        Método constructor encargado de definir e inicializar todo objeto Canal.
        
        Args: 
            - master: referencia al contenedor Frame del marco de representativo de cada Canal.
            - resto de atributos de instancia ya mencionados en el comentario de la clase Canal.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        super().__init__(master, fg_color="#343638", border_color="#4a4c4e", border_width=1, corner_radius=10)
        """
        Constructor heredado del objeto nativo de CustomTkinter CTkFrame, encargado de definir e inicializar el objeto FrameCTk que contiene el marco
        representativo de cada canal

        Args: 
            - master: referencia a la ventana principal del software desarrollado.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """
        self.color_canal = color_canal
        self.num_canal = num_canal
        self.actualizar_canal = actualizar_canal
        self.registro = registro
        self.after__cronometro = None
        self.estado_canal= False
        self._tiempo_inicial_pendiente = None

        # Llamamiento a la función _crear_canal para la creación visual automática del widget Canal en la GUI del software.
        self._crear_canal()


    def _crear_canal(self):
        """
        Creación del widget visual de la clase Canal representativa de un canal físico del olfatómetro.

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

        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((0,1), weight=1)
        
        self.l_color_canal = ctk.CTkLabel(self, text=f"Canal {self.color_canal}", font=ctk.CTkFont(size=20, weight="bold"))
        self.l_color_canal.grid(row=0, column=0, padx=(10,5), pady=10, sticky="w")

        self.e_olor_canal = ctk.CTkEntry(self, placeholder_text="Olor del canal", font=ctk.CTkFont(size=20), width=200)
        self.e_olor_canal.grid(row=0, column=1, padx=10, pady=10, sticky="e")
        CTkToolTip(self.e_olor_canal, message="Introduce el nombre del olor que se va a utilizar en este canal.\nEste nombre se mostrará en los informes de sesión.", delay=0.5, justify="left", wraplength=300)

        self.sv_tiempo_activo=ctk.StringVar(value="Tiempo activo: 00:00:00") 
        self.l_tiempo_act_canal = ctk.CTkLabel(self, textvariable= self.sv_tiempo_activo, font=ctk.CTkFont(size=14))
        self.l_tiempo_act_canal.grid(row=2, column=0, padx=10, pady=(10,5), sticky="wn")

        self.b_activar_canal = ctk.CTkButton(self, text="Activar", fg_color="#85ad75",text_color="#ffffff", 
                                             hover_color="#488f51",corner_radius=10,border_color="#006400",border_width=1,
                                             font=ctk.CTkFont(size=16, weight="bold"), command=self.activar_canal)
        self.b_activar_canal.grid(row=5, column=0, padx=10, pady=(5,10), sticky="w")
        CTkToolTip(self.b_activar_canal, message="Haz clic para activar el canal.", delay=0.5, justify="left", wraplength=300)

        self.b_parar_canal = ctk.CTkButton(self, text="Parar", fg_color="#f56a6a",text_color="#ffffff",
                                             hover_color="#ee4242",corner_radius=10,border_color="#ff0000",border_width=1,
                                             font=ctk.CTkFont(size=16, weight="bold"), command=self.parar_canal)
        self.b_parar_canal.grid(row=5, column=1, padx=10, pady=(5,10), sticky="e")
        CTkToolTip(self.b_parar_canal, message="Haz clic para detener el canal.", delay=0.5, justify="left", wraplength=300)


    def _cronometro(self,tiempo):
        """
        Representa y actualiza el tiempo activo del canal correspondiente.

        Args: 
            - tiempo (time.time): Duración de la activación a representar en el marco de cada canal y actualizado cada segundo activo.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """
        
        if self.estado_canal:
            self.sv_tiempo_activo.set(f"Tiempo activo: {tiempo.strftime('%H:%M:%S')}")
            self.after__cronometro = self.after(1000, lambda: self._cronometro(tiempo + datetime.timedelta(seconds=1)))


    def resetear__cronometro(self):
        """
        Reinicia el temporizador del tiempo activo del canal correspondiente.

        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.sv_tiempo_activo.set("Tiempo activo: 00:00:00")


    def pausar__cronometro(self):
        """
        Pausa el cronómetro representativo del tiempo activo del canal correspondiente.

        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        if self.after__cronometro:
            self.after_cancel(self.after__cronometro)
            self.after__cronometro = None
        

    def activar_canal(self,tiempo_inicial=datetime.datetime.strptime("00:00:00", "%H:%M:%S")):
        """
        Comienza el proceso de activación del canal correspondiente.

        Actualiza la bandera de estado del respectivo canal a activo, registra el tiempo inicial de la activación y llama a la función callback
        para desencadenar el proceso de activación en el módulo main.py.

        Args: 
            - tiempo_inicial (time.time), (opcional): Establecido por defecto como "00:00:00", es el tiempo desde el cual comienza el tiempo activo representado
            por el cronómetro del marco del canal. 
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        if not self.estado_canal:
            self.estado_canal=True
            self._tiempo_inicial_pendiente = tiempo_inicial
            if self.actualizar_canal:
                self.actualizar_canal(self.num_canal,"activar")


    def confirmar_activacion(self):
        """
        Completa el proceso de activación iniciado por "activar_canal" del canal correspondiente.

        Tras el mensaje ACK recibido por parte del ESP32-WROOM-32 tras la rotación a la posición asociada al canal a activar, comienza el cronómetro de
        tiempo activo con el tiempo inicial almacenado con anterioridad y actualiza visualmente el marco del widget del respectivo canal.

        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        if self.estado_canal:
            self._cronometro(self._tiempo_inicial_pendiente)
            self.configure(fg_color="#256F2F", border_color="#7DEB7D", border_width=4)  # Cambia el fondo del canal para indicar que está activo
            self.b_activar_canal.configure(text="En marcha", fg_color="#70c64e",text_color="#ffffff",border_color="#006400",border_width=1,font=ctk.CTkFont(size=14, weight="bold"))
            if self.registro:
                self.registro(f"Canal {self.color_canal} ({self.e_olor_canal.get()}) ACTIVADO")


    def parar_canal(self):
        """
        Detiene el canal activo correspondiente.

        El el único responsable de detener el canal previamente activado. Actualiza la bandera del respectivo canal a desactivado y actualiza visualmente
        el marco del widget Canal a su estado de reposo. Por último llama a la función callback para notificar al resto del software y enviar el comando de 
        parada al ESP32-WROOM-32U.

        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """
    
        if self.estado_canal:
            self.estado_canal=False
            self.pausar__cronometro()

            self.configure(fg_color="#343638", border_color="#4a4c4e", border_width=1)
            self.b_activar_canal.configure(text="Activar", fg_color="#85ad75",text_color="#ffffff",border_color="#006400",border_width=1,
                font=ctk.CTkFont(size=14, weight="bold"))
            
            if self.registro:
                olor = self.e_olor_canal.get() if self.e_olor_canal.winfo_exists() else ""
                self.registro(f"Canal {self.color_canal} ({olor}) DETENIDO")
            
            if self.actualizar_canal:
                self.actualizar_canal(self.num_canal,"parar")

        # Código correspondiente al cálculo temporal de actualización y proceso de detener un canal activo - Empleado en la evaluación de la solución.
        #self.update_idletasks()
        #diferencia_temporal = time.perf_counter() - self.t0_actualizacion_para_canal
        #self.t0_actualizacion_para_canal = 0
        #print(f"Tiempo de actualización de la UI al parar canal: {diferencia_temporal} segundos")
        #return diferencia_temporal



class SpinboxCTk(ctk.CTkFrame):
    """
    Representa el widget correspondiente a un selector numérico, permitiendo la introducción de valores numéricos por parte del usuario.

    Atributos (de instancia):
        - valor_min: Valor mínimo posible del selector numérico.
        - valor_max: Valor máximo posible del selector numérico.
        - escalon: Unidad de incremento y decremento entre niveles del selector  numérico. 
        - valor: Valor numérico contenido del selector. Presenta un valor de 120 unidades por defecto.

    """

    def __init__(self, master, valor=120,valor_min=0, valor_max=9999999, escalon=1
                 , border_width=0, corner_radius=10, width=120, height=30):
        """
        Método constructor encargado de definir e inicializar todo objeto SpinBoxCTk.
        
        Args: 
            - master: referencia al contenedor Frame donde se ubican los objetos que conforman SpinBoxCTk.
            - resto de atributos de instacia ya mencionados en el comentario de la clase SpinBoxCTk.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        super().__init__(master, fg_color = "#242424",width=width, height=height, border_width=border_width, corner_radius=corner_radius)
        """
        Constructor heredado del objeto nativo de CustomTkinter CTkFrame, encargado de definir e inicializar el objeto FrameCTk que contiene el 
        objeto SpinBoxCTk creado.

        Args: 
            - master: referencia a la ventana principal del software desarrollado.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.valor_min = valor_min
        self.valor_max = valor_max
        self.escalon = escalon
        self.valor = ctk.StringVar(value=valor)

        # Llamamiento a la función _crear_spinboxCTk para la creación visual automática del widget SpinBoxCTk en la GUI del software.
        self._crear_spinboxCTk()


    def _crear_spinboxCTk(self):
        """
        Creación del widget visual de la clase SpinBoxCTk representativa de los selectores numéricos del software.

        Atributos (de instancia):
            - f_spinbox (CTkFrame): Contenedor gráfico de los objetos que conforman el selector numérico.
            - b_decrementar (CTkButton): Botón encargado de decrementar escalón a escalón el valor numérico contenido en el selector.
            - e_spinbox (CTkEntry): Bloque de texto que recoge el valor numérico introducido por el usuario en el selector.
            - b_incrementar (CTkButton): Botón encargado de incrementar escalón a escalón el valor numérico contenido en el selector.

        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        f_spinbox = ctk.CTkFrame(self,fg_color="#242424", bg_color="#242424")
        f_spinbox.grid_columnconfigure((0,2),weight=0)
        f_spinbox.grid_columnconfigure(1,weight=0)
        f_spinbox.grid(row=0, column=0, sticky="w", padx=10, pady=10,)

        self.b_decrementar = ctk.CTkButton(f_spinbox,bg_color="#242424",fg_color="#0a5f70", text="-", width=30, command=self.decrementar,font=ctk.CTkFont(size=14, weight="bold"),border_color="#0a5f70", border_width=1)
        self.b_decrementar.grid(row=0,column=0, padx=5, pady=5, sticky="w")

        self.e_spinbox = ctk.CTkEntry(f_spinbox,bg_color="#242424", fg_color="#242424", textvariable=self.valor, font=ctk.CTkFont(size=14))
        self.e_spinbox.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.b_incrementar = ctk.CTkButton(f_spinbox, bg_color="#242424", fg_color="#0a5f70",text="+", width=30, command=self.incrementar,font=ctk.CTkFont(size=14, weight="bold"),border_color="#0a5f70", border_width=1)
        self.b_incrementar.grid(row=0,column=2, padx=5, pady=5, sticky="e")


    def incrementar(self):
        """
        Incrementa el valor contenido en el selector numérico en una unidad del escalón definido.

        Trata de la consulta del valor actual contenido en el selector convirtiéndolo mediante un hash en entero, actualiza el mismo sumando el valor definido por el 
        escalón respetando el límite máximo impuesto. En caso de error se limita a no actualizar ni definir el valor, sin realizar modificación ni ejecución alguna.

        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            - ValueError: En caso de que el valor contenido en el objeto SpinBoxCTk no pueda ser convertido a un entero.

        """
        
        try:
            valor_actual = int(self.valor.get())
            valor_final = valor_actual + self.escalon
            if valor_final <= self.valor_max:
                self.valor.set(valor_final)

        except ValueError:
                pass


    def decrementar(self):
        """
        Decrementa el valor contenido en el selector numérico en una unidad del escalón definido.

        Trata de la consulta del valor actual contenido en el selector convirtiéndolo mediante un hash en entero, actualiza el mismo restando el valor definido por 
        el escalón respetando el límite mínimo impuesto. En caso de error se limita a no actualizar ni definir el valor, sin realizar modificación ni ejecución alguna.

        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            - ValueError: En caso de que el valor contenido en el objeto SpinBoxCTk no pueda ser convertido a un entero.

        """

        try:
            valor_actual = int(self.valor.get())
            valor_final = valor_actual - self.escalon
            if valor_final >= self.valor_min:
                self.valor.set(valor_final)

        except ValueError:
                pass
    
    def get(self):
        """
        Consulta el valor numérico actual del selector numérico, empleado la función get y convirtiéndolo mediante un hash el texto introducido por el usuario. 

        Trata de la consulta del valor actual contenido en el selector y convertirlo mediante hash en un entero.
        En caso de error se limita a devolver el valor numérico correspondiente al límite mínimo.

        Args: 
            Ninguno.
        Return:
            - int(self.valor.get()): Convierte el texto contenido en el selector en un entero si no se da ningún error.
            - self.valor_min: Valor numérico establecido como límite mínimo del selector.
        Raises:
            - ValueError: En caso de que el valor contenido en el objeto SpinBoxCTk no pueda ser convertido a un entero

        """

        try:
            return int(self.valor.get())
        
        except ValueError:
            return self.valor_min

        
    def set(self, valor):
        """
        Establece el valor numérico pasado en el selector numérico ¡. 

        Emplea la función set y trata de convertir el valor pasado como argumento mediante hash, para definir el valor contenido en el selector numérico
        del SpinBoxCTk.

        Args: 
            Ninguno.
        Return:
            - int(self.valor.get()) (int): Convierte el texto contenido en el selector en un entero si no se da ningún error.
            - self.valor_min (int): Valor numérico establecido como límite mínimo del selector.
        Raises:
            - ValueError: En caso de que el valor contenido en el objeto SpinBoxCTk no pueda ser convertido a un entero

        """
        self.valor.set(int(valor)) 


        
class Consola(ctk.CTkTextbox):
    """
    Representa el widget correspondiente a la consola logger del software desarrollado como bloque de texto, informando de todo proceso y acción al usuario.

    Atributos (de instancia):
        - logger: Logger obtenido o creado con nombre concreto para el muestreo de mensajes por consola al usuario.
        - ruta_log_consola: Ruta para el almacenamiento temporal del historial de log presentados al usuario por consola.

    """

    def __init__(self, master):
        """
        Método constructor encargado de definir e inicializar todo objeto Consola.
        
        Args: 
            - master: referencia a la clase CTkTextbox donde se ubican y hereda el objeto Consola.
            - resto de atributos de instancia ya mencionados en el comentario de la clase Consola.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        super().__init__(master)
        """
        Constructor heredado del objeto nativo de CustomTkinter CTkTextbox, encargado de definir e inicializar el objeto CTkTextbox que contiene el 
        objeto Consola.

        Args: 
            - master: referencia a la ventana principal del software desarrollado.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.logger = logging.getLogger("olfametric.consola")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  

        self.ruta_log_consola = os.path.join(config.DIRECTORIO_ARCHIVOS_TEMPORALES, "historial_consola.log")

        # Se establece el modo escritura en la ruta del archivo temporal con el historial log, para el continuo registro de mensajes.
        with open(self.ruta_log_consola, "w", encoding = "utf-8"):
            pass

        # En caso de no existir el listado de manejadores de salida del logger creado, se crea archivo temporal con el historial de log como manejador en la ruta predefinida 
        # para añadiendo contenido.
        if not self.logger.handlers:
            archivo_handler = logging.FileHandler(os.path.join(config.DIRECTORIO_ARCHIVOS_TEMPORALES, "historial_consola.log"), mode="a", encoding="utf-8")
            self.logger.addHandler(archivo_handler)

        # Llamamiento a la función _crear_consola para la creación visual automática del widget Consola en la GUI del software.
        self._crear_consola()
        

    def _crear_consola(self):
        """
        Creación del widget visual de la clase Consola representativa del logger del software desarrollado.

        Atributos (de instancia):
            - t_registro (CTkTextbox): Bloque de texto que contiene el objeto Consola empleado como logger. 

        Args: 
            Ninguno.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Consola", text_color="#0f7780", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, padx=5, pady=(5,5), sticky="nw")

        self.t_registro=ctk.CTkTextbox(self, width=1000, height=150, font=ctk.CTkFont(size=14),)
        self.t_registro.grid(row=1, column=0, padx=10, pady=(10,5), sticky="nsew")


    def registro(self, mensaje, nivel="INFO"):
        """
        Muestra por pantalla y registra en el archivo temporal con el historial el mensaje pasado como argumento.

        Construye el mensaje final mostrado por pantalla agregando la hora actual al mensaje pasado asociándole un nivel especifico. Registra el mensaje por consola y registra
        el mismo, en el archivo temporal con el historial del resto de logs.


        Args: 
            - mensaje (str): Mensaje a mostrar por el objeto Consola al usuario y registrar en el archivo temporal.
            - nivel (str), (opcional): Nivel del mensaje pasado. Se establece como INFO por defecto.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        hora = datetime.datetime.now().strftime("%H:%M:%S")
        mensaje_final = f"{hora}- {nivel}- {mensaje}\n"
        self.t_registro.insert(index="end", text=mensaje_final)
        self.t_registro.see("end")

        if nivel.upper() == 'AVISO':
            nivel_logging = logging.WARNING

        else:
            nivel_logging = getattr(logging, nivel.upper(), logging.INFO)
        
        self.logger.log(nivel_logging, mensaje_final)

