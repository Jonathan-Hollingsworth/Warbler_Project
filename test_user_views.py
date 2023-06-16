"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py

import os
from unittest import TestCase

from models import db, connect_db, User, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        
        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

        self.test_id = self.testuser.id #We save the id to a separate variable to prevent errors
        self.test_id2 = self.testuser2.id 

    def test_user_follow(self):
        """Can one user follow another user using the app"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_id

            c.post(f'/users/follow/{self.test_id2}')

            usr1 = User.query.get(self.test_id)
            usr2 = User.query.get(self.test_id2)

            self.assertEqual((usr1.is_following(usr2)), True)
            self.assertEqual((usr2.is_followed_by(usr1)), True)

    def test_user_view_page(self):
        """Can a user view the page of another user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_id

            resp = c.get(f'/users/{self.test_id2}')

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Messages", html)
            self.assertIn("Following", html)
            self.assertIn("Followers", html)
            self.assertIn("likes", html)

    def test_user_logged_out(self):
        """Will certain actions be prohibited while logged out"""

        with self.client as c:

            resp1 = c.get(f'/users/profile', follow_redirects=True)
            resp2 = c.post(f'/users/follow/{self.test_id2}', follow_redirects=True)
            resp3 = c.post('/users/delete', follow_redirects=True)

            html1 = resp1.get_data(as_text=True)
            html2 = resp2.get_data(as_text=True)
            html3 = resp3.get_data(as_text=True)

            self.assertIn("Access unauthorized.", html1)
            self.assertIn("Access unauthorized.", html2)
            self.assertIn("Access unauthorized.", html3)