import re
from dataclasses import dataclass
from datetime import date

# "\sI$": nível I no fim do título (ex.: Analista I)
NIVEL_ENTRADA = re.compile(
    r"\b(est[aá]gio|estagi[aá]ri[oa]|trainee|intern(ship)?|j[uú]nior|jr|entry[- ]level)\b|\sI$",
    re.IGNORECASE,
)


@dataclass
class Vaga:
    id: str
    titulo: str
    empresa: str
    local: str
    link: str
    fonte: str
    descricao: str = ""
    modalidade: str = ""
    fim_inscricao: date | None = None
    eh_estagio: bool | None = None
    prioritaria: bool = False
    estrelas: int = 0


class Scraper:
    nome_fonte: str = ""

    def buscar_vagas(self) -> list[Vaga]:
        raise NotImplementedError
