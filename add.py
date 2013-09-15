#!/usr/bin/python

import argparse
import os
import os.path
import htpasswd
from random import randint


def convert_to_giga(string):
    return round(float(string)*1073741824)

def convert_to_tera(string):
    return round(float(string)*1099511627776)

class User:
    def __init__(self, username, password, home):
        self.username = username
        self.password = password
        self.homedir = home
        self.homedir = '{0}/{1}'.format(home, username)
        if os.path.isfile('/etc/gentoo-release'):
            self.system = 'gentoo'
        else:
            self.system = 'debian'

    def create_user(self):
        os.mkdir(self.homedir)
        os.system('useradd -d {0} {1}'.format(self.homedir, self.username))
        os.system('chown {0}:{0} -R {1}'.format(self.username, self.homedir))

    def set_main_password(self):
        os.system('passwd {}'.format(self.password))

    def set_www_password(self):
        if self.system == 'gentoo':
            generate_password = htpasswd.HtpasswdFile('/etc/lighttpd/rutorrent_passwd')
        else:
            generate_password = htpasswd.HtpasswdFile('/usr/local/lighttpd/rutorrent_passwd')
        generate_password.update(self.username, self.password)
        generate_password.save()

    def set_rtorrent(self, active):
        os.mkdir('/var/rutorrent/rutorrent/conf/users/{}'.format(self.username))
        os.mkdir('{}/downloads'.format(self.homedir))
        os.mkdir('{}/.rtorrent'.format(self.homedir))

        template = open('files/rtorrent_rc', 'r')
        template = template.read().format(username=self.username, homedir=self.homedir, port=randint(20000, 29999))
        f = open('{}/.rtorrent.rc'.format(self.homedir), 'a')
        f.write(template)
        if active:
            f.write('scheduler.max_active.set = {}'.format(active))

        template = open('files/rutorrent_config', 'r')
        template = template.read().format(homedir=self.homedir, xmlrpc=randint(10000000000, 99999999999))
        f = open('/var/rutorrent/rutorrent/conf/users/{}/config.php'.format(self.username), 'a')
        f.write(template)

        self.set_www_password()

        os.system('chown root:root {}/.rtorrent.rc'.format(self.homedir))
        os.system('chmod 644 {}/.rtorrent.rc'.format(self.homedir))
        os.system('chown {0}:{0} -R {1}/downloads'.format(self.username, self.homedir))
        os.system('chown {0}:{0} -R {1}/.rtorrent'.format(self.username, self.homedir))
        os.system('chown lighttpd:{} -R /var/rutorrent/rutorrent/share/users/{}'.format(self.username))
    
    def set_vnc(self):
        os.mkdir('{0}/.vnc'.format(self.homedir))
        os.system('cp files/xscreensaver {0}/.xscreensaver')
        os.system('cp files/xstartup {0}/.vnc')
        os.system('chown {0}:{0} -R {1}/.vnc'.format(self.username, self.homedir))
        os.system('chmod +x {}/.vnc/xstartup'.format(self.homedir))

    def set_quota(self, value):
        os.system('quotatool -u {0} -bl {1} {2}'.format(self.username, convert_to_giga(value), mountpoint)) # mountpoint

    def set_transfer_limit(self, value):
        os.system('iptables -A OUTPUT -p tcp -m owner --uid-owner {0} -m quota --quota {1} -j ACCEPT'.format(self.username, convert_to_tera(value)))
        os.system('iptables -A OUTPUT -p tcp -m owner --uid-owner {}} -j DROP'.format(self.username))
        f = open('/etc/iptables-save', 'w')
        f.write(os.system('iptables-save'))
parser = argparse.ArgumentParser()

parser.add_argument('-u', '--username', required=True)
parser.add_argument('-p', '--password', required=True)
parser.add_argument('-m', '--mount-point', default='/home')
parser.add_argument('-d', '--home-dir', default='/home')
parser.add_argument('-r', '--rtorrent', type=int)
parser.add_argument('-q', '--quota', type=convert_to_giga)
parser.add_argument('-t', '--transfer', type=convert_to_tera)
args = parser.parse_args()


create_user = User(args.username, args.password, args.home_dir)
create_user.create_user()
create_user.set_rtorrent(args.rtorrent)
print(vars(create_user))
