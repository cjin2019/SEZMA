# SEZMA

## Requirements

### OS
Only compatible for macOS 12+.

### Permisions

In order to run this app, you must run in `sudo` on Terminal.
### Installation - Outisde App

**NOTE: in [] should be changed to your config**

#### libpcap
1. `brew install libpcap`. If you don't have `homebrew` installed, you can install with:
   `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`[link](https://brew.sh/)
#### Screen Capture 
1. You will need permissions to screen capture from Terminal. 
    1. Go to Settings > Privacy & Security > Screen Recording. 
    2. Add Terminal to allowed applications.
2. **NOTE: May be a security issue. Remove terminal from allowed apps when done using**


### How to Run the App From Binary

#### Mac M1/Intel App File

##### Set Up
Open up Terminal App. All the following commands will be run in Terminal.
1. Once you unzip the file, `cd /path/to/mac_arm_macos_13` or `cd /path/to/mac_x86_64_macos_12`s
2. In`config.json` file,
    1. REQUIRED: "OutputDirectory": absolute filepath of directory to store data
    2. REQUIRED: "FrameRate": the screen capture at an initial frame capture rate (frames per second). The default frame capture rate may be too high for your laptop, in which case the frame rate will be reduced.  
    3. REQUIRED: "VideoFrameMetricsUsed": The default metrics shows all metrics available. You may remove metrics as you like. Note: the most intensive computation to least is NIQE, PIQE, and LAPLACIAN. You may want to start with LAPLACIAN first.
    3. NO CHANGE "IPAddress": IP address of the centralized server. 
3. `sudo videonetworkapp.app/Contents/MacOS/videonetworkapp `. If a pop-up starting with " "videonetworkapp" can't be opened because Apple cannot check it for malicious software" opens, click OK. 
    1. You will need to give permissions to run the app. Open Privacy & Security in Settings and scroll down until you see " "videonetworkapp" was blocked from use because it is not from an identified developer". Click Open Anyway. 
    2. If the pop-up of " "videonetworkapp" can't be opened because Apple cannot check it for malicious software" opens again, click Open. The app will pop up, run, and then close. 
4. `cp config.json videonetworkapp.app/Contents/MacOS/config.json`
5. Run `sudo videonetworkapp.app/Contents/MacOS/videonetworkapp` again. It should work now. 

##### Update
1. If you want to update your `config.ini`, update as described in Set Up 2.1 and/or 2.2
2. `cp config.ini videonetworkapp.app/Contents/MacOS/config.ini`

### How to Run App from Codebase

#### Install

1. Requires Python >= 3.8 and <= 3.10
2. Once you unzip file, `cd /path/to/videonetworkapp_codebase`
3. Run `./install.sh`

#### Run
Open up Terminal App. All the following commands will be run in Terminal.
1. Edit `config.ini` file to save 
    1. REQUIRED: "OutputDirectory": absolute filepath of directory to store data
    2. REQUIRED: "FrameRate": the screen capture at an initial frame capture rate (frames per second). The default frame capture rate may be too high for your laptop, in which case the frame rate will be reduced.  
    3. NO CHANGE "IPAddress": IP address of the centralized server. 
2. `cd /path/to/videonetworkapp_codebase`
3. `sudo ./run.sh`

#### Monitor Run

1. If you want to check usage, you can use `sudo ./monitor.sh`

### Binarize Python Codebase with Nuitka

1. Activate your virtual environment. `source venv/bin/activate`.
2. If nuitka not installed, run `python3 -m pip install -U nuitka`
3. Mac command: `python3 -m nuitka --onefile --include-plugin-directory=app --include-data-files=/path/to/videonetworkapp/app/video/metrics/niqe_image_params.mat=app/video/metrics/niqe_image_params.mat --macos-create-app-bundle videonetworkapp.py` --> python used homebrew python3.9 (did not work with installed python in M1 due to recursion import error)

#### FAQ
###### Failure in Installing Requirements

###### Failure in Running
1. `scapy.error.Scapy_Exception: Can't attach the BPF filter !`: `libpcap` may not have been installed. Run the following commands in terminal:
    1. `brew update`
    2. `brew install libpcap`
    3. `scapy`: to open scapy in terminal
    4. Once in the scapy terminal, run `conf.use_pcap = True`
2. When trying to binarize the package, I ran into `cv2` recursion import error. This is due to python3 Apple version. Try using `homebrew`'s python version instead. 
<!-- 1. What if you run into `ERROR: fontconfig not found using pkg-config` when running `./configure --enable-libfreetype --enable-libfontconfig`? 
Make sure `fontconfig` and `pkg-config` is installed. You can install through `brew install fontconfig pkg-config` -->

