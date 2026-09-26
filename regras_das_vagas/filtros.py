import re
from datetime import date

from configuracao import carregar
from fontes.base import Vaga
from regras_das_vagas.estrelas import classificar
from regras_das_vagas.texto import contem_algum, termos_distintos

ESTADOS = {
    "AC": "acre", "AL": "alagoas", "AP": "amapá", "AM": "amazonas", "BA": "bahia",
    "CE": "ceará", "DF": "distrito federal", "ES": "espírito santo", "GO": "goiás",
    "MA": "maranhão", "MT": "mato grosso", "MS": "mato grosso do sul", "MG": "minas gerais",
    "PA": "pará", "PB": "paraíba", "PR": "paraná", "PE": "pernambuco", "PI": "piauí",
    "RJ": "rio de janeiro", "RN": "rio grande do norte", "RS": "rio grande do sul",
    "RO": "rondônia", "RR": "roraima", "SC": "santa catarina", "SP": "são paulo",
    "SE": "sergipe", "TO": "tocantins",
}

_LUGAR = r"(?P<lugar>[A-ZÀ-Ú][^.;:,!?\n()|]{2,60})"
# residir/morar em X, região metropolitana de X, exclusiva X
EXIGENCIAS_DE_LOCAL = [
    re.compile(r"(?i:\b(?:resid(?:ir|ente|entes|a)|morar|moradores?|reside[mn]?)\s+"
               r"(?:em|na|no|nas|nos|na região de|próximo a|proximo a|perto de)\s+)" + _LUGAR),
    re.compile(r"(?i:\bregião\s+metropolitana\s+(?:de|do|da)\s+)" + _LUGAR),
    re.compile(r"(?i:\bexclusiv[ao]s?\s+(?:para\s+)?(?:residentes|moradores)\s+(?:de|em|da|do)\s+)" + _LUGAR),
    re.compile(r"(?i:\bexclusiv[ao]\s+)"
               r"(?P<lugar>(?i:(?!p/|pcd|pessoas|mulheres|negr|pret|afirmativ))[A-ZÀ-Ú][^.;:,!?\n()|-]{2,40})"),
]
CIDADE_UF_NO_TITULO = re.compile(r"(?P<lugar>[A-ZÀ-Ú][A-Za-zÀ-ú ]{2,40})\s*/\s*(?P<uf>[A-Z]{2})\b")
LUGARES_NACIONAIS = ("brasil", "território nacional", "todo o país")

PUBLICO_EXCLUSIVO = re.compile(
    r"(?i:\b(?:afirmativ|exclusiv)\w*\s+(?:para|a|à|às|aos|destinad\w*\s+(?:a|à|às|aos|para))\s+)"
    r"(?P<publico>[^.;:!?\n|]{2,80})"
)


# ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆
# FILTRO POR ÁREA
# ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆

def passa_na_area(vaga: Vaga, criterios: dict) -> bool:
    incluir = carregar.AREA_TERMOS
    incluir_titulo = carregar.AREA_TERMOS_TITULO
    minimo_descricao = criterios.get("minimo_termos_na_descricao", 1)
    if (incluir or incluir_titulo) and not (
        contem_algum(vaga.titulo, incluir + incluir_titulo)
        or len(termos_distintos(vaga.descricao, incluir)) >= minimo_descricao
    ):
        return False
    return not contem_algum(f"{vaga.titulo} {vaga.descricao}", carregar.AREA_EXCLUIR)


def exclusiva_para_outro_grupo(vaga: Vaga) -> bool:
    texto = f"{vaga.titulo}\n{vaga.descricao}"
    return any(contem_algum(m.group("publico"), carregar.GRUPOS_VAGAS_EXCLUSIVAS)
               for m in PUBLICO_EXCLUSIVO.finditer(texto))


def barrada(vaga: Vaga) -> bool:
    return (contem_algum(vaga.empresa, carregar.EMPRESAS_BLOQUEADAS)
            or contem_algum(vaga.titulo, carregar.AREA_EXCLUIR_TITULO)
            or exclusiva_para_outro_grupo(vaga))


# ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆
# FILTRO POR LOCAL E MODALIDADE
# ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆

