import json 
import requests
import os

def slice_list_into_chunks(lst, chunk_size=5):
    """Slices a list into chunks of specified size."""
    # Using list comprehension to create chunks
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def upload_tag_res(tagurl,tag_res):
    ifpost = False
    print("tagurl",tagurl)
    # response = requests.get(tagurl)
    headers = {
                "accept": "*/*",
                "Content-Type": "application/json"
            }
    print("tag_res",type(tag_res))
    # half = len(tag_res)
    

    slice_res = slice_list_into_chunks(tag_res)
    for index,slice_  in enumerate(slice_res):
        try:
            response = requests.post(tagurl,json=slice_,headers=headers)
        
            print("index",index,"response",response)
        
            data = response.json()

            if response.status_code == 200:
                if  data["success"] and data["message"] == "Success.":
                    ifpost = True 
            #   
            # data = response.json()
                
            #     print("message",data["message"])
            #     if  data["success"] and data["message"] == "Success.":
            #         ifpost = True
        except Exception as e:
            print("get_tags error",e)
            continue
    return ifpost

if __name__ == "__main__":
    tagurl = "http://44.213.48.82:11181/product/skc/batchTagSkc"
    tagdir  = '/root/autodl-tmp/tmp_res/tag_res/output/20231125_1525/tag_res'
    all_tag_res = os.listdir(tagdir)
    for tag_save_time in  all_tag_res:
        # print("tag_res",tag_res)
        save_date = tag_save_time.split("_")[0]
        save_time = tag_save_time.split("_")[1]
        # if tag_save_time after 1845,the upload
        if (save_date =="20231126") and (save_time <= "0948" ):
            tag_res_path = os.path.join(tagdir,tag_save_time,"tag_res.json")
            with open(tag_res_path,"r") as f:
                tag_res = json.load(f)
            ifpost = upload_tag_res(tagurl,tag_res)
            print(f'save {ifpost} to upload {tag_res_path}')
    # ifpost = upload_tag_res(tagurl,tag_res)
    # print(f'save {ifpost} to upload {tag_res_path}')
