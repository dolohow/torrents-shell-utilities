from fabric.api import *
# reconsider changing the execution model

env.user = 'root'
env.colorize_errors = True
[env.hosts.append(i.replace('\n', '')) for i in open('servers_list', 'r')]

def install_key():
    """copy ssh public key"""
    run('rm -rf ~/.ssh ; mkdir -p ~/.ssh')
    put('fabric/concat.pub', '~/.ssh/authorized_keys')
    put('fabric/id_rsa.pub', '~/.ssh')
    put('fabric/id_rsa', '~/.ssh')
    run('chmod 600 ~/.ssh/id_rsa')

@parallel
def search(arg):
    """search any file you want across servers"""
    run('updatedb')
    with settings(warn_only=True):
        run('locate -i %s' % arg)

@parallel
def load():
    """check the load across servers"""
    run('vnstat -d|tail -n7')

@parallel
def update_system():
    run('apt-get update -y')
    run('apt-get dist-upgrade -y --force-yes')

def update_git():
    run('git pull')
    
@parallel
def update_lighttpd():
    run('systemctl stop lighttpd')
    run('mkdir /backup;mv /usr/local/lighttpd/{lighttpd.conf,logs,rutorrent_passwd} /backup/')
    run('./autodl-setup --lighttpd')
    run('systemctl stop lighttpd')
    run('rm -r /usr/local/lighttpd/logs;mv /backup/* /usr/local/lighttpd/;rm -r /backup')
    run('pkill lighttpd')
    run('systemctl start lighttpd')

@parallel
def update_rutorrent():
    with cd('/var/rutorrent/rutorrent'):
        run('git pull')
        
@parallel
def update_rtorrent():
    run('./autodl-setup --rtorrent')
    
def install(*args):
    run('aptitude -y install %s' % ' '.join(args))

def install_base():
    # modify /etc/proftpd.conf file to jail user
    update_system()
    # two times acceptance for proftpd
    install('htop', 'iotop', 'nethogs', 'vnstat', 'git', 'mc', 'proftpd',
        'smartmontools', 'deborphan', 'mlocate', 'hdparm', 'vim', 'screen',
        'unattended-upgrades')
    #run("if [ -d ~/.ssh ] ; then rm -rf ~/.ssh/* ; else mkdir ~/.ssh ; fi")
    install_key()
    #run('chmod 600 ~/.ssh/id_rsa')
    # get rid of this yes prompt (| yes - probably a fix)
    run('yes | git clone https://dolohow@bitbucket.org/dolohow/server-file-configuration.git foo')
    run('mv foo/* foo/.git* .')
    run('rm -rf foo')
    run('dpkg-reconfigure -plow unattended-upgrades')

def install_autodl_irssi():
    # never tested if works
    install('libarchive-zip-perl', 'libnet-ssleay-perl', 'libhtml-parser-perl',
        'libxml-libxml-perl', 'libjson-perl', 'libjson-xs-perl',
        'libxml-libxslt-perl')
    with cd('/var/rutorrent/rutorrent/plugins'):
        run('svn co https://autodl-irssi.svn.sourceforge.net/svnroot/autodl-irssi/trunk/rutorrent/autodl-irssi')
        run('mv autodl-irssi/_conf.php autodl-irssi/conf.php')
        run('chown -R lighttpd:lighttpd autodl-irssi')
        run('chmod 640 autodl-irssi/conf.php')

    run('useradd --create-home irssi')
    run('su irssi')
    run('mkdir -p ~/.irssi/scripts/autorun')
    run('cd ~/.irssi/scripts')
    run('wget https://sourceforge.net/projects/autodl-irssi/files/autodl-irssi-v1.10.zip')
    run('unzip -o autodl-irssi-v*.zip')
    run('rm autodl-irssi-v*.zip')
    run('cp autodl-irssi.pl autorun/')
    run('mkdir -p ~/.autodl')
    run('touch ~/.autodl/autodl.cfg')


def install_vnc():
    update_system()
    run('wget http://installer.jdownloader.org/JD2Setup_x64.sh')
    install('openjdk-7-jre', 'tightvncserver', 'lxde-core', 'leafpad',
            'lxterminal', 'filezilla', 'iceweasel', 'chromium-browser',
            'xarchiver', 'rar', 'gpicview', 'autocutsel')

def install_rtorrent():
    # additional deps:
    # ffmpeg, mediainfo
    with cd('~/'):
        run('./autodl-setup -w --lighttpd --rtorrent --rutorrent')

def install_deluge(version):
    install('python', 'python-twisted', 'python-twisted-web',
        'python-openssl', 'python-simplejson', 'python-setuptools',
        'intltool', 'python-xdg', 'python-chardet', 'geoip-database',
        'python-libtorrent', 'python-notify', 'python-pygame',
        'python-glade2', 'librsvg2-common', 'xdg-utils', 'python-mako')
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
        
def install_transmission():
    install('transmission-daemon')

def install_quota(arg, version):
    # 1.4.13
    # TODO: Edit fstab file
    install('quota')
    run('/etc/init.d/quota stop')
    if arg == 'op' or arg == 's4u':
        run('mount -o remount /')
    if arg == 'ovh':
        run('mount -o remount /home')
    if arg == 's4u':
        run('mount -o remount /home2')
    run('quotacheck -avugm')
    run('/etc/init.d/quota start')
    run('wget https://github.com/ekenberg/quotatool/archive/v%s.zip' % version)
    run('unzip v%s.zip' % version)
    with cd('quotatool-%s' % version), settings(warn_only=True):
        run('./configure')
        run('make -j2')
        run('make install')
    run('rm -r *%s*' % version)

def install_openvpn():
    install('openvpn', 'easy-rsa')
    run('mkdir /etc/openvpn/easy-rsa')
    run('cp -r /usr/share/doc/openvpn/examples/easy-rsa/2.0/* \
        /etc/openvpn/easy-rsa')
    with cd('/etc/openvpn/easy-rsa'):
        run('source vars')
        run('./clean-all')
        run('./build-ca')
        run('./build-key-server server')
        run('./build-dh')
#    with cd('/etc/openvpn/easy-rsa/keys'):
#        run('cp server.key server.crt ca.crt dh1024.pem /etc/openvpn')
    run('iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 \
        -j MASQUERADE')
    # edit /etc/sysctl.conf: net.ipv4.ip_forward = 1
    run('echo 1 > /proc/sys/net/ipv4/ip_forward')
    put('openvpn/server.conf', '/etc/openvpn/')
    run('/etc/init.d/openvpn start')

def install_wine():
    run('dpkg --add-architecture i386')
    update_system()
    install('wine-bin:i386')

@parallel
def set_protection():
    run('chmod 770 /usr/bin/htop /usr/bin/top /bin/ps')
    with settings(warn_only=True):
        run('chmod 711 /home /home2')

def set_locale():
    run('echo LANG="en_GB.UTF-8" > /etc/default/locale')
    run('echo en_GB.UTF-8 UTF-8 > /etc/locale.gen')
    run('locale-gen')

def set_cron():
    run('echo -e "\n" >> /etc/crontab')
    run('echo "*/5 * * * *     root    /root/startrt start all > /dev/null" >> /etc/crontab')