def _locais_exigidos(vaga: Vaga) -> list[str]:
    texto = f"{vaga.titulo}\n{vaga.descricao}"
    lugares = [m.group("lugar") for padrao in EXIGENCIAS_DE_LOCAL for m in padrao.finditer(texto)]
    lugares += [f"{m.group('lugar')}/{m.group('uf')}" for m in CIDADE_UF_NO_TITULO.finditer(vaga.titulo)
                if m.group("uf") in ESTADOS]
    return [lugar for lugar in lugares if not any(n in lugar.lower() for n in LUGARES_NACIONAIS)]


def _local_aceito(lugar: str) -> bool:
    lugar = lugar.lower()
    if carregar.CIDADE_BASE and carregar.CIDADE_BASE.lower() in lugar:
        return True
    if carregar.UF_BASE:
        # nunca só o nome do estado > também é nome de cidade (SP, RJ)
        estado = ESTADOS.get(carregar.UF_BASE, "")
        if lugar.strip() == carregar.UF_BASE.lower() or (estado and re.search(rf"estado d[eo] {estado}", lugar)):
            return True
    return False


def remoto_com_local_exigido(vaga: Vaga) -> bool:
    exigidos = _locais_exigidos(vaga)
    return bool(exigidos) and not any(_local_aceito(lugar) for lugar in exigidos)


def passa_no_local(vaga: Vaga, criterios: dict) -> bool:
    regras = criterios.get("localizacao") or {}
    if not regras:
        return True

    cidade_base = carregar.CIDADE_BASE.lower()
    aceitar_presencial = regras.get("aceitar_presencial", False)
    modalidade = (vaga.modalidade or "").lower().strip()
    texto = f"{vaga.local} {vaga.titulo} {vaga.descricao}".lower()
    local_desconhecido = not vaga.local.strip()
    na_cidade_base = bool(cidade_base) and cidade_base in f"{vaga.local} {vaga.titulo}".lower()

    if vaga.prioritaria:
        remota = modalidade in ("remoto", "home office") or (
            not modalidade and "remoto" in texto and "híbrido" not in texto and "hibrido" not in texto
        )
        return local_desconhecido or na_cidade_base or (remota and not remoto_com_local_exigido(vaga))

    if not modalidade:
        # nunca "home office" antes de "híbrido" > híbrida cita home office
        if "híbrido" in texto or "hibrido" in texto:
            modalidade = "hibrido"
        elif "remoto" in texto or "home office" in texto:
            modalidade = "remoto"
        elif "presencial" in texto:
            modalidade = "presencial"
        else:
            return na_cidade_base

    if modalidade in ("remoto", "home office"):
        return not remoto_com_local_exigido(vaga)
    if modalidade in ("hibrido", "híbrido"):
        return na_cidade_base
    if modalidade == "presencial":
        return aceitar_presencial and na_cidade_base
    return na_cidade_base


# ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆
# FILTRAGEM E CLASSIFICAÇÃO
# ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆ ⋆⭒˚.⋆

def filtrar_e_classificar(vagas: list[Vaga]) -> list[Vaga]:
    criterios = carregar.criterios()
    sempre_incluir_prioritaria = (criterios.get("prioridade") or {}).get("sempre_incluir", False)

    aprovadas = []
    for vaga in vagas:
        vaga.prioritaria = contem_algum(vaga.empresa, carregar.EMPRESAS_PRIORITARIAS)
        if barrada(vaga) or not passa_no_local(vaga, criterios):
            continue
        if (vaga.prioritaria and sempre_incluir_prioritaria) or passa_na_area(vaga, criterios):
            classificar(vaga, criterios)
            aprovadas.append(vaga)
    return _sem_repetidas(aprovadas)


def _sem_repetidas(vagas: list[Vaga]) -> list[Vaga]:
    def chave(v: Vaga) -> tuple[str, str]:
        titulo = re.sub(r"\(c[óo]pia\)", "", v.titulo, flags=re.IGNORECASE)
        return (v.empresa.strip().lower(), re.sub(r"\W+", " ", titulo).strip().lower())

    unicas: dict[tuple[str, str], Vaga] = {}
    for v in vagas:
        atual = unicas.get(chave(v))
        if atual is None or (v.fim_inscricao or date.max) > (atual.fim_inscricao or date.max):
            unicas[chave(v)] = v
    return list(unicas.values())
