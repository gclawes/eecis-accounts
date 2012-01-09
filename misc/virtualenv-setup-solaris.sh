#!/bin/bash

cd ~
wget http://www.eecis.udel.edu/~lawes/python_solaris.tar.gz
gtar xvzf python_solaris.tar.gz

mkdir ~/python-virtualenv ~/virtualenv-temp

cd ~/virtualenv-temp

wget http://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.6.4.tar.gz

gtar xvf virtualenv-1.6.4.tar.gz
cd virtualenv-1.6.4

python virtualenv.py --no-site-packages --distribute --python=$HOME/python/bin/python ~/python-virtualenv

cd ~/python-virtualenv
rm -r ~/virtualenv-temp	

source ~/python-virtualenv/bin/activate

echo "Now using python from ~/python-virtualenv"

pip install Flask Flask-SQLAlchemy Flask-WTF pymysql itsdangerous passlib py-bcrypt

echo "Virtualenv setup completed! Please do not delete ~/python or ~/python-virtualenv"

