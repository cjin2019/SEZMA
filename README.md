# VideoAnalysis Software

## Requirements

### OS
Only compatible for macOS 10.12+.

### Permisions

In order to run this app, you must run in `sudo` on Terminal.
### Installation

**NOTE: in [] should be changed to your config**

<!-- #### tcpdump
1. Test command: `sudo tcpdump`. It should output the current network stats, like below
```
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on eth0, link-type EN10MB (Ethernet), capture size 65535 bytes
21:02:19.112502 IP test33.ntp > 199.30.140.74.ntp: NTPv4, Client, length 48
21:02:19.113888 IP 216.239.35.0.ntp > test33.ntp: NTPv4, Server, length 48
21:02:20.150347 IP test33.ntp > 216.239.35.0.ntp: NTPv4, Client, length 48
21:02:20.150991 IP 216.239.35.0.ntp > test33.ntp: NTPv4, Server, length 48
```  -->

<!-- #### tcpdump
1. Enable `sudo` cmd without having to input password. Following steps are from this [blog](http://www.linuxtechnotes.com/2015/10/how-to-give-sudo-access-to-user-run.html) 
    1. Make a backup of `/etc/sudoers` file. (`cp /etc/sudoers /tmp/sudoers_[MM_DD_YYYY]`, replacing with the current date)
    2. Edit the `/etc/sudoers` file. (`sudo visudo`)
    3. Add the entry under _User specification_ section: `[USERNAME] ALL=(root) NOPASSWD: /usr/sbin/tcpdump` 
    4. Go out of visudo: Escape button then type `wq!`
2. Test command: `sudo tcpdump`. It should output the current network stats, like below
```
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on eth0, link-type EN10MB (Ethernet), capture size 65535 bytes
21:02:19.112502 IP test33.ntp > 199.30.140.74.ntp: NTPv4, Client, length 48
21:02:19.113888 IP 216.239.35.0.ntp > test33.ntp: NTPv4, Server, length 48
21:02:20.150347 IP test33.ntp > 216.239.35.0.ntp: NTPv4, Client, length 48
21:02:20.150991 IP 216.239.35.0.ntp > test33.ntp: NTPv4, Server, length 48
``` 
3. **NOTE: This may have some security issues. You may want to comment Step 1.3 out when not using the app** -->

<!-- #### Xcode Command Line Tools
1. You must have an AppleID to install tool
2. Enable to run `swift` on terminal. Following steps are from [here](https://apple.stackexchange.com/a/254381)
    1. Run `xcode-select --install` to install Xcode command line tools. You do not need Xcode; you can install only the command line.
    2. If you are running into issues, run `sudo xcode-select --reset` then step 1.1.
2. Test command: `swift`. It should output a Welcome message.  -->

#### libpcap
1. `brew install libpcap`. If you don't have `homebrew` installed, you can install with:
   `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`[link](https://brew.sh/)
#### Screen Capture 
1. You will need permissions to screen capture from Terminal. 
    1. Go to Settings > Privacy & Security > Screen Recording. 
    2. Add Terminal to allowed applications.
2. **NOTE: May be a security issue. Remove terminal from allowed apps when done using**


### How to Run the App From Binary

#### Mac M1 App File

##### Set Up
Open up Terminal App. All the following commands will be run in Terminal.
1. Once you unzip the file, `cd /path/to/distribute_app`.
2. In`config.ini` file,
    1. REQUIRED: "OutputDirectoryt": filepath of directory to store data
    2. REQUIRED: "FrameRate": the screen capture at an initial frame capture rate (frames per second). The default frame capture rate may be too high for your laptop, in which case the frame rate will be reduced.  
    3. REQUIRED "KeyFilePath": filepath of the key file of centralized server to send results. Otherwise, set to NOT GIVEN
3. `sudo videonetworkapp.app/Contents/MacOS/videonetworkapp `. If a pop-up starting with " "videonetworkapp" can't be opened because Apple cannot check it for malicious software" opens, click OK. 
    1. You will need to give permissions to run the app. Open Privacy & Security in Settings and scroll down until you see " "videonetworkapp" was blocked from use because it is not from an identified developer". Click Open Anyway. 
    2. If the pop-up of " "videonetworkapp" can't be opened because Apple cannot check it for malicious software" opens again, click Open. The app will pop up, run, and then close. 
4. `cp config.ini videonetworkapp.app/Contents/MacOS/config.ini`
5. Run `sudo videonetworkapp.app/Contents/MacOS/videonetworkapp` again. It should work now. 

##### Update
1. If you want to update your `config.ini`, update as described in Set Up 2.1 and/or 2.2
2. `cp config.ini videonetworkapp.app/Contents/MacOS/config.ini`

#### Mac Intel App File

##### Set Up
Open up Terminal App. All the following commands will be run in Terminal.
1. Once you unzip the file, `cd /path/to/distribute_app`.
2. In`config.ini` file,
    1. REQUIRED: "OutputDirectoryt": filepath of directory to store data
    2. REQUIRED: "FrameRate": the screen capture at an initial frame capture rate (frames per second). The default frame capture rate may be too high for your laptop, in which case the frame rate will be reduced.  
    3. REQUIRED "KeyFilePath": filepath of the key file of centralized server to send results. Otherwise, set to NOT GIVEN
3. `sudo ./videonetworkapp.bin`. If a pop-up starting with " "videonetworkapp.bin" can't be opened because Apple cannot check it for malicious software" opens, click OK. 
    1. You will need to give permissions to run the app. Open Privacy & Security in Settings and scroll down until you see " "videonetworkapp.bin" was blocked from use because it is not from an identified developer". Click Open Anyway. 
    2. If the pop-up of " "videonetwork.bin" can't be opened because Apple cannot check it for malicious software" opens again, click Open. The app will pop up, run, and then close. 
4. Run `sudo ./videonetworkapp.bin` again. It should work now. 

##### Update
1. If you want to update your `config.ini`, update as described in Set Up 2.1 and/or 2.2


### How to Run App from Codebase

#### Install

1. Requires Python >= 3.8 and <= 3.10
2. Run `./install.sh`

#### Run

1. Edit `config.ini` file to save 
    1. REQUIRED: "OutputDirectoryt": filepath of directory to store data
    2. REQUIRED: "FrameRate": the screen capture at an initial frame capture rate (frames per second). The default frame capture rate may be too high for your laptop, in which case the frame rate will be reduced.  
    3. REQUIRED "KeyFilePath": filepath of the key file of centralized server to send results. Otherwise, set to NOT GIVEN
2. `sudo ./run.sh`

#### Monitor Run

1. If you want to check usage, you can use `sudo ./monitor.sh`

### Binarize Python Codebase with Nuitka

1. Activate your virtual environment. `source venv/bin/activate`.
2. If nuitka not installed, run `python3 -m pip install -U nuitka`
3. Mac M1 command: `python3 -m nuitka --onefile --include-plugin-directory=app --include-data-files=/Users/carolinejin/Documents/meng_project/videonetworkapp/app/video/metrics/niqe_image_params.mat=app/video/metrics/niqe_image_params.mat --macos-create-app-bundle videonetworkapp.py` --> python used homebrew python3.9 (did not work with installed python in M1 due to recursion import error)
4. Macbook Intel Laptop: `python3 -m nuitka --follow-imports --include-plugin-directory=app videonetworkapp.py`

<!-- #### Python 3.9. -->
<!-- 1. Set up a virtual environment inside `videonetworkapp` directory using `python3 -m venv venv`
2. Activate the virtual environment with `source [/PATH/TO/]venv/bin/activate`. Following python packages are installed inside the virtual environment, make sure your virtual environment is activated.
3. If you want to have multiple Python versions, you can follow [this](https://stackoverflow.com/questions/36968425/how-can-i-install-multiple-versions-of-python-on-latest-os-x-and-use-them-in-par)


##### videonetworkapp
1. Make sure your virtual environment is activated (`source [/PATH/TO/]venv/bin/activate`)
<!-- 2. Inside `videonetworkapp/`, run `python3 -m pip install -e .` -->

<!-- ### Commands to Run

#### Set up configuration
Edit `config.ini` file to save to the data to appropriate location and run the screen capture at an initial frame capture rate. The default frame capture rate may be too high for your laptop, in which case the frame rate will be
reduced.  -->
<!-- 1. Edit `config.json` file to save to the data to appropriate location and run the screen capture for however long you like -->
<!-- 2. To get the appropriate device index, run `ffmpeg -f avfoundation -list_devices true -i ""`. Choose the number in `[]` that correspond to screen capture for video -->

<!-- #### Run app end-to-end
1. Start Zoom with at least one other person. 
2. Once, you start up your Zoom call is ready, run `sudo python3 [/PATH/TO/]videonetworkapp/videonetworkapp.py` to capture data and produce graphs of the data -->
<!-- 2. Once, you start up your Zoom call is ready, run `python3 [/PATH/TO/]videonetworkapp/main.py` to capture data and produce graphs of the data  -->
<!-- #### Capture Zoom Screen
1. Activate virtual environment with `source /path/to/env/bin/activate`
2. `cd videonetworkapp` 
3. `python3 capture/tcpdump_cmd.py` -->

#### FAQ
###### Failure in Installing Requirements

###### Failure in Running
1. `scapy.error.Scapy_Exception: Can't attach the BPF filter !`: `libpcap` may not have been installed. Run the following commands in terminal:
    1. `brew update`
    2. `brew install libpcap`
    3. `scapy`: to open scapy in terminal
    4. Once in the scapy terminal, run `conf.use_pcap = True`
<!-- 1. What if you run into `ERROR: fontconfig not found using pkg-config` when running `./configure --enable-libfreetype --enable-libfontconfig`? 
Make sure `fontconfig` and `pkg-config` is installed. You can install through `brew install fontconfig pkg-config` -->

