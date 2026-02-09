from water_futures_battle.jurisdictions import build_state

def test_build_state():
    # Use a hardcoded file path (replace with a real test file path as needed)
    test_metadata_path = "./data/jurisdictions/jurisdictions-static_properties.xlsx"
    state = build_state(test_metadata_path)

    # Basic assertions
    assert state.display_name == "Netherlands"
    assert state.cbs_id == "NL0"
    # Check that regions are loaded
    assert len(state.regions) == 4
    # Check that at least one region has provinces
    for region in state.regions:
        assert len(state.provinces) == 12
        # Check that at least one province has municipalities
        for province in region.provinces:
            print(f"Prov {province.display_name} {len(province.municipalities)}")
            assert len(province.municipalities) > 0
            # Check that municipality has required fields
            for municipality in province.municipalities:
                assert hasattr(municipality, "latitude")
                assert hasattr(municipality, "longitude")
                assert hasattr(municipality, "elevation")