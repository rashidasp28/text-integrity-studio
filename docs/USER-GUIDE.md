# Text Integrity Studio user guide

## Start the application

Run the platform executable and keep its terminal window open. The interface
opens at `http://127.0.0.1:8765`. Press `Ctrl+C` in the terminal to stop it.

## Core workflow

1. Paste text or select **Open document**.
2. Use **Inspect** to inventory unusual characters without changing text.
3. Select a cleaning profile and use **Clean text**.
4. Review highlighted differences before copying or downloading output.
5. Use **Analyse style** for selectable deterministic suggestions.
6. Use **Review integrity** for citation checks and authorised-corpus comparison.

## Supported documents

TXT, Markdown, HTML, DOCX and PDF can be imported. DOCX and PDF are extracted
to text for inspection. The application does not currently write cleaned DOCX
or PDF files. Scanned PDFs require OCR and are not supported.

## Interpreting results

Character findings describe Unicode properties and configured actions. They do
not prove AI authorship. Local corpus matches identify overlap only with files
you deliberately provide. They are not plagiarism verdicts or predicted
Turnitin scores.

## Privacy

Processing occurs in memory on the local computer. The application binds only
to localhost, does not create an account and does not send document text to a
remote service. Downloaded audits are created only when requested.

## Troubleshooting

- If an older interface appears, stop every running copy with `Ctrl+C`, close
  the browser tab and start the newest executable.
- If port 8765 is occupied, stop the older process before restarting.
- If a scanned PDF produces no text, convert it with a trusted OCR tool first.
- If Apply is disabled, no rewrite suggestions are selected or available.
