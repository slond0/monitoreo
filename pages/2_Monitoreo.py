import streamlit as st
import paho.mqtt.client as mqtt
import time
from PIL import Image
import io
import numpy as np
import pandas as pd

# ─────────────────────────────────────────
#  CONFIG MQTT
# ─────────────────────────────────────────
BROKER          = "broker.hivemq.com"
PORT            = 1883
TOPIC_ACTIVIDAD = "petbuddy/sofia/actividad"    # suscribe  — PIR ESP32
TOPIC_ALERTA    = "petbuddy/sofia/alerta"       # publica   — cámara→ESP32
TOPIC_SERVO     = "petbuddy/sofia/servo"        # publica   — alimentar
TOPIC_CONFIRM   = "petbuddy/sofia/confirmacion" # suscribe  — ESP32 ok

# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="PetBuddy",
    page_icon="🐾",
    layout="wide",
)

# ─────────────────────────────────────────
#  ESTILOS GLOBALES
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@400;600;800&family=Nunito:wght@300;400;600&display=swap');

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #fdf6ec 0%, #fce8d5 50%, #f5dac8 100%);
    font-family: 'Nunito', sans-serif;
}
[data-testid="stHeader"]  { background: transparent; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fff8f0 0%, #ffe9d0 100%);
    border-right: 2px solid #f3c89a;
}
.pet-title {
    font-family: 'Baloo 2', cursive;
    font-size: 2.6rem;
    font-weight: 800;
    color: #d9622b;
    text-align: center;
    line-height: 1.1;
    margin-bottom: 0;
}
.pet-subtitle {
    font-size: 1rem;
    color: #b07040;
    text-align: center;
    margin-top: 0.2rem;
    margin-bottom: 1.2rem;
}
.paw-divider {
    text-align: center;
    font-size: 1.4rem;
    color: #f3c89a;
    margin: 0.5rem 0 1.2rem 0;
    letter-spacing: 10px;
}
.card {
    background: rgba(255,255,255,0.75);
    border-radius: 20px;
    padding: 1.4rem 1.6rem;
    box-shadow: 0 4px 18px rgba(210,120,50,0.12);
    border: 1.5px solid #f3c89a;
    margin-bottom: 1rem;
}
.card-title {
    font-family: 'Baloo 2', cursive;
    font-size: 1.1rem;
    font-weight: 600;
    color: #b05a20;
    margin-bottom: 0.4rem;
}
.badge-active {
    display:inline-block; background:#d9f7be; color:#389e0d;
    border-radius:50px; padding:.25rem 1rem; font-weight:700; font-size:1rem;
}
.badge-sleep {
    display:inline-block; background:#e6e6ff; color:#5050c0;
    border-radius:50px; padding:.25rem 1rem; font-weight:700; font-size:1rem;
}
.badge-none {
    display:inline-block; background:#f5f5f5; color:#888;
    border-radius:50px; padding:.25rem 1rem; font-weight:700; font-size:1rem;
}
.section-header {
    font-family: 'Baloo 2', cursive;
    font-size: 1.5rem;
    font-weight: 700;
    color: #c0501a;
    border-left: 5px solid #f09a4a;
    padding-left: 0.7rem;
    margin: 1.2rem 0 0.6rem 0;
}
.dog-alert {
    background: linear-gradient(90deg, #fff3e0, #ffe0b2);
    border: 2px solid #f09a4a;
    border-radius: 16px;
    padding: 1rem 1.4rem;
    font-family: 'Baloo 2', cursive;
    font-size: 1.1rem;
    color: #bf4f00;
    text-align: center;
}
.feed-count {
    font-family: 'Baloo 2', cursive;
    font-size: 3rem;
    font-weight: 800;
    color: #d9622b;
    text-align: center;
}
.feed-label {
    font-size: 0.9rem;
    color: #b07040;
    text-align: center;
    margin-top: -0.5rem;
}
div[data-testid="stButton"] button {
    background: linear-gradient(90deg, #f09a4a, #d9622b);
    color: white;
    border: none;
    border-radius: 50px;
    font-family: 'Baloo 2', cursive;
    font-weight: 600;
    font-size: 1rem;
    padding: 0.5rem 1.8rem;
    transition: opacity 0.2s;
}
div[data-testid="stButton"] button:hover { opacity: 0.85; }

/* Tabs */
div[data-testid="stTabs"] button {
    font-family: 'Baloo 2', cursive !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  ESTADO DE SESIÓN
# ─────────────────────────────────────────
defaults = {
    "estado_mascota":   "Sin actividad",
    "dog_detected":     False,
    "last_detection":   None,
    "veces_alimentado": 0,
    "ultimo_feed":      None,
    "confirmado":       False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────
#  MQTT — UN SOLO CLIENTE para toda la app
# ─────────────────────────────────────────
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    topic   = msg.topic
    if topic == TOPIC_ACTIVIDAD:
        if payload == "movimiento":
            st.session_state.estado_mascota = "Activa 🐶"
        elif payload == "quieta":
            st.session_state.estado_mascota = "Dormida 😴"
    elif topic == TOPIC_CONFIRM:
        if payload == "ok":
            st.session_state.confirmado = True

@st.cache_resource
def get_mqtt_client():
    client = mqtt.Client()
    client.on_message = on_message
    try:
        client.connect(BROKER, PORT, 60)
        client.subscribe(TOPIC_ACTIVIDAD)
        client.subscribe(TOPIC_CONFIRM)
        client.loop_start()
        return client
    except Exception:
        return None

mqtt_client = get_mqtt_client()

# ─────────────────────────────────────────
#  YOLO — carga única
# ─────────────────────────────────────────
@st.cache_resource
def load_model():
    try:
        from ultralytics import YOLO
        return YOLO("yolov5su.pt")
    except Exception:
        return None

# ─────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🐾 PetBuddy")
    st.markdown("---")
    st.markdown("**Estado MQTT**")
    if mqtt_client:
        st.success("🟢 Conectado al broker")
    else:
        st.error("🔴 Sin conexión MQTT")
    st.markdown("---")
    st.markdown("**Detección YOLO**")
    conf_threshold = st.slider("Confianza mínima", 0.0, 1.0, 0.25, 0.01)
    iou_threshold  = st.slider("Umbral IoU",       0.0, 1.0, 0.45, 0.01)
    max_det        = st.number_input("Detecciones máx.", 10, 500, 100, 10)
    st.markdown("---")
    st.caption("dog · cat · bird vigilados")

# ─────────────────────────────────────────
#  CABECERA
# ─────────────────────────────────────────
st.markdown('<p class="pet-title">🐾 PetBuddy</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="pet-subtitle">Monitoreo inteligente de tu mascota · IoT + IA</p>',
    unsafe_allow_html=True,
)
st.markdown('<div class="paw-divider">🐾 🐾 🐾</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
#  TABS PRINCIPALES
# ─────────────────────────────────────────
tab_monitor, tab_feed = st.tabs(["📡  Monitoreo", "🍖  Alimentar"])

# ══════════════════════════════════════════
#  TAB 1 — MONITOREO
# ══════════════════════════════════════════
with tab_monitor:

    estado = st.session_state.estado_mascota

    # Avatar + estado
    col_av, col_st = st.columns([1, 2], gap="large")

    with col_av:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if "Activa" in estado:
            st.image("https://cdn-icons-png.flaticon.com/512/616/616430.png", width=170)
        else:
            st.image("https://cdn-icons-png.flaticon.com/512/2138/2138440.png", width=170)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_st:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Estado del sensor de movimiento</div>',
                    unsafe_allow_html=True)

        if "Activa" in estado:
            st.markdown(f'<span class="badge-active">{estado}</span>',
                        unsafe_allow_html=True)
            st.success("La mascota está activa y moviéndose 🏃")
        elif "Dormida" in estado:
            st.markdown(f'<span class="badge-sleep">{estado}</span>',
                        unsafe_allow_html=True)
            st.info("La mascota está descansando 💤")
        else:
            st.markdown(f'<span class="badge-none">{estado}</span>',
                        unsafe_allow_html=True)
            st.warning("Esperando señal del sensor...")

        if st.session_state.dog_detected:
            st.markdown(
                '<div class="dog-alert">🚨 ¡Mascota detectada por cámara!</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # Cámara + YOLO
    st.markdown('<div class="section-header">📷 Detector por cámara</div>',
                unsafe_allow_html=True)

    with st.spinner("Cargando modelo YOLOv5..."):
        model = load_model()

    if model is None:
        st.error("❌ No se pudo cargar YOLOv5. Verifica que `ultralytics` esté en requirements.txt")
    else:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("Apunta la cámara a tu mascota. Detecta **perro**, **gato** y **ave** automáticamente.")

        picture = st.camera_input("📸 Capturar imagen", key="camera_pet")

        if picture:
            bytes_data = picture.getvalue()
            pil_img    = Image.open(io.BytesIO(bytes_data)).convert("RGB")
            np_img     = np.array(pil_img)[..., ::-1]

            with st.spinner("🔍 Analizando imagen..."):
                try:
                    results = model(
                        np_img,
                        conf    = conf_threshold,
                        iou     = iou_threshold,
                        max_det = int(max_det),
                    )
                except Exception as e:
                    st.error(f"Error en detección: {e}")
                    st.stop()

            result        = results[0]
            boxes         = result.boxes
            annotated_rgb = result.plot()[:, :, ::-1]

            PET_CLASSES     = {"dog", "cat", "bird"}
            label_names     = model.names
            detected_labels = set()

            if boxes is not None and len(boxes) > 0:
                for box in boxes:
                    detected_labels.add(label_names[int(box.cls.item())])

            pet_found = bool(detected_labels & PET_CLASSES)
            st.session_state.dog_detected = pet_found

            if mqtt_client:
                mqtt_client.publish(
                    TOPIC_ALERTA,
                    "alerta" if pet_found else "sin_deteccion"
                )

            if pet_found:
                pets_str = " · ".join(
                    f"🐾 {p}" for p in detected_labels if p in PET_CLASSES
                )
                st.markdown(
                    f'<div class="dog-alert">¡Mascota detectada! {pets_str}</div>',
                    unsafe_allow_html=True,
                )
                st.balloons()
            else:
                st.info("No se detectaron mascotas. Reduce el umbral de confianza si es necesario.")

            col_img, col_tbl = st.columns(2, gap="medium")
            with col_img:
                st.markdown("**Imagen analizada**")
                st.image(annotated_rgb, use_container_width=True)
            with col_tbl:
                st.markdown("**Objetos detectados**")
                if boxes is not None and len(boxes) > 0:
                    cat_count, cat_conf = {}, {}
                    for box in boxes:
                        c    = int(box.cls.item())
                        conf = float(box.conf.item())
                        cat_count[c] = cat_count.get(c, 0) + 1
                        cat_conf.setdefault(c, []).append(conf)
                    data = [
                        {
                            "Objeto":    label_names[c],
                            "Cantidad":  cnt,
                            "Confianza": f"{np.mean(cat_conf[c]):.0%}",
                            "Mascota":   "🐾" if label_names[c] in PET_CLASSES else "–",
                        }
                        for c, cnt in cat_count.items()
                    ]
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.bar_chart(df.set_index("Objeto")["Cantidad"])

        st.markdown('</div>', unsafe_allow_html=True)

    # Auto-refresh MQTT solo si no hay foto activa
    col_r, col_cap = st.columns([1, 4])
    with col_r:
        if st.button("🔄 Actualizar"):
            st.rerun()
    with col_cap:
        st.caption("Se actualiza cada 3s automáticamente cuando no hay foto activa")

    if st.session_state.get("camera_pet") is None:
        time.sleep(3)
        st.rerun()

# ══════════════════════════════════════════
#  TAB 2 — ALIMENTAR
# ══════════════════════════════════════════
with tab_feed:

    col_img2, col_ctrl = st.columns([1, 2], gap="large")

    with col_img2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.image(
    "https://cdn-icons-png.flaticon.com/512/616/616408.png",
    width=180,
)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_ctrl:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Control del dispensador</div>',
                    unsafe_allow_html=True)

        if st.button("🍖 ¡Alimentar ahora!"):
            if mqtt_client:
                mqtt_client.publish(TOPIC_SERVO, "alimentar")
                st.session_state.veces_alimentado += 1
                st.session_state.ultimo_feed      = time.strftime("%H:%M:%S")
                st.session_state.confirmado       = False
                st.success("✅ Comando enviado al dispensador")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Sin conexión MQTT")

        if st.session_state.confirmado:
            st.info("🤖 ESP32 confirmó: servo activado")

        if st.session_state.ultimo_feed:
            st.caption(f"Última alimentación: {st.session_state.ultimo_feed}")

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    col_cnt, col_how = st.columns(2, gap="medium")

    with col_cnt:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            f'<div class="feed-count">{st.session_state.veces_alimentado}</div>'
            '<div class="feed-label">veces alimentado hoy</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with col_how:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">¿Cómo funciona?</div>',
                    unsafe_allow_html=True)
        st.markdown("""
1. Presiona el botón de alimentar
2. Streamlit publica `alimentar` por MQTT
3. El ESP32 recibe el mensaje
4. El servo gira y dispensa la comida
5. El ESP32 responde `ok` de confirmación
        """)
        st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────
st.markdown("---")
st.caption("PetBuddy · MQTT + YOLOv5 + ESP32 · Sensor de movimiento + cámara inteligente")
