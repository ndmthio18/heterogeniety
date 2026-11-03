"""Redraw archived hete_test against Ali's data in solution molarity only.

Standalone, read-only with respect to experimental and simulation inputs.
New diagnostic figures, source tables and a report go to Figures/.
"""
from pathlib import Path
from datetime import datetime
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image
from pypdf import PdfReader, PdfWriter

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'analysis'/'model_experiment_comparison_20261028'
SIM=ROOT/'liqin_snapshot'/'Simulation_Data'/'REV_scale'/'hete_experiment'/'hete_test'
OUT=ROOT/'Figures'/'molarity_comparison_20261028'
SIDES=['F36','W3']
COL={'F36':'#0072B2','W3':'#D55E00'}
Z=np.arange(40)+.5
BANDS={'surface_0_3':(0,3),'upper_3_10':(3,10),'middle_10_20':(10,20),'deep_20_37':(20,37),'bottom_37_40':(37,40),'core_3_37':(3,37)}
PRIMARY=['upper_3_10','middle_10_20','deep_20_37']
PRECIP_H=33+50/60


def readcsv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def writecsv(name,rows):
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()


def vtu(path):
    root=ET.parse(path)
    fields={}
    for el in root.findall('.//CellData/DataArray'):
        arr=np.fromstring(el.text or '',sep=' ')
        n=int(el.get('NumberOfComponents','1'))
        fields[el.get('Name')]=arr if n==1 else arr.reshape(-1,n)
    pts=np.fromstring(root.find('.//Points/DataArray').text,sep=' ').reshape(-1,3)
    cn=np.fromstring(root.find('.//Cells/DataArray[@Name="connectivity"]').text,sep=' ',dtype=int).reshape(-1,4)
    vertices=pts[cn]
    center=vertices.mean(1)
    low=.04-vertices[:,:,1].max(1)
    high=.04-vertices[:,:,1].min(1)
    dx=np.ptp(vertices[:,:,0],axis=1)
    return fields,center,low,high,dx,vertices


def invsignal(side,s):
    if side=='F36':return (s-.96)/2.62
    disc=7.1241-.9032*(s-.6991)
    return np.where(disc>=0,(2.6693-np.sqrt(np.maximum(disc,0)))/.4516,np.nan)


def signal(side,cv):
    if side=='F36':return .96+2.62*cv
    return .6991+(7.1241-(2.6693-.4516*cv)**2)/.9032


