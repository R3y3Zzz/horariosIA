import pandas as pd
import re 

# --- ESTRUCTURA DE DATOS ---

class Grupo:
    """
    Representa una tarea a resolver: una materia específica para una cohorte.
    """
    def __init__(self, clv_mat, nombre, turno, cohorte_id, patron):
        self.clv_mat = clv_mat
        self.nombre = nombre
        self.turno = turno      # 'M' o 'V'
        self.cohorte_id = cohorte_id 
        self.patron = patron    # 'M-J', 'L-M-V', 'SABADO'

    def __repr__(self):
        return (f"<Grupo {self.nombre} ({self.clv_mat}) | "
                f"Cohorte: {self.cohorte_id} | Patron: {self.patron}>")


# --- FUNCIONES AUXILIARES ---

def inferir_patron(fila):
    """
    Infiere el patrón de horario (ej. 'M-J') basado en qué columnas
    de días tienen datos (no NaN).
    """
    dias_mj = ['Martes', 'Jueves']
    dias_lmv = ['Lunes', 'Miercoles', 'Viernes']
    
    hay_mj = any(pd.notna(fila.get(d, None)) for d in dias_mj)
    hay_lmv = any(pd.notna(fila.get(d, None)) for d in dias_lmv)

    if hay_mj:
        return 'M-J' 
    elif hay_lmv:
        return 'L-M-V'
        
    return 'Indefinido' 


def limpiar_nombre_materia(nombre_original):
    """Limpia caracteres especiales y espacios múltiples del nombre."""
    nombre_limpio = str(nombre_original).replace('\u00A0', ' ').strip()
    nombre_limpio = re.sub(r'\s{2,}', ' ', nombre_limpio)
    return nombre_limpio


# --- FUNCIONES DE CARGA PRINCIPAL ---

# Grupos que ANTES se omitían y AHORA se asignan el SÁBADO (En Línea)
GRUPOS_SABADO_ONLINE = {
    (1309, 480), (1407, 1417), (1509, 1503), (1560, 1503), 
    (1607, 434), (1708, 1719), (1807, 1810), (1808, 1813), 
    (1957, 1705), (1958, 1705), (1959, 1705), (1007, 1910), 
    (1010, 1003), (1057, 13), (1007, 308), (1007, 314), 
    (1010, 312)
}

# Diccionario de mapeo de Turnos 
MAPEO_TURNOS = {
    'T': 'V', # Turno Tarde -> Vespertino
    'M': 'M', # Turno Mañana -> Matutino
}


def cargar_grupos_de_csv(ruta_archivo):
    """
    Lee el CSV y separa los grupos: 
    - Grupos normales (para el Solver).
    - Grupos de Sábado (para asignación manual En Línea).
    
    Retorna: (lista_grupos_solver, lista_grupos_sabado)
    """
    print(f"Cargando archivo: {ruta_archivo}...")
    try:
        df = pd.read_csv(ruta_archivo, dtype={'Grupo': str, 'clv_Mat': str})
    except FileNotFoundError:
        print(f"ERROR: No se encontró el archivo en la ruta: {ruta_archivo}")
        return [], []
    
    grupos_solver = []
    grupos_sabado = []
    
    columnas_requeridas = ['Grupo', 'clv_Mat', 'Materia', 'Turno']
    if not all(col in df.columns for col in columnas_requeridas):
        print(f"ERROR: El CSV debe contener las columnas: {', '.join(columnas_requeridas)}")
        return [], []
    
    for indice, fila in df.iterrows():
        
        try:
            cohorte = int(fila['Grupo'])
            clv = int(fila['clv_Mat'])
        except (ValueError, TypeError):
            continue
        
        # --- VERIFICAR SI ES UN GRUPO DE SABADO (está en la lista de omisión) ---
        if (cohorte, clv) in GRUPOS_SABADO_ONLINE:
            
            nombre = limpiar_nombre_materia(fila['Materia'])
            
            grupo_sabado = Grupo(
                clv_mat=clv,
                nombre=nombre,
                turno='M', # Forzamos turno matutino para el bloque 08:00-12:00
                cohorte_id=cohorte,
                patron='SABADO' # ¡Forzamos el patrón!
            )
            grupos_sabado.append(grupo_sabado)
            continue # Saltamos el procesamiento normal
        
        # --- PROCESAMIENTO NORMAL (Si no es Sábado) ---
        
        patron_inferido = inferir_patron(fila)
        nombre = limpiar_nombre_materia(fila['Materia'])
        turno_csv = str(fila['Turno']).strip().upper()
        turno = MAPEO_TURNOS.get(turno_csv, 'M')
            
        nuevo_grupo = Grupo(
            clv_mat=clv,
            nombre=nombre,
            turno=turno,
            cohorte_id=cohorte,
            patron=patron_inferido
        )
        grupos_solver.append(nuevo_grupo)
            
    print(f"¡Carga completa! {len(grupos_solver)} grupos para Solver y {len(grupos_sabado)} para Sábado.")
    return grupos_solver, grupos_sabado 


if __name__ == "__main__":
    archivo_csv = "Horario.csv" 
    lista_solver, lista_sabado = cargar_grupos_de_csv(archivo_csv)
    
    if lista_solver:
        print("\n--- Primer grupo semanal ---")
        print(lista_solver[0])
    
    if lista_sabado:
        print("\n--- Primer grupo de Sabado ---")
        print(lista_sabado[0])