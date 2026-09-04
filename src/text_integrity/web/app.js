const source = document.querySelector('#source');
const output = document.querySelector('#output');
const status = document.querySelector('#status');
const table = document.querySelector('#findings');
const body = table.querySelector('tbody');
const empty = document.querySelector('#empty');
let lastResult = null;

source.addEventListener('input', () => {
  document.querySelector('#characters').textContent = `${source.value.length} characters`;
});

async function request(path) {
  status.textContent = '';
  const response = await fetch(path, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: source.value, profile: document.querySelector('#profile').value})
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Processing failed.');
  return result;
}

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
    document.querySelector('#change-count').textContent = `${lastResult.edits.length} rule changes`;
  } catch (error) { status.textContent = error.message; }
});

document.querySelector('#copy').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(output.value); status.textContent = 'Cleaned text copied.'; }
  catch { status.textContent = 'Clipboard permission was unavailable.'; }
});

document.querySelector('#download').addEventListener('click', () => {
  if (!lastResult) { status.textContent = 'Clean the text before downloading an audit.'; return; }
  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([JSON.stringify(lastResult, null, 2)], {type: 'application/json'}));
  link.download = 'text-integrity-audit.json';
  link.click();
  URL.revokeObjectURL(link.href);
});
