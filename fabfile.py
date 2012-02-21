"""
Fabfile for boostrapping and deploying a
Django/Nginx/Apache/Postgres/Postfix stack
on Ubuntu 10.4 LTS.
"""

from __future__ import with_statement
from functools import partial
import os, os.path, time
import functools

from fabric.api import *
from fabric.contrib.files import append, exists, comment, contains
from fabric.contrib.files import upload_template as orig_upload_template

# Stuff you're likely to change
PROJECT_NAME = 'project'
DOMAIN = 'project.com'
GIT_CLONE_PATH = 'reverie/%s.git' % PROJECT_NAME
PRODUCTION_USERNAME = 'root'
PRODUCTION_HOST = DOMAIN # Change this to an IP if your DNS isn't resolving yet
ADMIN_EMAIL = 'andrewbadr+django_fabfile@gmail.com'

# Probably don't change:
DJANGO_PORT = 81
BRANCH = 'master'
SERVER_GROUP = 'app'
ROLES = ['nginx', 'django', 'database', 'smtp']
PROJECT_DIR = '/project/%s' % PROJECT_NAME # Not templatized in config files
VIRTUALENV = '/envs/%s' % PROJECT_NAME # Not templatized in config files
DB_PASS = 'foo' # Should not contain quotes; coupled w/settings.py # IGNORED, postgres is now configured to trust local connections
GIT_CLONE_USERNAME = 'git'
GIT_CLONE_HOST = 'github.com'
GIT_CLONE_PSEUDOHOST = PROJECT_NAME # Used to specify site-specific behavior for SSH if multiple projects are hosted on e.g. github.com
PG_VERSION = (8, 4)
PYTHON_VERSION = (2,6)

#
# Fabric Hacks
#

# Fabric excludes `run` and `sudo` from being tasks, for no apparent reason
# This works around that:
run = functools.partial(run)
sudo = functools.partial(sudo)

def upload_template(src, dest, *args, **kwargs):
    """
    Wrapper around Fabric's upload_template that sets +r.

    upload_template does not preserve file permissions, http://code.fabfile.org/issues/show/117
    """
    orig_upload_template(src, dest, *args, **kwargs)
    sudo('chmod +r %s' % dest)

def boxed_task(name):
    """
    So you can use e.g. Pip.install_requirements as a task.
   
    E.g.: 'boxed_task:Pip.install_requirements'
    """
    # TODO: switch to fabric namespaces
    box, task = name.split('.', 1)
    box = globals()[box]
    task = getattr(box, task)
    task()


#
# Helpers
#

def home_dir(*args):
    # For some reason ~/.ssh/... stopped working as `put` arg, need to expand ~
    if env.user == 'root':
        return os.path.join("/root", *args)
    return os.path.join("/home/%s" % env.user, *args)

#
# Stage management
#

def stage_dev():
    env.user = os.getenv('USER')
    env.stage = {
        'hostname': 'dev.' + DOMAIN
    }
    env.hosts = [env.stage['hostname']]

def stage_staging():
    env.user = PRODUCTION_USERNAME
    env.stage = {
        'hostname': 'staging.' + DOMAIN
    }
    env.hosts = [env.stage['hostname']]

def stage_production():
    env.user = PRODUCTION_USERNAME
    env.stage = {
        'hostname': 'www.' + DOMAIN
    }
    env.hosts = [PRODUCTION_HOST]

#
# Tasks
#

class Apt(object):
    @staticmethod
    def install(*pkgs):
        sudo('apt-get install -y %s' % ' '.join(pkgs))

    @staticmethod
    def upgrade():
        sudo('apt-get update -y')
        sudo('apt-get upgrade -y')

class Pip(object):
    @staticmethod
    def install_virtualenv():
        sudo('pip install virtualenv')

    @staticmethod
    def install(*pkgs):
        pip =  os.path.join(VIRTUALENV, 'bin', 'pip')
        for pkg in pkgs:
            run('%s install -U %s' % (pip, pkg))

    @staticmethod
    def install_requirements():
        REMOTE_FILENAME = './tmp_requirements.txt'
        pip =  os.path.join(VIRTUALENV, 'bin', 'pip')
        put('./server/requirements.txt', REMOTE_FILENAME)
        run('%s install -r %s' % (pip, REMOTE_FILENAME))
        run('rm %s' % REMOTE_FILENAME)

