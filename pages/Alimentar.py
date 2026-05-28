import streamlit as st
import paho.mqtt.client as mqtt
import time

# ─────────────────────────────────────────
#  CONFIG MQTT
# ─────────────────────────────────────────
BROKER         = "broker.hivemq.com"
PORT           = 1883
TOPIC_SERVO    = "petbuddy/sofia/servo"       # publica → ESP32 mueve servo
TOPIC_CONFIRM  = "petbuddy/sofia/confirmacion" # suscribe ← ESP32 confirma

# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="PetBuddy – Alimentar",
    page_icon="🍖",
    layout="wide",
)

# ─────────────────────────────────────────
#  ESTILOS
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
    font-size: 2.8rem;
    font-weight: 800;
    color: #d9622b;
    text-align: center;
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
.paw-divider {
    text-align: center;
    font-size: 1.5rem;
    color: #f3c89a;
    margin: 0.8rem 0;
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
    font-size: 1.15rem;
    font-weight: 600;
    color: #b05a20;
    margin-bottom: 0.6rem;
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
    font-size: 1.1rem;
    padding: 0.6rem 2rem;
    width: 100%;
    transition: opacity 0.2s;
}
div[data-testid="stButton"] button:hover { opacity: 0.85; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  ESTADO DE SESIÓN
# ─────────────────────────────────────────
if "veces_alimentado" not in st.session_state:
    st.session_state.veces_alimentado = 0
if "ultimo_feed"      not in st.session_state:
    st.session_state.ultimo_feed = None
if "confirmado"       not in st.session_state:
    st.session_state.confirmado = False
if "mqtt_ok"          not in st.session_state:
    st.session_state.mqtt_ok = False

# ─────────────────────────────────────────
#  MQTT – cliente con callback de confirmación
# ─────────────────────────────────────────
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    if payload == "ok":
        st.session_state.confirmado = True

@st.cache_resource
def get_mqtt_client():
    client = mqtt.Client()
    client.on_message = on_message
    try:
        client.connect(BROKER, PORT, 60)
        client.subscribe(TOPIC_CONFIRM)
        client.loop_start()
        st.session_state.mqtt_ok = True
        return client
    except Exception:
        return None

mqtt_client = get_mqtt_client()

# ─────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🍖 PetBuddy")
    st.markdown("**Alimentador automático**")
    st.markdown("---")
    st.markdown("**Estado MQTT**")
    if mqtt_client:
        st.success("🟢 Conectado al broker")
    else:
        st.error("🔴 Sin conexión MQTT")
    st.markdown("---")
    st.markdown("**Topic de control**")
    st.caption(f"Publica en: `{TOPIC_SERVO}`")
    st.caption(f"Escucha en: `{TOPIC_CONFIRM}`")
    st.markdown("---")
    st.markdown("**Comando enviado**")
    st.info("🔄 `alimentar` → mueve servo")

# ─────────────────────────────────────────
#  CABECERA
# ─────────────────────────────────────────
st.markdown('<p class="pet-title">🍖 Alimentar mascota</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="pet-subtitle">Página 1: Control del dispensador de comida</p>',
    unsafe_allow_html=True,
)
st.markdown('<div class="paw-divider">🐾 🐾 🐾</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
#  FILA PRINCIPAL
# ─────────────────────────────────────────
col_img, col_control = st.columns([1, 2], gap="large")

with col_img:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.image(
        "https://cdn-icons-png.flaticon.com/512/2785/2785819.png",
        width=180,
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col_control:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Control del dispensador</div>', unsafe_allow_html=True)

    # Botón principal de alimentar
    if st.button("🍖 ¡Alimentar ahora!"):
        if mqtt_client:
            mqtt_client.publish(TOPIC_SERVO, "alimentar")
            st.session_state.veces_alimentado += 1
            st.session_state.ultimo_feed = time.strftime("%H:%M:%S")
            st.session_state.confirmado  = False
            st.success("✅ Comando enviado al dispensador")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("❌ Sin conexión MQTT — no se pudo enviar el comando")

    # Confirmación del ESP32
    if st.session_state.confirmado:
        st.info("🤖 ESP32 confirmó: servo activado correctamente")

    # Último horario
    if st.session_state.ultimo_feed:
        st.caption(f"Última alimentación: {st.session_state.ultimo_feed}")

    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
#  CONTADOR + HISTORIAL
# ─────────────────────────────────────────
st.markdown("---")
col_count, col_info = st.columns(2, gap="medium")

with col_count:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="feed-count">{st.session_state.veces_alimentado}</div>'
        '<div class="feed-label">veces alimentado hoy</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col_info:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">¿Cómo funciona?</div>', unsafe_allow_html=True)
    st.markdown("""
    1. Presiona el botón de alimentar
    2. Streamlit publica `alimentar` por MQTT
    3. El ESP32 en Wokwi recibe el mensaje
    4. El servo gira y dispensa la comida
    5. El ESP32 responde `ok` de confirmación
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────
st.markdown("---")
st.caption("PetBuddy · Alimentador automático · MQTT + Servo + ESP32")
