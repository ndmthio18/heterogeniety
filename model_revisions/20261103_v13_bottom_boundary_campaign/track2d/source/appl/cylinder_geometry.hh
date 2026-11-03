#ifndef HETEROGENEITY_CYLINDER_GEOMETRY_HH
#define HETEROGENEITY_CYLINDER_GEOMETRY_HH
#include <cmath>
#include <dumux/discretization/cellcentered/tpfa/fvgridgeometry.hh>
namespace Dumux {
// The mesh consists of extruded cyclic triangles/isoceles trapezoids.
// Their circumcentres, with horizontal-face circumcentres as integration
// points, give an orthogonal TPFA dual for scalar permeability/diffusion.
// Actual primal volumes, areas and normals remain those supplied by UGGrid.
template<class Geometry> auto cylinderCircumcentre(const Geometry& g) {
 auto c=g.center(); double best=0; auto a=g.corner(0),b=a,d=a;
 for(int j=1;j<g.corners();++j)for(int k=j+1;k<g.corners();++k){
  const auto p=g.corner(j)-a,q=g.corner(k)-a;
  const auto det=p[0]*q[2]-p[2]*q[0];
  if(std::abs(det)>std::abs(best)){best=det;b=p;d=q;}
 }
 if(std::abs(best)<1e-20)DUNE_THROW(Dune::InvalidStateException,"Degenerate cylinder cross-section");
 const auto rb=(b[0]*b[0]+b[2]*b[2])/2,rd=(d[0]*d[0]+d[2]*d[2])/2;
 c[0]=a[0]+(rb*d[2]-b[2]*rd)/best;
 c[2]=a[2]+(b[0]*rd-rb*d[0])/best;
 return c;
}
template<class GV> class CylinderScv:public CCSubControlVolume<GV>{
 using Base=CCSubControlVolume<GV>;using Geometry=typename Base::Traits::Geometry;
 using Index=typename Base::Traits::GridIndexType;
 typename Base::GlobalPosition position_;
public:
 CylinderScv()=default;
 CylinderScv(Geometry&& g,Index i):Base(std::move(g),i),position_(cylinderCircumcentre(Base::geometry())){}
 const auto& center()const{return position_;}
 const auto& dofPosition()const{return position_;}
};
template<class GV> class CylinderScvf:public CCTpfaSubControlVolumeFace<GV>{
 using Base=CCTpfaSubControlVolumeFace<GV>;using Index=typename Base::Traits::GridIndexType;
 using Storage=typename Base::Traits::GridIndexStorage;
 typename Base::GlobalPosition position_;
public:
 CylinderScvf()=default;
 template<class Intersection> CylinderScvf(const Intersection& is,const typename Intersection::Geometry& g,Index i,const Storage& indices,bool boundary)
 :Base(is,g,i,indices,boundary),position_(g.center()){
  if(std::abs(Base::unitOuterNormal()[1])>.99)position_=cylinderCircumcentre(g);
 }
 const auto& center()const{return position_;}
 const auto& ipGlobal()const{return position_;}
};
template<class GV>struct CylinderGeometryTraits:public CCTpfaDefaultGridGeometryTraits<GV>{
 using SubControlVolume=CylinderScv<GV>;
 using SubControlVolumeFace=CylinderScvf<GV>;
};
}
#endif
