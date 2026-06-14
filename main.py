from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.exceptions import ClientError
import os
from datetime import datetime
from decimal import Decimal

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# dynamodb = boto3.resource(
#     'dynamodb',
#     region_name=os.getenv('AWS_REGION'),
#     aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
#     aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
# )
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1'
)

# table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))
table = dynamodb.Table('patient-registration-data')

def convert_floats_to_decimal(obj):
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(i) for i in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj

@app.post("/patients")
async def save_patient(patient_data: dict):
    try:
        if 'patientId' not in patient_data:
            raise HTTPException(status_code=400, detail="patientId is required")
        
        item = {
            'patientId': patient_data['patientId'],
            'timestamp': datetime.now().isoformat(),
            **patient_data
        }
        
        item = convert_floats_to_decimal(item)
        table.put_item(Item=item)
        return {"message": "Patient saved successfully", "patientId": patient_data['patientId']}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patients")
async def get_patients():
    try:
        response = table.scan()
        return response.get('Items', [])
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patients/{patient_id}")
async def get_patient(patient_id: str):
    try:
        response = table.query(
            KeyConditionExpression='patientId = :pid',
            ExpressionAttributeValues={
                ':pid': patient_id
            }
        )
        items = response.get('Items', [])
        if items:
            return {"count": len(items), "items": items}
        raise HTTPException(status_code=404, detail="Patient not found")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete/{patient_id}")
async def delete_patient(patient_id: str):
    try:
        response = table.delete_item(
            Key={'patientId': patient_id},
            ReturnValues='ALL_OLD'
        )
        if 'Attributes' in response:
            return {"message": "Patient deleted successfully", "patientId": patient_id}
        raise HTTPException(status_code=404, detail="Patient not found")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/patients/{patient_id}")
async def update_patient(patient_id: str, patient_data: dict):
    try:
        if 'patientId' not in patient_data:
            patient_data['patientId'] = patient_id
        
        # Get the original timestamp if it exists, otherwise create new
        try:
            existing = table.get_item(Key={'patientId': patient_id})
            if 'Item' in existing:
                patient_data['timestamp'] = existing['Item'].get('timestamp', datetime.now().isoformat())
            else:
                patient_data['timestamp'] = datetime.now().isoformat()
        except:
            patient_data['timestamp'] = datetime.now().isoformat()
        
        patient_data['lastUpdated'] = datetime.now().isoformat()
        
        patient_data = convert_floats_to_decimal(patient_data)
        # Use put_item to replace entire item (avoids UpdateExpression size limit)
        table.put_item(Item=patient_data)
        
        return {"message": "Patient updated successfully", "patientId": patient_id, "data": patient_data}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/all-items")
async def get_all_items():
    try:
        items = []
        response = table.scan()
        items.extend(response.get('Items', []))
        
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        return {"count": len(items), "items": items}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/followups")
async def save_followup(followup_data: dict):
    try:
        followup_data = convert_floats_to_decimal(followup_data)
        table.put_item(Item=followup_data)
        return {"message": "Followup saved successfully"}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/followups")
async def get_followups():
    try:
        response = table.scan()
        return response.get('Items', [])
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
