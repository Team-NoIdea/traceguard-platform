import type { SecurityFinding } from '@/types'

import type { FindingRecord } from './types'

const hoursAgo = (h: number) => new Date(Date.now() - h * 60 * 60 * 1000).toISOString()
const minutesAgo = (m: number) => new Date(Date.now() - m * 60 * 1000).toISOString()

const sqlInjection: SecurityFinding = {
  finding_id: 'TG-001',
  title: 'SQL Injection',
  type: 'SQL_INJECTION',
  severity: 'HIGH',
  cwe: ['CWE-89'],
  location: { file: 'app/routes/users.py', line: 42, function: 'get_user' },
  confidence: 0.92,
  static_evidence: [
    {
      tool: 'Semgrep',
      rule_id: 'python.sql-injection',
      location: { file: 'app/routes/users.py', line: 42, function: 'get_user' },
      evidence: {
        source: 'request.args',
        sink: 'cursor.execute()',
        flow: ['request.args', 'user_id', 'query', 'cursor.execute()'],
        description: 'User-controlled query parameter flows unsanitized into a raw SQL execution call.',
      },
    },
  ],
  runtime_evidence: [
    {
      endpoint: '/api/user',
      method: 'GET',
      baseline_status: 200,
      mutated_status: 500,
      evidence: "Unhandled exception thrown when the id parameter contained a single quote",
      function: 'get_user',
      type: 'SERVER_ERROR',
    },
  ],
  source_tools: ['Semgrep', 'Runtime Fuzzer'],
  status: 'OPEN',
  explanation:
    "Static analysis traced unsanitized input from request.args through to a raw SQL execution call. Runtime testing independently confirmed the vulnerable path: mutating the id parameter with a single quote triggered a server-side exception at the same function, corroborating the static finding with live evidence.",
  remediation:
    '- query = f"SELECT * FROM users WHERE id={user_id}"\n+ query = "SELECT * FROM users WHERE id=?"\n\nUse parameterized queries to prevent user-controlled input from being interpreted as SQL syntax.',
}

const commandInjection: SecurityFinding = {
  finding_id: 'TG-002',
  title: 'Command Injection',
  type: 'COMMAND_INJECTION',
  severity: 'CRITICAL',
  cwe: ['CWE-78'],
  location: { file: 'api/exec.py', line: 91, function: 'run_export' },
  confidence: 0.87,
  static_evidence: [
    {
      tool: 'Semgrep',
      rule_id: 'python.lang.security.subprocess-shell-true',
      location: { file: 'api/exec.py', line: 91, function: 'run_export' },
      evidence: {
        source: "request.form['filename']",
        sink: 'subprocess.run(..., shell=True)',
        flow: ["request.form['filename']", 'filename', 'cmd', 'subprocess.run()'],
        description: 'Shell metacharacters in user input are not escaped before reaching a shell-executed subprocess.',
      },
    },
  ],
  runtime_evidence: [
    {
      endpoint: '/api/export',
      method: 'POST',
      baseline_status: 200,
      mutated_status: 500,
      evidence: 'Command-chaining payload in filename produced unexpected process output',
      function: 'run_export',
      type: 'SERVER_ERROR',
    },
  ],
  source_tools: ['Semgrep', 'Runtime Fuzzer'],
  status: 'OPEN',
  explanation:
    'The export endpoint builds a shell command using an unsanitized filename parameter. Runtime testing confirmed that shell metacharacters in that parameter change process behavior, matching the static analysis finding at the same function.',
  remediation:
    '- subprocess.run(f"export_tool {filename}", shell=True)\n+ subprocess.run(["export_tool", filename], shell=False)\n\nAvoid shell=True with unsanitized input — pass arguments as a list so the shell never interprets metacharacters.',
}

const unsafeEval: SecurityFinding = {
  finding_id: 'TG-003',
  title: 'Unsafe eval',
  type: 'CODE_INJECTION',
  severity: 'HIGH',
  cwe: ['CWE-95'],
  location: { file: 'utils/parser.py', line: 18, function: 'evaluate_expression' },
  confidence: 0.71,
  static_evidence: [
    {
      tool: 'CodeQL',
      rule_id: 'py/eval-injection',
      location: { file: 'utils/parser.py', line: 18, function: 'evaluate_expression' },
      evidence: {
        source: "request.json['expr']",
        sink: 'eval()',
        flow: ["request.json['expr']", 'expression', 'eval()'],
        description: 'A user-supplied expression string is passed directly to eval().',
      },
    },
  ],
  runtime_evidence: [],
  source_tools: ['CodeQL'],
  status: 'OPEN',
  explanation:
    'Static analysis found a direct path from request input to eval(). No runtime confirmation is attached yet, which is reflected in a lower confidence score than the correlated findings above.',
  remediation:
    '- result = eval(expression)\n+ result = ast.literal_eval(expression)\n\nReplace eval() with ast.literal_eval() (or a proper expression parser) so arbitrary code cannot be executed.',
}

