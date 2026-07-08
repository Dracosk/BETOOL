import boto3
from dotenv import load_dotenv

load_dotenv()
NOMBRE_DEL_BUCKET = 'bot-etl-s3-bucket'

def load_csv(folder, archive_name):
    try:
        s3 = boto3.client('s3')
        print(f"Uploading {archive_name} to bucket{NOMBRE_DEL_BUCKET}")
        s3.upload_file(archive_name,NOMBRE_DEL_BUCKET, archive_name)
        
        ruta_s3 = f"s3://{NOMBRE_DEL_BUCKET}/{folder}/{archive_name}"
    except Exception as e:
        print(f"Error for connecting or uploading {e}")
        return False
    return ruta_s3 
    
    
if __name__ == "__main__":
        load_csv('Odd_LaLiga.csv')
