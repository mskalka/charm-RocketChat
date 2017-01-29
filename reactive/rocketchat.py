import subprocess
import os
from shutil import copyfile

from charmhelpers.core import hookenv
from charmhelpers.core.hookenv import (
    status_set,
    log,
    config,
    charm_dir
)
from charmhelpers.core.host import (
    service_start,
    service_stop
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


@when_not('rocketchat.installed', 'rocketchat.ready')
def install_deps():
    # Pull dependencies
    status_set('maintenance', 'fetching rocket.chat packages')
    log('fetching rocket.chat packages', level='info')
    apt_install(['nodejs',
                 'build-essential',
                 'npm'])
    # subprocess.run(['sudo', 'npm', 'install', '-g', 'n'])
    # subprocess.run(['sudo', 'n', '4.5'])
    # Pull latest version of Rocket.Chat
    handler = ArchiveUrlFetchHandler()
    status_set('maintenance', 'fetching rocket.chat')
    log('fetching rocket.chat', level='info')
    handler.install('https://rocket.chat/releases/latest/download',
                    dest=charm_path)

    # Unpack Rocket.Chat to destination folder
    subprocess.run(['mv', charm_path + '/bundle/', '/opt/Rocket.Chat'])
    os.chdir('/opt/Rocket.Chat/programs/server')
    subprocess.run(['sudo', 'npm', 'install'])
    copyfile(charm_path + '/files/rocketchat.service',
                          '/etc/systemd/system/rocketchat.service')
    status_set('maintenance', 'packages installed')
    set_state('rocketchat.ready')


@when('rocketchat.ready', 'rocketchat.vars_set', 'database.connected')
@when_not('rocketchat.launched')
def launch_rocketchat(database):
    status_set('active', 'Launching Rocket.Chat')
    # Launch Rocket.Chat
    hookenv.open_port('3000')
    service_start('rocketchat')
    log('Launched Rocket.Chat @ {}'.format(config['host_url']),
        level='info')
    set_state('rocketchat.launched')


@when_not('rocketchat.launched', 'rocketchat.vars_set')
@when('database.connected', 'rocketchat.ready')
def set_rocketchat_config(database):
    if database.connection_string() is not None:
        with open('/etc/rocketchat', 'w') as f:
            f.writelines(env_vars(database))
        f.close()
        set_state('rocketchat.vars_set')
    else:
        status_set('maintenance', 'Waiting for MongoDB connection')


@when('database.removed', 'rocketchat.launched')
def reset_connection(database):
    service_stop('rocketchat')
    remove_state('rocketchat.launched')
    remove_state('rocketchat.vars_set')
    status_set('blocked', 'Lost MongoDB connection')


def env_vars(database):
    connection = database.connection_string()
    log('MongoDB URL:{}'.format(connection))
    out = []
    out.append('PORT={}\n'.format(config['port']))
    out.append('ROOT_URL={}\n'.format(config['host_url']))
    out.append('MONGO_URL=mongodb://{}/rocketchat\n'.format(connection))
    # out.append('MONGO_OPLOG_URL=mongodb://{}/local?replicaSet=myset\n'.format(connection))
    return out
