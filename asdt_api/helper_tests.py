from django.test import TestCase

# Create your tests here.
import csv, json
from http import HTTPStatus

from django.test import TestCase, Client
from django.http import HttpRequest
from django.conf import settings
from rest_framework.test import APITestCase


# Projet imports
from asdt_api import utils
from mongo_dummy import MongoDummy
from groups.models import Group

logger = utils.get_logger()

class ASDTTestCase(APITestCase):

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
    super().setUp()

  def authenticate(self, user, password):
    # Get token
    response = self.client.post('/{}/user/authenticate/'.format(settings.PREFIX), 
                            { "email": user, "password": password })
    self.assertTrue(response.status_code == HTTPStatus.OK)
    response_json = json.loads(response.content.decode())
    access_token = response_json['token']
    self.client.credentials(HTTP_AUTHORIZATION='Basic ' + access_token)

class DeviceTestCase(ASDTTestCase):

  base_url = None
  base_url_trimmed = None


  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # Remove last trailing slash
    if self.base_url is not None:
      self.base_url_trimmed = self.base_url[:-1] if self.base_url[-1] == '/' else self.base_url

  def setUp(self):
    """
    Called before every test
    """
    super().setUp()

  def test_list(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Get All
    response = self.client.get(self.base_url)
    self.assertTrue(response.status_code == HTTPStatus.OK)

  def test_retrieve(self, id):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Get single
    response = self.client.get('{}/{}/'.format(self.base_url_trimmed, id))
    self.assertTrue(response.status_code == HTTPStatus.OK)

  
  def test_create_update_delete(self, body, bodyupdated):
    """
    Checks:
    - item created properly with body 
    - item updated properly with bodyupdated
    """

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    group = Group.objects.get(id=body['groups'][0])
    group_updated = Group.objects.get(id=bodyupdated['groups'][0])

    # Create
    response = self.client.post('{}/'.format(self.base_url_trimmed), body, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)

    # Check properly created
    instance = self.model.objects.get( name='myname' )
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    self.assertTrue( instance in group.devices.zones )
    self.assertTrue( group.has_device(instance) )
    self.assertTrue( group in instance.groups )

    # Update
    response = self.client.put('{}/{}/'.format(self.base_url_trimmed, instance.id), bodyupdated, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)    

    # Check properly created
    instance = self.model.objects.get( name='mynameupdated' )
    group = Group.objects.get(id=body['groups'][0])
    group_updated = Group.objects.get(id=bodyupdated['groups'][0])
    self.assertFalse( group.has_device(instance) )
    self.assertTrue( group_updated.has_device(instance) )
    self.assertTrue( group_updated in instance.groups )

    # Delete
    response = self.client.delete('{}/{}/'.format(self.base_url_trimmed, instance.id), format='json')
    self.assertTrue(response.status_code == HTTPStatus.NO_CONTENT)    

    # Check properly created    
    group = Group.objects.get(id=body['groups'][0])
    group_updated = Group.objects.get(id=bodyupdated['groups'][0])
    self.assertTrue( self.model.objects.filter( name='mynameupdated' ).count() == 0 )


  def test_update_only_group(self, body, bodyupdated):
    """
    Checks:
    - item created properly with body 
    - item updated properly with bodyupdated
    """

    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group_2 = Group.objects.get(name='ADMIN_CHILD2_ASDT')

    # Create
    response = self.client.post('/{}/zones/'.format(settings.PREFIX), body, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)

    # Check properly created
    zone = Zone.objects.get( name='myname' )
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    self.assertTrue( zone in group.devices.zones )
    self.assertTrue( group in zone.groups )


    # Update
    response = self.client.put('/{}/zones/{}/'.format(settings.PREFIX, zone.id), bodyupdated, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)    

    # Check properly created
    zone = Zone.objects.get( name='myname' )
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    group2 = Group.objects.get(name='ADMIN_CHILD2_ASDT')
    self.assertFalse( group.has_device(zone) )
    self.assertTrue( group2.has_device(zone) )
    self.assertTrue( group2 in zone.groups )
