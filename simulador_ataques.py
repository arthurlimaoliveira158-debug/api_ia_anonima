import requests
import time
import random

BASE_URL = "http://localhost:8000"


def gerar_trafego_normal():
    print("Gerando tráfego normal...")
    user = f"usuario_comum_{random.randint(1, 1000)}"
    senha = "senha_segura"

    # 1. Cadastro normal
    requests.post(f"{BASE_URL}/registrar", json={"username": user, "password": senha})

    # 2. Login normal
    resp = requests.post(f"{BASE_URL}/login", data={"username": user, "password": senha})
    if resp.status_code == 200:
        token = resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Uso normal (consultas e inserções espaçadas)
        for _ in range(3):
            requests.post(f"{BASE_URL}/dados", json={"informacao": "Dado normal"}, headers=headers)
            time.sleep(1)  # Simula tempo humano
            requests.get(f"{BASE_URL}/dados", headers=headers)


def ataque_brute_force():
    print("Simulando ataque de Força Bruta (Brute Force)...")
    alvo = "admin_master"
    # Tenta várias senhas rapidamente até gerar o bloqueio de 15 minutos
    for i in range(5):
        requests.post(f"{BASE_URL}/login", data={"username": alvo, "password": f"senha_errada_{i}"})
        # Não há sleep, ação de robô


def ataque_ddos_camada_aplicacao():
    print("Simulando Inundação de Requisições (Comportamento de Bot)...")
    user = "usuario_bot"
    senha = "bot_password"
    requests.post(f"{BASE_URL}/registrar", json={"username": user, "password": senha})

    resp = requests.post(f"{BASE_URL}/login", data={"username": user, "password": senha})
    if resp.status_code == 200:
        token = resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # Faz 50 requisições em 1 segundo (anomalia de frequência)
        for _ in range(50):
            requests.get(f"{BASE_URL}/logs", headers=headers)


if __name__ == "__main__":
    gerar_trafego_normal()
    gerar_trafego_normal()
    ataque_brute_force()
    ataque_ddos_camada_aplicacao()
    print("Testes finalizados. Verifique o endpoint da IA!")