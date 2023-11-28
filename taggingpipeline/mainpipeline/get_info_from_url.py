import requests
import json

def get_tags(tagurl):
    category = {"first category":[],"subcategory":[]}
    labels = {"type":[],"top key":[]}
    selectType = {}
    cate_id_name = {}
    puc_tags= []

    print("tagurl",tagurl)
    response = requests.get(tagurl, stream=True,timeout=120)
    print("response.status_code",response.status_code)
    
    if response.status_code == 200:
        datas = response.json()

        categories = datas["data"]["categories"]
        tags = datas["data"]["tags"]
        categoryTagsMap = datas["data"]["categoryTagsMap"]

        # get cates 
        for cate in categories:
            options = []
            category["first category"].append(cate["enName"])
            if  cate.get("id") and cate.get("enName"):
                cate_id_name[cate["id"]] = cate["enName"]
            if cate.get("children"):
                for subcate in cate["children"]:
                    if subcate.get("id") and subcate.get("enName"):
                        cate_id_name[subcate["id"]] = subcate["enName"]
                    options.append(subcate["enName"])
            else:
                options.append(cate["enName"])
            category["subcategory"].append({cate["enName"]:options})
        tags = datas["data"]["tags"]
        print("cate_id_name",cate_id_name)

        # get tags
        for tag in tags:
            # print("tag",tag,"tag keys",tag.keys())   
            options =[]
            options = [i["value"] for  i in tag["items"]] if tag.get("items") else []
            # label = {tag["value"]:options}
            # labels["type"].append(label)
            puc_tags.append({tag["value"]:options})
            selectType[tag["value"]]=tag["selectType"]
        # print ("labels",labels)

        # get categoryTagsMap
        # labels ={"type":[],"top key":[]}
       
        for cate_id,value in categoryTagsMap.items():
            label = {}
            # label[cate_id]=[]
            if cate_id in cate_id_name.keys():
                
                catename = cate_id_name[cate_id]
                labels["top key"].append(catename)
                # print("cate_id",cate_id,"catename",catename)
                label[catename]=[]
                for tag in value:
                    lab = {tag["value"]:list(set([i["value"] for i in tag["items"]]))} 
                    label[catename].append(lab)
            label[catename].extend(puc_tags)
            # print("=========================")
            # print(label)
            labels["type"].append(label)
        # print ("labels",labels)

    # save cates
    with open("/root/autodl-tmp/autotagging/taggingpipeline/test/category.json","w") as f:
        json.dump(category,f)
    # save tags
    with open("/root/autodl-tmp/autotagging/taggingpipeline/test/label.json","w") as f:
        json.dump(labels,f)
    
    return category,labels

def get_products(product_url,params,device,spus=[]):
    total_skc = 0
    pageno = params["pageNo"]
    device_num = device["device_num"]
    device_index = device["device_index"]
    if len(spus)>=1:
        params["spus"]= spus
    else:
        del params["spus"]
    # get pageno by device_num and device_index,eg：device_num=2,device_index=0,then pageno=0，2,4,6,8,10...，if  device_num=3,device_index=1,then pageno=1,4,7,10,13,16...
    # pageno = device_num*pageno+device_index\
    print("params",params,"spus",spus)
    # del params['homepagestatus']
    if pageno == 0:
        params["pageNo"] = device_index
        product_infos,pronum,total_skc = get_product_info(product_url,params)
    else:
        params["pageNo"] = pageno
        product_infos,pronum,total_skc = get_product_info(product_url,params)
    
    # print("prouct_infos",product_infos)
    
    params["pageNo"]= pageno+device_num

    # params["pageNo"] 
    return product_infos,params,pronum,total_skc



