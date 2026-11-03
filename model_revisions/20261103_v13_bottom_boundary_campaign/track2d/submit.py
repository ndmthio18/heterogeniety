from pathlib import Path
import subprocess,json,datetime
R=Path(__file__).resolve().parent;assert not (R/'jobs.json').exists()
def submit(name,*args):
 out=subprocess.check_output(['sbatch','--parsable','--hold','--job-name='+name,'--output='+str(R/(name+'_%A_%a.log')),*args,str(R/'job.sh'),*({'bottom2d_core':['core'],'bottom2d_B':['case','array'],'bottom2d_Ggate':['gatesG']}[name] if name in ['bottom2d_core','bottom2d_B','bottom2d_Ggate'] else ['caseG',name[-2:]])],text=True).strip();return out.split(';')[0]
core=submit('bottom2d_core');b=submit('bottom2d_B','--array=0-3%1','--dependency=afterok:'+core);g=submit('bottom2d_Ggate','--dependency=afterok:'+core)
jobs={'core':core,'B_array':b,'G_gates':g}
for name in ['G1','G2','G3']:jobs[name]=submit('bottom2d_'+name,'--dependency=afterok:'+g)
(R/'jobs.json').write_text(json.dumps(dict(jobs=jobs,state='submitted_held; resource dispatcher releases only after eligibility',utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),indent=2));print(json.dumps(jobs))
