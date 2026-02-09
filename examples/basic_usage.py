from water_futures_battle import configure_system


if __name__ == "__main__":
    # Load and parse all data files
    settings, national_context, water_utilities = configure_system()

    # Query objects
    print(f"Number of water utilities: {len(water_utilities)}")