def save(fig,stem,manifest):
    fig.savefig(OUT/(stem+'.png'),dpi=260)
    fig.savefig(OUT/(stem+'.pdf'))
    plt.close(fig)
    with Image.open(OUT/(stem+'.png')) as im:
        pixels=list(im.size)
        im.verify()
    manifest[stem]={'png_pixels':pixels,'pdf_bytes':(OUT/(stem+'.pdf')).stat().st_size}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pvd=ET.parse(SIM/'hete.pvd').findall('.//DataSet')
    times=np.array([float(r.get('timestep'))/3600 for r in pvd])
    f,c,lo,hi,dx,verts=vtu(SIM/pvd[0].get('file'))
    overlap=np.maximum(0,np.minimum(hi[None,:],(Z[:,None]+.5)/1000)-np.maximum(lo[None,:],(Z[:,None]-.5)/1000))
    weights={side:overlap*dx[None,:]*((c[:,0]<.025) if side=='F36' else (c[:,0]>=.025))[None,:] for side in SIDES}
    matrices={s:weights[s]/weights[s].sum(1)[:,None] for s in SIDES}
    cube=np.empty((len(times),2,40));proxy=np.empty_like(cube)
    bad_counts=[];frame_meta=[];maps={};field_sources=[]
    map_times=[0.,8.,24.,48.]
    original_times=[0.,11.,20.,40.,times[-1]]
    needed=map_times+original_times
    for i,(t,r) in enumerate(zip(times,pvd)):
        path=SIM/r.get('file');ff,cc,ll,hh,ww,vv=vtu(path)
        assert np.allclose(cc,c) and np.allclose(ll,lo) and np.allclose(hh,hi)
        x=ff['x^NaCl_liq'];rho=ff['rhoMolar_liq']
        conc=x*rho/1000
        valid=(x>=0)&(x<=1)&(ff['x^H2O_liq']>=0)&(ff['x^H2O_liq']<=1)&np.isfinite(conc)&(rho>0)
        bad_counts.append(int((~valid).sum()))
        theta=ff['porosity']*ff['S_liq']
        for j,side in enumerate(SIDES):
            pred=matrices[side]@conc
            apparent=invsignal(side,matrices[side]@signal(side,theta*conc))/{'F36':.39,'W3':.35}[side]
            affected=(weights[side][:,~valid].sum(1)>0)
            pred[affected]=np.nan;apparent[affected]=np.nan
            cube[i,j]=pred;proxy[i,j]=apparent
        frame_meta.append({'time_h':float(t),'invalid_component_cells':int((~valid).sum()),'min_saturation':float(ff['S_liq'].min()),
                           'max_precipitate_volume_fraction':float(ff['precipitateVolumeFraction^NaCl'].max()),
                           'minimum_liquid_molarity':float(conc.min()),'maximum_liquid_molarity':float(conc.max()),
                           'x_NaCl_max':float(x.max()),'x_H2O_min':float(ff['x^H2O_liq'].min())})
        if any(abs(t-q)<1e-8 for q in needed):maps[float(t)]=(conc,valid)
        field_sources.append({'file':r.get('file'),'time_h':float(t),'sha256':sha(path)})
    bad_counts=np.array(bad_counts)

    def instantaneous(t,side,kind='liquid'):
        j=SIDES.index(side);a=cube if kind=='liquid' else proxy
        return np.array([np.interp(t,times,a[:,j,k]) for k in range(40)])

    def observed(t,side,kind='liquid'):
        if t==0:return instantaneous(0,side,kind)
        start=max(0,t-16/60);end=min(times[-1],t+16/60)
        knots=np.unique(np.r_[start,times[(times>start)&(times<end)],end])
        vals=np.array([instantaneous(tt,side,kind) for tt in knots])
        return np.trapezoid(vals,knots,axis=0)/(end-start)

    exrows=readcsv(BASE/'experimental_profiles.csv')
    exp={};recal={};shared={}
    for side in SIDES:
        ts=sorted(set(float(r['time_h']) for r in exrows if r['side']==side and float(r['time_h'])<=48))
        shared[side]=ts
        for t in ts:
            rr=sorted((r for r in exrows if r['side']==side and float(r['time_h'])==t),key=lambda r:float(r['depth_center_mm']))
            assert len(rr)==40 and np.allclose([float(r['depth_center_mm']) for r in rr],Z)
            exp[side,t]=np.array([float(r['archived_concentration']) for r in rr])
            recal[side,t]=np.array([float(r['signal_recalibration']) for r in rr])
    paired=[];band_rows=[];sse_rows=[];error_decomp=[];initial=[]
    for side in SIDES:
        for t in shared[side]:
            mod=observed(t,side);obs=exp[side,t];app=observed(t,side,'proxy')
            err=mod-obs;chg=(mod-observed(0,side))-(obs-exp[side,0])
            for k,z in enumerate(Z):
                paired.append({'side':side,'time_h':t,'registered_depth_mm':z,'experiment_mol_L':obs[k],'model_mol_L':mod[k],
                               'model_minus_experiment_mol_L':err[k],'model_MRI_proxy_mol_L':app[k],
                               'experiment_unmodified_signal_recalibration_mol_L':recal[side,t][k],
                               'change_from_initial_residual_mol_L':chg[k]})
            for name,(zmin,zmax) in BANDS.items():
                k=(Z>=zmin)&(Z<zmax)
                e=err[k];ob=obs[k];mm=mod[k]
                band_rows.append({'side':side,'time_h':t,'band':name,'depth_min_mm':zmin,'depth_max_mm':zmax,'n_bins':int(k.sum()),
                                  'experiment_mean_mol_L':float(ob.mean()),'model_mean_mol_L':float(mm.mean()),
                                  'bias_mol_L':float(e.mean()),'relative_mean_bias':float(e.mean()/ob.mean()),
                                  'rmse_mol_L':float(np.sqrt(np.mean(e**2))),
                                  'model_change_from_initial_mol_L':float((mod-observed(0,side))[k].mean()),
                                  'experiment_change_from_initial_mol_L':float((obs-exp[side,0])[k].mean())})
            core=(Z>=3)&(Z<37);total=float(np.sum(err[core]**2))
            for name in PRIMARY:
                zmin,zmax=BANDS[name];k=(Z>=zmin)&(Z<zmax)
                sse_rows.append({'side':side,'time_h':t,'band':name,'n_bins':int(k.sum()),
                                 'squared_error_mol2_L2':float(np.sum(err[k]**2)),
                                 'fraction_of_core_squared_error':float(np.sum(err[k]**2)/total)})
            bias=float(err[core].mean());mse=float(np.mean(err[core]**2))
            error_decomp.append({'side':side,'time_h':t,'core_bias_mol_L':bias,'core_rmse_mol_L':np.sqrt(mse),
                                 'shape_rmse_after_removing_mean_bias_mol_L':float(np.std(err[core])),
                                 'mean_bias_squared_fraction_of_mse':bias*bias/mse})
    writecsv('paired_profiles_molarity.csv',paired);writecsv('depth_band_metrics.csv',band_rows)
    writecsv('squared_error_by_depth.csv',sse_rows);writecsv('mean_bias_and_shape_error.csv',error_decomp)
    writecsv('model_frame_state.csv',frame_meta)
    continuous=[]
    for i,t in enumerate(times):
        if t>48:break
        for j,side in enumerate(SIDES):
            for band in PRIMARY:
                z0,z1=BANDS[band];k=(Z>=z0)&(Z<z1)
                continuous.append({'side':side,'time_h':float(t),'band':band,'model_mean_mol_L':float(cube[i,j,k].mean())})
    writecsv('continuous_model_band_means.csv',continuous)

    # Independent recomputation must reproduce the previous molarity values.
    prior=readcsv(BASE/'profile_comparison.csv');deltas=[]
    for r in prior:
        t=float(r['time_h'])
        if r['basis']!='molarity' or t>48:continue
        k=int(round(float(r['depth_mm'])-.5))
        deltas.append(abs(observed(t,r['side'])[k]-float(r['model_liquid'])))
    assert max(deltas)<1e-10
    assert len(times)==348 and bad_counts[-1]>0 and np.all(bad_counts[:-1]==0)
    assert all(np.isfinite(float(r['model_mol_L'])) for r in paired)
    for side in SIDES:
        for t in shared[side]:
            ss=[r for r in sse_rows if r['side']==side and r['time_h']==t]
            assert abs(sum(r['fraction_of_core_squared_error'] for r in ss)-1)<1e-12

    rc={'font.family':'Arial','font.size':10,'axes.spines.top':False,'axes.spines.right':False,
        'axes.titlesize':11,'axes.labelsize':10,'pdf.fonttype':42,'savefig.facecolor':'white','figure.facecolor':'white'}
    manifest={}
    with plt.rc_context(rc):
        # Actual quad cell boundaries, without interpolation or capped tails.
        xs=np.unique(verts[:,:,0])*100;ds=np.sort(np.unique(.04-verts[:,:,1]))*1000
        order=np.lexsort((c[:,0],.04-c[:,1]))
        vmax=max(float(maps[t][0].max()) for t in map_times)
        vmax=np.ceil(vmax*2)/2
        fig,axes=plt.subplots(1,4,figsize=(12.2,4.4),sharey=True,layout='constrained')
        for ax,t in zip(axes,map_times):
            cc,valid=maps[t];grid=cc[order].reshape(40,32)
            im=ax.pcolormesh(xs,ds,grid,cmap='viridis',vmin=0,vmax=vmax,shading='flat',rasterized=True)
            ax.axvline(2.5,color='white',ls='--',lw=1)
            ax.set(title=f'{t:g} h'+(' *' if t==48 else ''),xlabel='Horizontal position (cm)',ylim=(40,0),xlim=(0,5))
            ax.text(.25,1.015,'F36',transform=ax.transAxes,ha='center',fontsize=9)
            ax.text(.75,1.015,'W3',transform=ax.transAxes,ha='center',fontsize=9)
        axes[0].set_ylabel('Depth below model surface (mm)')
        fig.colorbar(im,ax=axes.tolist(),label='Liquid NaCl concentration (mol/L)',shrink=.87,pad=.02)
        fig.suptitle('Existing model, corrected solution molarity\n* 48 h includes simulated precipitation; instantaneous model fields',fontsize=12)
        save(fig,'01_model_2d_molarity',manifest)

        fig,axes=plt.subplots(2,4,figsize=(12.2,7.7),sharey=True,layout='constrained')
        for j,t in enumerate(map_times):
            for i,side in enumerate(SIDES):
                ax=axes[i,j]
                ax.plot(exp[side,t],Z,'o',color='#202020',ms=3.1,label='Ali archived MRI profile')
                ax.plot(observed(t,side),Z,color=COL[side],lw=1.8,label='Model, solution molarity')
                ax.axhspan(0,3,color='#eeeeee',zorder=-5);ax.axhspan(37,40,color='#eeeeee',zorder=-5)
                ax.set(title=f'{side}, {t:g} h'+(' *' if t==48 else ''),ylim=(40,0),xlim=(.5,5.1 if side=='W3' else 2.3))
                if j==0:ax.set_ylabel('Registered depth (mm)')
                if i==1:ax.set_xlabel('NaCl concentration (mol/L)')
        handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=2,frameon=False)
        fig.suptitle('Experiment and existing model on the same mol/L basis\nModel: 1 mm bins and 32 min average; grey edges excluded from core metrics; * simulated precipitation',fontsize=11)
        save(fig,'02_experiment_model_profiles_molarity',manifest)

        fig,axes=plt.subplots(2,3,figsize=(11,7.6),sharex=True,sharey=True,layout='constrained')
        for j,t in enumerate([8.,24.,48.]):
            for i,side in enumerate(SIDES):
                ax=axes[i,j];e=observed(t,side)-exp[side,t]
                change=e-(observed(0,side)-exp[side,0])
                ax.plot(e,Z,color=COL[side],lw=1.8,label='Model minus experiment')
                ax.plot(change,Z,color='#666666',ls='--',lw=1.2,label='Residual in change from initial')
                ax.axvline(0,color='black',lw=.8)
                for zz in [3,10,20,37]:ax.axhline(zz,color='#cccccc',lw=.6,ls=':')
                ax.axhspan(0,3,color='#eeeeee',zorder=-5);ax.axhspan(37,40,color='#eeeeee',zorder=-5)
                ax.set(title=f'{side}, {t:g} h'+(' *' if t==48 else ''),ylim=(40,0))
                if j==0:ax.set_ylabel('Registered depth (mm)')
                if i==1:ax.set_xlabel('Concentration residual (mol/L)')
        handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=2,frameon=False)
        fig.suptitle('Where the model differs: positive residual means model too high\nDashed curves diagnose initial offsets; they do not recalibrate the model; * simulated precipitation',fontsize=11)
        save(fig,'03_residual_by_depth_molarity',manifest)

        fig,axes=plt.subplots(2,3,figsize=(11.8,6.7),sharex=True,sharey='col',layout='constrained')
        for j,band in enumerate(PRIMARY):
            z0,z1=BANDS[band];k=(Z>=z0)&(Z<z1)
            for i,side in enumerate(SIDES):
                ax=axes[i,j];ii=times<=48
                ax.plot(times[ii],cube[ii,i][:,k].mean(1),color=COL[side],lw=1.8,label='Model')
                ts=shared[side];vals=[exp[side,t][k].mean() for t in ts]
                ax.scatter(ts,vals,color='#202020',s=25,zorder=5,label='Ali archived MRI')
                ax.axvline(PRECIP_H,color='#888888',ls=':',lw=1)
                ax.set(title=f'{side}, {z0}–{z1} mm',xlim=(0,49))
                if j==0:ax.set_ylabel('Mean concentration (mol/L)')
                if i==1:ax.set_xlabel('Nominal time (h)')
        handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=2,frameon=False)
        fig.suptitle('Evolution by depth band: model curves and measured scan times\nDotted line: first stored simulated precipitation, 33.83 h',fontsize=11)
        save(fig,'04_depth_band_evolution_molarity',manifest)

        h=readcsv(BASE/'model_history.csv');inv=readcsv(BASE/'experimental_inventories.csv');bal=readcsv(BASE/'balance_recomputed.csv')
        ht=np.array([float(r['time_h']) for r in h]);mask=ht<=48
        fig,axes=plt.subplots(2,2,figsize=(11.4,7.7),layout='constrained')
        for j,side in enumerate(SIDES):
            ax=axes[0,j]
            ax.plot(ht[mask],[float(r[side+'_dissolved_g']) for r in h if float(r['time_h'])<=48],color=COL[side],label='Model dissolved')
            ax.plot(ht[mask],[float(r[side+'_dissolved_g'])+float(r[side+'_solid_g']) for r in h if float(r['time_h'])<=48],color=COL[side],ls='--',label='Model dissolved + solid')
            ax.plot(ht[mask],[float(r[side+'_apparent_molarity_g']) for r in h if float(r['time_h'])<=48],color='#009E73',ls=':',label='Model idealized MRI proxy')
            ax.scatter([float(r['time_h']) for r in inv if float(r['time_h'])<=48],[float(r[side+'_MRI_NaCl_equiv_g']) for r in inv if float(r['time_h'])<=48],s=27,color='#202020',label='Ali MRI estimate',zorder=5)
            ax.axvline(PRECIP_H,color='#888888',ls=':',lw=.8)
            ax.set(title=side,xlabel='Nominal time (h)',ylabel='NaCl-equivalent mass (g)',xlim=(0,49),ylim=(.75,1.5))
        handles,labels=axes[0,0].get_legend_handles_labels();axes[0,0].legend(handles,labels,fontsize=8,frameon=False)
        bb=[r for r in bal if float(r['time_h'])<=48]
        bt=np.array([float(r['time_h']) for r in bb]);depth=np.array([float(r['proxy_depth_from_first_mm']) for r in bb])
        axes[1,0].plot(bt,depth,'ko-',ms=3,label='Reservoir-loss proxy')
        axes[1,0].plot(bt,(bt-1)*5.00256/24,color='#0072B2',label='Budget-consistent uniform setting')
        axes[1,0].set(xlabel='Nominal time (h)',ylabel='Depth relative to 1 h (mm)',title='Forcing comparison',xlim=(0,49))
        axes[1,0].legend(fontsize=8,frameon=False)
        axes[1,1].plot(bt[1:],[float(r['interval_rate_mm_day']) for r in bb[1:]],'ko-',ms=3,label='Interval reservoir-loss proxy')
        axes[1,1].axhline(5.00256,color='#0072B2',label='Uniform setting: 5.00 mm/day')
        axes[1,1].set(xlabel='Interval end time (h)',ylabel='Rate (mm/day)',title='Time-varying supply proxy',xlim=(0,49),ylim=(0,6.5))
        axes[1,1].legend(fontsize=8,frameon=False)
        fig.suptitle('Salt inventories and forcing diagnose different sources of discrepancy\n2D inventories scaled to equal cylinder area; reservoir loss is a supply proxy, not independent evaporation',fontsize=11)
        save(fig,'05_inventory_and_forcing',manifest)

        fig,axes=plt.subplots(2,2,figsize=(9.3,7.7),sharey=True,layout='constrained')
        for i,side in enumerate(SIDES):
            for j,t in enumerate([24.,48.]):
                ax=axes[i,j]
                ax.plot(exp[side,t],Z,'ko',ms=3,label='Ali archived profile')
                ax.plot(recal[side,t],Z,color='#888888',ls=':',label='Unmodified grey-value recalibration')
                ax.plot(observed(t,side),Z,color=COL[side],label='Model liquid molarity')
                ax.plot(observed(t,side,'proxy'),Z,color='#009E73',ls='--',label='Model idealized MRI proxy')
                ax.set(title=f'{side}, {t:g} h',ylim=(40,0),xlabel='Concentration (mol/L)')
                if j==0:ax.set_ylabel('Registered depth (mm)')
        handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=2,fontsize=9,frameon=False)
        fig.suptitle('Sensitivity to profile processing and a simplified MRI observation operator\nAll values use solution molarity; this proxy is not a full MRI reconstruction',fontsize=11)
        save(fig,'S1_processing_and_observation_molarity',manifest)

        # Preserve original Figure-8 snapshot times in a separate diagnostic.
        # Exclude the whole nonphysical final frame from physical maps rather
        # than silently presenting its remaining cells as a valid field.
        good_ts=original_times[:-1]
        cap=np.ceil(max(float(maps[t][0].max()) for t in good_ts)*2)/2
        fig,axes=plt.subplots(1,5,figsize=(13.6,4.4),sharey=True,layout='constrained')
        for ax,t in zip(axes,original_times):
            if t==times[-1]:
                ax.set_facecolor('#ededed')
                ax.text(.5,.55,'Nonphysical frame\nnot shown as a\nconcentration field',transform=ax.transAxes,ha='center',va='center',fontsize=10)
                ax.text(.5,.21,f'max x(NaCl) = {frame_meta[-1]["x_NaCl_max"]:.3f}\nmin x(water) = {frame_meta[-1]["x_H2O_min"]:.3f}',transform=ax.transAxes,ha='center',fontsize=9)
            else:
                cc,valid=maps[t];im=ax.pcolormesh(xs,ds,cc[order].reshape(40,32),cmap='viridis',vmin=0,vmax=cap,shading='flat',rasterized=True)
                ax.axvline(2.5,color='white',ls='--',lw=1)
            ax.set(title=f'{t:.2f} h' if t==times[-1] else f'{t:g} h',xlabel='Horizontal position (cm)',ylim=(40,0),xlim=(0,5))
        axes[0].set_ylabel('Depth below model surface (mm)')
        fig.colorbar(im,ax=axes[:4].tolist(),label='Liquid NaCl concentration (mol/L)',shrink=.85,pad=.015)
        fig.suptitle('Original Figure-8 snapshot times, corrected to mol/L\nLast PVD time is 57.83 h; the old 57 h label and nonphysical field are not retained',fontsize=11)
        save(fig,'S2_original_2d_snapshot_times_molarity',manifest)

        # Original Figure-9 temporal progression; invalid original last frame
        # is omitted and stated explicitly, not replaced by a different time.
        legacy=[0.,5.,10.,15.,20.,25.,30.,35.,40.,45.,50.,55.]
        fig,axes=plt.subplots(1,2,figsize=(9.5,6),sharey=True,layout='constrained')
        palette=plt.get_cmap('plasma')
        for j,side in enumerate(['W3','F36']):
            ax=axes[j]
            for i,t in enumerate(legacy):
                ax.plot(instantaneous(t,side),Z,color=palette(i/(len(legacy)-1)),label=f'{t:g} h',lw=1.2)
            ax.set(title=side,xlabel='NaCl concentration (mol/L)',ylim=(40,0))
        axes[0].set_ylabel('Registered depth (mm)')
        handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=6,fontsize=8,frameon=False)
        fig.suptitle('Original Figure-9 time progression, corrected to solution molarity\n1 mm depth bins; instantaneous profiles; nonphysical 57.83 h frame excluded',fontsize=11)
        save(fig,'S3_original_profile_times_molarity',manifest)

    writer=PdfWriter()
    for stem in manifest:
        reader=PdfReader(OUT/(stem+'.pdf'))
        assert len(reader.pages)==1
        writer.add_page(reader.pages[0])
    with (OUT/'Molarity_comparison_figures.pdf').open('wb') as f:writer.write(f)
    assert len(PdfReader(OUT/'Molarity_comparison_figures.pdf').pages)==len(manifest)

    def band(side,t,b):return next(r for r in band_rows if r['side']==side and r['time_h']==t and r['band']==b)
    def share(side,t,b):return next(r['fraction_of_core_squared_error'] for r in sse_rows if r['side']==side and r['time_h']==t and r['band']==b)
    table='\n'.join(f'| {t:g} | {s} | {band(s,t,"upper_3_10")["bias_mol_L"]:+.3f} | {band(s,t,"middle_10_20")["bias_mol_L"]:+.3f} | {band(s,t,"deep_20_37")["bias_mol_L"]:+.3f} | {share(s,t,"upper_3_10"):.1%} |' for t in [8.,24.,48.] for s in SIDES)
    coretable='\n'.join(f'| {t:g} | {s} | {band(s,t,"core_3_37")["relative_mean_bias"]:+.1%} | {band(s,t,"core_3_37")["rmse_mol_L"]:.3f} |' for t in [8.,24.,48.] for s in SIDES)
    report=f'''# mol/L 重绘与模型偏差定位

日期：2026-10-28。模型为此前绘图对应的 hete_test；本次未重算或调参。

## 结论

修正浓度单位后，模型与实验的偏差仍随时间发展。需要同时查看平均浓度、剖面形状和强迫条件；不能把浓度图相似或内部均值接近当作机制验证。具体偏差位置见下表，正值表示模型偏高，负值表示模型偏低。

主要发现：

1. **最大问题在 W3 细侧上部，且在沉淀前已出现。** 3–10 mm 平均浓度在 24 h 为实验 1.324、模型 1.899 mol/L（+43.4%）；48 h 为实验 1.537、模型 2.698 mol/L（+75.5%）。该带仅有 7 个深度点，却分别占 3–37 mm 内部平方误差的 81.9% 和 85.3%。它既不局限于最上面被排除的 0–3 mm，也不能全归因于 33.83 h 后的沉淀。
2. **F36 粗侧上部也富集过强。** 48 h 的 3–10 mm 为实验 1.146、模型 1.553 mol/L（+35.5%）；20–37 mm 已转为偏高约 12.1%，表明偏差还包括后续向深部的演化，不能仅用表层一个倍数校正。
3. **深度均值会掩盖空间分布问题。** 24 h W3 内部均值仅偏高 4.2%，但上部偏高 0.575、深部偏低 0.139 mol/L，存在抵消。去掉整体均值偏移后，其剖面 RMSE 仍为 0.308 mol/L（原为 0.313），说明主要误差是剖面形状而非一个统一的常数偏移。
4. **初始偏移会产生表面上的吻合。** 48 h W3 深部绝对浓度仅低约 1.6%，但相对各自初始值的增长分别为模型 0.129、实验 0.030 mol/L。初始模型偏低与后续增长过快部分抵消。相反，24 h F36 深部的增长约为模型 0.089、实验 0.088 mol/L，绝对浓度偏低主要与初始差异有关，不能直接将其解释为向下输运不足。

[整套 8 页图件 PDF](Molarity_comparison_figures.pdf)。

| 时间 h | 材料 | 3–10 mm 偏差 mol/L | 10–20 mm 偏差 mol/L | 20–37 mm 偏差 mol/L | 3–10 mm 占内部平方误差 |
|---|---|---:|---:|---:|---:|
{table}

“平方误差占比”是某深度带的逐点平方误差和占 3–37 mm 总和的比例，受该带包含的深度点数影响；这是误差定位指标，不是误差成因的贡献率，也不是独立重复的统计显著性。

| 时间 h | 材料 | 3–37 mm 平均浓度相对偏差 | 剖面 RMSE mol/L |
|---|---|---:|---:|
{coretable}

## 如何阅读图件

1. [01 二维浓度场](01_model_2d_molarity.png)：使用实验共有时刻 0、8、24、48 h；色标覆盖全部四个场的范围，使用真实网格边界。这里是模型空间场，不是重新重建的实验 MRI。
2. [02 实验与模型剖面](02_experiment_model_profiles_molarity.png)：黑点为 Ali 归档剖面，蓝/橙线为模型。只使用 mol/L，保留初始值差异。48 h 已有模型沉淀。
3. [03 深度偏差](03_residual_by_depth_molarity.png)：实线为模型减实验；虚线为各自减去初始值后的变化量之差，用于辨别初始偏移和演化偏差，没有用它拟合或移动模型曲线。
4. [04 分深度时间变化](04_depth_band_evolution_molarity.png)：按 3–10、10–20、20–37 mm 分组；模型连续输出曲线与实际扫描时刻的实验点并列，实验间隙不插值成数据。33.83 h 虚线只标识模型首次保存的沉淀。
5. [05 盐量与强迫](05_inventory_and_forcing.png)：区分溶解盐、固体盐和理想 MRI 信号代理；储液系统减重换算只称为供液代理，不作为独立真实蒸发率。
6. [S1 观测处理敏感性](S1_processing_and_observation_molarity.png)：作者处理与未修正灰度复算、液相浓度与理想 MRI 代理并列，均为 mol/L。F36 固定位置灰度尖峰可能为成像伪影，不能直接认定为物理浓度峰。
7. [S2 原二维图的时刻](S2_original_2d_snapshot_times_molarity.png)：保留 0、11、20、40、57.83 h；末帧因非物理组分明确标记并不显示成物理浓度场。
8. [S3 原剖面图的时间演进](S3_original_profile_times_molarity.png)：保留 0–55 h 每 5 h 的演进，修正单位；剔除原图误标为 57 h 的无效 57.83 h 帧，并明确披露。

每幅图另有同名矢量 PDF。用于研究讨论，未声明符合 WRR 最终出版格式。

## 换算、配准与解释边界

- 实验依据 Chapter 4 pp.48/50 与标定表 Molarity 的明示定义，按溶液摩尔浓度解释。模型逐单元使用 `c=x_NaCl*rhoMolar_liq/1000`。没有采用旧水基换算，也没有在图中画未经单位核对的 6.14 mol/L 溶解度线。
- 保留 Ali 的人工修正浓度作为主比较。按其灰度引用将前 40 个完整层注册为 0.5–39.5 mm；模型与 1 mm 层的实际重叠长度乘水平单元宽度作权重。实验绝对表面/ROI 对齐仍待确认，上下 0–3/37–40 mm 不纳入主指标。
- 共同名义时刻按 ±16 min 作模型时间平均，0 h 使用初始帧。另存的早先审查已检查 ±1 mm/±32 min 及扫描实际时钟情景，48 h 细侧偏高方向未改变。没有把名义时间直接替换成 Bruker 时钟差。
- 剖面是面积/区间平均，不是按局部水量加权的平均；MRI 观测代理另考虑体积含水量与标定非线性，但没有完整点扩散、ROI 或噪声模型。
- 没有已核实的独立异质性重复及均值置信区间，所以没有添加假定误差条。偏差表为描述性诊断，不能据此认定统计显著性或锁定某一物理参数。
- 重绘读出表层富集、层间分布和时间变化偏差；不直接识别密度浮力或界面交换的因果作用。判断机制仍需守恒面通量与独立对照。

## 优先排查的来源

1. 历史二进制与当前分区源码不同。二进制参数和储量诊断支持统一约 5.003 mm/day；按工作簿名义时间重算的 1–48 h 供液代理约为 4.087 mm/day，前者较高约 22%。这是值得优先检验的原因，尚未通过对照证明它能解释各层偏差。
2. 不能只调一个浓度倍数：若不同深度的误差不同，或正负号不同，就同时涉及空间分配。`mean_bias_and_shape_error.csv` 将均方误差分解为平均偏移和去除平均偏移后的形状误差；这个代数分解不是机制分解。
3. 继续检查中央窄入口、滤板与水位、二维/圆柱几何、材料参数和观测处理。当前数据无法单独识别其中哪项为根因，不能直接断言扩散太强或对流太弱。
4. 模型 33.83 h 后进入沉淀，57.83 h 末帧非物理并随后失败。48 h 比较只用于定位偏差，不能作为沉淀过程已验证的证据。

## 复算与资料

[配对剖面数据](paired_profiles_molarity.csv)、[深度带指标](depth_band_metrics.csv)、[平方误差分布](squared_error_by_depth.csv)、[均值与形状误差](mean_bias_and_shape_error.csv)、[输入哈希与方法](provenance.json)。此前的详细数据审查位于 `analysis/model_experiment_comparison_20261028/ASSESSMENT.md`。
'''
    (OUT/'READ_ME_偏差分析.md').write_text(report,encoding='utf-8')
    inputs={str((BASE/name).relative_to(ROOT)):sha(BASE/name) for name in ['experimental_profiles.csv','profile_comparison.csv','model_history.csv','experimental_inventories.csv','balance_recomputed.csv']}
    expfile=next((ROOT/'experimental_data'/'DARUS-6478'/'extracted').rglob('F36+W3_Hetero_Data_Analysis.xlsx'))
    inputs[str(expfile.relative_to(ROOT))]=sha(expfile);inputs[str((SIM/'hete.pvd').relative_to(ROOT))]=sha(SIM/'hete.pvd')
    prov={'created_local':'2026-10-28 Europe/Berlin','case':'hete_test','units':'solution molarity, mol/L',
          'formula':'x^NaCl_liq*rhoMolar_liq/1000','primary_experiment':'Ali archived concentration profiles; author corrections retained',
          'main_times_h':map_times,'original_figure8_times_h':list(map(float,original_times)),
          'registration':'First 40 full grey-value slices at 1 mm; model exact overlap weights; absolute MRI surface and ROI not independently verified',
          'temporal_operator':'Centred 32 min box average at nominal scan times; t=0 initial snapshot',
          'primary_bands_mm':[[3,10],[10,20],[20,37]],'uncertainty':'No independent replicate CI; processing alternatives are sensitivities, not uncertainty intervals',
          'exclude_nonphysical_final_frame_h':float(times[-1]),'all_earlier_frames_pass_component_range_check':bool(np.all(bad_counts[:-1]==0)),
          'validation':'component range check is not full solver convergence or physical validation',
          'max_difference_from_prior_molarity_recomputation':max(deltas),'inputs':inputs,'vtu_source_hashes':field_sources,
          'script_sha256':sha(Path(__file__)),'versions':{'numpy':np.__version__,'matplotlib':matplotlib.__version__},
          'combined_pdf_pages':len(manifest),'figures':manifest}
    (OUT/'provenance.json').write_text(json.dumps(prov,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(OUT),'figures':len(manifest),'max_recompute_difference':max(deltas),'metrics_24_48h':[r for r in band_rows if r['time_h'] in [24.,48.] and r['band'] in PRIMARY]},indent=2))


if __name__=='__main__':main()
