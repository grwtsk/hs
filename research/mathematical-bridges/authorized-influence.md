# A finite model of authorized influence and the proposed gap

Status: agent-proposed mathematics for research issue #80, prompted by
[HS-NAV-01](../../sources/conversation/03-edit-navigation.md). Not an adopted
influence policy, implemented interface, physical Yang-Mills result, or model of
human worth. Human choices remain with #9/#10/#65. Source revisits follow #75.

## Three quantities require a bridge

Newtonian F=ma describes constant-mass acceleration; fluid momentum transport adds
spatial transport and stresses, as in Navier-Stokes. A quantum Yang-Mills mass gap
is instead a spectral property of an appropriate quantum Hamiltonian above its
vacuum. These statements identify different mathematical objects; using one
number does not yet identify their domains or units. The source's existing
1/(2*pi) radians must also retain its angular meaning.

The point is not to dismiss the proposed connection. It is to give it a statement
that can be proved, tested or corrected without making a word stand in for a
construction. A finite stability calculation is one useful starting point.

## Proposition: work and dissipation in a declared finite system

Let x(t) be a twice continuously differentiable vector in R^n. Let M, C, K be
constant real symmetric matrices, with M positive definite and C, K positive
semidefinite. Let x0 be fixed. Suppose

    M x'' + C x' + K(x-x0) = u_A + f_E.

Here x represents a computational state, not measured belief. The proposal uses
u_A for an authorized human action and f_E for contributions admitted under the
user-agent contract. The equation itself does not enforce those permissions.
Define

    E(t) = (x'^T M x' + (x-x0)^T K(x-x0))/2.

Then

    E'(t) = x'^T (u_A + f_E) - x'^T C x'.

Proof. Symmetry and constancy give
E' = x'^T M x'' + x'^T K(x-x0). Substitute the stated equation. The two stiffness
terms cancel, leaving the asserted identity. Thus E is nonnegative, and when both
inputs vanish it is nonincreasing. This proves an identity and a finite-system
energy bound under the hypotheses; it does not prove consensus, truth or a
quantum mass gap.

Semidefinite damping is insufficient for asymptotic convergence: C=0, M=K=1 has
non-decaying sinusoidal solutions. A zero stiffness direction can also permit
drift; an energy bound on a semidefinite form does not bound every coordinate.
If matrices, permissions or targets change, their additional derivative or jump
terms require a new account. Do not silently apply the fixed-system identity
across an edit that changes those hypotheses.

## Units and finite accumulated work

These units are an explicit agent modeling convention, not measurements of a
person. For this convention all coordinates of x have a common representation
unit X, time has unit T, and the quadratic functional has model-energy unit U.
Different coordinate units would require a further declared conversion.

| Quantity | Defined role | Unit in this convention |
| --- | --- | --- |
| x, x0 | Computational representation and reference | X |
| M | Positive inertial matrix, not human worth | U T^2 / X^2 |
| C | Nonnegative damping matrix | U T / X^2 |
| K | Nonnegative stiffness matrix | U / X^2 |
| u_A, f_E | Declared forcing terms; admission is external | U / X |
| E, integrated work, integrated dissipation | Quadratic functional and transfers | U |
| Q, lambda_* | Mass-normalized stiffness and positive eigenvalue | T^-2 |
| sqrt(lambda_*) | Undamped angular modal frequency | T^-1 |
| theta_0 = 1/(2*pi) radians | Author's angular interaction scale | Angle, not model energy |

On a finite interval [a,b] with continuous forcing, the fundamental theorem of
calculus applied to the derivative already proved gives the exact identity

    E(b) + integral_a^b x'^T C x' dt
      = E(a) + integral_a^b x'^T (u_A + f_E) dt.

The nonnegative integral is dissipated model energy. No social agreement,
independent evidentiary weight or permission is inferred from either integral.
In particular, the equation cannot detect an unauthorized input masquerading as
u_A: authorization must be established before a term receives that name.

For differentiable time-dependent symmetric M, K and reference x0, the same
algebraic equation has additional energy terms:

    E' = x'^T(u_A+f_E) - x'^T C x'
         + (x'^T M' x' + (x-x0)^T K' (x-x0))/2
         - (x-x0)^T K x0'.

This is a derivative of the declared computational model, not a derivation of
variable-mass physical dynamics. An edit changing a matrix or target can inject
energy. Jumps require their finite energy difference to be recorded separately;
the fixed-coefficient decay claim cannot cross such a change unexamined.

## Where 1/(2*pi) can enter precisely

Define Q = M^(-1/2) K M^(-1/2), and fix the kernel/quotient independently of a
desired conclusion. Suppose there is at least one positive eigenvalue and let
lambda_* be the least positive eigenvalue. For the undamped homogeneous system,
put y=M^(1/2)(x-x0). Then y''+Q y=0, so the nonzero modal frequencies are the
square roots of Q's positive eigenvalues.

Write epsilon=1/(2*pi), a dimensionless numerical target, and choose a time
unit T0 > 0 explicitly. For tau=t/T0, the dimensionless stiffness is
Q_tau=T0^2 Q and its least positive eigenvalue is lambda_tau=T0^2 lambda_*.
Replace K, as a modeling normalization, by

    K_hat = (epsilon^2/lambda_tau) K
          = ((epsilon/T0)^2/lambda_*) K.

