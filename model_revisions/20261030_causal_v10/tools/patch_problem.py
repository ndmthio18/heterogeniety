"""One-shot patch of the copied v08 problem.hh into the v10 causal problem (CRLF-aware)."""
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_bytes().decode()
assert '\r\n' in s
def rep(a,b,count=1):
    global s
    a=a.replace('\n','\r\n');b=b.replace('\n','\r\n')
    assert s.count(a)==count,(s.count(a),a[:200]);s=s.replace(a,b)
rep('#include "phase_equilibrium.hh"\n','#include "phase_equilibrium.hh"\n#include "causal_switches.hh"\n#include <algorithm>\n#include <string>\n#include <vector>\n')
# Audit structure
rep('''  double smin=1,pmin=1,precip=0,cmax=0;
 };''','''  double smin=1,pmin=1,precip=0,cmax=0;
  // v10 causal diagnostics. Side 0=F36 coarse (x<=split), 1=W3 fine.
  // Interface fluxes are coarse->fine positive, [mode adv/diff][component][band].
  std::array<std::array<double,3>,2> sideN{},sideBoundaryOut{},sideBottomOut{},sideBottomOutPos{},sideBottomOutNeg{},sideTopOut{};
  std::array<std::array<double,5>,2> bandSalt{},bandDissolved{},bandWater{},bandLiquidVolume{};
  std::array<std::array<std::array<double,4>,3>,2> ifNet{},ifPos{},ifNeg{};
  std::array<double,4> ifVolNet{},ifVolPos{},ifVolNeg{};
  std::vector<double> planeAdv,planeAdvDown,planeDiff;
  std::size_t interfaceFaces=0;
 };''')
# Constructor: switches, reference, geometry of diagnostics
rep('''  if(supply_!="DistributedReservoir")DUNE_THROW(Dune::InvalidStateException,"Cylinder requires registered distributed supply; 2D slit is not a 3D aperture");''','''  initCausal_(*gg);
  if(supply_!="DistributedReservoir")DUNE_THROW(Dune::InvalidStateException,"Cylinder requires registered distributed supply; 2D slit is not a 3D aperture");''')
# Bottom boundary: same buoyancy convention as interior Darcy faces
rep('''   auto rhoFace=(rhoRes_+v.density(liq))/2;''','''   // v10: buoyancy density (exactly the actual density for lambda=1).
   auto rhoFace=(rhoRes_+v.buoyancyDensity(liq))/2;''')
# Audit signature (flux diagnostics optional for seed bisection)
rep(''' template<class GV>Audit audit(const SV& x,const GV& gv)const {
  Audit a;''',''' template<class GV>Audit audit(const SV& x,const GV& gv,bool fluxes=true)const {
  Audit a;a.planeAdv.assign(2*planeY_.size(),0.);a.planeAdvDown=a.planeAdv;a.planeDiff=a.planeAdv;''')
rep('''    a.dissolved+=nd;a.solid+=ns;(scv.center()[0]<split_?a.coarse:a.fine)+=nd+ns;''','''    a.dissolved+=nd;a.solid+=ns;(scv.center()[0]<split_?a.coarse:a.fine)+=nd+ns;
    {const int side=cellSide_[scv.dofIndex()];
     for(int ph=0;ph<2;++ph)for(int k=0;k<3;++k)a.sideN[side][k]+=volume*v.porosity()*v.saturation(ph)*v.molarDensity(ph)*v.moleFraction(ph,k);
     a.sideN[side][salt]+=ns;
     const double liquidVolume=volume*v.porosity()*v.saturation(liq),liquidWater=liquidVolume*v.molarDensity(liq)*v.moleFraction(liq,water);
     for(int b=0;b<5;++b){const double w=cellBand_[scv.dofIndex()][b];if(w==0)continue;
      a.bandSalt[side][b]+=w*(nd+ns);a.bandDissolved[side][b]+=w*nd;a.bandWater[side][b]+=w*liquidWater;a.bandLiquidVolume[side][b]+=w*liquidVolume;}}''')
