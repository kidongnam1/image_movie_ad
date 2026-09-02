from __future__ import annotations
import csv, html, json, sqlite3, zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parent
LIB = ROOT / 'AI_PROMPT_LIBRARY'
IDX = LIB / 'indexes'
LOG = LIB / 'logs'
REPORT_DIR = LIB / 'reports'


def load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def read_csv(path: Path):
    if not path.exists():
        return []
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def line(ch='-', n=72):
    print(ch * n)


def collect_report_data():
    dsum = load_json(LOG / 'download_only_summary.json') or {}
    isum = load_json(IDX / 'summary.json') or {}
    clone_status = load_json(LOG / 'clone_status_download_only.json') or []
    prompt_rows = read_csv(IDX / 'prompt_records.csv')
    model_summary_rows = read_csv(IDX / 'model_summary.csv')

    if dsum:
        download = {
            'Selected repos': dsum.get('repos_selected', 0),
            'Success repos': dsum.get('repos_ok', 0),
            'Failed repos': dsum.get('repos_failed', 0),
            'Text-only clone': dsum.get('text_only_clone', False),
            'Media counts': json.dumps(dsum.get('media_counts', {}), ensure_ascii=False),
            'Source kinds': json.dumps(dsum.get('source_kind_counts', {}), ensure_ascii=False),
        }
    elif clone_status:
        ok_status = {'cloned', 'updated', 'ok', 'exists', 'unchanged'}
        ok = sum(1 for s in clone_status if s.get('status') in ok_status)
        download = {
            'Selected repos': len(clone_status),
            'Success repos': ok,
            'Failed repos': len(clone_status) - ok,
            'Text-only clone': '',
            'Media counts': '',
            'Source kinds': '',
        }
    else:
        download = {'Status': 'No download summary found yet.'}

    index = {}
    if isum:
        mapping = [
            ('repos_selected', 'Selected repos'),
            ('repos_downloaded', 'Downloaded repos'),
            ('prompt_files', 'Prompt files'),
            ('raw_records', 'Raw records'),
            ('unique_prompts', 'Unique prompts'),
            ('duplicate_prompt_groups', 'Duplicate groups'),
            ('near_duplicate_review_pairs', 'Near-duplicate review pairs'),
            ('heavy_repo_overlap_pairs', 'Heavy repo overlap pairs'),
        ]
        index = {label: isum.get(key, 0) for key, label in mapping}
    else:
        index = {'Status': 'No index summary found yet.'}

    model_counts = Counter(r.get('model_family', 'unknown') for r in prompt_rows)
    tag_counts = Counter()
    quality_counts = Counter()
    media_counts = Counter()
    for r in prompt_rows:
        media_counts[r.get('media_type', 'unknown')] += 1
        quality_counts[r.get('quality_tier', '?')] += 1
        for t in (r.get('auto_tags') or '').split('|'):
            if t:
                tag_counts[t] += 1

    top_models = model_counts.most_common(30)
    top_tags = tag_counts.most_common(30)
    quality = [(t, quality_counts.get(t, 0)) for t in ['S', 'A', 'B', 'C', 'D', '?'] if quality_counts.get(t, 0)]
    media = media_counts.most_common()

    # If model_summary exists, use richer model rows for spreadsheet detail.
    model_detail = []
    if model_summary_rows:
        for r in model_summary_rows:
            model_detail.append([
                r.get('model_family', ''), r.get('media_type', ''), r.get('unique_prompts', ''),
                r.get('avg_combined_score', ''), r.get('avg_model_fit', ''), r.get('top_combined_score', '')
            ])
    else:
        model_detail = [[m, '', n, '', '', ''] for m, n in top_models]

    return {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'download': download,
        'index': index,
        'top_models': top_models,
        'top_tags': top_tags,
        'quality': quality,
        'media': media,
        'model_detail': model_detail,
        'prompt_count': len(prompt_rows),
    }


def print_console(data):
    print('=' * 72)
    print('AI Prompt Collector v6 - RESULT SUMMARY')
    print('=' * 72)
    print('\n[DOWNLOAD]')
    for k, v in data['download'].items():
        print(f'{k:24}: {v}')
    print('\n[INDEX]')
    for k, v in data['index'].items():
        print(f'{k:24}: {v}')
    if data['top_models']:
        print('\n[TOP MODELS]')
        for model, n in data['top_models'][:15]:
            print(f'{model:28} {n:>8}')
    if data['top_tags']:
        print('\n[TOP TAGS]')
        for tag, n in data['top_tags'][:15]:
            print(f'{tag:28} {n:>8}')
    if data['quality']:
        print('\n[QUALITY TIERS]')
        for tier, n in data['quality']:
            print(f'{tier:>4}: {n}')
    db = IDX / 'prompt_library.sqlite'
    if db.exists():
        try:
            con = sqlite3.connect(db)
            cur = con.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [r[0] for r in cur.fetchall()]
            con.close()
            print('\n[SQLITE]')
            print('Database                :', db)
            print('Tables                  :', ', '.join(tables))
        except Exception as e:
            print('\n[SQLITE] Error:', e)
    print('\n[PATHS]')
    print('Library                 :', LIB)
    print('Indexes                 :', IDX)
    print('Logs                    :', LOG)
    print('Reports                 :', REPORT_DIR)
    print('Dashboard               :', LIB / 'dashboard.html')
    line('=')


