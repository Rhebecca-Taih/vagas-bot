import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from configuracao import carregar
from envio import historico, telegram
from fontes.ciee import ScraperCiee
from fontes.gupy import ScraperGupy
from fontes.linkedin import ScraperLinkedin
from fontes.site_prioritario import ScraperSitePrioritario
from regras_das_vagas.estrelas import canal_da_vaga
from regras_das_vagas.filtros import filtrar_e_classificar

MAX_MENSAGENS_INDIVIDUAIS = 10

SCRAPERS = {
    "ciee": ScraperCiee,
    "site_prioritario": ScraperSitePrioritario,
    "gupy": ScraperGupy,
    "linkedin": ScraperLinkedin,
}


def _coletar() -> list:
    vagas = []
    for nome in carregar.fontes_ativas():
        try:
            vagas.extend(SCRAPERS[nome]().buscar_vagas())
        except Exception as exc:
            # nunca imprimir a mensagem > URL/chave em log público
            print(f"[buscar_vagas] erro na fonte '{nome}': {type(exc).__name__}")
    return vagas


def _notificar(vagas: list, canal: str) -> None:
    if canal != "prioridade" and len(vagas) > MAX_MENSAGENS_INDIVIDUAIS:
        telegram.notificar_lote(vagas, canal)
    else:
        for vaga in vagas:
            telegram.notificar_vaga_nova(vaga, canal)


def main(notificar: bool = True) -> None:
    coletadas = _coletar()
    novas = [v for v in filtrar_e_classificar(coletadas) if not historico.ja_notificada(v.id)]

    por_canal: dict[str, list] = {}
    for vaga in novas:
        por_canal.setdefault(canal_da_vaga(vaga), []).append(vaga)

    for canal, vagas in por_canal.items():
        vagas = telegram.ordenar(vagas)
        if notificar:
            _notificar(vagas, canal)
        for vaga in vagas:
            historico.marcar_notificada(vaga, canal)

    resumo = ", ".join(f"{c}={len(v)}" for c, v in por_canal.items()) or "nenhuma"
    print(f"[buscar_vagas] {len(coletadas)} coletadas, {len(novas)} novas ({resumo}).")


if __name__ == "__main__":
    main(notificar="--sem-notificar" not in sys.argv)
