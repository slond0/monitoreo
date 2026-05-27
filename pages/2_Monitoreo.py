import streamlit as st
import paho.mqtt.client as mqtt
import time
from PIL import Image
import io
import numpy as np
import pandas as pd

# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────
BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC  = "petbuddy/sofia/actividad"

# ─────────────────────────────────────────
#  PAGE CONFIG  (debe ir primero)
# ─────────────────────────────────────────
st.set_page_config(
    page_title="PetBuddy – Monitoreo",
    page_icon="🐾",
    layout="wide",
)

# ─────────────────────────────────────────
#  ESTILOS GLOBALES
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@400;600;800&family=Nunito:wght@300;400;600&display=swap');

/* Fondo general */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #fdf6ec 0%, #fce8d5 50%, #f5dac8 100%);
    font-family: 'Nunito', sans-serif;
}
[data-testid="stHeader"] { background: transparent; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fff8f0 0%, #ffe9d0 100%);
    border-right: 2px solid #f3c89a;
}

/* Título principal */
.pet-title {
    font-family: 'Baloo 2', cursive;
    font-size: 2.8rem;
    font-weight: 800;
    color: #d9622b;
    text-align: center;
    letter-spacing: -0.5px;
    line-height: 1.1;
    margin-bottom: 0;
}
.pet-subtitle {
    font-family: 'Nunito', sans-serif;
    font-size: 1rem;
    color: #b07040;
    text-align: center;
    margin-top: 0.2rem;
    margin-bottom: 1.5rem;
}

/* Tarjetas de estado */
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
    font-size: 1.15rem;
    font-weight: 600;
    color: #b05a20;
    margin-bottom: 0.4rem;
}

/* Badge de estado */
.badge-active {
    display: inline-block;
    background: #d9f7be;
    color: #389e0d;
    border-radius: 50px;
    padding: 0.25rem 1rem;
    font-weight: 700;
    font-size: 1.05rem;
}
.badge-sleep {
    display: inline-block;
    background: #e6e6ff;
    color: #5050c0;
    border-radius: 50px;
    padding: 0.25rem 1rem;
    font-weight: 700;
    font-size: 1.05rem;
}
.badge-none {
    display: inline-block;
    background: #f5f5f5;
    color: #888;
    border-radius: 50px;
    padding: 0.25rem 1rem;
    font-weight: 700;
    font-size: 1.05rem;
}

/* Sección de detección */
.section-header {
    font-family: 'Baloo 2', cursive;
    font-size: 1.6rem;
    font-weight: 700;
    color: #c0501a;
    border-left: 5px solid #f09a4a;
    padding-left: 0.7rem;
    margin: 1.5rem 0 0.7rem 0;
}

/* Alerta perro detectado */
.dog-alert {
    background: linear-gradient(90deg, #fff3e0, #ffe0b2);
    border: 2px solid #f09a4a;
    border-radius: 16px;
    padding: 1rem 1.4rem;
    font-family: 'Baloo 2', cursive;
    font-size: 1.2rem;
    color: #bf4f00;
    text-align: center;
    animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(240,154,74,0.4); }
    50%       { box-shadow: 0 0 0 10px rgba(240,154,74,0); }
}

