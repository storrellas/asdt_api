from django.test import TestCase

# Create your tests here.
import csv, json
from http import HTTPStatus

from django.test import TestCase, Client
from django.http import HttpRequest
from django.conf import settings
from rest_framework.test import APITestCase
from unittest.mock import patch

# Projet imports
from asdt_api import utils
from asdt_api import helper_tests
from mongo_dummy import MongoDummy
from .models import *
from user.models import User

logger = utils.get_logger()

class TestCase(helper_tests.ASDTTestCase):


  @classmethod
  def setUpClass(cls):
    """
    Called once in every suite
    """
    super().setUpClass()

  def setUp(self):
    """
    Called before every test
    """
    pass

  def test_get(self):
    
    group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Add groups
    response = self.client.get('/{}/groups/{}/'.format(settings.PREFIX, group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)


  def test_get_not_allowed(self):
    
    group = Group.objects.get(name='VIEWER_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Add groups
    response = self.client.get('/{}/groups/{}/'.format(settings.PREFIX, group.id))
    self.assertTrue(response.status_code == HTTPStatus.BAD_REQUEST)

  def test_get_all_admin(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Get All
    response = self.client.get('/{}/groups/all/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(len(response_json), 5)

  def test_get_all_viewer(self):
    
    # Get Token
    self.authenticate("viewer@asdt.eu", "asdt2019")

    # Get All
    response = self.client.get('/{}/groups/all/'.format(settings.PREFIX))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertEqual(len(response_json), 1)

  def test_create(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Create group
    body = { 'name': 'TEST_GROUP' }
    response = self.client.post('/{}/groups/'.format(settings.PREFIX), body)
    self.assertTrue(response.status_code == HTTPStatus.OK)

    # Check created
    user = User.objects.get(email='admin@asdt.eu')
    self.assertTrue(Group.objects.filter(name='TEST_GROUP').count() > 0)
    group = Group.objects.get(name='TEST_GROUP')
    self.assertEqual(user.group, group.parent)
    
    # Remove resources
    user.group.childs.remove(group)
    user.group.save()
    group.delete()

  def test_create_group_to_add(self):

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Add user to group
    group_to_add = Group.objects.get(name='ADMIN_CHILD_ASDT')
    body = { 'name': 'TEST_GROUP', 'groupToAdd':  group_to_add.id }
    response = self.client.post('/{}/groups/'.format(settings.PREFIX), body)
    self.assertTrue(response.status_code == HTTPStatus.OK)

    # Check created
    self.assertTrue(Group.objects.filter(name='TEST_GROUP').count() > 0)
    group = Group.objects.get(name='TEST_GROUP')
    self.assertEqual(group_to_add, group.parent)

    # Remove resources
    group_to_add = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group_to_add.childs.remove(group)
    group_to_add.save()
    group.delete()

  def test_update(self):
    # Target group to which add users
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Update group
    body = { 'name': 'ADMIN_CHILD_ASDT_UPDATED' }
    response = self.client.put('/{}/groups/{}/'.format(settings.PREFIX, group.id), body)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    self.assertTrue(Group.objects.filter(name='ADMIN_CHILD_ASDT_UPDATED').count() > 0)

    # Leave it as it was
    group = Group.objects.get(name='ADMIN_CHILD_ASDT_UPDATED')
    group.name = 'ADMIN_CHILD_ASDT'
    group.save()


  def test_update_parent(self):
    # Target group to which add users
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    former_group_parent = Group.objects.get(name='ADMIN_ASDT')
    group_parent = Group.objects.get(name='ADMIN_CHILD2_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Update group
    body = { 'name': 'ADMIN_CHILD_ASDT_UPDATED', 'parent': group_parent.id }
    response = self.client.put('/{}/groups/{}/'.format(settings.PREFIX, group.id), body)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    self.assertTrue(Group.objects.filter(name='ADMIN_CHILD_ASDT_UPDATED').count() > 0)

    # Check parent modified
    group = Group.objects.get(name='ADMIN_CHILD_ASDT_UPDATED')
    former_group_parent = Group.objects.get(name='ADMIN_ASDT')
    group_parent = Group.objects.get(name='ADMIN_CHILD2_ASDT')
    self.assertTrue(group.parent == group_parent)
    self.assertFalse( group in former_group_parent.childs )
    self.assertTrue( group in group_parent.childs )

    # Leave it as it was
    group.name = 'ADMIN_CHILD_ASDT'
    group.parent = former_group_parent
    group.save()

  def test_delete(self):
    admin_group = Group.objects.get(name='ADMIN_ASDT')

    # Creating scenario
    delete_child_group = Group.objects.create(name='DELETE_CHILD_ASDT', 
                                            devices=GroupDevices(), parent=admin_group)
    delete_group = Group.objects.create(name='DELETE_ASDT', childs=[delete_child_group], 
                                            devices=GroupDevices(), parent=admin_group)    
    delete_child_group.parent = delete_group
    delete_child_group.save()

    # Create user
    delete_user = User.objects.create(email='delete@asdt.eu', name='delete', role='ADMIN',
                                  group=delete_child_group, hasGroup=True)
    delete_child_group.users.append(delete_user)                                  
    delete_child_group.save()

    admin_group.childs.append(delete_group)
    admin_group.save()
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Delete Group
    response = self.client.delete('/{}/groups/{}/'.format(settings.PREFIX, delete_group.id))
    self.assertTrue(response.status_code == HTTPStatus.NO_CONTENT)
    self.assertTrue(Group.objects.filter(name='DELETE_ASDT').count() == 0)
    self.assertTrue(Group.objects.filter(name='DELETE_CHILD_ASDT').count() == 0)
    user = User.objects.get(email='delete@asdt.eu')
    self.assertTrue(user.group == None)

  def test_get_group_users(self):
    admin_group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Request users
    response = self.client.get('/{}/groups/{}/users/'.format(settings.PREFIX, admin_group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)

  def test_get_group_groups(self):
    admin_group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Request groups
    response = self.client.get('/{}/groups/{}/groups/'.format(settings.PREFIX, admin_group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)

  def test_add_user(self):
    
    # Create user with a group assigned
    user = User.objects.create(email='test@asdt.eu', name='test')
    viewer_group = Group.objects.get(name='VIEWER_ASDT')
    viewer_group.users.append(user)
    viewer_group.save()
    user.hasGroup = True
    user.group = viewer_group
    user.save()

    # Target group to which add users
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Add user to group
    response = self.client.post('/{}/groups/{}/users/{}/'.format(settings.PREFIX, group.id, user.id), {})
    self.assertTrue(response.status_code == HTTPStatus.OK)


    # Check groups properly configured
    group_id = user.group.id
    former_group = Group.objects.get(id=group_id)
    self.assertFalse( user in group.users )

    user = User.objects.get(email='test@asdt.eu')
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    self.assertEqual( user.group, group )
    self.assertTrue( user in group.users )

    # Delete user from group
    response = self.client.delete('/{}/groups/{}/users/{}/'.format(settings.PREFIX, group.id, user.id), {})
    self.assertTrue(response.status_code == HTTPStatus.NO_CONTENT)

    # Leave it as it was
    user = User.objects.get(email='test@asdt.eu')
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    self.assertNotEqual( user.group, group )
    self.assertFalse( user in group.users )
    user.delete()

  def test_add_user_not_allowed(self):
    
    user = User.objects.get(email='viewer@asdt.eu')
    group = Group.objects.get(name='VIEWER_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Add groups
    response = self.client.post('/{}/groups/{}/users/{}/'.format(settings.PREFIX, group.id, user.id), {})
    self.assertTrue(response.status_code == HTTPStatus.BAD_REQUEST)





