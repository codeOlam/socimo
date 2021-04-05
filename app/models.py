"""Database models."""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app import db


class User(UserMixin, db.Model):
    """User account model."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=False)
    email = db.Column(db.String(40), unique=True, nullable=False )
    password = db.Column(db.String(200), primary_key=False, unique=False, nullable=False)
    photo = db.Column(db.LargeBinary, index=False, unique=False, nullable=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow, index=False, unique=False, nullable=True)
    last_login = db.Column(db.DateTime, index=False, unique=False, nullable=True)
    posts = db.relationship('Post', backref='user', lazy=True)

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password, method='sha256')

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

    def __repr__(self):
        return '<User {}>'.format(self.name)



class Post(db.Model):
    """
        This is the Post model
    """
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text)
    created_on = db.Column(db.DateTime, default=datetime.utcnow, index=False, unique=False, nullable=True)


    def __repr__(self):
        return '<post: {}::{}>'.format(self.user.name, self.content)