def set_up_permissions(dirname):
    sudo('chown -R %s:%s %s' % (env.user, SERVER_GROUP, dirname))
    sudo('chmod -R g+w %s' % dirname)

def adduser(username):
    # Idempotent (non-failing) version of adduser
    base_cmd = 'useradd --user-group %s' % username
    sudo(base_cmd + ' || [[ $? == 9 ]]') # 9 is failure code for already exists
    # alt: getent passwd username || useradd, also thanks to \amethyst

def bootstrap_everything():
    print "bootstrap everything"
    install_common()
    install_nginx()
    install_database()
    install_django()
    install_smtp()
    configure_nginx()
    configure_django()
    configure_database()
    configure_smtp()
    restart_database() # Must be done before deploy so that syncdb works
    simple_deploy()
    restart_database()
    restart_django() # Must be done before nginx so that port 80 is free
    restart_nginx()
    restart_smtp()

def bootstrap_database():
    install_common()
    install_database()
    configure_database()
    restart_database()

def bootstrap_nginx():
    install_common()
    install_nginx()
    configure_nginx()
    deploy()
    restart_nginx()

def bootstrap_django():
    install_common()
    install_django()
    configure_django()
    deploy()
    restart_django()

def bootstrap_smtp():
    install_common()
    install_smtp()

def install_common():
    print "install common"
    # If you get prompted to configure grub, make a preseed file
    # and use it next time.
    #put('./server/grub_preseed.cfg', 'grub_preseed.cfg')
    #sudo('debconf-set-selections grub_preseed.cfg')
    Apt.upgrade()
    sudo('echo LANG=\\"en_US.UTF-8\\" > /etc/default/locale')
    locale_env = [
        'LANGUAGE="en_US.utf8"',
        'LANG="en_US.utf8"'
    ]
    append('/etc/environment', locale_env, use_sudo=True)
    Apt.install('python-setuptools', 'python-pycurl', 'vim', 'screen', 'language-pack-en', 'git-core',
            'subversion', 'cron', 'curl', 'man', 'build-essential', 'python-dev', 'libpq-dev',
            'python-psycopg2', 'libcurl4-gnutls-dev', 'debconf-utils', 'ntp', 'ack-grep',
            'memcached', 'python-memcache', # TODO: use a different memcached client
            )
    sudo('easy_install -U setuptools')
    sudo('easy_install pip')
    adduser(SERVER_GROUP)
    for dirname in ['releases', 'packages', 'bin', 'log']:
        sudo('mkdir -p %s' % os.path.join(PROJECT_DIR, dirname))
    set_up_permissions('/project')
    log_dir = os.path.join(PROJECT_DIR, 'log')
    sudo('chmod g+s %s' % log_dir)
    install_keys()

def _key_destination(public=True):
    key_name = PROJECT_NAME + '_rsa' + ('.pub' if public else '')
    path = '.ssh/' + key_name
    return home_dir(path)

def install_keys():
    run('mkdir -p ~/.ssh')
    # Failing here? You need to generate a keypair and put it in the 'server' directory.
    # The point is to use this as a GitHub (or other) 'deploy key'. Delete this stuff
    # if you don't want that.
    put('./server/id_rsa', _key_destination(public=False))
    put('./server/id_rsa.pub', _key_destination())
    run('chmod 600 %s' % _key_destination(public=False))

    # So we can git clone from git@github.com w/o manual confirmation:
    put('./server/known_hosts', home_dir('.ssh/known_hosts'))

    # Add SSH configuration...
    config_file = home_dir('.ssh/config')
    lines =  [
        'Host ' + GIT_CLONE_PSEUDOHOST,
        '   HostName ' + GIT_CLONE_HOST,
        '   IdentityFile ' + _key_destination(public=False)
    ]
    # Fabric's `append` does not run if the line is already in there.
    # Multiple projects will have the same HostName line.
    # We can't make the lines unique with a comment because ssh chokes; wants comments on their own line.
    # Therefore, just append for now until something needs to change. (SSH uses first match.)
    for l in lines:
        assert "'" not in l
        run("echo '%s' >> %s" % (l, config_file))
        run("echo '%s' >> %s" % ('', config_file))

