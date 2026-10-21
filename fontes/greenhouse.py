import html
import re
import time
from datetime import datetime

import requests

from configuracao import carregar
from fontes.base import NIVEL_ENTRADA, Scraper, Vaga

API = "https://boards-api.greenhouse.io/v1/boards/{empresa}/jobs"
PAUSA_ENTRE_REQUISICOES = 1.0

LOCAIS_BRASIL = re.compile(r"(?i)bra[sz]il|s[ãa]o paulo|rio de janeiro|belo horizonte|curitiba|"
                           r"porto alegre|florian[óo]polis|campinas|recife|\bremot[eo]\b|\bBR\b")
REMOTO = re.compile(r"(?i)\bremot[eo]\b|home office|100% remot")
HIBRIDO = re.compile(r"(?i)h[íi]brid|hybrid")

HEADERS = {"User-Agent": "Mozilla/5.0 (vagas-bot)", "Accept": "application/json"}


def _html_para_texto(trecho: str | None) -> str:
    sem_tags = re.sub(r"<[^>]+>", " ", html.unescape(trecho or ""))
    return re.sub(r"\s+", " ", html.unescape(sem_tags)).strip()


def _modalidade(titulo: str, local: str) -> str:
    texto = f"{titulo} {local}"
    if HIBRIDO.search(texto):
        return "hibrido"
    if REMOTO.search(texto):
        return "remoto"
    return ""


def _fim_inscricao(job: dict):
    if not job.get("application_deadline"):
        return None
    return datetime.fromisoformat(job["application_deadline"].replace("Z", "+00:00")).date()


class ScraperGreenhouse(Scraper):
    nome_fonte = "greenhouse"

    def __init__(self) -> None:
        self.sessao = requests.Session()
        self.sessao.headers.update(HEADERS)

    def _vagas_da_empresa(self, empresa: str) -> list[dict]:
        resp = self.sessao.get(API.format(empresa=empresa), params={"content": "true"}, timeout=30)
        time.sleep(PAUSA_ENTRE_REQUISICOES)
        resp.raise_for_status()
        return resp.json().get("jobs") or []

    def buscar_vagas(self) -> list[Vaga]:
        vagas: list[Vaga] = []
        for empresa in carregar.GREENHOUSE_EMPRESAS:
            try:
                jobs = self._vagas_da_empresa(empresa)
            except requests.RequestException as exc:
                print(f"[greenhouse] erro em uma empresa: {type(exc).__name__}")
                continue
            for job in jobs:
                titulo = (job.get("title") or "").strip()
                local = ((job.get("location") or {}).get("name") or "").strip()
                if not NIVEL_ENTRADA.search(titulo) or not LOCAIS_BRASIL.search(local):
                    continue
                vagas.append(
                    Vaga(
                        id=f"greenhouse_{job['id']}",
                        titulo=titulo,
                        empresa=(job.get("company_name") or empresa).strip(),
                        local=local,
                        link=job.get("absolute_url") or "",
                        fonte=self.nome_fonte,
                        descricao=_html_para_texto(job.get("content")),
                        modalidade=_modalidade(titulo, local),
                        fim_inscricao=_fim_inscricao(job),
                    )
                )
        return vagas


if __name__ == "__main__":
    for v in ScraperGreenhouse().buscar_vagas():
        print(f"{v.id:22} | {v.modalidade:8} | {v.empresa[:20]:20} | {v.titulo[:55]:55} | {v.local}")
