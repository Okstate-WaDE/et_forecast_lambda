import json
import boto3
import requests
from requests_toolbelt.multipart.decoder import MultipartDecoder
import base64
from datetime import datetime
import numpy as np

#below is mamatas modules
import os
os.chdir("/tmp")        
import pandas as pd
import openmeteo_requests
import requests_cache
from retry_requests import retry
import urllib.parse

def lambda_handler(event, context):
    
    #start new code here -------->
    # 1st step fetching the crop details from get api
    headers = {
        "forecast": "loKjxR1at9N37WgNAUnr9pGWgDQmNy3et6mTgItbLRS6te3SdSGmwOxM5v08JRk"
    }
    print("event body type :: ",type(event['body']))
    print("request version is :: ",requests.__version__)
    '''print("openmeteo_requests version is::",requests_toolbelt.__version__)
    print("requests_cache version is :: ",requests_cache.__version__)
    print("retry_requests version is :: ",retry_requests.__version)
    print("requests_toolbelt version is ::",requests_toolbelt.__version__)'''

    data = event['body']
    print("body is :: ",data)
    data = json.loads(data)
    print("data type is ",type(data))
    print("uname",data.get('username'))
    username = data.get('username')
    url = f'https://api-test.canopeoapp.beardon.com/canopeo/api/v1/EXDwXSR3TY6LhArDeHaHWWxr48MTKr1aHVuSiEMV0ZKodAEnPbeVWeLbp4cy1jp?username={username}'
    
    data = ""
    try:
        response = requests.get(url, headers=headers)
        #print("response :: ",response.json())
        print("response is :: ",response)
        response.raise_for_status()  # Raise an error for bad status codes
        
        # Process the response as needed
        data = response.json()
        print("d is",len(data))
        
        # Beta_users_list
        beta_users_list = ["mamata.pandey@okstate.edu","jeff.sadler@okstate.edu", "saikumar.payyavula@okstate.edu","fieldtest@test.com"]
        if data:
            first_entry = data[0]
            email = first_entry.get('email')
            user_id = str(first_entry.get('id'))
            canopy_cover = str(first_entry.get('canopy_cover'))
            planting_date = first_entry.get('planting_date')
            adjustments = first_entry.get('adjustments')
            original_image = first_entry.get('original_image')
            processed_image = first_entry.get('processed_image')
            latitude = str(first_entry.get('latitude'))
            longitude = str(first_entry.get('longitude'))
            
            print(f"Email: {email}, ID: {user_id}")
            if(email not in beta_users_list):
                return {
                    'statusCode': 200,
                    'body': "Success."#response #json.dumps(form_data)
                }
            
            # 2nd step Prepare the data to be written to JSON
            '''json_data = {
                "email": email,
                "id": user_id,
                "canopy_cover": canopy_cover,
                "planting_date": planting_date,
                "adjustments": adjustments,
                "original_image": original_image,
                "processed_image": processed_image,
                "latitude": latitude,
                "longitude": longitude
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
            s3.put_object(Body=json_data, Bucket=s3_bucket_name, Key=s3_object_key)'''
            
            # 4th step calling et-forecast analysig function
            response = func1(latitude, longitude)
            print("et-response type: ",type(response))
            print("et-response : ",response)
            # 5th step sending an email to the user.
            isEmailValid = True
            try:
                print("mail is :: ",email)
                send_email(email, response)
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
    '''
    # Sample data from Postman
    print(event['isBase64Encoded'])
    if event['isBase64Encoded']:
        data = base64.b64decode(event['body'])
    else:
        data = event['body'].encode()
    content_type = event['headers'].get('Content-Type')
    
    # Parse the multipart data
    print("data = ",data)
    decoder = MultipartDecoder(data, content_type)
    
    # Extract form fields and values
    form_data = {}
    # print("parts :: ",decoder.parts)
    # params for defined for string to flaot conversion logic
    params = ['canopy_cover','planting_date','adjustments','original_image','processed_image'] #'latitude', 'longitude','cropheight',
    
    datalist=[]
    # allparams defined for is value is present or not logic
    #allParams = ['latitude', 'longitude','cropheight','email','image','calcanopy','plantingdate']
    count = 0
    
    mail =''
    latitude = ''
    longitude = ''
    originalImage = ''
    for part in decoder.parts:
        try:
            # Attempt to decode the content as UTF-8 (text)
            content = part.content.decode('utf-8')
        except UnicodeDecodeError:
            # If decoding fails, treat it as binary data
            #content = part.content
            content = base64.b64encode(part.content).decode('utf-8')

        content_disposition = part.headers[b'Content-Disposition'].decode('utf-8')
        name_start = content_disposition.find('name="') + len('name="')
        name_end = content_disposition.find('"', name_start)
        field_name = content_disposition[name_start:name_end]
        
        print("field_name:", field_name)
        #print("content:", content)
        if field_name == 'email':
            mail = content
            print("mail is : ",mail)
        if field_name == 'latitude':
            latitude = content
        if field_name == 'longitude':
            longitude = content
        if field_name == 'original_image' or field_name == 'processed_image' :
            imageContent = content
            json_data = ''
            try:
                json_data = json.loads(imageContent)
            except Exception as e:
                return {
                   'statusCode': 500,
                    'body': 'Json format issue..! in '+field_name #json.dumps(form_data)
                }
            print("originalImage ",json_data)
        #start verification for value is present or not
        
        #end verification
        if field_name in params:
            if len(content) == 0:
                return {
                   'statusCode': 500,
                    'body': 'Something went wrong in the mondatory fields..!' #json.dumps(form_data)
                }
            # type conversion from string to float
            
            print(" c type is",type(content))
        form_data[field_name] = content
        #checking here all parameters should be validate
        if field_name in params:
            count = count +1;
            datalist.append(field_name)
    
    #check the mandotory fields covered or not logic
    if count != 5:
        filtered_list = [x for x in params if x not in datalist]
        return {
                   'statusCode': 500,
                    'body': 'All Mandotory fields are not sent. missing fields are = '+str(filtered_list) #json.dumps(form_data)
                }
    
    #load it into s3
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    json_data = json.dumps(form_data, indent=2)
    s3_bucket_name = 'et-forecast'
    s3_object_key = f'{mail}#{timestamp}.json'
    s3_object_key = s3_object_key.replace('"','')
    

    s3 = boto3.client('s3')
    s3.put_object(Body=json_data, Bucket=s3_bucket_name, Key=s3_object_key)
    response = func1(latitude, longitude)
    
    #email part started
    try:
        send_email(mail, response)
    except Exception as e:
        print("email is not verified")
    print(type(response))
    #email part ended
    return {
        'statusCode': 200,
        'body': response#'Successfully Data Stored into S3 Bucket..!' #json.dumps(form_data)
    }'''




