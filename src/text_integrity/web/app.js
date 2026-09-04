const source = document.querySelector('#source');
const output = document.querySelector('#output');
const status = document.querySelector('#status');
const table = document.querySelector('#findings');
const body = table.querySelector('tbody');
const empty = document.querySelector('#empty');
let lastResult = null;
let lastIntegrityResult = null;
let lastPayloadResult = null;
let lastRewriteAnalysis = null;
let lastRewriteResult = null;
let comparisonSources = [];
const profileRules = {
  safe: ['remove_hidden', 'convert_nbsp', 'normalize_unusual_spaces', 'remove_trailing_whitespace'],
  publishing: ['remove_hidden', 'convert_nbsp', 'normalize_unusual_spaces', 'remove_trailing_whitespace', 'normalize_dashes', 'normalize_quotes', 'convert_ellipsis']
};

source.addEventListener('input', () => {
  document.querySelector('#characters').textContent = `${source.value.length} characters`;
  if (lastIntegrityResult) {
    lastIntegrityResult = null;
    document.querySelector('#integrity-count').textContent = 'Review expired';
    document.querySelector('#download-integrity').disabled = true;
  }
  if (lastRewriteAnalysis) {
    lastRewriteAnalysis = null;
    lastRewriteResult = null;
    document.querySelector('#rewrite-suggestions').hidden = true;
    document.querySelector('#rewrite-suggestions tbody').replaceChildren();
    document.querySelector('#rewrite-count').textContent = 'Analysis expired';
    document.querySelector('#protected-summary').textContent = 'Text changed. Run Analyse style again.';
    document.querySelector('#protected-details').hidden = true;
    document.querySelector('#protected-values tbody').replaceChildren();
    document.querySelector('#rewrite-empty').hidden = true;
    document.querySelector('#apply-rewrite').disabled = true;
    document.querySelector('#download-rewrite').disabled = true;
  }
});

async function request(path) {
  status.textContent = '';
  const response = await fetch(path, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      text: source.value,
      profile: document.querySelector('#profile').value === 'custom' ? null : document.querySelector('#profile').value,
      options: [...document.querySelectorAll('#rules input:checked')].map(input => input.value)
      ,comparison_sources: comparisonSources
      ,exclusions: [...document.querySelectorAll('.integrity-exclusion:checked')].map(input => input.value)
    })
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Processing failed.');
  return result;
}

async function rewriteRequest(path, acceptedIds = []) {
  status.textContent = '';
  const response = await fetch(path, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: source.value, backend: 'deterministic', accepted_ids: acceptedIds})
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Rewrite processing failed.');
  return result;
}

function renderDiff(segments) {
  const original = document.querySelector('#diff-original');
  const cleaned = document.querySelector('#diff-output');
  original.replaceChildren();
  cleaned.replaceChildren();
  for (const segment of segments) {
    const oldNode = document.createElement(segment.operation === 'delete' || segment.operation === 'replace' ? 'mark' : 'span');
    oldNode.className = segment.operation === 'delete' || segment.operation === 'replace' ? 'delete' : '';
    oldNode.textContent = segment.original;
    original.appendChild(oldNode);
    const newNode = document.createElement(segment.operation === 'insert' || segment.operation === 'replace' ? 'mark' : 'span');
    newNode.className = segment.operation === 'insert' || segment.operation === 'replace' ? 'insert' : '';
    newNode.textContent = segment.output;
    cleaned.appendChild(newNode);
  }
}

function showChanges(edits) {
  const list = document.querySelector('#changes');
  list.replaceChildren();
  if (!edits.length) {
    const item = document.createElement('li');
    item.textContent = 'No changes were needed.';
    list.appendChild(item);
  }
  for (const edit of edits) {
    const item = document.createElement('li');
    item.textContent = `${edit.rule_id}: ${edit.explanation}`;
    list.appendChild(item);
  }
  document.querySelector('#applied-count').textContent = `${edits.length} applied rules`;
}

function download(content, filename, type) {
  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([content], {type}));
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

function syncRules() {
  const profile = document.querySelector('#profile').value;
  const enabled = profileRules[profile] || [];
  for (const input of document.querySelectorAll('#rules input')) {
    if (profile !== 'custom') input.checked = enabled.includes(input.value);
    input.disabled = profile !== 'custom';
  }
}

document.querySelector('#profile').addEventListener('change', syncRules);
syncRules();

