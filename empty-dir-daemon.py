#!/usr/bin/python
import sys
import os
import logging
import time
import re
import traceback
import signal
from ConfigParser import SafeConfigParser

import daemon  # https://pypi.python.org/pypi/python-daemon
from lockfile import LinkFileLock  # use this instead of python-daemon's lock

DAEMON_NAME = os.path.splitext(os.path.basename(sys.argv[0]))[0]
CONF_FILE = '%s.ini' % DAEMON_NAME
APP_LOG_DIR = "/var/log/%s" % DAEMON_NAME
APP_PIDF_DIR = "/var/run"

if not os.path.exists(APP_LOG_DIR):
    cwdir = os.getcwd()
    APP_LOG_DIR = cwdir
    APP_PIDF_DIR = cwdir

def write_pid_to_pidfile(pidfile_path):
    """ Write the PID in the named PID file. """
    open_flags = (os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    open_mode = (
        ((os.R_OK | os.W_OK) << 6) |
        ((os.R_OK) << 3) |
        ((os.R_OK)))
    pidfile_fd = os.open(pidfile_path, open_flags, open_mode)
    pidfile = os.fdopen(pidfile_fd, 'w')
    pid = os.getpid()
    pidfile.write("%d\n" % pid)
    pidfile.close()
    return pid

def remove_pidfile(pidfile_path):
    """ Remove the named PID file if it exists. Ignore not existing """
    try:
        os.remove(pidfile_path)
    except OSError, exc:
        if exc.errno == errno.ENOENT:
            pass
        else:
            raise

class App(object):
    def __init__(self, dir_name, logger, to_ignore=None, action=None):
        self.dir_name = dir_name
        self.logger = logger
        self.to_ignore = to_ignore
        self.action = action
        self.exit_now = False
        self.err = False
        self.terminated = False

    def do_main(self):
        # We do not check the contents of the subdirs, that is why we do not
        # continue the for loop with the next paths
        for paths, dirs, files in os.walk(self.dir_name):
            self.logger.debug("paths: %s" % paths)
            self.logger.debug("Found dirs: %s" % dirs)
            self.logger.debug("Found files: %s" % files)
            for i in dirs[:]:
                if self.to_ignore and re.match(self.to_ignore, i):
                    self.logger.debug("Ignored %s" % i)
                    dirs.remove(i)
            for i in files[:]:
                if self.to_ignore and re.match(self.to_ignore, i):
                    self.logger.debug("Ignored %s" % i)
                    files.remove(i)
            if not dirs and not files:
                self.exit_now = True
            # stop processing
            break

    def run(self, pid):
        self.logger.info("Running with pid: %s" % pid)
        while True:
            try:
                self.do_main()
            except:
                self.logger.error("Error in do_main: " % traceback.format_exc())
                self.err = True
                return self.err
            if self.exit_now:
                return self.err
            time.sleep(20)

    def do_action(self):
        ret = None
        self.logger.info("Execute action: %s" % self.action)
        try:
            ret = os.system(action)
        except Exception, e:
            self.logger.error("Action could not execute: %s" % e)
        if ret != 0:
            self.logger.error("Action failed")
        return ret


if __name__ == "__main__":
    pidfilename = os.path.join(APP_PIDF_DIR, "%s.pid" % DAEMON_NAME)
    pidfile = LinkFileLock(pidfilename)
    if pidfile.is_locked():
        print "Error: %s is already running / remove the PID file and lock" % DAEMON_NAME
        sys.exit(1)

    logger = logging.getLogger("%s-log" % DAEMON_NAME)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(os.path.join(APP_LOG_DIR, "%s.log" % DAEMON_NAME))
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    parser = SafeConfigParser()
    try:
        parser.read(CONF_FILE)
        dir_name = parser.get('main', 'dir_name')
        to_ignore = parser.get('main', 'to_ignore')
        action = parser.get('main', 'action')
    except Exception, e:
        print "%s\nERROR: There is something wrong with %s" % (e, CONF_FILE)
        sys.exit(1)

    app = App(dir_name, logger, to_ignore, action)

    def terminate(signum=None, frame=None):
        app.terminated = True
        # Cleanup the pid file if it was still locked
        if pidfile.is_locked():
            remove_pidfile(pidfilename)
            pidfile.release()
        # Check the exit status
        if app.err is not None:
            if not app.err and app.exit_now:
                logger.info("%s is now empty!" % dir_name)
                rc = app.do_action()
            logger.info("Exit with %s" % ('success' if not rc else 'error'))
            sys.exit(rc)
        elif signum:
            logger.info("Killed by signal %d" % signum)
            sys.exit(signum)
        else:
            logger.info("Exit with unknown status")
            sys.exit(-1)

    try:
        pidfile.acquire()
        # files_preserve ensures that the logger file handle 
        # does not get closed during daemonization
        ctx = daemon.DaemonContext(files_preserve=[handler.stream],
                                   detach_process=True,
                                   signal_map = {signal.SIGTERM: terminate,
                                                 signal.SIGHUP: terminate})
        with ctx:
            # We have to get the pid after we've entered the context to get
            # the pid of the detached process
            pid = write_pid_to_pidfile(pidfilename)
            app.run(pid)
        remove_pidfile(pidfilename)
        pidfile.release()
    except:
        if not app.terminated:
            logger.error(traceback.format_exc())

    if not app.terminated:
        terminate()

    """
    Be careful of one other thing: DaemonContext changes the working dir of your 
    program to /, making the WorkingDirectory of your service file useless. 
    If you want DaemonContext to chdir into another directory, 
    use DaemonContext(pidfile=pidfile, working_directory="/path/to/dir").
    """
