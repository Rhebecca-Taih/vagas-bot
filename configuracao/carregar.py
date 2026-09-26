import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

PASTA = Path(__file__).resolve().parent
ARQUIVO_CRITERIOS = PASTA / "ajustavel" / "criterios.yaml"
ARQUIVO_FONTES = PASTA / "ajustavel" / "fontes.yaml"

load_dotenv(PASTA / "sensivel" / ".env")


def _yaml(arquivo: Path) -> dict:
    with open(arquivo, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def criterios() -> dict:
    return _yaml(ARQUIVO_CRITERIOS)


def fontes_ativas() -> list[str]:
    return [nome for nome, dados in _yaml(ARQUIVO_FONTES)["fontes"].items() if dados.get("ativo")]


def _texto(nome: str) -> str:
    return os.environ.get(nome, "").strip()


def _lista(nome: str) -> list[str]:
    return [item.strip() for item in _texto(nome).split(",") if item.strip()]


CIDADE_BASE = _texto("CIDADE_BASE")
UF_BASE = _texto("UF_BASE").upper()

AREA_TERMOS = _lista("AREA_TERMOS")
AREA_TERMOS_TITULO = _lista("AREA_TERMOS_TITULO")
AREA_EXCLUIR = _lista("AREA_EXCLUIR")
AREA_EXCLUIR_TITULO = _lista("AREA_EXCLUIR_TITULO")

ESTRELAS_TERMOS_AREA = _lista("ESTRELAS_TERMOS_AREA")
ESTRELAS_TERMOS_PERFIL = _lista("ESTRELAS_TERMOS_PERFIL")

EMPRESAS_PRIORITARIAS = _lista("EMPRESAS_PRIORITARIAS")
EMPRESAS_BLOQUEADAS = _lista("EMPRESAS_BLOQUEADAS")
GRUPOS_VAGAS_EXCLUSIVAS = _lista("GRUPOS_VAGAS_EXCLUSIVAS")

PRIORIDADE_NOME_EMPRESA = _texto("PRIORIDADE_NOME_EMPRESA")
PRIORIDADE_FIRESTORE_PROJETO = _texto("PRIORIDADE_FIRESTORE_PROJETO")
PRIORIDADE_FIRESTORE_CHAVE = _texto("PRIORIDADE_FIRESTORE_CHAVE")
PRIORIDADE_URL_VAGAS = _texto("PRIORIDADE_URL_VAGAS")

TELEGRAM = {
    "estagio": (_texto("TELEGRAM_ESTAGIO_BOT_TOKEN"), _texto("TELEGRAM_ESTAGIO_CHAT_ID")),
    "prioridade": (_texto("TELEGRAM_PRIORIDADE_BOT_TOKEN"), _texto("TELEGRAM_PRIORIDADE_CHAT_ID")),
    "ti": (_texto("TELEGRAM_TI_BOT_TOKEN"), _texto("TELEGRAM_TI_CHAT_ID")),
}
