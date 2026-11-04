#ifndef HETEROGENEITY_REVISION_SUPPORT_HH
#define HETEROGENEITY_REVISION_SUPPORT_HH
#include <algorithm>
#include <cmath>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace HeterogeneityRevision {
struct WaterInterval { double start,end,flux; };
class WaterFluxSeries {
public:
 void load(const std::string& path) {
  std::ifstream f(path);if(!f)throw std::runtime_error("Cannot open forcing: "+path);
  std::string line;
  while(std::getline(f,line)) {
   if(line.empty()||line[0]=='#')continue;
   std::istringstream s(line);WaterInterval r;
   if(!(s>>r.start>>r.end>>r.flux))throw std::runtime_error("Malformed forcing");
   if(!(r.end>r.start)||r.flux<0||!std::isfinite(r.flux))throw std::runtime_error("Invalid forcing");
   if(!rows_.empty()&&std::abs(r.start-rows_.back().end)>1e-7)throw std::runtime_error("Noncontiguous forcing");
   rows_.push_back(r);
  }
  if(rows_.empty()||std::abs(rows_[0].start)>1e-8)throw std::runtime_error("Declare forcing t=0 assumption");
 }
 double integral(double a,double b)const {
  if(!(b>=a)||a<0||rows_.empty()||b>rows_.back().end+1e-7)throw std::runtime_error("Forcing outside coverage");
  double sum=0;for(const auto& r:rows_)sum+=std::max(0.0,std::min(b,r.end)-std::max(a,r.start))*r.flux;return sum;
 }
 std::vector<double> events()const {std::vector<double> v;for(const auto& r:rows_)v.push_back(r.end);return v;}
private:std::vector<WaterInterval> rows_;
};
inline double donorComponentFlux(double q,double rhoIn,double xIn,double rhoInside,double xInside)
{return q<0?q*rhoIn*xIn:q*rhoInside*xInside;}
inline double fineFluxMultiplier(double coarseMultiplier,double coarseAreaFraction)
{
 if(!std::isfinite(coarseMultiplier)||coarseMultiplier<0||!(coarseAreaFraction>0&&coarseAreaFraction<1))throw std::runtime_error("Invalid water-flux partition");
 auto result=(1-coarseAreaFraction*coarseMultiplier)/(1-coarseAreaFraction);
 if(result<0)throw std::runtime_error("Water-flux partition would require negative evaporation");
 return result;
}
inline double faceWaterMultiplier(double coarseMultiplier,double fineMultiplier,double left,double right,double split)
{
 if(!(right>left))throw std::runtime_error("Invalid face interval");
 auto fraction=std::max(0.,std::min(right,split)-left)/(right-left);
 return fraction*coarseMultiplier+(1-fraction)*fineMultiplier;
}
}
#endif
