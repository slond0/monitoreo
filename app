import streamlit as st

# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="PetBuddy",
    page_icon="🐾",
    layout="centered",
)

# ─────────────────────────────────────────
#  ESTILOS  (misma paleta que Monitoreo.py)
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

.hero-title {
    font-family: 'Baloo 2', cursive;
    font-size: 3.8rem;
    font-weight: 800;
    color: #d9622b;
    text-align: center;
    line-height: 1.05;
    margin-bottom: 0;
}
.hero-sub {
    font-family: 'Nunito', sans-serif;
    font-size: 1.15rem;
    color: #b07040;
    text-align: center;
    margin-top: 0.3rem;
    margin-bottom: 2rem;
}
.paw-divider {
    text-align: center;
    font-size: 1.4rem;
    color: #f3c89a;
    letter-spacing: 10px;
    margin: 0.5rem 0 1.8rem 0;
}
.card {
    background: rgba(255,255,255,0.78);
    border-radius: 20px;
    padding: 1.4rem 1.6rem;
    box-shadow: 0 4px 18px rgba(210,120,50,0.10);
    border: 1.5px solid #f3c89a;
    margin-bottom: 1rem;
}
.card-icon  { font-size: 2.2rem; margin-bottom: 0.3rem; }
.card-title {
    font-family: 'Baloo 2', cursive;
    font-size: 1.15rem;
    font-weight: 700;
    color: #b05a20;
    margin-bottom: 0.2rem;
}
.card-desc  { font-size: 0.95rem; color: #7a5030; }
.status-row {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
    margin: 1.5rem 0;
}
.status-pill {
    background: rgba(255,255,255,0.85);
    border: 1.5px solid #f3c89a;
    border-radius: 50px;
    padding: 0.35rem 1.1rem;
    font-size: 0.9rem;
    color: #b05a20;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  HERO
# ─────────────────────────────────────────
st.markdown('<p class="hero-title">🐾 PetBuddy</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">Monitoreo inteligente de tu mascota con IoT + IA</p>',
    unsafe_allow_html=True,
)
st.markdown('<div class="paw-divider">🐾 🐾 🐾</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
#  PILLS DE TECNOLOGÍAS
# ─────────────────────────────────────────
st.markdown("""
<div class="status-row">
  <span class="status-pill">ESP32 + Wokwi</span>
  <span class="status-pill">MQTT HiveMQ</span>
  <span class="status-pill">YOLOv5</span>
  <span class="status-pill">Streamlit</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  TARJETAS DE PÁGINAS
# ─────────────────────────────────────────
col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown("""
    <div class="card">
      <div class="card-icon">🍖</div>
      <div class="card-title">Alimentar</div>
      <div class="card-desc">
        Controla el servo del dispensador de comida desde la app.
        El ESP32 recibe la señal por MQTT y activa el motor.
      </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
      <div class="card-icon">📡</div>
      <div class="card-title">Monitoreo</div>
      <div class="card-desc">
        Sensor PIR detecta si tu mascota está activa o dormida.
        La cámara con YOLOv5 confirma su presencia en tiempo real.
      </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────
#  CÓMO FUNCIONA
# ─────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div class="card">
  <div class="card-title">¿Cómo funciona el sistema?</div>
  <div class="card-desc">
    <b>1.</b> El ESP32 en Wokwi lee el sensor PIR cada 3 segundos.<br>
    <b>2.</b> Publica el estado (<em>movimiento / quieta</em>) por MQTT al broker HiveMQ.<br>
    <b>3.</b> Streamlit escucha el broker y actualiza el avatar de la mascota.<br>
    <b>4.</b> La cámara con YOLOv5 detecta si el perro, gato o ave está en escena.<br>
    <b>5.</b> Si la cámara confirma la mascota, envía una alerta de vuelta al ESP32.<br>
    <b>6.</b> El ESP32 parpadea los LEDs como señal física de confirmación.
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────
st.markdown("---")
st.caption("PetBuddy · ESP32 + MQTT + YOLOv5 + Streamlit · Proyecto IoT")
