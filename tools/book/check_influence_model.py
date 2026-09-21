"""Exact symbolic checks of the finite research examples, not a field-theory proof.

Run with Python and SymPy. No network, application, model training or source
rewriting. The general propositions remain written derivations for review.
"""
import sys


def main() -> int:
    try:
        import sympy as s
    except ImportError:
        print("UNRUN: finite symbolic check requires SymPy", file=sys.stderr)
        return 2
    passed = []

    def verify(name, condition):
        if not condition:
            raise ValueError(name)
        passed.append(name)
        print("PASS", name)

    def zero(expression):
        return s.simplify(expression) == 0

    t = s.symbols("t", real=True)
    eta, mass = s.symbols("eta mass", positive=True)
    epsilon = 1 / (2*s.pi)
    K = s.Matrix([[1, -1], [-1, 1]])
    verify("two_node_spectrum", K.eigenvals() == {0: 1, 2: 1})
    verify("normalized_frequency_squared", (epsilon**2*K/2).eigenvals() == {0: 1, epsilon**2: 1})
    verify("weak_coupling_limit", (eta*K).eigenvals() == {0: 1, 2*eta: 1} and s.limit(2*eta, eta, 0, dir="+") == 0)
    verify("no_positive_mode_at_zero", (0*K).eigenvals() == {0: 2})
    verify("unbounded_mass_counterexample", (K/mass).eigenvals() == {0: 1, 2/mass: 1} and s.limit(2/mass, mass, s.oo) == 0)
    x = s.sin(t)
    verify("undamped_nondecay", zero(s.diff(x,t,2)+x) and zero((s.diff(x,t)**2+x**2)/2-s.Rational(1,2)))
    verify("zero_stiffness_drift", s.diff(t,t,2) == 0 and s.limit(t,t,s.oo) == s.oo)
    # Formal differentiation on arbitrary symmetric 2x2 matrices: algebraic
    # cancellation does not itself certify their positivity assumptions.
    m11,m12,m22,c11,c12,c22,k11,k12,k22 = s.symbols("m11 m12 m22 c11 c12 c22 k11 k12 k22", real=True)
    M = s.Matrix([[m11,m12],[m12,m22]])
    C = s.Matrix([[c11,c12],[c12,c22]])
    A = s.Matrix([[k11,k12],[k12,k22]])
    z = s.Matrix(s.symbols("z1 z2", real=True))
    v = s.Matrix(s.symbols("v1 v2", real=True))
    f = s.Matrix(s.symbols("f1 f2", real=True))
    acceleration = M.inv()*(f-C*v-A*z)
    derivative = (v.T*M*acceleration+v.T*A*z)[0]
    verify("fixed_work_identity", zero(derivative-(v.T*f-v.T*C*v)[0]))
    # A concrete finite interval checks accumulation as well as differentiation.
    displacement = t**2
    energy = (s.diff(displacement,t)**2+displacement**2)/2
    forcing = s.diff(displacement,t,2)+s.diff(displacement,t)+displacement
    verify("integrated_work_identity", zero(energy.subs(t,1)-energy.subs(t,0)+s.integrate(s.diff(displacement,t)**2,(t,0,1))-s.integrate(s.diff(displacement,t)*forcing,(t,0,1))))
    # Changing coefficients and target: scalar instance exposes all extra terms.
    mt,kt,ct = 1+t, 2+t**2, 3+t
    target = t**3
    zt = displacement-target
    vt = s.diff(displacement,t)
    force = mt*s.diff(displacement,t,2)+ct*vt+kt*zt
    E = (mt*vt**2+kt*zt**2)/2
    rhs = vt*force-ct*vt**2+(s.diff(mt,t)*vt**2+s.diff(kt,t)*zt**2)/2-zt*kt*s.diff(target,t)
    verify("changing_system_terms", zero(s.diff(E,t)-rhs))
    print(f"FINITE_SYMBOLIC_OK checks={len(passed)} sympy={s.__version__} authority=none")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, TypeError) as exc:
        print(f"FINITE_SYMBOLIC_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
