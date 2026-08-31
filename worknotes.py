def extract_table_from_page(self, pdf_id, page_number, expected_headers):
    """
    Extract a structured table from a specific PDF page.

    pdf_id is the file path returned by Open PDF File.
    """

    if pdf_id not in self._pdf_cache:
        raise AssertionError(
            f"PDF is not open or not found in cache: {pdf_id}"
        )

    pdf = self._pdf_cache[pdf_id]

    if page_number < 1 or page_number > len(pdf.pages):
        raise AssertionError(
            f"Invalid page number {page_number}. "
            f"PDF contains {len(pdf.pages)} pages."
        )

    page = pdf.pages[page_number - 1]

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
            f"No table found on page {page_number}"
        )

    expected_headers_normalized = [
        self._normalize_table_text(header)
        for header in expected_headers
    ]

    for table in tables:

        if not table:
            continue

        header_index = None

        # Find the expected header row
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

        # Extract rows after the header
        for row in table[header_index + 1:]:

            if not row:
                continue

            cleaned_row = [
                self._clean_table_cell(cell)
                for cell in row
            ]

            # Ignore empty rows
            if not any(cleaned_row):
                continue

            # Ignore repeated header rows
            normalized_row = [
                self._normalize_table_text(cell)
                for cell in cleaned_row
            ]

            if self._headers_match(
                normalized_row,
                expected_headers_normalized
            ):
                continue

            # Make number of cells match number of headers
            if len(cleaned_row) < len(headers):
                cleaned_row.extend(
                    [""] * (len(headers) - len(cleaned_row))
                )

            elif len(cleaned_row) > len(headers):
                cleaned_row = cleaned_row[:len(headers)]

            row_dictionary = dict(
                zip(headers, cleaned_row)
            )

            result.append(row_dictionary)

        return result

    raise AssertionError(
        f"Expected table headers not found on page {page_number}. "
        f"Expected headers: {expected_headers}"
    )




def _clean_table_cell(self, value):
    """
    Clean PDF table cell text.

    PDF line wrapping such as:
        Filtering
        Engine

    becomes:
        Filtering Engine
    """

    if value is None:
        return ""

    value = str(value)

    # Convert line breaks / multiple spaces to one space
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def _normalize_table_text(self, value):
    """
    Normalize text when comparing headers.
    """

    if value is None:
        return ""

    value = str(value)

    value = re.sub(r"\s+", " ", value)

    return value.strip().lower()


def _headers_match(self, actual_headers, expected_headers):
    """
    Check whether a row contains the expected table headers.
    """

    if len(actual_headers) < len(expected_headers):
        return False

    actual = actual_headers[:len(expected_headers)]

    return actual == expected_headers


def extract_action_audit_trail(self, pdf_id, page_number):
    """
    Extract Action Audit Trail table.
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
    Extract Audit Trail table.
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



PDF2Library.py
│
├── Open PDF File
│       │
│       ├── pdfplumber.open(file_path)
│       ├── self._pdf_cache[file_path] = pdf
│       └── return file_path
│
├── Get Page Text
│
├── Extract Value By Regex
│
├── Extract Value By Key
│
├── Extract Table From Page       ← NEW
│       │
│       ├── get PDF from _pdf_cache
│       ├── pdfplumber.extract_tables()
│       ├── find static headers
│       ├── extract dynamic rows
│       └── return List[Dictionary]
│
├── Extract Action Audit Trail    ← NEW
│       └── Extract Table From Page
│
└── Extract Audit Trail            ← NEW
        └── Extract Table From Page