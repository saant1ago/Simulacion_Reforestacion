import pandas as pd
import streamlit as st
from scipy.spatial.distance import euclidean
from datetime import datetime, timedelta
import plotly.express as px
import random

# ------------------------------------------------------------
# 0) VARIABLES AUXILIARES POR DEFECTO (se sobrescribirán desde el sidebar)
# ------------------------------------------------------------
tiempo_carga = 1      # minutos
tiempo_descarga = 1   # minutos

# ------------------------------------------------------------
# 1) SELECCIÓN DE ESCENARIO (SIN session_state)
# ------------------------------------------------------------
st.title("🌳 Simulación de Reforestación y Logística")

st.markdown(
    """
    Elige un escenario prefabricado o deja “Ninguno” para ingresar tus propios datos.
    """
)

escenario = st.selectbox(
    "Selecciona escenario",
    ["Ninguno", "Ejemplo Básico"]
)

def crear_poligonos_ejemplo():
    return pd.DataFrame([
        {"Polígono": 1, "X": 0,  "Y": 0},
        {"Polígono": 2, "X": 40, "Y": 20},
        {"Polígono": 3, "X": 25, "Y": 35},
        {"Polígono": 18,"X": 30, "Y": 60}
    ])

def crear_demandas_ejemplo():
    especies = ["Encino", "Pino", "Cedro"]
    filas = []
    for esp in especies:
        for pid in [1, 2, 3]:
            filas.append({
                "Especie": esp,
                "Polígono": pid,
                "Demanda": random.randint(5, 20)
            })
    return pd.DataFrame(filas)

def crear_proveedores_ejemplo():
    especies = ["Encino", "Pino", "Cedro"]
    filas = []
    for prov in ["Prov1", "Prov2", "Prov3"]:
        for esp in especies:
            filas.append({
                "Proveedor": prov,
                "Especie": esp,
                "Costo": round(random.uniform(4, 12), 2),
                "Max_oferta": random.randint(10, 30)
            })
    return pd.DataFrame(filas)

if escenario == "Ejemplo Básico":
    inicial_poligonos   = crear_poligonos_ejemplo()
    inicial_demandas    = crear_demandas_ejemplo()
    inicial_proveedores = crear_proveedores_ejemplo()
else:
    inicial_poligonos   = pd.DataFrame(columns=["Polígono", "X", "Y"])
    inicial_demandas    = pd.DataFrame(columns=["Especie", "Polígono", "Demanda"])
    inicial_proveedores = pd.DataFrame(columns=["Proveedor", "Especie", "Costo", "Max_oferta"])


# ------------------------------------------------------------
# 2) TABLAS EDITABLES (cada una con key distinta según escenario)
# ------------------------------------------------------------

# Polígonos
st.subheader("🗺️ Definir Polígonos (ID, X, Y)")
key_pol = f"poligonos_{escenario}"
df_poligonos = st.data_editor(
    inicial_poligonos,
    key=key_pol,
    num_rows="dynamic",
    use_container_width=True
)
try:
    poligonos_coords = {
        int(row["Polígono"]): (float(row["X"]), float(row["Y"]))
        for _, row in df_poligonos.iterrows()
        if pd.notnull(row["Polígono"])
    }
except Exception:
    poligonos_coords = {}

# Demandas
st.subheader("📈 Definir Demandas (Especie, Polígono, Demanda)")
key_dem = f"demandas_{escenario}"
df_demandas = st.data_editor(
    inicial_demandas,
    key=key_dem,
    num_rows="dynamic",
    use_container_width=True
)
demanda_poligonos = {}
for _, row in df_demandas.iterrows():
    if (
        pd.notnull(row["Especie"])
        and pd.notnull(row["Polígono"])
        and pd.notnull(row["Demanda"])
    ):
        esp = str(row["Especie"])
        pid = int(row["Polígono"])
        dem = float(row["Demanda"])
        demanda_poligonos.setdefault(esp, {})[pid] = dem

