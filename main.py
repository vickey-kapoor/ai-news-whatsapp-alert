"""Main entry point for AI Research WhatsApp Digest."""

import os
import sys

from dotenv import load_dotenv

from src.logger import get_logger
from src.research_fetcher import fetch_ai_research
from src.news_ranker import rank_research
from src.news_summarizer import summarize_research, summarize_research_detailed
from src.whatsapp_sender import format_research_message, send_whatsapp_message
from src.telegram_sender import send_telegram_message
from src.pdf_generator import generate_research_pdf
from src.json_exporter import export_papers, export_digest

logger = get_logger(__name__)


def main():
    """Fetch AI research, select the most important, and send to WhatsApp."""
    # Load environment variables
    load_dotenv()

    # Get required environment variables
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_whatsapp = os.getenv("TWILIO_WHATSAPP_NUMBER")
    your_whatsapp = os.getenv("YOUR_WHATSAPP_NUMBER")
    openai_key = os.getenv("OPENAI_API_KEY")

    # Telegram config (optional but recommended)
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    # Validate required variables
    missing = []
    has_whatsapp = all([twilio_sid, twilio_token, twilio_whatsapp, your_whatsapp])
    has_telegram = all([telegram_token, telegram_chat_id])

    if not has_whatsapp and not has_telegram:
        missing.append("TWILIO or TELEGRAM credentials")
    if not openai_key:
        missing.append("OPENAI_API_KEY")

    if missing:
        logger.error("Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)

    # Fetch AI research
    logger.info("Fetching AI research...")
    research_items = []
    try:
        research_items = fetch_ai_research(max_results=10)
        logger.info("Found %d research items", len(research_items))
    except Exception as e:
        logger.error("Error fetching research: %s", e)

    # Check if we have any content
    if not research_items:
        logger.info("No AI research found today")
        sys.exit(0)

    # Rank and select top research
    logger.info("Selecting most important research...")
    try:
        top_research = rank_research(research_items, openai_key)
        logger.info("Selected: %s", top_research["title"])
    except Exception as e:
        logger.error("Error ranking research: %s", e)
        top_research = research_items[0]

    # Export papers to JSON for dashboard
    logger.info("Exporting papers to JSON...")
    top_paper_id = None
    try:
        top_paper_id = export_papers(research_items, top_research)
        logger.info("Papers exported to data/papers.json")
    except Exception as e:
        logger.warning("Could not export papers to JSON: %s", e)

    # Generate short summary for WhatsApp
    logger.info("Generating WhatsApp summary...")
    try:
        top_research = summarize_research(top_research, openai_key)
        if "summary" in top_research:
            logger.info("Generated short summary for WhatsApp")
    except Exception:
        logger.warning("Could not generate WhatsApp summary")

    # Generate detailed summary for PDF
    logger.info("Generating detailed PDF summary...")
    try:
        top_research = summarize_research_detailed(top_research, openai_key)
        if "detailed_summary" in top_research:
            logger.info("Generated detailed summary for PDF")
    except Exception:
        logger.warning("Could not generate detailed summary")

    # Generate PDF report
    logger.info("Generating PDF report...")
    pdf_path = None
    try:
        pdf_path = generate_research_pdf(top_research)
        logger.info("PDF saved: %s", pdf_path)
    except Exception:
        logger.warning("Could not generate PDF")

    # Send Telegram message
    telegram_sent = False
    if has_telegram:
        logger.info("Sending Telegram message...")
        try:
            message = format_research_message(top_research)
            send_telegram_message(telegram_token, telegram_chat_id, message)
            telegram_sent = True
        except Exception as e:
            logger.error("Error sending Telegram message: %s", e)

    # Send WhatsApp message
    whatsapp_sent = False
    if has_whatsapp:
        logger.info("Sending WhatsApp message...")
        try:
            message = format_research_message(top_research)
            message_sid = send_whatsapp_message(
                twilio_sid,
                twilio_token,
                twilio_whatsapp,
                your_whatsapp,
                message,
            )
            logger.info("Message sent successfully! SID: %s", message_sid)
            whatsapp_sent = True
        except Exception as e:
            logger.error("Error sending WhatsApp message: %s", e)

    # Export digest entry to JSON for dashboard
    logger.info("Exporting digest to JSON...")
    try:
        workflow_run_id = os.getenv("GITHUB_RUN_ID", "")
        export_digest(
            top_paper_id=top_paper_id,
            papers_fetched=len(research_items),
            pdf_path=pdf_path,
            whatsapp_sent=whatsapp_sent,
            workflow_run_id=workflow_run_id
        )
        logger.info("Digest exported to data/digests.json")
    except Exception as e:
        logger.warning("Could not export digest to JSON: %s", e)

    if not whatsapp_sent and not telegram_sent:
        sys.exit(1)


if __name__ == "__main__":
    main()
