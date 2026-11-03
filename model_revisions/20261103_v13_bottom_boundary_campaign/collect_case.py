"""Immutable nominal-clock MRI comparisons and native-flux reductions per accepted case."""
from pathlib import Path
import json,sys,gzip,xml.etree.ElementTree as ET,hashlib
import numpy as np,pandas as pd
R=Path(__file__).resolve().parent;name=sys.argv[1];raw=R/'raw/runs'/name;out=R/'results'/name;out.mkdir(exist_ok=False)
status=json.loads((raw/'run_status.json').read_text());assert status['status']=='completed' and abs(status['evaporation_time_h']-174)<1e-7
geom=pd.read_csv(raw/'cell_geometry.csv').set_index('dof');exp=pd.read_csv(R/'baseline_reference/MRI_profile_pairs_unchanged.csv');profiles=[];metrics=[];flow=[];sources=[]
entries=ET.parse(raw/(name+'.pvd')).findall('.//DataSet')
for h in [24,60,84,96,120,144,174]:
 e=next(e for e in entries if abs(float(e.get('timestep'))/3600-2-h)<1e-7);p=raw/(e.get('file')+'.gz');b=p.read_bytes();root=ET.fromstring(gzip.decompress(b));a={el.get('Name'):np.fromstring(el.text or '',sep=' ').reshape(-1,int(el.get('NumberOfComponents','1'))) for el in root.findall('.//CellData/DataArray')}
 a={k:(v[:,0] if v.shape[1]==1 else v) for k,v in a.items()};ids=a['dof_id'].astype(int);g=geom.loc[ids];pos=g[['x_m','y_m','z_m']].to_numpy();v=g.volume_m3.to_numpy();low=(.04-g.ymax_m.to_numpy())*1000;high=(.04-g.ymin_m.to_numpy())*1000;depth=(.04-pos[:,1])*1000
 C=a['x^NaCl_liq']*a['rhoMolar_liq']/1000;vy=a['velocity_liq_interior_LS (m/s)'][:,1];rho=a['rho_liq']
 for side,mask in [('F36',(pos[:,0]<.025)&(pos[:,1]>0)),('W3',(pos[:,0]>.025)&(pos[:,1]>0))]:
  cs=[]
  for d in range(40):
   w=np.maximum(0,np.minimum(high,d+1)-np.maximum(low,d))/(high-low)*v*mask;cs.append(np.average(C,weights=w));profiles.append(dict(case=name,time_h=h,side=side,depth_mm=d+.5,C_M=cs[-1]))
  obs=exp[(exp.side==side)&(exp.time_h==h)].sort_values('depth_mm').MRI_archived_M.to_numpy();err=np.array(cs)[3:37]-obs[3:37]
  metrics.append(dict(case=name,time_h=h,side=side,mean_C_M=np.mean(cs[3:37]),MRI_mean_C_M=np.mean(obs[3:37]),bias_M=err.mean(),RMSE_M=np.sqrt(np.mean(err**2)),shape_RMSE_M=np.std(err),gradient_error_M_mm=np.polyfit(np.arange(3.5,37),err,1)[0]))
  anomaly=C.copy();ra=rho.copy()
  for y in np.unique(pos[mask,1]):
   m=mask&(pos[:,1]==y);anomaly[m]-=np.average(C[m],weights=v[m]);ra[m]-=np.average(rho[m],weights=v[m])
  for label,m in [('all',mask),('core',mask&(np.hypot(pos[:,0]-.025,pos[:,2])<.02)&(abs(pos[:,0]-.025)>.003)&(depth>5)&(depth<35))]:
   avg=lambda z:float(np.average(z[m],weights=v[m]));flow.append(dict(case=name,time_h=h,side=side,region=label,max_downflow_m_s=max(0.,-vy[m].min()),max_upflow_m_s=max(0.,vy[m].max()),down_volume_fraction=float(v[m&(vy<-1e-8)].sum()/v[m].sum()),horizontal_C_RMS_M=np.sqrt(avg(anomaly**2)),density_anomaly_RMS_kg_m3=np.sqrt(avg(ra**2))))
 sources.append(dict(file=p.name,sha256=hashlib.sha256(b).hexdigest()))
pd.DataFrame(profiles).to_csv(out/'profiles.csv',index=False);pd.DataFrame(metrics).to_csv(out/'concentration_metrics.csv',index=False);pd.DataFrame(flow).to_csv(out/'flow_metrics.csv',index=False)
film=pd.read_csv(raw/'film_budget.csv');loss=np.interp(174,film.evaporation_time_h,film.cumulative_reservoir_loss_g)-np.interp(1,film.evaporation_time_h,film.cumulative_reservoir_loss_g)
meas=pd.read_csv(R/'baseline_reference/experiment_mass.csv');meas=meas[(meas.time_h>=1)&(meas.time_h<=174)];pred=np.interp(meas.time_h,film.evaporation_time_h,film.cumulative_reservoir_loss_g);dt=np.diff(meas.time_h);rate=np.diff(pred)/dt;observed=-np.diff(meas.mass_g)/dt
pd.DataFrame(dict(start_h=meas.time_h.to_numpy()[:-1],end_h=meas.time_h.to_numpy()[1:],model_g_h=rate,measured_g_h=observed)).to_csv(out/'evaporation_intervals.csv',index=False)
result=dict(case=name,accepted_evaporation_h=174,reservoir_solution_loss_1_174_g=float(loss),target_g=51.52,error_fraction=float(loss/51.52-1),rate_RMSE_g_h=float(np.sqrt(np.average((rate-observed)**2,weights=dt))),limitations='exploratory boundary assumptions, fixed phi/K equivalent solid inventory; MRI unchanged; no actual nucleation inference')
if (raw/'native_fluxes.csv').exists():
 f=pd.read_csv(raw/'native_fluxes.csv');rows=[]
 for (kind,mat),z in f.groupby(['kind','material']):
  row=dict(kind=int(kind),material=int(mat));row.update({c:float(np.sum(z[c]*z.dt_s)) for c in ['qv_out','qv_in','water_adv_out','water_adv_in','water_diff_out','water_diff_in','salt_adv_out','salt_adv_in','salt_diff_out','salt_diff_in']});rows.append(row)
 pd.DataFrame(rows).to_csv(out/'native_integrated_throughputs.csv',index=False);result['gross_integration']='accepted-step backward Euler'
else:
 f=pd.read_csv(raw/'native_replay/flux_history.csv');integrals={c:float(np.trapezoid(np.r_[0,f[c].to_numpy()],np.r_[0,f.time_h.to_numpy()]*3600)) for c in f if c.endswith(('_pos','_neg','_net'))}
 (out/'native_integrated_throughputs.json').write_text(json.dumps(integrals,indent=2));result['gross_integration']='600 s saved-state quadrature with hydrostatic zero-time flux; compare accepted net ledger'
(out/'summary.json').write_text(json.dumps(result,indent=2));(out/'source_hashes.json').write_text(json.dumps(sources,indent=2));print(json.dumps(result))
