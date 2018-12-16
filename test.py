from launchkey.exceptions import EntityNotFound
import unittest
from launchkey.factories.service import ServiceFactory

organization_id = "2cd1360e-ff2e-11e8-911c-0a3c3cadd4fd"
organization_private_key = open('organization_private_key.key').read()
directory_id = "0172917a-ff69-11e8-ae69-4a5e312d9ab1"
service_id = "b3f8ddb2-ff33-11e8-871a-4a5e312d9ab1"
service_private_key = open('service_private_key.key').read()

service_factory = ServiceFactory(service_id, service_private_key)

class FlaskTestCase(unittest.TestCase):
    
    def test_get_organization_private_key(self):
        organization_private_key = open('organization_private_key.key').read()
        self.assertTrue(b'-----BEGIN RSA PRIVATE KEY-----' in organization_private_key)
        
    def test_get_service_private_key(self):
        service_private_key = open('service_private_key.key').read() 
        self.assertTrue(b'-----BEGIN RSA PRIVATE KEY-----' in service_private_key)

    def test_create_service_clien_successfully(self):
        service_client = service_factory.make_service_client()
        self.assertTrue(b'<launchkey.' in str(service_client))
    
    def test_get_auth_request_successfully(self):
        service_client = service_factory.make_service_client()
        auth_request_id = service_client.authorize("fcrojas28")
        self.assertTrue(b'-' in auth_request_id)
        
    def test_get_auth_request_with_user_not_found(self):
        service_client = service_factory.make_service_client()
        try:
            service_client.authorize("fcrojas28xxxx")
        except EntityNotFound as e:
            self.assertTrue(b'Unable to find user' in str(e))
        
    
if __name__ == '__main__' :
    unittest.main()