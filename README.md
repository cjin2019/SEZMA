# VideoAnalysis Software

## Requirements

### OS
Only compatible for macOS

### Packages

<!-- #### FFmpeg (Might not need it if doing screencapture command instead)
1. `git clone git@github.com:FFmpeg/FFmpeg.git`.
2. Before, installing add the following changes from `0001-added-milliseconds-to-filename.patch`.
3. `cd FFmpeg`: enter FFmpeg library to install
4. Follow installation from `ffmpeg` library: [link](https://github.com/FFmpeg/FFmpeg/blob/master/INSTALL.md). 
    1. To enable `libfontconfig`, install package libfontconfig1-dev
    2. Follow `./configure --help` to get some of the enabled extensions. In order to get drawtext filter to work, run `./configure --enable-libfreetype --enable-libfontconfig`.  -->

**NOTE: in [] should be changed to your config**

#### tcpdump
1. Enable `sudo` cmd without having to input password. Following steps are from this [blog](http://www.linuxtechnotes.com/2015/10/how-to-give-sudo-access-to-user-run.html) 
    1. Make a backup of `/etc/sudoers` file. (`cp /etc/sudoers /tmp/sudoers.date`)
    2. Edit the `/etc/sudoers` file. (`sudo visudo`)
    3. Add the entrie under User specification section: `[USERNAME] ALL=(root) NOPASSWD: /usr/sbin/tcpdump` 
    4. Go out of visudo: Escape button then type `wq!`
2. Test command: `sudo tcpdump`. It should output the current network stats. 

#### Python >=3.8 <=3.11.
1. Set up a virtual environment inside `videonetworkapp` directory using `python3 -m venv venv`
2. Activate the virtual environment with `source [/PATH/TO/]venv/bin/activate`. Following python packages are installed inside the virtual environment, make sure your virtual environment is activated.

##### Install external packages
1. Make sure your virtual environment is activated (`source [/PATH/TO/]venv/bin/activate`)
2. `python3 -m pip install -r requirements.txt`

<!-- ##### setuptools 
1. `pip3 install setuptools`

##### scapy
1. Follow the download and installation guidelines [here](https://scapy.readthedocs.io/en/latest/installation.html#installing-scapy-v2-x)
    1. `pip3 install scapy` inside your virtual environment `venv` -->

##### videonetworkapp
1. Make sure your virtual environment is activated (`source [/PATH/TO/]venv/bin/activate`)
<!-- 2. Inside `videonetworkapp/`, run `python3 -m pip install -e .` -->

### Commands to Run

#### Set up configuration
1. Edit `config.json` file to save to the data to appropriate location and run the screen capture for however long you like
<!-- 2. To get the appropriate device index, run `ffmpeg -f avfoundation -list_devices true -i ""`. Choose the number in `[]` that correspond to screen capture for video -->

#### Run app end-to-end
1. Start Zoom with one other person. 
2. Once, you start up your Zoom call is ready, run `python3 [/PATH/TO/]videonetworkapp/main.py` to capture data and produce graphs of the data 
<!-- #### Capture Zoom Screen
1. Activate virtual environment with `source /path/to/env/bin/activate`
2. `cd videonetworkapp` 
3. `python3 capture/tcpdump_cmd.py` -->

#### FAQ
###### Failure in Installing Requirements
<!-- 1. What if you run into `ERROR: fontconfig not found using pkg-config` when running `./configure --enable-libfreetype --enable-libfontconfig`? 
Make sure `fontconfig` and `pkg-config` is installed. You can install through `brew install fontconfig pkg-config` -->

