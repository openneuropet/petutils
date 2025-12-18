import os
import shutil
import gzip
import pathlib
import json
from bids import BIDSLayout
from bids.layout.models import BIDSImageFile, BIDSJSONFile
from typing import Union
from difflib import get_close_matches


def get_versions():
     #collect version from pyproject.toml
    places_to_look = [pathlib.Path(__file__).parent.absolute(), pathlib.Path(__file__).parent.parent.absolute()]

    __version__ = "unable to locate version number in pyproject.toml"
    
    # we use the default version at the time of this writing, but the most current version
    # can be found in the pyproject.toml file under the [tool.bids] section
    __bids_version__ = "1.8.0"
    
    # search for toml file
    for place in places_to_look:
        for root, folders, files in os.walk(place):
            for file in files:
                if file.endswith("pyproject.toml"):
                    toml_file = os.path.join(root, file)

                    with open(toml_file, "r") as f:
                        for line in f.readlines():
                            if "version" in line and len(line.split("=")) > 1 and "bids_version" not in line:
                                __version__ = line.split("=")[1].strip().replace('"', "")
                            if "bids_version" in line and len(line.split("=")) > 1:
                                __bids_version__ = line.split("=")[1].strip().replace('"', "")
                    break
    return {"ingest_pet_version": __version__, "bids_version": __bids_version__}

def zip_nifti(nifti_file):
    """Zips an un-gzipped nifti file and removes the original file."""
    if str(nifti_file).endswith('.gz'):
        return nifti_file
    else:
        with open(nifti_file, 'rb') as infile:
            with gzip.open(nifti_file + '.gz', 'wb') as outfile:
                shutil.copyfileobj(infile, outfile)
        os.remove(nifti_file)
        return nifti_file + '.gz'

def write_out_dataset_description_json(input_bids_dir, output_bids_dir=None):

    # set output dir to input dir if output dir is not specified
    if output_bids_dir is None:
        output_bids_dir = pathlib.Path(os.path.join(input_bids_dir, "derivatives", "petdeface"))
        output_bids_dir.mkdir(parents=True, exist_ok=True)

    # collect name of dataset from input folder
    try:
        with open(os.path.join(input_bids_dir, 'dataset_description.json')) as f:
            source_dataset_description = json.load(f)
    except FileNotFoundError:
        source_dataset_description = {"Name": "Unknown"}

    with open(os.path.join(output_bids_dir, 'dataset_description.json'), 'w') as f:
        dataset_description = {
            "Name": f"description verygeneric - this is a placeholder: "
                    f"Not much to read here, if this has been published you've messed up`{source_dataset_description['Name']}`",
            "BIDSVersion": __bids_version__,
            "GeneratedBy": [
                {"Name": "TBD",
                 "Version": __version__,
                 "CodeURL": "https://github.com/someuser/someproject"}],
            "HowToAcknowledge": "This ________ uses ______________: `Someone, A., A Title. Journal, 2099. 12(3): p. 1-5.`,"
                                "and the ___________ developed by Some other person: `https://notarealurl.super.fake/extremelyfake`",
            "License": "CCBY"
        }

        json.dump(dataset_description, f, indent=4)

def collect_anat_and_pet(bids_data: Union[pathlib.Path, BIDSLayout], suffixes=["T1w", "T2w"], subjects: list=[], check_single_subject=False):
    if type(bids_data) is BIDSLayout:
        pass
    elif isinstance(bids_data, (pathlib.PosixPath, pathlib.WindowsPath)) and bids_data.exists():
        bids_data = BIDSLayout(bids_data)
    else:
        raise TypeError(f"{bids_data} must be a BIDSLayout or valid Path object, given type: {type(bids_data)}.")
    
    # return all subjects if no list of subjects is given
    if subjects == []:
        subjects = bids_data.get_subjects()

    mapped_pet_to_anat = {}
    for subject in subjects:
        mapped_pet_to_anat[subject] = {}
    for subject in subjects:
        pet_files = bids_data.get(subject=subject, suffix="pet")
        anat_files = [a.path for a in bids_data.get(suffix=suffixes, subject=subject, extension=["nii", "nii.gz"])]
        # for each pet image file we create an entry our mapping dictionary
        for entry in pet_files:
            if type(entry) is BIDSImageFile:
                try:
                    # search through anatomical files and find the closest match
                    mapped_pet_to_anat[subject][entry.path] = get_close_matches(entry.path, anat_files, n=1)[0]
                except IndexError:
                    mapped_pet_to_anat[subject][entry.path] = ''
    return mapped_pet_to_anat

