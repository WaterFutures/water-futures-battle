from typing import Dict

from geopy.distance import geodesic
import numpy as np
import pandas as pd
from scipy.spatial import Delaunay

from water_futures_battle.jurisdictions.entities import Municipality, Province
from water_futures_battle.sources.entities import WaterSource, SourcesContainer

import epanet_utils

COLUMNS_CONNECTION = [
    # entities columns that gets saved out
    "from_node",
    "to_node",
    "distance",
    "minor_loss_coefficient",
    "pipes-installation_dates",
    "pipes-option_ids",
    "last_pipe_decom_date",
    "replaced_by",
    "replaces",
    "usable_in_2025",
    # support columns 
    "removable", # ignore in remove excess connections (everything except delaunay pipes: manually added pipes and sources)
    "optimisable", # select diam with pygmo optimisation
    "min_date", # when the connections first appears (min between begin dates), pipes can not be installed before this date
    "disappearing" # from node and to node are the same in 2025, thus does not exist in 2025 and can't be optimised
]

def compute_distance(m1: Municipality | WaterSource, m2: Municipality) -> float:
    return geodesic(m1.coordinates, m2.coordinates).m

def lifted_to_existing(
        a_province: Province,
        peak_demands_df: pd.DataFrame
        ) -> tuple[pd.DataFrame, set[Municipality]]:
    """
    Create a DataFrame of connections from all municipalities that close (lifted)
    to an existing municipality in 2000. This municipality will simply be connected 
    with a pipe that at the historical peak demand has 2.0 m/s velocity.
    
    :param a_province: Description
    :type a_province: Province
    :param peak_demands_df: DataFrame with each year peak demand at the province 
    level, but with values at each municipality
    :type peak_demands_df: pd.DataFrame
    :return: Description
    :rtype: tuple[DataFrame, set[Municipality]]
    """
    data_list = []

    munis_2000 = a_province.active_municipalities(when=2000)
    handled_munis = set()

    for muni in munis_2000:
        if muni.is_active(when=2025):
            continue
        if muni.end_reason != 'lifted':
            continue

        # Discover where it went when closed (biggest muni in the same province on its closing year)
        try:
            dest_m = muni.effective_entity(when=muni.end_date)
        except:
            continue
        if not any(m.matches(dest_m) for m in munis_2000):
            # No need to consider it, will be handled automatically
            continue

        # We ordered them from dest to muni so that the flows are initialized already
        # in the correct direction
        data_list.append({
            "from_node": dest_m.cbs_id,
            "to_node": muni.cbs_id,
            "distance": compute_distance(dest_m, muni),
            "minor_loss_coefficient": 0,
            "pipes-installation_dates": max(dest_m.begin_date, muni.begin_date),
            "pipes-option_ids": epanet_utils.get_pipe_option_id(
                pipe_flow__m3ps=peak_demands_df[muni.cbs_id].max()/3600,
                design_vel__mps=0.75
            ),
            "last_pipe_decom_date": pd.NaT,
            "replaced_by": "",
            "replaces": "",
            "usable_in_2025": True,
            "removable": False,
            "optimisable": False,
            "min_date": max(dest_m.begin_date, muni.begin_date),
            "disappearing": True
        })
        handled_munis.add(muni)

    if len(data_list) > 0:
        df = pd.DataFrame(data_list)
    else:
        df = pd.DataFrame(columns=COLUMNS_CONNECTION)

    return df.sort_values("distance").reset_index(drop=True), handled_munis

