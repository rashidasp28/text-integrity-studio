# Release candidate acceptance tests

Record the operating system, executable checksum, result and evidence for each
test. A failed critical test blocks v1.0.0.

| ID | Test | Expected result | Priority |
|---|---|---|---|
| AT-01 | Start application offline | Local interface opens on 127.0.0.1 | Critical |
| AT-02 | Paste ordinary text | Text remains unchanged until an action is chosen | Critical |
| AT-03 | Clean `A` + U+200B + `B` | Preview is `AB` with an audited removal | Critical |
| AT-04 | Undo cleaning | Original text is restored | Critical |
| AT-05 | Rewrite the documented sample | Protected date, citation and measurement remain unchanged | Critical |
| AT-06 | Analyse text with no suggestions | Apply is visibly disabled with an explanation | High |
| AT-07 | Import DOCX | Paragraph text appears with extraction warning | Critical |
| AT-08 | Import macro-bearing DOCX | Import is rejected | Critical |
| AT-09 | Import selectable-text PDF | Text appears with layout warning | High |
| AT-10 | Import scanned PDF | No-text or OCR limitation is explained | High |
| AT-11 | Load authorised comparison source | Matching passage and source name are shown | Critical |
| AT-12 | Review or dismiss a finding | Decision appears in downloaded audit | Critical |
| AT-13 | Analyse Arabic or mixed-script text | Joiners are preserved and mixing is contextual | Critical |
| AT-14 | Batch 2 TXT files | Both results appear and JSON downloads | High |
| AT-15 | Attempt file above configured limit | Operation is rejected without a crash | Critical |
| AT-16 | Stop application | Local server stops and interface becomes unavailable | Critical |

## Approval

- Tester:
- Version:
- Platform:
- Date:
- Critical failures:
- Decision: Approve / Reject / Retest
