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





${complete_message_content}=    Extract Complete Message Content
...    ${pdf_id}

Log    ${complete_message_content}





Test_Extract_Message_Content_Fields
    [Documentation]    Extract complete Message Content from PDF

    [Tags]    pdf    extraction    message_content

    ${pdf_id}=    Open PDF File    ${PDF_FILE_PATH}

    ${complete_message_content}=    Extract Complete Message Content
    ...    ${pdf_id}

    ${complete_message_content}=    Clean Extracted Text
    ...    ${complete_message_content}

    Log    ${complete_message_content}

    Close PDF File    ${pdf_id}