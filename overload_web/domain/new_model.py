class DomainBibClass:
    def __init__(
        self,
        library: str,
        orders: List[OrderClass],
        bib_id: Optional[str] = None,
        isbn: Optional[str] = None,
        oclc_number: Optional[str] = None,
        upc: Optional[str] = None,
    ):
        self.library = library
        self.orders = orders
        self.bib_id = bib_id
        self.isbn = isbn
        self.oclc_number = oclc_number
        self.upc = upc

    def apply_template(self, template: TemplateClass) -> None:
        for order in self.orders:
            order.apply_template(template=template)

    def match(self, bibs: List[DomainBibClass], matchpoints: List[str]) -> None:
        max_matched_points = -1
        best_match_bib_id = None
        for bib in bibs:
            matched_points = 0
            for attr in matchpoints:
                if getattr(self, attr) == getattr(bib, attr):
                    matched_points += 1

            if matched_points > max_matched_points:
                max_matched_points = matched_points
                best_match_bib_id = bib.bib_id
        self.bib_id = best_match_bib_id


class OrderClass:
    def __init__(
        self,
        audience: Optional[str],
        blanket_po: Optional[str],
        copies: Optional[Union[str, int]],
        country: Optional[str],
        create_date: Optional[Union[datetime.datetime, datetime.date, str]],
        format: Optional[str],
        fund: Optional[str],
        internal_note: Optional[str],
        lang: Optional[str],
        locations: List[str],
        order_type: Optional[str],
        price: Optional[Union[str, int]],
        selector: Optional[str],
        selector_note: Optional[str],
        source: Optional[str],
        status: Optional[str],
        var_field_isbn: Optional[str],
        vendor_code: Optional[str],
        vendor_notes: Optional[str],
        vendor_title_no: Optional[str],
    ) -> None:
        self.audience = audience
        self.blanket_po = blanket_po
        self.copies = copies
        self.country = country
        self.create_date = create_date
        self.format = format
        self.fund = fund
        self.internal_note = internal_note
        self.lang = lang
        self.locations = locations
        self.order_type = order_type
        self.price = price
        self.selector = selector
        self.selector_note = selector_note
        self.source = source
        self.status = status
        self.var_field_isbn = var_field_isbn
        self.vendor_code = vendor_code
        self.vendor_notes = vendor_notes
        self.vendor_title_no = vendor_title_no

    def apply_template(self, template: TemplateClass) -> None:
        template_dict = template.__dict__
        for k, v in template_dict.items():
            if v and k in self.__dict__.keys():
                setattr(self, k, v)


class TemplateClass:
    def __init__(
        self,
        match_rules: MatchRules,
        name: str,
        audience: Optional[str] = None,
        blanket_po: Optional[str] = None,
        copies: Optional[Union[str, int]] = None,
        country: Optional[str] = None,
        create_date: Optional[Union[datetime.datetime, datetime.date, str]] = None,
        format: Optional[str] = None,
        fund: Optional[str] = None,
        internal_note: Optional[str] = None,
        lang: Optional[str] = None,
        order_type: Optional[str] = None,
        price: Optional[Union[str, int]] = None,
        selector: Optional[str] = None,
        selector_note: Optional[str] = None,
        source: Optional[str] = None,
        status: Optional[str] = None,
        var_field_isbn: Optional[str] = None,
        vendor_code: Optional[str] = None,
        vendor_notes: Optional[str] = None,
        vendor_title_no: Optional[str] = None,
    ) -> None:
        self.audience = audience
        self.blanket_po = blanket_po
        self.copies = copies
        self.country = country
        self.create_date = create_date
        self.format = format
        self.fund = fund
        self.internal_note = internal_note
        self.lang = lang
        self.order_type = order_type
        self.match_rules = match_rules
        self.name = name
        self.price = price
        self.selector = selector
        self.selector_note = selector_note
        self.source = source
        self.status = status
        self.var_field_isbn = var_field_isbn
        self.vendor_code = vendor_code
        self.vendor_notes = vendor_notes
        self.vendor_title_no = vendor_title_no


@dataclass
class MatchRules:
    primary_matchpoint: str
    secondary_matchpoint: Optional[str] = None
    tertiary_matchpoint: Optional[str] = None
