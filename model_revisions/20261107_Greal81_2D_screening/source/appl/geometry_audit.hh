#ifndef HETEROGENEITY_GEOMETRY_AUDIT_HH
#define HETEROGENEITY_GEOMETRY_AUDIT_HH
#include <cmath>
#include <fstream>
#include <iomanip>
#include <dumux/common/parameters.hh>

// Audit physical extruded 2D control volumes, not unit-depth UGGrid geometry.
template<class GG>void auditCylinderGeometry(const GG& gg){
 const double extrusion=Dumux::getParam<double>("Geometry.ExtrusionWidth",.05);
 const double split=Dumux::getParam<double>("SpatialParams.SplitCoordinate",.5*(gg.bBoxMin()[0]+gg.bBoxMax()[0]));
 const bool primary=Dumux::getParam<bool>("Geometry.PrimaryEquivalent",true);
 const double sandBottom=0.;
 double volume=0,sandVolume=0,filterVolume=0,coarseSand=0,top=0,bottom=0,wall=0,contact=0,filterCross=0,minVolume=1,maxSin=0,minDistance=1,maxLinearError=0;
 std::ofstream cells("cell_geometry.csv");cells<<std::setprecision(17)<<"dof,x_m,y_m,z_m,volume_m3,ymin_m,ymax_m\n";
 for(const auto& e:elements(gg.gridView())){
  auto fv=localView(gg);fv.bind(e);const auto& scv=fv.scv(gg.elementMapper().index(e));
  auto g=e.geometry();const auto c=scv.center();const auto v=scv.volume()*extrusion;
  double lo=1,hi=-1;for(int i=0;i<g.corners();++i){lo=std::min(lo,double(g.corner(i)[1]));hi=std::max(hi,double(g.corner(i)[1]));}
  cells<<scv.dofIndex()<<','<<c[0]<<','<<c[1]<<','<<0.0<<','<<v<<','<<lo<<','<<hi<<'\n';
  volume+=v;minVolume=std::min(minVolume,v);
  if(c[1]>=sandBottom-1e-12){sandVolume+=v;if(c[0]<split)coarseSand+=v;}else filterVolume+=v;
  for(const auto& f:scvfs(fv)){
   auto d=f.ipGlobal()-c;const auto n=f.unitOuterNormal();const auto normal=d*n;minDistance=std::min(minDistance,double(normal));
   auto tangent=d;tangent.axpy(-normal,n);maxSin=std::max(maxSin,double(tangent.two_norm()/d.two_norm()));
   for(int k=0;k<2;++k)maxLinearError=std::max(maxLinearError,std::abs(double(normal/d.two_norm2()*d[k]-n[k])));
   const auto physicalArea=f.area()*extrusion;
   if(f.boundary()){
    if(f.ipGlobal()[1]>gg.bBoxMax()[1]-1e-9)top+=physicalArea;
    else if(f.ipGlobal()[1]<gg.bBoxMin()[1]+1e-9)bottom+=physicalArea;else wall+=physicalArea;
   }else if(c[0]<split&&std::abs(f.ipGlobal()[0]-split)<1e-9){
    if(f.ipGlobal()[1]>=sandBottom-1e-12)contact+=physicalArea;else filterCross+=physicalArea;
   }
  }
 }
 const double pi=std::acos(-1.),R=.025,H=.04;
 const double targetSandVolume=pi*R*R*H,targetTopArea=pi*R*R,expectedContact=extrusion*H;
 std::ofstream out("geometry_audit.json");out<<std::setprecision(17)
  <<"{\"dimension\":2,\"primary_equivalent\":"<<(primary?"true":"false")
  <<",\"extrusion_width_m\":"<<extrusion<<",\"cells\":"<<gg.numDofs()
  <<",\"volume_m3\":"<<volume<<",\"sand_volume_m3\":"<<sandVolume<<",\"filter_volume_m3\":"<<filterVolume
  <<",\"coarse_sand_volume_m3\":"<<coarseSand<<",\"top_area_m2\":"<<top<<",\"bottom_area_m2\":"<<bottom
  <<",\"wall_area_m2\":"<<wall<<",\"direct_sand_interface_area_m2\":"<<contact<<",\"filter_cross_area_m2\":"<<filterCross
  <<",\"target_3d_sand_volume_m3\":"<<targetSandVolume<<",\"target_3d_top_area_m2\":"<<targetTopArea
  <<",\"min_cell_volume_m3\":"<<minVolume<<",\"min_normal_distance_m\":"<<minDistance
  <<",\"max_nonorthogonality_sin\":"<<maxSin<<",\"max_affine_flux_error\":"<<maxLinearError<<"}\n";out.close();
 const bool equivalent=std::abs(sandVolume-targetSandVolume)<1e-12&&std::abs(top-targetTopArea)<1e-12;
 const bool interfaceOk=std::abs(contact-expectedContact)<1e-12&&(!primary||std::abs(contact-.002)<1e-12);
 if(extrusion<=0||minVolume<=0||minDistance<=0||maxSin>1e-8||maxLinearError>1e-8||!equivalent||!interfaceOk||std::abs(coarseSand/sandVolume-.5)>1e-10)
  DUNE_THROW(Dune::InvalidStateException,"Extruded 2D geometry/orthogonality gate failed; see geometry_audit.json");
}
#endif
