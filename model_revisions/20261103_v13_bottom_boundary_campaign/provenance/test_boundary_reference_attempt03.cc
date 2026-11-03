#include <config.h>
#include <fstream>
#include <iostream>
#include <memory>
#include <dumux/common/initialize.hh>
#include "properties.hh"
#include <dumux/io/grid/gridmanager.hh>
int main(int argc,char**argv)try{
 using namespace Dumux;using Tag=Properties::TTag::TYPETAG;Dumux::initialize(argc,argv);Parameters::init(argc,argv);
 using GG=GetPropType<Tag,Properties::GridGeometry>;using Problem=GetPropType<Tag,Properties::Problem>;using GV=GetPropType<Tag,Properties::GridVariables>;using SV=GetPropType<Tag,Properties::SolutionVector>;using FS=GetPropType<Tag,Properties::FluidSystem>;
 GridManager<GetPropType<Tag,Properties::Grid>> manager;manager.init();auto gg=std::make_shared<GG>(manager.grid().leafGridView());auto p=std::make_shared<Problem>(gg);
 auto clock=std::make_shared<CheckPointTimeLoop<double>>(0,1,2);p->setTimeLoop(clock);SV x(gg->numDofs());p->applyInitialSolution(x);auto gv=std::make_shared<GV>(p,gg);gv->init(x);
 std::vector<std::array<double,3>> port;bool filter=getParam<bool>("Revision.ExplicitFilter",false);if(filter){std::ifstream f(getParam<std::string>("Revision.PortAreaFile"));double a,b,c;while(f>>a>>b>>c)port.push_back({a,b,c});}
 std::array<bool,2>done{};int probes=0;double activeArea=0,bottomArea=0,maxHydro=0,maxDonor=0,maxHeat=0;
 for(const auto&e:elements(gg->gridView())){
  auto fv=localView(*gg);fv.bind(e);auto ev=localView(gv->curGridVolVars());ev.bind(e,fv,x);auto fc=localView(gv->gridFluxVarsCache());fc.bind(e,fv,ev);
  for(const auto&f:scvfs(fv))if(f.boundary()&&f.ipGlobal()[1]<gg->bBoxMin()[1]+1e-9){
   double fraction=1;if(filter){fraction=-1;for(const auto& row:port)if(std::hypot(f.ipGlobal()[0]-row[0],f.ipGlobal()[2]-row[1])<1e-10){fraction=row[2];break;}if(fraction<0)throw std::runtime_error("Unmatched port face");}
   bottomArea+=f.area();activeArea+=fraction*f.area();auto hydro=p->neumann(e,fv,ev,fc,f);maxHydro=std::max(maxHydro,std::abs(hydro[0])+std::abs(hydro[2]));
   int side=f.ipGlobal()[0]<.025?0:1;if(fraction==0||done[side])continue;done[side]=true;
   auto initial=ev[f.insideScvIdx()];int id=fv.scv(f.insideScvIdx()).dofIndex();
   for(double pressureChange:{-5000.,5000.}){
    SV trial=x;trial[id][0]+=pressureChange;trial[id][2]*=1.5;gv->update(trial);auto tv=localView(gv->curGridVolVars());tv.bind(e,fv,trial);auto tc=localView(gv->gridFluxVarsCache());tc.bind(e,fv,tv);const auto&v=tv[f.insideScvIdx()];auto q=p->neumann(e,fv,tv,tc,f);
    bool incoming=pressureChange<0;double sum=q[0]+q[1]+q[2];if((sum<0)!=incoming)throw std::runtime_error("Incorrect donor direction");
    auto rs=initial.fluidState();for(int ph=0;ph<2;++ph){rs.setPressure(ph,getParam<double>("Reservoir.AtmosphericPressure"));rs.setTemperature(ph,getParam<double>("Reservoir.Temperature"));}
    double molar=incoming?FS::molarDensity(rs,0):v.molarDensity(0);double density=incoming?FS::density(rs,0):v.density(0);double enthalpy=incoming?FS::enthalpy(rs,0):v.enthalpy(0);
    double xs=incoming?rs.moleFraction(0,2):v.moleFraction(0,2);double qv=sum/molar;double expected=qv*molar*xs;double de=std::abs(q[2]-expected)/std::max(std::abs(expected),1e-15);maxDonor=std::max(maxDonor,de);
    double energy=qv*density*enthalpy;double he=std::abs(q[4]-energy)/std::max(std::abs(energy),1e-12);maxHeat=std::max(maxHeat,he);
    std::cout<<"DONOR_PROBE side="<<side<<" incoming="<<incoming<<" salt_error="<<de<<" heat_error="<<he<<std::endl;
    if(de>1e-8||he>1e-8)throw std::runtime_error("Donor salt or heat mismatch");++probes;gv->update(x);
   }
  }
 }
 if(probes!=4||maxHydro>1e-8)throw std::runtime_error("Probe coverage or hydrostatic flux failed");
 std::ofstream out("boundary_selftest.json");out<<std::setprecision(17)<<"{\"passed\":true,\"probes\":"<<probes<<",\"bottom_area_m2\":"<<bottomArea<<",\"port_area_m2\":"<<activeArea<<",\"max_hydrostatic_component_flux\":"<<maxHydro<<",\"max_donor_relative_error\":"<<maxDonor<<",\"max_heat_relative_error\":"<<maxHeat<<"}\n";
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}
