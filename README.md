# Intro #

I've used this Fabfile for several real-world Django projects. It makes it easy to bring up a production server and deploy/rollback with atomic symlink swaps. It's expecting you to lay things out in a certain way, but probably it wouldn't be too hard to modify to accommodate other layouts.

It comes bundled with a default Django project that includes a few tweaks I usually use. Feel free to delete this project and replace it with your own.

Watch it used to start and launch site in five minutes: http://www.youtube.com/watch?v=HOC0bEqn1iI (Watch in HD to read what I'm typing)

Subjective bits: http://andrewbadr.com/log/9/django-fabfile/
 
# Feature Details #

## Features ##
- Fabfile for fully automated Django project installation and deploy process on an Ubuntu 10.4 server
- Stack: nginx, Apache, Django, PostgreSQL, Postfix
- Cooperates with siblings -- run multiple of these on the same server
- All services run on a single server

## Non-features ##
- Sites running across multiple servers (e.g., a separate database server, or multiple web servers). This is available in a branch, but you might not like it.
- Compatibility with servers running setups other than this one. The Fabfile overwrites configuration files and in general might step on things.
- Accepting inbound email
- Configuration tuned for high traffic. Set your own values in the `server` directory's various config files.
- Running on servers other than Ubuntu 10.4

## Non-configurable, but modifying the source should be easy ##
- Runs your site from www.yourdomain.com
- Static files are served with URL prefix /static/
- Assumes you're using Git and hosting at GitHub

## Caveats ##
- I haven't tried running this from Windows

# Installation & Usage #
## Installation ##
### If you're starting a new Django project ###
 1. Move 'project' to your new project name. This is PROJECT_NAME for the steps below.
 2. Change the "Stuff you're likely to change" settings at the top of fabfile.py
 3. In yourproject/settings.py:
    - Change the PROJECT_NAME and DOMAIN at the top of settings.py to match fabfile.py
    - Modify the SECRET_KEY='' line to use a random key (see comment there for help)
    - Change the ADMINS setting (unless you want me getting your tracebacks)
 4. Generate a keypair using ssh-keygen and put it in the server directory.
    Upload the public key to GitHub as your project's "Deploy Key".
 5. Consider doing a `pip freeze` on your server and updating server/requirements.txt with version requirements.

### If you're converting an existing Django project ###
 1. Make things look like you did all the steps above.
 2. If you have to change the Fabfile because something isn't configurable, like the
    static url prefix, consider submitting a patch to make it a configuration setting.

### Out of band project setup ###
- GitHub project hosting
- Server provisioning
- DNS records
- SPF records (optional)
- authorized_keys on server (optional)

## Usage ##
 - To bring the server up for the first time, "fab stage_production bootstrap_everything"
 - To deploy a new version, "fab stage_production simple_deploy"

