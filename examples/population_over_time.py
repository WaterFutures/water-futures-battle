from water_futures_battle import configure_system


if __name__ == "__main__":
    # Load and parse all data files
    settings, national_context, water_utilities = configure_system()

    # Print population over time of the "Nieuwegein (GM0356)" municipality.
    ng = national_context.state.municipality('Nieuwegein') # you can also search using the ID 'GM0356'
    print(f"The waterkwartier (KWR premises) is located in {ng.display_name}")
    
    print(f"The historical population in this town is: ")
    print(ng.population)  # Note that this municipality did not exist before 2006!