def get_product_info(product_url,params):
    product_infos = []
    pronum = 0
    try: 
        headers = {
                    "accept": "*/*",
                    "Content-Type": "application/json"
                }
        print("get_product_info params",params)
        response = requests.post(product_url,json=params,headers=headers)
        if response.status_code == 200:
            # if response.code == 200:
            datas = response.json()
            
            if datas["data"]:
                product_infos =  datas["data"]
                
                
            if datas["total"]:
                total_skc = datas["total"]

            # not_to_tags =[]
            # if len(product_infos)>=1:
            #     for product_info in product_infos:
            #         if product_info.get("tagCount"):
            #             if product_info["tagCount"]>=1:
            #                 not_to_tags.append(product_info)
            
            # if len(not_to_tags)>=1:
            #     for not_to_tag in not_to_tags:
            #         product_infos.remove(not_to_tag)
            
            pronum = len(product_infos)

            
    except Exception as e:
        print("get_tags error",e)
    return product_infos,pronum,total_skc


def get_product_infp(tagurl,pageno,pagesize):
    prouct_infos = []
    try:
        print("tagurl",tagurl)
        # response = requests.get(tagurl)
        request_data = {
                        "pageNo":pageno,
                        "pageSize":pagesize
                        }
        
        headers = {
                    "accept": "*/*",
                    "Content-Type": "application/json"
                }

        print("request_data",request_data)
        response = requests.post(tagurl,json=request_data,headers=headers)
        if response.status_code == 200:
            # if response.code == 200:
            datas = response.json()
            # print("datas",datas)
            if datas["data"]:
                prouct_infos =  datas["data"]
    except Exception as e:
        print("get_tags error",e)
    return prouct_infos

def get_total_num(tagurl,spus=[]):
    prouct_infos = []
    try:
        if len(spus)>=1:
            # request_data = { "pageNo":0,"pageSize":1,"homepagestatus":2,"spus":spus}
            request_data = { "pageNo":0,"pageSize":1,"spus":spus}
        # request_data = { "pageNo":0,"pageSize":1,"homepagestatus":2}
        headers = {"accept": "*/*","Content-Type": "application/json"}
        print("request_data",request_data)
        response = requests.post(tagurl,json=request_data,headers=headers)
        print("response",response)
        if response.status_code == 200:
            # if response.code == 200:
            datas = response.json()
            # print("datas",datas)
            totalnum = datas["total"]

    except Exception as e:
        print("get_tags error",e)
    return totalnum


def upload_tag_res(tagurl,tag_res):
    ifpost = False
    message = 'post but failed'
    try:
        print("tagurl",tagurl)
        # response = requests.get(tagurl)
        headers = {
                    "accept": "*/*",
                    "Content-Type": "application/json"
                }
        # print("tag_res",tag_res)
        print('tah_restah_restah_restah_res',type(tag_res))
        # if  not isinstance(tag_res,list):
        #     tag_res = [tag_res]

        response = requests.post(tagurl,json=tag_res,headers=headers)
    
        print("response",response,response.json())

        if response.status_code == 200:
            
            data = response.json()
            print("data",data)
            message = str(data)
            print("message",data["message"])
            if  data["success"] and data["message"] == "Success.":
                ifpost = True
    except Exception as e:
        print("get_tags error",e)
    return ifpost,message





# if __name__ == "__main__":
# #     tagurl = "http://44.213.48.82:11181/category/getTagsConfig"
# #     imgs = get_tags(tagurl)
# #     producturl = "http://44.213.48.82:11181/product/skc/pageSkc"
# #     pageno=1
# #     pagesize=3

