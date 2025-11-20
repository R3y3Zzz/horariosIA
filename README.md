# horariosIA
# Estructura y Arquitectura del Planificador de Horarios IA

## 1. 🧠 Base de Conocimiento (`base_conocimiento.py`)

Este archivo es el **cerebro de reglas** y define el universo de opciones (dominios) que el Solver puede usar.

| Contenido | Función |
| **`SALONES_DISPONIBLES`** | Dominio de la variable "Salón" (recursos físicos). |
| **`PROFES_POR_MATERIA`** | Dominio de la variable "Profesor", mapeada a la materia requerida. |
| **`PATRONES_INFO`** | Define los días y duración de los patrones (`M-J`, `L-M-V`, `SABADO`). |
| **`BLOQUES_HORARIOS`** | Define los bloques de tiempo posibles para cada turno y patrón (ej. 07:00-09:00, 07:00-11:00). |

## 2. 📑 Cargador de Datos (`cargar_datos.py`)

Este módulo actúa como el **preparador de tareas** que traduce la información del mundo real (CSV) al lenguaje del Solver.

| Contenido | Función |
| :--- | :--- |
| **Clase `Grupo`** | Define la estructura de cada **tarea a resolver** (Cohorte, Materia, Turno, Patrón). |
| **`GRUPOS_SABADO_ONLINE`** | La lista de excepciones que se asignarán fuera del Backtracking. |
| **`cargar_grupos_de_csv`** | Función principal que lee el CSV, limpia los nombres, infiere patrones y **separa las tareas** en dos listas: `grupos_solver` (L-V) y `grupos_sabado` (online). |

## 3. 🤖 Motor de I.A. (`solver.py`)

Este es el **núcleo de la inteligencia** que ejecuta la lógica de búsqueda y asignación. 

| Contenido | Función |
| :--- | :--- |
| **Clase `Asignacion`** | Define el **resultado final** de una tarea asignada (Cohorte, Profesor, Salón, Bloque). |
| **`es_valida`** | Función de **Verificación de Restricciones (El "Muro")**. Verifica si una asignación propuesta choca con cualquier asignación existente (conflicto de profesor, cohorte o salón a la misma hora). |
| **`resolver_horario`** | Función recursiva que implementa el algoritmo de **Backtracking**. Prueba secuencialmente las opciones (Profesor, Bloque, Salón) y retrocede si encuentra un callejón sin salida. |
| **`asignar_grupos_sabado`** | Función que aplica la **asignación determinística** a los grupos de Sábado. Usa los dos bloques disponibles y asigna la ubicación "Clase en Línea (Virtual)". |

## 4. 🌐 Interfaz de Usuario (`app.py` / Streamlit)

Este archivo maneja la interacción con el usuario, la visualización y la descarga de resultados.

| Contenido | Función |
| :--- | :--- |
| **`st.file_uploader`** | Permite al usuario subir el archivo CSV con la demanda de tareas. |
| **`ejecutar_solver`** | Coordina la ejecución: llama primero a `resolver_horario` (semana) y luego a `asignar_grupos_sabado` (sábado). |
| **`st.dataframe`** | Presenta el resultado (`solucion_final`) en un formato tabular interactivo que se puede consultar y descargar. |
