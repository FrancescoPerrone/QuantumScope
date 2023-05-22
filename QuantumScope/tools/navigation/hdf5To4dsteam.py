import os
import fnmatch
import h5py
import py4DSTEM
import numpy as np
import argparse
from QuantumScope.tools.navigation.hdf5To4dsteam import *

def get_file_list(filepath: str, file_extensions: list = ['*.h5', '*.hdf5']) -> list:
    """
    This function returns a sorted list of files in the specified directory that matches any of the specified file extensions.
    """
    if not os.path.isdir(filepath):
        raise FileNotFoundError(f"The specified directory does not exist: {filepath}")
    
    files = [file for file in os.listdir(filepath) for file_extension in file_extensions if fnmatch.fnmatch(file, file_extension)]
    files.sort()
    return files

def print_attrs(name, obj, datasets):
    if isinstance(obj, h5py.Dataset):
        print(f'Dataset path:  {name}')
        datasets[name] = obj

def load_4DSTEM_data(file_path, dataset_path):
    """
    Load a 4DSTEM dataset from a specified path within an HDF5 file.

    Parameters:
    file_path: str
        The path to the HDF5 file.
    dataset_path: str
        The path to the dataset within the HDF5 file.

    Returns:
    np.ndarray
        The loaded dataset.
    """

    with h5py.File(file_path, 'r') as f:
        if isinstance(dataset_path, (str, bytes)):
            if dataset_path in f:
                data = f[dataset_path][()]
                return data
            else:
                raise KeyError(f"The dataset path was not found in the file: {dataset_path}")
        else:
            raise TypeError(f"The dataset path must be a str or bytes, not {type(dataset_path)}")


def explore_and_load_4DSTEM_data(file_paths: list):
    """
    Explore the available datasets in a list of HDF5 files and prompt the user to select a dataset to load.
    The user is shown the path structure of the HDF5 file and asked to enter the path to the dataset they wish to load.
    If a valid dataset is selected, it is loaded and returned. If the user decides to change the file, a special keyword is returned.
    
    Parameters:
    file_paths: list
        The list of file paths to the HDF5 files.

    Returns:
    np.ndarray or str
        The loaded dataset, or a special keyword indicating the user's wish to change the file.
    """
    for file_path in file_paths:
        print(f'Exploring file: {file_path}')

        try:
            with h5py.File(file_path, 'r') as f:
                datasets = {}
                f.visititems(lambda name, obj: print_attrs(name, obj, datasets))
                while True:
                    print("Available datasets:")
                    for i, dataset_name in enumerate(datasets.keys(), start=1):
                        print(f"{i}: {dataset_name}")
                    dataset_index = input("Enter the number of the dataset you wish to load, or 'change file' to explore another file: ")
                    if dataset_index.lower() == 'change file':
                        return 'change file'
                    try:
                        dataset_index = int(dataset_index) - 1
                        dataset_path = list(datasets.keys())[dataset_index]
                        print(f'Trying to load: {file_path}/{dataset_path}')
                        data = datasets[dataset_path][()]
                        return data
                    except (ValueError, IndexError, KeyError, OSError) as e:
                        print(f'An error occurred while trying to load the dataset: {e}')
                        print('Please select a different dataset.')

        except OSError as e:
            print(f'An error occurred while trying to explore the file: {e}')

try:
    file_list = get_file_list(filepath, file_extensions)
    print('File list:')
    print(file_list)

    loaded_data = explore_and_load_4DSTEM_data(file_list)
    # Continue processing the dataset...

except (FileNotFoundError, OSError, KeyError) as e:
    print(e)


def visualize_4DSTEM_data(data):
    """
    Visualize a 4DSTEM dataset.

    Parameters:
    data: np.ndarray
        The 4DSTEM dataset.

    """

    # Create a DataCube object
    dataset = py4DSTEM.io.datastructure.DataCube(data = data)

    # Calculate max and mean diffraction patterns
    dataset.get_dp_max()
    dataset.get_dp_mean()

    # Visualize the computed diffraction patterns
    py4DSTEM.visualize.show_image_grid(
        lambda i:[
            dataset.tree['dp_mean'],
            dataset.tree['dp_max']
        ][i],
        H=1,
        W=2,
        cmap='turbo',
        scaling='power',
        power=0.25
    )

# Function to select a file from the file list
def select_file(file_list):
    print("Available files:")
    for i, file in enumerate(file_list):
        print(f"{i+1}: {file}")
    file_index = int(input("Enter the number of the file you want to explore, or 0 to quit: ")) - 1
    if file_index == -1:
        return None
    return file_list[file_index]
        
from . import hdf5To4dsteam
def main(filepath=None, file_extensions=None):
    while True:
        try:
            if filepath is None:
                __IPYTHON__
                filepath = input("Please enter the path to the directory containing the data files (or 'exit' to quit): ")
                if filepath.lower() == 'exit':
                    print("Exiting...")
                    return
                file_extensions = input("Please enter the list of file extensions to include (separated by spaces): ").split()
                if not os.path.isdir(filepath):
                    raise FileNotFoundError
            else:
                if not os.path.isdir(filepath):
                    print("Invalid directory. Please try again.")
                    filepath = None
                    continue
            # Get list of files
            try:
                file_list = _4dsteam.get_file_list(filepath, file_extensions)
                print('File list:')
                print(file_list)
            except FileNotFoundError as e:
                print("Invalid directory. Please try again.")
                filepath = None
                continue

            # User selects file
            while True:
                selected_file = _4dsteam.select_file(file_list)
                if selected_file is None:
                    print("Exiting...")
                    break

                # Load and visualize data for the selected file
                full_file_path = os.path.join(filepath, selected_file)
                loaded_data = _4dsteam.explore_and_load_4DSTEM_data([full_file_path])  # Pass a list with a single file path
                if loaded_data == 'change file':
                    continue
                try:
                    _4dsteam.visualize_4DSTEM_data(loaded_data)
                except Exception as e:
                    print(f'An error occurred while trying to visualize the dataset: {e}')
        finally:
            filepath = None

if __name__ == "__main__":
    main()
