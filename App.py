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
    ["Ninguno", "Ejemplo Completo"]
)

# ------------------------------------------------------------
# 2) FUNCIONES PARA CREAR EL ESCENARIO COMPLETO
# ------------------------------------------------------------

def crear_poligonos_completo():
    # IDs dados: 1, 3, 4, 5, 20, 23, 24, 18, 17, 16, 19, 25, 26
    # Coordenadas arbitrarias para cada polígono (puedes ajustar si tienes datos reales)
    coords = {
        1:  ( 0,  0),
        3:  (10,  0),
        4:  (20,  0),
        5:  (30,  0),
        20: ( 0, 10),
        23: (10, 10),
        24: (20, 10),
        19: (40, 10),
        25: (50, 10),
        26: (60, 10),
        18: (20, 20),
        17: (30, 20),
        16: (40, 20),

    }
    df = pd.DataFrame([
        {"Polígono": pid, "X": x, "Y": y}
        for pid, (x, y) in coords.items()
    ])
    return df

def crear_demandas_completo():
    # Hectáreas por polígono
    hectareas = {
        1:  5.40,
        3:  8.00,
        4:  8.00,
        5:  7.56,
        20: 1.38,
        23: 5.53,
        24: 5.64,
        18: 7.11,
        17: 6.11,
        16: 5.64,
        19: 4.92,
        25: 5.05,
        26: 4.75,
    }
    # Densidad por hectárea (unidades/ha) de cada especie
    densidad = {
        "Lechugilla":            33,
        "Maguey Verde Salmiana": 157,
        "Maguey azul":           33,
        "Maguey Verde Striata":  33,
        "Cuijo cantabriginesis":  39,
        "Cuijo engelmani":       30,
        "Tapón":                 58,
        "Cardón":                51,
        "Mezquite":              69,
        "palma china":           21
    }

    filas = []
    for pid, ha in hectareas.items():
        for esp, d in densidad.items():
            demanda_unidades = int(round(ha * d))
            filas.append({
                "Especie":   esp,
                "Polígono":  pid,
                "Demanda":   demanda_unidades
            })
    df = pd.DataFrame(filas)
    return df

def crear_proveedores_completo():
    # Cada proveedor y las especies que ofrece con su costo; max_oferta = 10000 (genérico)
    filas = []
    # Vivero: Mezquite a 26.5, palma china a 26
    filas.extend([
        {"Proveedor": "Vivero", "Especie": "Mezquite",    "Costo": 26.5, "Max_oferta": 10000},
        {"Proveedor": "Vivero", "Especie": "palma china", "Costo": 26.0, "Max_oferta": 10000},
    ])
    # Moctezuma: Maguey azul y Maguey Verde Striata a 26; Cuijo cantabriginesis y Tapón a 17
    filas.extend([
        {"Proveedor": "Moctezuma", "Especie": "Maguey azul",            "Costo": 26.0, "Max_oferta": 10000},
        {"Proveedor": "Moctezuma", "Especie": "Maguey Verde Striata",   "Costo": 26.0, "Max_oferta": 10000},
        {"Proveedor": "Moctezuma", "Especie": "Cuijo cantabriginesis",  "Costo": 17.0, "Max_oferta": 10000},
        {"Proveedor": "Moctezuma", "Especie": "Tapón",                  "Costo": 17.0, "Max_oferta": 10000},
    ])
    # Venado: Maguey Verde Striata a 25; Cuijo cantabriginesis, Cuijo engelmani, Tapón, Cardón a 18
    filas.extend([
        {"Proveedor": "Venado", "Especie": "Maguey Verde Striata",      "Costo": 25.0, "Max_oferta": 10000},
        {"Proveedor": "Venado", "Especie": "Cuijo cantabriginesis",      "Costo": 18.0, "Max_oferta": 10000},
        {"Proveedor": "Venado", "Especie": "Cuijo engelmani",           "Costo": 18.0, "Max_oferta": 10000},
        {"Proveedor": "Venado", "Especie": "Tapón",                     "Costo": 18.0, "Max_oferta": 10000},
        {"Proveedor": "Venado", "Especie": "Cardón",                    "Costo": 18.0, "Max_oferta": 10000},
    ])
    # Laguna seca: Lechugilla, Maguey Verde Salmiana, Maguey azul a 26; Cuijo engelmani a 21; Tapón a 18
    filas.extend([
        {"Proveedor": "Laguna seca", "Especie": "Lechugilla",           "Costo": 26.0, "Max_oferta": 10000},
        {"Proveedor": "Laguna seca", "Especie": "Maguey Verde Salmiana","Costo": 26.0, "Max_oferta": 10000},
        {"Proveedor": "Laguna seca", "Especie": "Maguey azul",          "Costo": 26.0, "Max_oferta": 10000},
        {"Proveedor": "Laguna seca", "Especie": "Cuijo engelmani",      "Costo": 21.0, "Max_oferta": 10000},
        {"Proveedor": "Laguna seca", "Especie": "Tapón",                "Costo": 18.0, "Max_oferta": 10000},
    ])

    df = pd.DataFrame(filas)
    return df

