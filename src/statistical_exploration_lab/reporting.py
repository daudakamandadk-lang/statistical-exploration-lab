"""A local, offline report window with explicit counts and escaped input labels."""

import html
import json
from pathlib import Path


def _display(value):
    if value is None:
        return '—'
    if isinstance(value, float):
        return f'{value:.6g}'
    return str(value)


def _escape(value):
    return html.escape(_display(value), quote=True)


def _table(headings, rows):
    header = ''.join(f'<th>{_escape(value)}</th>' for value in headings)
    body = ''.join('<tr>' + ''.join(f'<td>{_escape(value)}</td>' for value in row) + '</tr>'
                   for row in rows)
    return f'<div class="table-wrap"><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>'


def render_html(report):
    """Render computed evidence, without executing labels or calling external services."""
    sections = []
    numeric_rows = []
    for field, summary in report['numeric_distributions'].items():
        numeric_rows.append([field, summary['usable_count'], summary['missing_count'],
                             summary['nonfinite_count'], summary['mean'], summary['median'],
                             summary['min'], summary['q25'], summary['q75'], summary['max'],
                             summary['std'], summary['reason'] or summary['status']])
    sections.append('<section><h2>Numeric distributions</h2>' + _table(
        ['Field', 'Usable', 'Missing', 'Nonfinite', 'Mean', 'Median', 'Min', 'Q25', 'Q75',
         'Max', 'Sample SD', 'Status / reason'], numeric_rows) + '</section>')
    for field, summary in report['categorical_distributions'].items():
        rows = [[item['value'], item['count'], f"{100 * item['proportion']:.2f}%"]
                for item in summary['categories']]
        bars = ''.join(
            f'<div class="bar-row"><span>{_escape(item["value"])}</span>'
            f'<meter min="0" max="1" value="{item["proportion"]:.8f}"></meter>'
            f'<span>{item["count"]}</span></div>' for item in summary['categories'])
        sections.append(f'<section><h2>Categories: {_escape(field)}</h2>'
                        f'<p>Usable {summary["usable_count"]}; missing {summary["missing_count"]}. '
                        f'Percentages use {_escape(summary["proportion_denominator"])}.</p>'
                        + bars + _table(['Category', 'Count', 'Share'], rows) + '</section>')
    numeric_pairs = []
    for pair in report['numeric_relationships']:
        for method, coefficient in pair['coefficients'].items():
            numeric_pairs.append([pair['left'], pair['right'], method, coefficient,
                                  pair['usable_count'], pair['excluded_count'],
                                  pair['reason'] or pair['status']])
    sections.append('<section><h2>Numeric relationships</h2>'
                    '<p>Coefficients describe linear (Pearson) or rank (Spearman) association. '
                    'Read usable counts and skipped reasons alongside each result.</p>' + _table(
                        ['Left', 'Right', 'Method', 'Coefficient', 'Usable pairs', 'Excluded rows',
                         'Status / reason'], numeric_pairs) + '</section>')
    for pair in report['categorical_relationships']:
        rows = []
        for index, label in enumerate(pair['row_categories']):
            cells = [f'{count} ({percentage:.2f}%)' for count, percentage in zip(
                pair['counts'][index], pair['row_percentages'][index])]
            rows.append([label, *cells])
        sections.append(f'<section><h2>{_escape(pair["left"])} by {_escape(pair["right"])}</h2>'
                        f'<p>Usable pairs {pair["usable_count"]}; excluded rows {pair["excluded_count"]}. '
                        f'Status: {_escape(pair["reason"] or pair["status"])}. '
                        f'Each cell shows count and percentage of {_escape(pair["percentage_denominator"])}.</p>'
                        + _table([pair['left'], *pair['column_categories']], rows) + '</section>')
    for summary in report['group_summaries']:
        rows = []
        for group in summary['groups']:
            stats = group['statistics']
            rows.append([group['value'], group['total_count'], group['usable_count'],
                         group['missing_count'], group['nonfinite_count'], stats['mean'],
                         stats['median'], stats['std'], group['reason'] or group['status']])
        sections.append(f'<section><h2>{_escape(summary["measure"])} by {_escape(summary["group"])}</h2>'
                        f'<p>Rows with missing group: {summary["missing_group_count"]}. '
                        'Counts remain visible when a small group has withheld statistics.</p>'
                        + _table(['Group', 'Rows', 'Usable', 'Missing measure', 'Nonfinite measure',
                                  'Mean', 'Median', 'Sample SD', 'Status / reason'], rows) + '</section>')
    limitations = ''.join(f'<li>{_escape(value)}</li>' for value in report['limitations'])
    config = report['configuration']
    source = report['source']
    evidence = html.escape(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
<title>Statistical Exploration Lab</title><style>
:root{{font-family:system-ui,sans-serif;color:#182738;background:#f0f4f7}}body{{margin:0}}
main{{max-width:1180px;margin:auto;padding:32px 20px}}header{{padding:28px;background:#16364a;color:white;border-radius:16px}}
h1{{font-size:1.8rem}}h2{{font-size:1.2rem}}section{{background:white;margin:20px 0;padding:22px;border-radius:12px}}
.table-wrap{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;text-align:left;font-size:.9rem}}
th,td{{padding:10px;border-bottom:1px solid #dde5eb;white-space:nowrap}}th{{background:#f2f7fa}}
.bar-row{{display:grid;grid-template-columns:minmax(120px,2fr) 3fr 60px;gap:12px;align-items:center;margin:8px 0}}
meter{{width:100%;height:18px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.8rem}}
li{{margin:8px 0}}small{{color:#d6e9f1}}details{{background:white;padding:20px;border-radius:12px}}
</style></head><body><main><header><small>DESCRIPTIVE EXPLORATION · VERSION 0.1</small>
<h1>{_escape(report['question'])}</h1><p>{report['rows']} rows · {_escape(config['observation']['grain'])}
· unit: {_escape(config['observation']['unit'])}</p>
<p>Source: {_escape(source.get('name', source['kind']))} · {_escape(source['kind'])}</p></header>
<section><h2>Read this first</h2><p>{_escape(report['missingness'])}.</p><ul>{limitations}</ul>
<p>Generated: {_escape(report['generated_at'])}. The full configuration, source fingerprint,
exclusion counts and runtime versions are in the evidence below and report.json.</p></section>
{''.join(sections)}<details><summary>Configuration and complete result evidence</summary><pre>{evidence}</pre></details>
</main></body></html>'''


def write_report(report, output):
    """Write a new report directory; never overwrite an existing analysis."""
    encoded = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
    window = render_html(report)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    owned_files = []
    try:
        for name, content in [('report.json', encoded), ('report.html', window)]:
            path = output / name
            with path.open('x', encoding='utf-8') as handle:
                owned_files.append(path)
                handle.write(content)
    except BaseException:
        # These are the two newly created files, never a pre-existing report.
        for path in owned_files:
            path.unlink(missing_ok=True)
        try:
            output.rmdir()
        except OSError:
            pass
        raise
    return output / 'report.html'
