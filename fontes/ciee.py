import html
import json
import re
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from fontes.base import Scraper, Vaga

API = "https://api-solucoes-especiais.ciee.org.br/api/editais"
URL_VAGA = "https://solucoes.ciee.org.br/vitrine/{id}/detalhe"

STATUS_INTERESSANTES = {"ABERTO", "EM_BREVE"}

TAMANHO_PAGINA = 100
MAX_PAGINAS = 30
PAUSA_ENTRE_REQUISICOES = 0.5

ARQUIVO_CACHE = Path(__file__).resolve().parent.parent / "dados" / "cache_ciee.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (vagas-bot)", "Accept": "application/json"}


def _periodo_inscricao(edital: dict) -> tuple[datetime | None, datetime | None]:
    fases = [c for c in edital.get("cronogramas") or [] if c.get("tipoFase") == "INSCRICAO"]
    inicios = [datetime.fromisoformat(c["dataInicio"]) for c in fases if c.get("dataInicio")]
    fins = [datetime.fromisoformat(c["dataFim"]) for c in fases if c.get("dataFim")]
    return (min(inicios) if inicios else None, max(fins) if fins else None)


def _inscricao_aberta_ou_futura(edital: dict, agora: datetime) -> bool:
    # nunca confiar só no status > segue ABERTO após o prazo
    if edital.get("status") not in STATUS_INTERESSANTES:
        return False
    _, fim = _periodo_inscricao(edital)
    return fim is None or fim >= agora


def _html_para_texto(trecho: str | None) -> str:
    sem_tags = re.sub(r"<[^>]+>", " ", trecho or "")
    return re.sub(r"\s+", " ", html.unescape(sem_tags)).strip()


def _carregar_cache() -> dict:
    if not ARQUIVO_CACHE.exists():
        return {}
    with open(ARQUIVO_CACHE, "r", encoding="utf-8") as f:
        return json.load(f)


def _salvar_cache(cache: dict) -> None:
    ARQUIVO_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


class ScraperCiee(Scraper):
    nome_fonte = "ciee"

    def __init__(self) -> None:
        self.sessao = requests.Session()
        self.sessao.headers.update(HEADERS)

    def _listar_editais(self) -> list[dict]:
        # nunca parar pelo "last" > API encerra cedo e repete editais
        editais: dict[int, dict] = {}
        for pagina in range(MAX_PAGINAS):
            resp = self.sessao.post(
                f"{API}/vitrine",
                params={"page": pagina, "size": TAMANHO_PAGINA},
                json={},
                timeout=30,
            )
            resp.raise_for_status()
            conteudo = resp.json().get("content") or []
            if not conteudo:
                break
            for edital in conteudo:
                editais[edital["id"]] = edital
            time.sleep(PAUSA_ENTRE_REQUISICOES)
        return list(editais.values())

    def _detalhe(self, edital_id: int, cache: dict) -> dict:
        chave = str(edital_id)
        if chave in cache:
            return cache[chave]

        time.sleep(PAUSA_ENTRE_REQUISICOES)
        resp = self.sessao.get(f"{API}/{edital_id}", timeout=30)
        resp.raise_for_status()
        detalhe = resp.json() if resp.content else {}

        partes = [
            _html_para_texto(detalhe.get("sobreVaga")),
            _html_para_texto((detalhe.get("requisitos") or {}).get("descricaoRequisito")),
        ]
        valores = sorted({r["valor"] for r in detalhe.get("remuneracao") or [] if r.get("valor")})
        if valores:
            partes.append("Bolsa: " + " / ".join(f"R$ {v:.2f}" for v in valores))

        # nunca usar cidades da listagem > lista incompleta
        cidades = dict.fromkeys(
            f"{local['cidade'].title()}/{local['uf']}" if local.get("uf") else local["cidade"].title()
            for local in detalhe.get("locaisEstagio") or []
            if local.get("cidade")
        )

        cache[chave] = {"descricao": "\n".join(p for p in partes if p), "local": ", ".join(cidades)}
        return cache[chave]

    def buscar_vagas(self) -> list[Vaga]:
        agora = datetime.now(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)
        editais = [e for e in self._listar_editais() if _inscricao_aberta_ou_futura(e, agora)]

        cache = _carregar_cache()
        vagas: list[Vaga] = []
        try:
            for edital in editais:
                detalhe = self._detalhe(edital["id"], cache)
                titulo = (edital.get("identificacao") or "").strip()
                inicio, fim = _periodo_inscricao(edital)
                if edital["status"] == "EM_BREVE" or (inicio and inicio > agora):
                    titulo += " (inscrições em breve)"
                vagas.append(
                    Vaga(
                        id=f"ciee_edital_{edital['id']}",
                        titulo=titulo,
                        empresa=((edital.get("orgao") or {}).get("nome") or "").strip(),
                        local=detalhe["local"],
                        link=URL_VAGA.format(id=edital["id"]),
                        fonte=self.nome_fonte,
                        descricao=detalhe["descricao"],
                        fim_inscricao=fim.date() if fim else None,
                        eh_estagio=True,
                    )
                )
        finally:
            ativos = {str(e["id"]) for e in editais}
            _salvar_cache({k: v for k, v in cache.items() if k in ativos})
        return vagas


if __name__ == "__main__":
    for v in ScraperCiee().buscar_vagas():
        print(f"{v.id:20} | {v.empresa[:30]:30} | {v.titulo[:60]:60} | {v.local}")
