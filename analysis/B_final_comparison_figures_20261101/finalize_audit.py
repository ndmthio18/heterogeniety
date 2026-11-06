"""Audit final PDF artifacts, create a reading pack, and finalize provenance."""
from pathlib import Path
import hashlib,json,subprocess,sys
import fitz
from PIL import Image,ImageOps,ImageDraw

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
NAMES=['Fig05_B_final_response_robustness','Fig04_B_final_supply_and_partitioning',
       'FigS_B_final_local_transport_compensation','FigS_B_final_numerical_and_plume_limits']
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(2**20),b''):h.update(c)
    return h.hexdigest()

m=json.loads((HERE/'MANIFEST.json').read_text())
assert m['script_sha256']==sha(HERE/'make_figures.py')
for p,h in m['source_sha256'].items():assert sha(ROOT/p)==h,p
audit_script=Path.home()/'.agents/skills/nature-figure/scripts/audit_figure_collisions.py'
report={};merged=fitz.open();toc=[]
for i,name in enumerate(NAMES):
    pdf=HERE/f'{name}.pdf';audit=HERE/f'{name}.collisions.json'
    run=subprocess.run([sys.executable,'-X','utf8',str(audit_script),str(pdf),'--json-out',str(audit)],capture_output=True,text=True,encoding='utf-8')
    if run.returncode:print(run.stdout);raise RuntimeError(name+' collision audit failed')
    r=json.loads(audit.read_text());assert r['verdict']=='PASS'
    doc=fitz.open(pdf);assert len(doc)==1
    fonts=doc[0].get_fonts(full=True);assert all(f[1] for f in fonts),fonts
    pic=Image.open(HERE/f'{name}.png');assert min(pic.info['dpi'])>599
    report[name]={'pdf_sha256':sha(pdf),'collision_summary':r['summary'],'font_names':[f[3] for f in fonts],
        'page_points':list(doc[0].rect),'raster_pixels':list(pic.size),'dpi':list(pic.info['dpi'])}
    merged.insert_pdf(doc);toc.append([1,name,i+1])
merged.set_toc(toc)
merged.set_metadata({'title':'Completed A+B comparison figures: surface effects, supply and verification','author':'Codex; based on archived A/B numerical results'})
merged.save(HERE/'B_final_comparison_pack.pdf',garbage=4,deflate=True)
sheet=Image.new('RGB',(1200,1240),'white')
for i,name in enumerate(NAMES):
    pic=Image.open(HERE/f'{name}_preview.png').convert('RGB')
    pic=ImageOps.contain(pic,(590,600))
    sheet.paste(pic,((i%2)*600+(600-pic.width)//2,(i//2)*620))
sheet.save(HERE/'CONTACT_SHEET.png')
num=json.loads((HERE/'NUMERIC_QA.json').read_text())
report['numeric_summary']={'accepted_cases':num['accepted_cases'],
    'max_independent_0_2mm_closure_mg':max(v for k,v in num.items() if k.endswith('_0_2_closure_max_mg')),
    'source_files_verified':len(m['source_sha256'])}
report['visual_review']='All four final previews reviewed for labels, legends, clipping and honest scale/uncertainty encoding.'
report['submission_status']='Provisional scientific figure package, not certification of journal production compliance or experimental validation.'
(HERE/'FINAL_QA.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
m['output_sha256']={str(p.relative_to(HERE)):sha(p) for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='MANIFEST.json' and '__pycache__' not in str(p)}
(HERE/'MANIFEST.json').write_text(json.dumps(m,indent=2),encoding='utf-8')
print(json.dumps(report['numeric_summary']))
print('Four figures passed rendered collision audits; combined PDF and contact sheet exported.')
