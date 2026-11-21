import boto3
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
NOMBRE_DEL_BUCKET = 'betool-dl'

def upload_to_s3(folder, archive_name):
    local_path = Path(archive_name)
    key = f"{folder.rstrip('/')}/{local_path.name}"
    
    try:
        s3 = boto3.client('s3')
        s3.upload_file(str(local_path),NOMBRE_DEL_BUCKET, key)
        print(f"Uploading {archive_name} to bucket{NOMBRE_DEL_BUCKET}")
        
    except Exception as e:
        print(f"Error for connecting or uploading {e}")
        return False
    return key

def hash_get(route, lt_hash):
    try:
        s3_out = boto3.client('s3')
        s3 = s3_out.get_object(Bucket= NOMBRE_DEL_BUCKET, Key=route)
        hash_value = s3['Body'].read().decode('utf-8')
        if hash_value == lt_hash:
            return False
        else:
            s3_out.put_object(Body=lt_hash, Bucket=NOMBRE_DEL_BUCKET, Key=route)
            return True
    except Exception as e:
        error = str(e)
        if 'NoSuchKey' in error:
            s3_out.put_object(Body=lt_hash, Bucket=NOMBRE_DEL_BUCKET, Key=route)
            return True
        return print(f"Error for connecting or uploading {e}")

    

    
