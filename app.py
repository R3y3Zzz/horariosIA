import streamlit as st
import pandas as pd
import io
import time # Usaremos time para medir el rendimiento

# Importamos las funciones y clases de tu lógica
# ¡Asegúrate de que estos archivos estén en la misma carpeta!
from cargar_datos import cargar_grupos_de_csv 
from solver import resolver_horario, asignar_grupos_sabado, Asignacion 
from base_conocimiento import obtener_bloques_para, PROFES_POR_MATERIA, SALONES_DISPONIBLES

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(layout="wide", page_title="Planificador de Horarios IA")

st.title("📅 Planificador de Horarios IA")
st.markdown("Carga tu archivo CSV para generar el horario optimizado mediante **Backtracking**.")

# --- 2. FUNCIÓN DE CARGA DE DATOS (Con Caching) ---

@st.cache_data
def cargar_y_procesar_datos(uploaded_file):
    """
    Función que lee el archivo cargado, lo convierte a un objeto tipo archivo
    en memoria y devuelve las dos listas de grupos.
    """
    if uploaded_file is not None:
        # Decodificamos el archivo subido (bytes) en un objeto de texto (StringIO)
        # que es lo que tu función de carga basada en pandas necesita.
        csv_data = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
        
        # Llamamos a tu función principal de carga
        grupos_solver, grupos_sabado = cargar_grupos_de_csv(csv_data)
        
        return grupos_solver, grupos_sabado
    return [], [] # Retorna listas vacías si no hay archivo


# --- 3. LÓGICA PRINCIPAL DEL SOLVER (Con Caching y Corrección del Error) ---

@st.cache_data(show_spinner="⏳ Ejecutando el Solver de Backtracking y Asignación de Sábados...")
def ejecutar_solver(_grupos_solver, _grupos_sabado):
    """
    Función que llama a las rutinas del Solver y Sábado para generar el horario final.
    
    Nota: Se usa '_' en los argumentos para evitar el error UnhashableParamError
    y que Streamlit pueda usar el caching.
    """
    
    solucion_final = []
    exito = False
    
    tiempo_inicio = time.time()
    
    # A. Resolver la semana (Backtracking)
    if _grupos_solver:
        exito = resolver_horario(_grupos_solver, 0, solucion_final)
        
        if not exito:
            # Si el solver falla, mostramos el error y retornamos lo que llevamos
            st.error("❌ FALLO CRÍTICO: No se pudo encontrar una solución semanal completa.")
            return None, False

    # B. Asignar grupos de Sábado (En Línea)
    if _grupos_sabado:
        # La función de sábado añade las asignaciones a 'solucion_final'
        asignar_grupos_sabado(_grupos_sabado, solucion_final)

    tiempo_fin = time.time()
    
    # C. Convertir a DataFrame para visualización
    data = [{
        'Cohorte': a.grupo.cohorte_id,
        'Materia': a.grupo.nombre,
        'Profesor': a.profesor,
        'Días': a.grupo.patron,
        'Bloque': a.bloque_horario,
        'Salón/Ubicación': a.salon
    } for a in solucion_final]
    
    df_resultado = pd.DataFrame(data)
    
    st.success(f"Tiempo total de procesamiento: **{tiempo_fin - tiempo_inicio:.2f} segundos**")
    
    return df_resultado, True


# --- 4. INTERFAZ DE USUARIO ---

uploaded_file = st.file_uploader("Sube tu archivo CSV de Horarios", type=["csv"])

if uploaded_file is not None:
    
    # Cargar y procesar los grupos (usa cache)
    grupos_solver, grupos_sabado = cargar_y_procesar_datos(uploaded_file)
    
    # Mostrar resumen de la carga
    st.info(f"Se encontraron **{len(grupos_solver)}** grupos para el Solver y **{len(grupos_sabado)}** grupos de Sábado (En Línea).")
    
    # Botón para iniciar la generación
    if st.button("🚀 Generar Horario Completo", type="primary"):
        
        # Ejecutar el solver
        # Le pasamos los argumentos SIN el guion bajo
        df_resultado, exito = ejecutar_solver(grupos_solver, grupos_sabado)
        
        if exito and df_resultado is not None:
            st.balloons()
            st.header("✅ Horario Generado con Éxito")
            st.dataframe(df_resultado, use_container_width=True)
            
            # Opción para descargar el resultado
            csv_export = df_resultado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar Horario (CSV)",
                data=csv_export,
                file_name='horario_final.csv',
                mime='text/csv',
            )