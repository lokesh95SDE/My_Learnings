def extract_table_from_page(self, pdf_id, page_number, expected_headers):
    """
    Extract a structured table from a PDF page using pdfplumber.

    Args:
        pdf_id: Open PDF identifier/handle used by the existing framework.
        page_number: 1-based PDF page number.
        expected_headers: List of expected column headers.

    Returns:
        List[dict]: Table rows represented as dictionaries.
    """

    pdf = self._get_pdf_document(pdf_id)

    if pdf is None:
        raise AssertionError(f"PDF not found for pdf_id: {pdf_id}")

    if page_number < 1 or page_number > len(pdf.pages):
        raise AssertionError(
            f"Invalid page number {page_number}. "
            f"PDF contains {len(pdf.pages)} pages."
        )

    page = pdf.pages[page_number - 1]

    # The PDF tables shown in your screenshots have visible
    # horizontal and vertical borders.
    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "intersection_tolerance": 5,
        "snap_tolerance": 3,
        "join_tolerance": 3,
        "edge_min_length": 3,
        "min_words_vertical": 1,
        "min_words_horizontal": 1,
    }

    tables = page.extract_tables(table_settings)

    if not tables:
        raise AssertionError(
            f"No table found on PDF page {page_number}"
        )

    expected_headers_normalized = [
        self._normalize_table_text(header)
        for header in expected_headers
    ]

    for table in tables:

        if not table:
            continue

        # Find the header row.
        header_index = None

        for index, row in enumerate(table):
            if not row:
                continue

            normalized_row = [
                self._normalize_table_text(cell)
                for cell in row
            ]

            if self._headers_match(
                normalized_row,
                expected_headers_normalized
            ):
                header_index = index
                break

        if header_index is None:
            continue

        headers = [
            self._clean_table_cell(cell)
            for cell in table[header_index]
        ]

        result = []

        for row in table[header_index + 1:]:

            if not row:
                continue

            cleaned_row = [
                self._clean_table_cell(cell)
                for cell in row
            ]

            # Ignore completely empty rows.
            if not any(cleaned_row):
                continue

            # Ignore repeated headers appearing on continuation pages.
            normalized_row = [
                self._normalize_table_text(cell)
                for cell in cleaned_row
            ]

            if self._headers_match(
                normalized_row,
                expected_headers_normalized
            ):
                continue

            # Make sure row has the same number of cells as headers.
            if len(cleaned_row) < len(headers):
                cleaned_row.extend(
                    [""] * (len(headers) - len(cleaned_row))
                )

            if len(cleaned_row) > len(headers):
                cleaned_row = cleaned_row[:len(headers)]

            row_dict = dict(zip(headers, cleaned_row))

            result.append(row_dict)

        return result

    raise AssertionError(
        f"Expected table headers not found on page {page_number}. "
        f"Expected: {expected_headers}"
    )



def _clean_table_cell(self, value):
    """
    Clean a PDF table cell while preserving meaningful spaces.
    """

    if value is None:
        return ""

    value = str(value)

    # Replace line breaks caused by wrapped PDF text.
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def _normalize_table_text(self, value):
    """
    Normalize text for comparison.
    """

    if value is None:
        return ""

    value = str(value)

    value = re.sub(r"\s+", " ", value)

    return value.strip().lower()


def _headers_match(self, actual_headers, expected_headers):
    """
    Determine whether a PDF row represents the expected table header.
    """

    if len(actual_headers) < len(expected_headers):
        return False

    actual = actual_headers[:len(expected_headers)]

    return actual == expected_headers



def extract_action_audit_trail(self, pdf_id, page_number):
    """
    Extract Action Audit Trail table from the specified PDF page.
    """

    headers = [
        "Date",
        "Operator",
        "Action Type",
        "Status",
        "Comment",
        "Alert Flag"
    ]

    return self.extract_table_from_page(
        pdf_id,
        page_number,
        headers
    )


def extract_audit_trail(self, pdf_id, page_number):
    """
    Extract Audit Trail table from the specified PDF page.
    """

    headers = [
        "Date",
        "Operator",
        "Action Type",
        "Status",
        "Comment",
        "Alert Flag"
    ]

    return self.extract_table_from_page(
        pdf_id,
        page_number,
        headers
    )