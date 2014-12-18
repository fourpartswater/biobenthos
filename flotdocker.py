"""
special tricks for opening flotilla with docker in OS X - hacked for linux

for linux, this needs to use sudo - or user added to docker group
"""

import time
import subprocess
import os
import sys
import signal
import argparse
import json

DEFAULT_FLOTILLA_VERSION = "latest"
DEFAULT_FLOTILLA_NOTEBOOK_DIR = "~/flotilla_notebooks"
DEFAULT_FLOTILLA_PROJECTS_DIR = "~/flotilla_projects"
DEFAULT_MEMORY_REQUIREMENT = 3500


class CommandLine(object):

    def __init__(self, opts=None):
        self.parser = parser = argparse.ArgumentParser(
            description='Start flotilla with docker.')

        parser.add_argument('--branch', required=False,
                            type=str, action='store',
                            default=DEFAULT_FLOTILLA_VERSION,
                            help="branch of flotilla to "
                                 "use from dockerhub, default:{}".format(DEFAULT_FLOTILLA_VERSION))

        parser.add_argument('--notebook_dir', required=False,
                            type=str, action='store',
                            default=DEFAULT_FLOTILLA_NOTEBOOK_DIR,
                            help="local directory to place/read notebooks:{}".format(DEFAULT_FLOTILLA_NOTEBOOK_DIR))

        parser.add_argument('--flotilla_packages', required=False,
                            type=str, action='store',
                            default=DEFAULT_FLOTILLA_PROJECTS_DIR,
                            help="local directory to place/read "
                            "flotilla packages:{}".format(DEFAULT_FLOTILLA_PROJECTS_DIR))

        parser.add_argument('--memory_request', required=False,
                            type=int, action='store',
                            default=DEFAULT_MEMORY_REQUIREMENT,
                            help="memory request for docker VM:{}".format(DEFAULT_MEMORY_REQUIREMENT))

        if opts is None:
            self.args = vars(self.parser.parse_args())
        else:
            self.args = vars(self.parser.parse_args(opts))

    def do_usage_and_die(self, str):
        '''
        If a critical error is encountered, where it is suspected that the
        program is not being called with consistent parameters or data, this
        method will write out an error string (str), then terminate execution
        of the program.
        '''
        import sys

        print >> sys.stderr, str
        self.parser.print_usage()
        return 2


# Class: Usage
class Usage(Exception):
    '''
    Used to signal a Usage error, evoking a usage statement and eventual
    exit when raised
    '''

    def __init__(self, msg):
        self.msg = msg


class FlotillaRunner(object):
    """Start docker flotilla, open the browser"""
    def __init__(self, flotilla_version=DEFAULT_FLOTILLA_VERSION,
                 notebook_dir=DEFAULT_FLOTILLA_NOTEBOOK_DIR,
                 flotilla_packages_dir=DEFAULT_FLOTILLA_PROJECTS_DIR,
                 memory_request=DEFAULT_MEMORY_REQUIREMENT):
        notebook_dir =os.path.abspath(os.path.expanduser(notebook_dir))
        flotilla_packages_dir = os.path.abspath(os.path.expanduser(flotilla_packages_dir))
        self.flotilla_version = flotilla_version
        self.flotilla_process = None
        self.flotilla_packages_dir = flotilla_packages_dir
        self.notebook_dir = notebook_dir
        self.memory_request = memory_request

        subprocess.call("docker pull mlovci/flotilla:%s" % flotilla_version, shell=True)

    def __enter__(self):
        docker_runner = "docker run -m \"{3}m\" -v {0}:/root/flotilla_projects " \
                               "-v {1}:/root/ipython " \
                               "-d -P -p 8888 " \
                               "mlovci/flotilla:{2}".format(self.flotilla_packages_dir,
                                                            self.notebook_dir,
                                                            self.flotilla_version,
                                                            self.memory_request)
        sys.stderr.write("running: {}\n".format(docker_runner))
        self.flotilla_process = subprocess.Popen(docker_runner,
                                                 shell=True, stdout=subprocess.PIPE)
        self.flotilla_container = self.flotilla_process.stdout.readlines()[0].strip()
        docker_port = subprocess.Popen("docker port {}".format(self.flotilla_container),
                                       shell=True,
                                       stdout=subprocess.PIPE)
        self.flotilla_port = docker_port.stdout.readlines()[0].split(":")[-1].strip()
        flotilla_url = 'http://{}:{}'.format(os.environ['DOCKER_IP'],  self.flotilla_port)
        sys.stderr.write("flotilla is running at: {}\n".format(flotilla_url))
        subprocess.call('open {}'.format(flotilla_url), shell=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        p = subprocess.Popen("docker stop {0} && docker rm {0}".format(self.flotilla_container), shell=True)
        try:
            sys.stderr.write("Shutting down notebook. Be slightly patient.")
            p.wait()
        except KeyboardInterrupt:
                signal.signal(signal.SIGTERM, waiter)


def main(flotilla_branch, flotilla_notebooks, flotilla_projects, memory_request):
    with FlotillaRunner(flotilla_branch, flotilla_notebooks, flotilla_projects, memory_request) as fr:
        print "Use Ctrl-C once, and only once, to exit"
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                exit(0)


if __name__ == '__main__':
    try:
        cl = CommandLine()
        main(cl.args['branch'], cl.args['notebook_dir'],
             cl.args['flotilla_packages'], cl.args['memory_request'])

    except Usage, err:
        cl.do_usage_and_die()
