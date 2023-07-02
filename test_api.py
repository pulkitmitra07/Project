import unittest
import requests

class TestAgeStructureAPI(unittest.TestCase):
    def setUp(self):
        # Set up the base URL for the API
        self.base_url = 'http://localhost:5000/api'

    def test_get_age_structure_endpoint(self):
        # Test the /api/age-structure endpoint

        # Make a GET request to the endpoint
        response = requests.get(f'{self.base_url}/age-structure/102/1')

        # Check the response status code
        self.assertEqual(response.status_code, 200)

        # Check the response data
        data = response.json()
        self.assertEqual(data['regionCode'], '102')
        self.assertEqual(data['regionName'], 'Central Coast')
        self.assertIsInstance(data['data'], list)
        self.assertTrue(len(data['data']) > 0)

        for item in data['data']:
            self.assertIn('age', item)
            self.assertIn('sex', item)
            self.assertIn('censusYear', item)
            self.assertIn('population', item)

    def test_get_age_structure_diff_endpoint(self):
        # Test the /api/age-structure-diff endpoint

        # Make a GET request to the endpoint
        response = requests.get(f'{self.base_url}/age-structure-diff/102/1/2011/2016')

        # Check the response status code
        self.assertEqual(response.status_code, 200)

        # Check the response data
        data = response.json()
        self.assertEqual(data['regionCode'], '102')
        self.assertEqual(data['regionName'], 'Central Coast')
        self.assertEqual(data['censusYear'], '2011-2016')
        self.assertIsInstance(data['data'], list)
        self.assertTrue(len(data['data']) > 0)

        for item in data['data']:
            self.assertIn('age', item)
            self.assertIn('sex', item)
            self.assertIn('population', item)

if __name__ == '__main__':
    unittest.main()