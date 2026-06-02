from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Conversation, Message, Notification
from .views import unread_chat_message_count


class ChatUnreadBadgeTests(TestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(username='viewer', password='pass12345')
        self.sender = User.objects.create_user(username='sender', password='pass12345')
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.viewer, self.sender)
        Message.objects.create(conversation=self.conversation, sender=self.viewer, body='Earlier reply')
        Message.objects.create(conversation=self.conversation, sender=self.sender, body='One')
        Message.objects.create(conversation=self.conversation, sender=self.sender, body='Two')

    def test_inbox_does_not_mark_messages_seen(self):
        self.client.force_login(self.viewer)

        response = self.client.get(reverse('inbox'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(unread_chat_message_count(self.viewer), 2)

    def test_opening_specific_chat_marks_that_chat_seen(self):
        self.client.force_login(self.viewer)

        response = self.client.get(reverse('chat_room', kwargs={'conversation_id': self.conversation.id}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(unread_chat_message_count(self.viewer), 0)

    def test_new_message_notification_opens_inbox_not_chat(self):
        self.client.force_login(self.viewer)

        response = self.client.post(
            reverse('chat_room', kwargs={'conversation_id': self.conversation.id}),
            {'body': 'Please check this'},
        )

        self.assertEqual(response.status_code, 302)
        notification = Notification.objects.get(user=self.sender, title='New message')
        self.assertEqual(notification.url, reverse('inbox'))