def sources(
        a_province: Province,
        nl_sources: SourcesContainer,
        nl_sources_lookups: Dict[str, pd.DataFrame]
        ) -> pd.DataFrame:
    
    data_list = []
    for source in sorted(
        nl_sources.source_by_province(a_province=a_province),
        key=lambda s: s.bwf_id
    ):
        assert source.province == a_province, "Error in extracting the sources by province provinces.."

        municipality = a_province.municipality(
            nl_sources_lookups[source.NAME].loc[source.bwf_id, 'closest_municipality']
        )

        if pd.notna(source.activation_date):
            inst_date = max(source.activation_date, municipality.begin_date)
            inst_optid = epanet_utils.get_pipe_option_id(
                pipe_flow__m3ps=source.nominal_capacity/24/3600,
                design_vel__mps=0.75
            )
            if pd.notna(source.closure_date):
                deco_date = source.closure_date
                replacedby = "CLOSED_WSOURCE"
                usablein2k25 = False
            else:
                deco_date = pd.NaT
                replacedby = ""
                usablein2k25 = True
        else:
            inst_date = pd.NaT
            inst_optid = ""
            deco_date = pd.NaT
            replacedby = ""
            usablein2k25 = True

        data_list.append({
            "from_node": source.bwf_id,
            "to_node": municipality.cbs_id,
            "distance": compute_distance(
                source,
                municipality
            ),
            "minor_loss_coefficient": 0,
            "pipes-installation_dates": inst_date,
            "pipes-option_ids": inst_optid,
            "last_pipe_decom_date": deco_date,
            "replaced_by": replacedby,
            "replaces": "",
            "usable_in_2025": usablein2k25,
            "removable": False,
            "optimisable": False,
            "min_date": max(source.activation_date, municipality.begin_date),
            "disappearing": False
        })
    
    df = pd.DataFrame(data_list)
    return df.sort_values("distance").reset_index(drop=True)

def full_delaunay(
        a_province: Province,
        handled_municipalities: set[Municipality],
        year: int,
        default_option_id: str
        ) -> pd.DataFrame:
    municipalities = a_province.active_municipalities(when=year)
    municipalities = municipalities - handled_municipalities
    municipalities = list(municipalities)

    # Convert to ndarray the municipalities coordinates (latitude, longitude)
    points = np.array([[m.latitude, m.longitude] for m in municipalities], dtype=float)
    
    # Compute Delaunay triangulation
    tri = Delaunay(points)
    # tri.simplices is an array of shape (ntri, 3) with indices into points
    # You can use these to create possible connections (edges)
    edges = set()
    for simplex in tri.simplices:
        for i in range(3):
            a, b = simplex[i], simplex[(i+1)%3]
            edge = tuple(sorted((a, b)))
            edges.add(edge)

    # edges is a set of (i, j) pairs, where i and j are indices into munis_2000
    data_list = []
    for i, j in edges:
        node_a = municipalities[i].cbs_id
        node_b = municipalities[j].cbs_id
        
        # Ensure alphabetical order
        from_node = min(node_a, node_b)
        to_node = max(node_a, node_b)
        from_m = a_province.municipality(from_node)
        to_m = a_province.municipality(to_node)

        data_list.append({
            "from_node": from_node,
            "to_node": to_node,
            "distance": compute_distance(from_m, to_m),
            "minor_loss_coefficient": 0,
            "pipes-installation_dates": max(from_m.begin_date,to_m.begin_date),
            "pipes-option_ids": default_option_id,
            "last_pipe_decom_date": pd.NaT,
            "replaced_by": "",
            "replaces": "",
            "usable_in_2025": True,
            "removable": True,
            "optimisable": True,
            "min_date": max(from_m.begin_date,to_m.begin_date),
            "disappearing": (
                from_m.effective_cbs_id(when=2025) == to_m.effective_cbs_id(when=2025)
            )
        })

    df = pd.DataFrame(data_list)
    return df.sort_values("distance").reset_index(drop=True)