rep('''     auto q=neumann(e,fv,ev,fc,face);auto factor=face.area()*ev[face.insideScvIdx()].extrusionFactor();
     for(int k=0;k<3;++k)a.out[k]+=q[k]*factor;''','''     auto q=neumann(e,fv,ev,fc,face);auto factor=face.area()*ev[face.insideScvIdx()].extrusionFactor();
     for(int k=0;k<3;++k)a.out[k]+=q[k]*factor;
     {const int side=cellSide_[fv.scv(face.insideScvIdx()).dofIndex()];
      const bool isTop=face.ipGlobal()[1]>this->gridGeometry().bBoxMax()[1]-1e-9,isBottom=face.ipGlobal()[1]<this->gridGeometry().bBoxMin()[1]+1e-9;
      for(int k=0;k<3;++k){const double r=q[k]*factor;a.sideBoundaryOut[side][k]+=r;
       if(isTop)a.sideTopOut[side][k]+=r;
       if(isBottom){a.sideBottomOut[side][k]+=r;(r>0?a.sideBottomOutPos:a.sideBottomOutNeg)[side][k]+=r;}}}''')
rep('''      if constexpr(FluxVars::MolecularDiffusionType::referenceSystemFormulation()==ReferenceSystemFormulation::massAveraged)a.interfaceDiff+=d[salt]/FS::molarMass(salt);
      else a.interfaceDiff+=d[salt];
     }
    }
   }''','''      if constexpr(FluxVars::MolecularDiffusionType::referenceSystemFormulation()==ReferenceSystemFormulation::massAveraged)a.interfaceDiff+=d[salt]/FS::molarMass(salt);
      else a.interfaceDiff+=d[salt];
     }
    }
    if(fluxes&&!face.boundary())causalInteriorFace_(a,e,fv,ev,fc,face);
   }''')
rep(''' void initializeBudget(const Audit& a){initial_=a.n;initialParts_={a.coarse,a.fine};}''',''' void initializeBudget(const Audit& a){initial_=a.n;initialParts_={a.coarse,a.fine};initialSide_=a.sideN;}''')
# record: causal budget before the existing gate, side gate after it
rep('''  auto tol=getParam<Scalar>("Revision.MaxBudgetRelativeResidual",.001);
  if(std::abs(rw)>tol*initial_[water]||std::abs(rs)>tol*initial_[salt])DUNE_THROW(Dune::InvalidStateException,"Budget residual exceeds registered gate");''','''  const auto sideResidual=recordCausal_(a,time,dt);
  auto tol=getParam<Scalar>("Revision.MaxBudgetRelativeResidual",.001);
  if(std::abs(rw)>tol*initial_[water]||std::abs(rs)>tol*initial_[salt])DUNE_THROW(Dune::InvalidStateException,"Budget residual exceeds registered gate");
  for(int s=0;s<2;++s)if(std::abs(sideResidual[s][water])>tol*initialSide_[s][water]||std::abs(sideResidual[s][salt])>tol*initialSide_[s][salt])
   DUNE_THROW(Dune::InvalidStateException,"v10 side budget residual exceeds registered gate");''')
# seed: inventories only in bisection; record side/band impulses
rep('''  auto total=[&](Scalar shift){for(std::size_t i=0;i<x.size();++i){candidate[i]=x[i];candidate[i][salt]+=noise[i]-shift;}gv.update(candidate);return audit(candidate,gv).n[salt];};''','''  auto total=[&](Scalar shift){for(std::size_t i=0;i<x.size();++i){candidate[i]=x[i];candidate[i][salt]+=noise[i]-shift;}gv.update(candidate);return audit(candidate,gv,false).n[salt];};''')
rep('''  out<<"],\\"partition_impulses_mol\\":["<<impulseParts_[0]<<','<<impulseParts_[1]<<"]}\\n";return true;''','''  out<<"],\\"partition_impulses_mol\\":["<<impulseParts_[0]<<','<<impulseParts_[1]<<"]";
  // v10: per-side component and per-band salt impulses (same seed definition).
  out<<",\\"side_component_impulses_mol\\":[";
  for(int s=0;s<2;++s){out<<(s?",[":"[");for(int k=0;k<3;++k){sideImpulse_[s][k]+=after.sideN[s][k]-before.sideN[s][k];out<<(k?",":"")<<after.sideN[s][k]-before.sideN[s][k];}out<<"]";}
  out<<"],\\"band_salt_impulses_mol\\":[";
  for(int s=0;s<2;++s){out<<(s?",[":"[");for(int b=0;b<5;++b)out<<(b?",":"")<<after.bandSalt[s][b]-before.bandSalt[s][b];out<<"]";}
  out<<"]}\\n";return true;''')
