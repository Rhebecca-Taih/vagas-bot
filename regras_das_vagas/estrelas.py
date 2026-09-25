import re

from configuracao import carregar
from fontes.base import Vaga
from regras_das_vagas.texto import contem_algum

ESTAGIO = re.compile(r"\b(est[aá]gio|estagi[aá]ri[oa]s?|intern(ship)?)\b", re.IGNORECASE)
ESTAGIO_OU_TRAINEE = re.compile(r"\b(est[aá]gio|estagi[aá]ri[oa]|trainee|intern(ship)?)\b", re.IGNORECASE)


def canal_da_vaga(vaga: Vaga) -> str:
    if vaga.prioritaria:
        return "prioridade"
    if vaga.eh_estagio is not None:
        return "estagio" if vaga.eh_estagio else "ti"
    return "estagio" if ESTAGIO.search(vaga.titulo) else "ti"


def classificar(vaga: Vaga, criterios: dict) -> int:
    empresas = criterios.get("classificacao") or {}
    nota = 1

    if contem_algum(vaga.empresa, empresas.get("empresas_top") or []):
        nota += 2
    elif contem_algum(vaga.empresa, empresas.get("empresas_boas") or []):
        nota += 1
    elif contem_algum(vaga.empresa, empresas.get("empresas_intermediarias") or []):
        nota -= 1

    if contem_algum(vaga.titulo, carregar.ESTRELAS_TERMOS_AREA):
        nota += 1
    if contem_algum(vaga.titulo, carregar.ESTRELAS_TERMOS_PERFIL):
        nota += 1
    if ESTAGIO_OU_TRAINEE.search(vaga.titulo):
        nota += 1

    vaga.estrelas = max(1, min(5, nota))
    return vaga.estrelas
