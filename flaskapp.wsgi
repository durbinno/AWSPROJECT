import sys

# This must match wherever you copy the project folder to on the EC2 instance.
sys.path.insert(0, "/var/www/flaskapp/")

from app import app as application