def func1(latitude,longitude):
        # Setup the Open-Meteo API client with cache and retry on error
        cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        openmeteo = openmeteo_requests.Client(session = retry_session)
        
        latitude = float(latitude)
        longitude = float(longitude)
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "et0_fao_evapotranspiration",
                "wind_speed_unit": "ms",
                "timezone": "auto",
                "forecast_days": 16
        }
            
        responses = openmeteo.weather_api(url, params=params)
            
        # Process response. 
        response = responses[0]
            
        daily = response.Daily()
        daily_et0_fao_evapotranspiration = daily.Variables(0).ValuesAsNumpy()
        
        #Rounding the digits after decimal point
        daily_et0_fao_evapotranspiration = np.round(daily_et0_fao_evapotranspiration, 2)

        daily_data = {"Valid Date": pd.date_range(
                start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
                end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
                freq = pd.Timedelta(seconds = daily.Interval()),
                inclusive = "left" 
                ).strftime('%Y-%m-%d')}
            
        daily_data["Reference ET (in mm)"] = daily_et0_fao_evapotranspiration
        daily_dataframe = pd.DataFrame(data = daily_data)
        #print("type is")
        #print(type(daily_dataframe['Valid Date'][0]))
        daily_dataframe['Valid Date'] = daily_dataframe['Valid Date'].astype(str)
        daily_dataframe['Reference ET (in inches)'] = np.round((daily_dataframe['Reference ET (in mm)']/25.4),2).astype(str)
        daily_dataframe['Reference ET (in mm)'] = daily_dataframe['Reference ET (in mm)'].astype(str)
        

        # Rename Valid date to Date
        daily_dataframe = daily_dataframe.rename(columns ={"Valid Date" : "Date"})
        print("ffinal :: ",daily_dataframe)
        return daily_dataframe.to_json(orient='records')
        
def send_email(mail, response):
    sesClient = boto3.client("ses",region_name ="us-east-2")
    print("actual ",response)
    data = json.loads(response)
    html_table = data_to_html(data)
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


def data_to_html(data):
    html_content = "<html><body><table border='1'><tr>"
    headers = data[0].keys() if data else []
    for header in headers:
        html_content += f"<th>{header}</th>"
    html_content += "</tr>"
    
    for item in data:
        print(item)
    for item in data:
        html_content += "<tr>"
        for value in item.values():
            html_content += f"<td style='text-align: center;'>{value}</td>"
        html_content += "</tr>"
    html_content += "</table></body></html>"
    return html_content