"""Render the 20-row Yale sample quotation to PDF and DOCX for checking the layout by eye.

Run from backend/:  .venv/bin/python -m scripts.render_sample [output_dir]
"""
import sys
from pathlib import Path

from app.schemas.quote import QuoteItemIn
from app.services.amount_words import amount_in_words
from app.services.docx_gen import quote_docx
from app.services.pdf import quote_pdf
from app.services.quote_logic import compute_totals

ITEMS = [
    ("Rack with MS Heavy Duty Extruded Structure 25U x 600W x 1000mmD", 1, 75200, None),
    ("Rack (Monitor Arm,PDU,Keyboard Tray,Sliding tray ,Front Door,Rack input plug,Cable Manger, "
     "Input Circuit Breaker )", 1, 52500, None),
    ("Industrial PC IPC510 with Monitor, Keyboard and Mouse", 1, 120000, None),
    ("Programmable Power Supply ( 4CH)", 1, 195500, None),
    ("Oscilloscope", 1, 110000, None),
    ("DMM - 6 1/2 Digit", 1, 158000, None),
    ("32 Channel Relay card +Customized Controller Board", 2, 66000, None),
    ("Connector, USB HUB , Terminal blocks and accessories Etc", 1, 25500, None),
    ("PCAN / CANape tool", 1, 123500, None),
    ("Auto Scanner (Honeywell )", 1, 16500, None),
    ("Sotware Develpoment /LabView Programming including ,GUI Software interface ,Integration ,"
     "Test code Development", 1, 450000, 1),
    ("Labview installer professional for excel generation labview studio", None, None, 1),
    ("Sensors/actuators+Resistive load-10K, 100K, 500K pot etc", 1, 42500, None),
    ("FAN for cooling load resistors", 1, 12300, None),
    ("Test Fixture + Fixture Assembly + Wiring", 1, 225000, None),
    ("Design Charges, Mechanical assembly/ Electrical assembly", 1, 320000, None),
    ("Electrical Accessories", 1, 14500, None),
    ("Installation : At Emechanicz Test Solutions Pvt. Ltd.", None, None, 2),
    ("Documentation & Training", 1, 40000, 2),
    ("Packing&Shipping with Pallet to Customer site @Bangalore", 1, 25000, None),
]

COMPANY = {
    "name": "Emechanicz Test Solutions Pvt Ltd",
    "signatory_name": "EMechanicZ Test Solution Pvt ltd",
    "footer_address": "1st Floor, 1st Cross Adj to SBI ATM, Kodanda Rama Reddy Lyt, Ramamurthy Nagar, "
                      "Bengaluru – 560016,",
    "phone": "+91 9844561185, 9980592929",
    "emails": "Sales@emechanicz.com ; Service@emechanicz.com",
    "gst_no": "29AADCE7362F1ZI",
    "closing_line": "Thanking you and assuring you of our best services at all the times.",
    "system_generated_note": "This is System generated document hence signature not required.",
}


def sample_quote() -> dict:
    items = [QuoteItemIn(sl_no=i + 1, description=d, qty=q, unit_price=p, group_id=g)
             for i, (d, q, p, g) in enumerate(ITEMS)]
    rows, subtotal = compute_totals(items)
    return {
        "ref_no": "ETS/SS10/26-27", "quote_date": "2026-05-23", "issue_status": "1.1",
        "kind_attn": "Mr Jayashekar R Yale",
        "intro": "Dear Sir,\nFurther to your enquiry, please find the quote below",
        "subtotal": float(subtotal), "amount_in_words": amount_in_words(subtotal),
        "customers": {"company_name": "Yale Electronics Services Pvt Ltd"},
        "quote_items": rows,
        "terms": [
            "Delivery: 10-12 Weeks from the date of PO & Confirmation",
            "Payment Terms:50% Advance & 50% Against Delivery",
            "Carriage: Delivery to - At Customer site",
            "Mode of Payment: Through ECS Transfer/Cheque",
            "Order to be placed on:\nEmechanicz Test Solutions Pvt Ltd ,\n"
            "No.190/3,Kalkere Village ,Horamavu Post,Bangalore 560016.",
            "GST @ 18% or actuals extra (GST No. : 29AADCE7362F1ZI)",
            "Validity of quotation: 15 Days from the date of proposal.",
        ],
    }


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    quote = sample_quote()
    (out / "sample-quote.pdf").write_bytes(quote_pdf(quote, COMPANY))
    (out / "sample-quote.docx").write_bytes(quote_docx(quote, COMPANY))
    print(f"Wrote {out / 'sample-quote.pdf'} and {out / 'sample-quote.docx'}")


if __name__ == "__main__":
    main()
