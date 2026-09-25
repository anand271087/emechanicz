from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from app.services.formatting import ORDINAL_RE, format_date, inr, qty
from app.services.quote_layout import table_rows

APP_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = APP_DIR / "static"

_env = Environment(loader=FileSystemLoader(APP_DIR / "templates"),
                   autoescape=select_autoescape(["html"]))
_env.filters.update(inr=inr, qty=qty, date=format_date)


def _ordinals(text) -> Markup:
    """Escape, then superscript ordinals: '1st Floor' -> '1<sup>st</sup> Floor'."""
    return Markup(ORDINAL_RE.sub(r"\1<sup>\2</sup>", str(escape(text or ""))))


def _lines(text) -> Markup:
    """Escape, then keep the user's line breaks."""
    return Markup(str(escape(text or "")).replace("\n", "<br>"))


_env.filters.update(ordinals=_ordinals, lines=_lines)


def render_quote_html(quote: dict, company: dict, static_url: str | None = None) -> str:
    """HTML of the quote document; static_url defaults to local files (for PDF)."""
    return _env.get_template("quote.html").render(
        q=quote, c=company, rows=table_rows(quote.get("quote_items", [])),
        customer=quote.get("customers") or {},
        static=static_url or STATIC_DIR.as_uri(),
    )


def quote_pdf(quote: dict, company: dict) -> bytes:
    from weasyprint import HTML

    return HTML(string=render_quote_html(quote, company)).write_pdf()
