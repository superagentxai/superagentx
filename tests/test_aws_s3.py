from agentx.handler.aws_s3 import AWSS3Handler
import os
s3_handler = AWSS3Handler(

    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    bucket_name="ocppbeta-artifacts",
    region_name="ap-south-1"



)
def test_s3_handler_1():
    #res = s3_handler.list_buckets()
    current_directory = os.path.dirname(os.path.abspath(__file__))

    # Define the .txt file name
    txt_upload_file_name = 'test.txt'

    # Full path to the .txt file
    file_path = os.path.join(current_directory, txt_upload_file_name)
    #uncomment to test upload files
    res=s3_handler.upload_file(file_path,"test_new_folder/test_sub_folder/test.txt")
    #uncomment to test download files
    # download_res=s3_handler.download_file("test_new_folder/test_sub_folder/test.txt","E:/praveena_aws/testterdownload.txt")
    #uncomment to test list files
    #list_files = s3_handler.list_files()
    #print(list_files)


