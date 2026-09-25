from fastapi import APIRouter, Depends, HTTPException

from app.deps import CurrentUser, get_current_user, get_db
from app.routers.documents import DOCX_TYPE
from app.schemas.email import SendEmailIn
from app.services.app_settings import get_setting
from app.services.docx_gen import quote_docx
from app.services.formatting import download_name
from app.services.mailer import MailError, MailNotConfigured, send_mail
from app.services.pdf import quote_pdf
from app.services.quotes import fetch_quote, mark_sent

router = APIRouter(prefix="/api/v1/quotes", tags=["email"])


@router.get("/{qid}/email-draft")
def email_draft(qid: str, db=Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    quote = fetch_quote(db, qid)
    customer = quote.get("customers") or {}
    company = get_setting(db, "company")
    attn = quote.get("kind_attn") or customer.get("contact_person") or "Sir/Madam"
    return {
        "to": [customer["email"]] if customer.get("email") else [],
        "cc": [],
        "subject": f"Quotation {quote['ref_no']} - Emechanicz Test Solutions",
        "body": (f"Dear {attn},\n\n"
                 f"Further to your enquiry, please find attached our quotation {quote['ref_no']}.\n\n"
                 "Please feel free to contact us for any clarification.\n\n"
                 f"Thanks & Regards,\n{company.get('name', '')}\n"
                 f"M {company.get('phone', '')}\n{company.get('emails', '')}"),
    }


@router.post("/{qid}/send-email")
def send_quote_email(qid: str, body: SendEmailIn, db=Depends(get_db),
                     user: CurrentUser = Depends(get_current_user)):
    quote = fetch_quote(db, qid)
    company = get_setting(db, "company")
    attachments = [(download_name(quote, "pdf"), quote_pdf(quote, company), "application/pdf")]
    if body.attach_docx:
        attachments.append((download_name(quote, "docx"), quote_docx(quote, company), DOCX_TYPE))
    try:
        send_mail(body.to, body.cc, body.subject, body.body, attachments)
    except MailNotConfigured as e:
        raise HTTPException(503, str(e))
    except MailError as e:
        raise HTTPException(502, str(e))
    mark_sent(db, qid)
    return {"sent": True}