# Proveedores
st.subheader("🤝 Definir Proveedores (Proveedor, Especie, Costo, Max_oferta)")
key_prov = f"proveedores_{escenario}"
df_proveedores = st.data_editor(
    inicial_proveedores,
    key=key_prov,
    num_rows="dynamic",
    use_container_width=True
)
demandas_oferta = {}
for _, row in df_proveedores.iterrows():
    if (
        pd.notnull(row["Proveedor"])
        and pd.notnull(row["Especie"])
        and pd.notnull(row["Costo"])
        and pd.notnull(row["Max_oferta"])
    ):
        prov = str(row["Proveedor"])
        esp = str(row["Especie"])
        costo = float(row["Costo"])
        max_oferta = float(row["Max_oferta"])
        demandas_oferta.setdefault(prov, {})[esp] = {"costo": costo, "max_oferta": max_oferta}


# ------------------------------------------------------------
# 3) PARÁMETROS LOGÍSTICOS EN EL SIDEBAR
# ------------------------------------------------------------

st.sidebar.header("⚙️ Parámetros de Simulación")
dias_totales = st.sidebar.number_input(
    "Días totales", min_value=1, max_value=30, value=5, step=1
)
aclimatacion_min_dias = st.sidebar.number_input(
    "Días para aclimatación",
    min_value=0,
    max_value=int(dias_totales / 2),
    value=1,
    step=1
)
capacidad_camion = st.sidebar.number_input(
    "Capacidad del camión (unidades)", min_value=1, value=8, step=1
)
jornada_min = st.sidebar.number_input(
    "Minutos por jornada", min_value=60, value=300, step=30
)
espacio_max_almacen = st.sidebar.number_input(
    "Espacio máximo en almacén (unidades)", min_value=1, value=15, step=1
)
costo_transporte = st.sidebar.number_input(
    "Costo transporte por proveedor", min_value=0, value=200, step=50
)
velocidad = st.sidebar.number_input(
    "Velocidad (km/h)", min_value=1.0, value=60.0, step=1.0
)
costo_plantacion = st.sidebar.number_input(
    "Costo plantación por unidad", min_value=0.0, value=1.0, step=0.5
)

# → Nuevos inputs en sidebar: tiempo de carga y descarga
tiempo_carga = st.sidebar.number_input(
    "Tiempo de carga (minutos)", min_value=0, value=1, step=1
)
tiempo_descarga = st.sidebar.number_input(
    "Tiempo de descarga (minutos)", min_value=0, value=1, step=1
)

# Verificar polígono 18 (almacén)
if 18 not in poligonos_coords:
    st.error("❗ Debes incluir el polígono 18 (almacén) en la tabla de Polígonos.")
    st.stop()


# ------------------------------------------------------------
# 4) FUNCIONES DE SIMULACIÓN
# ------------------------------------------------------------

def tiempo_entre(p1, p2):
    distancia = euclidean(poligonos_coords[p1], poligonos_coords[p2])
    return (distancia / velocidad) * 60

def actualizar_inventario(inventario, dia):
    if dia == 0:
        return
    for esp in inventario:
        inventario[esp][dia] += inventario[esp][dia - 1]

def calcular_disponibles(inventario):
    disponibles = {esp: [0] * (dias_totales + 1) for esp in demanda_poligonos}
    for dia in range(dias_totales + 1):
        for esp in demanda_poligonos:
            if dia >= aclimatacion_min_dias:
                disponibles[esp][dia] = inventario[esp][dia - aclimatacion_min_dias]
    return disponibles

def planificar_rutas(dia, disponibles, demanda_restante):
    rutas_dia = []
    entregado = {esp: 0 for esp in demanda_poligonos}
    tiempo_total = 0

    while tiempo_total < jornada_min:
        ruta = [18]
        tiempo_ruta = tiempo_carga
        carga = 0
        detalle = []

        while True:
            last = ruta[-1]
            candidatos = [
                pid
                for esp in demanda_restante
                for pid, d in demanda_restante[esp].items()
                if d > 0
            ]
            if not candidatos:
                break

            # Primer paso: al nodo más lejano desde el almacén
            if len(ruta) == 1:
                candidatos.sort(
                    key=lambda pid: euclidean(poligonos_coords[last], poligonos_coords[pid]),
                    reverse=True
                )
            else:
                # Luego, vecino más cercano
                candidatos.sort(
                    key=lambda pid: euclidean(poligonos_coords[last], poligonos_coords[pid])
                )

            encontrado = False
            for pid in candidatos:
                t_viaje = tiempo_entre(last, pid)
                t_vuelta = tiempo_entre(pid, 18)
                t_extra = t_viaje + tiempo_descarga + t_vuelta
                if tiempo_total + tiempo_ruta + t_extra > jornada_min:
                    continue

                entrega_nodo = {}
                total_nodo = 0
                for esp in demanda_poligonos:
                    disp = disponibles[esp][dia]
                    dem = demanda_restante[esp].get(pid, 0)
                    cap_rest = capacidad_camion - carga - total_nodo
                    q = min(disp, dem, cap_rest)
                    if q > 0:
                        entrega_nodo[esp] = q
                        total_nodo += q

                if total_nodo > 0:
                    ruta.append(pid)
                    tiempo_ruta += t_viaje + tiempo_descarga
                    for esp, q in entrega_nodo.items():
                        disponibles[esp][dia] -= q
                        demanda_restante[esp][pid] -= q
                        entregado[esp] += q
                    carga += total_nodo
                    detalle.append((pid, entrega_nodo))
                    encontrado = True
                    break

            if not encontrado:
                break

        if len(ruta) > 1:
            tiempo_ruta += tiempo_entre(ruta[-1], 18)
            tiempo_total += tiempo_ruta
            rutas_dia.append({
                "Día": dia,
                "Ruta": " → ".join(map(str, ruta + [18])),
                "Duración_min": round(tiempo_ruta),
                "Unidades": carga,
                "Detalle": detalle
            })
        else:
            break

    return rutas_dia, entregado

