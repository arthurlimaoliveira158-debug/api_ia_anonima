import pandas as pd
from sklearn.ensemble import IsolationForest
from prisma import Prisma
from datetime import timedelta


class DetetorAnomalias:
    def __init__(self):
        # Otimização: n_estimators (mais árvores = maior precisão), contamination=0.1 (10% de anomalias esperadas)
        self.modelo = IsolationForest(
            n_estimators=200,
            max_samples='auto',
            contamination=0.1,
            random_state=42
        )

    def _classificar_risco_acao(self, acao: str) -> int:
        """Atribui um peso de severidade baseado no tipo de log."""
        acao_upper = acao.upper()
        if "BLOQUEIO" in acao_upper: return 20
        if "FALHA DE LOGIN" in acao_upper: return 15
        if "AUDITORIA" in acao_upper: return 5  # Consultar logs frequentemente é suspeito
        if "CONSULTA" in acao_upper: return 2
        if "PANICO_USUARIO" in acao_upper: return 100 # Peso altíssimo, evento crítico!
        if "BLOQUEIO" in acao_upper: return 20
        return 1  # Cadastro, Inserção ou Login bem sucedido
            
    async def analisar_logs(self, db: Prisma):
        # Busca mais logs para um treinamento mais robusto
        logs = await db.logauditoria.find_many(order={"dataHora": "desc"}, take=2000)

        if len(logs) < 100:
            return {"mensagem": "Gere mais tráfego com o simulador de ataques para treinar a IA."}

        dados = []
        df_temp = pd.DataFrame([
            {"id": log.id, "data_hora": log.dataHora, "acao": log.acao}
            for log in logs
        ])

        # Converte para datetime do pandas para facilitar cálculos de tempo
        df_temp['data_hora'] = pd.to_datetime(df_temp['data_hora'])
        df_temp = df_temp.sort_values('data_hora').reset_index(drop=True)

        # Extração de Features Avançadas (Janela de Tempo)
        for i, row in df_temp.iterrows():
            hora_atual = row['data_hora']

            # 1. Quantas ações ocorreram no último 1 minuto? (Detecta bots/DDoS)
            janela_1_minuto = df_temp[
                (df_temp['data_hora'] <= hora_atual) &
                (df_temp['data_hora'] >= hora_atual - timedelta(minutes=1))
                ]
            frequencia_acoes = len(janela_1_minuto)

            # 2. Risco da ação atual
            risco = self._classificar_risco_acao(row['acao'])

            # 3. Horário de funcionamento (1 para madrugada/fim de semana, 0 para horário comercial)
            hora_dia = hora_atual.hour
            dia_semana = hora_atual.weekday()
            # Considera fora do expediente apenas acessos na madrugada (ex: 00:00 às 05:00) em qualquer dia
            fora_expediente = 1 if (hora_dia >= 0 and hora_dia < 5) else 0

            dados.append({
                "id": row['id'],
                "frequencia_1_min_anteriores": frequencia_acoes,
                "risco_acao": risco,
                "fora_expediente": fora_expediente,
                "acao_original": row['acao']
            })

        df = pd.DataFrame(dados)

        # Features enviadas para a IA (removendo texto e IDs)
        features = df[['frequencia_1_min_anteriores', 'risco_acao', 'fora_expediente']]

        # Treinamento e Predição
        df['predicao'] = self.modelo.fit_predict(features)

        # Extrair resultados (-1 é anomalia)
        anomalias = df[df['predicao'] == -1]

        detalhes_anomalias = []
        for _, row in anomalias.iterrows():
            motivo = []
            if row['frequencia_1_min_anteriores'] > 10:
                motivo.append(f"Alta frequência ({row['frequencia_1_min_anteriores']} req/min)")
            if row['risco_acao'] >= 15:
                motivo.append("Ação de alto risco de segurança")
            if row['fora_expediente'] == 1:
                motivo.append("Atividade fora do expediente comercial")

            detalhes_anomalias.append({
                "log_id": row['id'],
                "acao_suspeita": row['acao_original'],
                "indicadores": " | ".join(motivo) if motivo else "Padrão de comportamento atípico"
            })

        return {
            "status": "Analise Concluida",
            "logs_processados": len(df),
            "anomalias_detectadas": len(anomalias),
            "nivel_ameaca": "ALTO" if len(anomalias) > (len(df) * 0.05) else "CONTROLADO",
            "relatorio_detalhado": detalhes_anomalias
        }