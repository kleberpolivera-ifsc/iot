from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Banco de dados simulado na memória do servidor para guardar o histórico
historico_temperaturas = []

# Limite para acionamento do cooler
LIMITE_TEMPERATURA = 30.0

@app.route('/api/temperatura', methods=['POST'])
def receber_temperatura():
    # 1. Valida se a requisição contém um JSON
    if not request.is_json:
        return jsonify({"status": "erro", "mensagem": "O corpo da requisição precisa ser JSON"}), 400

    dados = request.get_json()

    # 2. Valida se o campo obrigatório 'temperatura' existe no JSON
    if 'temperatura' not in dados:
        return jsonify({"status": "erro", "mensagem": "Campo 'temperatura' não encontrado"}), 400

    try:
        # Converte e extrai o valor recebido do ESP32
        temperatura_recebida = float(dados['temperatura'])
        timestamp_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 3. Guarda os dados no nosso "banco" temporário
        leitura = {
            "timestamp": timestamp_atual,
            "temperatura": temperatura_recebida
        }
        historico_temperaturas.append(leitura)

        # Print visual bonito no terminal do servidor
        print(f"\n[LOG {timestamp_atual}]")
        print(f" -> ESP32 enviou: {temperatura_recebida}°C")
        print(f" -> Total de leituras na memória: {len(historico_temperaturas)}")

        # 4. Lógica de decisão (Regra de Negócio)
        comando = "DESLIGAR_COOLER"
        if temperatura_recebida > LIMITE_TEMPERATURA:
            comando = "LIGAR_COOLER"
            print(" -> [ALERTA] Temperatura alta! Enviando comando para LIGAR o cooler.")
        else:
            print(" -> [INFO] Temperatura normal. Mantendo cooler desligado.")

        # 5. Resposta estruturada enviada de volta para o ESP32
        resposta = {
            "status": "sucesso",
            "mensagem": "Dados processados com sucesso.",
            "comando": comando,
            "temperatura_limite": LIMITE_TEMPERATURA
        }
        return jsonify(resposta), 200

    except (ValueError, TypeError):
        return jsonify({"status": "erro", "mensagem": "O valor da temperatura deve ser um número válido"}), 400

# Rota extra: Permite que você acesse pelo navegador para ver o histórico de dados
@app.route('/api/historico', methods=['GET'])
def obter_historico():
    return jsonify({
        "total_registros": len(historico_temperaturas),
        "historico": historico_temperaturas
    }), 200

if __name__ == '__main__':
    # host='0.0.0.0' expõe o servidor para a rede local (essencial para o ESP32 se conectar)
    # port=5000 define a porta padrão do Flask
    app.run(host='0.0.0.0', port=5000, debug=True)