# public hooks + private helpers
rep(''' const std::string& name()const{return name_;}''',''' const std::string& name()const{return name_;}
 // v10: true only for interior faces between the two materials when the
 // interface exchange switch is off. Material is the spatial-parameter rule.
 template<class FVG,class F>bool interfaceExchangeBlocked(const FVG& fv,const F& f)const{
  if(interfaceExchange_||f.boundary())return false;
  return isCoarse_(fv.scv(f.insideScvIdx()).center())!=isCoarse_(fv.scv(f.outsideScvIdx()).center());
 }
 bool interfaceExchangeEnabled()const{return interfaceExchange_;}
 Scalar salinityBuoyancyScale()const{return lambda_;}
 template<class P>bool isCoarse(const P& p)const{return isCoarse_(p);}
 // Bottom hydraulic driving potential (Pa) with an explicit buoyancy scale; the
 // solver applies the configured scale in neumann().
 template<class V,class P>Scalar bottomDriving(const V& v,const P& pos,const P& center,Scalar lambda)const{
  auto pExt=patm_+rhoRes_*9.81*(level_-pos[1]);
  auto rhoFace=(rhoRes_+v.scaledBuoyancyDensity(liq,lambda))/2;
  return v.pressure(liq)-pExt+rhoFace*9.81*(center[1]-pos[1]);
 }''')
