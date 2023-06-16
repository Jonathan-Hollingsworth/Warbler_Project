"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes

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


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Likes.query.delete()

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

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")
    
    def test_remove_message(self):
        """Can user remove a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_id

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()

            resp2 = c.post(f"/messages/{msg.id}/delete")

            self.assertEqual(resp2.status_code, 302)
            self.assertEqual(Message.query.one_or_none(), None)
    
    def test_remove_message_fail(self):
        """Is a user unable to remove another user's message"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_id

            c.post("/messages/new", data={"text": "Hello"})

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_id2

            msg = Message.query.one()

            resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('You cannot delete someone else&#39;s message.', html)
            self.assertNotEqual(Message.query.one_or_none(), None)

    def test_message_like(self):
        """Can a user like a message that isn't their own"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_id

            c.post("/messages/new", data={"text": "Hello"})

            msg = Message.query.one()

            resp1 = c.post(f"/users/add_like/{msg.id}", follow_redirects=True)

            html1 = resp1.get_data(as_text=True)

            self.assertEqual(resp1.status_code, 200)
            self.assertIn('You cannot like your own message.', html1)
            self.assertEqual(Likes.query.one_or_none(), None)

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_id2

            resp2 = c.post(f"/users/add_like/{msg.id}")

            self.assertEqual(resp2.status_code, 302)
            self.assertNotEqual(Likes.query.one_or_none(), None)

    def test_logged_out(self):
        """Are messages unaffected by users who aren't logged in?"""

        with self.client as c:

            resp1 = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)

            html1 = resp1.get_data(as_text=True)

            self.assertEqual(resp1.status_code, 200)
            self.assertIn('Access unauthorized.', html1)
            self.assertEqual(Message.query.one_or_none(), None)

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.test_id

            c.post(f"/messages/new", data={"text": "Hello"})

            c.get("/logout")

            msg = Message.query.one()

            self.assertEqual(msg.text, "Hello")

            resp2 = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)

            html2 = resp2.get_data(as_text=True)

            self.assertEqual(resp2.status_code, 200)
            self.assertIn('Access unauthorized.', html2)
            self.assertNotEqual(Message.query.one_or_none(), None)
