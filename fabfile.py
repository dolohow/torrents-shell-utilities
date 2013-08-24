from fabric.api import *

env.password = 'rower01'
env.user = 'root'
env.hosts = ['zulu1507.server4you.net', 'ks305597.kimsufi.com', 'alster019.server4you.net', 'ks389320.kimsufi.com', 'alpha145.server4you.net', 'ks3099356.kimsufi.com', 'ks394793.kimsufi.com', 'ks3282885.kimsufi.com', '85.17.24.97']

# execute any command by fab command:'command'
@parallel
def command(c):
  run(c)

@parallel
def find(f):
  run('updatedb')
  with settings(warn_only=True):
    run('locate %s' % f)

@parallel
def upgrade():
  run('apt-get update')
  run('apt-get dist-upgrade -y --force-yes')

def install_base():
  upgrade()
  run('apt-get install htop iotop nethogs vnstat git mc proftpd smartmontools deborphan mlocate')

def install_vnc():
  run('apt-get install vnc4server lxde-core leafpad lxterminal filezilla wine firefox chromium-browser jdownloader flasplugin-nonfree xarchiver rar')

def install_quota():
  run('apt-get install quota quotatool')

def install_rtorrent():
  with cd('~/'):
    run('./autodl-setup -w --lighttpd --rtorrent --rutorrent')

def install_deluge(version):
  with cd('~/'):
    run('wget http://download.deluge-torrent.org/source/deluge-%s.tar.bz2' % version)
    run('tar xvjf deluge-%s.tar.bz2' % version)
    run('rm deluge-%s.tar.bz2' % version)
    with cd('deluge-%s' % version):
      run('python setup.py clean -a')
      run('python setup.py build')
      run('python setup.py install')
      run('python setup.py install_data')
    run('rm -r deluge-%s' % version)

def set_protection():
  run('chmod 770 /usr/bin/htop /usr/bin/top /bin/ps')
  run('chmod 711 /home /home2')

def s4u():
  run('mkdir /home2')
  run('umount /dev/sdb1')
  run('mkfs.ext4 /dev/sdb1')
  """manually add:
  noatime,usrjquota=aquota.user,grpjquota=aquota.group,jqfmt=vfsv0	0 1
  to fstab
  no workaround yet
  """
  run('mount -o remount /')
  run('mount /dev/sdb1')
  run('quotaoff -a')
  run('quotacheck -vagum')
  run('quotaon -a')

def set_panel():
  """add to crontab:
  */5 * * * *     root    /root/server-file-configuration/startrt start all > /dev/null
  */5 * * * *     root    /root/server-file-configuration/panel > /dev/null
  """
  pass