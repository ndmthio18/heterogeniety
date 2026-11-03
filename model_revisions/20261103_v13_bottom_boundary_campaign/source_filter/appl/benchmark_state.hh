#ifndef HETEROGENEITY_PERFORMANCE_STATE_HH
#define HETEROGENEITY_PERFORMANCE_STATE_HH
#include <fstream>
#include <iomanip>
#include <chrono>
#include <cmath>
#include <string>
#include <stdexcept>
// Exact primary-variable snapshots for isolated performance segments only.
// Cumulative budgets are reset and are intentionally NOT production restarts.
namespace PerformanceBenchmark {
inline double now(){return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();}
struct Header { double time=0;bool seeded=false;std::size_t cells=0;int equations=0;};
inline Header header(const std::string& path){
 Header h;if(path.empty())return h;std::ifstream f(path);std::string magic;int thermal=-1;
 f>>magic>>thermal>>h.time>>h.seeded>>h.cells>>h.equations;
 if(!f||magic!="PERF_SEGMENT_V1"||thermal!=NONISOTHERMAL||!std::isfinite(h.time)||h.time<0)throw std::runtime_error("Invalid performance snapshot header");
 return h;
}
template<class SV>void read(const std::string& path,SV& x,const Header& h){
 if(path.empty())return;
 if(h.cells!=x.size()||x.size()==0||h.equations!=x[0].size())throw std::runtime_error("Snapshot grid/equation size mismatch");
 std::ifstream f(path);std::string line;std::getline(f,line);
 for(auto& v:x){int phase;f>>phase;if(phase<1||phase>3)throw std::runtime_error("Invalid snapshot phase state");v.setState(phase);for(auto& a:v){f>>a;if(!std::isfinite(a))throw std::runtime_error("Invalid snapshot primary variable");}}
 if(!f)throw std::runtime_error("Incomplete snapshot");std::string extra;if(f>>extra)throw std::runtime_error("Extra snapshot data");
}
template<class SV>void write(const std::string& path,const SV& x,double time,bool seeded){
 if(path.empty())return;std::ofstream f(path);f<<std::setprecision(17)<<"PERF_SEGMENT_V1 "<<NONISOTHERMAL<<" "<<time<<" "<<seeded<<" "<<x.size()<<" "<<x[0].size()<<"\n";
 for(const auto& v:x){f<<v.state();for(const auto& a:v)f<<" "<<a;f<<"\n";}if(!f)throw std::runtime_error("Cannot write performance snapshot");
}
}
#endif
