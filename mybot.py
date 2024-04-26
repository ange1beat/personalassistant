from crewai import Agent, Task, Crew, Process
from crewai_tools import tool
from langchain_groq import ChatGroq
from crewai_tools.tools import FileReadTool
from langchain_community.tools import DuckDuckGoSearchRun
import os
from langchain.agents import load_tools


from telegram.ext import ApplicationBuilder
from telegram import Update
from telegram.ext import BusinessConnectionHandler, MessageHandler, CommandHandler, ContextTypes, filters



telegram = ApplicationBuilder().token("ВАШ ТГ КЛЮЧ").concurrent_updates(True).build()



async def business_welcome_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.business_connection.user

    if update.business_connection.is_enabled:

        print(update.business_connection.id)

        if not update.business_connection.can_reply:
            await user.send_message("You didn't let bot to reply!")
        else:
            await user.send_message("Connected, You are rock!")

    else:
        try:
            await user.send_message("You are disconnected the bot :/")
        finally:
            pass

async def echo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    llm = ChatGroq(
    api_key= "ВАШ КЛЮЧ ОТ GROQ",
    model = "llama3-8b-8192"
    )

    question = update.effective_message.text

    classifier = Agent(
        role = "question classifier",
        goal = "ты аккуратно определяешь класс вопроса на основе срочности, для каждого вопроса давай свой класс: важный, не важный, ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ",
        backstory = "Ты ИИ ассистент который определяет класс вопроса, чтобы понять его важность, твоя работа это помогать сотрудникам распределять вопросы по срочности",
        verbose = True,
        allow_delegation = False,
        llm = llm
    )

    responder = Agent(
        role = "question responder",
        goal = "ты отвечаешь только на НЕ важные вопросы, если вопрос важный, то не отвечаешь и игнорируешь, ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ и БЕЗ ВОСКЛИЦАТЕЛЬНЫХ ЗНАКОВ в спокойной манере",
        backstory = "Ты ИИ ассистент который отвечает на не важные вопросы, важность сообщения тебе определяет 'classifier' агент, веди себя как человек",
        verbose = True,
        allow_delegation = False,
        llm = llm
    )

    classify_email = Task (
        description = f"Классифицируй этот вопрос: '{question}'",
        agent = classifier,
        expected_output = "один из этих трех классов: 'важный', 'не важный'"
    )

    respond_to_email = Task (
        description = f"Ответь на вопрос: '{question}'",
        agent = responder,
        expected_output = "Короткий ответ на вопрос"
    )

    crew = Crew (
        agents = [classifier, responder],
        tasks = [classify_email, respond_to_email],
        verbose = 2,
        process = Process.sequential
    )

    output = crew.kickoff()
    print(output)
    await update.effective_message.reply_text(output)


telegram.add_handler(BusinessConnectionHandler(business_welcome_callback)) 
telegram.add_handler(MessageHandler(
    filters=filters.UpdateType.BUSINESS_MESSAGES & filters.TEXT, callback=echo_callback
))


telegram.run_polling()