/* Botón de refrescar */
div[data-testid="stButton"] button {
    background: linear-gradient(90deg, #f09a4a, #d9622b);
    color: white;
    border: none;
    border-radius: 50px;
    font-family: 'Baloo 2', cursive;
    font-weight: 600;
    padding: 0.5rem 1.8rem;
    font-size: 1rem;
    transition: opacity 0.2s;
}
div[data-testid="stButton"] button:hover { opacity: 0.85; }

/* Separador decorativo */
.paw-divider {
    text-align: center;
    font-size: 1.5rem;
    color: #f3c89a;
    margin: 0.8rem 0;
    letter-spacing: 10px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  ESTADO DE SESIÓN
# ─────────────────────────────────────────
if "estado_mascota" not in st.session_state:
    st.session_state.estado_mascota = "Sin actividad"
if "dog_detected" not in st.session_state:
    st.session_state.dog_detected = False
if "last_detection" not in st.session_state:
    st.session_state.last_detection = None
if "mqtt_connected" not in st.session_state:
    st.session_state.mqtt_connected = False

# ─────────────────────────────────────────
#  MQTT
# ─────────────────────────────────────────
def on_message(client, userdata, msg):
    mensaje = msg.payload.decode()
    if mensaje == "movimiento":
        st.session_state.estado_mascota = "Activa 🐶"
    elif mensaje == "quieta":
        st.session_state.estado_mascota = "Dormida 😴"

@st.cache_resource
def get_mqtt_client():
    client = mqtt.Client()
    client.on_message = on_message
    try:
        client.connect(BROKER, PORT, 60)
        client.subscribe(TOPIC)
        client.loop_start()
        st.session_state.mqtt_connected = True
        return client
    except Exception:
        return None

mqtt_client = get_mqtt_client()

# ─────────────────────────────────────────
#  MODELO YOLO
# ─────────────────────────────────────────
@st.cache_resource
def load_model():
    try:
        from ultralytics import YOLO
        model = YOLO("yolov5su.pt")
        return model
    except Exception as e:
        return None

# ─────────────────────────────────────────
#  SIDEBAR – parámetros de detección
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🐾 PetBuddy")
    st.markdown("**Configuración de detección**")
    conf_threshold = st.slider("Confianza mínima", 0.0, 1.0, 0.25, 0.01)
    iou_threshold  = st.slider("Umbral IoU",       0.0, 1.0, 0.45, 0.01)
    max_det        = st.number_input("Detecciones máx.", 10, 500, 100, 10)

    st.markdown("---")
    st.markdown("**Estado MQTT**")
    if mqtt_client:
        st.success("🟢 Conectado al broker")
    else:
        st.error("🔴 Sin conexión MQTT")

    st.markdown("---")
    st.markdown("**Clases vigiladas**")
    st.info("🐕 dog  •  🐈 cat  •  🐦 bird")
    st.caption(f"Topic: `{TOPIC}`")

# ─────────────────────────────────────────
#  CABECERA
# ─────────────────────────────────────────
st.markdown('<p class="pet-title">🐾 PetBuddy – Monitoreo</p>', unsafe_allow_html=True)
st.markdown('<p class="pet-subtitle">Actividad en tiempo real + detección de mascota por cámara</p>', unsafe_allow_html=True)
st.markdown('<div class="paw-divider">🐾 🐾 🐾</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
#  FILA 1 – Estado MQTT + avatar
# ─────────────────────────────────────────
col_avatar, col_status = st.columns([1, 2], gap="large")

estado = st.session_state.estado_mascota

with col_avatar:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if "Activa" in estado:
        st.image("https://cdn-icons-png.flaticon.com/512/616/616430.png", width=180)
    else:
        st.image("https://cdn-icons-png.flaticon.com/512/2138/2138440.png", width=180)
    st.markdown('</div>', unsafe_allow_html=True)

with col_status:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Estado del sensor de movimiento</div>', unsafe_allow_html=True)

    if "Activa" in estado:
        st.markdown(f'<span class="badge-active">{estado}</span>', unsafe_allow_html=True)
        st.success("La mascota está activa y moviéndose 🏃")
    elif "Dormida" in estado:
        st.markdown(f'<span class="badge-sleep">{estado}</span>', unsafe_allow_html=True)
        st.info("La mascota está descansando 💤")
    else:
        st.markdown(f'<span class="badge-none">{estado}</span>', unsafe_allow_html=True)
        st.warning("Esperando señal del sensor...")

    st.markdown("<br>", unsafe_allow_html=True)

    # Alerta de cámara si se detectó perro
    if st.session_state.dog_detected:
        st.markdown(
            '🚨 <strong>¡Mascota detectada por cámara!</strong> La cámara confirmó presencia de tu perro.',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
#  FILA 2 – Detección por cámara
# ─────────────────────────────────────────
st.markdown('<div class="section-header">📷 Detector de mascota por cámara</div>', unsafe_allow_html=True)

with st.spinner("Cargando modelo de detección YOLOv5..."):
    model = load_model()

if model is None:
    st.error("❌ No se pudo cargar YOLOv5. Verifica que `ultralytics` esté instalado: `pip install ultralytics`")
else:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("Apunta la cámara hacia tu mascota. El sistema detectará automáticamente si aparece un **perro**, **gato** u otro animal.")

    picture = st.camera_input("📸 Capturar imagen", key="camera_pet")

    if picture:
        bytes_data = picture.getvalue()
        pil_img    = Image.open(io.BytesIO(bytes_data)).convert("RGB")
        np_img     = np.array(pil_img)[..., ::-1]   # RGB → BGR para YOLO

        with st.spinner("🔍 Analizando imagen..."):
            try:
                results = model(
                    np_img,
                    conf    = conf_threshold,
                    iou     = iou_threshold,
                    max_det = int(max_det),
                )
            except Exception as e:
                st.error(f"Error en la detección: {e}")
                st.stop()

        result        = results[0]
        boxes         = result.boxes
        annotated     = result.plot()
        annotated_rgb = annotated[:, :, ::-1]   # BGR → RGB

        # ¿Hay perro en la imagen?
        PET_CLASSES = {"dog", "cat", "bird"}
        label_names = model.names
        detected_labels = set()
        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                name = label_names[int(box.cls.item())]
                detected_labels.add(name)

        pet_found = bool(detected_labels & PET_CLASSES)
        st.session_state.dog_detected = pet_found
        st.session_state.last_detection = detected_labels

        # Alerta visual
        if pet_found:
            pets_str = " • ".join(
                f"🐾 {p}" for p in detected_labels if p in PET_CLASSES
            )
            st.markdown(
                f'<div class="dog-alert">¡Mascota detectada! &nbsp; {pets_str}</div>',
                unsafe_allow_html=True,
            )
            st.balloons()
        else:
            st.info("No se detectaron mascotas en la imagen.")

        # Columnas: imagen anotada + tabla
        col_img, col_table = st.columns(2, gap="medium")

        with col_img:
            st.markdown("**Imagen analizada**")
            st.image(annotated_rgb, use_container_width=True)

        with col_table:
            st.markdown("**Objetos detectados**")
            if boxes is not None and len(boxes) > 0:
                cat_count: dict = {}
                cat_conf:  dict = {}
                for box in boxes:
                    cat  = int(box.cls.item())
                    conf = float(box.conf.item())
                    cat_count[cat] = cat_count.get(cat, 0) + 1
                    cat_conf.setdefault(cat, []).append(conf)

                data = [
                    {
                        "Objeto":      label_names[c],
                        "Cantidad":    cnt,
                        "Confianza":   f"{np.mean(cat_conf[c]):.0%}",
                        "¿Mascota?":   "🐾" if label_names[c] in PET_CLASSES else "–",
                    }
                    for c, cnt in cat_count.items()
                ]
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.bar_chart(df.set_index("Objeto")["Cantidad"])
            else:
                st.caption("Sin detecciones con los parámetros actuales. Reduce el umbral de confianza.")

    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
#  FOOTER + AUTO-REFRESH
# ─────────────────────────────────────────
st.markdown("---")
col_r, col_cap = st.columns([1, 4])
with col_r:
    if st.button("🔄 Actualizar"):
        st.rerun()
with col_cap:
    st.caption("PetBuddy · MQTT + YOLOv5 · Sensor de movimiento + cámara inteligente")

# Auto-refresh cada 3 s para el MQTT (solo si no hay imagen capturada)
if "camera_pet" not in st.session_state or st.session_state.get("camera_pet") is None:
    time.sleep(3)
    st.rerun()
