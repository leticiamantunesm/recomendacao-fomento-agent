"""Gabarito de negócios + metadados dos 10 projetos em docs/TCC/exemplos_projetos."""

from __future__ import annotations

from pathlib import Path

EXEMPLOS_DIR = (
    Path(__file__).resolve().parents[2] / "docs" / "TCC" / "exemplos_projetos"
)

# Mapeamento ID → arquivo PDF (confirmado pela varredura 2026-11-10)
PROJECT_FILES: dict[str, str] = {
    "01": "AgroBioTech_Ltda.pdf",  # SojaResiliente AI
    "02": "VidaSense_Tecnologias_Médicas_SA.pdf",  # CardioPatch IoT
    "03": "Pão_Quente_Comércio_de_Alimentos_Ltda.pdf",  # Padaria Digital 4.0
    "04": "NeuroGen_Biotec.pdf",  # NeuroGen — rubricas vedadas
    "05": "EcoPlast_Ind_Polimeros.pdf",  # EcoPlast PR — UF
    "06": "agrotitan_sa.pdf",  # AgroTitan — porte
    "07": "Produtora_Olhar_Cultural_Ltda.pdf",  # CineRaízes — cultural
    "08": "projeto_08_Carlos_Eduardo_Silva_Pessoa_Física.pdf",  # QuantumSec — PF
    "09": "projeto_09_Ventos_do_Sul_Energia_SA.pdf",  # H2V Sul
    "10": "projeto_10_RotaCerta_Softwares_Ltda.pdf",  # SmartLogística
}

# Expectativa de negócio por ID
GABARITO: dict[str, dict] = {
    "01": {
        "alias": "SojaResiliente AI",
        "class": "PERFEITO",
        "expect": "pass_ideal",
        "ideal_instruments": ["subvencao", "parceria"],
        "ideal_keywords": ["pipe", "centelha", "fapesp"],
        "must_have_tech_risk": True,
        "must_block_reasons": [],
        "notes": "ME/SP/TRL4→6 — PIPE/Centelha",
    },
    "02": {
        "alias": "CardioPatch IoT",
        "class": "PERFEITO",
        "expect": "pass_ideal",
        "ideal_instruments": ["subvencao"],
        "ideal_keywords": ["tecnova", "finep", "subvenção", "subvencao"],
        "must_have_tech_risk": True,
        "must_block_reasons": [],
        "notes": "EPP/RS/TRL7→9 — Tecnova/FINEP",
    },
    "03": {
        "alias": "Padaria Digital 4.0",
        "class": "IMPERFEITO",
        "expect": "block_no_tech_risk",
        "ideal_instruments": [],
        "ideal_keywords": ["sebraetec", "finame", "crédito", "credito"],
        "must_have_tech_risk": False,
        "must_block_reasons": ["risco tecnológico", "modernização", "p&d"],
        "notes": "Compra fornos/ERP/reforma TRL9 — bloquear subvenção",
    },
    "04": {
        "alias": "NeuroGen Terapias",
        "class": "IMPERFEITO",
        "expect": "alert_forbidden_budget",
        "ideal_instruments": [],
        "ideal_keywords": [],
        "must_have_tech_risk": True,  # há P&D real, mas rubricas ruins
        "must_block_reasons": ["imóvel", "terreno", "obra", "veículo", "veiculo"],
        "notes": "Rubricas imóvel/obra/veículo vedadas",
    },
    "05": {
        "alias": "EcoPlast Paraná",
        "class": "IMPERFEITO",
        "expect": "block_region",
        "ideal_instruments": [],
        "ideal_keywords": [],
        "must_have_tech_risk": True,
        "must_block_reasons": ["região", "regiao", "sp", "uf"],
        "notes": "Empresa PR vs edital restrito SP (FAPESP)",
    },
    "06": {
        "alias": "AgroTitan / DroneAgro",
        "class": "IMPERFEITO",
        "expect": "block_size",
        "ideal_instruments": [],
        "ideal_keywords": [],
        "must_have_tech_risk": True,
        "must_block_reasons": ["porte", "mpe", "centelha", "faturamento"],
        "notes": "Grande Empresa R$450M vs Centelha/MPE",
    },
    "07": {
        "alias": "CineRaízes da Serra",
        "class": "PERFEITO_CULTURAL",
        "expect": "pass_cultural",
        "ideal_instruments": [],  # não é subvenção P&D
        "ideal_keywords": ["proac", "rouanet", "cultura", "audiovisual"],
        "must_have_tech_risk": False,
        "must_block_reasons": ["risco tecnológico", "modernização", "p&d", "cultura"],
        "notes": "Audiovisual/cultura — ProAC/Rouanet, não FINEP P&D",
    },
    "08": {
        "alias": "QuantumSec Brasil",
        "class": "IMPERFEITO",
        "expect": "block_pf_trl",
        "ideal_instruments": [],
        "ideal_keywords": [],
        "must_have_tech_risk": True,
        "must_block_reasons": ["pessoa física", "pj", "porte", "cnpj", "trl"],
        "notes": "PF pedindo linha PJ / TRL 1–2 inadequado a crédito bancário",
    },
    "09": {
        "alias": "H2V Sul Energia",
        "class": "PERFEITO",
        "expect": "pass_ideal",
        "ideal_instruments": ["parceria", "subvencao"],
        "ideal_keywords": ["embrapii", "finep", "hidrogênio", "transição"],
        "must_have_tech_risk": True,
        "must_block_reasons": [],
        "notes": "Empresa+ICT Embrapii / FINEP transição energética",
    },
    "10": {
        "alias": "SmartLogística ERP",
        "class": "IMPERFEITO",
        "expect": "alert_budget_math_and_ads",
        "ideal_instruments": [],
        "ideal_keywords": [],
        "must_have_tech_risk": True,
        "must_block_reasons": ["marketing", "ads", "inconsist", "orçamento", "orcamento"],
        "notes": "Soma rubricas 750k ≠ 500k + Google Ads vedado",
    },
}
