from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response

from app.deps import get_current_user, get_db
from app.services.app_settings import get_setting
from app.services.formatting import download_name
from app.services.pdf import quote_pdf, render_quote_html
from app.services.quotes import fetch_quote

router = APIRouter(prefix="/api/v1/quotes", tags=["documents"],
                   dependencies=[Depends(get_current_user)])


def _attachment(content: bytes, media_type: str, filename: str) -> Response:
    return Response(content, media_type=media_type,
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/{qid}/html", response_class=HTMLResponse)
def preview_html(qid: str, request: Request, db=Depends(get_db)):
    static_url = str(request.base_url).rstrip("/") + "/static"
    return render_quote_html(fetch_quote(db, qid), get_setting(db, "company"), static_url)


@router.get("/{qid}/pdf")
def download_pdf(qid: str, db=Depends(get_db)):
    quote = fetch_quote(db, qid)
    return _attachment(quote_pdf(quote, get_setting(db, "company")), "application/pdf",
                       download_name(quote, "pdf"))