# now using the population of the muni in that year, we get the class and limit the number of posible connections
# SMALL : 2, MEDIUM: 3, LARGE: 4, G4 not limited
def topology_heuristic(
        df: pd.DataFrame,
        a_province: Province
        ) -> pd.DataFrame:
    df = df.copy()
    
    # We use the active column to keep track which to remove and which to keep
    # Those that are not removable (not delaunay generated) are active by definition 
    df['active'] = ~df['removable'].astype(bool)
    
    # We sort the municipality by population size
    muni_pop = {}
    muni_pop = {muni: muni.population.dropna().iloc[-1]
                for muni in a_province.municipalities}
    ranked_muni_pop = sorted(muni_pop.items(), key=lambda x: x[1])

    for muni, _ in ranked_muni_pop:
        muni_sclass = muni.size_class.dropna().iloc[-1]

        if muni_sclass >= 4:
            continue
        max_connections = int(muni_sclass)+1

        # get all connections with this municipality
        mask = df['removable'] & (
            (df['from_node'] == muni.cbs_id) | (df['to_node'] == muni.cbs_id)
        )
        keep_idxs = df.loc[mask].sort_values('distance').head(max_connections).index
        
        df.loc[keep_idxs, 'active'] = True

    df.loc[~df['active'], ['pipes-installation_dates', 'pipes-option_ids']] = [pd.NaT, ""]

    return df.drop(columns=['active'])

def new_loose_municipalities(
        a_province: Province,
        year: int,
        all_existing_connections_df: pd.DataFrame,
        peak_demands_df: pd.DataFrame
    ) -> pd.DataFrame:

    municipalities_Y = a_province.active_municipalities(when=year)
    handled_municipalities = a_province.active_municipalities(when=(year-1))

    new_municipalities = municipalities_Y - handled_municipalities

    if len(new_municipalities) == 0:
        return pd.DataFrame(columns=COLUMNS_CONNECTION)

    # Now that we know that there are new municipalities, are they all correctly connected?
    # aka do they inherit enough connections from the old ones?
    # It could happen that a new municipality doesn't inherit any connection because
    # the muncipalities that make up for it go also somewhere else which takes precedence.
    # With a first run we saw that this was happening only between "Midden-Delfland (GM1843)"
    # and "Westland (GM1783)"

    # First, make sure we consider the right connections (no sources and in the province)
    MASK_G2G_CNNS = all_existing_connections_df.index.str.startswith('CG')
    MASK_PV_CNNS = all_existing_connections_df['province'] == a_province.cbs_id
    
    existing_connections = all_existing_connections_df[MASK_G2G_CNNS & MASK_PV_CNNS].copy()

    # Second, let's see what would be the status of the connections in this year
    existing_connections['from_effective'] = existing_connections['from_node'].apply(
        lambda m: a_province.municipality(m).effective_cbs_id(when=year)
    )
    existing_connections['to_effective'] = existing_connections['to_node'].apply(
        lambda m: a_province.municipality(m).effective_cbs_id(when=year)
    )

    data_list = []
    for m in new_municipalities:

        # If the municipality has enough connections (at least one) we are ok with it
        if sum(
            (existing_connections['from_effective'] == m.cbs_id) |
            (existing_connections['to_effective'] == m.cbs_id)
        ) > 0:
            continue

        # We found a new municipality that remains unconnected. Add a number of
        # connections equal to its class to the closest municipality
        print("New municipality is disconnected from the network.",
                f"Municipality: {m.display_name}",
                sep='\n')
        
        m_distances = {mto: compute_distance(m1=m, m2=mto)
                       for mto in municipalities_Y}
        sorted_possible_connections = sorted(m_distances.items(), key=lambda x: x[1])

        ts = pd.Timestamp(year=year, month=1, day=1)
        muni_sclass = m.size_class.loc[ts]
        if muni_sclass >= 4:
            import warnings
            warnings.warn(
                f"Attention needed, a new municipality of class 4 or higher has been found: {m.display_name}",
                UserWarning
            )
        max_connections = int(muni_sclass)+1

        # Let's simply split equally the demand between the connections
        peak_m_demand = peak_demands_df[m.cbs_id].max()

        pipe_design_demand__m3ps = peak_m_demand/max_connections/3600 # to m^3/s

        pipe_option_id = epanet_utils.get_pipe_option_id(
                pipe_flow__m3ps=pipe_design_demand__m3ps,
                design_vel__mps=0.75
            )

        for c in range(1, max_connections+1): # we skip 0 because the self connection should be the shortest (0 m)
            data_list.append({
                "from_node": m.cbs_id,
                "to_node": sorted_possible_connections[c][0].cbs_id,
                "distance": compute_distance(
                    m,
                    sorted_possible_connections[c][0]
                ),
                "minor_loss_coefficient": 0,
                "pipes-installation_dates": max(
                    m.begin_date,
                    sorted_possible_connections[c][0].begin_date
                ),
                "pipes-option_ids": pipe_option_id,
                "last_pipe_decom_date": pd.NaT,
                "replaced_by": "",
                "replaces": "",
                "usable_in_2025": True,
                "removable": False,
                "optimisable": False,
                "min_date": max(
                    m.begin_date,
                    sorted_possible_connections[c][0].begin_date
                ),
                "disappearing": False
            })

    if len(data_list) == 0:
        return pd.DataFrame(columns=COLUMNS_CONNECTION)
    
    return pd.DataFrame(data_list).sort_values("distance").reset_index(drop=True)

