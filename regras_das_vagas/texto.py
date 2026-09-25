import re


def contem_algum(texto: str, termos: list[str]) -> bool:
    for termo in termos:
        # nunca termo curto como prefixo > "ti" casaria "atividades"
        fim = r"(?!\w)" if len(termo) <= 3 else ""
        if re.search(rf"(?<!\w){re.escape(termo)}{fim}", texto, re.IGNORECASE):
            return True
    return False


def termos_distintos(texto: str, termos: list[str]) -> set[str]:
    achados = {t.lower() for t in termos if contem_algum(texto, [t])}
    return {t for t in achados if not any(t != outro and t in outro for outro in achados)}
