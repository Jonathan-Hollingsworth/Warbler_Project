"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test model for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_following(self):
        """Tests the `is_following` and `is_followed_by` methods"""

        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )

        u3 = User(
            email="test3@test.com",
            username="testuser3",
            password="HASHED_PASSWORD"
        )

        db.session.add_all([u1, u2, u3])
        db.session.commit()

        u1.following.append(u2)
        u3.following.append(u1)
        db.session.commit()

        self.assertEqual(u1.is_following(u2), True)
        self.assertEqual(u1.is_following(u3), False)
        self.assertEqual(u1.is_followed_by(u3), True)
        self.assertEqual(u1.is_followed_by(u2), False)

    def test_user_signup(self):
        """Tests the `signup` class method for User"""

        user = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="/static/images/default-pic.png"
        )

        db.session.commit()
        
        self.assertEqual(User.query.get(user.id), user)
        self.assertRaises(ValueError, User.signup, email=None, username=None, password=None, image_url=None)

        error = User.signup(
            email="test@test.com", 
            username="testuser", 
            password="HASHED_PASSWORD", 
            image_url=None)

        self.assertRaises(IntegrityError, db.session.commit)

    def test_user_authentication(self):
        """Tests the `authenticate` class method for User"""

        user = User.signup(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="/static/images/default-pic.png"
        )

        db.session.commit()

        self.assertEqual(User.authenticate("testuser", "HASHED_PASSWORD"), user)
        self.assertEqual(User.authenticate("testuser", "WRONG_PASSWORD"), False)
        self.assertEqual(User.authenticate("wronguser", "HASHED_PASSWORD"), False)

    def test_user_repr(self):
        """Test the `__repr__` method to see if it workd properly"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        self.assertEqual(u.__repr__(), f'<User #{u.id}: {u.username}, {u.email}>')