const pathTraversal: SecurityFinding = {
  finding_id: 'TG-004',
  title: 'Path Traversal',
  type: 'PATH_TRAVERSAL',
  severity: 'MEDIUM',
  cwe: ['CWE-22'],
  location: { file: 'app/files.py', line: 27, function: 'download_file' },
  confidence: 0.58,
  static_evidence: [
    {
      tool: 'Semgrep',
      rule_id: 'python.lang.security.path-traversal-open',
      location: { file: 'app/files.py', line: 27, function: 'download_file' },
      evidence: {
        source: "request.args['filename']",
        sink: 'open()',
        flow: ["request.args['filename']", 'path', 'open()'],
        description: 'A filename query parameter is joined into a filesystem path without normalization.',
      },
    },
  ],
  runtime_evidence: [],
  source_tools: ['Semgrep'],
  status: 'CONFIRMED',
  explanation:
    'The download endpoint resolves a file path from user input without checking that the result stays within the intended directory. A team member has manually confirmed the path is reachable.',
  remediation:
    '- path = os.path.join(UPLOAD_DIR, filename)\n+ path = safe_join(UPLOAD_DIR, filename)\n\nValidate that the resolved path stays within the intended directory before opening it (e.g. werkzeug\'s safe_join).',
}

const xss: SecurityFinding = {
  finding_id: 'TG-005',
  title: 'Reflected XSS',
  type: 'XSS',
  severity: 'LOW',
  cwe: ['CWE-79'],
  location: { file: 'templates/render.py', line: 55, function: 'render_comment' },
  confidence: 0.64,
  static_evidence: [
    {
      tool: 'Semgrep',
      rule_id: 'python.django.security.audit.xss.mark-safe',
      location: { file: 'templates/render.py', line: 55, function: 'render_comment' },
      evidence: {
        source: 'comment.text',
        sink: 'mark_safe()',
        flow: ['comment.text', 'rendered_html', 'mark_safe()'],
        description: 'Comment text is marked safe and rendered without HTML-escaping.',
      },
    },
  ],
  runtime_evidence: [
    {
      endpoint: '/comments/render',
      method: 'POST',
      baseline_status: 200,
      mutated_status: 200,
      evidence: 'Response body echoed a raw <script> payload without encoding',
      function: 'render_comment',
      type: 'REFLECTED_PAYLOAD',
    },
  ],
  source_tools: ['Semgrep', 'Runtime Fuzzer'],
  status: 'OPEN',
  explanation:
    'A comment field is rendered without escaping. Runtime testing confirmed a script payload is reflected verbatim in the response, though exposure is limited to a low-traffic internal view.',
  remediation:
    '- return mark_safe(comment.text)\n+ return escape(comment.text)\n\nEscape user-controlled content before rendering, or use the template engine\'s autoescaping instead of mark_safe().',
}

const hardcodedSecret: SecurityFinding = {
  finding_id: 'TG-006',
  title: 'Hardcoded Secret',
  type: 'HARDCODED_SECRET',
  severity: 'HIGH',
  cwe: ['CWE-798'],
  location: { file: 'config/settings.py', line: 9 },
  confidence: 0.55,
  static_evidence: [
    {
      tool: 'Gitleaks',
      rule_id: 'generic-api-key',
      location: { file: 'config/settings.py', line: 9 },
      evidence: {
        flow: [],
        description: 'A live-looking API key literal was found committed directly in source.',
      },
    },
  ],
  runtime_evidence: [],
  source_tools: ['Gitleaks'],
  status: 'DISMISSED',
  explanation:
    'A secret-scanning pattern matched an API key literal in a config file. Dismissed after the team confirmed the key had already been rotated and revoked.',
  remediation:
    '- STRIPE_API_KEY = "sk_live_51Hxxxxxxxxxxxxxxxx"\n+ STRIPE_API_KEY = os.environ["STRIPE_API_KEY"]\n\nMove secrets out of source control and load them from environment variables or a secrets manager.',
}

export const mockFindingRecords: FindingRecord[] = [
  { finding: sqlInjection, repository: 'acme/payment-api', branch: 'main', scan_id: 'scan-8f21ac', detected_at: hoursAgo(2) },
  { finding: commandInjection, repository: 'acme/payment-api', branch: 'main', scan_id: 'scan-8f21ac', detected_at: hoursAgo(6) },
  { finding: unsafeEval, repository: 'team-noidea/demo-api', branch: 'develop', scan_id: 'scan-3d9c11', detected_at: hoursAgo(26) },
  { finding: pathTraversal, repository: 'example/flask-app', branch: 'main', scan_id: 'scan-b02e77', detected_at: hoursAgo(74) },
  { finding: xss, repository: 'team-noidea/demo-api', branch: 'develop', scan_id: 'scan-3d9c11', detected_at: minutesAgo(30) },
  { finding: hardcodedSecret, repository: 'acme/payment-api', branch: 'main', scan_id: 'scan-8f21ac', detected_at: hoursAgo(216) },
]