def procesar_entregas(inventario, entregas, entregado, dia):
    for esp, cantidad in entregado.items():
        if cantidad > 0:
            inventario[esp][dia] -= cantidad
            entregas.append({
                "Especie": esp,
                "Día entrega": dia,
                "Cantidad": cantidad,
                "Costo plantación": cantidad * costo_plantacion
            })

def realizar_compras(inventario, compras, oferta_usada, dia):
    proveedores_hoja = set()
    for esp in demanda_poligonos:
        if dia + aclimatacion_min_dias >= dias_totales:
            continue

        total_dem = sum(demanda_poligonos[esp].values())
        total_cmp = sum(c["Cantidad"] for c in compras if c["Especie"] == esp)
        restante = total_dem - total_cmp

        espacio_disp = espacio_max_almacen - inventario[esp][dia]
        max_posible = min(restante, espacio_disp)
        if max_posible <= 0:
            continue

        opciones = []
        for p, datos in demandas_oferta.items():
            info = datos.get(esp)
            if info:
                disponible_prov = info["max_oferta"] - oferta_usada[p][esp]
                if disponible_prov > 0:
                    opciones.append((p, info["costo"], disponible_prov))
        opciones.sort(key=lambda x: x[1])

        restante_a_comprar = max_posible
        for p_sel, costo, dispo in opciones:
            if restante_a_comprar <= 0:
                break
            cantidad = min(dispo, restante_a_comprar)
            costo_trans = costo_transporte if p_sel not in proveedores_hoja else 0

            compras.append({
                "Especie": esp,
                "Día pedido": dia,
                "Proveedor": p_sel,
                "Cantidad": cantidad,
                "Costo compra": cantidad * costo,
                "Costo transporte": costo_trans
            })
            proveedores_hoja.add(p_sel)
            oferta_usada[p_sel][esp] += cantidad
            inventario[esp][dia + 1] += cantidad

            restante_a_comprar -= cantidad
            espacio_disp -= cantidad

def simular():
    inventario = {esp: [0] * (dias_totales + 1) for esp in demanda_poligonos}
    demanda_restante = {esp: demanda_poligonos[esp].copy() for esp in demanda_poligonos}
    ofertas_usadas = {p: {esp: 0 for esp in demanda_poligonos} for p in demandas_oferta}
    compras = []
    entregas = []
    rutas = []
    lista_inventario = []

    for dia in range(dias_totales):
        actualizar_inventario(inventario, dia)
        row_inv = {"Día": dia}
        for esp in inventario:
            row_inv[esp] = inventario[esp][dia]
        lista_inventario.append(row_inv)

        disponibles = calcular_disponibles(inventario)
        rutas_dia, entregado = planificar_rutas(dia, disponibles, demanda_restante)
        rutas.extend(rutas_dia)
        procesar_entregas(inventario, entregas, entregado, dia)
        realizar_compras(inventario, compras, ofertas_usadas, dia)

    row_inv = {"Día": dias_totales}
    for esp in inventario:
        row_inv[esp] = inventario[esp][dias_totales]
    lista_inventario.append(row_inv)

    df_inventario = pd.DataFrame(lista_inventario)
    df_compras = pd.DataFrame(compras)
    df_entregas = pd.DataFrame(entregas)
    df_rutas = pd.DataFrame(rutas)

    return df_inventario, df_compras, df_entregas, df_rutas