# #    imgs =  get_product_infp(producturl,pageno,pagesize)
# #     print(imgs)
#     import os
#     tagurl = "http://44.213.48.82:11181/product/skc/batchTagSkc"
#     tagdir  = '/root/autodl-tmp/tmp_res/tag_res/output/20231123_1429/tag_res'
#     all_tag_res = os.listdir(tagdir)
#     for tag_res in  all_tag_res:
#         print("tag_res",tag_res)
#         tag_save_time = tag_res.split("_")[1]
#         # if tag_save_time after 1845,the upload
#         if tag_save_time >= "1530":
#             tag_res_path = os.path.join(tagdir,tag_res,"tag_res.json")
#             with open(tag_res_path,"r") as f:
#                 tag_res = json.load(f)
#             ifpost = upload_tag_res(tagurl,tag_res)
#             print(f'save {ifpost} to upload {tag_res_path}')
    # a = [
    #     {"firstCategory": "Tops", 
    #     "skcId": "1722859538946555906", 
    #     "subCategory": "T-shirt",
    #     "tags": {"Waistband": ["Elastic Waist"], "Rise": ["High"], "Length": ["Ankle-length"], "Waist": ["Fitted"], "Back": ["Open"], "Design": ["Jogger"], "Color": ["Blue"], "Saturation": ["Vivid"], "Brightness": ["Light"], "Material": ["Organic"], "Pattern": ["Floral"], "Trends": ["Cottagecore"], "Process": ["Tie dyeing"], "Occasion": ["Casual Day Out"], "Location": ["City/Urban"], "Style": [" "], "Season": ["Summer"], "Fit": ["Relaxed"], "Event": [" "], "Neckline": ["Turtleneck"], "Shoulder": ["Off-the-Shoulder"], "Collar": ["Funnel Collar"], "Sleeve Length": ["Long"], "Cuff": ["Ribbed"], "Sleeve Shape": ["Tapered Sleeve"], "Cut": ["Off-the-Shoulder"]}},
    #     {"firstCategory": "Set", 
    #     "skcId": "1722859538946555907", 
    #     "subCategory": "Pants Set",
    #     "tags": {"Waistband": ["Elastic Waist"], "Rise": ["High"], "Length": ["Ankle-length"], "Waist": ["Fitted"], "Back": ["Open"], "Design": ["Jogger"], "Color": ["Blue"], "Saturation": ["Vivid"], "Brightness": ["Light"], "Material": ["Organic"], "Pattern": ["Floral"], "Trends": ["Gender-fluid"], "Process": ["Raw Edge"], "Occasion": ["Casual Day Out"], "Location": ["City/Urban"], "Style": [" "], "Season": ["Summer"], "Fit": ["Relaxed"], "Event": [" "], "Neckline": ["Turtleneck"], "Shoulder": ["Off-the-Shoulder"], "Collar": ["Funnel Collar"], "Sleeve Length": ["Long"], "Cuff": ["Ribbed"], "Sleeve Shape": ["Tapered Sleeve"], "Cut": ["Off-the-Shoulder"]}}
    #     ]

    # upload_tag_res(tagurl,a)

    # a = [
    #     {"firstCategory": "Tops", 
    #     "skcId": "1722859538946555906", 
    #     "subCategory": "T-shirt",
    #     "tags": {"Waistband": ["Elastic Waist"], "Rise": ["High"], "Length": ["Ankle-length"], "Waist": ["Fitted"], "Back": ["Open"], "Design": ["Jogger"], "Color": ["Blue"], "Saturation": ["Vivid"], "Brightness": ["Light"], "Material": ["Organic"], "Pattern": ["Floral"], "Trends": ["Cottagecore"], "Process": ["Tie dyeing"], "Occasion": ["Casual Day Out"], "Location": ["City/Urban"], "Style": [" "], "Season": ["Summer"], "Fit": ["Relaxed"], "Event": [" "], "Neckline": ["Turtleneck"], "Shoulder": ["Off-the-Shoulder"], "Collar": ["Funnel Collar"], "Sleeve Length": ["Long"], "Cuff": ["Ribbed"], "Sleeve Shape": ["Tapered Sleeve"], "Cut": ["Off-the-Shoulder"]}
    #     },
    #     {"firstCategory": "Set", 
    #     "skcId": "1722859538946555907", 
    #     "subCategory": "Pants Set",
    #     "tags": {"Waistband": ["Elastic Waist"], "Rise": ["High"], "Length": ["Ankle-length"], "Waist": ["Fitted"], "Back": ["Open"], "Design": ["Jogger"], "Color": ["Blue"], "Saturation": ["Vivid"], "Brightness": ["Light"], "Material": ["Organic"], "Pattern": ["Floral"], "Trends": ["Gender-fluid"], "Process": ["Raw Edge"], "Occasion": ["Casual Day Out"], "Location": ["City/Urban"], "Style": [" "], "Season": ["Summer"], "Fit": ["Relaxed"], "Event": [" "], "Neckline": ["Turtleneck"], "Shoulder": ["Off-the-Shoulder"], "Collar": ["Funnel Collar"], "Sleeve Length": ["Long"], "Cuff": ["Ribbed"], "Sleeve Shape": ["Tapered Sleeve"], "Cut": ["Off-the-Shoulder"]}
    #     }
    #     ]

    # b = [
    #     {"firstCategory": "Bottoms", 
    #      "skcId": "1722159535424921601",
    #        "subCategory": "Pants",
    #          "tags": {"Waistband": ["Elastic Waist"], "Rise": ["High"], "Length": ["Full-length"], "Waist": ["Corseted"], "Back": ["Regular"], "Design": ["Jogger"], "Color": ["Blue"], "Saturation": ["Vivid"], "Brightness": ["Light"], "Material": ["Viscose/Rayon"], "Pattern": ["Floral"], "Trends": ["Cottagecore"], "Process": ["Tie dyeing"], "Occasion": ["Vacations/Travel"], "Location": ["Beach"], "Style": [" "], "Season": ["Summer"], "Fit": ["Regular"], "Event": ["Summer New Arrival"]}
    #     },
    #     {"firstCategory": "Dresses",
    #       "skcId": "1722160731522981890", 
    #       "subCategory": "Midi Dresses", 
    #       "tags": {"Waistband": ["Elastic Waist"], "Rise": ["High"], "Length": [" "], "Waist": ["Fitted"], "Back": ["Regular"], "Design": ["Jogger"], "Color": ["Blue"], "Saturation": ["Vivid"], "Brightness": ["Light"], "Material": ["Cotton"], "Pattern": ["Floral"], "Trends": ["Cottagecore"], "Process": ["Embroidery"], "Occasion": ["Weddings"], "Location": ["City/Urban"], "Style": ["Classic"], "Season": ["Winter"], "Fit": ["Regular"], "Event": [" "], "Neckline": ["Crew Neck"], "Shoulder": [" "], "Collar": ["Notched Collar"], "Sleeve Length": ["Sleeveless"], "Cuff": ["Elasticized cuffs"], "Sleeve Shape": ["Ruffle sleeves"]}
    #       },
    #     {"firstCategory": "Tops", 
    #      "skcId": "1722859538946555905",
    #        "subCategory": "T-shirt", 
    #        "tags": {"Waistband": ["Elastic Waist"], "Rise": ["High"], "Length": ["Ankle Length"], "Waist": ["Fitted"], "Back": ["Open"], "Design": ["Jogger"], "Color": ["Blue"], "Saturation": ["Vivid"], "Brightness": ["Light"], "Material": ["Organic"], "Pattern": ["Floral"], "Trends": ["Cottagecore"], "Process": ["Tie dyeing"], "Occasion": ["Casual Day Out"], "Location": ["City/Urban"], "Style": [" "], "Season": ["Summer"], "Fit": ["Relaxed"], "Event": ["New Year"], "Neckline": ["Turtleneck"], "Shoulder": ["Off-the-Shoulder"], "Collar": ["Funnel Collar"], "Sleeve Length": ["Long"], "Cuff": ["Ribbed"], "Sleeve Shape": ["Tapered Sleeve"], "Cut": ["Off-the-Shoulder"]}
    #        }
    #         ]
    # print(upload_tag_res(tagurl,b))

    #  ["larelaxed_8115204554981", "faithfullthebrand_6736691789888", "hillhousehome_7136205307947"]