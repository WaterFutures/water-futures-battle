from pathlib import Path
from typing import Dict, List, Set, Tuple

import pandas as pd

from ..jurisdictions import State
from ..sources.entities import WaterSource, SourcesContainer
from ..pumping_stations.entities import PumpingStation
from ..economy.entities import BondIssuance
from ..energy.entities import SolarFarm
from ..connections.entities import Connection, SupplyConnection, PeerConnection

from ..views.services import get_snapshot

from .entities import WaterUtility
from .dynamic_properties import WaterUtilityDB

def configure_water_utilities(
    desc: Dict,
    a_state: State,
    sources: SourcesContainer,
    pumping_stations: Set[PumpingStation],
    connections: Set[Connection],
    utilities_bonds: Dict[str, Set[BondIssuance]],
    solar_farms: Set[SolarFarm]
) -> Tuple[Set[WaterUtility], Set[Connection]]:
    
    # First of all, let's setup the common database for the dyn prop.
    wu_db = WaterUtilityDB.load_from_file(desc[WaterUtilityDB.NAME])
    WaterUtility.set_dynamic_properties(wu_db)

    # Then, let's start creating the entities
    wu_st_properties = desc['water_utilities-static_properties']

    if isinstance(wu_st_properties, str):
        wu_st_properties = pd.read_excel(
            Path(wu_st_properties),
            sheet_name=None
        )

    wutilities: Set[WaterUtility] = set()
    assigned_connections: Set[Connection] = set()
    for idx, row in wu_st_properties['entities'].iterrows():
        wutility_id = str(row[WaterUtility.ID])

        assgn_prov_ids = str(row[WaterUtility.ASSGN_PROVINCES]).split(';')

        wu_provinces = set([a_state.province(pv_id) for pv_id in assgn_prov_ids])
        
        wu_sources = set([s for s in sources if s.province in wu_provinces])
        
        wu_supplies: Dict[WaterSource, Tuple[PumpingStation, Connection]] = {}
        for source in wu_sources:
            pumping_station = next(ps for ps in pumping_stations if ps.source == source)
        
            connection = next(c for c in connections if isinstance(c, SupplyConnection) and c.from_node == source)

            wu_supplies[source] = (pumping_station, connection)

            assigned_connections.add(connection)

        wu_peer_connections: Set[Connection] = set()
        for connection in connections:
            if not isinstance(connection, PeerConnection):
                continue
            
            if (connection.from_node.province in wu_provinces and 
                connection.to_node.province in wu_provinces):
                
                wu_peer_connections.add(connection)
                assigned_connections.add(connection)

        wu_solar_farms = set([sf for sf in solar_farms if sf.connected_entity.province in wu_provinces])
        
        wutilities.add(
            WaterUtility(
                bwf_id=wutility_id,
                m_provinces=wu_provinces,
                m_supplies=wu_supplies,
                m_peer_connections=wu_peer_connections,
                m_bonds=utilities_bonds.get(wutility_id, set()),
                m_solar_farms=wu_solar_farms
            )
        )

    unassigned_connections = connections - assigned_connections

    return wutilities, unassigned_connections
