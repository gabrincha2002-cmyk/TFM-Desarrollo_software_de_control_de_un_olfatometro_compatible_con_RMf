"""
Genera, define y configura los informes de la sesión experimental realizada en los formatos de interés.

El módulo engloba un total de tres funciones principales, destinadas cada una de las mismas a generar y configurar un formato de interés (.csv, .pdf y .xlsx). Adicionalmente 
define la dataclass DatosInformes, para el almacenamiento de datos estructurados en el módulo main.py y la generación de los diferentes informes. Por último, también
incluye métodos para el cálculo métricas y conversión de datos provenientes de la caracterización realizada en los informes.


Librerías externas:
    - dataclasses: Librería nativa de Python destinada a la creación de clases para ekl almacenamiento de datos.
    - datetime: Módulo nativo de Python empleado en la manipulación y operación de fechas y horas.
    - statistics: Módulo nativo de Python que posibilita realizar operaciones sobre datos numéricos.
    - reportlab: Librería de Python que permite la creación y generación de archivos .pdf.
    - openpyxl: Librería de Python que permite leer y escribir de archivos .xlsx y .xlsm.
    - matplotlib: Librería nativa de Python que permite la creación de gráficos 2D y 3D.
    - config: Módulo propio del proyecto que centraliza la totalidad de las constantes destinadas a la configuración de la aplicación.
    - tempfile: Librería nativa de Python que permite la creación de archivos y directorios temporales.
    - os: Librería estándar de Python para interactuar con el sistema operativo, utilizada para manejar rutas de archivos y directorios.
    - csv: Librería de Python que permite leer y escribir archivos de formato .csv y .tsv.

"""

from dataclasses import dataclass
import datetime
import statistics
import config
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import matplotlib.pyplot as plt
import tempfile
import os
import csv



@dataclass
class DatosInforme:
    """
    Dataclass destinada al almacenamiento de datos para la generación de informes. 

    Almacena los datos generados por del software y provenientes del ESP32-WROOM-32U. Los datos almacenados se distribuyen en: metadatos de sesión, configuración 
    de protocolo y datos de la sesión experimental realizada.

    Atributos (de instancia):
        - id_sesion (str): Número de identificación de la sesión experimental.
        - id_paciente (str): Número de identificación del paciente.
        - duracion_sesion (str): Duración de la sesión experimental.
        - tiempo_inicio_sesion (float): Tiempo en el que inició la sesión.
        - num_ciclos (str): Número de ciclos del protocolo.
        - tiempo_exposicion (str): Tiempo de exposición del odorante de cada canal.
        - tiempo_desensibilizacion (str): Tiempo de desensibilización  del paciente y limpieza de canal con odorante.
        - intervalo_ciclos (str): Tiempo entre cada ciclo de un protocolo.
        - tiempo_caracterizacion (str): Tiempo de caracterización de parámetros de interés.
        - historial_sesion (list[dict]): Historial completo de los datos obtenidos en una sesión experimental.
        - historial_caracterizacion (dict[int, dict]): Historial de caracterización de parámetros por cada canal.
        - colores_canales (list[str]): Colores asociados a cada canal.

    """

    # Metadatos de sesión.
    id_sesion: str
    id_paciente: str
    duracion_sesion: str
    tiempo_inicio_sesion: float

    # Configuración  del protocolo. 
    num_ciclos: str
    tiempo_exposicion: str
    tiempo_desensibilizacion: str
    intervalo_ciclos: str
    tiempo_caracterizacion: str

    # Datos sesión experimental.
    historial_sesion: list[dict] 
    historial_caracterizacion: dict[int, dict]
    colores_canales: list[str]


def _media(lista):
    """
    Calcula el promedio de un conjunto de datos numéricos.

    Comprueba el tipo de los datos almacenados en la lista pasada mediante condicionales, y calcula la media aritmética del conjunto.
    En caso de que la lista sea un único dato numérico, ya sea entero o con decimales, lo devuelve tal cual.
        
    Args: 
        - lista (list[int/float] o int/float): Lista de datos sobre la que iterar o valores numéricos para hacer media aritmética.
    Return:
        - lista (int/float): El mismo valor numérico pasado como argumento.
        - statistics.mean(seq) (int/float): Promedio de los valores numéricos contenidos en la lista pasada.
        - 0: Se devuelve el valor numérico 0, en caso de que la lista contenga strings, sea Nulo o no contenga datos.
    Raises:
        - TypeError: En caso de que la lista o el valor pasado no sea iterable o contenga valores no numéricos.

    """

    try:
        if lista is None:
            return 0
        
        if isinstance(lista, (int, float)):
            return lista
        
        if isinstance(lista, str):
            return 0
        
        seq = list(lista)
        return statistics.mean(seq) if seq else 0
    
    except TypeError:
        return 0 


