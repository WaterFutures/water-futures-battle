from water_futures_battle import configure_system

if __name__ == "__main__":
    # Load and parse all data files
    settings, national_context, water_utilities = configure_system()

    print(f"Inflation in {national_context.state.display_name} has been: ")
    print(national_context.inflation)
    