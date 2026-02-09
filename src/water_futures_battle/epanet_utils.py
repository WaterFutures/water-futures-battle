"""
This file contains helper functions for working with EPANET.
"""
import math
from epanet_plus import EPyT, EpanetConstants


def merge(networks: list[EPyT]) -> EPyT:
    """
    Merges a list of water networks into a single network.

    Note: We assume that except shared elements, all nodes and links
    (incl. their demand patterns) have unique identifiers.

    Parameters
    ----------
    networks : `epanet_plus.epanet_toolkit.EPyT`
        List of networks (i.e., EPANET instances) to be merged.

    Returns
    -------
    `epanet_plus.epanet_toolkit.EPyT`
        Merged network as an EPANET instance.
    """
    if any(not isinstance(net, EPyT) for net in networks):
        raise TypeError("All items in 'networks' must be instances of 'epanet_plus.epanet_toolkit.EPyT'")

    r = EPyT(use_project=True)  # Create empty network
    r.setflowunits(EpanetConstants.EN_CMH)
    r.setoption(EpanetConstants.EN_HEADLOSSFORM, EpanetConstants.EN_DW)

    curves = {}
    patterns = {}
    for net in networks:
        # Method for copying a curve
        def copy_curve(curve_idx: int):
            curve_id = net.getcurveid(curve_idx)

            if curve_id in curves:
                return curves[curve_id]
            
            r.addcurve(curve_id)
            new_curve_idx = len(curves)+1
            curves[curve_id] = new_curve_idx

            net.getcurvetype(curve_idx)
            r.setcurvetype(new_curve_idx, net.getcurvetype(curve_idx))

            x = []
            y = []
            for i in range(1, net.getcurvelen(curve_idx) + 1):
                x_, y_ = net.getcurvevalue(curve_idx, i)
                x.append(x_)
                y.append(y_)

            r.setcurve(new_curve_idx, x, y, len(x))

            return new_curve_idx

        # Copy pattern
        for pat_id in net.get_all_patterns_id():
            if pat_id in patterns:
                continue

            pat_idx = net.getpatternindex(pat_id)
            pattern = net.get_pattern(pat_idx)

            patterns[pat_id] = pattern

            r.add_pattern(pat_id, pattern)

        # Copy nodes and links
        nodes_id = net.get_all_nodes_id()
        nodes_elevation = [net.get_node_elevation(node_idx)
                           for node_idx in net.get_all_nodes_idx()]
        nodes_type = [net.get_node_type(node_idx)
                      for node_idx in net.get_all_nodes_idx()]
        nodes_coord = [net.getcoord(node_idx)
                       for node_idx in net.get_all_nodes_idx()]
        nodes_comments = [net.get_node_comment(node_idx)
                          for node_idx in net.get_all_nodes_idx()]

        links_id = net.get_all_links_id()
        links_type = [net.get_link_type(link_idx)
                      for link_idx in net.get_all_links_idx()]
        links_data = net.get_all_links_connecting_nodes_id()
        links_diameter = [net.get_link_diameter(link_idx)
                          for link_idx in net.get_all_links_idx()]
        links_length = [net.get_link_length(link_idx)
                        for link_idx in net.get_all_links_idx()]
        links_roughness_coeff = [net.get_link_roughness(link_idx)
                                 for link_idx in net.get_all_links_idx()]
        links_bulk_coeff = [net.get_link_bulk_reaction_coeff(link_idx)
                            for link_idx in net.get_all_links_idx()]
        links_wall_coeff = [net.get_link_wall_reaction_coeff(link_idx)
                            for link_idx in net.get_all_links_idx()]
        links_loss_coeff = [net.get_link_minorloss(link_idx)
                            for link_idx in net.get_all_links_idx()]

        # Copy nodes
        for node_id, node_elevation, node_type, \
                node_coord, node_comment in zip(nodes_id, nodes_elevation, nodes_type, nodes_coord,
                                                nodes_comments):
            if node_id not in r.get_all_nodes_id():
                node_idx = net.get_node_idx(node_id)
                node_coord_x, node_coord_y = node_coord

                r.addnode(node_id, node_type)
                new_node_idx = r.get_node_idx(node_id)
                r.setcoord(new_node_idx, node_coord_x, node_coord_y)
                r.setnodevalue(new_node_idx, EpanetConstants.EN_ELEVATION, node_elevation)
                r.setcomment(EpanetConstants.EN_NODE, new_node_idx, node_comment)

                if node_type == EpanetConstants.EN_JUNCTION:

                    dem_pat_idx = net.getdemandpattern(node_idx, 1)
                    dem_pattern = net.getpatternid(dem_pat_idx) if dem_pat_idx != 0 else ""

                    r.setjuncdata(new_node_idx, node_elevation,
                                  sum([net.getbasedemand(node_idx, dmnd_idx + 1)
                                       for dmnd_idx in range(net.getnumdemands(node_idx))]),
                                       dem_pattern
                                  )
                elif node_type == EpanetConstants.EN_TANK:
                    node_tank_idx = net.get_node_idx(node_id)
                    diameter = float(net.get_tank_diameter(node_tank_idx))
                    max_level = float(net.get_tank_max_level(node_tank_idx))
                    min_level = float(net.get_tank_min_level(node_tank_idx))
                    minvol = float(net.getnodevalue(node_tank_idx, EpanetConstants.EN_MINVOLUME))
                    initvol = float(net.getnodevalue(EpanetConstants.EN_INITVOLUME))
                    volcurve_idx = int(net.getnodevalue(node_tank_idx, EpanetConstants.EN_VOLCURVE))
                    volcurve = net.getcurveid(volcurve_idx) if volcurve_idx != 0 else ""

                    if volcurve_idx != 0:
                        volcurve_new_idx = copy_curve(volcurve_idx)

                    initlvl = initvol / (0.25 * diameter**2 * math.pi)
                    r.settankdata(new_node_idx, node_elevation, initlvl, min_level, max_level, diameter, minvol, volcurve)

        # Copy links
        for link_id, link_type, link, diameter, length, roughness_coeff, bulk_coeff, \
            wall_coeff, loss_coeff in zip(links_id, links_type, links_data, links_diameter,
                                          links_length, links_roughness_coeff, links_bulk_coeff,
                                          links_wall_coeff, links_loss_coeff):
            link_idx = net.get_link_idx(link_id)

            r.addlink(link_id, link_type, link[0], link[1])
            new_link_idx = r.get_link_idx(link_id)

            r.setlinkvalue(new_link_idx, EpanetConstants.EN_INITSETTING,
                           net.getlinkvalue(link_idx, EpanetConstants.EN_INITSETTING))
            r.setlinkvalue(new_link_idx, EpanetConstants.EN_WALLORDER, wall_coeff)
            r.setlinkvalue(new_link_idx, EpanetConstants.EN_BULKORDER, bulk_coeff)

            if link_type == EpanetConstants.EN_PIPE:
                r.setpipedata(new_link_idx, length, diameter, roughness_coeff, loss_coeff)
            elif link_type == EpanetConstants.EN_PUMP:
                r.setlinkvalue(new_link_idx, EpanetConstants.EN_PUMP_ECOST,
                               net.getlinkvalue(link_idx, EpanetConstants.EN_PUMP_ECOST))
                # r.setlinkvalue(new_link_idx, EpanetConstants.EN_PUMP_POWER,
                #                net.getlinkvalue(link_idx, EpanetConstants.EN_PUMP_POWER))

                link_pattern_idx = int(net.getlinkvalue(link_idx, EpanetConstants.EN_LINKPATTERN))
                if link_pattern_idx != 0:
                    link_pattern_id = net.getpatternid(link_pattern_idx)
                    r.setlinkvalue(new_link_idx, EpanetConstants.EN_LINKPATTERN,
                                   r.getpatternindex(link_pattern_id))

                hcurve_idx = int(net.getlinkvalue(link_idx, EpanetConstants.EN_PUMP_HCURVE))
                if hcurve_idx != 0:
                    hcurve_new_idx = copy_curve(hcurve_idx)

                    # hcurve_id = net.getcurveid(hcurve_idx)
                    r.setlinkvalue(new_link_idx, EpanetConstants.EN_PUMP_HCURVE,
                                   hcurve_new_idx)

                ecurve_idx = int(net.getlinkvalue(link_idx, EpanetConstants.EN_PUMP_ECURVE))
                if ecurve_idx != 0:
                    ecurve_new_idx = copy_curve(ecurve_idx)

                    # ecurve_id = net.getcurveid(ecurve_idx)
                    r.setlinkvalue(new_link_idx, EpanetConstants.EN_PUMP_ECURVE,
                                   ecurve_new_idx)

                link_epattern_idx = int(net.getlinkvalue(link_idx, EpanetConstants.EN_PUMP_EPAT))
                if link_epattern_idx != 0:
                    link_epattern_id = net.getpatternid(link_epattern_idx)
                    r.setlinkvalue(new_link_idx, EpanetConstants.EN_PUMP_EPAT,
                                   r.getpatternindex(link_epattern_id))

        # Copy controls and rules
        for control_idx in range(1, net.get_num_controls() + 1):
            control_type, link_index, setting, node_index, level = net.getcontrol(control_idx)
            r.add_control(control_type, link_index, setting, node_index, level)

        for rule_idx in range(1, net.get_num_rules() + 1):
            raise NotImplementedError()

    return r
