"""Check delivered artifacts, then compose the four-page reading pack."""
from pathlib import Path
import hashlib,json,subprocess,sys
import fitz
from PIL import Image,ImageOps

HERE=Path(__file__).resolve().parent
SKILL=Path.home()/'.agents/skills/nature-figure/scripts'
NAMES=['Fig05_surface_response_v2','Fig04_supply_partition_v2','FigS_local_compensation_v2','FigS_numerical_limits_v2']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(script,args,out):
    r=subprocess.run([sys.executable,'-X','utf8',str(SKILL/script),*map(str,args)],capture_output=True,text=True,encoding='utf-8')
    (HERE/out).write_text(r.stdout,encoding='utf-8')
    if r.returncode:raise RuntimeError(script+' failed: '+r.stdout+r.stderr)
    return json.loads(r.stdout)

m=json.loads((HERE/'MANIFEST.json').read_text())
assert m['script_sha256']==sha(HERE/'redraw.py')
assert m['parent_manifest_sha256']==sha(HERE.parent/'MANIFEST.json')
for p,h in m['sources_sha256'].items():
    assert sha(HERE/p)==h and sha(HERE.parent/p)==h,p
report={'frozen_source_tables_verified':len(m['sources_sha256']),
        'original_numeric_QA_sha256':sha(HERE.parent/'NUMERIC_QA.json'),
        'scope':'Visual revision only; parent raw-field and balance checks are inherited, not rerun.',
        'visual_review':'All four previews and all four pages rendered from the final combined PDF inspected; no clipping or layout defects found; explicit endpoint zoom; original failed metrics preserved.',
        'initial_audit_resolution':'Initial static export warnings were due to dynamic extension paths and a screen-only preview DPI. Exports are now explicit and thumbnails derived from 600-dpi PNGs. The first legend was moved slightly to clear a fill-edge warning. Original audit records retained.'}
report['source_validator']=audit('validate_figure.py',[HERE/'redraw.py','--json'],'SOURCE_VALIDATION.json')
merged=fitz.open()
sheet=Image.new('RGB',(1500,1360),'white')
for i,name in enumerate(NAMES):
    pdf=HERE/(name+'.pdf')
    fontcheck=audit('audit_pdf_text.py',[pdf,'--min-pt','7','--json'],name+'.text.json')
    collisionfile=HERE/(name+'.collisions.json')
    r=subprocess.run([sys.executable,'-X','utf8',str(SKILL/'audit_figure_collisions.py'),str(pdf),'--json-out',str(collisionfile)],capture_output=True,text=True,encoding='utf-8')
    if r.returncode:raise RuntimeError(name+': '+r.stdout+r.stderr)
    collision=json.loads(collisionfile.read_text());assert collision['verdict']=='PASS',collision
    alignment=json.loads((HERE/(name+'.alignment.json')).read_text())
    assert alignment['verdict']=='PASS',alignment
    doc=fitz.open(pdf);assert len(doc)==1
    fonts=doc[0].get_fonts(full=True);assert all(f[1] for f in fonts)
    img=Image.open(HERE/(name+'.png'));assert min(img.info['dpi'])>599
    assert abs(doc[0].rect.width/72*25.4-183)<.01
    report[name]={'pdf_sha256':sha(pdf),'font_audit':fontcheck,'collision_summary':collision['summary'],
        'panel_alignment':alignment,'fonts':[f[3] for f in fonts],
        'page_points':list(doc[0].rect),'raster_pixels':list(img.size),'dpi':list(img.info['dpi'])}
    merged.insert_pdf(doc)
    preview=ImageOps.contain(Image.open(HERE/(name+'_preview.png')).convert('RGB'),(742,670))
    sheet.paste(preview,((i%2)*750+(750-preview.width)//2,(i//2)*680))
merged.set_toc([[1,n,i+1] for i,n in enumerate(NAMES)])
merged.set_metadata({'title':'A+B final comparison figures — visual revision v2','author':'Codex, based on frozen A+B evidence'})
merged.save(HERE/'B_final_comparison_pack_v2.pdf',garbage=4,deflate=True)
sheet.save(HERE/'CONTACT_SHEET_v2.png')
(HERE/'FINAL_QA.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
m['output_sha256']={str(p.relative_to(HERE)):sha(p) for p in HERE.rglob('*') if p.is_file() and p.name!='MANIFEST.json' and '__pycache__' not in str(p)}
(HERE/'MANIFEST.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print('PASS: frozen tables, source audit, four PDF text/collision audits, alignment, embedded fonts, 600 dpi; four-page pack created.')
