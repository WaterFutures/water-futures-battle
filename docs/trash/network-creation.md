## Water Distirbution System Synthesis

For each province:
### Phase 1: **Baseline Network Construction (Year 2000)** 🗺️

1.  **Initial Network Generation (Intra-Provincial)**
    * Generate a full **Delaunay Triangulation** for all municipality centroids within the province. This forms the universe of potential connections.
2.  **Network Simplification via Weighted Pruning** 📏
    * **Node Ranking and Binning:** Rank municipalities by **population** and define **$N_B$ population bins**.
    * **Maximum Connections $\left(n_b\right)$:** Assign a maximum allowed number of connections $\left(n_b\right)$ to each bin.
    * **Connection Pruning:**
        * Define the connection weight: $$W_{i, j} = \frac{\text{Distance}_{i, j}}{\left(\text{Population}_i \cdot \text{Population}_j\right)^\alpha}$$
        * Iterate from the smallest municipality bin to the largest. For each node, **keep only its $n_b$ connections with the lowest $\mathbf{W}_{i, j}$ value**.
    * **Connectivity Check:** Verify the resulting network's connectivity. The network must not have too many independent subgraphs. Ensure that the **minimum size of any resulting independent subgraph is at least $10\%$ of the total number of municipalities** in the province.

---

### Phase 2: **Source Integration and Infrastructure Tracking (Year 2000 & 2025)** 

3.  **Source-to-Network Connection (Year 2000)**
    * **Service Area Delineation:** Create a **Weighted Voronoi Tesselation** where source weights are proportional to their **permit/physical capacity**.
    * **Sequential Source Connection Logic:** For each source:
        * Identify the $\mathbf{n_s}$ closest nodes (municipalities) within its assigned Voronoi cell.
        * **Prioritize Connection Path:** The connection should aim to reach the **largest (highest demand) node first**, but must pass through any smaller intermediary municipality that falls directly on the straight-line path (or within a tight buffer) between the source and the target node.
        * **Pipe Routing:** Connect the source sequentially to the municipalities along this prioritized path, ensuring all new connections **do not cross existing intra-provincial pipes**. This reflects a realistic, demand-driven, step-wise construction process.
4.  **Network Validation and Refinement (Heuristic Adjustment)**
    * **Heuristic Adjustments:** **Manually review** (or apply proximity-based heuristics) to identify and correct for:
        * Missing logical connections (e.g., a short, direct path between two large cities where the Pruning step failed).
        * Implausible connections that could be replaced by a more logical path, ensuring the connectivity constraint is still met.
5.  **Future Network Integration (Year 2025)** 🔄
    * **Data Update:** Use 2025 population/demand and source capacity data.
    * **Municipality Tracking:** Identify all 2025 municipalities resulting from a **merger**.
    * **Infrastructure Mapping:**
        * The merged 2025 node gets the **summed demand** of its constituents.
        * All 2000 pipes connected to the constituent nodes become connections to the new 2025 node, **retaining their original physical properties**. This locks in the existing infrastructure.
    * **New Node Generation:** Add any new non-merged 2025 municipalities.
    * **Potential New Infrastructure:** Apply **Weighted Pruning (Step 2)** and **Sequential Source Connection Logic (Step 3)** to the 2025 system. The resulting set of pipes/connections that **do not already exist** are the **potential new investments** (the universe of options for the optimizer).

---

### Phase 3: **Optimization and Historical Synthesis (2000 $\to$ 2025)** 🛠️

6.  **Optimization of the 2025 System** 💡
    * **Initial State:** The network consists of all **existing 2000 pipes** plus the **potential new investment pipes** identified in Step 5.
    * **Optimization:** Run a **network optimization model** (e.g., minimizing capital cost, optimizing flow/pressure, or maximizing redundancy) to select the optimal subset of *new pipes* and *upgrades* required to satisfy the **2025 demand** under the 2025 source capacities. This yields the **Optimized 2025 System**.
7.  **Backward Application (Synthetic Evolution)**
    * **Identify Investments:** The difference between the **Optimized 2025 System** and the **2000 System** (after merger integration) represents the **synthetic set of investments** (new pipes, source upgrades) made between 2000 and 2025. This establishes the network's plausible historical evolution.