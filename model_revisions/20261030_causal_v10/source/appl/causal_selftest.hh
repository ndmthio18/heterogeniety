#ifndef HETEROGENEITY_CAUSAL_SELFTEST_HH
#define HETEROGENEITY_CAUSAL_SELFTEST_HH
// Revision.CausalSelfTest=true: deterministic checks of both switches on the
// production mesh, using the flux laws, assembler and Jacobian of the solver.
// Writes causal_selftest.json and returns nonzero on failure. No time loop.
#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <string>
#include <vector>
#include "causal_switches.hh"
namespace HeterogeneityCausal {
template<class TypeTag,class Problem,class GG,class GV,class Assembler,class SV>
int selfTest(const Problem& problem,const GG& gg,GV& gv,Assembler& assembler,const SV& x0){
 using namespace Dumux;
 using FS=GetPropType<TypeTag,Properties::FluidSystem>;
 using FluxVars=GetPropType<TypeTag,Properties::FluxVariables>;
 using Darcy=GetPropType<TypeTag,Properties::AdvectionType>;
 constexpr int liq=FS::liquidPhaseIdx,salt=FS::NaClIdx,pIdx=0;
 const auto begin=std::chrono::steady_clock::now();
 const double pi=std::acos(-1.);
 const bool exchange=problem.interfaceExchangeEnabled();const double lambda=problem.salinityBuoyancyScale();
 auto wave=[&](const auto& c,double a,double b,double d,double phase){return std::sin(2*pi*((c[0]-.025)/a+c[1]/b+c[2]/d)+phase);};
 // xU: hydrostatic 1 M initial state; xP: same pressures, strongly non-uniform
 // salinity (+-30 %); xF: xP plus a +-20 Pa pressure pattern driving flow.
 SV xU=x0,xP=x0,xF=x0;
 for(const auto& e:elements(gg.gridView())){auto fv=localView(gg);fv.bindElement(e);
  for(const auto& scv:scvs(fv)){const auto c=scv.center();const auto i=scv.dofIndex();
   xP[i][salt]*=1+.3*wave(c,.013,.017,.011,.3);xF[i][salt]=xP[i][salt];xF[i][pIdx]+=20*wave(c,.021,.009,.015,1.1);}}
 struct FaceFlux{double causal,upstream,scaled0,scaled1;bool across,bottom;double driving0,driving1;};
 auto evaluate=[&](const SV& x){
  gv.update(x);std::vector<FaceFlux> out;
  for(const auto& e:elements(gg.gridView())){
   auto fv=localView(gg);fv.bind(e);auto ev=localView(gv.curGridVolVars());ev.bind(e,fv,x);auto fc=localView(gv.gridFluxVarsCache());fc.bind(e,fv,ev);
   for(const auto& f:scvfs(fv)){
    FaceFlux r{0,0,0,0,false,false,0,0};
    if(f.boundary()){
     if(f.ipGlobal()[1]<gg.bBoxMin()[1]+1e-9){const auto& v=ev[f.insideScvIdx()];const auto c=fv.scv(f.insideScvIdx()).center();
      r.bottom=true;r.driving0=problem.bottomDriving(v,f.ipGlobal(),c,0.);r.driving1=problem.bottomDriving(v,f.ipGlobal(),c,1.);out.push_back(r);}
     continue;
    }
    r.across=problem.isCoarse(fv.scv(f.insideScvIdx()).center())!=problem.isCoarse(fv.scv(f.outsideScvIdx()).center());
    r.causal=Darcy::flux(problem,e,fv,ev,f,liq,fc);r.upstream=Darcy::upstreamFlux(problem,e,fv,ev,f,liq,fc);
    r.scaled0=Darcy::scaledFlux(problem,e,fv,ev,f,liq,fc,0.);r.scaled1=Darcy::scaledFlux(problem,e,fv,ev,f,liq,fc,1.);
    out.push_back(r);
   }
  }
  return out;
 };
 const auto U=evaluate(xU),P=evaluate(xP),F=evaluate(xF);
 double upstreamScale=0,reimplementation=0,salinity0=0,salinity1=0,uniform01=0,bottom0=0,bottom1=0;std::size_t configuredMismatch=0,blockedNonzero=0,faces=0;
 for(std::size_t i=0;i<U.size();++i){
  if(U[i].bottom){bottom0=std::max(bottom0,std::abs(P[i].driving0-U[i].driving0));bottom1=std::max(bottom1,std::abs(P[i].driving1-U[i].driving1));continue;}
  ++faces;upstreamScale=std::max(upstreamScale,std::abs(F[i].upstream));
  reimplementation=std::max(reimplementation,std::abs(F[i].scaled1-F[i].upstream));
  salinity0=std::max(salinity0,std::abs(P[i].scaled0-U[i].scaled0));salinity1=std::max(salinity1,std::abs(P[i].scaled1-U[i].scaled1));
  uniform01=std::max(uniform01,std::abs(U[i].scaled0-U[i].scaled1));
  for(const auto* s:{&U[i],&P[i],&F[i]}){
   const double expected=(!exchange&&s->across)?0.:(lambda==1.?s->upstream:(lambda==0.?s->scaled0:std::nan("")));
   if(!(s->causal==expected))++configuredMismatch;
   if(!exchange&&s->across&&s->causal!=0.)++blockedNonzero;
  }
 }
 // Offline interface fluxes at the flowing state, through FluxVariables.
 gv.update(xF);double interfaceAdv=0,interfaceDiff=0,otherAdv=0,otherDiff=0;std::size_t interfaceFaces=0;double interfaceArea=0;
 std::vector<std::pair<std::size_t,std::size_t>> pairs;
 for(const auto& e:elements(gg.gridView())){
  auto fv=localView(gg);fv.bind(e);auto ev=localView(gv.curGridVolVars());ev.bind(e,fv,xF);auto fc=localView(gv.gridFluxVarsCache());fc.bind(e,fv,ev);
  for(const auto& f:scvfs(fv)){
   if(f.boundary())continue;
   const auto& in=fv.scv(f.insideScvIdx());const auto& out=fv.scv(f.outsideScvIdx());
   const bool across=problem.isCoarse(in.center())&&!problem.isCoarse(out.center());
   FluxVars flux;flux.init(problem,e,fv,ev,f,fc);double adv=0,dif=0;
   for(int ph=0;ph<2;++ph){adv=std::max(adv,std::abs(flux.advectiveFlux(ph,[](const auto&){return 1.;})));
    const auto d=flux.molecularDiffusionFlux(ph);for(int k=0;k<3;++k)dif=std::max(dif,std::abs(double(d[k])));}
   if(across){++interfaceFaces;interfaceArea+=f.area();interfaceAdv=std::max(interfaceAdv,adv);interfaceDiff=std::max(interfaceDiff,dif);pairs.emplace_back(in.dofIndex(),out.dofIndex());}
   else{otherAdv=std::max(otherAdv,adv);otherDiff=std::max(otherDiff,dif);}
  }
 }
 // Jacobian blocks between the two sides of every interface face.
 // The cached grid variables must hold the state, as Newton ensures in the solver.
 assembler.setLinearSystem();gv.update(xF);assembler.assembleJacobianAndResidual(xF);
 const auto& J=assembler.jacobian();double jacobianInterface=0,jacobianOther=0;
 auto blockMax=[](const auto& block){double m=0;for(const auto& row:block)for(const auto& v:row)m=std::max(m,std::abs(double(v)));return m;};
 for(const auto& [i,j]:pairs){
  if(J.exists(i,j))jacobianInterface=std::max(jacobianInterface,blockMax(J[i][j]));
  if(J.exists(j,i))jacobianInterface=std::max(jacobianInterface,blockMax(J[j][i]));
 }
 std::vector<int> side(gg.numDofs());
 for(const auto& e:elements(gg.gridView())){auto fv=localView(gg);fv.bindElement(e);for(const auto& scv:scvs(fv))side[scv.dofIndex()]=problem.isCoarse(scv.center())?0:1;}
 for(auto row=J.begin();row!=J.end();++row)for(auto col=row->begin();col!=row->end();++col)
  if(col.index()!=row.index()&&side[row.index()]==side[col.index()])jacobianOther=std::max(jacobianOther,blockMax(*col));
 // Residual of one side must be invariant to arbitrary changes on the other.
 auto residual=[&](const SV& x){gv.update(x);assembler.assembleResidual(x);return assembler.residual();};
 const auto R=residual(xF);double crossChange[2]={0,0},ownChange[2]={0,0};
 for(int perturbed=0;perturbed<2;++perturbed){
  SV x=xF;
  for(const auto& e:elements(gg.gridView())){auto fv=localView(gg);fv.bindElement(e);
   for(const auto& scv:scvs(fv))if(side[scv.dofIndex()]==perturbed){const auto c=scv.center();
    x[scv.dofIndex()][salt]*=1+.05*wave(c,.007,.013,.019,.7);x[scv.dofIndex()][pIdx]+=30*wave(c,.011,.023,.009,2.);}}
  const auto R2=residual(x);
  for(std::size_t i=0;i<R.size();++i)for(std::size_t k=0;k<R[i].size();++k){
   const double d=std::abs(double(R2[i][k]-R[i][k]));
   if(side[i]==perturbed)ownChange[perturbed]=std::max(ownChange[perturbed],d);else crossChange[perturbed]=std::max(crossChange[perturbed],d);
  }
 }
 gv.update(x0);
 bool pass=true;std::vector<std::string> failures;
 auto require=[&](bool ok,const char* what){if(!ok){pass=false;failures.push_back(what);}};
 require(configuredMismatch==0,"runtime law differs from configured switch definition");
 require(reimplementation<=1e-13*upstreamScale,"scaled-law reimplementation at lambda=1 differs from upstream Darcy law");
 require(salinity0==0.,"lambda=0 Darcy flux depends on salinity at fixed pressure");
 require(salinity1>0.,"lambda=1 Darcy flux does not respond to salinity (test has no power)");
 require(bottom0==0.&&bottom1>0.,"bottom driving potential violates lambda convention");
 require(interfaceArea>0&&std::abs(interfaceArea-.002)<1e-10,"interface area differs from 0.002 m2");
 require(otherAdv>0&&otherDiff>0&&jacobianOther>0,"non-interface fluxes/Jacobian unexpectedly zero");
 if(exchange){
  require(interfaceAdv>0&&interfaceDiff>0&&jacobianInterface>0,"connected interface shows no coupling");
  require(crossChange[0]>0&&crossChange[1]>0,"connected sides show no residual coupling");
 }else{
  require(blockedNonzero==0&&interfaceAdv==0.&&interfaceDiff==0.,"blocked interface has nonzero flux");
  require(jacobianInterface==0.,"blocked interface has nonzero Jacobian coupling");
  require(crossChange[0]==0.&&crossChange[1]==0.,"blocked sides remain residual-coupled");
 }
 const double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
 std::ofstream o("causal_selftest.json");o<<std::setprecision(17)<<"{\"status\":\""<<(pass?"passed":"failed")<<"\",\"InterfaceExchangeEnabled\":"<<(exchange?"true":"false")<<",\"SalinityBuoyancyScale\":"<<lambda
  <<",\"interior_face_orientations\":"<<faces<<",\"interface_faces\":"<<interfaceFaces<<",\"interface_area_m2\":"<<interfaceArea
  <<",\"configured_law_mismatches\":"<<configuredMismatch<<",\"blocked_faces_nonzero\":"<<blockedNonzero
  <<",\"max_abs_upstream_liquid_darcy_flux\":"<<upstreamScale<<",\"max_abs_reimplementation_minus_upstream_lambda1\":"<<reimplementation
  <<",\"max_abs_salinity_response_lambda0\":"<<salinity0<<",\"max_abs_salinity_response_lambda1\":"<<salinity1<<",\"max_abs_lambda0_minus_lambda1_uniform_1M\":"<<uniform01
  <<",\"max_abs_bottom_driving_salinity_response_lambda0_Pa\":"<<bottom0<<",\"max_abs_bottom_driving_salinity_response_lambda1_Pa\":"<<bottom1
  <<",\"max_abs_interface_advective_flux\":"<<interfaceAdv<<",\"max_abs_interface_diffusive_flux\":"<<interfaceDiff<<",\"max_abs_other_advective_flux\":"<<otherAdv<<",\"max_abs_other_diffusive_flux\":"<<otherDiff
  <<",\"max_abs_jacobian_interface_blocks\":"<<jacobianInterface<<",\"max_abs_jacobian_same_side_offdiagonal_blocks\":"<<jacobianOther
  <<",\"max_abs_fine_residual_change_when_coarse_perturbed\":"<<crossChange[0]<<",\"max_abs_coarse_residual_change_when_fine_perturbed\":"<<crossChange[1]
  <<",\"max_abs_own_residual_change\":["<<ownChange[0]<<','<<ownChange[1]<<"],\"states\":\"xU hydrostatic 1M; xP salinity*(1+0.3 wave); xF xP + 20 Pa pressure wave\",\"seconds\":"<<seconds<<",\"failures\":[";
 for(std::size_t i=0;i<failures.size();++i)o<<(i?",":"")<<'"'<<failures[i]<<'"';
 o<<"]}\n";o.close();
 std::cout<<"CAUSAL_SELFTEST "<<(pass?"passed":"failed")<<std::endl;
 return pass?0:3;
}
}
#endif
