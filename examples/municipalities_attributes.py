from water_futures_battle import configure_system
from water_futures_battle.core import get_snapshot

if __name__ == "__main__":
    # Load and parse all data files
    settings, national_context, water_utilities = configure_system()

    # List all attributes in the year 2012 from all municipalities (considering all utilties)
    for wu in water_utilities:
        print(f"Utility ID: {wu.bwf_id}")

        # Get all municpalities in the year 2012
        for muni in wu.active_municipalities(when=2012):  # Note that not all municipalities exist at all times
            muni = get_snapshot(muni, 2012)   # We are interested in the year 2012 only!

            # Get the municpality's attributes
            print(f"    Municipality name: {muni.display_name}")
            print(f"        Population size: {muni.population}")
            print(f"        Number of houses: {muni.n_houses}")
            print(f"        Number of businesses: {muni.n_businesses}")
            print(f"        Average income: {muni.disp_income_avg}")
            print(f"        Total number of km of pipes: {muni.dist_network_length}")

            # Dynamic endogenous properties (e.g., average age of the inner distribution network)
            # can not be queried until after the evaluation
