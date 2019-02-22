from flask import Flask, flash, redirect, render_template, request, session, abort
from ldap3 import Server, Connection
import flask
from app import app
import os
from subprocess import PIPE, Popen
import pickle

app.secret_key = os.urandom(12)

ldap_uri = 'ldaps://138.202.168.3:636'
s = Server(ldap_uri, port=636)


with open('/home/david/virt/vm_dict.pickle', 'rb') as handle:
    vm_dict = pickle.load(handle)
with open('/home/david/virt/vm_list.pickle', 'rb') as handle:
    vms = pickle.load(handle)
with open('/home/david/virt/servers.pickle', 'rb') as handle:
    servers = pickle.load(handle)
with open('/home/david/virt/server_count.pickle', 'rb') as handle:
    server_count = pickle.load(handle)


def validate_upload(f):
    def wrapper():
        if 'completed' not in flask.session or not flask.session['completed']:
            return flask.redirect('/')
        return f()

    wrapper.__name__ = f.__name__
    return wrapper


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')




@app.route('/second', methods=['POST'])
def second():
    username, password = flask.request.form['username'], flask.request.form['password']

    u = 'uid={username},ou=People,o=cs,dc=usfca,dc=edu'.format(username=username)
    p = password

    c = Connection(s, user=u, password=p)

    c.open()

    if c.bind():
        flask.session['username'] = username

        flask.session['password'] = password

        flask.session['completed'] = True
    else:
        return flask.redirect('/')

    return flask.redirect('/tabs')


@app.route('/upload', methods=['POST', 'GET'])
@validate_upload
def do_something():
    if flask.request.method == 'POST':
        vm = flask.request.form.get("vm")
        print(vm)

    return render_template('server_select.html', vms=vms, servers=servers)


@app.route('/tabs', methods=['POST', 'GET'])
@validate_upload
def tabs():

    if flask.request.method == 'POST':
        if flask.request.form['btn'] == 'Restart':
            vm = flask.request.form.get("vm")
            print(vm)
            if not restart(vm):
                flash("server is currently offline. Please migrate to another server")
                return render_template('tabs.html', vms=vms, servers=servers)
            return flask.redirect('/done')
        if flask.request.form['btn'] == 'Migrate':
            vm = flask.request.form.get("vm")
            server = flask.request.form.get("server")
            print(vm)
            print(server)
            if not migrate(vm, server):
                flash("dest server is down, please choose another destination server")
                return render_template('tabs.html', vms=vms, servers=servers)

            return flask.redirect('/done')
        if flask.request.form['btn'] == 'Stop':
            vm = flask.request.form.get("vm")
            if not stop(vm):
                flash("that server is currently offline, please email support if this is unexpected")
                return render_template('tabs.html', vms=vms, servers=servers)

            return flask.redirect('/done')

    return render_template('tabs.html', vms=vms, servers=servers)


@app.route('/migrate', methods=['POST', 'GET'])
@validate_upload
def migrate():

    return render_template('migrate.html', vms=vms, servers=servers)

@app.route('/done', methods=['GET'])
@validate_upload
def done():
    html = """
    <h1>DONE</h1>
    """
    return html

def restart(vm):

    server = vm_dict[vm]
    host_rsp = os.system("ping -c 1 " + server)
    if host_rsp is 0:
        cmd = ['ssh', 'root@{0}'.format(server), 'virsh reboot {0}'.format(vm)]
        stream = Popen(cmd, stdin=PIPE, stdout=PIPE)
        rsp = stream.stdout.read().decode('utf-8')
        print(rsp)
        return True
    else:
        return False

def migrate(vm, server_dest):
    dest_rsp = os.system("ping -c 1 " + server_dest)
    host_rsp = os.system("ping -c 1 " + vm_dict[vm])

    if dest_rsp == 0 and host_rsp == 0:

        server = vm_dict[vm]
        cmd = ['ssh', 'root@{0}'.format(server), 'virsh dumpxml {0} > /gfs/{1}.xml'.format(vm, vm),
               '&&', 'virsh destroy {0}'.format(vm)]

        stream = Popen(cmd, stdin=PIPE, stdout=PIPE)
        rsp = stream.stdout.read().decode('utf-8')
        print(rsp)

        cmd = ['ssh', 'root@{0}'.format(server_dest), 'virsh create /gfs/{0}.xml'.format(vm)]
        stream = Popen(cmd, stdin=PIPE, stdout=PIPE)
        rsp = stream.stdout.read().decode('utf-8')
        print(rsp)

        vm_dict[vm] = server_dest


        pickle.dump(vm_dict, open('/home/david/virt/vm_dict.pickle', "wb"))
        return True
    else:
        if dest_rsp is not 0:
            print("DEST DOWN")
            return False
        if host_rsp is not 0:
            cmd = ['ssh', 'root@{0}'.format(server_dest), 'virsh create /gfs/{0}.xml'.format(vm)]
            stream = Popen(cmd, stdin=PIPE, stdout=PIPE)
            rsp = stream.stdout.read().decode('utf-8')
            print(rsp)
            vm_dict[vm] = server_dest
            pickle.dump(vm_dict, open('/home/david/virt/vm_dict.pickle', "wb"))
            return True

def stop(vm):
    host_rsp = os.system("ping -c 1 " + vm_dict[vm])
    if host_rsp is not 0:
        return False
    else:
        cmd = ['ssh', 'root@{0}'.format(vm_dict[vm]), 'virsh destroy {0}'.format(vm)]
        stream = Popen(cmd, stdin=PIPE, stdout=PIPE)
        rsp = stream.stdout.read().decode('utf-8')
        print(rsp)
        return True

def create():
    min_node = min(server_count, key=server_count.get)
    vm_name = 'mcvm%d' % (len(vms) + 1)

    cmd = ['ssh', 'root@{0}'.format(min_node), 'cd /gfs/mcvm && python /gfs/mcvm/genxml.py {0} {1} && '
        'mv {2}.xml /gfs && cd /gfs && virsh define {3}.xml && virsh start {4}'.format(
        (len(vms) + 1), (len(vms) + 1), vm_name, vm_name, vm_name)]

    stream = Popen(cmd, stdin=PIPE, stdout=PIPE)
    rsp = stream.stdout.read().decode('utf-8')
    print(rsp)

    vms.append(vm_name)
    vm_dict[vm_name] = min_node

    pickle.dump(vm_dict, open('/home/david/virt/vm_dict.pickle', "wb"))
    pickle.dump(vms, open('/home/david/virt/vm_list.pickle', 'wb'))

