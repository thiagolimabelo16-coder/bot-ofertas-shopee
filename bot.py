import os
import html
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import quote
from urllib.request import Request, urlopen
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CANAL = "@ofertasshopee7392"
def formatar_preco(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def buscar_produto_shopee(link):
    req = Request(
        link,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urlopen(req, timeout=15) as resposta:
        url_final = resposta.geturl()
        print("URL FINAL SHOPEE:", url_final, flush=True)
        achou = re.search(r"/opaanlp/(\d+)/(\d+)", url_final)

    if not achou:
        achou = re.search(r"-i\.(\d+)\.(\d+)", url_final)

    if not achou:
        achou = re.search(r"/product/(\d+)/(\d+)", url_final)

    if not achou:
        return None

    shopid, itemid = achou.groups()

    # Busca a própria página do produto em vez da API /api/v4
    req = Request(
        url_final,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 13) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml"
        }
    )

    with urlopen(req, timeout=15) as resposta:
        pagina = resposta.read().decode("utf-8", errors="ignore")
         print("HTML SHOPEE:", pagina[:2000], flush=True)
    # Tenta encontrar o nome do produto
    nome_match = re.search(
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)',
        pagina,
        re.IGNORECASE
    )

    if not nome_match:
        nome_match = re.search(
            r'<title>(.*?)</title>',
            pagina,
            re.IGNORECASE | re.DOTALL
        )

    # Tenta encontrar o preço
    preco_match = re.search(
        r'"price"\s*:\s*"?([0-9]+(?:\.[0-9]+)?)"?',
        pagina,
        re.IGNORECASE
    )

    if not nome_match or not preco_match:
        print("ERRO SHOPEE: nome ou preço não encontrados", flush=True)
        return None

    nome = html.unescape(nome_match.group(1)).strip()

    valor = float(preco_match.group(1))

    # Alguns valores da Shopee aparecem multiplicados por 100000
    if valor > 100000:
        valor = valor / 100000

    preco_atual = formatar_preco(valor)

    return {
        "produto": nome,
        "preco_novo": preco_atual,
        "preco_antigo": None
    }
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot funcionando!")

    def log_message(self, format, *args):
        return


def iniciar_servidor():
    port = int(os.environ.get("PORT", 10000))
    servidor = HTTPServer(("0.0.0.0", port), HealthHandler)
    servidor.serve_forever()
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Gerador de Ofertas Shopee\n\n"
        "Envie 4 linhas:\n"
"Nome do produto\n"
"Preço antigo\n"
"Preço promocional\n"
"Link de afiliado"
    )

async def receber_oferta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    linhas = texto.splitlines()

    if len(linhas) == 1 and texto.startswith(("http://", "https://")) and "shopee" in texto.lower():
        link = texto

        await update.message.reply_text("🔎 Buscando dados do produto...")

        try:
            dados = buscar_produto_shopee(link)
            print("DADOS SHOPEE:", repr(dados), flush=True)
        except Exception as e:
            print("ERRO SHOPEE:", repr(e), flush=True)
            dados = None

        if not dados:
            await update.message.reply_text(
            "Não consegui ler esse produto automaticamente.\n\n"
            "Você ainda pode enviar 4 linhas:\n"
            "Nome do produto\n"
            "Preço antigo\n"
            "Preço promocional\n"
            "Link de afiliado"
            )
            return

            produto = dados["produto"]
            preco_novo = dados["preco_novo"]
            preco_antigo = dados["preco_antigo"]

    else:
        if len(linhas) < 4:
            await update.message.reply_text(
            "Envie somente o link da Shopee ou 4 linhas:\n"
            "Nome do produto\n"
            "Preço antigo\n"
            "Preço promocional\n"
            "Link de afiliado"
            )
            return

        produto = linhas[0].strip()
        preco_antigo = linhas[1].strip()
        preco_novo = linhas[2].strip()
        link = linhas[3].strip()

    valor_novo = float(preco_novo.replace(".", "").replace(",", "."))
    desconto = None

    if preco_antigo and preco_antigo not in ("0", "0,00", "-"):
        valor_antigo = float(preco_antigo.replace(".", "").replace(",", "."))

        if valor_antigo > valor_novo:
            desconto = round((1 - valor_novo / valor_antigo) * 100)
        else:
            preco_antigo = None
    else:
        preco_antigo = None
    produto_html = html.escape(produto)
    preco_antigo_html = html.escape(preco_antigo) if preco_antigo else None
    preco_novo_html = html.escape(preco_novo)
    link_html = html.escape(link, quote=True)

    if preco_antigo and desconto is not None:
        bloco_preco_telegram = (
            f"De <s>R$ {preco_antigo_html}</s>\n"
            f"💸 <b>Por R$ {preco_novo_html}</b>\n"
            f"🏷️ <b>{desconto}% OFF</b>\n\n"
        )

        bloco_preco_whatsapp = (
            f"De ~R$ {preco_antigo}~\n"
            f"💸 *Por R$ {preco_novo}*\n"
            f"🏷️ *{desconto}% OFF*\n\n"
        )
    else:
        bloco_preco_telegram = (
            f"💸 <b>Por R$ {preco_novo_html}</b>\n\n"
        )

        bloco_preco_whatsapp = (
            f"💸 *Por R$ {preco_novo}*\n\n"
        )

    oferta = (
        "🔥 <b>BAIXOU MAISS</b> 🔥\n\n"
        f"🛍️ <b>{produto_html}</b>\n\n"
        f"{bloco_preco_telegram}"
        f"🛒 <b>COMPRE AQUI:</b>\n{link_html}\n\n"
        "⚡ Preço e disponibilidade podem mudar."
    )

    texto_whatsapp = (
        "🔥 *BAIXOU MAISS* 🔥\n\n"
        f"🛍️ *{produto}*\n\n"
        f"{bloco_preco_whatsapp}"
        f"🛒 *COMPRE AQUI:*\n{link}\n\n"
        "⚡ Preço e disponibilidade podem mudar."
       )

    whatsapp_url = "https://wa.me/?text=" + quote(texto_whatsapp)

    teclado = InlineKeyboardMarkup([
        [InlineKeyboardButton("📲 Enviar no WhatsApp", url=whatsapp_url)]
    ])

    await update.message.reply_text(
        oferta,
        parse_mode="HTML",
        reply_markup=teclado
        )
    await context.bot.send_message(chat_id=CANAL, text=oferta, parse_mode="HTML")

def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN nao configurado")

    threading.Thread(
        target=iniciar_servidor,
        daemon=True
    ).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            receber_oferta
        )
    )
    app.run_polling()


if __name__ == "__main__":
    main()
