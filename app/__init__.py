from flask import Flask

app = Flask(__name__)
app.static_folder = 'static'
app.secret_key = "key1" # NOTE: changing this clears all session cookies

from app import routes