def install_nginx():
    Apt.install('nginx')
    assert exists('/etc/nginx/sites-enabled') # Right package install format?
    if exists('/etc/nginx/sites-enabled/default'):
        sudo('rm /etc/nginx/sites-enabled/default')

#def install_processor():
#    """
#    Stuff to compile javascript
#    """
#    put('./server/processor/compiler.jar', os.path.join(PROJECT_DIR, 'bin', 'compiler.jar'))
#    put('./server/processor/processor', os.path.join(PROJECT_DIR, 'bin', 'processor'))

def install_django():
    Pip.install_virtualenv()
    if not exists(VIRTUALENV): # TODO: better test than `exists`?
        sudo('mkdir -p %s' % VIRTUALENV)
        sudo('virtualenv %s' % VIRTUALENV)
    set_up_permissions(VIRTUALENV)
    Pip.install_requirements()
    Apt.install('apache2', 'postgresql-client', 'libapache2-mod-wsgi')
    if exists('/etc/apache2/sites-enabled/000-default'):
        sudo('rm /etc/apache2/sites-enabled/000-default')
    sudo('usermod -G %s -a www-data' % SERVER_GROUP)

def install_smtp():
    # this next line is really configuration, but it has to happen before installing
    # the package or else it will prompt for configuration
    put('./server/postfix_preseed.cfg', 'postfix_preseed.cfg')
    sudo('debconf-set-selections postfix_preseed.cfg')
    Apt.install('postfix')
    run('rm postfix_preseed.cfg')

def install_database():
    # This uses whatever the default encoding and locale get set to on your system.
    # For me, this started being UTF-8 and and en_US.UTF8 by default, which is what 
    # I want. If you want something different, you might need to drop and recreate
    # your cluster.
    Apt.install('postgresql')
    restart_database()

def configure_nginx():
    put('./server/nginx/nginx.conf', '/etc/nginx/nginx.conf', use_sudo=True)
    upload_template( './server/nginx/site', '/etc/nginx/sites-available/%s' % PROJECT_NAME, 
            use_sudo=True, use_jinja=True, context={
        'hostname': env.stage['hostname'],
        'django_host': '127.0.0.1', # Change this on switch to a multi-server setup
        'DJANGO_PORT': DJANGO_PORT,
        'DOMAIN': DOMAIN,
        'PROJECT_NAME': PROJECT_NAME
    })
    if not exists('/etc/nginx/sites-enabled/%s' % PROJECT_NAME):
        sudo('ln -s /etc/nginx/sites-available/%s /etc/nginx/sites-enabled/%s' % (PROJECT_NAME, PROJECT_NAME))

def configure_django():
    upload_template('./server/django/wsgi.py', os.path.join(PROJECT_DIR, 'wsgi.py'), use_jinja=True, context={
        'PROJECT_NAME': PROJECT_NAME,
        'PYTHON_VERSION_STR': "%d.%d" % PYTHON_VERSION,
    })
    upload_template('./server/django/vhost', '/etc/apache2/sites-available/%s' % PROJECT_NAME, use_sudo=True, use_jinja=True, context={
        'DJANGO_PORT': DJANGO_PORT,
        'PROJECT_NAME': PROJECT_NAME,
        'DOMAIN': DOMAIN, # Should we use env.stage['hostname']?
        'ADMIN_EMAIL': ADMIN_EMAIL

    })
    upload_template('./server/django/ports.conf', '/etc/apache2/ports.conf', use_sudo=True, use_jinja=True, context={
        'DJANGO_PORT': DJANGO_PORT,
    })
    upload_template('./server/django/stagesettings.py', os.path.join(PROJECT_DIR, 'stagesettings.py'), use_sudo=True, 
        use_jinja=True, context={
        'database_host': '127.0.0.1', # Change this on swtich to a multi-server setup
    })
    if not exists('/etc/apache2/sites-enabled/%s' % PROJECT_NAME):
        sudo('ln -s /etc/apache2/sites-available/%s /etc/apache2/sites-enabled/%s' % (PROJECT_NAME, PROJECT_NAME))

