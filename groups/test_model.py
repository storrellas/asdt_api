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

class GroupModelTestCase(APITestCase):


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


  def test_group_get_full_devices(self):
    group = Group.objects.get(name='ADMIN_ASDT')
    devices = group.get_full_devices()
    self.assertEqual(len(devices.detectors), 3)
    

  def test_group_is_parent_of(self):
    # Check Ok
    admin_child_child_group = Group.objects.get(name='ADMIN_CHILD_CHILD_ASDT')
    admin_group = Group.objects.get(name='ADMIN_ASDT')
    self.assertTrue(admin_group.is_parent_of(admin_child_child_group))

    # Check inverse    
    self.assertFalse(admin_child_child_group.is_parent_of(admin_group))

    # Check other group
    viewer_group = Group.objects.get(name='VIEWER_ASDT')
    self.assertFalse(admin_group.is_parent_of(viewer_group))

  def test_group_get_full_children(self):
    group = Group.objects.get(name='ADMIN_ASDT')
    group_children = group.get_full_children()
    self.assertTrue(len(group_children) == 4)

  def print_tree(self, group):
    print(group.name)
    output = group.name + ": "
    print(output)
    for item in group.childs:      
      output = output + self.print_tree(item) + " "
    return output
    
  def test_group_get_tree_children(self):
    group = Group.objects.get(name='ADMIN_ASDT')
    group_tree = group.get_tree_children()
    self.assertEqual(len(group_tree['children']), 2)
    self.assertEqual(len(group_tree['children'][0]['children']), 2)
    self.assertEqual(len(group_tree['children'][1]['children']), 0)

  def test_delete_recursive(self):
    # Creating scenario
    delete_child_group = Group.objects.create(name='DELETE_CHILD_ASDT', 
                                            devices=GroupDevices())
    delete_group = Group.objects.create(name='DELETE_ASDT', childs=[delete_child_group], 
                                            devices=GroupDevices())    
    delete_child_group.parent = delete_group
    delete_child_group.save()

    # Create viewer
    delete_user = User.objects.create(email='delete@asdt.eu', name='delete', role='ADMIN',
                                  group=delete_child_group, hasGroup=True)
    delete_child_group.users.append(delete_user)                                  
    delete_child_group.save()

    # Launch delete recursive
    delete_group.delete_recursive()

    # Assertions
    self.assertTrue(Group.objects.filter(name='DELETE_CHILD_ASDT').count() == 0)
    self.assertTrue(Group.objects.filter(name='DELETE_ASDT').count() == 0)

    user = User.objects.get(email='delete@asdt.eu')
    self.assertTrue(user.group == None)






