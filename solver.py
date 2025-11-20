"""
SOLVER (Planificador de Horarios)

Archivo principal que ejecuta el algoritmo de Búsqueda con Backtracking 
y la asignación de Sábado.
"""

import time 

# --- 1. IMPORTAR NUESTRA BASE DE CONOCIMIENTO Y CARGADOR ---

from cargar_datos import Grupo, cargar_grupos_de_csv 
from base_conocimiento import (
    SALONES_DISPONIBLES,
    PROFES_POR_MATERIA,
    PATRONES_INFO,
    obtener_bloques_para
)

# --- 2. ESTRUCTURA DE LA SOLUCIÓN ---

class Asignacion:
    """
    Representa una "respuesta" final. 
    """
    def __init__(self, grupo, profesor, salon, bloque_horario):
        self.grupo = grupo 
        self.profesor = profesor 
        self.salon = salon      
        self.bloque_horario = bloque_horario 

    def __repr__(self):
        # Para imprimir la solución de forma clara
        return (f"[SOLUCIÓN: {self.grupo.cohorte_id} - {self.grupo.nombre} | "
                f"PROF: {self.profesor} | "
                f"SALÓN: {self.salon} | "
                f"HORARIO: {self.grupo.patron} {self.bloque_horario}]")


# --- 3. EL VERIFICADOR DE RESTRICCIONES (Solo para Lunes a Viernes) ---

def es_valida(grupo_nuevo, prof_nuevo, bloque_nuevo, salon_nuevo, solucion_parcial):
    """
    Revisa si una nueva asignación propuesta choca con CUALQUIER asignación
    previamente hecha en la 'solucion_parcial'.
    """
    
    # Obtener información de la asignación propuesta
    dias_nuevos = set(PATRONES_INFO.get(grupo_nuevo.patron, {}).get('dias', []))
    cohorte_nueva = grupo_nuevo.cohorte_id
    
    if not dias_nuevos:
        return False

    # Iterar sobre las asignaciones existentes para buscar conflictos
    for asignacion_existente in solucion_parcial:
        
        grupo_existente = asignacion_existente.grupo
        dias_existentes = set(PATRONES_INFO.get(grupo_existente.patron, {}).get('dias', []))
        
        # No se verifica Sábado aquí, ya que ese grupo no está en lista_de_tareas_solver.
        
        # Verificación de Empalme de Tiempo (Días y Bloque)
        hay_empalme_dias = not dias_nuevos.isdisjoint(dias_existentes)
        hay_empalme_bloque = (bloque_nuevo == asignacion_existente.bloque_horario)
        
        # Si NO hay empalme de tiempo (días Y bloque), no hay conflicto de recursos.
        if not (hay_empalme_dias and hay_empalme_bloque):
            continue

        # --- CONFLICTO DE TIEMPO DETECTADO: REVISAR RECURSOS ---
        
        # RESTRICCIÓN 1: CONFLICTO DE COHORTE (ALUMNOS)
        if cohorte_nueva == grupo_existente.cohorte_id:
            return False 

        # RESTRICCIÓN 2: CONFLICTO DE PROFESOR
        if prof_nuevo == asignacion_existente.profesor:
            return False 

        # RESTRICCIÓN 3: CONFLICTO DE SALÓN
        if salon_nuevo == asignacion_existente.salon:
            return False 

    return True 


# --- 4. EL MOTOR DE BACKTRACKING (Para Lunes a Viernes) ---

def resolver_horario(lista_de_tareas, grupo_index, solucion_parcial):
    """
    Función recursiva principal. Intenta asignar la tarea en 'grupo_index'.
    """

    # --- CASO BASE (ÉXITO) ---
    if grupo_index == len(lista_de_tareas):
        return True 

    # --- PREPARACIÓN ---
    grupo_actual = lista_de_tareas[grupo_index]

    profesores_posibles = PROFES_POR_MATERIA.get(grupo_actual.nombre, [])
    bloques_posibles = obtener_bloques_para(grupo_actual.turno, grupo_actual.patron)
    salones_posibles = SALONES_DISPONIBLES
    
    # Pruning: Si no hay opciones, retroceder inmediatamente
    if not profesores_posibles or not bloques_posibles or not salones_posibles:
        return False 
    
    # --- BÚSQUEDA (Probando todas las combinaciones) ---
    for prof in profesores_posibles:
        for bloque in bloques_posibles:
            for salon in salones_posibles:
                
                # 4. VERIFICAR RESTRICCIONES 
                if es_valida(grupo_actual, prof, bloque, salon, solucion_parcial):
                    
                    # 5. "PROBAR" (Asignar)
                    nueva_asignacion = Asignacion(grupo_actual, prof, salon, bloque)
                    solucion_parcial.append(nueva_asignacion)
                    
                    # 6. LLAMADA RECURSIVA (Paso adelante)
                    if resolver_horario(lista_de_tareas, grupo_index + 1, solucion_parcial):
                        return True 
                        
                    # 7. "DESHACER" (Backtrack)
                    solucion_parcial.pop()
    
    # --- CASO BASE (FALLO) ---
    return False 

