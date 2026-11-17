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
    header = ''.join(f'<th scope="col">{_escape(value)}</th>' for value in headings)
    body = ''.join('<tr>' + ''.join(f'<td>{_escape(value)}</td>' for value in row) + '</tr>'
                   for row in rows)
    return f'<div class="table-wrap"><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>'


def _status(result):
    reason = result.get('reason')
    return f'{result["status"]}: {reason}' if reason else result['status']


def _coefficient(pair, method, requested_methods):
    if method not in requested_methods:
        return 'Not requested'
    value = pair['coefficients'].get(method)
    if value is None:
        return f'Skipped: {pair.get("reason") or "unavailable"}'
    return value


def _coefficient_color(value):
    """Use sign and magnitude for color only; do not classify associations."""
    neutral = (247, 250, 252)
    endpoint = (181, 219, 234) if value >= 0 else (246, 201, 168)
    weight = min(abs(value), 1.0)
    channels = [round(start + (end - start) * weight)
                for start, end in zip(neutral, endpoint)]
    return f'rgb({channels[0]},{channels[1]},{channels[2]})'


def _heatmap(report, method):
    """Display selected evidence symmetrically; never calculate extra pairs."""
    fields = report['configuration']['fields']['numeric']
    pairs = {frozenset((pair['left'], pair['right'])): pair
             for pair in report['numeric_relationships']}
    header = '<th scope="col">Field</th>' + ''.join(
        f'<th scope="col">{_escape(field)}</th>' for field in fields)
    rows = []
    for left in fields:
        cells = []
        for right in fields:
            style = ''
            if left == right:
                text = 'Same field'
                state = 'same-field'
                note = 'Same field; no coefficient calculated'
            elif frozenset((left, right)) not in pairs:
                text = 'Not requested'
                state = 'not-requested'
                note = 'Not requested; this pair was not selected'
            else:
                pair = pairs[frozenset((left, right))]
                value = pair['coefficients'].get(method)
                note = (f'Usable pairs {pair["usable_count"]} of {pair["total_count"]}; '
                        f'excluded rows {pair["excluded_count"]}; status {_status(pair)}')
                if value is None:
                    text = f'Skipped: {pair.get("reason") or "unavailable"}'
                    state = 'skipped'
                else:
                    text = _display(value)
                    state = 'coefficient'
                    style = f' style="background:{_coefficient_color(value)}"'
            description = f'{left} / {right}, {method.title()}: {text}. {note}'
            cells.append(f'<td class="matrix-{state}" data-state="{state}"{style} '
                         f'title="{_escape(note)}" aria-label="{_escape(description)}">'
                         f'{_escape(text)}</td>')
        rows.append(f'<tr><th scope="row">{_escape(left)}</th>{"".join(cells)}</tr>')
    return (f'<h3>{_escape(method.title())}</h3><div class="table-wrap">'
            f'<table class="heatmap"><caption>{_escape(method.title())} coefficients for '
            'selected pairs. Each selected pair is mirrored; counts and status are '
            'available on its cells.</caption>'
            f'<thead><tr>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def _numeric_relationships(report, include_heatmaps):
    methods = report['configuration']['relationships']['numeric_methods']
    pairs = report['numeric_relationships']
    content = ('<section id="numeric-relationships"><h2>Numeric relationships</h2>'
               '<p>Pearson describes linear association; Spearman describes monotonic '
               'association using average ranks for ties. Coefficients range from '
               '−1 to +1. These are not significance tests or causal findings.</p>')
    if not pairs:
        content += '<p class="empty-state">No numeric pairs selected; no correlations calculated.</p>'
    if include_heatmaps and report['configuration']['fields']['numeric']:
        content += ('<details class="coefficient-maps" open><summary>Coefficient maps '
                    '(selected pairs only)</summary><p>Color shows coefficient sign and '
                    'magnitude, not statistical significance. “Not requested” means '
                    'that pair was not selected. “Skipped” means selected but unavailable. '
                    'The diagonal is not calculated. Scroll wide maps horizontally.</p>'
                    '<div class="coefficient-legend" aria-label="Coefficient color scale: '
                    'negative orange, zero neutral, positive blue">'
                    '<span>−1</span><span class="color-scale"></span><span>+1</span></div>'
                    + ''.join(_heatmap(report, method) for method in methods) + '</details>')
    if pairs:
        rows = [[pair['left'], pair['right'],
                 _coefficient(pair, 'pearson', methods),
                 _coefficient(pair, 'spearman', methods), pair['total_count'],
                 pair['usable_count'], pair['excluded_count'], _status(pair)]
                for pair in pairs]
        table = _table(['Left', 'Right', 'Pearson', 'Spearman', 'Total rows',
                        'Usable pairs', 'Excluded rows', 'Status / reason'], rows)
        if len(pairs) > 12:
            table = (f'<details><summary>Exact selected-pair results ({len(pairs)} pairs)</summary>'
                     + table + '</details>')
        content += table
    return (content + '<p>Read usable counts and skipped reasons for each pair. '
            'An unavailable coefficient is not zero; different pairs may use different rows.</p></section>')


def render_html(report, include_heatmaps=True):
    """Render computed evidence, without executing labels or calling external services."""
    sections = []
    config = report['configuration']
    numeric_rows = []
    for field, summary in report['numeric_distributions'].items():
        numeric_rows.append([field, summary['usable_count'], summary['missing_count'],
                             summary['nonfinite_count'], summary['mean'], summary['median'],
                             summary['min'], summary['q25'], summary['q75'], summary['max'],
                             summary['std'], summary['reason'] or summary['status']])
    numeric_distribution = ('<section id="numeric-distributions"><h2>Numeric distributions</h2>'
        + (f'<details><summary>Field summaries ({len(numeric_rows)} numeric fields)</summary>' + _table(
        ['Field', 'Usable', 'Missing', 'Nonfinite', 'Mean', 'Median', 'Min', 'Q25', 'Q75',
         'Max', 'Sample SD', 'Status / reason'], numeric_rows) + '</details>' if numeric_rows else
           '<p class="empty-state">No numeric fields declared.</p>') + '</section>')
    categories = []
    for field, summary in report['categorical_distributions'].items():
        rows = [[item['value'], item['count'], f"{100 * item['proportion']:.2f}%"]
                for item in summary['categories']]
        bars = ''.join(
            f'<div class="bar-row"><span>{_escape(item["value"])}</span>'
            f'<meter min="0" max="1" value="{item["proportion"]:.8f}"></meter>'
            f'<span>{item["count"]}</span></div>' for item in summary['categories'])
        categories.append(f'<details><summary>Categories: {_escape(field)}</summary>'
                        f'<p>Usable {summary["usable_count"]}; missing {summary["missing_count"]}. '
                        f'Status: {_escape(_status(summary))}. '
                        f'Percentages use {_escape(summary["proportion_denominator"])}.</p>'
                        + (bars + _table(['Category', 'Count', 'Share'], rows) if rows else
                           '<p class="empty-state">No usable category values.</p>') + '</details>')
    sections.append(_numeric_relationships(report, include_heatmaps))
    categorical_pairs = []
    for pair in report['categorical_relationships']:
        rows = []
        for index, label in enumerate(pair['row_categories']):
            cells = [f'{count} ({percentage:.2f}%)' for count, percentage in zip(
                pair['counts'][index], pair['row_percentages'][index])]
            rows.append([label, *cells])
        categorical_pairs.append(f'<h3>{_escape(pair["left"])} by {_escape(pair["right"])}</h3>'
                        f'<p>Usable pairs {pair["usable_count"]}; excluded rows {pair["excluded_count"]}. '
                        f'Status: {_escape(_status(pair))}. '
                        f'Each cell shows count and percentage of {_escape(pair["percentage_denominator"])}.</p>'
                        + (_table([pair['left'], *pair['column_categories']], rows) if rows else
                           '<p class="empty-state">No complete category pairs.</p>'))
    sections.append('<section id="categorical-relationships"><h2>Categorical relationships</h2>'
                    + (''.join(categorical_pairs) if categorical_pairs else
                       '<p class="empty-state">No categorical pairs selected.</p>') + '</section>')
    group_summaries = []
    for summary in report['group_summaries']:
        rows = []
        for group in summary['groups']:
            stats = group['statistics']
            rows.append([group['value'], group['total_count'], group['usable_count'],
                         group['missing_count'], group['nonfinite_count'], stats['mean'],
                         stats['median'], stats['std'], _status(group)])
        group_summaries.append(f'<h3>{_escape(summary["measure"])} by {_escape(summary["group"])}</h3>'
                        f'<p>Status: {_escape(_status(summary))}. '
                        f'Rows with missing group: {summary["missing_group_count"]}. '
                        'Counts remain visible when a small group has withheld statistics.</p>'
                        + (_table(['Group', 'Rows', 'Usable', 'Missing measure', 'Nonfinite measure',
                                   'Mean', 'Median', 'Sample SD', 'Status / reason'], rows) if rows else
                           '<p class="empty-state">No groups available.</p>'))
    sections.append('<section id="group-summaries"><h2>Numeric summaries by group</h2>'
                    + (''.join(group_summaries) if group_summaries else
                       '<p class="empty-state">No group summaries selected.</p>') + '</section>')
    sections.append(numeric_distribution)
    sections.append('<section id="categorical-distributions"><h2>Categorical distributions</h2>'
                    + (''.join(categories) if categories else
                       '<p class="empty-state">No categorical fields declared.</p>') + '</section>')
    limitations = ''.join(f'<li>{_escape(value)}</li>' for value in report['limitations'])
    source = report['source']
    numeric_count = len(config['fields']['numeric'])
    possible_pairs = numeric_count * (numeric_count - 1) // 2
    selected_pairs = len(config['relationships']['numeric_pairs'])
    skipped_pairs = sum(pair['status'] == 'skipped' for pair in report['numeric_relationships'])
    methods = ', '.join(method.title() for method in config['relationships']['numeric_methods'])
    evidence = html.escape(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
<title>Statistical Exploration Lab</title><style>
:root{{font-family:system-ui,sans-serif;color:#182738;background:#f0f4f7}}body{{margin:0}}
*,*::before,*::after{{box-sizing:border-box}}main{{width:100%;min-width:0;max-width:1220px;margin:auto;padding:32px 20px}}
header{{padding:28px;background:#16364a;color:white;border-radius:16px}}header,p,h1,h2,h3{{overflow-wrap:anywhere}}
h1{{font-size:1.8rem}}h2{{font-size:1.2rem}}section{{background:white;margin:20px 0;padding:22px;border-radius:12px}}
h3{{font-size:1rem;margin-top:24px}}p{{line-height:1.55}}section,details{{scroll-margin-top:20px}}
nav{{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0}}nav a{{color:#16364a;background:white;padding:10px 14px;border-radius:8px}}
.table-wrap{{max-width:100%;overflow-x:auto}}table{{border-collapse:collapse;width:100%;text-align:left;font-size:.9rem}}
th,td{{padding:10px;border-bottom:1px solid #dde5eb;white-space:nowrap}}th{{background:#f2f7fa}}
.bar-row{{display:grid;grid-template-columns:minmax(120px,2fr) 3fr 60px;gap:12px;align-items:center;margin:8px 0}}
meter{{width:100%;height:18px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.8rem}}
li{{margin:8px 0}}small{{color:#d6e9f1}}details{{background:#f7fafc;padding:16px;border-radius:8px;margin:12px 0}}
summary{{cursor:pointer;font-weight:600}}details[open]>summary{{margin-bottom:14px}}.empty-state{{color:#526371}}
.heatmap{{font-size:.78rem;width:max-content;min-width:100%}}
.heatmap td{{text-align:center;white-space:normal;overflow-wrap:anywhere;min-width:76px;max-width:120px;padding:8px}}
.heatmap th{{white-space:nowrap;min-width:96px}}
.heatmap tbody th,.heatmap thead th:first-child{{position:sticky;left:0;z-index:1;min-width:112px;background:#f2f7fa;border-right:1px solid #dde5eb}}
caption{{text-align:left;margin:10px 0;color:#526371}}
.matrix-same-field{{background:#e4eaf0;color:#526371}}.matrix-not-requested{{background:#eef1f4;color:#526371}}
.matrix-skipped{{background:#fff1cb;color:#624b16}}.coefficient-legend{{display:flex;align-items:center;gap:10px;max-width:300px}}
.color-scale{{height:16px;flex:1;background:linear-gradient(to right,#f6c9a8,#f7fafc,#b5dbea);border:1px solid #dde5eb}}
</style></head><body><main><header><small>DESCRIPTIVE EXPLORATION · VERSION 0.1</small>
<h1>{_escape(report['question'])}</h1><p>{report['rows']} rows · {_escape(config['observation']['grain'])}
· unit: {_escape(config['observation']['unit'])}</p>
<p>Source: {_escape(source.get('name', source['kind']))} · {_escape(source['kind'])}</p></header>
<nav aria-label="Report sections"><a href="#relationship-overview">Overview</a>
<a href="#numeric-relationships">Numeric relationships</a><a href="#categorical-relationships">Categorical relationships</a>
<a href="#group-summaries">Group summaries</a><a href="#numeric-distributions">Numeric distributions</a>
<a href="#categorical-distributions">Categories</a><a href="#evidence">Complete evidence</a></nav>
<section><h2>Read this first</h2><p>{_escape(report['missingness'])}.</p><ul>{limitations}</ul>
<p>Generated: {_escape(report['generated_at'])}. The full configuration, source fingerprint,
exclusion counts and runtime versions are in the evidence below and report.json.</p></section>
<section id="relationship-overview"><h2>Relationship overview</h2>
<p>{numeric_count} declared numeric fields; {selected_pairs} selected numeric pairs out of {possible_pairs} possible unique pairs.
Only selected pairs were investigated; other pairs were not requested. The lab does not automatically search every pair.</p>
<p>Requested numeric methods: {_escape(methods)}. Selected pairs marked skipped: {skipped_pairs}.
Selected categorical pairs: {len(config['relationships']['categorical_pairs'])};
selected group summaries: {len(config['relationships']['group_summaries'])}.</p>
<p>Compare coefficients with counts and the stated question. Linear and rank associations can differ;
neither establishes causation or predictive reliability.</p></section>
{''.join(sections)}<details id="evidence"><summary>Configuration and complete result evidence</summary><pre>{evidence}</pre></details>
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
