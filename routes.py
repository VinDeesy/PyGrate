from flask import Flask, flash, redirect, render_template, request, session, abort
from ldap3 import Server, Connection
import flask
import functools
from app import app
import os



app.secret_key = os.urandom(12)

ldap_uri = 'ldaps://138.202.168.3:636'
s = Server(ldap_uri, port=636)

kvm_server = {}
kvm_server['centos7'] = 'scratch1'
kvm_server['centos8'] = 'scratch2'

vms = ['centos7','centos8']


def validate_upload(f):
  def wrapper():
    if 'completed' not in flask.session or not flask.session['completed']:
      return flask.redirect('/')
    return f()
  return wrapper


@app.route('/', methods = ['GET'])
def home():
    html = """
   <form action='/second' method = 'POST'>
     <input type='text' name='username'>
     <input type='password' name='password'>
     <input type='submit' value='Submit'>
   </form>
   """
    return html



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






  return flask.redirect('/upload')



@app.route('/upload', methods=['POST','GET'])
@validate_upload
def do_something():
    if flask.request.method == 'POST':
        vm = flask.request.form.get("vm")
        print(vm)



    return render_template('server_select.html', vms=vms)
