import requests

from configuracao import carregar
from fontes.base import NIVEL_ENTRADA, Scraper, Vaga

URL_CONSULTA = "https://firestore.googleapis.com/v1/projects/{projeto}/databases/(default)/documents:runQuery"

CONSULTA_VAGAS_ABERTAS = {
    "structuredQuery": {
        "from": [{"collectionId": "job-postings"}],
        "where": {
            "fieldFilter": {
                "field": {"fieldPath": "status"},
                "op": "EQUAL",
                "value": {"stringValue": "open"},
            }
        },
    }
}

MODALIDADES = (("híbrido", "hibrido"), ("hibrido", "hibrido"), ("remoto", "remoto"), ("presencial", "presencial"))


def _valor(campo: dict | None):
    if not campo:
        return None
    if "arrayValue" in campo:
        return [_valor(v) for v in campo["arrayValue"].get("values", [])]
    return next(iter(campo.values()))


class ScraperSitePrioritario(Scraper):
    nome_fonte = "site_prioritario"

    def buscar_vagas(self) -> list[Vaga]:
        if not (carregar.PRIORIDADE_FIRESTORE_PROJETO and carregar.PRIORIDADE_FIRESTORE_CHAVE):
            return []

        resp = requests.post(
            URL_CONSULTA.format(projeto=carregar.PRIORIDADE_FIRESTORE_PROJETO),
            params={"key": carregar.PRIORIDADE_FIRESTORE_CHAVE},
            json=CONSULTA_VAGAS_ABERTAS,
            timeout=30,
        )
        resp.raise_for_status()

        vagas: list[Vaga] = []
        for item in resp.json():
            if "document" not in item:
                continue
            campos = {k: _valor(v) for k, v in item["document"]["fields"].items()}
            titulo = (campos.get("title") or "").strip()
            if not NIVEL_ENTRADA.search(titulo):
                continue

            local = campos.get("location") or ""
            codigo = campos.get("jobCode") or item["document"]["name"].rsplit("/", 1)[-1]
            vagas.append(
                Vaga(
                    id=f"site_prioritario_{codigo}",
                    titulo=titulo,
                    empresa=carregar.PRIORIDADE_NOME_EMPRESA,
                    local=local,
                    link=campos.get("link") or carregar.PRIORIDADE_URL_VAGAS,
                    fonte=self.nome_fonte,
                    descricao=" | ".join(
                        str(x) for x in [campos.get("category"), campos.get("coe"), *(campos.get("tags") or [])] if x
                    ),
                    modalidade=next((nome for chave, nome in MODALIDADES if chave in local.lower()), ""),
                )
            )
        return vagas


if __name__ == "__main__":
    for v in ScraperSitePrioritario().buscar_vagas():
        print(v)
