# COSC2753_A2_S3_G7

This code is developed only to work in a Windows 11 machine with at least 32GB of RAM and an NVIDIA 4070 GPU. To run this code, ensure this configuration:

1. Download Anaconda.
2. In the conda prompt, create a new environment with Python 3.10.
3. Download TensorFlow 2.10 version, which is the latest version that supports NVIDIA GPU on Windows OS.
4. Uninstall the newest NumPy version to avoid conflict with older TensorFlow versions.
5. Download older NumPy version — 1.23.5.

Project Setup Instructions

1. Download and extract the dataset

   - Download the dataset ZIP file.
   - Unzip it so that the extracted folder is named train_images/.
   - Inside train_images/, you should see subfolders named by label, each containing the corresponding training images.

2. Place metadata and prediction files

   - Place the metadata file meta_train.csv at the same directory level as the train_images/ folder.
   - Also, place the prediction_submission.csv file at this root directory (same level as train_images/ and meta_train.csv). This file is used for prediction tasks.

3. Organize your task files

   - For any task-specific files (e.g., notebooks, scripts), put them in the root directory alongside meta_train.csv and train_images/.

4. Verify before running
   - train_images/ folder
   - meta_train.csv file
   - prediction_submission.csv file

Website: After extracting the file "A2_GUI", follow the instructions in its README.md to run the website code from the terminal.
