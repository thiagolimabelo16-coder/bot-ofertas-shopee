import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("TELEGRAM_TOKEN")


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
    mensagem = (
        "🔥 Gerador de Ofertas Shopee\n\n"
        "Me envie a oferta neste formato:\n\n"
        "Nome do produto\n"
        "Preço\n"
        "Link de afiliado\n\n"
        "Exemplo:\n"
        "Pijama Feminino de Verão\n"
        "29,99\n"
        "https://s.shopee.com.br/xxxxx