The multiplier is dimensionless. In tau-time the new least positive eigenvalue
is epsilon^2 and its least positive undamped angular modal frequency is epsilon.
In the original time unit the frequency is epsilon/T0, not a frequency in cycles
per unit time (which divides angular frequency by 2*pi once more). The author's
theta_0 remains an angle; choosing T0 supplies no physical interpretation of it.

These assertions follow because scaling a matrix by a positive constant scales
every eigenvalue by that constant. This is exact finite linear algebra, not a
discovery that evidence or a physical field has this mass.

If a generator eigenvalue rather than a frequency is to equal epsilon, its scaling
would be different. If a physical energy is intended, an energy unit E0 must be
identified before writing Delta=E0/(2*pi). Choosing the unit or rescaling an
already-gapped operator does not prove that the original gap is positive.

Example in already dimensionless time. M=I and K=[[1,-1],[-1,1]] have Q eigenvalues 0 and 2. The normalized K_hat
has eigenvalues 0 and epsilon^2. The constant mode remains; removing it is a stated
mathematical quotient, not permission to delete an inconvenient human voice.
For K_eta=eta*K with eta>0, the original positive eigenvalue is 2*eta and tends to
zero as eta tends to zero. Thus pointwise finite positivity is not a uniform gap
over changing caches. At eta=0 there is no positive mode to normalize. An asserted
normalization must not hide this loss by amplifying an arbitrarily weak coupling
without recording the altered scale.

## A sufficient uniform bound with its additional assumptions exposed

A constructive finite alternative to rescaling is to establish bounds on a
specified family before normalization. Here is one elementary sufficient
condition, not an architecture selected for Hs.

Let K be the weighted Laplacian of a connected undirected graph with n vertices,
2 <= n <= N. All edge weights are nonnegative. Suppose a spanning tree has every
edge weight at least a > 0. Let M be diagonal with 0 < m_i <= m_bar. Fix the
kernel of K as span{1}, so the kernel of Q=M^(-1/2) K M^(-1/2)
is span{M^(1/2)1}, independently of a desired conclusion. Then

    lambda_*(M^(-1/2) K M^(-1/2)) >= a / (m_bar N(N-1)).

Proof. For a positive-mode vector y perpendicular to M^(1/2)1, put
z=M^(-1/2)y. Then sum_i m_i z_i=0, so min z <= 0 <= max z. Set
R=max z-min z. A path in the spanning tree between extrema has at most n-1
edges. Cauchy-Schwarz and the edge lower bound give

    R^2 <= (n-1) sum_tree_edges (z_i-z_j)^2
        <= (n-1) z^T K z / a.

Also z^T M z <= m_bar n R^2, since every |z_i| <= R. For nonzero y in the
declared complement, connectedness makes R positive. Thus its Rayleigh quotient
is at least a/[m_bar n(n-1)], hence at least the stated bound. Minimizing on this
finite-dimensional complement proves the claim. The frequency bound is the
square root, in the declared units, of this eigenvalue bound.

This result exposes rather than supplies the missing uniform hypotheses.
Weakening connecting edges removes a; disconnected graphs acquire additional
zero modes; increasing n removes the fixed size bound; unbounded modeled masses
remove m_bar. For example M=L*I on the two-node graph gives lambda_*=2/L, which
tends to zero despite unchanged edges. None of these failures can be repaired
by suppressing a person, discarding dissent or charging an edit enough numerical
mass. The representation and any usable bounds still require justification.
The elementary inequality is neither a uniform continuum estimate nor a
Yang-Mills field construction.

## What a fluid or Yang-Mills correspondence would still need

A fluid model must define a domain, density, velocity, constitutive stresses,
sources and boundary conditions, and justify any conservation/incompressibility
assumptions. An evidence graph does not become an incompressible fluid because it
has a density attribute. No Navier-Stokes regularity result follows here.

For an actual Yang-Mills correspondence, supply the gauge/field construction,
Hilbert space, Hamiltonian, vacuum, axioms, continuum/volume limits and a proved
spectral bound for that theory. Jaffe and Witten define a gap by absence of spectrum
in an interval (0, Delta) above the vacuum and formulate the four-dimensional
quantum theory existence problem separately from any chosen normalization. This
note does not supply that construction or claim their problem is solved.

## Human boundary and research obligations

Numerical resistance acts on an explicitly modeled representation. It cannot be
used to trap the person in a route or require enough accumulated influence to
edit, refuse, undo or contribute. The user-agent's semantic override remains an
authority boundary; it is not simulated as an amount of force that might be too
small. Truth assessment, relevance, familiarity, resource capacity, dissemination
and consent require separately accountable records.

Next research: justify a representation and admissible weights without a
credibility score based on identity, money or popularity; analyze disconnected
and changing graphs; preserve competing accounts and source lineage; define
what locality contributes; and investigate the proposed correspondence rather
than treating the finite example as its completion. No automatic propagation,
model training or interface behavior is implemented by the equations.

## Sources and reading scope

NASA Glenn, [Navier-Stokes Equations](https://www.grc.nasa.gov/www/BGH/nseqs.html):
read the explanatory text on 2026-09-21 for momentum, viscosity and the dependent
fields; no image-based equation transcription is relied upon.

Arthur Jaffe and Edward Witten, [Quantum Yang-Mills Theory](https://www.claymath.org/wp-content/uploads/2022/06/yangmills.pdf),
sections 3-4, especially printed page 6: read the Hamiltonian/vacuum and mass-gap
statement on 2026-09-21. The finite proposition and examples above are this
note's derivations, not conclusions attributed to that paper.
