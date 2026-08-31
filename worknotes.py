    @keyword("Extract Complete Message Content")
    def extract_complete_message_content(
        self,
        file_path: str,
        start_page: Optional[int] = None,
        x_tolerance: float = 3,
        y_tolerance: float = 3,
        keep_blank_chars: bool = True
    ) -> str:
        """
        Extracts complete Message Content from consecutive PDF pages.

        If start_page is provided, extraction starts from that page.
        If start_page is None, the first Message Content page is found
        automatically.

        The Message Content is continued across consecutive pages and
        returned as one combined string.
        """

        if file_path not in self._pdf_cache:
            raise AssertionError(
                f"PDF file '{file_path}' not opened. "
                f"Use 'Open PDF File' first."
            )

        pdf = self._pdf_cache[file_path]

        total_pages = len(pdf.pages)

        # ---------------------------------------------------------
        # Find starting page automatically if not supplied
        # ---------------------------------------------------------
        if start_page is None:

            for index, page in enumerate(pdf.pages, start=1):

                page_text = page.extract_text(
                    x_tolerance=x_tolerance,
                    y_tolerance=y_tolerance,
                    keep_blank_chars=keep_blank_chars
                ) or ""

                if re.search(
                    r"Message\s+Content",
                    page_text,
                    re.IGNORECASE
                ):
                    start_page = index
                    break

        if start_page is None:
            return ""

        if start_page < 1 or start_page > total_pages:
            raise AssertionError(
                f"Page number '{start_page}' out of range. "
                f"PDF has {total_pages} pages."
            )

        # ---------------------------------------------------------
        # Extract Message Content page by page
        # ---------------------------------------------------------
        complete_content = []

        for page_number in range(start_page, total_pages + 1):

            page = pdf.pages[page_number - 1]

            page_text = page.extract_text(
                x_tolerance=x_tolerance,
                y_tolerance=y_tolerance,
                keep_blank_chars=keep_blank_chars
            ) or ""

            if not page_text:
                continue

            # Check whether this page contains Message Content
            message_match = re.search(
                r"Message\s+Content",
                page_text,
                re.IGNORECASE
            )

            # First page must contain Message Content.
            # Following pages may be continuation pages.
            if page_number == start_page:

                if not message_match:
                    break

                content = page_text[message_match.end():]

            else:

                # Stop when the next section starts.
                #
                # Your PDF examples show sections such as:
                # Action Audit Trail
                # Hits Overview
                # Hits Details
                #
                if re.search(
                    r"Action\s+Audit\s+Trail|"
                    r"Hits\s+Overview|"
                    r"Hits\s+Details",
                    page_text,
                    re.IGNORECASE
                ):
                    break

                # If another Message Content header exists,
                # remove that header.
                if message_match:
                    content = page_text[message_match.end():]
                else:
                    content = page_text

            # Remove footer from the extracted page content
            content = re.split(
                r"Live\s+Alert\s+Filtering\s+Report",
                content,
                maxsplit=1,
                flags=re.IGNORECASE
            )[0]

            content = content.strip()

            if content:
                complete_content.append(content)

        return "\n".join(complete_content)





@keyword("Extract Value By Regex")
def extract_value_by_regex(
    self,
    file_path: str,
    pattern: str,
    occurrence: int = 1,
    case_sensitive: bool = False,
    page_number: Optional[int] = None
) -> str:
    """
    Extracts a value using a custom regex pattern.

    If page_number is provided, regex extraction is performed
    only on that specific page.

    If page_number is None, the entire PDF text is searched.

    Arguments:
    - file_path: PDF file path/handle
    - pattern: Regex pattern with at least one capture group
    - occurrence: Match occurrence to return (1-based)
    - case_sensitive: Whether matching is case sensitive
    - page_number: Optional 1-based page number

    Returns:
    - Extracted value from the first capture group
    - Empty string if no match is found
    """

    # ------------------------------------------------------------
    # Get text from requested page OR entire PDF
    # ------------------------------------------------------------

    if page_number is not None:
        text = self.get_page_text(file_path, page_number)
    else:
        if file_path not in self._extracted_text_cache:
            raise AssertionError(
                f"PDF file '{file_path}' not opened. "
                f"Use 'Open PDF File' first."
            )

        text = self._extracted_text_cache[file_path]

    # ------------------------------------------------------------
    # Apply regex
    # ------------------------------------------------------------

    flags = 0 if case_sensitive else re.IGNORECASE

    matches = re.findall(
        pattern,
        text,
        flags
    )

    # ------------------------------------------------------------
    # Return requested occurrence
    # ------------------------------------------------------------

    if matches and len(matches) >= occurrence:

        match = matches[occurrence - 1]

        if isinstance(match, tuple):
            return match[0].strip()

        return match.strip()

    return ""



