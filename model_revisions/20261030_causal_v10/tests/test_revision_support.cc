#include "../source/appl/revision_support.hh"
#include "../source/appl/water_activity.hh"
#include <limits>
#include <cassert>
#include <cstdio>
#include <iostream>
int main(){
 using namespace HeterogeneityRevision;
 const char* p="forcing_test_intervals.txt";
 {std::ofstream f(p);f<<"# start end flux\n0 10 2\n10 20 5\n20 30 1\n";}
 WaterFluxSeries s;s.load(p);
 assert(std::abs(s.integral(5,25)-65)<1e-12);
 assert(std::abs(s.integral(0,30)-s.integral(0,7)-s.integral(7,13)-s.integral(13,30))<1e-12);
 assert(std::abs(s.integral(12,14)/2-5)<1e-12);
 bool rejected=false;try{s.integral(0,31);}catch(const std::runtime_error&){rejected=true;}assert(rejected);
 assert(donorComponentFlux(-2,10,.1,20,.3)==-2);
 assert(donorComponentFlux(2,10,.1,20,.3)==12);
 assert(std::abs(fineFluxMultiplier(1.2,.5)-.8)<1e-14);
 assert(std::abs(fineFluxMultiplier(.8,.5)-1.2)<1e-14);
 double weighted=0;for(int i=0;i<7;++i){double a=i*.05/7,b=(i+1)*.05/7;weighted+=(b-a)*faceWaterMultiplier(1.2,.8,a,b,.025);}
 assert(std::abs(weighted-.05)<1e-14);
 bool negative=false;try{fineFluxMultiplier(3,.5);}catch(const std::runtime_error&){negative=true;}assert(negative);
 assert(naclWaterActivity(0,.01801518)==1);
 // Independent external scale check: near-saturated (~6 m) NaCl has aw ~0.76.
 assert(naclWaterActivity(6,.01801518)>.75&&naclWaterActivity(6,.01801518)<.77);
 for(double m=.01;m<=6;m+=.01)assert(naclWaterActivity(m,.01801518)<naclWaterActivity(m-.01,.01801518));
 const auto weights=normalizedEvaporationWeights({.98,.90,.82},{1.,2.,3.},.4);
 assert(std::abs(weights[0]+2*weights[1]+3*weights[2]-6)<1e-14);
 assert(weights[0]>weights[1]&&weights[1]>weights[2]);
 const auto equal=normalizedEvaporationWeights({.9,.9},{1.,7.},0.);
 assert(std::abs(equal[0]-1)<1e-14&&std::abs(equal[1]-1)<1e-14);
 for(double bad:{-1.,6.1,std::numeric_limits<double>::quiet_NaN()}){
  bool caught=false;try{naclWaterActivity(bad,.01801518);}catch(const std::runtime_error&){caught=true;}assert(caught);
 }
 bool condense=false;try{normalizedEvaporationWeights({.8,.9},{1.,2.},.85);}catch(const std::runtime_error&){condense=true;}assert(condense);
 std::remove(p);std::cout<<"PASS intervals, retry coverage, donor reversal, fixed-total partition, NaCl activity domain/scale/monotonicity, area normalization, uniform limit, condensation rejection\n";
}
