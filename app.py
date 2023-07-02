import csv
import pyodbc
from flask import Flask, jsonify, request
import pandas as pd

# Connect to the database
connection = pyodbc.connect('DRIVER=ODBC Driver 17 for SQL Server;SERVER=<your-server-name>;DATABASE=<your-database-name>;UID=<your-username>;PWD=<your-password>;Trusted_Connection=yes;')
cursor = connection.cursor()

# Check if the tables exist
tables_exist = False
cursor.execute("SELECT 1 FROM sys.tables WHERE name = 'FactPopulation'")
if cursor.fetchone():
    tables_exist = True

if not tables_exist:
    # Create the tables if they don't exist
    cursor.execute('''
        CREATE TABLE DimRegion (
            RegionCode INT PRIMARY KEY,
            RegionName VARCHAR(255),
            StateCode INT,
            StateName VARCHAR(255)
        );
    ''')

    cursor.execute('''
        CREATE TABLE DimSex (
            SexCode INT PRIMARY KEY,
            Sex VARCHAR(255)
        );
    ''')

    cursor.execute('''
        CREATE TABLE DimAge (
            AgeCode VARCHAR(10) PRIMARY KEY,
            Age VARCHAR(255)
        );
    ''')

    cursor.execute('''
        CREATE TABLE FactPopulation (
            RegionCode INT,
            SexCode INT,
            AgeCode VARCHAR(10),
            CensusYear INT,
            Population INT,
            PRIMARY KEY (RegionCode, SexCode, AgeCode, CensusYear)
        );
    ''')

# Read the CSV file
data = pd.read_csv('<your-file-path>/data.csv')

# Normalize and insert data into dimension tables
region_data = data[['ASGS_2016', 'Region', 'STATE', 'State']].drop_duplicates()
region_data['ASGS_2016'] = region_data['ASGS_2016'].astype(str)  # Convert ASGS_2016 to string type
state_data = region_data[region_data['ASGS_2016'].str.len() == 2]
sa4_data = region_data[region_data['ASGS_2016'].str.len() == 5]

# Insert data into DimRegion for state codes
for _, row in state_data.iterrows():
    state_code = row['ASGS_2016']
    state_name = row['State']
    cursor.execute("SELECT RegionCode FROM DimRegion WHERE RegionCode = ?", state_code)
    existing_row = cursor.fetchone()
    if not existing_row:
        cursor.execute("INSERT INTO DimRegion (RegionCode, RegionName, StateCode, StateName) VALUES (?, ?, ?, ?)",
                       state_code, row['Region'], state_code, state_name)
connection.commit()

# Insert data into DimRegion for SA4 codes
for _, row in sa4_data.iterrows():
    region_code = row['ASGS_2016']
    state_code = region_code[:2]
    state_name = state_data.loc[state_data['ASGS_2016'] == state_code, 'State'].values[0]
    cursor.execute("SELECT RegionCode FROM DimRegion WHERE RegionCode = ?", region_code)
    existing_row = cursor.fetchone()
    if not existing_row:
        cursor.execute("INSERT INTO DimRegion (RegionCode, RegionName, StateCode, StateName) VALUES (?, ?, ?, ?)",
                       region_code, row['Region'], state_code, state_name)
connection.commit()

# Normalize and insert data into the fact table
for _, row in data.iterrows():
    region_code = row.get('ASGS_2016', '')
    state_code = row.get('STATE', '')
    sex_code = row.get('SEX_ABS', '')
    age_code = str(row.get('AGE', ''))
    census_year = row.get('Census year', '')
    population = row.get('Value', '')

    # Check if the record already exists
    cursor.execute('''
        SELECT 1
        FROM FactPopulation
        WHERE RegionCode = ? AND SexCode = ? AND AgeCode = ? AND CensusYear = ?
    ''', region_code, sex_code, age_code, census_year)

    if cursor.fetchone():
        continue  # Skip the record if it already exists

    cursor.execute("INSERT INTO FactPopulation (RegionCode, SexCode, AgeCode, CensusYear, Population) VALUES (?, ?, ?, ?, ?)",
                   region_code, sex_code, age_code, census_year, population)

    # If the region has a state code, insert an additional record for the state aggregation
    if state_code:
        cursor.execute('''
            SELECT 1
            FROM FactPopulation
            WHERE RegionCode = ? AND SexCode = ? AND AgeCode = ? AND CensusYear = ?
        ''', state_code, sex_code, age_code, census_year)

        if cursor.fetchone():
            continue  # Skip the record if it already exists

        cursor.execute("INSERT INTO FactPopulation (RegionCode, SexCode, AgeCode, CensusYear, Population) VALUES (?, ?, ?, ?, ?)",
                       state_code, sex_code, age_code, census_year, population)

connection.commit()

# Commit the changes and close the connection
connection.commit()

# Set up the Flask app
app = Flask(__name__)

def get_region_name(region_code):
    # Function to retrieve the region name based on the region code
    cursor.execute('SELECT RegionName FROM DimRegion WHERE RegionCode = ?', region_code)
    row = cursor.fetchone()
    if row:
        return row[0]
    return None

def get_sa4_codes(state_code):
    # Function to retrieve the SA4 codes based on the state code
    cursor.execute('SELECT RegionCode FROM DimRegion WHERE StateCode = ?', (state_code,))
    rows = cursor.fetchall()
    sa4_codes = [row[0] for row in rows]
    return sa4_codes


