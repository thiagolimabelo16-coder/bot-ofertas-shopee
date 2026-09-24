import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.environ.get("TELEGRAM_TOKEN")


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
        "https://s.shopee.com.br/xxxxx"
    )
    await update.message.reply_text(mensagem)


async def criar_oferta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]

    if len(linhas) < 3:
        await update.message.reply_text(
            "❌ Não consegui montar a oferta.\n\n"
            "Envie assim:\n\n"
            "Nome do produto\n"
            "Preço\n"
            "Link de afiliado"
        )
        return

    nome = linhas[0]
    preco = linhas[1]
    link = linhas[2]

    if not link.startswith(("http://", "https://")):
        await update.message.reply_text(
            "❌ O terceiro item precisa ser o link da oferta."
        )
        return

    if not preco.upper().startswith("R$"):
        preco = f"R$ {preco}"

    oferta = (
        "🔥 ACHADINHO SHOPEE! 🔥\n\n"
        f"🛍️ {nome}\n\n"
        f"💰 Por apenas *{preco}*\n\n"
        "🛒 PEGUE A OFERTA AQUI:\n"
        f"{link}\n\n"
        "⚡ Preço e disponibilidade podem mudar."
    )

    await update.message.reply_text(oferta, parse_mode="Markdown")


def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN não configurado")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, criar_oferta)
    )

    app.run_polling()


if __name__ == "__main__":
    main()
