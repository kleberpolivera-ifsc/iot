import streamlit as st
import paho.mqtt.client as mqtt
import json
import sqlite3
import pandas as pd
import time

# Configurações do Broker MQTT (Devem bater exatamente com o ESP32)
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
TOPICO_TELEMETRIA = "dashboard/iot/telemetria"
TOPICO_COMANDO = "topico_do_kebi" 
DB_NAME = "dados_luz_iot.db"

st.set_page_config(page_title="Dashboard IoT Centralizado", layout="wide")
st.title("🎛️ Portal IoT Centralizado: Sensores e Atuadores")

# 1. Inicializar Banco SQLite com Luminosidade e Movimento
def inicializar_banco():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            luminosidade INTEGER,
            movimento INTEGER
        )
    ''')
    conn.commit()
    conn.close()

inicializar_banco()

# 2. Callback de recebimento (Telemetria ➡️ SQLite)
def quando_receber_mensagem(client, userdata, msg):
    try:
        if msg.topic == TOPICO_TELEMETRIA:
            payload = msg.payload.decode("utf-8")
            dados = json.loads(payload)
            luz = dados.get("luminosidade")
            mov = dados.get("movimento")
            
            if luz is not None and mov is not None:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO leituras (luminosidade, movimento) VALUES (?, ?)", (luz, mov))
                conn.commit()
                conn.close()
    except Exception as e:
        print(f"Erro ao salvar telemetria: {e}")

# 3. Inicializar Conexão MQTT Persistente
@st.cache_resource
def iniciar_cliente_mqtt():
    cliente = mqtt.Client()
    cliente.on_message = quando_receber_mensagem
    cliente.connect(MQTT_BROKER, MQTT_PORT, 60)
    cliente.subscribe(TOPICO_TELEMETRIA)
    cliente.loop_start()
    return cliente

# Ativa o cliente MQTT
mqtt_client = iniciar_cliente_mqtt()

# 4. Painel de Controle do Atuador (Na barra lateral)
st.sidebar.header("🕹️ Controle de Atuadores")

if st.sidebar.button("🟢 Ligar Dispositivo (LED/Relé)", use_container_width=True):
    mqtt_client.publish(TOPICO_COMANDO, "LIGAR")
    st.sidebar.success("Comando 'LIGAR' enviado!")

if st.sidebar.button("🔴 Desligar Dispositivo (LED/Relé)", use_container_width=True):
    mqtt_client.publish(TOPICO_COMANDO, "DESLIGAR")
    st.sidebar.error("Comando 'DESLIGAR' enviado!")

# 5. Renderização da Interface de Monitoramento
espaco_metricas = st.empty()
espaco_grafico = st.empty()

def buscar_dados():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT datetime(timestamp, 'localtime') as hora, luminosidade, movimento FROM leituras ORDER BY id DESC LIMIT 50", conn)
    conn.close()
    return df.iloc[::-1]

df_dados = buscar_dados()

if not df_dados.empty:
    ultimo_registro = df_dados.iloc[-1]
    
    # Formata o status do movimento para exibição amigável
    status_movimento = "Detectado 🚨" if ultimo_registro['movimento'] == 1 else "Normal 🟢"
    
    with espaco_metricas.container():
        c1, c2 = st.columns(2)
        c1.metric("💡 Luminosidade Atual", f"{ultimo_registro['luminosidade']}")
        c2.metric("🚶 Movimento Atual", status_movimento)
        
    with espaco_grafico.container():
        st.subheader("📊 Histórico Gravado no SQLite (Luz e Movimento)")
        st.line_chart(df_dados.set_index("hora")[["luminosidade", "movimento"]])
else:
    st.info("⏳ Aguardando primeiras telemetrias do ESP32...")

# Atualização automática da tela a cada 1 segundo
time.sleep(1)
st.rerun()