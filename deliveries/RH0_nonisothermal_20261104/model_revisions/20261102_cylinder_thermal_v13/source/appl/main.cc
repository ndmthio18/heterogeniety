#include <config.h>
#include <algorithm>
#include <fstream>
#include <iostream>
#include <memory>
#include <dune/common/parallel/mpihelper.hh>
#include "properties.hh"
#include <dumux/common/parameters.hh>
#include <dumux/linear/amgbackend.hh>
#include <dumux/linear/linearsolvertraits.hh>
#include <dumux/nonlinear/newtonsolver.hh>
#include <dumux/assembly/fvassembler.hh>
#include <dumux/assembly/diffmethod.hh>
#include <dumux/io/vtkoutputmodule.hh>
#include <dumux/io/grid/gridmanager.hh>
#include "geometry_audit.hh"
#include "hydraulic_selftest.hh"
int main(int argc,char** argv)try{
 using namespace Dumux;using Tag=Properties::TTag::TYPETAG;
 const auto& mpi=Dune::MPIHelper::instance(argc,argv);
 if(mpi.size()!=1)DUNE_THROW(Dune::InvalidStateException,"Serial diagnostic revision: MPI budget reduction not implemented");
 Parameters::init(argc,argv);GridManager<GetPropType<Tag,Properties::Grid>> manager;manager.init();const auto& view=manager.grid().leafGridView();
 using GG=GetPropType<Tag,Properties::GridGeometry>;using Problem=GetPropType<Tag,Properties::Problem>;
 using GV=GetPropType<Tag,Properties::GridVariables>;using SV=GetPropType<Tag,Properties::SolutionVector>;using Scalar=GetPropType<Tag,Properties::Scalar>;
 auto gg=std::make_shared<GG>(view);auditCylinderGeometry(*gg);auto problem=std::make_shared<Problem>(gg);
 auto dt=getParam<Scalar>("TimeLoop.DtInitial",10),end=getParam<Scalar>("TimeLoop.TEnd"),maxDt=getParam<Scalar>("TimeLoop.MaxTimeStepSize",300);
 auto clock=std::make_shared<CheckPointTimeLoop<Scalar>>(0,dt,end);clock->setMaxTimeStepSize(maxDt);problem->setTimeLoop(clock);
 // This dependency version does not pop an explicit checkpoint when it
 // coincides with a periodic one. Use one sorted, duplicate-free queue.
 auto events=problem->forcingEvents();
 const auto outputInterval=getParam<Scalar>("TimeLoop.CheckpointOutputInterval",600);
 if(outputInterval<=0)DUNE_THROW(Dune::InvalidStateException,"Output interval must be positive");
 for(Scalar t=outputInterval;t<end;t+=outputInterval)events.push_back(t);
 events.push_back(end);std::sort(events.begin(),events.end());
 events.erase(std::unique(events.begin(),events.end(),[](auto a,auto b){return std::abs(a-b)<1e-7;}),events.end());
 for(auto t:events)if(t>0&&t<=end)clock->setCheckPoint(t);
 SV x(gg->numDofs());problem->applyInitialSolution(x);auto old=x;auto gv=std::make_shared<GV>(problem,gg);gv->init(x);
 if(getParam<bool>("Revision.HydraulicSelfTest",false))return HeterogeneityFixed::selfTest<Tag>(*problem,*gg,x);
 using Fields=GetPropType<Tag,Properties::IOFields>;VtkOutputModule<GV,SV> vtk(*gv,x,problem->name());
 Fields::initOutputModule(vtk);
 vtk.addField(problem->getPermeability(),"Permeability");
 vtk.addField(problem->getDiagnosticVelocity(),"velocity_liq_interior_LS (m/s)");
 vtk.addField(problem->getDofIds(),"dof_id");
 problem->updateVtkOutput(x);problem->updateDiagnosticVelocity(x,*gv);vtk.write(0);
 problem->prepareEvaporation(x,*gv);
 auto initial=problem->audit(x,*gv);problem->initializeBudget(initial);problem->record(initial,0,0);
 using Assembler=FVAssembler<Tag,DiffMethod::numeric>;auto assembler=std::make_shared<Assembler>(problem,gg,gv,clock,old);
 using Linear=AMGBiCGSTABBackend<LinearSolverTraits<GG>>;auto linear=std::make_shared<Linear>(view,gg->dofMapper());NewtonSolver<Assembler,Linear> newton(assembler,linear);
 {std::ofstream p("effective_parameters.txt");auto* oldBuffer=std::cout.rdbuf(p.rdbuf());Parameters::print();std::cout.rdbuf(oldBuffer);}
 bool seeded=false,stop=false;clock->start();
 while(!clock->finished()){
  if(!(clock->timeStepSize()>0))DUNE_THROW(Dune::InvalidStateException,"Nonpositive time step before Newton solve");
  problem->prepareEvaporation(x,*gv);
  assembler->setPreviousSolution(old);newton.solve(x,*clock);
  const auto acceptedDt=clock->timeStepSize(),acceptedTime=clock->time()+acceptedDt;
  auto a=problem->audit(x,*gv);problem->record(a,acceptedTime,acceptedDt);
  gv->advanceTimeStep();clock->advanceTimeStep();
  if(!seeded&&clock->time()>=problem->preDuration()-1e-8&&!clock->finished()){
   seeded=true;if(problem->seed(x,*gv))gv->advanceTimeStep();
  }
  old=x;stop=getParam<bool>("Revision.StopOnPrecipitation",true)&&a.precip>1e-8;
  if(clock->isCheckPoint()||clock->finished()||stop){problem->updateVtkOutput(x);problem->updateDiagnosticVelocity(x,*gv);vtk.write(clock->time());}
  clock->reportTimeStep();if(stop)break;clock->setTimeStepSize(std::min(maxDt,acceptedDt*1.5));
 }
 std::ofstream state("run_status.json");state<<std::setprecision(17)<<"{\"status\":\""<<(stop?"stopped_at_precipitation":"completed")<<"\",\"time_s\":"<<clock->time()<<",\"evaporation_time_h\":"<<(clock->time()-problem->preDuration())/3600<<"}\n";
 Parameters::print();return 0;
}catch(const std::exception& e){std::ofstream f("run_status.json");f<<"{\"status\":\"failed\"}\n";std::cerr<<"REVISED_FAILURE "<<e.what()<<std::endl;return 1;}
