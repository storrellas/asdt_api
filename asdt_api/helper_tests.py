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

  def list_device(self):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Get All
    response = self.client.get(self.base_url)
    self.assertTrue(response.status_code == HTTPStatus.OK)

  def list_device_not_allowed(self):
    
    # Get Token
    self.authenticate("viewer@asdt.eu", "asdt2019")

    # Get All
    response = self.client.get(self.base_url)
    self.assertTrue(response.status_code == HTTPStatus.FORBIDDEN)   

  def retrieve_device(self, id):
    
    # Get Token
    self.authenticate("admin@asdt.eu", "asdt2019")

    # Get single
    response = self.client.get('{}/{}/'.format(self.base_url_trimmed, id))
    self.assertTrue(response.status_code == HTTPStatus.OK)

  
  def create_update_delete_device(self, body, bodyupdated):
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
    response_json = json.loads(response.content.decode())
    instance_id = response_json['id']

    # Check properly created
    instance = self.model.objects.get( id=instance_id )
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    if 'name' in body:
      self.assertEqual( instance.name, body['name'] )
    elif 'sn' in body:
      self.assertEqual( instance.sn, body['sn'] )
    self.assertTrue( group.has_device(instance) )

    # Update
    response = self.client.put('{}/{}/'.format(self.base_url_trimmed, instance.id), bodyupdated, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)    

    # Check properly created
    instance = self.model.objects.get( id=instance_id )
    group = Group.objects.get(id=body['groups'][0])
    group_updated = Group.objects.get(id=bodyupdated['groups'][0])
    if 'name' in bodyupdated:
      self.assertEqual( instance.name, bodyupdated['name'] )
    elif 'sn' in bodyupdated:
      self.assertEqual( instance.sn, bodyupdated['sn'] )
    self.assertFalse( group.has_device(instance) )
    self.assertTrue( group_updated.has_device(instance) )

    # Delete
    response = self.client.delete('{}/{}/'.format(self.base_url_trimmed, instance.id), format='json')
    self.assertTrue(response.status_code == HTTPStatus.NO_CONTENT)    

    # Check properly created    
    group = Group.objects.get(id=body['groups'][0])
    group_updated = Group.objects.get(id=bodyupdated['groups'][0])
    self.assertTrue( self.model.objects.filter( id=instance_id ).count() == 0 )


  def update_only_group_device(self, body, bodyupdated):
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
    response_json = json.loads(response.content.decode())
    instance_id = response_json['id']

    # Check properly created
    instance = self.model.objects.get( id=instance_id )
    group = Group.objects.get(name='ADMIN_CHILD_ASDT')
    if 'name' in body:
      self.assertEqual( instance.name, body['name'] )
    elif 'sn' in body:
      self.assertEqual( instance.sn, body['sn'] )
    self.assertTrue( group.has_device(instance) )


    # Update
    response = self.client.put('{}/{}/'.format(self.base_url_trimmed, instance.id), bodyupdated, format='json')
    self.assertTrue(response.status_code == HTTPStatus.OK)    

    # Check properly updated
    instance = self.model.objects.get( id=instance_id )
    group = Group.objects.get(id=body['groups'][0])
    group_updated = Group.objects.get(id=bodyupdated['groups'][0])
    if 'name' in body:
      self.assertEqual( instance.name, body['name'] )
    elif 'sn' in body:
      self.assertEqual( instance.sn, body['sn'] )
    self.assertFalse( group.has_device(instance) )
    self.assertTrue( group_updated.has_device(instance) )

    # Delete instance
    instance.delete()
    group = Group.objects.get(id=body['groups'][0])
    group_updated = Group.objects.get(id=bodyupdated['groups'][0])
