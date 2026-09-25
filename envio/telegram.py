import time
from datetime import date

import requests

from configuracao import carregar

CANAIS = carregar.TELEGRAM
TENTATIVAS_ENVIO = 3
LIMITE_TELEGRAM = 4000  # nunca acima de 4096 > limite do Telegram


def canal_configurado(canal: str) -> bool:
    return all(CANAIS.get(canal, (None, None)))


def canal_efetivo(canal: str) -> str:
    return canal if canal_configurado(canal) else "estagio"


def enviar_mensagem(texto: str, canal: str = "estagio") -> None:
    token, chat_id = CANAIS[canal_efetivo(canal)]
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_ESTAGIO_BOT_TOKEN e TELEGRAM_ESTAGIO_CHAT_ID não configurados.")
    for tentativa in range(1, TENTATIVAS_ENVIO + 1):
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": texto,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=15,
            )
            if resp.status_code == 429:
                time.sleep(resp.json().get("parameters", {}).get("retry_after", 5))
                continue
            resp.raise_for_status()
            return
        except requests.ConnectionError:
            if tentativa == TENTATIVAS_ENVIO:
                raise
            time.sleep(5 * tentativa)
    raise RuntimeError(f"Telegram recusou a mensagem {TENTATIVAS_ENVIO} vezes.")


def enviar_em_partes(blocos: list[str], canal: str = "estagio") -> None:
    mensagem = ""
    for bloco in blocos:
        if mensagem and len(mensagem) + len(bloco) + 2 > LIMITE_TELEGRAM:
            enviar_mensagem(mensagem, canal)
            mensagem = ""
        mensagem = f"{mensagem}\n\n{bloco}" if mensagem else bloco
    if mensagem:
        enviar_mensagem(mensagem, canal)


def estrelas_texto(n: int) -> str:
    return "⭐" * n if n else ""


def prazo_texto(fim: date | None, hoje: date | None = None) -> str:
    if not fim:
        return ""
    faltam = (fim - (hoje or date.today())).days
    if faltam <= 0:
        quando = "encerra HOJE"
    elif faltam == 1:
        quando = "encerra amanhã"
    else:
        quando = f"faltam {faltam} dias"
    return f"⏰ até {fim:%d/%m} ({quando})"


def ordenar(vagas: list) -> list:
    return sorted(vagas, key=lambda v: (-v.estrelas, v.fim_inscricao or date.max))


def formatar_vaga(vaga) -> str:
    linhas = [f"{estrelas_texto(vaga.estrelas)} <b>{vaga.titulo}</b>".strip(),
              f"{vaga.empresa} — {vaga.local}"]
    prazo = prazo_texto(vaga.fim_inscricao)
    if prazo:
        linhas.append(prazo)
    linhas.append(vaga.link)
    return "\n".join(linhas)


def notificar_vaga_nova(vaga, canal: str = "estagio") -> None:
    enviar_mensagem(formatar_vaga(vaga), canal)


def notificar_lote(vagas: list, canal: str = "estagio") -> None:
    blocos = [f"<b>{len(vagas)} vagas novas</b>"]
    grupo_atual = None
    for v in ordenar(vagas):
        if v.estrelas != grupo_atual:
            grupo_atual = v.estrelas
            blocos.append(f"━━━━━━ {estrelas_texto(v.estrelas)} ━━━━━━")
        blocos.append(formatar_vaga(v))
    enviar_em_partes(blocos, canal)