def write_html_report(data, path: Path):
    def table_dict(d):
        return ''.join(f'<tr><th>{html.escape(str(k))}</th><td>{html.escape(str(v))}</td></tr>' for k, v in d.items())
    def table_pairs(pairs, h1, h2):
        rows = ''.join(f'<tr><td>{html.escape(str(a))}</td><td class="num">{html.escape(str(b))}</td></tr>' for a, b in pairs)
        return f'<table><thead><tr><th>{h1}</th><th>{h2}</th></tr></thead><tbody>{rows}</tbody></table>'
    css = '''
    body{font-family:Segoe UI,Arial,sans-serif;margin:28px;background:#f6f8fb;color:#1f2937}
    h1{margin-bottom:4px} .sub{color:#64748b;margin-bottom:24px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px}
    .card{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:18px;box-shadow:0 2px 8px rgba(15,23,42,.05)}
    table{border-collapse:collapse;width:100%;background:#fff} th,td{border-bottom:1px solid #e5e7eb;padding:8px 10px;text-align:left}
    th{background:#eaf2f8}.num{text-align:right;font-variant-numeric:tabular-nums}.warn{background:#fff7ed;border-left:4px solid #f59e0b;padding:10px}
    code{background:#eef2f7;padding:2px 4px;border-radius:4px}
    '''
    document = f'''<!doctype html><html><head><meta charset="utf-8"><title>AI Prompt Collector v6 Result Summary</title><style>{css}</style></head><body>
    <h1>AI Prompt Collector v6 — Result Summary</h1><div class="sub">Generated: {html.escape(data['generated_at'])}</div>
    <div class="warn">Near-duplicates are review-only. UNKNOWN license means not verified, not free-use.</div><br>
    <div class="grid">
      <div class="card"><h2>Download</h2><table>{table_dict(data['download'])}</table></div>
      <div class="card"><h2>Index</h2><table>{table_dict(data['index'])}</table></div>
      <div class="card"><h2>Quality tiers</h2>{table_pairs(data['quality'],'Tier','Prompts')}</div>
      <div class="card"><h2>Media</h2>{table_pairs(data['media'],'Media','Prompts')}</div>
    </div><br>
    <div class="grid">
      <div class="card"><h2>Top models</h2>{table_pairs(data['top_models'][:30],'Model','Prompts')}</div>
      <div class="card"><h2>Top tags</h2>{table_pairs(data['top_tags'][:30],'Tag','Prompts')}</div>
    </div>
    </body></html>'''
    path.write_text(document, encoding='utf-8')


# Minimal XLSX writer using only Python standard library.
def _col_letter(n: int) -> str:
    out = ''
    n += 1
    while n:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def _sheet_xml(rows):
    xml_rows = []
    for ri, row in enumerate(rows, 1):
        cells = []
        for ci, value in enumerate(row):
            if value is None:
                continue
            ref = f'{_col_letter(ci)}{ri}'
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                cells.append(f'<c r="{ref}"><v>{value}</v></c>')
            else:
                txt = xml_escape(str(value))
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{txt}</t></is></c>')
        xml_rows.append(f'<row r="{ri}">{"".join(cells)}</row>')
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' \
           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + ''.join(xml_rows) + '</sheetData></worksheet>'


def write_xlsx_report(data, path: Path):
    sheets = []
    summary_rows = [['AI Prompt Collector v6 Result Summary', ''], ['Generated at', data['generated_at']], ['',''], ['DOWNLOAD','']]
    summary_rows += [[k, v] for k, v in data['download'].items()]
    summary_rows += [['',''], ['INDEX','']] + [[k, v] for k, v in data['index'].items()]
    sheets.append(('Summary', summary_rows))
    sheets.append(('Models', [['Model','Media','Unique Prompts','Avg Combined Score','Avg Model Fit','Top Combined Score']] + data['model_detail']))
    sheets.append(('Tags', [['Tag','Prompts']] + [[a,b] for a,b in data['top_tags']]))
    sheets.append(('Quality', [['Tier','Prompts']] + [[a,b] for a,b in data['quality']]))

    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        content_types = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                         '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
                         '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
                         '<Default Extension="xml" ContentType="application/xml"/>',
                         '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>']
        for i in range(1, len(sheets)+1):
            content_types.append(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
        content_types.append('</Types>')
        z.writestr('[Content_Types].xml', ''.join(content_types))
        z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        workbook_sheets = ''.join(f'<sheet name="{xml_escape(name)}" sheetId="{i}" r:id="rId{i}"/>' for i,(name,_) in enumerate(sheets,1))
        z.writestr('xl/workbook.xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'+workbook_sheets+'</sheets></workbook>')
        rels = ''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1,len(sheets)+1))
        z.writestr('xl/_rels/workbook.xml.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+rels+'</Relationships>')
        for i,(_,rows) in enumerate(sheets,1):
            z.writestr(f'xl/worksheets/sheet{i}.xml', _sheet_xml(rows))


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = collect_report_data()
    print_console(data)
    html_path = REPORT_DIR / 'RESULT_SUMMARY.html'
    xlsx_path = REPORT_DIR / 'RESULT_SUMMARY.xlsx'
    json_path = REPORT_DIR / 'RESULT_SUMMARY.json'
    write_html_report(data, html_path)
    write_xlsx_report(data, xlsx_path)
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print('\nGenerated reports:')
    print('HTML :', html_path)
    print('Excel:', xlsx_path)
    print('JSON :', json_path)


if __name__ == '__main__':
    main()
