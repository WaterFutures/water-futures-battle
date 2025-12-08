# Total capital investment at year \(t\)

The total capital cost in year \(t\) is:

$$
K_{\text{cap}}(t)
= K_{\text{sources}}(t)
+ K_{\text{pipes}}(t)
+ K_{\text{pumps}}(t)
+ K_{\text{solar}}(t)
$$


## Capital investment for new sources at year \(t\)

$$
K_{\text{sources}}(t)
= \sum_{s \in S_{\text{new-src}}}
\mathbf{1}_{\{t_s = t\}} \,
c_{\text{unit}}^{\text{source}}(t) \,
\text{Capacity}_{\text{nominal},s}
$$

where:

- $S_{\text{new-src}}$: set of all sources that are newly built (activated).  
- $t_s$: year when source $s$ is built.  
- $\mathbf{1}_{\{t_s = t\}}$: 1 if source $s$ is built in year $t$, 0 otherwise.  
- $c_{\text{unit}}^{\text{source}}(t)$: unit construction cost of sources in year $t$ ($\text{€}/m^3/day$).  
- $\text{Capacity}_{\text{nominal},s}$: nominal capacity of source $s$ ($m^3/day$).

---

## Capital investment for new pipes at year \(t\)

$$
K_{\text{pipes}}(t)
= \sum_{j \in J_{\text{new-pipe}}}
\mathbf{1}_{\{t_j = t\}} \,
c_{\text{unit}}^{\text{pipe}}(D_j, M_j, t) \,
L_j
$$

where:

- $J_{\text{new-pipe}}$: set of all new pipe interventions (new pipes that can be built).  
- $t_j$: year when pipe $j$ is built.  
- $\mathbf{1}_{\{t_j = t\}}$: 1 if pipe $j$ is built in year $t$, 0 otherwise.  
- $D_j$: diameter of pipe $j$.  
- $M_j$: material of pipe $j$.  
- $c_{\text{unit}}^{\text{pipe}}(D_j, M_j, t)$: unit construction cost of a pipe with diameter $D_j$ and material $M_j$ in year $t$ (€/m).  
- $L_j$: length of pipe $j$ (m).

---

## Capital investment for pumps at year \(t\)

Total pump CAPEX in year \(t\):

$$
K_{\text{pumps}}(t)
= K_{\text{pumps,new}}(t) + K_{\text{pumps,repl}}(t)
$$

### 1. Pumps for new sources

$$
K_{\text{pumps,new}}(t)
= \sum_{s \in S_{\text{new-src}}}
\mathbf{1}_{\{t_s = t\}} \,
c_{\text{unit}}^{\text{pump}}(o_s, t) \,
N_{\text{pump},s}
$$

where:

- $S_{\text{new-src}}$: set of sources that are newly opened.  
- $t_s$: year source $s$ is opened (and its pumps are installed).  
- $\mathbf{1}_{\{t_s = t\}}$: 1 if source $s$ is opened in year $t$, 0 otherwise.  
- $o_s$: pump option chosen for source $s$.  
- $c_{\text{unit}}^{\text{pump}}(o_s, t)$: cost of one pump of option $o_s$ in year $t$ (€/pump).  
- $N_{\text{pump},s}$: number of pumps installed for source $s$.

### 2. Pump replacements

Replacements use the same pump option $o_s$ as originally chosen for source $s$:

$$
K_{\text{pumps,repl}}(t)
= \sum_{s \in S}
c_{\text{unit}}^{\text{pump}}(o_s, t) \,
N_{\text{pump},s}^{\text{repl}}(t)
$$

where:

- $S$: set of all sources with pumps (existing and new).  
- $N_{\text{pump},s}^{\text{repl}}(t)$: number of pumps at source $s$ that are replaced in year $t$ (0 if no replacement at $s$ in year $t$).

---

## Capital investment for solar PV at year \(t\)

$$
K_{\text{solar}}(t)
= c_{\text{unit}}^{\text{PV}}(t) \,
\sum_{s \in S_{\text{PV}}}
C_{\text{PV}}^{\text{new}}(s, t)
$$

where:

- $S_{\text{PV}}$: set of sources where PV can be installed (i.e. with an associated pumping station suitable for PV).  
- $c_{\text{unit}}^{\text{PV}}(t)$: unit cost of solar PV in year $t$ (€/kW).  
- $C_{\text{PV}}^{\text{new}}(s, t)$: new PV capacity (kW) installed at source $s$ in year $t$  
  (0 if no new PV is installed at $s$ in year $t$).