document.querySelector('#file-input').addEventListener('change', async event => {
  const file = event.target.files[0];
  if (!file) return;
  if (file.size > 2 * 1024 * 1024) { status.textContent = 'File exceeds the 2 MB limit.'; return; }
  source.value = await file.text();
  source.dispatchEvent(new Event('input'));
  status.textContent = `Opened ${file.name}.`;
});

document.querySelector('#corpus-input').addEventListener('change', async event => {
  const files = [...event.target.files];
  const total = files.reduce((sum, file) => sum + file.size, 0);
  if (files.length > 20 || total > 2 * 1024 * 1024) {
    status.textContent = 'The authorised corpus is limited to 20 files and 2 MB.';
    event.target.value = '';
    return;
  }
  comparisonSources = await Promise.all(files.map(async file => ({name: file.name, text: await file.text()})));
  document.querySelector('#corpus-count').textContent = comparisonSources.length
    ? `${comparisonSources.length} authorised file${comparisonSources.length === 1 ? '' : 's'}`
    : 'No comparison files';
  status.textContent = comparisonSources.length ? 'Authorised comparison files loaded locally.' : '';
});

function showFindings(findings) {
  body.replaceChildren();
  for (const finding of findings) {
    const row = document.createElement('tr');
    for (const value of [finding.character, finding.code_point, finding.name, finding.category, finding.action, finding.offset]) {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.appendChild(cell);
    }
    body.appendChild(row);
  }
  document.querySelector('#finding-count').textContent = `${findings.length} findings`;
  empty.hidden = findings.length > 0;
  empty.textContent = 'No unusual characters found.';
  table.hidden = findings.length === 0;
}

document.querySelector('#inspect').addEventListener('click', async () => {
  try { showFindings((await request('/api/inspect')).findings); }
  catch (error) { status.textContent = error.message; }
});

document.querySelector('#clean').addEventListener('click', async () => {
  try {
    lastResult = await request('/api/clean');
    output.value = lastResult.output;
    showFindings(lastResult.findings);
    renderDiff(lastResult.diff);
    showChanges(lastResult.edits);
    document.querySelector('#change-count').textContent = `${lastResult.edits.length} rule changes`;
  } catch (error) { status.textContent = error.message; }
});

function renderRewriteAnalysis(analysis) {
  const rewriteTable = document.querySelector('#rewrite-suggestions');
  const rewriteBody = rewriteTable.querySelector('tbody');
  rewriteBody.replaceChildren();
  for (const suggestion of analysis.suggestions) {
    const row = document.createElement('tr');
    const choose = document.createElement('td');
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.value = suggestion.suggestion_id;
    checkbox.setAttribute('aria-label', `Accept ${suggestion.suggestion_id}`);
    choose.appendChild(checkbox);
    row.appendChild(choose);
    for (const value of [suggestion.original, suggestion.replacement || '(remove)', suggestion.explanation]) {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.appendChild(cell);
    }
    rewriteBody.appendChild(row);
  }
  rewriteTable.hidden = analysis.suggestions.length === 0;
  document.querySelector('#rewrite-count').textContent = `${analysis.suggestions.length} suggestions`;
  const categories = {};
  for (const span of analysis.protected_spans) categories[span.category] = (categories[span.category] || 0) + 1;
  document.querySelector('#protected-summary').textContent = analysis.protected_spans.length
    ? `Protected facts: ${Object.entries(categories).map(([key, value]) => `${value} ${key}`).join(', ')}.`
    : 'No dates, measurements, citations, URLs, emails, numbers or identifiers require protection.';
  const protectedBody = document.querySelector('#protected-values tbody');
  protectedBody.replaceChildren();
  for (const span of analysis.protected_spans) {
    const row = document.createElement('tr');
    for (const value of [span.text, span.category, `${span.start}–${span.end}`]) {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.appendChild(cell);
    }
    protectedBody.appendChild(row);
  }
  document.querySelector('#protected-details').hidden = analysis.protected_spans.length === 0;
  document.querySelector('#rewrite-empty').hidden = analysis.suggestions.length !== 0;
  document.querySelector('#apply-rewrite').disabled = analysis.suggestions.length === 0;
  document.querySelector('#apply-rewrite').title = analysis.suggestions.length
    ? 'Apply the rewrite suggestions selected above.'
    : 'No suggestions are available to apply.';
  document.querySelector('#download-rewrite').disabled = true;
}