# Según el escenario, definimos los DataFrames iniciales
if escenario == "Ejemplo Completo":
    inicial_poligonos   = crear_poligonos_completo()
    inicial_demandas    = crear_demandas_completo()
    inicial_proveedores = crear_proveedores_completo()
else:
    inicial_poligonos   = pd.DataFrame(columns=["Polígono", "X", "Y"])
    inicial_demandas    = pd.DataFrame(columns=["Especie", "Polígono", "Demanda"])
    inicial_proveedores = pd.DataFrame(columns=["Proveedor", "Especie", "Costo", "Max_oferta"])


# ------------------------------------------------------------
# 3) TABLAS EDITABLES
# ------------------------------------------------------------

# 3.1 Polígonos
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

# 3.2 Demandas
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

# 3.3 Proveedores
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
# 4) PARÁMETROS LOGÍSTICOS EN EL SIDEBAR
# ------------------------------------------------------------

st.sidebar.header("⚙️ Parámetros de Simulación")
dias_totales = st.sidebar.number_input(
    "Días totales", min_value=1, max_value=1000, value=5, step=1
)
aclimatacion_min_dias = st.sidebar.number_input(
    "Días para aclimatación",
    min_value=0,
    max_value=5,
    value=3,  # mínimo de 3 días según PDF
    step=1
)
capacidad_camion = st.sidebar.number_input(
    "Capacidad del camión (unidades)", min_value=1, value=8000, step=100
)
jornada_min = st.sidebar.number_input(
    "Minutos por jornada", min_value=60, value=360, step=30
)
espacio_max_almacen = st.sidebar.number_input(
    "Espacio máximo en almacén (unidades)", min_value=1, value=4000, step=100
)
costo_transporte = st.sidebar.number_input(
    "Costo transporte por viaje", min_value=0, value=4500, step=500
)
velocidad = st.sidebar.number_input(
    "Velocidad (km/h)", min_value=1.0, value=60.0, step=1.0
)
costo_plantacion = st.sidebar.number_input(
    "Costo plantación por unidad", min_value=0.0, value=20.0, step=1.0
)

# Nuevos inputs en sidebar: tiempo de carga y descarga
tiempo_carga = st.sidebar.number_input(
    "Tiempo de carga (minutos)", min_value=0, value=30, step=5
)
tiempo_descarga = st.sidebar.number_input(
    "Tiempo de descarga (minutos)", min_value=0, value=30, step=5
)

# Verificar polígono 18 (almacén)
if 18 not in poligonos_coords:
    st.error("❗ Debes incluir el polígono 18 (almacén) en la tabla de Polígonos.")
    st.stop()


# ------------------------------------------------------------
# 5) FUNCIONES DE SIMULACIÓN
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
        disponible_hoy = inventario[esp][dia]
        a_entregar = min(disponible_hoy, cantidad)

        if a_entregar > 0:
            inventario[esp][dia] -= a_entregar
            entregas.append({
                "Especie":      esp,
                "Día entrega":  dia,
                "Cantidad":     a_entregar,
                "Costo plantación": a_entregar * costo_plantacion
            })

