#!/bin/bash
PYTHON=python2.7
mkdir build
cd build
curl -O http://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.6.4.tar.gz
tar xfvz virtualenv-1.6.4.tar.gz
cd virtualenv-1.6.4
python virtualenv.py --no-site-packages --distribute --python=PYTHON ../../accounts-py
cd ../..
source ./accounts-py/bin/activate
pip install Flask Flask-SQLAlchemy Flask-WTF pymysql itsdangerous passlib py-bcrypt
rm -r build
echo "Downloads complete."
echo "Copying the config example. Using sqlite by default."
cp accounts/config-example.py accounts/config.py
echo "Setting up the database."
python accounts -r
echo "A python virtual environment has been created in `pwd`/accounts-py/"
echo "To activate it, run \`source `pwd`/accounts-py/bin/activate\`."
echo "It must be activated in order for the test environment to run properly."
echo "To run the code, check the options by running \`python accounts -h\`."