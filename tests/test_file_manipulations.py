from petutils import collect_runs 
import re


def test_collect_runs_groups_by_run_pattern(multi_run_pet_scans):
    """Test that collect_runs finds and groups files with run entities."""
    # Use the data directory directly - it has ses-multirun with run-01 and run-02
    grouped = collect_runs(multi_run_pet_scans)
    
    # Should have found grouped runs
    assert len(grouped) > 0
    
    # Each group key should have _run-XX placeholder
    for key in grouped.keys():
        assert '_run-XX' in key
    
    # Find the multirun PET group
    multirun_keys = [k for k in grouped.keys() if 'run' in k and '_pet' in k]
    
    # Should have at least one group for the multirun session
    assert len(multirun_keys) >= 1
    
    for key in multirun_keys:
        runs = grouped[key]
        # Should have 2 runs (run-01 and run-02)
        assert len(runs) == 2
        
        # Runs should be sorted
        run_numbers = [re.search(r'run-(\d+)', str(r)).group(1) for r in runs]
        assert run_numbers == sorted(run_numbers)
        
        # Verify the files exist
        for run_path in runs:
            assert run_path.exists()


def test_collect_runs_includes_json_sidecars(multi_run_pet_scans):
    """Test that both .nii.gz and .json files are collected."""
    grouped = collect_runs(multi_run_pet_scans)
    
    # Should have groups for both nifti and json files
    nii_groups = [k for k in grouped.keys() if '.nii' in k]
    json_groups = [k for k in grouped.keys() if '.json' in k]
    
    assert len(nii_groups) > 0
    assert len(json_groups) > 0