# --- 5. FUNCIÓN DE ASIGNACIÓN DE SÁBADO (En Línea) ---

# Ubicación estática para clases en línea.
UBICACION_ONLINE = "Clase en Línea (Virtual)"

def asignar_grupos_sabado(grupos_sabado, solucion_final):
    """
    Asigna los grupos del Sábado (En Línea) iterando sobre los bloques 
    disponibles para evitar conflictos de Profesor y Cohorte.
    """
    
    # Obtenemos los dos bloques posibles: ['07:00-11:00', '11:00-15:00']
    BLOQUES_SABADO = obtener_bloques_para('M', 'SABADO')
    
    # Inicializamos una estructura para rastrear recursos por bloque de tiempo
    # { '07:00-11:00': {'profes': set(), 'cohortes': set()}, ... }
    recursos_por_bloque = {
        bloque: {'profes': set(), 'cohortes': set()} 
        for bloque in BLOQUES_SABADO
    }

    print(f"\n--- Asignando {len(grupos_sabado)} grupos de Sábado (En Línea) ---")
    
    grupos_no_asignados = []

    for grupo in grupos_sabado:
        
        profesor_asignado = PROFES_POR_MATERIA.get(grupo.nombre, ['[PROFESOR NO ENCONTRADO]'])[0]
        asignado_con_exito = False
        
        # Intentamos asignar el grupo al primer bloque libre
        for bloque_actual in BLOQUES_SABADO:
            
            recursos = recursos_por_bloque[bloque_actual]
            
            # 1. Verificar conflictos
            es_conflicto_profesor = profesor_asignado in recursos['profes']
            es_conflicto_cohorte = grupo.cohorte_id in recursos['cohortes']

            if not es_conflicto_profesor and not es_conflicto_cohorte:
                
                # 2. Asignación
                asignacion = Asignacion(
                    grupo, 
                    profesor_asignado, 
                    UBICACION_ONLINE, 
                    bloque_actual # <-- Bloque específico asignado
                )
                solucion_final.append(asignacion)
                
                # 3. Marcar recursos como usados para ESTE BLOQUE
                recursos['profes'].add(profesor_asignado)
                recursos['cohortes'].add(grupo.cohorte_id)
                
                asignado_con_exito = True
                break # Salir del bucle de bloques e ir al siguiente grupo
        
        if not asignado_con_exito:
            grupos_no_asignados.append(grupo)
            print(f"ALERTA CRÍTICA: El grupo {grupo.cohorte_id} - {grupo.nombre} no se pudo asignar. Faltan horas/profesores/aulas.")

    if grupos_no_asignados:
         print(f"Total de grupos no asignados: {len(grupos_no_asignados)}")


# --- 6. EJECUCIÓN PRINCIPAL ---

if __name__ == "__main__":
    
    print("---  Iniciando Planificador de Horarios IA ---")
    
    # 1. Cargar las tareas y SEPARAR las listas
    archivo_csv = "Horario_PRUEBA.csv" 
    lista_de_tareas_solver, lista_de_tareas_sabado = cargar_grupos_de_csv(archivo_csv) 
    
    solucion_final = []
    
    # 2. PROCESAR GRUPOS DE SEMANA (L-V) con el SOLVER
    if not lista_de_tareas_solver:
        print("No hay grupos para asignar en la semana. Solo procesando Sábado.")
    else:
        print(f"\nSe van a asignar {len(lista_de_tareas_solver)} grupos semanales...")
        print("Iniciando solver de Backtracking...")
        
        tiempo_inicio = time.time()
        exito = resolver_horario(lista_de_tareas_solver, 0, solucion_final) 
        tiempo_fin = time.time()
        
        print("\n--- Búsqueda Terminada (Solver) ---")
        print(f"Tiempo de búsqueda: {tiempo_fin - tiempo_inicio:.2f} segundos")
        
        if not exito:
            print("\nFALLO CRÍTICO: No se pudo encontrar una solución semanal completa.")
            # Continuamos a Sábado, pero el horario semanal ya falló
            
    # 3. ASIGNAR GRUPOS DE SÁBADO (En Línea)
    if lista_de_tareas_sabado:
        asignar_grupos_sabado(lista_de_tareas_sabado, solucion_final)
        
    # 4. Mostrar resultados FINALES
    print("\n" + "="*40)
    print("      RESULTADO FINAL COMPLETO")
    print("="*40)
    print(f"Total de asignaciones: {len(solucion_final)}")
    
    # Imprimir la solución completa
    for asignacion in solucion_final:
        print(asignacion)