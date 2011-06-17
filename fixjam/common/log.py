import os, logging, logging.handlers, time

from django.conf import settings

def _mkdir(newdir):
    # Copied from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/82465
    # os.makedirs ? -SL
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            _mkdir(head)
        if tail:
            os.mkdir(newdir)

_mkdir(settings.LOG_DIRECTORY)

# Give every user a different log file so the shell doesn't step on 
# the webserver's toes. (No global way to make newly created log
# files have g+w.)
filename = settings.LOG_DIRECTORY + '/django_%s.log' % os.getuid()

def convert_log_args(f):
    """Makes logger functions act right."""
    from functools import wraps
    @wraps(f)
    def new_f(*args):
        return f(', '.join(unicode(a) for a in args))
    return new_f

logger = logging.getLogger('default')
handler = logging.handlers.RotatingFileHandler(filename, maxBytes=10*1024*1024, backupCount=10)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.setLevel(1) # 0 seems to skip DEBUG messages, contrary to the docs

debug =     convert_log_args(logger.debug)
info =      convert_log_args(logger.info)
warning =   convert_log_args(logger.warning)
error =     convert_log_args(logger.error)
critical =  convert_log_args(logger.critical)
exception = convert_log_args(logger.exception)

