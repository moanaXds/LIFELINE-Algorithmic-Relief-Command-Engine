"""
writer.py - Zero-dependency OpenXML (.xlsx) Workbook Writer
Uses standard Python library (zipfile, io, xml.sax.saxutils).
Produces clean, compliant Excel workbooks matching OpenXML spreadsheet standards.
Deterministic: writes entries with fixed timestamp for byte-identical reproducibility.
"""

import io
import zipfile
from xml.sax.saxutils import escape

# Fixed timestamp for deterministic zip creation
FIXED_ZIP_DATE = (2026, 1, 1, 0, 0, 0)

def _col_name(n):
    """Convert 1-based column index to Excel column letters (1 -> A, 27 -> AA)."""
    result = []
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result.append(chr(65 + rem))
    return "".join(reversed(result))

def _write_entry(z, filename, data_str):
    """Write an entry with a deterministic timestamp and compression."""
    zinfo = zipfile.ZipInfo(filename, date_time=FIXED_ZIP_DATE)
    zinfo.compress_type = zipfile.ZIP_DEFLATED
    # Ensure standard permissions
    zinfo.external_attr = 0o644 << 16
    data_bytes = data_str.encode('utf-8')
    z.writestr(zinfo, data_bytes)

def save_workbook(sheet_dict, output_path):
    """
    Save multiple sheets to an .xlsx file.
    :param sheet_dict: dict of {sheet_name: [ [row1_col1, row1_col2, ...], [row2_...], ... ]}
    :param output_path: file path to write cases.xlsx
    """
    sheet_names = list(sheet_dict.keys())
    
    # 1. [Content_Types].xml
    content_types = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">']
    content_types.append('  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>')
    content_types.append('  <Default Extension="xml" ContentType="application/xml"/>')
    content_types.append('  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>')
    for i in range(1, len(sheet_names) + 1):
        content_types.append(f'  <Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
    content_types.append('</Types>')
    content_types_xml = "\n".join(content_types)

    # 2. _rels/.rels
    root_rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''

    # 3. xl/_rels/workbook.xml.rels
    wb_rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    for i in range(1, len(sheet_names) + 1):
        wb_rels.append(f'  <Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>')
    wb_rels.append('</Relationships>')
    wb_rels_xml = "\n".join(wb_rels)

    # 4. xl/workbook.xml
    wb_xml_parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">\n  <sheets>']
    for i, name in enumerate(sheet_names, start=1):
        escaped_name = escape(name)
        wb_xml_parts.append(f'    <sheet name="{escaped_name}" sheetId="{i}" r:id="rId{i}"/>')
    wb_xml_parts.append('  </sheets>\n</workbook>')
    workbook_xml = "\n".join(wb_xml_parts)

    # Write to zip
    with open(output_path, 'wb') as f_out:
        with zipfile.ZipFile(f_out, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            _write_entry(z, '[Content_Types].xml', content_types_xml)
            _write_entry(z, '_rels/.rels', root_rels_xml)
            _write_entry(z, 'xl/_rels/workbook.xml.rels', wb_rels_xml)
            _write_entry(z, 'xl/workbook.xml', workbook_xml)

            for i, name in enumerate(sheet_names, start=1):
                rows = sheet_dict[name]
                sheet_lines = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">\n  <sheetData>']
                for r_idx, row in enumerate(rows, start=1):
                    row_parts = [f'    <row r="{r_idx}">']
                    for c_idx, val in enumerate(row, start=1):
                        cell_ref = f"{_col_name(c_idx)}{r_idx}"
                        if isinstance(val, (int, float)) and not isinstance(val, bool):
                            row_parts.append(f'<c r="{cell_ref}"><v>{val}</v></c>')
                        else:
                            val_str = "" if val is None else str(val)
                            escaped_val = escape(val_str)
                            row_parts.append(f'<c r="{cell_ref}" t="inlineStr"><is><t>{escaped_val}</t></is></c>')
                    row_parts.append('</row>')
                    sheet_lines.append("".join(row_parts))
                sheet_lines.append('  </sheetData>\n</worksheet>')
                _write_entry(z, f'xl/worksheets/sheet{i}.xml', "\n".join(sheet_lines))
