#ifndef HETEROGENEITY_GEOMETRY_AUDIT_HH
#define HETEROGENEITY_GEOMETRY_AUDIT_HH
#include <fstream>
#include <iomanip>
template<class GG>void auditCylinderGeometry(const GG& gg){
 double volume=0,coarse=0,top=0,bottom=0,wall=0,contact=0,minVolume=1,maxSin=0,minDistance=1,maxLinearError=0;
 std::ofstream cells("cell_geometry.csv");cells<<std::setprecision(17)<<"dof,x_m,y_m,z_m,volume_m3,ymin_m,ymax_m\n";
 for(const auto& e:elements(gg.gridView())){
  auto fv=localView(gg);fv.bind(e);const auto& scv=fv.scv(gg.elementMapper().index(e));
  auto g=e.geometry();const auto c=scv.center();const auto v=scv.volume();
  double lo=1,hi=-1;for(int i=0;i<g.corners();++i){lo=std::min(lo,g.corner(i)[1]);hi=std::max(hi,g.corner(i)[1]);}
  cells<<scv.dofIndex()<<','<<c[0]<<','<<c[1]<<','<<c[2]<<','<<v<<','<<lo<<','<<hi<<'\n';
  volume+=v;coarse+=c[0]<.025?v:0;minVolume=std::min(minVolume,v);
  for(const auto& f:scvfs(fv)){
   auto d=f.ipGlobal()-c;const auto n=f.unitOuterNormal();const auto normal=d*n;minDistance=std::min(minDistance,normal);
   auto tangent=d;tangent.axpy(-normal,n);maxSin=std::max(maxSin,tangent.two_norm()/d.two_norm());
   // Unit scalar coefficient: one-sided TPFA flux must reproduce every
   // affine field component at the integration point.
   for(int k=0;k<3;++k)maxLinearError=std::max(maxLinearError,std::abs(normal/d.two_norm2()*d[k]-n[k]));
   if(f.boundary()){
    if(f.ipGlobal()[1]>.04-1e-9)top+=f.area();
    else if(f.ipGlobal()[1]<gg.bBoxMin()[1]+1e-9)bottom+=f.area();else wall+=f.area();
   }else if(c[0]<.025&&std::abs(f.ipGlobal()[0]-.025)<1e-9)contact+=f.area();
  }
 }
 std::ofstream out("geometry_audit.json");out<<std::setprecision(17)<<"{\"cells\":"<<gg.numDofs()<<",\"volume_m3\":"<<volume<<",\"coarse_volume_m3\":"<<coarse<<",\"top_area_m2\":"<<top<<",\"bottom_area_m2\":"<<bottom<<",\"wall_area_m2\":"<<wall<<",\"interface_area_m2\":"<<contact<<",\"min_cell_volume_m3\":"<<minVolume<<",\"min_normal_distance_m\":"<<minDistance<<",\"max_nonorthogonality_sin\":"<<maxSin<<",\"max_affine_flux_error\":"<<maxLinearError<<"}\n";out.close();
 if(minVolume<=0||minDistance<=0||maxSin>1e-8||maxLinearError>1e-8||std::abs(contact-.05*(gg.bBoxMax()[1]-gg.bBoxMin()[1]))>1e-10||std::abs(coarse/volume-.5)>1e-10)
  DUNE_THROW(Dune::InvalidStateException,"Cylinder geometry/orthogonality gate failed; see geometry_audit.json");
}
#endif
