"""Gera uma base FICTÍCIA de ativos de TI em dados/ativos.csv.

Nenhum dado real de empresa é usado: nomes, setores e equipamentos são
sorteados a partir das listas abaixo. A semente fixa faz o arquivo sair
sempre igual, o que facilita testar e comparar resultados.

Uso:  python gerar_dados.py [quantidade]   (padrão: 200 ativos)
"""

import random
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

SEMENTE = 42
HOJE = date(2026, 10, 17)

SETORES = ["Administrativo", "Financeiro", "Comercial", "Logística",
           "Produção", "Qualidade", "RH", "TI", "Diretoria"]

NOMES = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Fábio", "Gabriela",
         "Henrique", "Isabela", "João", "Karina", "Lucas", "Mariana",
         "Nelson", "Olívia", "Paulo", "Renata", "Sérgio", "Tatiana", "Vítor"]
SOBRENOMES = ["Almeida", "Barbosa", "Costa", "Dias", "Ferreira", "Gomes",
              "Lima", "Martins", "Oliveira", "Pereira", "Rocha", "Souza"]

# tipo: (peso no sorteio, [(marca, modelo, faixa de valor em R$)], sistemas)
CATALOGO = {
    "Notebook": (30, [("Dell", "Latitude 3440", (4200, 5800)),
                      ("Lenovo", "ThinkPad E14", (4500, 6200)),
                      ("HP", "ProBook 440 G10", (4000, 5500))],
                 ["Windows 11 Pro", "Windows 10 Pro"]),
    "Desktop": (20, [("Dell", "OptiPlex 3000", (3200, 4500)),
                     ("Lenovo", "ThinkCentre M70s", (3300, 4700))],
                ["Windows 11 Pro", "Windows 10 Pro"]),
    "Monitor": (25, [("LG", "24MP400", (700, 950)),
                     ("Dell", "P2422H", (1100, 1500)),
                     ("Samsung", "LS24C310", (650, 900))], ["—"]),
    "Celular": (15, [("Samsung", "Galaxy A55", (1900, 2500)),
                     ("Motorola", "Moto G84", (1300, 1700))], ["Android"]),
    "Impressora": (5, [("Brother", "DCP-L5652DN", (2800, 3600)),
                       ("HP", "LaserJet M432", (3000, 3900))], ["—"]),
    "Switch": (3, [("Cisco", "CBS250-24T", (2500, 3400)),
                   ("TP-Link", "TL-SG3428", (1400, 1900))], ["—"]),
    "Servidor": (2, [("Dell", "PowerEdge T150", (14000, 19000))],
                 ["Ubuntu Server 24.04", "Windows Server 2022"]),
}

STATUS = ["Em uso"] * 80 + ["Estoque"] * 10 + ["Manutenção"] * 6 + ["Descartado"] * 4


def gerar(qtd: int) -> pd.DataFrame:
    rnd = random.Random(SEMENTE)
    tipos = list(CATALOGO)
    pesos = [CATALOGO[t][0] for t in tipos]
    linhas = []

    for i in range(1, qtd + 1):
        tipo = rnd.choices(tipos, pesos)[0]
        _, modelos, sistemas = CATALOGO[tipo]
        marca, modelo, (vmin, vmax) = rnd.choice(modelos)
        aquisicao = HOJE - timedelta(days=rnd.randint(30, 7 * 365))
        status = rnd.choice(STATUS)
        computador = tipo in ("Notebook", "Desktop", "Servidor")

        # equipamentos de infraestrutura ou parados não têm responsável
        sem_dono = status in ("Estoque", "Descartado") or tipo in ("Switch", "Servidor", "Impressora")
        responsavel = "" if sem_dono else f"{rnd.choice(NOMES)} {rnd.choice(SOBRENOMES)}"

        # a saúde do disco cai com a idade do equipamento
        idade_anos = (HOJE - aquisicao).days / 365
        saude = max(35, min(100, round(100 - idade_anos * rnd.uniform(4, 9)))) if computador else None

        linhas.append({
            "codigo": f"TI-{i:06d}",
            "tipo": tipo,
            "marca": marca,
            "modelo": modelo,
            "setor": "TI" if tipo in ("Switch", "Servidor") else rnd.choice(SETORES),
            "responsavel": responsavel,
            "status": status,
            "sistema": rnd.choice(sistemas),
            "ram_gb": rnd.choice([8, 16, 16, 32]) if computador else None,
            "saude_disco_pct": saude,
            "data_aquisicao": aquisicao.isoformat(),
            "garantia_ate": (aquisicao + timedelta(days=365 * rnd.choice([1, 3]))).isoformat(),
            "valor_rs": round(rnd.uniform(vmin, vmax), 2),
        })

    return pd.DataFrame(linhas)


if __name__ == "__main__":
    qtd = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    destino = Path(__file__).parent / "dados" / "ativos.csv"
    destino.parent.mkdir(exist_ok=True)
    df = gerar(qtd)
    df.to_csv(destino, index=False, encoding="utf-8")
    print(f"{len(df)} ativos fictícios gravados em {destino}")
    print(df["tipo"].value_counts().to_string())