def _calculo_max_min(lista):
    """
    Calcula el máximo y mínimo del conjunto de valores numéricos contenidos en la lista pasada.

    En el caso de que la lista pasada sea un valor nulo o vacío se devuelve un valor numérico de ceros. Se intenta calcular el máximo y mínimo contenidos en la lista
    , en caso de que un error tuviera lugar se recoge la excepción y se devuelve el mismo valor numérico mencionado.
        
    Args: 
        - lista (list[int/float] o int/float): Lista de datos sobre la que iterar o valores numéricos para el cálculo de máximo y mínimo.
    Return:
        - max(lista) (int/float), min(lista) (int/float): Máximo y mínimo encontrados en el conjunto pasado.
        - 0,0: Ceros como máximo y mínimo del conjunto. 
    Raises:
        - TypeError, ValueError: En caso de que la lista o el valor pasado no sea iterable, contenga valores no numéricos o se encuentre vacío (para casos puntuales).

    """

    if not lista:
        return 0,0
    
    try:
        return max(lista), min(lista)
    
    except (TypeError, ValueError):
        return 0,0


def _conversor_list_muestras_caracterizacion(datos: DatosInforme):
    """
    Convierte los datos obtenidos en la caracterización en un formato compatible para la generación de informes.

    A partir de los datos pasados como argumento, genera un diccionario de los datos obtenidos durante la caracterización con la misma estructura que los datos 
    generados en el historial de sesión. Extrae las métricas contenidas en la dataclass y las almacena en diferentes listas para la generación del correspondiente
    diccionario.
        
    Args: 
        - datos (DatosInforme): Dataclass con los datos generados en la sesión experimental.
    Return:
        - muestras_caracterizacion (list[dict]): Listado con los datos de caracterización de la sesión experimental.
    Raises:
        Ninguno.

    """

    muestras_caracterizacion = []

    if not datos.historial_caracterizacion:
        return []
    
    for num_canal, metrica in datos.historial_caracterizacion.items():
        tiempo_inicial_caracterizacion = metrica.get("tiempo_inicio", datos.tiempo_inicio_sesion)
        lista_flujo = list(metrica.get("flujo", []) or [])
        lista_concentracion = list(metrica.get("concentracion", []) or [])
        lista_velocidad = list(metrica.get("velocidad", []) or [])
        lista_latencia = list(metrica.get("latencia", []) or [])

        # En caso que la caracterización de parámetros difiera en longitud de contenidos, se recorre el bucle en función del parámetro con mayor número de datos. 
        for i in range(max(len(lista_flujo),len(lista_concentracion),len(lista_latencia),len(lista_velocidad))):
            muestras_caracterizacion.append({
                "timestamp" : tiempo_inicial_caracterizacion + i*config.MUESTREO_CARACTERIZACION,
                "onset": round(i*config.MUESTREO_CARACTERIZACION, 3),
                "canal": num_canal,
                "olor": metrica.get("olor","----"),
                "estado": "activo",
                "flujo": lista_flujo[i] if i< len(lista_flujo) else 0.0,
                "concentracion": lista_concentracion[i] if i< len(lista_concentracion) else 0.0,
                "velocidad_motor": lista_velocidad[i] if i< len(lista_velocidad) else 0.0,
                "latencia": lista_latencia[i] if i< len(lista_latencia) else 0,
            })

    return muestras_caracterizacion