def get_state_code(sa4_code):
    # Function to retrieve the state code based on the SA4 code
    cursor.execute('SELECT StateCode FROM DimRegion WHERE RegionCode = ?', (sa4_code,))
    row = cursor.fetchone()
    if row:
        state_code = row[0]
        return state_code
    else:
        return None

@app.route('/api/age-structure/<string:code>/<int:sex_code>', methods=['GET'])
def get_age_structure(code, sex_code):
    # Check if the code is a state code
    cursor.execute('SELECT RegionCode FROM DimRegion WHERE StateCode = ?', (code,))
    row = cursor.fetchone()
    if row:
        sa4_codes = None  # Do not aggregate for SA4 codes
    else:
        sa4_codes = [code]  # Use the provided code as an SA4 code

    result = {
        'regionCode': code,
        'regionName': get_region_name(code),
        'data': []
    }

    if not sa4_codes:
        # Get all SA4 codes for the given state code
        cursor.execute('SELECT RegionCode FROM DimRegion WHERE StateCode = ?', (code,))
        sa4_codes = [row[0] for row in cursor.fetchall()]

    cursor.execute('''
        SELECT da.Age, fp.CensusYear, SUM(fp.Population) AS Population, ds.Sex
        FROM FactPopulation AS fp
        JOIN DimAge AS da ON fp.AgeCode = da.AgeCode
        JOIN DimSex AS ds ON fp.SexCode = ds.SexCode
        WHERE fp.RegionCode IN ({}) AND fp.SexCode = ?
        GROUP BY da.Age, fp.CensusYear, ds.Sex
        ORDER BY da.Age, fp.CensusYear
    '''.format(','.join('?' * len(sa4_codes))), *sa4_codes, sex_code)

    columns = [column[0] for column in cursor.description]

    for row in cursor.fetchall():
        row_data = dict(zip(columns, row))
        age = f"{row_data['Age']} year old"
        census_year = row_data['CensusYear']
        population = row_data['Population']
        sex = row_data['Sex']

        result['data'].append({
            'age': age,
            'sex': sex,
            'censusYear': census_year,
            'population': population
        })

    return jsonify(result)

@app.route('/api/age-structure-diff/<string:code>/<int:sex>/<int:year1>/<int:year2>', methods=['GET'])
def get_age_structure_diff(code, sex, year1, year2):
    # Check if the code is a state code
    cursor.execute('SELECT RegionCode FROM DimRegion WHERE StateCode = ?', (code,))
    row = cursor.fetchone()
    if row:
        region_codes = cursor.execute('SELECT RegionCode FROM DimRegion WHERE StateCode = ?', (code,)).fetchall()
        region_codes = [region_code[0] for region_code in region_codes]
    else:
        region_codes = [code]

    cursor.execute('''
        SELECT dr.RegionCode, dr.RegionName, da.Age, ds.Sex, ABS(fp2.Population - fp1.Population) AS population
        FROM FactPopulation fp1
        JOIN FactPopulation fp2 ON fp1.RegionCode = fp2.RegionCode AND fp1.SexCode = fp2.SexCode AND fp1.AgeCode = fp2.AgeCode
        JOIN DimRegion dr ON fp1.RegionCode = dr.RegionCode
        JOIN DimAge da ON fp1.AgeCode = da.AgeCode
        JOIN DimSex ds ON fp1.SexCode = ds.SexCode
        WHERE dr.RegionCode IN ({}) AND ds.SexCode = ? AND fp1.CensusYear = ? AND fp2.CensusYear = ?
    '''.format(','.join('?' * len(region_codes))), *region_codes, sex, year1, year2)

    data = []
    columns = [column[0] for column in cursor.description]

    for row in cursor.fetchall():
        row_data = dict(zip(columns, row))
        age = f"{row_data['Age']} year old"
        sex = row_data['Sex']
        population = row_data['population']

        data.append({
            'age': age,
            'sex': sex,
            'population': population
        })

    result = {
        'regionCode': code,
        'regionName': get_region_name(code),
        'censusYear': f"{year1}-{year2}",
        'data': data
    }

    return jsonify(result)

if __name__ == '__main__':
    app.run()

'''
This script connects to a SQL Server database and performs data normalization and insertion. It creates the necessary tables if they don't exist and inserts data from a CSV file into the dimension and fact tables.

The Flask app is set up to provide two API endpoints:
1. `/api/age-structure/<string:code>/<int:sex_code>` - Retrieves age structure data for a given region code and sex code. It aggregates the data for SA4 codes if the provided code is a state code.
2. `/api/age-structure-diff/<string:code>/<int:sex>/<int:year1>/<int:year2>` - Retrieves the difference in age structure data between two census years for a given region code, sex, and years. It calculates the difference in population between the two years.

To run the script, you need to have the required dependencies installed, such as `pyodbc` and `pandas`. Make sure to replace the database connection details and CSV file path with your own.

Once the script is running, you can make HTTP requests to the API endpoints using a tool like `curl` or a web browser.

Note: The script assumes that the data in the CSV file follows a specific format and that the dimension and fact tables have been defined appropriately in the database schema.
'''