def appearing_municipalities(
        a_province: Province,
        year: int,
        all_existing_connections_df: pd.DataFrame,
        peak_demands_df: pd.DataFrame
    ) -> pd.DataFrame:
    # Define the connections that get replaced, those that gets hidden, and the new ones we have

    municipalities_Y = a_province.active_municipalities(when=year)
    handled_municipalities = a_province.active_municipalities(when=(year-1))

    new_municipalities = municipalities_Y - handled_municipalities

    if len(new_municipalities) == 0:
        return pd.DataFrame(columns=COLUMNS_CONNECTION)

    # First, make sure we consider the right connections (no sources and in the province)
    MASK_G2G_CNNS = all_existing_connections_df.index.str.startswith('CG')
    MASK_PV_CNNS = all_existing_connections_df['province'] == a_province.cbs_id
    MASK_STILL_USABLE = all_existing_connections_df['usable_in_2025']
    
    existing_connections = all_existing_connections_df[
        MASK_G2G_CNNS & MASK_PV_CNNS & MASK_STILL_USABLE
    ].copy()

    # Second, let's see what would be the status of the connections in this year
    existing_connections['from_effective'] = existing_connections['from_node'].apply(
        lambda m: a_province.municipality(m).effective_cbs_id(when=year)
    )
    existing_connections['to_effective'] = existing_connections['to_node'].apply(
        lambda m: a_province.municipality(m).effective_cbs_id(when=year)
    )

    # Priority goes to new municipalities that are orphan
    data_list = []
    for m in new_municipalities:

        inherited_cnns_mask = (
            (existing_connections['from_effective'] == m.cbs_id) |
            (existing_connections['to_effective'] == m.cbs_id)
        )
        
        # If the new municipality is not completely isolated
        if any(inherited_cnns_mask):
            continue
    
        # We found a new municipality that remains unconnected. Add a number of
        # connections equal to its class to the closest municipalities
        print("New municipality is disconnected from the network.",
                f"Municipality: {m.display_name}",
                sep='\n')
        
        m_distances = {mto: compute_distance(m1=m, m2=mto)
                    for mto in municipalities_Y}
        sorted_possible_connections = sorted(m_distances.items(), key=lambda x: x[1])

        ts = pd.Timestamp(year=year, month=1, day=1)
        muni_sclass = m.size_class.loc[ts]
        if muni_sclass >= 4:
            import warnings
            warnings.warn(
                f"Attention needed, a new municipality of class 4 or higher has been found: {m.display_name}",
                UserWarning
            )
        max_connections = int(muni_sclass)+1

        # Let's simply split equally the demand between the connections
        peak_m_demand = peak_demands_df[m.cbs_id].max()

        pipe_design_demand__m3ps = peak_m_demand/max_connections/3600 # to m^3/s

        pipe_option_id = epanet_utils.get_pipe_option_id(
                pipe_flow__m3ps=pipe_design_demand__m3ps,
                design_vel__mps=0.75
            )

        for c in range(1, max_connections+1): # we skip 0 because the self connection should be the shortest (0 m)
            data_list.append({
                "from_node": m.cbs_id,
                "to_node": sorted_possible_connections[c][0].cbs_id,
                "distance": compute_distance(
                    m,
                    sorted_possible_connections[c][0]
                ),
                "minor_loss_coefficient": 0,
                "pipes-installation_dates": max(
                    m.begin_date,
                    sorted_possible_connections[c][0].begin_date
                ),
                "pipes-option_ids": pipe_option_id,
                "last_pipe_decom_date": pd.NaT,
                "replaced_by": "",
                "replaces": "",
                "usable_in_2025": True,
                "removable": False,
                "optimisable": False,
                "min_date": max(
                    m.begin_date,
                    sorted_possible_connections[c][0].begin_date
                ),
                "disappearing": False
            })
        
    # Now that we have handled the orphan new municipalities, we can focus on the remaining ones
    # The idea is that every connection that in that year is being affected
    # (i.e. in that year, either or both the from or to municipality close)
    # if the two ends become the same one
    #           usable in 2025 NO
    #           last pipe decom date on THIS YEAR
    #.          replaced by SELF_LOOP
    # if only one of the two ends changes,
    #           new connection 
    for cnn_id, c in existing_connections.iterrows():

        last_year_from_eff = a_province.municipality(c['from_node']).effective_entity(when=year-1)
        last_year_to_eff = a_province.municipality(c['to_node']).effective_entity(when=year-1)
            
        if (
            last_year_from_eff.cbs_id == c['from_effective'] and
            last_year_to_eff.cbs_id == c['to_effective']
        ):
            # it didn't happen this year, so it's not my concern
            continue
        
        if c['from_effective'] == c['to_effective']:
            # we know it happend this year, and we know it becomes a self loop,
            all_existing_connections_df.loc[
                c.name,
                ["last_pipe_decom_date", "replaced_by", "usable_in_2025"]
            ] = [
                pd.Timestamp(year=year, month=1, day=1),
                "SELF_LOOP",
                False
            ]

            # handled, move on
            continue

        if not ((
            pd.notna(last_year_from_eff.end_date) and 
            last_year_from_eff.end_date.year == year and
            last_year_from_eff.end_reason == "lifted"
        ) or (
            pd.notna(last_year_to_eff.end_date) and 
            last_year_to_eff.end_date.year == year and
            last_year_to_eff.end_reason == "lifted"
        )):
            # neither of the two was lifted (both renamed, one renamed and one not)
            # we don't care, renamed municipalities are effectively the same
            continue
        
        # it happened this year, and either both or one of the two municipalities
        # appeared this year. Anyway we need a new connection
        from_node = min(c["from_effective"], c["to_effective"])
        to_node = max(c["from_effective"], c["to_effective"])
        data_list.append({
                "from_node": from_node,
                "to_node": to_node,
                "distance": compute_distance(
                    a_province.municipality(c["from_effective"]),
                    a_province.municipality(c["to_effective"])
                ),
                "minor_loss_coefficient": 0,
                # we won't necessarily install something here yet, we just define the connection
                "pipes-installation_dates": pd.NaT,
                "pipes-option_ids": "",
                "last_pipe_decom_date": pd.NaT,
                "replaced_by": "",
                "replaces": cnn_id,
                "usable_in_2025": True,
                "removable": False,
                "optimisable": False,
                "min_date": max(
                    a_province.municipality(c["from_effective"]).begin_date,
                    a_province.municipality(c["to_effective"]).begin_date
                ),
                "disappearing": False
            })
        
        # while the old one, gets replaced by it (another algorithm will take care
        # of deciding if we need to uninstall this pipe and install it in the new connection)
        # we haven't decided the new connections ids yet here, so I insert a placeholder,
        # and later we will re-find it.
        all_existing_connections_df.loc[
                c.name,
                ["replaced_by", "usable_in_2025"]
            ] = ["SOMEONE",    False]

    if len(data_list) == 0:
        return pd.DataFrame(columns=COLUMNS_CONNECTION)
    
    new_df = pd.DataFrame(data_list).sort_values("distance").reset_index(drop=True)

    # it could be that a one connection replaces multiple connections, in that case we should
    # expect that we have more dupliacte entries
    # Merge 'replaces' for duplicates
    grouped = new_df.groupby(['from_node', 'to_node'], as_index=False).agg({
        **{col: 'first' for col in new_df.columns if col not in ['from_node', 'to_node', 'replaces']},
        'replaces': lambda x: ';'.join(str(v) for v in x if v)
    })
    return grouped

