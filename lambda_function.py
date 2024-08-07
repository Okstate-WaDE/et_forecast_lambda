import json
import boto3
import requests
from datetime import datetime
import csv
# import reverse_geocode
from geopy.geocoders import Nominatim


import os
os.chdir("/tmp")

def lambda_handler(event, context):
    
    #start new code here -------->
    # 1st step fetching the crop details from get api
    headers = {
        "forecast": "loKjxR1at9N37WgNAUnr9pGWgDQmNy3et6mTgItbLRS6te3SdSGmwOxM5v08JRk"
    }
    print("event type :; ",type(event))
    print("event is :: ",event)
    #print("event body type :: ",type(event['body']))
    print("request version is :: ",requests.__version__)

    #Handling multiple events structures. 
    if 'body' in event:
        data = event['body']
        print("body is :: ",data)
        data = json.loads(data)
    else:
        data = event
        print("body is in simple event:: ",data)
        data = json.dumps(data)
        data = json.loads(data)
    print("data type is ",type(data))
    print("username is ",data.get('username'))
    username = data.get('username')
    #url = f'https://api-test.canopeoapp.beardon.com/canopeo/api/v1/EXDwXSR3TY6LhArDeHaHWWxr48MTKr1aHVuSiEMV0ZKodAEnPbeVWeLbp4cy1jp?username={username}'
    url=f'https://canopeoapp.com/canopeo/api/v1/EXDwXSR3TY6LhArDeHaHWWxr48MTKr1aHVuSiEMV0ZKodAEnPbeVWeLbp4cy1jp?username={username}'
    
    # Specify the CSV file name 
    #csv_file = '/users.csv'
    #print("file path is :: ",csv_file)
    
    # Get the current directory of the lambda function
    current_dir = os.path.dirname(os.path.realpath(__file__))
    print("current_dir :: ",current_dir)
    
    # Construct the full file path
    file_path = os.path.join(current_dir, 'betausers.csv')
    
    # Read the CSV file
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        users = [row for row in reader]

    # Extracting names from the list of dictionaries
    usersList = [user['Name'] for user in users]
    
    # Print the list of users
    for user in users:
        print(user['Name'])
    print("type ",type(users))
    
    
    data = ""
    try:    
        response = requests.get(url, headers=headers)
        #print("response :: ",response.json())
        print("response is :: ",response)
        response.raise_for_status()  # Raise an error for bad status codes
        
        print("test1")
        # Process the response as needed
        data = response.json()
        print("test2")
        print("d is",len(data))

        
        
        # Beta_users_list
        # beta_users_list = ["mamata.pandey@okstate.edu","jeff.sadler@okstate.edu", "saikumar.payyavula@okstate.edu","fieldtest@test.com"]
        if data:
            first_entry = data[0]
            email = first_entry.get('email')
            user_id = str(first_entry.get('id'))
            canopy_cover = str(first_entry.get('canopy_cover'))
            planting_date = first_entry.get('planting_date')
            adjustments = first_entry.get('adjustments')
            original_image = first_entry.get('original_image')
            processed_image = first_entry.get('processed_image')
            latitude = float(first_entry.get('latitude'))
            longitude = float(first_entry.get('longitude'))
            #for addition details
            print("data from GET api is :: ",first_entry)
            date = str(first_entry.get("date_time"))
            cropType = str(first_entry.get("vegetation_type"))
            cropHeight = str(first_entry.get("vegetation_height"))
            photoDate = str(first_entry.get("created_at"))

            #Planting Date convertion
            # Parse the original datetime string to a datetime object
            planting_date = datetime.strptime(planting_date, "%Y-%m-%dT%H:%M:%S.%fZ")
            photoDate = datetime.strptime(photoDate, "%Y-%m-%dT%H:%M:%S.%fZ")

            # Format the datetime object to the desired format
            planting_date = planting_date.strftime("%Y-%m-%d %H:%M:%S")
            photoDate = photoDate.strftime("%Y-%m-%d %H:%M:%S")

            #Fetch lat, long details of current location
            locationDetails = get_current_location(12.0, 13.45)
            print("location Details :: ",locationDetails)

            cropData = {
                "Email": email,
                #"Date": date,
                "Latitude": latitude,
                "Longitude": longitude,
                "Planting Date": planting_date,
                "Crop Type": cropType,
                "Crop Height": cropHeight,
                "Photo Date":photoDate,
                "Location" : locationDetails
            }
            print("Crop Data is :: ",cropData)
            
            print(f"Email: {email}, ID: {user_id}")
            if(email not in usersList):
                return {
                    'statusCode': 200,
                    'body': "Success."#response #json.dumps(form_data)
                }
            
            
            # 4th step calling et-forecast analysig function
            #response = func1(latitude, longitude)
            #here update changes
            client = boto3.client('lambda')
            payload = {
                'latitude': latitude,
                'longitude': longitude
            }
            response = client.invoke(
                FunctionName='generate_et_forecast_test',
                InvocationType='RequestResponse',  # Use 'Event' for asynchronous invocation
                Payload=json.dumps(payload)
            )
            response_payload = json.loads(response['Payload'].read())
            response = response_payload["body"]
            print("response from ANOTHER LAMBDA----->>",json.dumps(response_payload))
            print("et-response type: ",type(response))
            print("et-response : ",response)
            # 5th step sending an email to the user.
            isEmailValid = True
            try:
                print("mail is :: ",email)
                send_email(email, response, cropData)
            except Exception as e:
                print("email is not verified",e)
                isEmailValid = False
                '''return {
                   'statusCode': 500,
                    'body': 'Some issue in Email ..!' #json.dumps(form_data)
                }'''
            print(type(response))
            
            # new step for s3 storage
            json_data = {
                "email": email,
                "id": user_id,
                "canopy_cover": canopy_cover,
                "planting_date": planting_date,
                "adjustments": adjustments,
                "original_image": original_image,
                "processed_image": processed_image,
                "latitude": latitude,
                "longitude": longitude,
                "isEmailValid" : isEmailValid,
                "et-forecast" : response
            }
            
            # Write data to a JSON file
            with open('/tmp/data.json', 'w') as json_file:
                json.dump(json_data, json_file)
            print("Json file created to store into S3 bucket")
            
            #3rd step load json file  into S3
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            json_data = json.dumps(json_data, indent=2)
            s3_bucket_name = 'et-forecast'
            s3_object_key = f'{email}#{timestamp}.json'
            s3_object_key = s3_object_key.replace('"','')
            
            s3 = boto3.client('s3')
            s3.put_object(Body=json_data, Bucket=s3_bucket_name, Key=s3_object_key)
            # ended s3 storage
            
            
            return {
                'statusCode': 200,
                'body': "Successfully generated ET-Forecast values and sent an email to the user."#response #json.dumps(form_data)
            }
    
    except requests.exceptions.RequestException as e:
        print("Provided username does not contain the data in the GET Api ",e)
        return {
                   'statusCode': 500,
                    'body': 'No Data found with the provided username..!' #json.dumps(form_data)
                }
    
    
    #end new code here <-----
    



        
