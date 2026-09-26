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
    from http.cookiejar import CookieJar
    from urllib.request import build_opener, HTTPCookieProcessor

    cookies = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookies))

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 13) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Mobile Safari/537.36"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
    }

    resolver_req = Request(
        link,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urlopen(resolver_req, timeout=15) as resposta:
        url_final = resposta.geturl()
        resposta.read()

    print("URL FINAL SHOPEE:", url_final, flush=True)

    achou = re.search(r"/opaanlp/(\d+)/(\d+)", url_final)

    if not achou:
        achou = re.search(r"-i\.(\d+)\.(\d+)", url_final)

    if not achou:
        achou = re.search(r"/product/(\d+)/(\d+)", url_final)

    if not achou:
        print("ERRO SHOPEE: IDs não encontrados", flush=True)
        return None

    shopid, itemid = achou.groups()

    api_url = (
        "https://shopee.com.br/api/v4/pdp/get_pc"
        f"?shop_id={shopid}&item_id={itemid}"
    )

    api_req = Request(
        api_url,
        headers={
            "User-Agent": headers["User-Agent"],
            "Accept": "application/json",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Referer": url_final,
            "X-API-SOURCE": "pc"
        }
    )

    with opener.open(api_req, timeout=15) as resposta:
        dados = json.loads(resposta.read().decode("utf-8"))

    if dados.get("error") not in (None, 0):
        print("ERRO API SHOPEE:", dados, flush=True)
        return None

    data = dados.get("data") or {}
    item = data.get("item") or {}
    produto_preco = data.get("product_price") or {}

    nome = item.get("title") or item.get("name")

    def pegar_valor(obj):
        if isinstance(obj, (int, float)):
            return obj

        if isinstance(obj, dict):
            valor = obj.get("single_value")

            if isinstance(valor, (int, float)) and valor > 0:
                return valor

            valor = obj.get("range_min")

            if isinstance(valor, (int, float)) and valor > 0:
                return valor

        return None

    preco_atual_raw = pegar_valor(produto_preco.get("price"))

    if not preco_atual_raw:
        preco_atual_raw = item.get("price") or item.get("price_min")

    preco_antigo_raw = pegar_valor(
        produto_preco.get("price_before_discount")
    )

    if not preco_antigo_raw:
        preco_antigo_raw = item.get("price_before_discount")

    if not nome or not preco_atual_raw:
        print("ERRO SHOPEE: API sem nome/preço", flush=True)
        return None

    preco_atual = formatar_preco(float(preco_atual_raw) / 100000)

    preco_antigo = None

    if preco_antigo_raw and preco_antigo_raw > preco_atual_raw:
        preco_antigo = formatar_preco(
            float(preco_antigo_raw) / 100000
        )

    return {
        "produto": nome,
        "preco_novo": preco_atual,
        "preco_antigo": preco_antigo
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
        if len(linhas) not in (3, 4):
            await update.message.reply_text(
                "Envie em um destes formatos:\n\n"
                "SEM promoção (3 linhas):\n"
                "Nome do produto\n"
                "Preço atual\n"
                "Link de afiliado\n\n"
                "COM promoção (4 linhas):\n"
                "Nome do produto\n"
                "Preço antigo\n"
                "Preço promocional\n"
                "Link de afiliado"
            )
            return

        produto = linhas[0].strip()

        if len(linhas) == 3:
            preco_antigo = None
            preco_novo = linhas[1].strip()
            link = linhas[2].strip()
        else:
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
