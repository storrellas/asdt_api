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
from mongo_dummy import MongoDummy
from .models import *
from user.models import User

logger = utils.get_logger()

class GroupTestCase(APITestCase):


  @classmethod
  def setUpClass(cls):
    """
    Called once in every suite
    """
    super().setUpClass()
    logger.info("----------------------------")
    logger.info("--- Generating scenario  ---")
    logger.info("----------------------------")    
    settings.MONGO_DB = 'asdt_test'
    logger.info("DB Generated: {}".format(settings.MONGO_DB))

    mongo_dummy = MongoDummy()
    mongo_dummy.setup(settings.MONGO_DB, settings.MONGO_HOST, int(settings.MONGO_PORT))
    mongo_dummy.generate_scenario()

  def setUp(self):
    """
    Called before every test
    """
    pass

  def authenticate(self, user, password):
    # Get token
    response = self.client.post('/api/v2/user/authenticate/', 
                            { "email": user, "password": password })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['data']['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

  def test_get(self):
    
    group = Group.objects.get(name='ADMIN_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Add groups
    response = self.client.get('/api/v2/groups/{}/'.format(group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

  def test_get_not_allowed(self):
    
    group = Group.objects.get(name='VIEWER_ASDT')

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Add groups
    response = self.client.get('/api/v2/groups/{}/'.format(group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertFalse(response_json['success'])

  def test_get_all_admin(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Get All
    response = self.client.get('/api/v2/groups/all/')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])
    self.assertEqual(len(response_json['data']), 5)

  def test_get_all_viewer(self):
    
    # Get Token
    self.authenticate("viewer@asdt.eu", "asdt2019")

    # Get All
    response = self.client.get('/api/v2/groups/all/')
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])
    self.assertEqual(len(response_json['data']), 1)

  def test_create(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Create group
    body = { 'name': 'TEST_GROUP' }
    response = self.client.post('/api/v2/groups/', body)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

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
    response = self.client.post('/api/v2/groups/', body)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])

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
    response = self.client.put('/api/v2/groups/{}/'.format(group.id), body)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])
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
    body = { 'name': 'ADMIN_CHILD_ASDT_UPDATED', 'newParent': group_parent.id }
    response = self.client.put('/api/v2/groups/{}/'.format(group.id), body)
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])
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
    response = self.client.delete('/api/v2/groups/{}/'.format(delete_group.id))
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    self.assertTrue(response_json['success'])
    self.assertTrue(Group.objects.filter(name='DELETE_ASDT').count() == 0)
    self.assertTrue(Group.objects.filter(name='DELETE_CHILD_ASDT').count() == 0)
    user = User.objects.get(email='delete@asdt.eu')
    self.assertTrue(user.group == None)












