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
    return os.path.join(
        os.environ.get( "_MEIPASS2", os.path.abspath(".")),
        relative_path
    )

# =================================================================
# SQLITE RELEATED FUNCTIONS
# =================================================================


# =================================================================
# SSH RELEATED FUNCTIONS
# =================================================================
class Ssh:
    """works with ssh connection to pfSense"""

    def __init__(self, verbose, address, port, user):
        self.verbose = verbose
        self.address = address
        self.port = port
        self.user = user
        self.shell = 0
        self.client = 0

    def ssh_open(self):
        """ open ssh conncetion to pfSense router"""
        self.client = SSHClient()
        self.client.load_system_host_keys()
        if self.verbose:
            print("About to Connect")
        self.client.connect(
            self.address,
            port=self.port,
            username=self.user,
        )

    def get_ssh_shell(self):
        """ get ssh shell for current session"""
        self.shell = self.client.invoke_shell()
        if self.verbose:
            print("Connected")

    def ssh_up(self):
        """setup connection"""
        self.ssh_open()
        self.get_ssh_shell()

    def ssh_down(self):
        """tear down connection"""
        self.client.close()
        if self.verbose:
            print("Disconnected")

    def wait_menu_prompt(self):
        """wait for menu prompt"""
        output = ''
        result = ''
        while "Enter an option:" not in result:
            result = self.shell.recv(65100).decode('ascii')
            output += result
            if self.verbose:
                print(result)
        return output

    def wait_command_prompt(self):
        """wait for prompt and return output"""
        output = ''
        result = ''
        while "pfSense.nrb.com" not in result:
            result = self.shell.recv(65100).decode('ascii')
            output += result
            if self.verbose:
                print(result)
        return output

    def send_command(self, command):
        """send command to remote server"""
        self.shell.send(command + "\n")


# =================================================================
# BREAD AND BUTTER STUFF
# =================================================================
def get_machines(verbose):
    """collect list of mac/ip"""
    pfsense = Ssh(
        verbose,
        os.environ.get('SSH_ADDRESS', '127.0.0.1'),
        os.environ.get('SSH_PORT', 22),
        os.environ.get('SSH_USER', 'root'),
    )

    pfsense.ssh_up()
    _ = pfsense.wait_menu_prompt()
    pfsense.send_command("8")
    _ = pfsense.wait_command_prompt()
    pfsense.send_command("arp -a ; exit")
    output = pfsense.wait_menu_prompt()
    pfsense.ssh_down()

    # process addresses
    lines = output.split("\r")
    ip_macs = [x[1:] for x in lines if "?" in x]
    machines = []
    for ip_mac in ip_macs:
        if len(ip_mac.split("(")):
            ip_address = ip_mac.split("(")[1].split(")")[0]
            mac_address = ip_mac.split("(")[1].split("at ")[1].split(" ")[0]
            machines.append((mac_address, ip_address))
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
