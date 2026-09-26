import os
import html
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import quote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CANAL = "@ofertasshopee7392"

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
    linhas = update.message.text.splitlines()

    if len(linhas) < 4:
      await update.message.reply_text(
        "Envie: nome, preco antigo, preco promocional e link, cada um em uma linha."
    )
      return
    produto = linhas[0].strip()
    preco_antigo = linhas[1].strip()
    preco_novo = linhas[2].strip()
    link = linhas[3].strip()
    valor_antigo = float(preco_antigo.replace(".", "").replace(",", "."))
    valor_novo = float(preco_novo.replace(".", "").replace(",", "."))
    desconto = round((1 - valor_novo / valor_antigo) * 100)
    produto_html = html.escape(produto)
    preco_antigo_html = html.escape(preco_antigo)
    preco_novo_html = html.escape(preco_novo)
    link_html = html.escape(link, quote=True)

    oferta = (
    "🔥 <b>BAIXOU MAISS</b> 🔥\n\n"
    f"🛍️ <b>{produto_html}</b>\n\n"
    f"De <s>R$ {preco_antigo_html}</s>\n"
    f"💸 <b>Por R$ {preco_novo_html}</b>\n\n"
    f"🏷️ <b>{desconto}％ OFF</b>\n\n"
    f"🛒 <b>COMPRE AQUI:</b>\n{link_html}\n\n"
    "⚡ Preço e disponibilidade podem mudar."
    )   
    texto_whatsapp = (
            "🔥 *BAIXOU MAISS* 🔥\n\n"
        f"🛍️ *{produto}*\n\n"
        f"De ~R$ {preco_antigo}~\n"
        f"💸 *Por R$ {preco_novo}*\n"
        f"🏷️ *{desconto}％ OFF*\n\n"
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