rep('''private:
 Scalar gasWaterMassFraction_(Scalar y)const''','''private:
 template<class P>bool isCoarse_(const P& p)const{return p[0]<=split_;}
 template<std::size_t N>static std::array<double,N> bandFractions_(const std::array<double,N+1>& edges,double lo,double hi){
  std::array<double,N> w{};for(std::size_t b=0;b<N;++b)w[b]=std::max(0.,std::min(hi,edges[b+1])-std::max(lo,edges[b]))/(hi-lo);return w;
 }
 std::size_t planeIndex_(double y)const{
  auto it=std::lower_bound(planeY_.begin(),planeY_.end(),y-1e-12);
  if(it==planeY_.end()||std::abs(*it-y)>1e-12)DUNE_THROW(Dune::InvalidStateException,"Horizontal face outside registered planes");
  return std::size_t(it-planeY_.begin());
 }
 void initCausal_(const GG& gg){
  interfaceExchange_=HeterogeneityCausal::Switches::interfaceExchange();lambda_=HeterogeneityCausal::Switches::buoyancyScale();
  HeterogeneityCausal::BuoyancyReference::set({{double(reservoir_.moleFraction(liq,0)),double(reservoir_.moleFraction(liq,1)),double(reservoir_.moleFraction(liq,2))}});
  top_=gg.bBoxMax()[1];cellSide_.assign(gg.numDofs(),0);cellBand_.assign(gg.numDofs(),{});
  std::vector<double> levels;std::size_t materialFaces=0,geometricFaces=0,mismatch=0,centresOnSplit=0;double area=0;
  for(const auto& e:elements(gg.gridView())){
   auto fv=localView(gg);fv.bind(e);const auto g=e.geometry();
   double lo=1e9,hi=-1e9;for(int i=0;i<g.corners();++i){lo=std::min(lo,double(g.corner(i)[1]));hi=std::max(hi,double(g.corner(i)[1]));}
   for(const auto& scv:scvs(fv)){
    cellSide_[scv.dofIndex()]=isCoarse_(scv.center())?0:1;cellBand_[scv.dofIndex()]=bandFractions_<5>(inventoryEdges_,top_-hi,top_-lo);
    if(std::abs(scv.center()[0]-split_)<1e-12)++centresOnSplit;
   }
   for(const auto& f:scvfs(fv)){
    if(f.boundary())continue;
    const bool a=isCoarse_(fv.scv(f.insideScvIdx()).center()),b=isCoarse_(fv.scv(f.outsideScvIdx()).center()),geo=std::abs(f.ipGlobal()[0]-split_)<1e-9;
    if(a&&!b){++materialFaces;area+=f.area();}
    if(geo&&fv.scv(f.insideScvIdx()).center()[0]<split_)++geometricFaces;
    if((a!=b)!=geo)++mismatch;
    if(f.unitOuterNormal()[1]<-.99)levels.push_back(f.ipGlobal()[1]);
   }
  }
  std::sort(levels.begin(),levels.end());
  for(auto y:levels)if(planeY_.empty()||y-planeY_.back()>1e-12)planeY_.push_back(y);
  if(mismatch||centresOnSplit||materialFaces!=geometricFaces||materialFaces==0)
   DUNE_THROW(Dune::InvalidStateException,"Material-interface faces do not coincide with the geometric split plane");
  interfaceFaces_=materialFaces;interfaceArea_=area;
  std::ofstream out("causal_switches.json");out<<std::setprecision(17)<<"{\\"InterfaceExchangeEnabled\\":"<<(interfaceExchange_?"true":"false")
   <<",\\"SalinityBuoyancyScale\\":"<<lambda_<<",\\"reference_liquid_mole_fractions_water_air_NaCl\\":["<<reservoir_.moleFraction(liq,0)<<','<<reservoir_.moleFraction(liq,1)<<','<<reservoir_.moleFraction(liq,2)
   <<"],\\"reference_molarity_mol_L\\":"<<reservoir_.moleFraction(liq,salt)*molarRes_/1000<<",\\"reference_density_at_patm_T_kg_m3\\":"<<rhoRes_
   <<",\\"buoyancy_density\\":\\"liquid: rho_ref(p_liq,T,x_ref)+lambda*(rho-rho_ref); lambda=1 uses the upstream law and actual rho; gas phase actual density\\""
   <<",\\"interface_rule\\":\\"interior face with cells in different materials (x<=split coarse) has zero Darcy flux of both phases and zero Fickian flux of all components when disabled\\""
   <<",\\"interface_faces\\":"<<interfaceFaces_<<",\\"interface_area_m2\\":"<<interfaceArea_<<",\\"split_m\\":"<<split_
   <<",\\"side_convention\\":\\"0=F36 coarse x<=split, 1=W3 fine\\",\\"interface_sign\\":\\"positive coarse to fine\\",\\"inventory_band_edges_depth_m\\":[";
  for(std::size_t i=0;i<inventoryEdges_.size();++i)out<<(i?",":"")<<inventoryEdges_[i];
  out<<"],\\"interface_band_edges_depth_m\\":[";for(std::size_t i=0;i<interfaceEdges_.size();++i)out<<(i?",":"")<<interfaceEdges_[i];
  out<<"],\\"horizontal_plane_depths_m\\":[";for(std::size_t i=0;i<planeY_.size();++i)out<<(i?",":"")<<top_-planeY_[i];out<<"]}\\n";
  std::cout<<std::setprecision(17)<<"CAUSAL_SWITCHES interface_exchange="<<interfaceExchange_<<" salinity_buoyancy_scale="<<lambda_<<" interface_faces="<<interfaceFaces_<<" interface_area_m2="<<interfaceArea_<<" planes="<<planeY_.size()<<std::endl;
 }
 template<class EV_,class FC_>void causalInteriorFace_(Audit& a,const Elem& e,const FV& fv,const EV_& ev,const FC_& fc,const Face& face)const{
  const auto& inside=fv.scv(face.insideScvIdx());const auto& outside=fv.scv(face.outsideScvIdx());
  const bool inC=isCoarse_(inside.center()),outC=isCoarse_(outside.center()),across=inC&&!outC,plane=face.unitOuterNormal()[1]<-.99;
  if(!across&&!plane)return;
  FluxVars flux;flux.init(*this,e,fv,ev,face,fc);
  std::array<double,3> adv{},dif{};
  for(int ph=0;ph<2;++ph){
   const auto d=flux.molecularDiffusionFlux(ph);
   for(int k=0;k<3;++k){
    adv[k]+=flux.advectiveFlux(ph,[ph,k](const auto& v){return v.molarDensity(ph)*v.moleFraction(ph,k)*v.mobility(ph);});
    if constexpr(FluxVars::MolecularDiffusionType::referenceSystemFormulation()==ReferenceSystemFormulation::massAveraged)dif[k]+=d[k]/FS::molarMass(k);
    else dif[k]+=d[k];
   }
  }
  if(across){
   ++a.interfaceFaces;
   const double volume=flux.advectiveFlux(liq,[](const auto& v){return v.mobility(liq);});
   const auto g=fv.geometry(face);double lo=1e9,hi=-1e9;
   for(int i=0;i<g.corners();++i){lo=std::min(lo,double(g.corner(i)[1]));hi=std::max(hi,double(g.corner(i)[1]));}
   const auto w=bandFractions_<4>(interfaceEdges_,top_-hi,top_-lo);
   for(int b=0;b<4;++b){if(w[b]==0)continue;
    for(int m=0;m<2;++m)for(int k=0;k<3;++k){const double F=w[b]*(m?dif[k]:adv[k]);a.ifNet[m][k][b]+=F;(F>0?a.ifPos:a.ifNeg)[m][k][b]+=F;}
    const double F=w[b]*volume;a.ifVolNet[b]+=F;(F>0?a.ifVolPos:a.ifVolNeg)[b]+=F;
   }
  }
  if(plane){
   const std::size_t i=(inC?0:1)*planeY_.size()+planeIndex_(face.ipGlobal()[1]);
   a.planeAdv[i]+=adv[salt];a.planeAdvDown[i]+=std::max(0.,adv[salt]);a.planeDiff[i]+=dif[salt];
  }
 }
 std::array<std::array<double,3>,2> recordCausal_(const Audit& a,Scalar time,Scalar dt){
  static const char* side[2]={"F36","W3"};static const char* comp[3]={"water","air","salt"};static const char* mode[2]={"adv","diff"};
  static const char* inv[5]={"0_2","2_3","3_10","10_20","20_40"};static const char* ifb[4]={"0_2","2_10","10_20","20_40"};
  if(!causalCsv_.is_open()){
   causalCsv_.open("causal_budget.csv");causalCsv_<<std::setprecision(17)<<"time_s,evaporation_time_h,dt_s,interface_faces_evaluated";
   for(int s=0;s<2;++s){
    for(int k=0;k<3;++k)causalCsv_<<','<<side[s]<<'_'<<comp[k]<<"_mol";
    for(int k=0;k<3;++k)causalCsv_<<','<<side[s]<<"_bottom_"<<comp[k]<<"_in_mol_s,"<<side[s]<<"_top_"<<comp[k]<<"_out_mol_s,"<<side[s]<<"_boundary_"<<comp[k]<<"_out_mol_s";
    for(int k=0;k<3;++k)causalCsv_<<','<<side[s]<<"_cum_bottom_"<<comp[k]<<"_in_mol,"<<side[s]<<"_cum_bottom_"<<comp[k]<<"_gross_in_mol,"<<side[s]<<"_cum_bottom_"<<comp[k]<<"_gross_out_mol,"<<side[s]<<"_cum_top_"<<comp[k]<<"_out_mol,"<<side[s]<<"_cum_boundary_"<<comp[k]<<"_out_mol";
    for(int k=0;k<3;++k)causalCsv_<<','<<side[s]<<"_residual_"<<comp[k]<<"_mol";
    for(int b=0;b<5;++b)causalCsv_<<','<<side[s]<<"_salt_mol_"<<inv[b]<<"mm,"<<side[s]<<"_dissolved_salt_mol_"<<inv[b]<<"mm,"<<side[s]<<"_liquid_water_mol_"<<inv[b]<<"mm,"<<side[s]<<"_liquid_volume_m3_"<<inv[b]<<"mm";
   }
   for(int m=0;m<2;++m)for(int k=0;k<3;++k)for(int b=0;b<4;++b){const auto n=std::string("if_")+mode[m]+"_"+comp[k]+"_"+ifb[b]+"mm";causalCsv_<<','<<n<<"_mol_s,"<<n<<"_cum_net_mol,"<<n<<"_cum_pos_mol,"<<n<<"_cum_neg_mol";}
   for(int b=0;b<4;++b){const auto n=std::string("if_liquid_volume_")+ifb[b]+"mm";causalCsv_<<','<<n<<"_m3_s,"<<n<<"_cum_net_m3,"<<n<<"_cum_pos_m3,"<<n<<"_cum_neg_m3";}
   causalCsv_<<'\\n';
   planeCsv_.open("vertical_salt_flux.csv");planeCsv_<<std::setprecision(17)<<"time_s,evaporation_time_h,dt_s";
   for(int s=0;s<2;++s)for(std::size_t l=0;l<planeY_.size();++l){const auto d=std::to_string(std::lround((top_-planeY_[l])*1e7));
    planeCsv_<<','<<side[s]<<"_adv_down_net_mol_s_d"<<d<<','<<side[s]<<"_adv_down_gross_mol_s_d"<<d<<','<<side[s]<<"_diff_down_net_mol_s_d"<<d;}
   planeCsv_<<'\\n';
  }
  for(int s=0;s<2;++s)for(int k=0;k<3;++k){
   cumSideBoundaryOut_[s][k]+=dt*a.sideBoundaryOut[s][k];cumSideBottomOut_[s][k]+=dt*a.sideBottomOut[s][k];cumSideTopOut_[s][k]+=dt*a.sideTopOut[s][k];
   cumSideBottomOutPos_[s][k]+=dt*a.sideBottomOutPos[s][k];cumSideBottomOutNeg_[s][k]+=dt*a.sideBottomOutNeg[s][k];
  }
  for(int m=0;m<2;++m)for(int k=0;k<3;++k)for(int b=0;b<4;++b){cumIfNet_[m][k][b]+=dt*a.ifNet[m][k][b];cumIfPos_[m][k][b]+=dt*a.ifPos[m][k][b];cumIfNeg_[m][k][b]+=dt*a.ifNeg[m][k][b];}
  for(int b=0;b<4;++b){cumIfVolNet_[b]+=dt*a.ifVolNet[b];cumIfVolPos_[b]+=dt*a.ifVolPos[b];cumIfVolNeg_[b]+=dt*a.ifVolNeg[b];}
  std::array<std::array<double,3>,2> residual{};
  for(int k=0;k<3;++k){double I=0;for(int m=0;m<2;++m)for(int b=0;b<4;++b)I+=cumIfNet_[m][k][b];
   for(int s=0;s<2;++s)residual[s][k]=a.sideN[s][k]-initialSide_[s][k]+cumSideBoundaryOut_[s][k]+(s==0?I:-I)-sideImpulse_[s][k];}
  causalCsv_<<time<<','<<(time-pre_)/3600<<','<<dt<<','<<a.interfaceFaces;
  for(int s=0;s<2;++s){
   for(int k=0;k<3;++k)causalCsv_<<','<<a.sideN[s][k];
   for(int k=0;k<3;++k)causalCsv_<<','<<-a.sideBottomOut[s][k]<<','<<a.sideTopOut[s][k]<<','<<a.sideBoundaryOut[s][k];
   for(int k=0;k<3;++k)causalCsv_<<','<<-cumSideBottomOut_[s][k]<<','<<-cumSideBottomOutNeg_[s][k]<<','<<cumSideBottomOutPos_[s][k]<<','<<cumSideTopOut_[s][k]<<','<<cumSideBoundaryOut_[s][k];
   for(int k=0;k<3;++k)causalCsv_<<','<<residual[s][k];
   for(int b=0;b<5;++b)causalCsv_<<','<<a.bandSalt[s][b]<<','<<a.bandDissolved[s][b]<<','<<a.bandWater[s][b]<<','<<a.bandLiquidVolume[s][b];
  }
  for(int m=0;m<2;++m)for(int k=0;k<3;++k)for(int b=0;b<4;++b)causalCsv_<<','<<a.ifNet[m][k][b]<<','<<cumIfNet_[m][k][b]<<','<<cumIfPos_[m][k][b]<<','<<cumIfNeg_[m][k][b];
  for(int b=0;b<4;++b)causalCsv_<<','<<a.ifVolNet[b]<<','<<cumIfVolNet_[b]<<','<<cumIfVolPos_[b]<<','<<cumIfVolNeg_[b];
  causalCsv_<<'\\n';causalCsv_.flush();
  planeCsv_<<time<<','<<(time-pre_)/3600<<','<<dt;
  for(std::size_t i=0;i<a.planeAdv.size();++i)planeCsv_<<','<<a.planeAdv[i]<<','<<a.planeAdvDown[i]<<','<<a.planeDiff[i];
  planeCsv_<<'\\n';planeCsv_.flush();
  return residual;
 }
 Scalar gasWaterMassFraction_(Scalar y)const''')
rep(''' double cumAdv_=0,cumDiff_=0;std::ofstream csv_;
};''',''' double cumAdv_=0,cumDiff_=0;std::ofstream csv_;
 // v10 causal state
 bool interfaceExchange_=true;Scalar lambda_=1;double top_=0,interfaceArea_=0;std::size_t interfaceFaces_=0;
 const std::array<double,6> inventoryEdges_{{0,.002,.003,.010,.020,.040}};
 const std::array<double,5> interfaceEdges_{{0,.002,.010,.020,.040}};
 std::vector<int> cellSide_;std::vector<std::array<double,5>> cellBand_;std::vector<double> planeY_;
 std::array<std::array<double,3>,2> initialSide_{},sideImpulse_{},cumSideBoundaryOut_{},cumSideBottomOut_{},cumSideTopOut_{},cumSideBottomOutPos_{},cumSideBottomOutNeg_{};
 std::array<std::array<std::array<double,4>,3>,2> cumIfNet_{},cumIfPos_{},cumIfNeg_{};
 std::array<double,4> cumIfVolNet_{},cumIfVolPos_{},cumIfVolNeg_{};
 std::ofstream causalCsv_,planeCsv_;
};''')
p.write_bytes(s.encode());print('patched',p)