def configure_smtp():
    main_cf = '/etc/postfix/main.cf'
    comment(main_cf, "^inet_interfaces = all$", use_sudo=True)
    append(main_cf, "inet_interfaces = loopback-only", use_sudo=True)

def run_with_safe_error(cmd, safe_error, use_sudo=False, user=None):
    # Todo: use _run_command in 1.0
    if user:
        assert use_sudo
    if use_sudo:
        runner = partial(sudo, user=user)
    else:
        runner = run
    with settings(warn_only=True):
        result = runner(cmd)
    if not result.failed:
        return result
    if result == safe_error: # Will probably end up using 'in' instead of '==', but wait and see
        return result
    # FAIL: this can't work right now b/c we don't have access to stderr. Wait for Fabric 1.0
    return result # Remove this.
    abort("Command had unexpected error:\n" + 
            "  Command: %s\n" % cmd + 
            "  Expected error: %s\n" % safe_error + 
            "  Actual error: %s" % result
            )

def configure_database():
    config_dir = '/etc/postgresql/%d.%d/main' % PG_VERSION
    sudo('mkdir -p %s' % config_dir)
    for filename in ['environment', 'pg_ctl.conf', 'pg_hba.conf', 'pg_ident.conf', 'postgresql.conf', 'start.conf']:
        local_file = os.path.join('./server/database', filename)
        remote_file = os.path.join(config_dir, filename)
        upload_template( local_file, remote_file, use_sudo=True, use_jinja=True, context={
            'PROJECT_NAME': PROJECT_NAME,
            'PG_VERSION_STRING': "%d.%d" % PG_VERSION,
        })
        sudo('chown %s:%s %s' % ('postgres', 'postgres', remote_file))
    run_with_safe_error("createdb %s" % PROJECT_NAME, 'some dumb error', use_sudo=True, user='postgres')
    run_with_safe_error("""psql -c "create user %s with createdb encrypted password '%s'" """ % (PROJECT_NAME, DB_PASS), "some dumb error", use_sudo=True, user='postgres')
    sudo("""psql -c "grant all privileges on database %s to %s" """ % (PROJECT_NAME, PROJECT_NAME), user='postgres')

def make_symlink_atomically(new_target, symlink_location, sudo=False):
    # From http://blog.moertel.com/articles/2005/08/22/how-to-change-symlinks-atomically
    runner = sudo if sudo else run
    params = {
            'new_target': new_target,
            'symlink_location': symlink_location,
            'tempname': 'current_tmp',
            }
    cmd = "ln -s %(new_target)s %(tempname)s && mv -Tf %(tempname)s %(symlink_location)s" % params
    runner(cmd)

