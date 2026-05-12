from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__, static_folder='../css', static_url_path='/css')

app.config["SECRET_KEY"] = "change-this-before-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'kenniceleong@gmail.com'
app.config['MAIL_PASSWORD'] = 'edgf gfpm ajct jghp'
app.config['MAIL_DEFAULT_SENDER'] = 'kenniceleong@gmail.com'



db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)
mail = Mail(app)
csrf = CSRFProtect(app)

# imported at the bottom to avoid circular imports
from app import models, routes  # noqa: F401