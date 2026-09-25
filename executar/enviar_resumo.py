import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from envio import historico, telegram

DIAS_LEMBRETE = 3
ESTRELAS_MINIMAS_LEMBRETE = 3

TITULOS = {
    "estagio": "Resumo estágios",
    "prioridade": "Resumo prioridade",
    "ti": "Resumo vagas TI (não-estágio)",
}


def _fim(v: dict) -> date | None:
    return date.fromisoformat(v["fim_inscricao"]) if v.get("fim_inscricao") else None


def _linha(v: dict, hoje: date) -> str:
    prazo = telegram.prazo_texto(_fim(v), hoje)
    return (f"{telegram.estrelas_texto(v.get('estrelas', 0))} <b>{v['titulo']}</b>".strip()
            + f"\n{v['empresa']} — {v['local']}"
            + (f"\n{prazo}" if prazo else "")
            + f"\n{v['link']}")


def _ordenar(vagas: list[dict]) -> list[dict]:
    return sorted(vagas, key=lambda v: (-v.get("estrelas", 0), _fim(v) or date.max))


def _montar_blocos(titulo: str, do_dia: list[dict], encerrando: list[dict], hoje: date) -> list[str]:
    blocos = [f"<b>{titulo} — {hoje:%d/%m}</b>"]

    if encerrando:
        blocos.append(f"━━━━━━ ⏰ Encerrando nos próximos {DIAS_LEMBRETE} dias ━━━━━━")
        blocos += [_linha(v, hoje) for v in sorted(encerrando, key=_fim)]

    if not do_dia:
        blocos.append("Nenhuma vaga nova hoje.")
        return blocos

    blocos.append(f"<b>{len(do_dia)} vaga(s) nova(s) hoje</b>")
    grupo_atual = None
    for v in _ordenar(do_dia):
        if v.get("estrelas", 0) != grupo_atual:
            grupo_atual = v.get("estrelas", 0)
            blocos.append(f"━━━━━━ {telegram.estrelas_texto(grupo_atual) or 'sem nota'} ━━━━━━")
        blocos.append(_linha(v, hoje))
    return blocos


def main() -> None:
    hoje = date.today()
    do_dia = historico.vagas_do_dia()
    encerrando = [
        v for v in historico.todas()
        if v["data"] != hoje.isoformat()
        and _fim(v) and hoje <= _fim(v) <= hoje + timedelta(days=DIAS_LEMBRETE)
        and (v.get("prioritaria") or v.get("estrelas", 0) >= ESTRELAS_MINIMAS_LEMBRETE)
    ]

    grupos: dict[str, tuple[list, list]] = {
        c: ([], []) for c in TITULOS if telegram.canal_configurado(c)
    }
    for v in do_dia:
        grupos[telegram.canal_efetivo(v["canal"])][0].append(v)
    for v in encerrando:
        grupos[telegram.canal_efetivo(v["canal"])][1].append(v)

    for canal, (dia, fim) in grupos.items():
        telegram.enviar_em_partes(_montar_blocos(TITULOS[canal], dia, fim, hoje), canal)
    print(f"[enviar_resumo] enviado ({len(do_dia)} do dia, {len(encerrando)} encerrando).")


if __name__ == "__main__":
    main()
