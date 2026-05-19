import streamlit as st
import paho.mqtt.client as mqtt
import time

# ---------- CONFIG MQTT ----------
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "petbuddy/sofia/actividad"

# ---------- ESTADO ----------
if "estado_mascota" not in st.session_state:
    st.session_state.estado_mascota = "Sin actividad"

# ---------- CALLBACK MQTT ----------
def on_message(client, userdata, msg):
    mensaje = msg.payload.decode()

    if mensaje == "movimiento":
        st.session_state.estado_mascota = "Activa 🐶"
    elif mensaje == "quieta":
        st.session_state.estado_mascota = "Dormida 😴"

# ---------- CLIENTE MQTT ----------
client = mqtt.Client()
client.on_message = on_message

try:
    client.connect(BROKER, PORT, 60)
    client.subscribe(TOPIC)
    client.loop_start()
except:
    st.error("No se pudo conectar al broker MQTT")

# ---------- INTERFAZ ----------
st.set_page_config(page_title="PetBuddy - Monitoreo", page_icon="🐾")

st.title("🐾 Monitoreo de mascota")
st.subheader("Página 2: Actividad en tiempo real")

st.write(
    "Esta página monitorea si la mascota está activa o descansando."
)

estado = st.session_state.estado_mascota

# ---------- AVATAR ----------
if "Activa" in estado:
    st.image(
        "https://cdn-icons-png.flaticon.com/512/616/616430.png",
        width=200
    )
    st.success("La mascota está activa y moviéndose")
else:
    st.image(
        "https://cdn-icons-png.flaticon.com/512/2138/2138440.png",
        width=200
    )
    st.info("La mascota está descansando")

# ---------- ESTADO ----------
st.markdown("## Estado actual")
st.write(f"### {estado}")

# ---------- REFRESH ----------
time.sleep(2)
st.rerun()