def install_new_pipes(
        connections: pd.DataFrame,
        pipes_rgh_history: pd.DataFrame,
        pipes_options: pd.DataFrame,
        year: int,
        mask_pv_cnns: pd.Series,
        sampled_end_dates: pd.Series
    ) -> tuple[pd.DataFrame, pd.DataFrame]:

    TS_YEAR = pd.Timestamp(year=year, month=1, day=1)
    MASK_NEW_PIPES = (sampled_end_dates.dt.year == year) & mask_pv_cnns

    # Variables for pandas bulk update
    updt_rghn_history = {}
    for connection_id, end_date in sampled_end_dates[MASK_NEW_PIPES].items():

        if pd.notna(connections.loc[connection_id, 'last_pipe_decom_date']):
            # if it has already a decommision date is because it will go out of use
            # anyway in the historical period
            # thus we ignore the object
            continue

        # the last pipe needs to be decommission and a new one on its place
        new_pipe_inst_date = TS_YEAR
        new_pipe_option = str(connections.loc[connection_id, 'pipes-option_ids'])

        if connections.loc[connection_id, 'replaced_by'] == '':
            # default case, replace the pipe with a new pipe in the same connection 
            new_pipe_bwf_id = str(connection_id)+'-01'
        
            connections.loc[connection_id, 'pipes-installation_dates'] = ';'.join([
                connections.loc[connection_id, 'pipes-installation_dates'],
                new_pipe_inst_date.strftime('%Y-%m-%d')
            ])
            connections.loc[connection_id, 'pipes-option_ids'] = ';'.join([
                connections.loc[connection_id, 'pipes-option_ids'],
                new_pipe_option
            ])

        else:
            # the connections has been replaced by another one
            replacement_cnn_id = connections.loc[connection_id, 'replaced_by']
            assert len(connections.loc[replacement_cnn_id, 'replaces'].split(';')) == 1

            # if the replacing cnn is also being replaced, we may have to move it on
            # the re-replacement connection has to be a valid connection (not empty not self loop)
            # it has to be a 1-to-1 replacement
            # it has to have a min_date (date of definition) before this moment
            re_replacement_cnn_id = connections.loc[replacement_cnn_id, 'replaced_by']
            if (
                re_replacement_cnn_id != '' and
                re_replacement_cnn_id != 'SELF_LOOP' and
                len(connections.loc[re_replacement_cnn_id, 'replaces'].split(';')) == 1 and 
                connections.loc[re_replacement_cnn_id, 'min_date'] <= TS_YEAR
            ):
                replacement_cnn_id = re_replacement_cnn_id

            new_pipe_bwf_id = str(replacement_cnn_id)+'-00'

            connections.loc[
                connection_id,
                'last_pipe_decom_date'
            ] = new_pipe_inst_date

            connections.loc[
                replacement_cnn_id, 
                ['pipes-installation_dates', 'pipes-option_ids']
            ] = [
                new_pipe_inst_date.strftime('%Y-%m-%d'),
                new_pipe_option
            ]
        
        # to conclude we add the new pipe in the roughness history
        updt_rghn_history[new_pipe_bwf_id] = pipes_options.loc[
            new_pipe_option,
            'darcy_friction_factor-new_pipe'
        ]
    
    # end of loop for pipes reaching end of lifetime
    # We delay the pandas bulk update for the new pipes frictions until the next loop

    # Start of loop to deal with the completely new pipes... 
    for cnn_id, cnn in connections[mask_pv_cnns].iterrows():
        
        if cnn['pipes-installation_dates'] == '':
            # if empty there are no pipes here
            continue

        if len(cnn['pipes-installation_dates'].split(';')) > 1:
            # if len > 1 we should have handled them above already
            continue

        if str(cnn_id)+'-00' in pipes_rgh_history.columns:
            # we have already dealt with this pipe, continue
            continue

        new_pipe_bwf_id = str(cnn_id)+'-00'
        new_pipe_option = str(cnn['pipes-option_ids'])

        if new_pipe_option != "UNDECIDED":
            updt_rghn_history[new_pipe_bwf_id] = pipes_options.loc[
                new_pipe_option,
                'darcy_friction_factor-new_pipe'
            ]

        else:
            updt_rghn_history[new_pipe_bwf_id] = 128.0

    pipes_rgh_history.loc[
        TS_YEAR,
        list(updt_rghn_history.keys())
    ] = list(updt_rghn_history.values())

    return pipes_rgh_history, connections