document.querySelector('#analyse-rewrite').addEventListener('click', async () => {
  try {
    lastRewriteAnalysis = await rewriteRequest('/api/rewrite/analyse');
    lastRewriteResult = null;
    renderRewriteAnalysis(lastRewriteAnalysis);
    status.textContent = lastRewriteAnalysis.suggestions.length
      ? 'Select the style suggestions you want to accept.'
      : 'No deterministic style refinements were identified.';
  } catch (error) { status.textContent = error.message; }
});

document.querySelector('#apply-rewrite').addEventListener('click', async () => {
  try {
    const acceptedIds = [...document.querySelectorAll('#rewrite-suggestions input:checked')].map(input => input.value);
    lastRewriteResult = await rewriteRequest('/api/rewrite/apply', acceptedIds);
    output.value = lastRewriteResult.output;
    renderDiff(lastRewriteResult.diff);
    document.querySelector('#change-count').textContent = `${lastRewriteResult.accepted_suggestions.length} accepted revisions`;
    document.querySelector('#download-rewrite').disabled = false;
    status.textContent = lastRewriteResult.facts_preserved
      ? 'Accepted revisions applied. All protected facts were preserved.'
      : 'Rewrite validation failed.';
  } catch (error) { status.textContent = error.message; }
});

document.querySelector('#download-rewrite').addEventListener('click', () => {
  if (!lastRewriteResult) { status.textContent = 'Apply rewrite suggestions before downloading the audit.'; return; }
  download(JSON.stringify(lastRewriteResult, null, 2), 'text-integrity-rewrite-audit.json', 'application/json');
});

document.querySelector('#review-integrity').addEventListener('click', async () => {
  try {
    lastIntegrityResult = await request('/api/integrity');
    const metrics = document.querySelector('#metrics');
    metrics.replaceChildren();
    const labels = {
      citations_detected: 'Citations detected',
      references_detected: 'References detected',
      matched_references: 'Matched references',
      authorised_sources: 'Authorised sources',
      matched_passages: 'Matched passages',
      matched_text_coverage_percent: 'Local match coverage %',
      excluded_findings: 'Excluded findings',
      unresolved_findings: 'Unresolved findings'
    };
    for (const [key, value] of Object.entries(lastIntegrityResult.metrics)) {
      const item = document.createElement('div');
      item.className = 'metric';
      const number = document.createElement('strong');
      number.textContent = value;
      const label = document.createElement('span');
      label.textContent = labels[key] || key;
      item.append(number, label);
      metrics.appendChild(item);
    }
    const integrityTable = document.querySelector('#integrity-findings');
    const integrityBody = integrityTable.querySelector('tbody');
    integrityBody.replaceChildren();
    for (const finding of lastIntegrityResult.findings) {
      const row = document.createElement('tr');
      for (const value of [finding.category, finding.severity, finding.message, finding.evidence, finding.source]) {
        const cell = document.createElement('td');
        cell.textContent = value;
        row.appendChild(cell);
      }
      const decisionCell = document.createElement('td');
      const decision = document.createElement('select');
      decision.dataset.findingId = finding.finding_id;
      for (const value of ['unresolved', 'reviewed', 'dismissed']) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = value[0].toUpperCase() + value.slice(1);
        decision.appendChild(option);
      }
      decisionCell.appendChild(decision);
      row.appendChild(decisionCell);
      integrityBody.appendChild(row);
    }
    integrityTable.hidden = lastIntegrityResult.findings.length === 0;
    document.querySelector('#integrity-count').textContent = `${lastIntegrityResult.findings.length} findings`;
    document.querySelector('#integrity-limitations').textContent = lastIntegrityResult.limitations.join(' ');
    document.querySelector('#download-integrity').disabled = false;
    status.textContent = lastIntegrityResult.findings.length
      ? 'Review the evidence before revising your document.'
      : 'No citation or attribution issues were identified by the local checks.';
  } catch (error) { status.textContent = error.message; }
});

document.querySelector('#download-integrity').addEventListener('click', async () => {
  if (!lastIntegrityResult) { status.textContent = 'Run the integrity review before downloading an audit.'; return; }
  const decisions = {};
  for (const select of document.querySelectorAll('#integrity-findings select')) decisions[select.dataset.findingId] = select.value;
  try {
    const response = await fetch('/api/integrity/audit', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        text: source.value,
        report: lastIntegrityResult,
        decisions,
        transparency_statement: document.querySelector('#transparency-statement').value
      })
    });
    const audit = await response.json();
    if (!response.ok) throw new Error(audit.error || 'Integrity audit failed.');
    download(JSON.stringify(audit, null, 2), 'text-integrity-review-audit.json', 'application/json');
    status.textContent = 'Integrity review audit downloaded.';
  } catch (error) { status.textContent = error.message; }
});