*** Test Cases ***

Test_Validate_Common_Footer
    [Documentation]    Validate common footer information on all pages except page 1
    [Tags]             pdf    footer    validation

    ${pdf_id}=          Open PDF File    ${PDF_FILE_PATH}
    ${page_count}=      Get PDF Page Count    ${pdf_id}

    Log    Total PDF pages: ${page_count}

    Should Be True    ${page_count} >= 2

    # Page 2 will be used as the baseline.
    ${expected_report_title}=
    ...    Extract Value By Regex
    ...    ${pdf_id}
    ...    ${message_information_report_title}
    ...    1
    ...    False
    ...    2

    ${expected_classification}=
    ...    Extract Value By Regex
    ...    ${pdf_id}
    ...    ${message_information_classification}
    ...    1
    ...    False
    ...    2

    ${expected_report_created_full}=
    ...    Extract Value By Regex
    ...    ${pdf_id}
    ...    ${message_information_report_created_full}
    ...    1
    ...    False
    ...    2

    Should Not Be Empty    ${expected_report_title}
    Should Not Be Empty    ${expected_classification}
    Should Not Be Empty    ${expected_report_created_full}

    Log    Expected Report Title: ${expected_report_title}
    Log    Expected Classification: ${expected_classification}
    Log    Expected Report Created: ${expected_report_created_full}

    # Extract timestamp and page number from Page 2
    ${expected_parts}=    Split String    ${expected_report_created_full}

    ${expected_timestamp}=
    ...    Set Variable
    ...    ${expected_parts}[0] ${expected_parts}[1]

    ${expected_page_number}=
    ...    Get From List
    ...    ${expected_parts}
    ...    2

    Should Be Equal    ${expected_page_number}    2

    # ------------------------------------------------------------
    # Validate Page 2 through last page
    # ------------------------------------------------------------

    ${last_page}=    Evaluate    ${page_count} + 1

    FOR    ${page_number}    IN RANGE    2    ${last_page}

        Log    ===== Validating Footer - Page ${page_number} =====

        ${actual_report_title}=
        ...    Extract Value By Regex
        ...    ${pdf_id}
        ...    ${message_information_report_title}
        ...    1
        ...    False
        ...    ${page_number}

        ${actual_classification}=
        ...    Extract Value By Regex
        ...    ${pdf_id}
        ...    ${message_information_classification}
        ...    1
        ...    False
        ...    ${page_number}

        ${actual_report_created_full}=
        ...    Extract Value By Regex
        ...    ${pdf_id}
        ...    ${message_information_report_created_full}
        ...    1
        ...    False
        ...    ${page_number}

        Should Not Be Empty    ${actual_report_title}
        Should Not Be Empty    ${actual_classification}
        Should Not Be Empty    ${actual_report_created_full}

        # --------------------------------------------------------
        # Common footer fields
        # --------------------------------------------------------

        Should Be Equal
        ...    ${actual_report_title}
        ...    ${expected_report_title}
        ...    Report Title mismatch on page ${page_number}

        Should Be Equal
        ...    ${actual_classification}
        ...    ${expected_classification}
        ...    Classification mismatch on page ${page_number}

        # --------------------------------------------------------
        # Separate timestamp and page number
        # --------------------------------------------------------

        ${actual_parts}=    Split String    ${actual_report_created_full}

        ${actual_timestamp}=
        ...    Set Variable
        ...    ${actual_parts}[0] ${actual_parts}[1]

        ${actual_page_number}=
        ...    Get From List
        ...    ${actual_parts}
        ...    2

        # Timestamp must be identical on all pages
        Should Be Equal
        ...    ${actual_timestamp}
        ...    ${expected_timestamp}
        ...    Report Created Timestamp mismatch on page ${page_number}

        # Page number must match actual PDF page
        Should Be Equal
        ...    ${actual_page_number}
        ...    ${page_number}
        ...    Incorrect page number on page ${page_number}

        Log    Footer validated successfully on page ${page_number}

    END

    Close PDF File    ${pdf_id}