def age_pipes(
        connections: pd.DataFrame,
        pipes_rgh_history: pd.DataFrame,
        pipes_options: pd.DataFrame,
        year: int,
        pipe_ageing_rng: np.random.Generator
    ) -> pd.DataFrame:

    # Track a few properties to vectorize the set operation
    pv_pipe_ids = []
    pipe_dec_rate_lb = []
    pipe_dec_rate_ub = []

    # Sort by connection id to maintain consistency with the evaluator
    for connection_id, connection in connections.sort_index().iterrows():

        # Get which is the active pipe, if more than one
        pipes_inst_dates = [
            pd.to_datetime(d)
            for d in connection['pipes-installation_dates'].split(';')
        ]
        pipes_option_ids = connection['pipes-option_ids'].split(';')
        pipes_end_dates = pipes_inst_dates[1:]+[connection['last_pipe_decom_date']]

        cnns_pipes_ids = [f'{connection_id}-{x:02d}' for x in range(len(pipes_option_ids))]

        pipe = {}
        for i in range(len(pipes_option_ids)):
            if (
                pipes_inst_dates[i].year <= year and 
                (
                    pd.isna(pipes_end_dates[i]) or 
                    pipes_end_dates[i].year > year
                )
            ):
                pipe['install_date'] = pipes_inst_dates[i]
                pipe['option'] = pipes_option_ids[i]
                pipe['deco_date'] = pipes_end_dates[i]
                pipe['bwd_id'] = cnns_pipes_ids[i]
                break

        if not pipe:
            continue

        pv_pipe_ids.append(pipe["bwd_id"])
        if pipe["option"] != "UNDECIDED":
            pipe_dec_rate_lb.append(
                pipes_options.loc[
                    pipe["option"], "darcy_friction_factor-decay_rate-min"
                ]
            )
            pipe_dec_rate_ub.append(
                pipes_options.loc[
                    pipe["option"], "darcy_friction_factor-decay_rate-min"
                ]
            )
        else:
            pipe_dec_rate_lb.append(0.0)
            pipe_dec_rate_ub.append(1.0)

    # Sample and calculate the decay for all these pipes
    rnd_sample = pipe_ageing_rng.uniform(low=0, high=1, size=len(pv_pipe_ids))
    decay_low = np.array(pipe_dec_rate_lb)
    decay_high = np.array(pipe_dec_rate_ub)

    decay = decay_low + (decay_high-decay_low)*rnd_sample

    # Get this year value and add the new decay to it for next year.
    ts = pd.Timestamp(year=year, month=1, day=1)
    base_values = pipes_rgh_history.loc[ts, pv_pipe_ids]

    Nts = pd.Timestamp(year=year+1, month=1, day=1)
    updated_values = base_values.values + decay
    pipes_rgh_history.loc[Nts, pv_pipe_ids] = updated_values

    return pipes_rgh_history
