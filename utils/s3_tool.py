import boto3
from dotenv import load_dotenv

load_dotenv()
NOMBRE_DEL_BUCKET = 'betool-dl'

def upload_to_s3(folder, archive_name):
    try:
        ruta_s3 = f"{folder}/{archive_name}"
        s3 = boto3.client('s3')
        s3.upload_file(archive_name,NOMBRE_DEL_BUCKET, ruta_s3)
        print(f"Uploading {archive_name} to bucket{NOMBRE_DEL_BUCKET}")
        
    except Exception as e:
        print(f"Error for connecting or uploading {e}")
        return False
    return ruta_s3 
    
    

    
