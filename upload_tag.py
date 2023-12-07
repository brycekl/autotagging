import json
import os

import requests
from loguru import logger
from taggingpipeline.mainpipeline.get_info_from_url import upload_tag_res as ori_upload

logger.add("/root/autodl-tmp/tmp_res/logs_util/upload_tag.log", rotation="500 MB", retention="10 days", level="INFO")


def slice_list_into_chunks(lst, chunk_size=2):
    """Slices a list into chunks of specified size."""
    # Using list comprehension to create chunks
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def upload_tag_res(tagurl, tag_res):
    ifpost = False
    print("tagurl", tagurl)
    # response = requests.get(tagurl)
    headers = {
        "accept": "*/*",
        "Content-Type": "application/json"
    }
    print("tag_res", type(tag_res))
    # half = len(tag_res)

    slice_res = slice_list_into_chunks(tag_res)
    for index, slice_ in enumerate(slice_res):
        try:
            response = requests.post(tagurl, json=slice_, headers=headers)

            print("index", index, "response", response)

            data = response.json()

            if response.status_code == 200:
                if data["success"] and data["message"] == "Success.":
                    logger.info(f"upload {index} success")
                    ifpost = True
                else:
                    logger.info(f"upload {index} failed")
            else:
                logger.info(f"upload {index} failed")
            #   
            # data = response.json()

            #     print("message",data["message"])
            #     if  data["success"] and data["message"] == "Success.":
            #         ifpost = True
        except Exception as e:
            print("get_tags error", e)
            continue
    return ifpost, ''


format_item = {"firstCategory": "string",
               "firstFrom": "string",
               "skcId": "string",
               "subCategory": "string",
               "subFrom": "string",
               "tags": {"additionalProp1": ["string"], "additionalProp2": ["string"], "additionalProp3": ["string"]}}


def format_json(json_path):
    with open(json_path, 'r') as r:
        json_data = json.load(r)
    for item in json_data:
        for attr in format_item:
            if attr not in item:
                item[attr] = 'ai'
    return json_data


def upload(tagurl, tagdir):
    all_tag_res = os.listdir(tagdir)
    for path_name in all_tag_res:
        json_path = os.path.join(tagdir, path_name, 'tag_res.json')
        json_data = format_json(json_path)
        ifpost, message = upload_tag_res(tagurl, json_data)
        if ifpost:
            with open(json_path, 'w') as writer:
                json.dump(json_data, writer)
            print(path_name, ' has been successfully uploaded.')
        else:
            print(path_name, ' can not be upload, please check.')


if __name__ == "__main__":
    tagurl = "http://44.213.48.82:11181/product/skc/batchTagSkc"
    tagdir = '/root/autodl-tmp/tmp_res/tag_res/output/20231204_1544/tag_res'
    upload(tagurl, tagdir)
    # all_tag_res = os.listdir(tagdir)
    # for tag_save_time in  all_tag_res:
    #     # print("tag_res",tag_res)
    #     save_date = tag_save_time.split("_")[0]
    #     save_time = tag_save_time.split("_")[1]
    #     if save_time in ["0617","0630","0237","0249","0214","0151","0203","2309","2321"]:
    #     # if tag_save_time after 1845,the upload
    #     # if (save_date =="20231126") and (save_time <= "0948" ):
    #         tag_res_path = os.path.join(tagdir,tag_save_time,"tag_res.json")
    #         print("tag_res_path",tag_res_path)
    #         with open(tag_res_path,"r") as f:
    #             tag_res = json.load(f)
    #         ifpost = upload_tag_res(tagurl,tag_res)
    #         print(f'save {ifpost} to upload {tag_res_path}')
    # ifpost = upload_tag_res(tagurl,tag_res)
    # print(f'save {ifpost} to upload {tag_res_path}')
