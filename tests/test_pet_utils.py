import pytest
import pathlib
import re
from petutils.petutils import get_versions, zip_nifti, write_out_dataset_description_json
from petutils.petutils import collect_anat_and_pet
import subprocess

project_dir = pathlib.Path(__file__).parent.parent.absolute()

def test_anat_in_no_session_folder(anat_in_no_session_folder):
    subprocess.run(["tree", anat_in_no_session_folder])
    a_and_p = collect_anat_and_pet(anat_in_no_session_folder)
    # check that for each pet file, there is a corresponding inherited anat file from the subject level
    for subject in a_and_p.keys():
        for pet_image, anat_image in a_and_p[subject].items():
            pet_image = pathlib.Path(pet_image)
            anat_image = pathlib.Path(anat_image)
            # check that the pet image is at least a subfolder deeper than the anat image
            assert len(pet_image.parts) > len(anat_image.parts)
            assert re.search(r"ses-", str(anat_image)) is None
            assert re.search(r"ses-", str(pet_image)) is not None
            assert re.search(r"nii|(.gz)", str(anat_image)) is not None

def test_anat_in_first_session_folder(anat_in_first_session_folder):
    subprocess.run(["tree", anat_in_first_session_folder])
    a_and_p = collect_anat_and_pet(anat_in_first_session_folder)
    for subject in a_and_p.keys():
        set_of_anat_images = set()
        set_of_pet_images = set()
        anat_exists_in_one_session_folder = False
        for pet_image, anat_image in a_and_p[subject].items():
            pet_image = pathlib.Path(pet_image)
            anat_image = pathlib.Path(anat_image)

            # add images to the set
            set_of_anat_images.add(str(anat_image))
            set_of_pet_images.add(str(pet_image))

            # check that at least one session contains both a pet and an anat image
            if re.search(r"ses-[^_|\/]*", str(anat_image))[0]  == re.search(r"ses-[^_|\/]*", str(pet_image))[0]:
                anat_exists_in_one_session_folder = True

        assert anat_exists_in_one_session_folder is True
        assert len(set_of_anat_images) == 1
        assert len(set_of_pet_images) == 1


def test_anat_in_first_session_folder_multi_sessions(anat_in_first_session_folder_multi_sessions):
    subprocess.run(["tree", anat_in_first_session_folder_multi_sessions])
    a_and_p = collect_anat_and_pet(anat_in_first_session_folder_multi_sessions)
    for subject in a_and_p.keys():
        set_of_anat_images = set()
        set_of_pet_images = set()
        anat_exists_in_one_session_folder = False
        for pet_image, anat_image in a_and_p[subject].items():
            pet_image = pathlib.Path(pet_image)
            anat_image = pathlib.Path(anat_image)

            # add images to the set
            set_of_anat_images.add(str(anat_image))
            set_of_pet_images.add(str(pet_image))

            # check that at least one session contains both a pet and an anat image
            if re.search(r"ses-[^_|\/]*", str(anat_image))[0]  == re.search(r"ses-[^_|\/]*", str(pet_image))[0]:
                anat_exists_in_one_session_folder = True
        print("!"*100)
        print(set_of_pet_images)
        assert anat_exists_in_one_session_folder is True
        assert len(set_of_anat_images) == 1
        assert len(set_of_pet_images) > 1


def test_anat_in_each_session_folder(anat_in_each_session_folder):
    subprocess.run(["tree", anat_in_each_session_folder])
    a_and_p = collect_anat_and_pet(anat_in_each_session_folder)
     # check that for each pet file, there is a corresponding anat file in the same session
    for subject in a_and_p.keys():
        for pet_image, anat_image in a_and_p[subject].items():
            pet_image = pathlib.Path(pet_image)
            anat_image = pathlib.Path(anat_image)
            # check that the pet image is at least a subfolder deeper than the anat image
            assert len(pet_image.parts) == len(anat_image.parts)
            assert re.search(r"ses-[^_|\/]*", str(anat_image))[0]  == re.search(r"ses-[^_|\/]*", str(pet_image))[0]
            assert re.search(r"nii|(.gz)", str(anat_image)) is not None

def test_multi_run_pet_scans(multi_run_pet_scans):
    subprocess.run(["tree", multi_run_pet_scans])
    a_and_p = collect_anat_and_pet(multi_run_pet_scans)
    for subject in a_and_p.keys():
        for pet_image, anat_image in a_and_p[subject].items():
            pet_image = pathlib.Path(pet_image)
            anat_image = pathlib.Path(anat_image)
            assert len(pet_image.parts) == len(anat_image.parts)
            assert re.search(r"ses-[^_|\/]*", str(anat_image))[0]  == re.search(r"ses-[^_|\/]*", str(pet_image))[0]
            assert re.search(r"nii|(.gz)", str(anat_image)) is not None