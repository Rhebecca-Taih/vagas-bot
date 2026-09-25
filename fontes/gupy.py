import html
import re
import time
from datetime import datetime, timezone

import requests

from configuracao import carregar
from fontes.base import Scraper, Vaga

API = "https://employability-portal.gupy.io/api/v1/jobs"
TAMANHO_PAGINA = 100  # nunca acima de 100 > API recusa
MAX_PAGINAS = 10
PAUSA_ENTRE_REQUISICOES = 0.5

TERMOS = ["estágio", "estagiário", "trainee", "júnior", "junior"]

TIPOS_ACEITOS = {
    "vacancy_type_internship",
    "vacancy_type_trainee",
    "vacancy_type_effective",
    "vacancy_type_talent_pool",
}

MODALIDADES = {"remote": "remoto", "hybrid": "hibrido", "on-site": "presencial"}

HEADERS = {"User-Agent": "Mozilla/5.0 (vagas-bot)", "Accept": "application/json"}


def _html_para_texto(trecho: str | None) -> str:
    sem_tags = re.sub(r"<[^>]+>", " ", trecho or "")
    return re.sub(r"\s+", " ", html.unescape(sem_tags)).strip()


def _recortes() -> list[dict]:
    recortes = [{"workplaceType": "remote"}]
    if carregar.CIDADE_BASE:
        recortes.append({"city": carregar.CIDADE_BASE})
    return recortes


def _fim_inscricao(job: dict) -> datetime | None:
    if not job.get("applicationDeadline"):
        return None
    fim = datetime.fromisoformat(job["applicationDeadline"].replace("Z", "+00:00"))
    return fim if fim.tzinfo else fim.replace(tzinfo=timezone.utc)


class ScraperGupy(Scraper):
    nome_fonte = "gupy"

    def __init__(self) -> None:
        self.sessao = requests.Session()
        self.sessao.headers.update(HEADERS)

    def _consultar(self, termo: str, recorte: dict) -> list[dict]:
        # nunca usar "pagination.total" > valor incorreto
        resultados = []
        for pagina in range(MAX_PAGINAS):
            resp = self.sessao.get(
                API,
                params={"jobName": termo, "limit": TAMANHO_PAGINA,
                        "offset": pagina * TAMANHO_PAGINA, **recorte},
                timeout=30,
            )
            resp.raise_for_status()
            dados = resp.json().get("data") or []
            resultados.extend(dados)
            time.sleep(PAUSA_ENTRE_REQUISICOES)
            if len(dados) < TAMANHO_PAGINA:
                break
        return resultados

    def buscar_vagas(self) -> list[Vaga]:
        brutas: dict[int, dict] = {}
        for termo in TERMOS:
            for recorte in _recortes():
                for job in self._consultar(termo, recorte):
                    brutas[job["id"]] = job

        agora = datetime.now(timezone.utc)
        vagas: list[Vaga] = []
        for job in brutas.values():
            fim = _fim_inscricao(job)
            if job.get("type") not in TIPOS_ACEITOS or (fim and fim < agora):
                continue

            modalidade = MODALIDADES.get(job.get("workplaceType") or "", "")
            local = ", ".join(p for p in (job.get("city"), job.get("state")) if p)
            if not local and modalidade == "remoto":
                local = "Remoto"
            vagas.append(
                Vaga(
                    id=f"gupy_{job['id']}",
                    titulo=(job.get("name") or "").strip(),
                    empresa=(job.get("careerPageName") or "").strip(),
                    local=local,
                    link=job.get("jobUrl") or "",
                    fonte=self.nome_fonte,
                    descricao=_html_para_texto(job.get("description")),
                    modalidade=modalidade,
                    fim_inscricao=fim.date() if fim else None,
                    # nunca False pelo tipo > banco de talentos de estágio tem outro tipo
                    eh_estagio=True if job.get("type") == "vacancy_type_internship" else None,
                )
            )
        return vagas


if __name__ == "__main__":
    for v in ScraperGupy().buscar_vagas():
        print(f"{v.id:16} | {v.modalidade:10} | {v.empresa[:25]:25} | {v.titulo[:60]:60} | {v.local}")
