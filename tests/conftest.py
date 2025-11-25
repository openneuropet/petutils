import pathlib
import pytest
import shutil
import tempfile
import os

# our first steps to testing are to build the different types of bids datasets that we expect to encounter
# these are:
# 1. a dataset with an anatomical scan at the top level and a pet scan below it in a session folder
# 2. a dataset with the anatomical scan pet scan contained in the same session folder
# 3. a dataset with the anatomical scan in the first session folder and multiple pet scan sessions that share that anatomical scan
# 4. a dataset with multiple anatomical scans and pet scans contained in the same session folder

# collect test bids dataset from data directory
data_dir = pathlib.Path(__file__).parent.parent / "data"

# 1
@pytest.fixture
def anat_in_no_session_folder(tmpdir):
    dest_dir = pathlib.Path(tmpdir) / "anat_in_subject_folder"
    shutil.copytree(data_dir, dest_dir)

    original_anat_folder = (
        dest_dir / "sub-01" / "ses-baseline" / "anat"
    )
    subject_folder = dest_dir / "sub-01"
    # now we move the anatomical folder in the first session of our test data into the subject level folder
    shutil.move(original_anat_folder, subject_folder)

    inherited_anat_folder = subject_folder / "anat"

    # and next remove the ses- entities from the files in the newly created anat folder
    for file in inherited_anat_folder.glob("sub-01_ses-baseline_*"):
        shutil.move(
            file,
            pathlib.Path(tmpdir)
            / "anat_in_subject_folder"
            / "sub-01"
            / "anat"
            / file.name.replace("ses-baseline_", ""),
        )
    return dest_dir

# 2
@pytest.fixture
def anat_in_first_session_folder(tmpdir):
    dest_dir = pathlib.Path(tmpdir) / "anat_in_first_session_folder"
    shutil.copytree(data_dir, dest_dir)
    return dest_dir

# 3
@pytest.fixture
def anat_in_first_session_folder_multi_sessions(tmpdir):
    dest_dir = pathlib.Path (tmpdir) / "anat_in_first_session_folder_multi_sessions"
    shutil.copytree(data_dir, dest_dir)

    # create a second session
    second_session_folder = (
        dest_dir / "sub-01" / "ses-second"
    )
    second_session_folder.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        dest_dir / "sub-01" / "ses-baseline",
        second_session_folder,
        dirs_exist_ok=True,
    )

    # replace the ses- entities in the files in the newly created second session folder
    for file in second_session_folder.glob("pet/*"):
        shutil.move(
            file,
            second_session_folder
            / "pet"
            / file.name.replace("ses-baseline_", "ses-second_"),
        )

    # remove anat in second session folder
    shutil.rmtree(second_session_folder / "anat")
    
    return dest_dir

# 4
@pytest.fixture
def anat_in_each_session_folder(tmpdir):
    dest_dir = pathlib.Path(tmpdir) / "anat_in_each_session_folder"
    shutil.copytree(data_dir, dest_dir)

    # create a second session
    second_session_folder = (
        dest_dir / "sub-01" / "ses-second"
    )
    second_session_folder.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        dest_dir / "sub-01" / "ses-baseline",
        second_session_folder,
        dirs_exist_ok=True,
    )

    # replace the ses- entities in the files in the newly created second session folder
    for file in second_session_folder.glob("pet/*"):
        shutil.move(
            file,
            second_session_folder
            / "pet"
            / file.name.replace("ses-baseline_", "ses-second_"),
        )

    for file in second_session_folder.glob("anat/*"):
        shutil.move(
            file,
            second_session_folder
            / "anat"
            / file.name.replace("ses-baseline_", "ses-second_"),
        )
    return dest_dir

#5 - test dataset with multi run pet scans
@pytest.fixture
def multi_run_pet_scans(tmpdir):
    dest_dir = pathlib.Path(tmpdir) / "multi_run_pet_scans"
    shutil.copytree(data_dir, dest_dir)

    runs = ["01", "02"]

    for run in runs:
        shutil.copy(
            dest_dir / "sub-01" / "ses-baseline" / "pet" / "sub-01_ses-baseline_pet.nii.gz",
            dest_dir / "sub-01" / "ses-baseline" / "pet" / f"sub-01_ses-baseline_run-{run}_pet.nii.gz",
        )
        shutil.copy(
            dest_dir / "sub-01" / "ses-baseline" / "pet" / "sub-01_ses-baseline_pet.json",
            dest_dir / "sub-01" / "ses-baseline" / "pet" / f"sub-01_ses-baseline_run-{run}_pet.json",
        )
    
    os.remove(dest_dir / "sub-01" / "ses-baseline" / "pet" / "sub-01_ses-baseline_pet.nii.gz")
    os.remove(dest_dir/ "sub-01" / "ses-baseline" / "pet" / "sub-01_ses-baseline_pet.json")

    return dest_dir

