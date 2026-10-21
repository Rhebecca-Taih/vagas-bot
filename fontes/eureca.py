import html
import re
import time
from datetime import datetime, timedelta

import requests

from fontes.base import Scraper, Vaga

API = "https://candidate-api.eureca.me/programs"
URL_PROGRAMA = "https://app.eureca.me/programas/{id}"
TAMANHO_PAGINA = 50
MAX_PAGINAS = 10
PAUSA_ENTRE_REQUISICOES = 0.5
FUSO_BRASILIA = timedelta(hours=-3)

CONTRATOS_IGNORADOS = {"young-apprentice"}
CONTRATOS_ESTAGIO = {"internship"}

HEADERS = {"User-Agent": "Mozilla/5.0 (vagas-bot)", "Accept": "application/json"}


def _html_para_texto(trecho: str | None) -> str:
    sem_tags = re.sub(r"<[^>]+>", " ", trecho or "")
    return re.sub(r"\s+", " ", html.unescape(sem_tags)).strip()


def _fim_inscricao(programa: dict):
    if not programa.get("endApplying"):
        return None
    fim = datetime.fromisoformat(programa["endApplying"].replace("Z", "+00:00"))
    return (fim + FUSO_BRASILIA).date()


def _local(vagas_do_programa: list[dict]) -> str:
    cidades = sorted({v["cityName"] for v in vagas_do_programa if v.get("cityName")})
    return ", ".join(cidades) if cidades else "Ver locais no programa"


class ScraperEureca(Scraper):
    nome_fonte = "eureca"

    def __init__(self) -> None:
        self.sessao = requests.Session()
        self.sessao.headers.update(HEADERS)

    def _get(self, url: str, params: dict | None = None) -> dict:
        resp = self.sessao.get(url, params=params, timeout=30)
        time.sleep(PAUSA_ENTRE_REQUISICOES)
        resp.raise_for_status()
        return resp.json()

    def _listar_programas(self) -> list[dict]:
        programas = []
        for pagina in range(1, MAX_PAGINAS + 1):
            dados = self._get(API, {"page": pagina, "pageSize": TAMANHO_PAGINA})
            programas.extend(dados.get("items") or [])
            if len(programas) >= dados.get("total", 0) or not dados.get("items"):
                break
        return programas

    def buscar_vagas(self) -> list[Vaga]:
        hoje = datetime.now().date()
        vagas: list[Vaga] = []
        for resumo in self._listar_programas():
            programa = self._get(f"{API}/{resumo['id']}")
            contrato = ((programa.get("workCondition") or {}).get("contractType") or {}).get("key", "")
            fim = _fim_inscricao(programa)
            if contrato in CONTRATOS_IGNORADOS or (fim and fim < hoje):
                continue

            vagas_do_programa = programa.get("jobs") or []
            areas = "\n".join(
                f"{v.get('name', '')}: {_html_para_texto(v.get('description'))}" for v in vagas_do_programa
            )
            vagas.append(
                Vaga(
                    id=f"eureca_{programa['id']}",
                    titulo=(programa.get("name") or "").strip(),
                    empresa=((programa.get("company") or {}).get("name") or resumo.get("companyName") or "").strip(),
                    local=_local(vagas_do_programa),
                    link=URL_PROGRAMA.format(id=programa["id"]),
                    fonte=self.nome_fonte,
                    descricao=f"{_html_para_texto(programa.get('description'))}\n{areas}",
                    fim_inscricao=fim,
                    eh_estagio=True if contrato in CONTRATOS_ESTAGIO else (False if contrato == "trainee" else None),
                    programa=True,
                )
            )
        return vagas


if __name__ == "__main__":
    for v in ScraperEureca().buscar_vagas():
        print(f"{v.id[:20]:20} | {v.empresa[:25]:25} | {v.titulo[:60]:60} | {v.fim_inscricao} | {v.local}")
