# Copyright (c) 2016, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#
# Author = Anees Mohammed
#

from jsonrpclib import Server, ProtocolError
import getpass
import argparse
import requests
import sys
import ssl
ssl._create_default_https_context = ssl._create_unverified_context


# Input/Output files
parser = argparse.ArgumentParser()
parser.add_argument("-i", help="File name with the list of switches")
parser.add_argument("-o", help="Path to write the show tech of the switches")
args = parser.parse_args()

if not args.i or not args.o:
    print('-i and -o are mandatory')
    print("syntax is")
    print("python sh_tech_copy.py -i /path../switches.txt -o /path../sh-tech")
    print("example....")
    print("python sh_tech_copy.py -i switches.txt -o ./sh-tech")
    sys.exit(2)

switches_file = args.i
output_path = args.o

# Input Device Authentication Credentials
username = raw_input("User Name: ")
password = getpass.getpass("Password: ")


# Helper functions

def eapi_connection(switch):
    # define eapi connection string
    node = Server("https://" + username + ":" +
                  password + "@" + switch.strip() +
                  "/command-api")

    return node


def check_shtech_scheduler(node):
    try:
        # check whether auto show tech is enabled
        shtech_scheduler = node.runCmds(1, [
            "enable", "show schedule tech-support"], "text")
        # if the command is successful, it is enabled
        shtech_enabled = "Yes"

    except ProtocolError as e:
        shtech_enabled = "No"

    except:
        shtech_enabled = "eAPI Connection Error"

    return shtech_enabled


def download_shtech_file(node, switch):
    try:
        # Identify  the latest show tech file name
        latest_shtech_cmd = "bash timeout 10  ls /mnt/flash/schedule/tech-support -rt | tail -n 1"
        latest_file_json = node.runCmds(1, ["enable", latest_shtech_cmd], "text")
        latest_file_name = latest_file_json[1]["output"]
        print "Latest show tech file name is " + latest_file_name

        # Copy the file to the downloadable location
        print "copying the file to http folder"
        cp_command = "bash timeout 10 sudo cp /mnt/flash/schedule/tech-support/" + latest_file_name + " /usr/share/nginx/html"
        chmod_file_command = "bash timeout 10 sudo chmod 444 /usr/share/nginx/html/" + latest_file_name

        node.runCmds(1, ["enable", cp_command], "text")
        node.runCmds(1, ["enable", chmod_file_command], "text")

        # Download the file
        print "Downloading the file"
        url = "http://" + switch + "/" + latest_file_name
        get_file = requests.get(url.strip())

        # Create a File Name
        file_name = switch + "_" + latest_file_name
        output_file = output_path + "/" + file_name.strip()

        # Write the file to local disk
        print "Saving the File as " + file_name

        with open(output_file, "wb") as data:
            data.write(get_file.content)

        # Delete the file from the downloadable location
        rm_file_command = "bash timeout 10 sudo rm -f /usr/share/nginx/html/" + latest_file_name
        node.runCmds(1, ["enable", rm_file_command], "text")

    except ProtocolError as e:
        errors = "Invalid EOS Command" + str(e)
        return errors

    except:
        errors = "eAPI Connection Error"
        return errors


def run_show_tech_download(switches):
    for each_switch in switches:
        try:
            # Define eapi Connection
            node = eapi_connection(each_switch)

            # run show tech and save it in the downloadable location
            print "running show tech in " + each_switch
            sh_tech_command = "show tech-support >> /schedule/tech-support/tech-support.log"
            node.runCmds(1, ["enable", sh_tech_command], "text")

            # Download the show tech files
            download_shtech_file(node, each_switch.strip())

        except ProtocolError as e:
            errors = "Invalid EOS Command" + str(e)
            return errors

        except:
            errors = "eAPI Connection Error"
            return errors


def main():
    """
    main program

    input device authentication credential.

    read the list of switch ip addresses
    from the text file.

    for each switch download show tech files
    using the helper functions.

    """

    # Build the list of switches
    switches = []

    with open(switches_file) as readtext:
        for each_line in readtext:
            switches.append(str(each_line))

    # Define dictionaries
    switches_shtech_disabled = []
    errors = {}

    # download show tech
    for each_switch in switches:
        # Define eapi Connection
        node = eapi_connection(each_switch)

        print "###############################################################"
        print "Working on the switch " + each_switch

        # Verify sh tech scheduler is enabled
        shtech_enabled = check_shtech_scheduler(node)

        # If enabled, download the show tech files
        if shtech_enabled == "Yes":
            print """ show tech scheduler is enabled for """ + each_switch
            print " Downloading the latest show tech from " + each_switch
            download_shtech_file(node, each_switch.strip())

        elif shtech_enabled == "No":
            print """ show tech scheduler is disabled for """ + each_switch
            switches_shtech_disabled.append(each_switch.strip())

        else:
            print "eAPI connectivity error"
            errors[each_switch] = shtech_enabled

    if bool(switches_shtech_disabled):
        print "show tech is not enabled on all these switches"
        print switches_shtech_disabled
        authorize = raw_input("""Do you authorize to run show tech-support
                    on these switches? (Yes/No): """)
        if authorize in ["y", "Y", "Yes", "YES"]:
            run_show_tech_download(switches_shtech_disabled)
        else:
            print "Skipping show techs on these switches"
            print switches_shtech_disabled

    if bool(errors):
        print "eAPI connectivity issues"
        print errors

    print "Task Completed"


if __name__ == "__main__":
    main()