def send_email(mail, response, cropData):
    sesClient = boto3.client("ses",region_name ="us-east-2")
    print("actual ",response)
    data = json.loads(response)
    html_table = data_to_html(data, cropData)
    #print("html table ",html_table)
    emainResponse = sesClient.send_email(
        
        Destination ={
            "ToAddresses": [mail]
        },
        Message={
            "Body":{
                "Html":{
                    "Data": html_table
                }
                
            },
            "Subject":{
                "Data":"Reg: ET Forecast Updates"
            },
        },
        Source ="baewaterdata@okstate.edu"
        )


def data_to_html(data, cropData):
    html_content = "<html><body>"

    # Add cropData information above the table
    html_content += "<div><br>"
    for key, value in cropData.items():
        html_content += f"<p><strong>{key}:</strong> {value}</p>"
    html_content += "</div>"

    # Create the table
    html_content += "<table border='1'><tr>"
    headers = data[0].keys() if data else []
    for header in headers:
        html_content += f"<th>{header}</th>"
    html_content += "</tr>"
    
    for item in data:
        html_content += "<tr>"
        for value in item.values():
            html_content += f"<td style='text-align: center;'>{value}</td>"
        html_content += "</tr>"
    
    html_content += "</table></body></html>"
    return html_content

def get_current_location(lat, long):
    # coord = (lat, long)
    # print("co-ordinates:: ",coord)
    # location = reverse_geocode.get(coord)
    geolocator = Nominatim(user_agent="canopeo")
    location = geolocator.reverse((lat, long))
    print("geopy iss--->>>> ",location.address)
    
    city =  location.raw['address'].get('city', ''),
    state =  location.raw['address'].get('state', ''),
    country =  location.raw['address'].get('country', '')
    formatted_location = f"{city}, {state}, {country}"
    return formatted_location