class PETFrameTimingError(Exception):
    """Raised when frame timing information is inconsistent with NIFTI header or within a sidecar JSON file."""
    pass

def check_nifti_json_frame_consistency(bids_data: Union[pathlib.Path, BIDSLayout], subjects: list=[]):
    """
    This function checks the consistency of the frame timing information in the NIFTI header and the sidecar JSON file as well as 
    the number of entries between FrameTimesStart and FrameDuration within the sidecar JSON file. Intended to be used to either 
    direcly raise a PETFrameTimingError or return a dictionary of inconsistent files for each subject.
    
    If you are intending to later raise errors from the output of this function returned as a dictionary you should import 
    PETFrameTimingError from petutils and raise the error with the error string as the argument.

    Parameters
    ----------
    bids_data : Union[pathlib.Path, BIDSLayout]
        The path to the BIDS dataset or a BIDSLayout object.
    subjects : list, optional
        A list of subjects to check. If not given, all subjects in the dataset will be checked. If a single subject is given
        then an exception will be raised if any inconsistencies are found. The default is [].
    return : dict
        A dictionary of dictionaries containing the inconsistent files for each subject as well as the errors found.
        subject -> {errors: [error strings], files: {pet_file: json_file}}
    """
    if type(bids_data) is BIDSLayout:
        pass
    elif isinstance(bids_data, (pathlib.PosixPath, pathlib.WindowsPath)) and bids_data.exists():
        bids_data = BIDSLayout(bids_data)
    else:
        raise TypeError(f"{bids_data} must be a BIDSLayout or valid Path object, given type: {type(bids_data)}.")
    
    # We change the behavior of this function to raise an error if a single subject is given otherwise it returns
    # a dictionary of all the inconsistent files for each subject
    if len(subjects) == 1:
        check_single_subject = True
    else:
        check_single_subject = False

    # return all subjects if no list of subjects is given
    if subjects == []:
        subjects = bids_data.get_subjects()

    # inconsistent files will be stored as image files and their associated sidecar json files
    inconsistent_files = {}
    for subject in subjects:
        inconsistent_files[subject] = {'errors': [], 'files': {}}
        pet_files = bids_data.get(subject=subject, suffix="pet", extension=['nii', 'nii.gz'])
        for entry in pet_files:
            if type(entry) is BIDSImageFile:
                entry_image = entry.get_image()
                nii_frames = entry_image.header.get("dim")[4]
                error_string = []
                # build the path to the sidecar json
                entry_path = pathlib.Path(entry.path)
                if len(entry_path.suffixes) > 1:
                    entry_json = str(entry_path).replace('.nii.gz', '.json')
                else:
                    entry_json = str(entry_path).replace('.nii', '.json')
                
                # check that each frame timing info is the correct length as implied by the nifti header
                frame_timings = {"FrameTimesStart": len(entry.entities['FrameTimesStart']), "FrameDuration": len(entry.entities['FrameDuration'])}
                if frame_timings["FrameTimesStart"] != frame_timings["FrameDuration"]:
                        error_string.append(f"Number of entries for FrameTimesStart -> {frame_timings['FrameTimesStart']} and FrameDuration -> {frame_timings['FrameDuration']} do not match in {entry_json}")
                        inconsistent_files[subject]['files'][entry.path] = entry_json
                if frame_timings["FrameTimesStart"] != nii_frames:
                        error_string.append(f"Number frames in {entry.path} header -> {nii_frames} does not match the number of frames in FrameTimesStart -> {frame_timings['FrameTimesStart']} at {entry_json}")
                        inconsistent_files[subject]['files'][entry.path] = entry_json
                if frame_timings["FrameDuration"] != nii_frames:
                        error_string.append(f"Number frames in {entry.path} header -> {nii_frames} does not match the number of frames in FrameDuration -> {frame_timings['FrameDuration']} at {entry_json}")
                        inconsistent_files[subject]['files'][entry.path] = entry_json

                
                if len(error_string) > 0:
                        inconsistent_files[subject]['errors'] = error_string

                if check_single_subject:
                    # concat error string 
                    error_string = '\n'.join(error_string)
                    # raise error 
                    if len(error_string) > 0:
                        raise PETFrameTimingError(error_string)

    return inconsistent_files