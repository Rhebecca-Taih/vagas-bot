import html
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import NamedTuple

import requests

from configuracao import carregar
from fontes.base import NIVEL_ENTRADA, Scraper, Vaga

API = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
GEO_BRASIL = "106057199"
ULTIMA_SEMANA = "r604800"
REMOTO_BRASIL = {"geoId": GEO_BRASIL, "f_WT": "2"}

INTERVALO_MINIMO = timedelta(hours=3)  # nunca reduzir > risco de bloqueio do IP
ARQUIVO_ULTIMA_EXECUCAO = Path(__file__).resolve().parent.parent / "dados" / "linkedin_ultima_busca.txt"

PAUSA_ENTRE_REQUISICOES = 2.0
POR_PAGINA = 10

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/128.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


class Consulta(NamedTuple):
    palavras: str
    filtros: dict
    paginas: int
    remota: bool


def _consultas() -> list[Consulta]:
    # nunca cidade antes das remotas > primeira ocorrência prevalece
    consultas = [
        Consulta("estágio desenvolvedor", REMOTO_BRASIL, 3, True),
        Consulta("estágio TI", REMOTO_BRASIL, 2, True),
        Consulta("estágio dados", REMOTO_BRASIL, 1, True),
        Consulta("trainee desenvolvedor", REMOTO_BRASIL, 1, True),
        Consulta("desenvolvedor júnior", REMOTO_BRASIL, 2, True),
    ]
    if carregar.CIDADE_BASE:
        na_cidade = {"location": f"{carregar.CIDADE_BASE}, Brasil", "distance": "10"}
        consultas += [Consulta("estágio", na_cidade, 3, False), Consulta("júnior", na_cidade, 1, False)]
    return consultas


def _texto(card: str, classe: str) -> str:
    m = re.search(rf'class="[^"]*{classe}[^"]*"[^>]*>(.*?)</', card, re.S)
    if not m:
        return ""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))).strip()


def _pode_executar_agora() -> bool:
    if not ARQUIVO_ULTIMA_EXECUCAO.exists():
        return True
    try:
        ultima = datetime.fromisoformat(ARQUIVO_ULTIMA_EXECUCAO.read_text().strip())
    except ValueError:
        return True
    return datetime.now() - ultima >= INTERVALO_MINIMO


def _registrar_execucao() -> None:
    ARQUIVO_ULTIMA_EXECUCAO.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO_ULTIMA_EXECUCAO.write_text(datetime.now().isoformat(timespec="seconds"))


def _modalidade(titulo: str, remota: bool, local: str) -> str:
    # nunca confiar só no filtro "remoto" > marcado pela empresa
    titulo = titulo.lower()
    if "presencial" in titulo or "on-site" in titulo:
        return "presencial"
    if re.search(r"h[ií]brid|hybrid", titulo):
        return "hibrido"
    if not remota:
        return ""
    cidade = re.split(r",| e Região", local)[0].strip().lower()
    return "" if len(cidade) > 2 and cidade in titulo else "remoto"


class ScraperLinkedin(Scraper):
    nome_fonte = "linkedin"

    def buscar_vagas(self, ignorar_intervalo: bool = False) -> list[Vaga]:
        if not ignorar_intervalo and not _pode_executar_agora():
            print(f"[linkedin] ignorado: última busca há menos de {INTERVALO_MINIMO}.")
            return []
        _registrar_execucao()

        sessao = requests.Session()
        sessao.headers.update(HEADERS)
        vagas: dict[str, Vaga] = {}

        for consulta in _consultas():
            for pagina in range(consulta.paginas):
                resp = sessao.get(
                    API,
                    params={"keywords": consulta.palavras, "f_TPR": ULTIMA_SEMANA,
                            "start": pagina * POR_PAGINA, **consulta.filtros},
                    timeout=30,
                )
                time.sleep(PAUSA_ENTRE_REQUISICOES)
                if resp.status_code == 429:
                    print("[linkedin] limite de requisições atingido; busca interrompida.")
                    return list(vagas.values())
                resp.raise_for_status()

                cards = resp.text.split("<li>")[1:]
                for card in cards:
                    m = re.search(r'href="(https://[a-z]+\.linkedin\.com/jobs/view/[^"?]*?-(\d+))[?"]', card)
                    titulo = _texto(card, "base-search-card__title")
                    if not m or not titulo or not NIVEL_ENTRADA.search(titulo):
                        continue
                    vaga_id = f"linkedin_{m.group(2)}"
                    if vaga_id in vagas:
                        continue

                    local = _texto(card, "job-search-card__location")
                    modalidade = _modalidade(titulo, consulta.remota, local)
                    if modalidade == "remoto" and local:
                        local = f"Remoto · anúncio de {re.split(r' e Região', local)[0]}"

                    vagas[vaga_id] = Vaga(
                        id=vaga_id,
                        titulo=titulo,
                        empresa=_texto(card, "base-search-card__subtitle"),
                        local=local,
                        link=m.group(1),
                        fonte=self.nome_fonte,
                        modalidade=modalidade,
                    )
                if len(cards) < POR_PAGINA:
                    break
        return list(vagas.values())


if __name__ == "__main__":
    for v in ScraperLinkedin().buscar_vagas(ignorar_intervalo=True):
        print(f"{v.id:22} | {v.modalidade:7} | {v.empresa[:25]:25} | {v.titulo[:60]:60} | {v.local}")
