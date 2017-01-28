import subprocess
import os

from charmhelpers.core import hookenv
from charmhelpers.core.hookenv import (
    status_set,
    log,
    config,
    charm_dir
)
from charmhelpers.fetch.archiveurl import ArchiveUrlFetchHandler
from charmhelpers.fetch import apt_install
from charms.reactive import (
    when,
    when_not,
    set_state,
    remove_state,
)

config = config()
charm_path = charm_dir()


@when_not('rocketchat.installed', 'rocketchat.deps_installed')
def install_deps():
    # Pull dependencies
    status_set('maintenance', 'fetching rocket.chat packages')
    log('fetching rocket.chat packages', level='info')
    apt_install(['graphicsmagick',
                 'curl',
                 'npm',
                 'build-essential'])
    subprocess.run(['sudo', 'npm', 'install', '-g', 'n'])
    subprocess.run(['sudo', 'n', '4.5'])

    # Pull latest version of Rocket.Chat
    handler = ArchiveUrlFetchHandler()
    status_set('maintenance', 'fetching rocket.chat')
    log('fetching rocket.chat', level='info')
    handler.install('https://rocket.chat/releases/latest/download',
                    dest=charm_path)

    # Unpack Rocket.Chat to destination folder
    subprocess.run(['mv', charm_path + '/bundle/',
                    charm_path + '/Rocket.Chat'])
    os.chdir(charm_path + '/Rocket.Chat/programs/server')
    subprocess.run(['sudo', 'npm', 'install'])
    # Ensure .bashrc exists
    subprocess.run('touch ~/.bashrc', shell=True)
    status_set('maintenance', 'packages installed')
    set_state('rocketchat.deps_installed')


@when('rocketchat.deps_installed', 'database.connected')
@when_not('rocketchat.launched')
def launch_rocketchat(database):
    # Set Environmental Variables
    set_env_vars(database)
    # Run Rocket.Chat
    subprocess.run('sudo node ' + charm_path + '/Rocket.Chat/main.js',
                   shell=True)
    log('Launched Rocket.Chat @ {}'.format(config['host_url']), level='info')
    set_state('rocketchat.launched')


@when('rocketchat.launched', 'database.connected')
def running(database):
    status_set('active', 'Rocket.Chat ready at {}'.format(config['host_url']))


@when('rocketchat.deps_installed', 'rocketchat.launched', 'database.removed')
def db_lost(database):
    status_set('maintenance', 'database lost')
    remove_state('rocketchat.launched')


@when('config.changed', 'rocketchat.deps_installed', 'database.connected')
def reconfigure_rc(database):
    status_set('maintenance', 'updating configuration')
    set_env_vars(database)
    remove_state('rocketchat.launched')


def set_env_vars(database):
    mongo_url = database.hostname()
    mongo_port = database.port()
    with open("~/.bashrc", "a") as outfile:
        outfile.write('export ROOT_URL={}'.format(config['host_url']))
        outfile.write('export MONGO_URL=mongodb://{}:{}/rocketchat'.format(mongo_url,
                                                                           mongo_port))
        outfile.write('export PORT={}'.format(config['port']))
