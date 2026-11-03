#include <config.h>
#include <fstream>
#include <iostream>
#include <memory>
#include <dune/common/parallel/mpihelper.hh>
#include "properties.hh"
#include <dumux/common/parameters.hh>
#include <dumux/io/grid/gridmanager.hh>
int main(int argc,char** argv)try{
 using namespace Dumux;using Tag=Properties::TTag::TYPETAG;
 Dune::MPIHelper::instance(argc,argv);Parameters::init(argc,argv);
 GridManager<GetPropType<Tag,Properties::Grid>> manager;manager.init();
 using GG=GetPropType<Tag,Properties::GridGeometry>;using Problem=GetPropType<Tag,Properties::Problem>;
 using GV=GetPropType<Tag,Properties::GridVariables>;using SV=GetPropType<Tag,Properties::SolutionVector>;
 using Ind=typename GetPropType<Tag,Properties::ModelTraits>::Indices;
 auto gg=std::make_shared<GG>(manager.grid().leafGridView());auto p=std::make_shared<Problem>(gg);
 auto clock=std::make_shared<CheckPointTimeLoop<double>>(0,1,1e7);p->setTimeLoop(clock);
 SV x(gg->numDofs());p->applyInitialSolution(x);auto gv=std::make_shared<GV>(p,gg);gv->init(x);
 double time;int n;
 while(std::cin>>time>>n){
  if(n!=x.size())throw std::runtime_error("State size mismatch");
  for(int i=0;i<n;++i){int id,state;double pressure,sw,salt,solid;std::cin>>id>>state>>pressure>>sw>>salt>>solid;
   if(!std::cin||id<0||id>=n||(state!=Ind::firstPhaseOnly&&state!=Ind::bothPhases))throw std::runtime_error("Invalid replay state");
   x[id].setState(state);x[id][Ind::pressureIdx]=pressure;x[id][Ind::switchIdx]=sw;x[id][2]=salt;x[id][3]=solid;
  }
  clock=std::make_shared<CheckPointTimeLoop<double>>(time,1,time+1);p->setTimeLoop(clock);gv->update(x);
  const auto a=p->audit(x,*gv);p->writeFaceAudit(x,*gv,time);
  std::cout<<std::setprecision(17)<<"REPLAY_OK "<<time<<' '<<a.n[0]<<' '<<a.n[2]<<' '<<a.coarse<<' '<<a.fine<<' '<<a.bottomCoarse<<' '<<a.bottomFine<<' '<<a.interfaceAdv<<' '<<a.interfaceDiff<<std::endl;
 }
 return 0;
}catch(const std::exception& e){std::cerr<<"REPLAY_FAILURE "<<e.what()<<std::endl;return 1;}
