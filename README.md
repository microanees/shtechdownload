Download Show tech-support from Arista Switches
===============================================

The goal of this program is to download the show tech-support from any number of switches in the network from your computer.

By default show tech-support is scheduled to run every hour in Arista switches. The script will download the latest show tech-support file.

If show tech-support scheduler is disabled, the script will ask you whether you want to run the show tech-support on the switch and download the file.


Step 1: Install Python Modules
------------------------------

sudo pip install jsonrpclib

sudo pip install requests


Step 2: How to use the script
-----------------------------

Download the download_show_tech.py file.

Create a text file switches.txt and enter the switch IP addresses.

from your terminal

python download_show_tech.py -i /home/arista/show-tech/switches.txt switches.txt -o /home/arista/show-tech

The script will download the show tech-support file and store it in the /home/arista/show-tech folder.

The script will append the switch IP address before the show tech-support file.
