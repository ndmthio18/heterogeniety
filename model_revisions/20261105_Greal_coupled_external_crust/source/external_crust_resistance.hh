#ifndef GREAL_EXTERNAL_CRUST_RESISTANCE_HH
#define GREAL_EXTERNAL_CRUST_RESISTANCE_HH
#include <cmath>
#include <stdexcept>

namespace GrealExternalCrust {
// Pure constitutive helpers. Not yet wired into or validated with DuMuX.
inline double height(double solidMoles, double molarMass, double area,
                     double crystalDensity, double porosity, double alpha)
{
    if (!(solidMoles >= 0 && molarMass > 0 && area > 0 && crystalDensity > 0
          && porosity >= 0 && porosity < 1 && alpha >= 0 && alpha <= 1))
        throw std::domain_error("Invalid external crust inventory or geometry");
    return alpha*solidMoles*molarMass/(crystalDensity*(1-porosity)*area);
}
inline double vaporFactor(double h, double delta, double ratio, double coverage=1)
{
    if (!(h >= 0 && delta > 0 && ratio > 0 && coverage > 0 && coverage <= 1))
        throw std::domain_error("Invalid external crust vapor resistance");
    if (h == 0 || std::isinf(ratio)) return 1;
    return (1-coverage)+coverage/(1+h/(coverage*delta*ratio));
}
inline double thermalConductance(double h, double delta, double airK, double crustK)
{
    if (!(h >= 0 && delta > 0 && airK > 0 && crustK > 0))
        throw std::domain_error("Invalid external crust thermal resistance");
    return 1/(delta/airK+h/crustK);
}
}
#endif