# ------------------------------------------------------------
# 8) EJECUCIÓN DE SIMULACIÓN Y RESULTADOS
# ------------------------------------------------------------

if st.button("🔄 Ejecutar simulación"):
    if len(demanda_poligonos) == 0:
        st.error("❗ Debes definir al menos una demanda en la tabla de Demandas.")
    else:
        with st.spinner("🏃‍♂️ Ejecutando simulación…"):
            df_inventario, df_compras, df_entregas, df_rutas = simular()
        st.success("✅ ¡Simulación completada!")

        # ------------------------------------------------------------
        # 9) KPIs CON TARJETAS GRANDES (st.metric)
        # ------------------------------------------------------------
        num_viajes = len(df_rutas)
        if num_viajes == 0:
            dias_total = 0
            duracion_ultima = 0
        else:
            dias_total = df_rutas["Día"].max()
            duracion_ultima = int(df_rutas.iloc[-1]["Duración_min"])

        costo_compra_sum = df_compras["Costo compra"].sum() if not df_compras.empty else 0
        costo_transp_sum = df_compras["Costo transporte"].sum() if not df_compras.empty else 0
        costo_plant_sum = df_entregas["Costo plantación"].sum() if not df_entregas.empty else 0
        costo_total = costo_compra_sum + costo_transp_sum + costo_plant_sum

        st.subheader("KPIs de la Solución")
        k1, k2, k3 = st.columns(3)
        k1.metric(
            label="🚌 Viajes totales",
            value=f"{num_viajes}"
        )
        k2.metric(
            label="⏱️ Tiempo total",
            value=f"{dias_total}d {duracion_ultima}m"
        )
        k3.metric(
            label="💰 Costo total",
            value=f"${costo_total:.2f}"
        )

        # ------------------------------------------------------------
        # 10) RESULTADOS TABULARES
        # ------------------------------------------------------------
        st.subheader("📊 Inventario Diario")
        st.dataframe(df_inventario, use_container_width=True)

        st.subheader("🛒 Compras Realizadas")
        if not df_compras.empty:
            st.dataframe(df_compras, use_container_width=True)
        else:
            st.info("No se realizaron compras durante la simulación.")

        st.subheader("📦 Entregas Ejecutadas")
        if not df_entregas.empty:
            st.dataframe(df_entregas, use_container_width=True)
        else:
            st.info("No se registraron entregas durante la simulación.")

        st.subheader("🗺️ Rutas Diarias")
        if not df_rutas.empty:
            df_rutas["Detalle"] = df_rutas["Detalle"].astype(str)
            st.dataframe(df_rutas, use_container_width=True)

            st.subheader("📈 Diagrama de Gantt de Rutas")
            def generar_gantt_rutas(df_rutas):
                base = datetime(2025, 1, 1, 9, 0, 0)
                df = df_rutas.copy().reset_index(drop=True)
                df["Start"] = pd.NaT
                df["Finish"] = pd.NaT

                for dia, grupo in df.groupby("Día"):
                    tiempo_acum = 0
                    for idx in grupo.index:
                        inicio = base + timedelta(days=int(dia), minutes=tiempo_acum)
                        dur = int(df.at[idx, "Duración_min"])
                        fin = inicio + timedelta(minutes=dur)

                        df.at[idx, "Start"] = inicio
                        df.at[idx, "Finish"] = fin
                        tiempo_acum += dur

                df["Task"] = "Día " + df["Día"].astype(str) + " – ruta " + df.index.astype(str)

                fig = px.timeline(
                    df,
                    x_start="Start",
                    x_end="Finish",
                    y="Task",
                    color="Día",
                    title="Diagrama de Gantt de Rutas",
                    labels={"Día": "Día", "Task": "Ruta"}
                )
                fig.update_yaxes(autorange="reversed")
                fig.update_layout(
                    xaxis_title="Fecha y hora",
                    margin=dict(l=200, r=40, t=80, b=40),
                    height=150 + 30 * len(df)
                )
                return fig

            fig_rutas = generar_gantt_rutas(df_rutas)
            st.plotly_chart(fig_rutas, use_container_width=True)
        else:
            st.info("No hay rutas para graficar.")