def realizar_compras(inventario, compras, oferta_usada, dia):
    """
    Compra todas las especies que hagan falta para reponer el inventario,
    cobrando un solo costo de transporte por día, y asegurándose de que
    el espacio en almacén (espacio_max_almacen) se trate como un total agregado.
    """
    # 1) Flag para cobrar transporte solo una vez por día
    transporte_cobrado = False

    # 2) Calculamos cuánto hay en total en inventario en el día 'dia'
    total_en_almacen = sum(inventario[esp][dia] for esp in inventario)
    espacio_libre_total = espacio_max_almacen - total_en_almacen
    # Si ya está lleno o no hay espacio, no compramos nada:
    if espacio_libre_total <= 0:
        return

    # 3) Iteramos especie por especie para reponer demanda
    for esp in demanda_poligonos:
        # Ya no alcanzaría a llegar (si no cabe en almacén para aclimatar):
        if dia + aclimatacion_min_dias >= dias_totales:
            continue

        # Demanda total de esta especie (sobre todos los polígonos)
        total_dem = sum(demanda_poligonos[esp].values())
        # Cuánto ya se compró de esta especie (sumamos en 'compras')
        total_cmp = sum(c["Cantidad"] for c in compras if c["Especie"] == esp)
        restante = total_dem - total_cmp

        if restante <= 0:
            continue

        # Ahora el espacio disponible para esta especie es
        # el "espacio_libre_total", no un valor por especie.
        if espacio_libre_total <= 0:
            break  # ya no cabe nada más en almacén

        max_posible = min(restante, espacio_libre_total)

        # Recolectamos las ofertas disponibles de proveedores para esta especie
        opciones = []
        for p, datos in demandas_oferta.items():
            info = datos.get(esp)
            if info:
                dispo = info["max_oferta"] - oferta_usada[p][esp]
                if dispo > 0:
                    opciones.append((p, info["costo"], dispo))
        opciones.sort(key=lambda x: x[1])  # orden por costo ascendente

        restante_a_comprar = max_posible
        for p_sel, costo_unit, dispo in opciones:
            if restante_a_comprar <= 0 or espacio_libre_total <= 0:
                break
            cantidad = min(dispo, restante_a_comprar, espacio_libre_total)

            # 4) Cobro único de transporte por día:
            costo_trans = 0
            if not transporte_cobrado:
                costo_trans = costo_transporte
                transporte_cobrado = True

            compras.append({
                "Especie":          esp,
                "Día pedido":       dia,
                "Proveedor":        p_sel,
                "Cantidad":         cantidad,
                "Costo compra":     cantidad * costo_unit,
                "Costo transporte": costo_trans
            })

            # Actualizamos oferta usada y espacio en almacén para este día + 1
            oferta_usada[p_sel][esp] += cantidad
            inventario[esp][dia + 1] += cantidad

            # Reducimos el espacio libre total
            espacio_libre_total -= cantidad
            restante_a_comprar -= cantidad

            # Si se acabó el espacio, salimos de ambos bucles
            if espacio_libre_total <= 0:
                break


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
# 6) EJECUCIÓN DE SIMULACIÓN Y RESULTADOS
# ------------------------------------------------------------
if st.button("🔄 Ejecutar simulación"):
    if len(demanda_poligonos) == 0:
        st.error("❗ Debes definir al menos una demanda en la tabla de Demandas.")
    else:
        with st.spinner("🏃‍♂️ Ejecutando simulación…"):
            df_inventario, df_compras, df_entregas, df_rutas = simular()
        st.success("✅ ¡Simulación completada!")

        # ------------------------------------------------------------
        # 7) KPIs CON TARJETAS GRANDES (st.metric)
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
                # … después de tus k1.metric, k2.metric, k3.metric …

        # ------------------------------------------------------------
        # → NUEVAS MÉTRICAS DE EFICIENCIA
        # ------------------------------------------------------------
        # 1) Unidades demandadas totales
        total_demandadas = sum(
            d for esp in demanda_poligonos 
            for d in demanda_poligonos[esp].values()
        )

        # 2) Unidades efectivamente entregadas
        total_entregadas = df_entregas["Cantidad"].sum() if not df_entregas.empty else 0

        # Fill Rate
        fill_rate = (total_entregadas / total_demandadas * 100) if total_demandadas > 0 else 0

        # Utilización media de camión
        if len(df_rutas) > 0:
            utilizaciones = df_rutas["Unidades"] / capacidad_camion
            util_media = utilizaciones.mean() * 100
        else:
            util_media = 0

        # Costo unitario
        coste_unitario = (costo_total / total_entregadas) if total_entregadas > 0 else 0

        # Mostrar con st.metric
        um1, um2, um3, um4 = st.columns(4)
        um1.metric(
            label="📦 Fill Rate",
            value=f"{fill_rate:.1f}%",
            delta=f"{total_entregadas}/{total_demandadas}"
        )
        um2.metric(
            label="🚚 Utilización media",
            value=f"{util_media:.1f}%",
            delta=f"Camión cap. {capacidad_camion}"
        )
        um3.metric(
            label="💲 Costo unidad",
            value=f"${coste_unitario:,.2f}",
            delta="promedio"
        )
        um4.metric(
            label="📊 Unidades entregadas",
            value=f"{total_entregadas}"
        )


        # ------------------------------------------------------------
        # 8) RESULTADOS TABULARES
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
