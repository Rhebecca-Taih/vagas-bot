import json
from datetime import date
from pathlib import Path

ARQUIVO_ESTADO = Path(__file__).resolve().parent.parent / "dados" / "historico_vagas.json"


def _carregar() -> dict:
    if not ARQUIVO_ESTADO.exists():
        return {"vagas": {}}
    with open(ARQUIVO_ESTADO, "r", encoding="utf-8") as f:
        return json.load(f)


def _salvar(estado: dict) -> None:
    ARQUIVO_ESTADO.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)


def ja_notificada(vaga_id: str) -> bool:
    return vaga_id in _carregar()["vagas"]


def marcar_notificada(vaga, canal: str) -> None:
    estado = _carregar()
    estado["vagas"][vaga.id] = {
        "titulo": vaga.titulo,
        "empresa": vaga.empresa,
        "local": vaga.local,
        "link": vaga.link,
        "fonte": vaga.fonte,
        "prioritaria": vaga.prioritaria,
        "estrelas": vaga.estrelas,
        "canal": canal,
        "fim_inscricao": vaga.fim_inscricao.isoformat() if vaga.fim_inscricao else None,
        "data": date.today().isoformat(),
    }
    _salvar(estado)


def todas() -> list[dict]:
    return list(_carregar()["vagas"].values())


def vagas_do_dia(dia: str | None = None) -> list[dict]:
    dia = dia or date.today().isoformat()
    return [v for v in todas() if v["data"] == dia]