class Deploy(object):

    run_time = time.time()

    @staticmethod
    def get_current_commit():
        return local('git rev-parse --verify %s' % BRANCH, capture=True).strip()

    @staticmethod
    def get_time_str():
        return time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(Deploy.run_time))

    @staticmethod
    def get_release_name():
        return Deploy.get_time_str() + '_' + Deploy.get_current_commit()

    @staticmethod
    def switch_symlink(name):
        assert name
        new_target = os.path.join(PROJECT_DIR, 'releases', name)
        symlink_location = os.path.join(PROJECT_DIR, 'current')
        make_symlink_atomically(new_target, symlink_location)

    @staticmethod
    def get_release_dir(name):
        assert name
        return os.path.join(PROJECT_DIR, 'releases', name)

    @staticmethod
    def get_git_repo():
        return GIT_CLONE_USERNAME + '@' + GIT_CLONE_PSEUDOHOST + ':' + GIT_CLONE_PATH
 
    @staticmethod
    def upload_new_release():
        name = Deploy.get_release_name()
        release_dir = Deploy.get_release_dir(name)
        if exists(release_dir):
            assert release_dir.startswith(os.path.join(PROJECT_DIR, 'releases'))
            run('rm -rf %s' % release_dir)
        run('git clone %s %s' % (Deploy.get_git_repo(), release_dir))
        set_up_permissions(release_dir)
        current_commit = Deploy.get_current_commit()
        with cd(release_dir):
            run('git reset --hard %s' % current_commit)
        return name

    @staticmethod
    def prep_release(name):
        """Prepares all the files in the release dir."""
        assert name
        release_dir = Deploy.get_release_dir(name)
        django_dir = os.path.join(release_dir, PROJECT_NAME)
        # If you run a preprocessor, like JS/CSS compilation, do that here, e.g. :
        #run(os.path.join(PROJECT_DIR, 'bin', 'processor') + ' ' + release_dir)
        print 'Setting up Django settings symlinks'
        with cd(django_dir):
            run('ln -nfs %s .' % os.path.join(PROJECT_DIR, 'stagesettings.py'))
            run('ln -nfs %s .' % os.path.join(PROJECT_DIR, 'localsettings.py'))

        print 'Doing Django database updates'
        with cd(django_dir):
            with_ve =  'source ' + os.path.join(VIRTUALENV, 'bin', 'activate') + ' && '
            run(with_ve + 'python manage.py syncdb --noinput')
            run(with_ve + 'python manage.py migrate --noinput')
            run(with_ve + 'python manage.py loaddata initial_data')
            run(with_ve + 'python manage.py collectstatic --noinput')
            

        print 'Installing crontab'
        crontab_path = os.path.join(release_dir, 'server/crontab')
        # need to use the stdin formulation. For some reason the path in the normal form
        # gets truncated.
        run('crontab - < %s' % crontab_path)

    @staticmethod
    def cleanup_release(name):
        pkg_filename = "%s.tar.gz" % name
        if os.path.exists(pkg_filename):
            local('rm %s' % pkg_filename)


def list_releases():
    with cd(os.path.join(PROJECT_DIR, 'releases')):
        run('''ls -ltc | grep -v total | awk '{print $6 " " $7 " " $8}' | head -n 10''')
        #run('ls -l %s | cut -d " " -f "10"' % os.path.join(PROJECT_DIR, CURRENT_RELEASE_DIR))

# Two-step Deploy; use this for HA multi-server setup:
# 1. deploy_prep_new_release
# 2. deploy_activate_release:<release_name>

def deploy_prep_new_release():
    local('git push')
    release_name = Deploy.upload_new_release()
    Deploy.prep_release(release_name)
    print '*'*20
    print "Prepped new release", release_name
    print 'You probably want to deploy_activate_release:%s' % release_name
    print '*'*20

def deploy_activate_release(release_name):
    assert release_name
    Deploy.switch_symlink(release_name)
    restart_after_deploy()
    Deploy.cleanup_release(release_name)

# One-step Deploy; use this for one-server setup or if lazy
# 1. simple_deploy

def deploy():
    release_name = Deploy.upload_new_release()
    Deploy.prep_release(release_name)
    Deploy.switch_symlink(release_name)
    Deploy.cleanup_release(release_name)

def restart_after_deploy():
    restart_django()

def simple_deploy():
    local('git push')
    deploy()
    restart_after_deploy()

# 
# Service control
# 

def reload_nginx():
    sudo('initctl reload nginx')

def reload_django():
    sudo('apache2ctl graceful')

def reload_database():
    if PG_VERSION < (9, 0):
        sudo('/etc/init.d/postgresql-8.4 reload')
    else:
        sudo('/etc/init.d/postgresql reload')

def restart_nginx():
    sudo('/etc/init.d/nginx restart')

def restart_django():
    sudo('apache2ctl graceful || apache2ctl start')

def restart_database():
    if PG_VERSION < (9, 0):
        sudo('/etc/init.d/postgresql-8.4 restart || /etc/init.d/postgresql-8.4 start')
    else:
        sudo('/etc/init.d/postgresql restart || /etc/init.d/postgresql start')

def restart_smtp():
    sudo('/etc/init.d/postfix restart')
