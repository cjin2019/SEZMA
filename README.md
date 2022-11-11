# VideoAnalysis Software

## Requirements

### OS
Only compatible for macOS

### Packages

#### FFmpeg 
1. `git clone git@github.com:FFmpeg/FFmpeg.git`.
2. Before, installing add the following changes from `0001-added-milliseconds-to-filename.patch`.
3. Follow installation from `ffmpeg` library: [link](git@github.com:FFmpeg/FFmpeg.git). 
    1. Follow `./configure --help` to get some of the enabled extensions. In order to get drawtext filter to work, run `./configure --enable-libfreetype --enable-libfontconfig`. 

#### tcpdump
1. Enable `sudo` cmd without having to input password. Follow this [blog](http://www.linuxtechnotes.com/2015/10/how-to-give-sudo-access-to-user-run.html) 

#### Python 3.8+.
1. Set up a virtual environment inside `videonetworkapp` directory using `python3 -m venv venv`
2. Activate the virtual environment with `source /path/to/venv/bin/activate`. Following python packages are installed inside the virtual environment, make sure your virtual environment is activated.

##### setuptools 
1. `pip3 install setuptools`

##### scapy
1. Follow the download and installation guidelines [here](https://scapy.readthedocs.io/en/latest/installation.html#installing-scapy-v2-x)
    1. `pip3 install scapy` inside your virtual environment `venv`

##### videonetworkapp
1. Make sure your virtual environment is activated (`source /path/to/venv/bin/activate`)
2. Inside `videonetworkapp/`, run `python3 -m pip install -e .`
