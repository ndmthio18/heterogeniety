// Included inside Problem's public scope. Diagnostic storage only; never edits x.
template<class GV>void campaignAudit(const SV& x,const GV& gv,double time,double dt,bool impulse=false,bool maps=false,bool mapsOnly=false){
 using LR=GetPropType<TypeTag,Properties::LocalResidual>;LR residual(this);
 std::array<std::array<double,3>,3> inventory{},outward{};
 // Rows: material 0 coarse sand, 1 fine sand, 2 filter. Columns water, total salt, energy.
 std::array<std::array<double,14>,18> gross{};
 std::ofstream faces;
 if(maps){std::ostringstream name;name<<"native_faces_"<<std::fixed<<std::setprecision(0)<<time<<".csv";faces.open(name.str());faces<<std::setprecision(17)<<"kind,material,x_m,y_m,z_m,area_m2,q_liq_m3_s,water_adv_mol_s,water_diff_mol_s,salt_adv_mol_s,salt_diff_mol_s,energy_W,p_liq_Pa,T_K,donor_C_M\n";}
 auto region=[&](const auto& p){return this->spatialParams().isFilter(p)?2:(p[0]<split_?0:1);};
 for(const auto& e:elements(this->gridGeometry().gridView())){
  auto fv=localView(this->gridGeometry());fv.bind(e);auto ev=localView(gv.curGridVolVars());ev.bind(e,fv,x);auto fc=localView(gv.gridFluxVarsCache());fc.bind(e,fv,ev);
  for(const auto& scv:scvs(fv)){
   const auto& v=ev[scv];const int mat=region(scv.center());const auto vol=scv.volume()*v.extrusionFactor();auto storage=residual.computeStorage(*this,scv,v);
   inventory[mat][0]+=vol*storage[water];inventory[mat][1]+=vol*storage[salt];inventory[mat][2]+=vol*storage[Ind::energyEqIdx];
  }
  for(const auto& f:scvfs(fv)){
   const auto pos=f.ipGlobal();const auto c=fv.scv(f.insideScvIdx()).center();const auto& v=ev[f.insideScvIdx()];const int mat=region(c);const double area=f.area()*v.extrusionFactor();
   double qv=0,wa=0,wd=0,sa=0,sd=0,heat=0,donor=0;int kind=-1;bool cut=false;
   if(f.boundary()){
    auto q=neumann(e,fv,ev,fc,f);wa=q[water]*area;sa=q[salt]*area;heat=q[Ind::energyEqIdx]*area;cut=true;
    if(pos[1]<this->gridGeometry().bBoxMin()[1]+1e-9){kind=0;bool incoming=wa<0;auto molar=incoming?molarRes_:v.molarDensity(liq);qv=(q[water]+q[air]+q[salt])*area/molar;donor=molar*(incoming?reservoir_.moleFraction(liq,salt):v.moleFraction(liq,salt))/1000.;}
   }else{
    const auto co=fv.scv(f.outsideScvIdx()).center();const int other=region(co);cut=other!=mat;
    if(mat==0&&other==1)kind=1;
    if(mat<2&&other==2)kind=3; // outward from sand into filter; inflow has negative sign
    if(mat==2&&other==2&&c[0]<split_&&co[0]>split_)kind=5;
    if(f.unitOuterNormal()[1]>.999){
     if(mat==2&&std::abs(pos[1]+.00225)<1e-9)kind=4;
     if(mat<2&&(std::abs(pos[1]-.0110026)<1e-8||std::abs(pos[1]-.0190235)<1e-8||std::abs(pos[1]-.0302801)<1e-8))kind=2;
    }
    if(!cut&&kind<0)continue;
    FluxVars flux;flux.init(*this,e,fv,ev,f,fc);qv=flux.advectiveFlux(liq,[](const auto& w){return w.mobility(liq);});
    for(int ph=0;ph<2;++ph){
     wa+=flux.advectiveFlux(ph,[ph](const auto& w){return w.mobility(ph)*w.molarDensity(ph)*w.moleFraction(ph,water);});
     sa+=flux.advectiveFlux(ph,[ph](const auto& w){return w.mobility(ph)*w.molarDensity(ph)*w.moleFraction(ph,salt);});
     heat+=flux.advectiveFlux(ph,[ph](const auto& w){return w.mobility(ph)*w.density(ph)*w.enthalpy(ph);});
     auto d=flux.molecularDiffusionFlux(ph);
     if constexpr(FluxVars::MolecularDiffusionType::referenceSystemFormulation()==ReferenceSystemFormulation::massAveraged){wd+=d[water]/FS::molarMass(water);sd+=d[salt]/FS::molarMass(salt);}else{wd+=d[water];sd+=d[salt];}
    }
    heat+=flux.heatConductionFlux();
   }
   if(cut){outward[mat][0]+=wa+wd;outward[mat][1]+=sa+sd;outward[mat][2]+=heat;}
   if(kind>=0){
    const std::array<double,7> values{qv,wa,wd,sa,sd,heat,area};auto& row=gross[kind*3+mat];
    for(int k=0;k<7;++k){row[2*k]+=std::max(values[k],0.);row[2*k+1]-=std::min(values[k],0.);}
    if(maps)faces<<kind<<','<<mat<<','<<pos[0]<<','<<pos[1]<<','<<pos[2]<<','<<area<<','<<qv<<','<<wa<<','<<wd<<','<<sa<<','<<sd<<','<<heat<<','<<v.pressure(liq)<<','<<v.temperature()<<','<<donor<<'\n';
   }
  }
 }
 if(mapsOnly)return;
 if(!campaignInitialized_){campaignInitial_=inventory;campaignPrevious_=inventory;campaignInitialized_=true;}
 if(!campaignParts_.is_open()){
  campaignParts_.open("material_budgets.csv");campaignParts_<<std::setprecision(17)<<"time_s,evaporation_h,dt_s,impulse,material,water_mol,salt_mol,energy_J,water_out_mol_s,salt_out_mol_s,energy_out_W,water_residual_mol,salt_residual_mol,energy_residual_J\n";
  campaignFlux_.open("native_fluxes.csv");campaignFlux_<<std::setprecision(17)<<"time_s,dt_s,kind,material,qv_out,qv_in,water_adv_out,water_adv_in,water_diff_out,water_diff_in,salt_adv_out,salt_adv_in,salt_diff_out,salt_diff_in,energy_out,energy_in,area_m2,unused\n";
 }
 for(int m=0;m<3;++m){
  std::array<double,3> res{};
  for(int k=0;k<3;++k){if(impulse)campaignImpulse_[m][k]+=inventory[m][k]-campaignPrevious_[m][k];else campaignIntegral_[m][k]+=dt*outward[m][k];res[k]=inventory[m][k]-campaignInitial_[m][k]+campaignIntegral_[m][k]-campaignImpulse_[m][k];
   if(std::abs(res[k])>1e-6*std::max(std::abs(campaignInitial_[m][k]),k==2?1.:1e-12))DUNE_THROW(Dune::InvalidStateException,"Sand/filter material water/salt/energy closure failed");}
  campaignParts_<<time<<','<<(time-pre_)/3600<<','<<dt<<','<<impulse<<','<<m;for(auto v:inventory[m])campaignParts_<<','<<v;for(auto v:outward[m])campaignParts_<<','<<v;for(auto v:res)campaignParts_<<','<<v;campaignParts_<<'\n';
 }
 campaignPrevious_=inventory;campaignParts_.flush();
 for(int kind=0;kind<6;++kind)for(int mat=0;mat<3;++mat){const auto& row=gross[kind*3+mat];if(row[12]==0)continue;campaignFlux_<<time<<','<<dt<<','<<kind<<','<<mat;for(auto v:row)campaignFlux_<<','<<v;campaignFlux_<<'\n';}campaignFlux_.flush();
}
private:
 bool campaignInitialized_=false;
 std::array<std::array<double,3>,3> campaignInitial_{},campaignPrevious_{},campaignIntegral_{},campaignImpulse_{};
 std::ofstream campaignParts_,campaignFlux_;
public:
