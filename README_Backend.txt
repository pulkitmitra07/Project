# Age Structure Data Management

This project provides a script to manage age structure data in a SQL Server database and exposes an API to retrieve age structure information for different regions.

## Features

- Data normalization and insertion into dimension and fact tables
- API endpoints to retrieve age structure data and population differences between census years

## Prerequisites

- Python 3.6 or higher
- Dependencies : csv, Flask, pyodbc, pandas
- Access to a SQL Server database
- CSV file containing age structure data (`data.csv`)

## Installation

1. Clone the repository

2. Install the required dependencies

## Configuration

1. Update the database connection details in the script (`app.py`) to match your SQL Server database:
connection = pyodbc.connect('DRIVER=ODBC Driver 17 for SQL Server;SERVER=<your-server-name>;DATABASE=<your-database-name>;UID=<your-username>;PWD=<your-password>;Trusted_Connection=yes;')

2. Place your CSV file containing age structure data in the project directory and update the file path in the script (`app.py`):
data = pd.read_csv('<your-file-path>/data.csv')

## Usage

1. Run the script to create tables, normalize data, and start the Flask app:
py app.py


2. The Flask app will start running on `http://localhost:5000`.

3. Use API endpoints to retrieve age structure data:

- `/api/age-structure/<string:code>/<int:sex_code>` - Retrieves age structure data for a given region code and sex code.
- `/api/age-structure-diff/<string:code>/<int:sex>/<int:year1>/<int:year2>` - Retrieves the difference in age structure data between two census years for a given region code, sex, and years.

Get age structure for a specific region and sex:

Endpoint: /api/age-structure/{code}/{sex_code}
Example: /api/age-structure/1/1 (Get age structure for Central Coast region with sex code 1)
Example: /api/age-structure/102/1 (Get age structure for Central Coast region with sex code 1)

Get age structure difference between two years for a specific region and sex:

Endpoint: /api/age-structure-diff/{code}/{sex}/{year1}/{year2}
Example: /api/age-structure-diff/1/1/2011/2016 (Get age structure difference between 2011 and 2016 for Central Coast region with sex code 1)
Example: /api/age-structure-diff/102/1/2011/2016 (Get age structure difference between 2011 and 20216 for Cntral Coast region with sex code 1)

Replace {code} with the desired region code (state code or SA4 code) and {sex_code} with the desired sex code (e.g., 1 for male, 2 for female). In the age structure difference endpoint, replace {year1} and {year2} with the desired years for comparison.

Make sure to run the Flask app using app.run() to start the API server before making the API requests.

## Testing

1.To test the API endpoints, a test_api.py file is created which contains unittest for Endpoint: /api/age-structure/{code}/{sex_code}. Here's an example of how to test the API:
1.1 Make sure to run the Flask app using app.run()
1.2 Run the unittest : py test_api.py
1.3 The tests will send requests to the specified API endpoints and validate the responses
1.4 If the test is successful, the output of the unittest framework will show the test results as a summary. Each test method in the TestAgeStructureAPI class will be executed, and if all assertions pass without any errors, the test will be considered successful.

Here's an example of the expected output when running the test_api.py file:

..
----------------------------------------------------------------------
Ran 2 tests in 4.096s

OK


In this example, the .. indicates that tests (test_get_age_structure_endpoint) and (test_get_age_structure_diff_endpoint) passed successfully. The OK message at the end indicates that all tests were executed without any errors.

If any assertion fails during the test, the output will indicate which specific test failed and provide details about the assertion error. This helps in identifying the exact issue that caused the test to fail.






