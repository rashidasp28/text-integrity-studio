const source = document.querySelector('#source');
const output = document.querySelector('#output');
const status = document.querySelector('#status');
const table = document.querySelector('#findings');
const body = table.querySelector('tbody');
const empty = document.querySelector('#empty');
let lastResult = null;
let lastIntegrityResult = null;
let lastPayloadResult = null;
const profileRules = {
  safe: ['remove_hidden', 'convert_nbsp', 'normalize_unusual_spaces', 'remove_trailing_whitespace'],
  publishing: ['remove_hidden', 'convert_nbsp', 'normalize_unusual_spaces', 'remove_trailing_whitespace', 'normalize_dashes', 'normalize_quotes', 'convert_ellipsis']
};

source.addEventListener('input', () => {
  document.querySelector('#characters').textContent = `${source.value.length} characters`;
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
    })
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Processing failed.');
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

document.querySelector('#review-integrity').addEventListener('click', async () => {
  try {
    lastIntegrityResult = await request('/api/integrity');
    const metrics = document.querySelector('#metrics');
    metrics.replaceChildren();
    const labels = {
      citations_detected: 'Citations detected',
      references_detected: 'References detected',
      matched_references: 'Matched references',
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
      for (const value of [finding.category, finding.severity, finding.message, finding.evidence, finding.offset]) {
        const cell = document.createElement('td');
        cell.textContent = value;
        row.appendChild(cell);
      }
      integrityBody.appendChild(row);
    }
    integrityTable.hidden = lastIntegrityResult.findings.length === 0;
    document.querySelector('#integrity-count').textContent = `${lastIntegrityResult.findings.length} findings`;
    status.textContent = lastIntegrityResult.findings.length
      ? 'Review the evidence before revising your document.'
      : 'No citation or attribution issues were identified by the local checks.';
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
  document.querySelector('#payloads').hidden = true;
  document.querySelector('#payloads tbody').replaceChildren();
  document.querySelector('#inventory tbody').replaceChildren();
  document.querySelector('#payload-count').textContent = 'Not inspected';
});
