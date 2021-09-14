#!/usr/bin/env python
""" get arp table from pfSense firewall"""

import os
import sys
import click
from dotenv import load_dotenv
from paramiko import SSHClient

# =================================================================
# UTILITY FUNCTIONS
# =================================================================
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# =================================================================
# SSH RELEATED FUNCTIONS
# =================================================================
def ssh_open(verbose):
    """ open ssh conncetion to pfSense router"""
    client = SSHClient()
    client.load_system_host_keys()
    if verbose:
        print("About to Connect")
    client.connect(
        os.getenv('SSH_ADDRESS'),
        port=os.getenv('SSH_PORT'),
        username=os.getenv('SSH_USER'),
    )
    return client

def ssh_close(client, verbose):
    """close connection"""
    client.close()
    if verbose:
        print("Disconnected")

def get_ssh_shell(client, verbose):
    """ get ssh shell for current session"""
    my_ssh_shell = client.invoke_shell()
    if verbose:
        print("Connected")
    return my_ssh_shell

def wait_menu_prompt(my_ssh_shell, verbose):
    """wait for menu prompt"""
    output = ''
    result = ''
    while "Enter an option:" not in result:
        result = my_ssh_shell.recv(65100).decode('ascii')
        output += result
        if verbose:
            print(result)
    return output

def wait_command_prompt(my_ssh_shell, verbose):
    """wait for prompt and return output"""
    output = ''
    result = ''
    while "pfSense.nrb.com" not in result:
        result = my_ssh_shell.recv(65100).decode('ascii')
        output += result
        if verbose:
            print(result)
    return output

def send_command(my_ssh_shell, command):
    """send command to remote server"""
    my_ssh_shell.send(command + "\n")

# =================================================================
# BREAD AND BUTTER STUFF
# =================================================================
def get_machines(verbose):
    """collect list of mac/ip"""
    client = ssh_open(verbose)
    my_ssh_shell = get_ssh_shell(client, verbose)
    _ = wait_menu_prompt(my_ssh_shell, verbose)
    send_command(my_ssh_shell, "8")
    _ = wait_command_prompt(my_ssh_shell, verbose)
    send_command(my_ssh_shell, "arp -a ; exit")
    output = wait_menu_prompt(my_ssh_shell, verbose)

    subset = output.split("\r")
    ip_macs = [x[1:] for x in subset if "?" in x]
    machines = []
    for ip_mac in ip_macs:
        if len(ip_mac.split("(")):
            ip_address = ip_mac.split("(")[1].split(")")[0]
            mac_address = ip_mac.split("(")[1].split("at ")[1].split(" ")[0]
            machines.append((mac_address, ip_address))
    ssh_close(client, verbose)
    return machines

@click.command()
@click.option(
    '--verbose/--no-verbose',
    '-v',
    default=False,
    help='show output',
)
def cli(verbose):
    """main command function"""

    # load environmental variables
    env_path = resource_path('.env')
    load_dotenv(dotenv_path=env_path)


    _ = get_machines(verbose)
    sys.exit(0)


if __name__ == "__main__" :
    cli() # pylint: disable=no-value-for-parameter
