---
name: static-analysis
description: Static analysis toolkit with CodeQL, Semgrep, and SARIF parsing for security vulnerability detection. Use for security scans, pattern-based bug detection, and CI/CD integration.
---

# Static Analysis

A comprehensive static analysis toolkit with CodeQL, Semgrep, and SARIF parsing for security vulnerability detection.

Based on the Trail of Bits Testing Handbook:
- [CodeQL Testing Handbook](https://appsec.guide/docs/static-analysis/codeql/)
- [Semgrep Testing Handbook](https://appsec.guide/docs/static-analysis/semgrep/)

## When to Use

- Perform security vulnerability detection on codebases
- Run CodeQL for interprocedural taint tracking and data flow analysis
- Use Semgrep for fast pattern-based bug detection
- Parse SARIF output from security scanners
- Set up static analysis in CI/CD pipelines
- Aggregate and deduplicate findings from multiple tools

## CodeQL

Deep security analysis with taint tracking and data flow.

### Create Database
```bash
# Python
codeql database create db --language=python --source-root=.

# JavaScript/TypeScript
codeql database create db --language=javascript --source-root=.
```

### Run Security Queries
```bash
# Run all security queries
codeql database analyze db \
  --format=sarif-latest \
  --output=results.sarif \
  codeql/python-queries:codeql-suites/python-security-extended.qls
```

### Custom Query Example
```ql
/**
 * @name SQL injection
 * @kind path-problem
 */
import python
import semmle.python.security.dataflow.SqlInjectionQuery

from SqlInjectionConfiguration config, DataFlow::PathNode source, DataFlow::PathNode sink
where config.hasFlowPath(source, sink)
select sink.getNode(), source, sink, "SQL injection from $@.", source.getNode(), "user input"
```

## Semgrep

Fast pattern-based security scanning.

### Quick Scans
```bash
# OWASP Top 10
semgrep --config=p/owasp-top-ten .

# Python security
semgrep --config=p/python .

# All security rules
semgrep --config=p/security-audit .
```

### Custom Rule Example
```yaml
rules:
  - id: hardcoded-password
    patterns:
      - pattern: password = "..."
      - pattern-not: password = ""
    message: Hardcoded password detected
    severity: ERROR
    languages: [python]
```

### Taint Mode
```yaml
rules:
  - id: sql-injection
    mode: taint
    pattern-sources:
      - pattern: request.args.get(...)
    pattern-sinks:
      - pattern: cursor.execute($QUERY, ...)
    message: SQL injection vulnerability
    severity: ERROR
    languages: [python]
```

## SARIF Parsing

Parse results from static analysis tools.

### Quick Analysis with jq
```bash
# Count total results
jq '.runs[].results | length' results.sarif

# Get all rule IDs
jq '.runs[].results[].ruleId' results.sarif

# Get high severity findings
jq '.runs[].results[] | select(.level == "error")' results.sarif
```

### Python Processing
```python
import json

with open('results.sarif') as f:
    sarif = json.load(f)

for run in sarif['runs']:
    for result in run['results']:
        print(f"{result['ruleId']}: {result['message']['text']}")
        for loc in result.get('locations', []):
            uri = loc['physicalLocation']['artifactLocation']['uri']
            line = loc['physicalLocation']['region']['startLine']
            print(f"  {uri}:{line}")
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Semgrep
  uses: returntocorp/semgrep-action@v1
  with:
    config: p/security-audit

- name: Run CodeQL
  uses: github/codeql-action/analyze@v2
```

## Best Practices

1. **Run both tools** - CodeQL for deep analysis, Semgrep for speed
2. **Custom rules** - Add project-specific patterns
3. **Baseline scanning** - Track new vs existing issues
4. **SARIF aggregation** - Combine results from multiple tools
5. **CI blocking** - Block PRs on high-severity findings
