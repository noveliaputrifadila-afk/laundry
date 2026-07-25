from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def rupiah(value):
    try:
        nilai = Decimal(value or 0)
    except (InvalidOperation, TypeError, ValueError):
        nilai = Decimal("0")

    hasil = f"{nilai:,.0f}"
    hasil = hasil.replace(",", ".")

    return f"Rp{hasil}"