# Helper function to convert single run PET scans to multi-run
def convert_to_multi_run(dest_dir):
    """Convert all single-run PET scans in a directory to multi-run (run-01, run-02)"""
    runs = ["01", "02"]
    
    # Find all PET files without run entities
    for pet_file in dest_dir.glob("**/pet/*_pet.nii.gz"):
        if "run-" not in pet_file.name:
            # Create run-01 and run-02 versions
            for run in runs:
                new_name = pet_file.name.replace("_pet.nii.gz", f"_run-{run}_pet.nii.gz")
                shutil.copy(pet_file, pet_file.parent / new_name)
            # Remove original
            os.remove(pet_file)
    
    # Do the same for JSON sidecars
    for json_file in dest_dir.glob("**/pet/*_pet.json"):
        if "run-" not in json_file.name:
            for run in runs:
                new_name = json_file.name.replace("_pet.json", f"_run-{run}_pet.json")
                shutil.copy(json_file, json_file.parent / new_name)
            os.remove(json_file)

# 1 - Multi-run version
@pytest.fixture
def anat_in_no_session_folder_multi_run(tmpdir):
    dest_dir = pathlib.Path(tmpdir) / "anat_in_subject_folder_multi_run"
    shutil.copytree(data_dir, dest_dir)

    original_anat_folder = (
        dest_dir / "sub-01" / "ses-baseline" / "anat"
    )
    subject_folder = dest_dir / "sub-01"
    # now we move the anatomical folder in the first session of our test data into the subject level folder
    shutil.move(original_anat_folder, subject_folder)

    inherited_anat_folder = subject_folder / "anat"

    # and next remove the ses- entities from the files in the newly created anat folder
    for file in inherited_anat_folder.glob("sub-01_ses-baseline_*"):
        shutil.move(
            file,
            pathlib.Path(tmpdir)
            / "anat_in_subject_folder_multi_run"
            / "sub-01"
            / "anat"
            / file.name.replace("ses-baseline_", ""),
        )
    
    # Convert to multi-run
    convert_to_multi_run(dest_dir)
    
    return dest_dir

# 2 - Multi-run version
@pytest.fixture
def anat_in_first_session_folder_multi_run(tmpdir):
    dest_dir = pathlib.Path(tmpdir) / "anat_in_first_session_folder_multi_run"
    shutil.copytree(data_dir, dest_dir)
    
    # Convert to multi-run
    convert_to_multi_run(dest_dir)
    
    return dest_dir

# 3 - Multi-run version
@pytest.fixture
def anat_in_first_session_folder_multi_sessions_multi_run(tmpdir):
    dest_dir = pathlib.Path (tmpdir) / "anat_in_first_session_folder_multi_sessions_multi_run"
    shutil.copytree(data_dir, dest_dir)

    # create a second session
    second_session_folder = (
        dest_dir / "sub-01" / "ses-second"
    )
    second_session_folder.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        dest_dir / "sub-01" / "ses-baseline",
        second_session_folder,
        dirs_exist_ok=True,
    )

    # replace the ses- entities in the files in the newly created second session folder
    for file in second_session_folder.glob("pet/*"):
        shutil.move(
            file,
            second_session_folder
            / "pet"
            / file.name.replace("ses-baseline_", "ses-second_"),
        )

    # remove anat in second session folder
    shutil.rmtree(second_session_folder / "anat")
    
    # Convert to multi-run
    convert_to_multi_run(dest_dir)
    
    return dest_dir

# 4 - Multi-run version
@pytest.fixture
def anat_in_each_session_folder_multi_run(tmpdir):
    dest_dir = pathlib.Path(tmpdir) / "anat_in_each_session_folder_multi_run"
    shutil.copytree(data_dir, dest_dir)

    # create a second session
    second_session_folder = (
        dest_dir / "sub-01" / "ses-second"
    )
    second_session_folder.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        dest_dir / "sub-01" / "ses-baseline",
        second_session_folder,
        dirs_exist_ok=True,
    )

    # replace the ses- entities in the files in the newly created second session folder
    for file in second_session_folder.glob("pet/*"):
        shutil.move(
            file,
            second_session_folder
            / "pet"
            / file.name.replace("ses-baseline_", "ses-second_"),
        )

    for file in second_session_folder.glob("anat/*"):
        shutil.move(
            file,
            second_session_folder
            / "anat"
            / file.name.replace("ses-baseline_", "ses-second_"),
        )
    
    # Convert to multi-run
    convert_to_multi_run(dest_dir)
    
    return dest_dir