def generar_csv(ruta: str , datos: DatosInforme):
    """
    Genera el informe de sesión en formato .csv y el complementario _eventos.tsv, en la ruta pasada.

    A partir de los datos generados por la sesión experimental pasado como argumento, crea un conjunto de listados con las diferentes secciones que conformarán el informe
    en formato .csv (metadatos, resultados de caracterización ,historial de caracterización e historial de sesión). Por cada sección agrega una cabecera y posteriormente 
    sus correspondientes datos. Tras generar el complementario archivo .tsv, se genera cada sección dando lugar al archivo .csv en la ruta definida como argumento.
        
    Args: 
        - ruta (str): Ruta del ordenador donde se almacenará el informe .csv.
        - datos (DatosInforme): Dataclass con los datos generados en la sesión experimental.
    Return:
        Ninguno.
    Raises:
        Ninguno.

    """

    # Sección Metadatos de sesión.
    seccion_metadatos=[["OlfaMetric - Informe de sesión"],
                       ["ID Sesión", datos.id_sesion],
                       ["ID Paciente", datos.id_paciente],
                       ["Fecha",datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                       ["Duración sesión", datos.duracion_sesion.replace("Duración de sesión: ","")],
                       [],
                       []]
        
    seccion_protocolo=[["PARÁMETROS DEL PROTOCOLO"],
                        ["Número de ciclos", datos.num_ciclos],
                        ["Tiempo de exposición", datos.tiempo_exposicion],
                        ["Tiempo de desensibilización", datos.tiempo_desensibilizacion],
                        ["Tiempo de intervalo entre ciclos", datos.intervalo_ciclos],
                        [],
                        []
                        ]

    # Sección Resultados de caracterización.
    seccion_caracterizacion_resultados = [["RESULTADOS CARACTERIZACIÓN"],["Tiempo caracterización (s)","Canal", "Olor", "Concentración media(VOC)","Concentración max.(VOC)", 
                                "Concentración min.(VOC)", 
                                "Flujo media(ml/min)","Velocidad media(rpm)","Latencia media(ms)"]]

    if datos.historial_caracterizacion:
        for num_canal, metrica in datos.historial_caracterizacion.items():
            seccion_caracterizacion_resultados.append([metrica.get("duracion", datos.tiempo_caracterizacion),
                                    datos.colores_canales[num_canal],
                                    metrica.get("olor","----"),
                                    round(_media(metrica.get("concentracion", 0)), 2),
                                    round(_calculo_max_min(metrica.get("concentracion", 0))[0],2),
                                    round(_calculo_max_min(metrica.get("concentracion", 0))[1],2),
                                    round(_media(metrica.get("flujo", 0)), 2),
                                    round(_media(metrica.get("velocidad",0)), 1),
                                    round(_media(metrica.get("latencia",0)), 1)])
    
    seccion_caracterizacion_resultados.append([])
    seccion_caracterizacion_resultados.append([])

    # Sección Historial de caracterización.
    seccion_caracterizacion_historial = [["HISTORIAL DE CARACTERIZACIÓN"],["Hora","Onset (s)","Canal", "Olor","Concentración(VOC)", 
                                   "Flujo (ml/min)","Velocidad (rpm)","Latencia (ms)"]]
    
    for muestra in _conversor_list_muestras_caracterizacion(datos):
            seccion_caracterizacion_historial.append([
                datetime.datetime.fromtimestamp(muestra["timestamp"]).strftime("%H:%M:%S"),
                muestra["onset"],
                datos.colores_canales[muestra["canal"]],
                muestra.get("olor","----"),  
                round(muestra.get("concentracion", 0),2),              
                round(muestra.get("flujo", 0),2),
                round(muestra.get("velocidad_motor",0),1),
                round(muestra.get("latencia",0),1)
                ])

    seccion_caracterizacion_historial.append([])
    seccion_caracterizacion_historial.append([])


    #Sección Historial de sesión. 
    seccion_sesion_historial = [["HISTORIAL DEL SESIÓN"],["Onset (s)","Hora","Canal", "Olor",
                                   "Estado", "Velocidad (rpm)","Latencia (ms)", "Modo"]]
    
    for metrica in datos.historial_sesion :
        onset = round(metrica["timestamp"] - datos.tiempo_inicio_sesion,3)
        seccion_sesion_historial.append([
            onset,
            datetime.datetime.fromtimestamp(metrica["timestamp"]).strftime("%H:%M:%S"),
            datos.colores_canales[metrica["canal"]],
            metrica.get("olor","----"),
            metrica.get("estado",""),
            metrica.get("velocidad_motor",0),
            metrica.get("latencia",0),
            metrica.get("modo","----")
        ])

    # Generación del archivo complemetario _eventos.tsv .
    ruta_eventos = ruta.replace(".csv", "_eventos.tsv")
    _generar_csv_eventos(ruta_eventos, datos)
        
    # Generación de archivo .csv con las secciones almacenadas.
    with open(ruta, "w", newline="", encoding="utf-8-sig") as fila:
        writer = csv.writer(fila, delimiter=";")
                
        writer.writerows(seccion_metadatos)
        writer.writerows(seccion_protocolo)
        writer.writerows(seccion_caracterizacion_resultados)
        writer.writerows(seccion_caracterizacion_historial)
        writer.writerows(seccion_sesion_historial)


def _generar_csv_eventos(ruta: str, datos: DatosInforme):
    """
    Genera el informe de _eventos.tsv compatible con el estándar BIDS en la ruta pasada.

    Genera un informe con los eventos transcurridos en la sesión experimental según el estándar BIDS compatible con neurimagen establecido. A partir de los datos pasados 
    como argumento, crea las columnas onset, duration, trial_type, channel y odor correspondientes en la ruta especificada pasada.
        
    Args: 
        - ruta (str): Ruta del ordenador donde se almacenará el informe _eventos.tsv.
        - datos (DatosInforme): Dataclass con los datos generados en la sesión experimental.
    Return:
        Ninguno.
    Raises:
        Ninguno.

    """

    eventos = [["onset","duration","trial_type","channel","odor"]]

    # Diccionario con el registro de canales activos.
    canal_inicio = {}

    for metrica in datos.historial_sesion:
        canal = metrica.get("canal", -1)
        estado = metrica.get("estado", "")
        olor = metrica.get("olor", "----")
        timestamp = metrica.get ("timestamp", 0)
        onset = round(timestamp - datos.tiempo_inicio_sesion,3)

        # Cálculo y generación de parámetros compatibles con BIDS.
        if estado == "activo" and canal not in canal_inicio:
            canal_inicio[canal]= {
                "onset": onset,
                "timestamp": timestamp,
                "odor": olor
            }
        
        elif estado == "inactivo" and canal in canal_inicio:
            inicio = canal_inicio.pop(canal)
            duracion = round(onset - inicio["onset"],3)
            eventos.append([
                inicio["onset"],
                duracion,
                "estimulación" if canal != config.CANAL_BLANCO else "desensibilización",
                datos.colores_canales[canal],
                inicio["odor"]
            ])

    # Generación de archivo _eventos.tsv .
    with open(ruta, "w", newline="", encoding="utf-8-sig") as fila:
        writer = csv.writer(fila, delimiter="\t")    
        writer.writerows(eventos)


def generar_excel(ruta: str, datos: DatosInforme):
    """
    Genera el informe de sesión en formato .xlsx en la ruta pasada.

    Genera un informe tabular .xlsx completo mediante la creación de hojas por sección. Cada sección está compuesta de forma general por un título, una cabecera con los
    parámetros registrados y el cuerpo con sus correspondientes datos. De forma adicional respecto al resto de formatos, dibuja las gráficas obtenidas de la caracterización
    de cada parámetro de interes en una hoja específica. Por último, tras generar el informe correspondiente, elimina la copia temporal de las gráficas representadas para
    la liberación de recursos.
        
    Args: 
        - ruta (str): Ruta del ordenador donde se almacenará el informe .xlsx .
        - datos (DatosInforme): Dataclass con los datos generados en la sesión experimental.
    Return:
        Ninguno.
    Raises:
        Ninguno.

    """
    
    workbook = openpyxl.Workbook()

    # Creación de estilos para las hojas .xlsx .
    estilo_titulo = Font(bold=True, size=14, color='FF01BDCE')
    estilo_cabecera = Font(bold=True, color='FFFFFFFF')
    relleno_cabecera = PatternFill('solid', fgColor='FF1E1E1E')
    centrado = Alignment(horizontal='center', vertical='center')


    def aplicar_estilo_cabecera(celda,texto):
        """
        Aplica el estilo de cabecera creado con anterioridad a cada celda pasada.
        
        Args: 
            - celda (Cell): Celda de la hoja de cálculo a aplicar el estilo.
            - texto (str): Texto contenido en la celda pasada.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        celda.value = texto
        celda.font = estilo_cabecera
        celda.fill = relleno_cabecera
        celda.alignment = centrado


    def ajustar_ancho_columnas(hoja):
        """
        Ajusta el ancho de las columnas de la hoja de cálculo de forma automática a la longitud máxima del valor contenido.
        
        Args: 
            - hoja (Worksheet): Hoja de cálculo a ajustar.
        Return:
            Ninguno.
        Raises:
            Ninguno.

        """

        for columna in hoja.columns:
            max_ancho = max(len(str(celda.value or "")) for celda in columna)
            hoja.column_dimensions[columna[0].column_letter].width= max_ancho + 4


    # Hoja 1: Resumen de sesión.
    hoja_resumen = workbook.active
    hoja_resumen.title = "Resumen de sesión"

    # Datos de sesión.
    hoja_resumen['A1'].value = "OlfaMetric - Informe de sesión"
    hoja_resumen['A1'].font = Font(bold=True, size=20, color='FF01BDCE')
    
    datos_sesion = [
        ("ID sesión", datos.id_sesion),
        ("ID paciente", datos.id_paciente),
        ("Fecha", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Duración de sesión", datos.duracion_sesion.replace("Duración de sesión: ",""))
    ]

    # Creación de tabla resumen con metadatos de sesión.
    for contador, (clave,valor) in enumerate(datos_sesion, start=2):
        hoja_resumen[f'A{contador}'] = clave
        hoja_resumen[f'A{contador}'].font = Font(bold = True)
        hoja_resumen[f'B{contador}'] = valor
    
    # Parámetros del protocolo.
    fila = 7
    hoja_resumen[f'A{fila}'] = "PARÁMETROS DEL PROTOCOLO"
    hoja_resumen[f'A{fila}'].font = estilo_titulo
    fila += 1

    datos_protocolo = [
        ("Número de ciclos", datos.num_ciclos),
        ("Tiempo de exposición", f'{datos.tiempo_exposicion} s'),
        ("Tiempo de desensibilización", f'{datos.tiempo_desensibilizacion} s'),
        ("Tiempo de intervalo entre ciclos", f'{datos.intervalo_ciclos} s')
    ]

    # Creación de tabla resumen con metadatos de protocolo.
    for clave, valor in datos_protocolo:
        hoja_resumen[f'A{fila}'] = clave
        hoja_resumen[f'A{fila}'].font = Font(bold=True)
        hoja_resumen[f'B{fila}'] = valor
        fila += 1
    
    # Resultados de caracterización.
    fila += 1
    hoja_resumen[f'A{fila}'] = "RESULTADOS CARACTERIZACIÓN"
    hoja_resumen[f'A{fila}'].font = estilo_titulo
    fila +=1

    cabeceras_caracterizacion = ["Tiempo caracterización (s)","Canal", "Olor", "Concentración media(VOC)","Concentración max.(VOC)", 
                            "Concentración min.(VOC)", "Flujo medio (ml/min)",
                            "Velocidad media(rpm)","Latencia media(ms)"]
    
    for columna, cabecera in enumerate(cabeceras_caracterizacion, start=1):
        aplicar_estilo_cabecera(hoja_resumen.cell(fila, columna),cabecera)

    fila +=1
    
    if datos.historial_caracterizacion:

        for num_canal, metrica in datos.historial_caracterizacion.items():
            fila_datos = [
                metrica.get("duracion", datos.tiempo_caracterizacion),
                datos.colores_canales[num_canal],
                metrica.get("olor","----"),
                round(_media(metrica.get("concentracion", 0)), 2),
                round(_calculo_max_min(metrica.get("concentracion", 0))[0],2),
                round(_calculo_max_min(metrica.get("concentracion", 0))[1],2),
                round(_media(metrica.get("flujo", 0)),2),
                round(_media(metrica.get("velocidad",0)),1),
                round(_media(metrica.get("latencia",0)),1)
                ]
            
            for columna, valor in enumerate(fila_datos, start=1):
                hoja_resumen.cell(fila, columna).value = valor
            
            fila +=1

    ajustar_ancho_columnas(hoja_resumen)

    # Hoja 2: Historial de caracterización.
    hoja_historial_caracterizacion = workbook.create_sheet("Historial Caracterización")

    cabeceras_historial_caracterizacion = ["Hora", "Onset(s)","Canal", "Olor", "Estado","Concentración(VOC)", "Flujo (ml/min)",
                                    "Velocidad (rpm)", "Latencia (ms)"]
    
    for columna, cabecera in enumerate(cabeceras_historial_caracterizacion,start=1):
        aplicar_estilo_cabecera(hoja_historial_caracterizacion.cell(1,columna),cabecera)
        
    for fila, muestra in enumerate(_conversor_list_muestras_caracterizacion(datos),start = 2):
        fila_datos = [
        datetime.datetime.fromtimestamp(muestra["timestamp"]).strftime("%H:%M:%S"),
        muestra["onset"],  
        datos.colores_canales[muestra["canal"]],
        muestra["olor"],
        muestra["estado"],
        round(muestra["concentracion"],2),
        round(muestra["flujo"], 2),
        round(muestra["velocidad_motor"], 1),
        round(muestra["latencia"], 1),
        ]

        for columna, valor in enumerate(fila_datos, start=1):
            hoja_historial_caracterizacion.cell(fila, columna).value = valor

    ajustar_ancho_columnas(hoja_historial_caracterizacion)

    # Hoja 3: Historial de sesión.
    hoja_historial_sesion = workbook.create_sheet("Historial de Sesión")
    hoja_historial_sesion.title = "Historial de sesión"

    cabeceras_historial_sesion = ["Onset","Hora","Canal", "Olor", "Estado",
                                    "Velocidad (rpm)", "Latencia (ms)", "Modo"]
    
    for columna, cabecera in enumerate(cabeceras_historial_sesion,start=1):
        aplicar_estilo_cabecera(hoja_historial_sesion.cell(1,columna),cabecera)

    for fila, metrica in enumerate(datos.historial_sesion, start=2):
        onset = round(metrica["timestamp"]- datos.tiempo_inicio_sesion,3)
        fila_datos = [
            onset,
            datetime.datetime.fromtimestamp(metrica["timestamp"]).strftime("%H:%M:%S"),  
            datos.colores_canales[metrica["canal"]],
            metrica.get("olor","----"),
            metrica.get("estado",""),
            round(_media(metrica.get("velocidad_motor", 0)), 1),
            round(_media(metrica.get("latencia", 0)), 1),
            metrica.get("modo","----")
        ]

        for columna, valor in enumerate(fila_datos, start=1):
            hoja_historial_sesion.cell(fila, columna).value = valor

    ajustar_ancho_columnas(hoja_historial_sesion)

    ## Hoja 3: Gráficas de caracterización.
    hoja_graficas = workbook.create_sheet("Gráficas de caracterizacion")
    hoja_graficas.title = "Gráficas de caracterizacion"
    hoja_graficas['A1'].font = estilo_titulo

    etiquetas_parametros = dict(config.PARAMETROS_CARACTERIZACION)

    archivos_temporales = []

    if datos.historial_caracterizacion:
        fila = 3

        for num_canal, metricas in datos.historial_caracterizacion.items():
            color_canal = datos.colores_canales[num_canal]

            for parametro, valores in metricas.items():

                if parametro in ("olor", "tiempo_inicio", "duracion"):
                    continue

                if not valores:
                    continue

                etiquetas_y = etiquetas_parametros.get(parametro, "----")
                tiempo = [i * config.MUESTREO_CARACTERIZACION for i in range(len(valores))]

                # Generación de gráfica.
                figura, eje = plt.subplots(figsize=(9,4), dpi=110)
                figura.set_facecolor("#ffffff")
                eje.set_facecolor("#fafafa")
                eje.plot(tiempo,valores, color="#01bdce", linewidth=1.6)
                eje.set_title(f'Canal {color_canal}/{metricas.get("olor","----")} - {etiquetas_y}', fontdict={'fontsize': 10, 'fontweight': 'bold'}, color = "#555555")
                eje.set_xlabel('Tiempo (s)', fontsize= 10, color="#1a1a1a")
                eje.set_ylabel(etiquetas_y, fontsize=10,color="#1a1a1a")
                eje.grid(True, linestyle='--', alpha=0.5)
                eje.tick_params(colors="#1a1a1a")

                for spine in eje.spines.values():
                    spine.set_color('#333333')
                    spine.set_linewidth(0.8)

                figura.tight_layout(rect=[0,0,1,0.90])

                # Guardado temporal.
                with tempfile.NamedTemporaryFile(suffix=".png", delete= False) as temporal:
                    ruta_figura = temporal.name

                archivos_temporales.append(ruta_figura)
                figura.savefig(ruta_figura, bbox_inches='tight', facecolor=figura.get_facecolor(), dpi=110)
                plt.close(figura)

                imagen = openpyxl.drawing.image.Image(ruta_figura)
                imagen.anchor = f'A{fila}'
                hoja_graficas.add_image(imagen)

                fila += 22

            fila +=22

    # Generación de informe .xlsx .
    workbook.save(ruta)

    # Eliminación de archivos temporales.
    for archivo in archivos_temporales:
        if os.path.exists(archivo):
            os.unlink(archivo)


def generar_pdf(ruta: str, datos: DatosInforme):
    """
    Genera el informe de sesión en formato .pdf en la ruta pasada.

    Genera un informe .pdf a partir del conjunto de listas que conforman las diferentes secciones. Tras la creción de los diferentes estilos, se van agregando a la lista
    global las secciones con sus correspondietes datos. Finalizando con la configuración del archivo .pdf .
        
    Args: 
        - ruta (str): Ruta del ordenador donde se almacenará el informe .xlsx .
        - datos (DatosInforme): Dataclass con los datos generados en la sesión experimental.
    Return:
        Ninguno.
    Raises:
        Ninguno.

    """

    # Creación de estilos.
    estilo_titulo = ParagraphStyle('Titulo',
                                fontSize=25,
                                textColor=colors.HexColor('#01BDCE'),
                                alignment=TA_CENTER,          
                                spaceAfter=20,
                                fontName='Helvetica-Bold')

    estilo_seccion = ParagraphStyle('Seccion',
                                fontSize=16,
                                textColor=colors.HexColor('#01BDCE'),
                                spaceBefore=15,
                                spaceAfter=10,
                                fontName='Helvetica-Bold')

    estilo_tabla_cabecera = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E1E1E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#EEEEEE'), colors.white]),  
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('PADDING', (0, 0), (-1, -1), 8),
    ])

    #Lista global del informe.
    informe = []

    # Título de informe.
    informe.append(Paragraph("OlfaMetric - Informe de sesion", estilo_titulo)) 
    informe.append(Spacer(1, 4*mm))

    # Sección de Metadatos.
    # Metadatos de sesión.
    informe.append(Paragraph("Datos de sesion", estilo_seccion))

    datos_sesion = [
        ["ID sesion", datos.id_sesion],
        ["ID paciente", datos.id_paciente],
        ["Fecha", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["Duracion de sesion", datos.duracion_sesion]
    ]

    tabla_sesion = Table(datos_sesion, colWidths=(100*mm, 80*mm))
    tabla_sesion.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('PADDING', (0, 0), (-1, -1), 8),
        ]))
    
    informe.append(tabla_sesion)
    informe.append(Spacer(1, 10*mm))

    # Metadatos de protocolo.
    informe.append(Paragraph("Parametros del protocolo", estilo_seccion))

    datos_protocolo = [
        ["Numero de ciclos", datos.num_ciclos],
        ["Tiempo de exposicion", f'{datos.tiempo_exposicion} s'],
        ["Tiempo de desensibilizacion", f'{datos.tiempo_desensibilizacion} s'],
        ["Tiempo de intervalo entre ciclos", f'{datos.intervalo_ciclos} s']
    ]

    tabla_protocolo = Table(datos_protocolo, colWidths=(100*mm, 80*mm))
    tabla_protocolo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('PADDING', (0, 0), (-1, -1), 8),
        ]))
    
    informe.append(tabla_protocolo)
    informe.append(Spacer(1, 10*mm))

    # Sección de Resultados de caracterización.
    informe.append(Paragraph("Resultados de caracterizacion", estilo_seccion))

    cabeceras_caracterizacion = [[                                    
    "Tiempo(s)","Canal", "Olor", "VOC medio", "VOC max.",
    "VOC min.", "ml/min med.", "rpm med.", "ms med."
    ]]

    datos_caracterizacion = []

    if datos.historial_caracterizacion:
        for num_canal, metrica in datos.historial_caracterizacion.items():
            datos_caracterizacion.append([
                metrica.get("duracion", datos.tiempo_caracterizacion),
                datos.colores_canales[num_canal],
                metrica.get("olor", "----"),
                round(_media(metrica.get("concentracion", [])),2),
                round(_calculo_max_min(metrica.get("concentracion", []))[0], 2),
                round(_calculo_max_min(metrica.get("concentracion", []))[1], 2),
                round(_media(metrica.get("flujo", [])), 2),
                round(_media(metrica.get("velocidad", [])), 1),
                round(_media(metrica.get("latencia", [])), 1),
                ])
            
    tabla_caracterizacion = Table(cabeceras_caracterizacion + datos_caracterizacion,
                            colWidths=[20*mm,14*mm, 30*mm, 22*mm, 22*mm, 22*mm, 24*mm, 20*mm, 18*mm])
    tabla_caracterizacion.setStyle(estilo_tabla_cabecera)

    informe.append(tabla_caracterizacion)
    informe.append(PageBreak())

    # Sección de historial de caracterización.
    informe.append(Paragraph("Historial Caracterización", estilo_seccion))

    cabeceras_historial_caracterizacion = [[
        "Hora", "Onset(s)","Canal", "Olor","Estado","Concentración(VOC)", "ml/min","rpm", "ms"
    ]]

    datos_historial_caracterizacion = []
    for muestra in _conversor_list_muestras_caracterizacion(datos):
        datos_historial_caracterizacion.append([
            datetime.datetime.fromtimestamp(muestra["timestamp"]).strftime("%H:%M:%S"),
            muestra["onset"],
            datos.colores_canales[muestra["canal"]],
            muestra["olor"],
            muestra["estado"],
            round(muestra["concentracion"], 2),
            round(muestra["flujo"], 2),
            round(muestra["velocidad_motor"], 1),
            round(muestra["latencia"], 1),
            ])
        
    tabla_historial_caracterizacion = Table(cabeceras_historial_caracterizacion + datos_historial_caracterizacion, 
                                        colWidths=[18*mm, 18*mm, 14*mm, 30*mm, 18*mm, 18*mm, 18*mm, 20*mm, 18*mm])
    tabla_historial_caracterizacion.setStyle(estilo_tabla_cabecera)

    informe.append(tabla_historial_caracterizacion)
    informe.append(PageBreak())

    # Sección de historial de sesión.
    informe.append(Paragraph("Historial de Sesión", estilo_seccion))

    cabeceras_historial_sesion = [[
        "Onset(s)","Hora", "Canal", "Olor","Estado","rpm", "ms", "Modo"
    ]]

    datos_historial_sesion = []

    for metrica in datos.historial_sesion:
        onset = round(metrica["timestamp"] - datos.tiempo_inicio_sesion,3)
        datos_historial_sesion.append([
            onset,
            datetime.datetime.fromtimestamp(metrica["timestamp"]).strftime("%H:%M:%S"),
            datos.colores_canales[metrica["canal"]],
            metrica.get("olor", "----"),
            metrica.get("estado", ""),
            round(metrica.get("velocidad_motor", 0), 1),
            round(metrica.get("latencia", 0), 1),
            metrica.get("modo","----")
            ])
        
    tabla_historial_sesion = Table(cabeceras_historial_sesion + datos_historial_sesion, 
                                        colWidths=[18*mm, 16*mm, 14*mm, 30*mm, 16*mm, 18*mm, 14*mm, 24*mm])
    tabla_historial_sesion.setStyle(estilo_tabla_cabecera)

    informe.append(tabla_historial_sesion)

    # Genración y configuración de archivo .pdf .
    documento = SimpleDocTemplate(ruta, pagesize=A4,
                                    rightMargin=15*mm, leftMargin=15*mm,
                                    topMargin=15*mm, bottomMargin=15*mm)
    documento.build(informe)
            


