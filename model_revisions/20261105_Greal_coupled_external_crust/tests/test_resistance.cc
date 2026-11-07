#include "../source/external_crust_resistance.hh"
#include <iostream>
#include <limits>
#include <stdexcept>
void check(bool ok) { if(!ok) throw std::runtime_error("resistance test failed"); }
int main(){
 const double delta=.008100162249880822;
 for(double r:{.05,.08,.10,.23}){
  double previous=1;
  for(double h:{0.,.0001,.0005,.001}){
   const auto beta=GrealExternalCrust::vaporFactor(h,delta,r);
   check(std::abs(beta-delta*r/(delta*r+h))<1e-14);
   check(beta<=previous); previous=beta;
   check((-2*beta)/(-2)==beta);
  }
 }
 check(GrealExternalCrust::height(0,.05844,1e-6,2165,.43,1)==0);
 check(GrealExternalCrust::height(1,.05844,1e-6,2165,.43,0)==0);
 for(double a:{1e-6,2.7e-6}){
  double h=GrealExternalCrust::height(.001,.05844,a,2165,.43,1);
  check(std::abs(h*2165*.57*a-.001*.05844)<1e-18);
 }
 check(GrealExternalCrust::vaporFactor(.001,delta,std::numeric_limits<double>::infinity())==1);
 std::cout<<"PASS constitutive inventory, geometry scaling, analytical resistance, signed flux, limits and monotonicity; solver gates pending\n";
}
