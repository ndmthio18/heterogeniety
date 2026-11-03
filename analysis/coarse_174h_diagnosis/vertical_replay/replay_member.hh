 // Read-only diagnostics: original boundary function and original FV flux classes.
 template<class GV>void writeFaceAudit(const SV& x,const GV& gv,double time)const {
  std::ofstream out("faces.csv");out<<std::setprecision(17);
  out<<"kind,time_s,x_m,y_m,z_m,area_m2,material,liquid_volume_m3_s,water_adv_mol_s,water_diff_mol_s,salt_adv_mol_s,salt_diff_mol_s,donor_C_mol_L\n";
  for(const auto& e:elements(this->gridGeometry().gridView())){
   auto fv=localView(this->gridGeometry());fv.bind(e);auto ev=localView(gv.curGridVolVars());ev.bind(e,fv,x);
   auto fc=localView(gv.gridFluxVarsCache());fc.bind(e,fv,ev);
   for(const auto& f:scvfs(fv)){
    const auto pos=f.ipGlobal();const auto& v=ev[f.insideScvIdx()];
    const auto area=f.area()*v.extrusionFactor();const auto material=fv.scv(f.insideScvIdx()).center()[0]<split_?0:1;
    int kind=-1;double qv=0,wa=0,wd=0,sa=0,sd=0,donor=0;
    if(f.boundary()&&pos[1]<this->gridGeometry().bBoxMin()[1]+1e-9){
     kind=0;auto q=neumann(e,fv,ev,fc,f);wa=q[water]*area;sa=q[salt]*area;
     const auto inward=wa<0;const auto rhoM=inward?molarRes_:v.molarDensity(liq);
     qv=(q[water]+q[air]+q[salt])*area/rhoM;
     donor=rhoM*(inward?reservoir_.moleFraction(liq,salt):v.moleFraction(liq,salt))/1000;
    }else if(!f.boundary()){
     if(std::abs(pos[0]-split_)<1e-9&&material==0)kind=1;
     else if(f.unitOuterNormal()[1]>.999&&((pos[1]>.0105&&pos[1]<.0115)||(pos[1]>.0185&&pos[1]<.0195)||(pos[1]>.0300&&pos[1]<.0305)))kind=2;
     if(kind<0)continue;
     FluxVars flux;flux.init(*this,e,fv,ev,f,fc);
     qv=flux.advectiveFlux(liq,[](const auto& vv){return vv.mobility(liq);});
     for(int ph=0;ph<2;++ph){
      wa+=flux.advectiveFlux(ph,[ph](const auto& vv){return vv.mobility(ph)*vv.molarDensity(ph)*vv.moleFraction(ph,water);});
      sa+=flux.advectiveFlux(ph,[ph](const auto& vv){return vv.mobility(ph)*vv.molarDensity(ph)*vv.moleFraction(ph,salt);});
      auto d=flux.molecularDiffusionFlux(ph);
      if constexpr(FluxVars::MolecularDiffusionType::referenceSystemFormulation()==ReferenceSystemFormulation::massAveraged){wd+=d[water]/FS::molarMass(water);sd+=d[salt]/FS::molarMass(salt);}
      else{wd+=d[water];sd+=d[salt];}
     }
    }
    if(kind>=0)out<<kind<<','<<time<<','<<pos[0]<<','<<pos[1]<<','<<pos[2]<<','<<area<<','<<material<<','<<qv<<','<<wa<<','<<wd<<','<<sa<<','<<sd<<','<<donor<<'\n';
   }
  }
 }