document.querySelector('#inspect-payloads').addEventListener('click', async () => {
  try {
    lastPayloadResult = await request('/api/payloads');
    const payloadTable = document.querySelector('#payloads');
    const payloadBody = payloadTable.querySelector('tbody');
    payloadBody.replaceChildren();
    for (const payload of lastPayloadResult.payloads) {
      const row = document.createElement('tr');
      for (const value of [payload.codec, `${payload.start}–${payload.end}`, payload.character_count, payload.decoded_text || 'Not decoded', payload.confidence, payload.explanation]) {
        const cell = document.createElement('td');
        cell.textContent = value;
        row.appendChild(cell);
      }
      payloadBody.appendChild(row);
    }
    payloadTable.hidden = lastPayloadResult.payloads.length === 0;
    const inventoryBody = document.querySelector('#inventory tbody');
    inventoryBody.replaceChildren();
    for (const item of lastPayloadResult.inventory) {
      const row = document.createElement('tr');
      for (const value of [item.offset, item.visible, item.code_point, item.name, item.category]) {
        const cell = document.createElement('td');
        cell.textContent = value;
        row.appendChild(cell);
      }
      inventoryBody.appendChild(row);
    }
    document.querySelector('#payload-count').textContent = `${lastPayloadResult.payloads.length} possible payloads`;
    status.textContent = lastPayloadResult.payloads.length
      ? 'Possible encoded data found. Review the codec, decoded text and confidence.'
      : 'No recognised encoded payload was found. Review the raw inventory for individual characters.';
  } catch (error) { status.textContent = error.message; }
});

document.querySelector('#copy').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(output.value); status.textContent = 'Cleaned text copied.'; }
  catch { status.textContent = 'Clipboard permission was unavailable.'; }
});

document.querySelector('#download').addEventListener('click', () => {
  if (!lastResult) { status.textContent = 'Clean the text before downloading an audit.'; return; }
  download(JSON.stringify(lastResult, null, 2), 'text-integrity-audit.json', 'application/json');
});

document.querySelector('#download-text').addEventListener('click', () => {
  if (!lastResult) { status.textContent = 'Clean the text before downloading it.'; return; }
  download(lastResult.output, 'cleaned-text.txt', 'text/plain;charset=utf-8');
});

document.querySelector('#undo').addEventListener('click', () => {
  output.value = source.value;
  lastResult = null;
  lastIntegrityResult = null;
  lastPayloadResult = null;
  lastRewriteAnalysis = null;
  lastRewriteResult = null;
  comparisonSources = [];
  renderDiff([{operation: 'equal', original: source.value, output: source.value}]);
  showChanges([]);
  document.querySelector('#change-count').textContent = '0 changes';
  status.textContent = 'Cleaning preview undone. The original text was not changed.';
});

document.querySelector('#reset').addEventListener('click', () => {
  source.value = '';
  output.value = '';
  lastResult = null;
  source.dispatchEvent(new Event('input'));
  showFindings([]);
  renderDiff([]);
  showChanges([]);
  document.querySelector('#change-count').textContent = '0 changes';
  status.textContent = 'Workspace reset.';
  document.querySelector('#metrics').replaceChildren();
  document.querySelector('#integrity-findings').hidden = true;
  document.querySelector('#integrity-count').textContent = 'Not reviewed';
  document.querySelector('#integrity-limitations').textContent = '';
  document.querySelector('#download-integrity').disabled = true;
  document.querySelector('#transparency-statement').value = '';
  document.querySelector('#corpus-input').value = '';
  document.querySelector('#corpus-count').textContent = 'No comparison files';
  document.querySelector('#payloads').hidden = true;
  document.querySelector('#payloads tbody').replaceChildren();
  document.querySelector('#inventory tbody').replaceChildren();
  document.querySelector('#payload-count').textContent = 'Not inspected';
  document.querySelector('#rewrite-suggestions').hidden = true;
  document.querySelector('#rewrite-suggestions tbody').replaceChildren();
  document.querySelector('#rewrite-count').textContent = 'Not analysed';
  document.querySelector('#protected-summary').textContent = 'No protected facts have been inventoried.';
  document.querySelector('#protected-details').hidden = true;
  document.querySelector('#protected-values tbody').replaceChildren();
  document.querySelector('#rewrite-empty').hidden = true;
  document.querySelector('#apply-rewrite').disabled = true;
  document.querySelector('#download-rewrite').disabled = true;
});
