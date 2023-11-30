import imghdr
import json
import os
import re

import pandas as pd
import requests
from PIL import Image

from get_info_from_url import get_tags


def load_config(version, csvpath, versiondir='/root/autodl-tmp/autotagging/taggingpipeline/mainpipeline/configs'):
    # load csv file
    # csvpath: csv file path
    # return: pd data
    reslist = {}
    versions = os.listdir(versiondir)
    if version not in versions:
        if version.startswith('http') or version.startswith('https'):
            category, labels = get_tags(version)
            if csvpath == 'category':
                reslist = category
            elif csvpath == 'label':
                reslist = labels
        else:
            return 'version not in versions'
    else:

        versionfiles = os.listdir(os.path.join(versiondir, version))
        if versionfiles == []:
            return 'versionfiles is empty'

        if f'{csvpath}.json' in versionfiles:
            cfgpath = os.path.join(versiondir, version, f'{csvpath}.json')
            reslist = load_cfg_json(cfgpath)

        elif f'{csvpath}.csv' in versionfiles:
            cfgpath = os.path.join(versiondir, version, f'{csvpath}.csv')
            reslist = load_cfg_csv(cfgpath)

            # save reslist to json file
            cfgpath = os.path.join(versiondir, version, f'{csvpath}.json')
            with open(cfgpath, 'w') as f:
                json.dump(reslist, f)
            f.close()

    return reslist


def load_cfg_json(jsonpath):
    with open(jsonpath, 'r') as f:
        reslist = json.load(f)
    f.close()

    return reslist


def load_cfg_csv(csvpath):
    reslist = {}
    print('csvpath', csvpath)
    pddata = pd.read_csv(csvpath, skipinitialspace=True)
    colsname = pddata.columns.tolist()
    print('colsname', colsname)

    cols = 0
    curcols = colsname[cols]
    categorylist1 = pddata[curcols].tolist()
    categorylistres = only_one_ele(categorylist1, [])
    print('categorylistresss', categorylistres)

    # if 'category' in csvpath:
    #     # load category csv file
    #     reslist.update({'first category':categorylistres})
    #     # cols = 1

    #     for cols in range(len(colsname)-1):

    #         curcols = colsname[cols]
    #         print('cols',cols,'curcols',curcols)
    #         reslist.update({curcols:[]})
    #         categorys = list(set(pddata[colsname[cols]].dropna().tolist()))
    #         for category in categorys:
    #             subtaglist = get_corr(pddata,colsname[cols],colsname[cols+1],category)
    #             if subtaglist != []:
    #                 reslist[curcols].append({category:subtaglist})
    if 'category' in csvpath:
        # load category csv file
        reslist.update({'first category': categorylistres})
        # cols = 1

        for cols in range(len(colsname) - 1):
            curcols = colsname[cols]
            print('cols', cols, 'curcols', curcols)
            if cols == 0:
                reslist[curcols] == categorylistres
            else:
                reslist.update({curcols: []})
                categorys = list(set(pddata[colsname[cols - 1]].dropna().tolist()))
                for category in categorys:
                    subtaglist = get_corr(pddata, colsname[cols - 1], colsname[cols], category)
                    if subtaglist != []:
                        reslist[curcols].append({category: subtaglist})
        print('reslist', reslist)

    if 'label' in csvpath:
        reslist = {'type': []}
        # load label csv file
        print('categorylistres', categorylistres)
        # tt_categorylistres = list(set([ i.s]))
        # handle 'all' and 'ALL'
        # print('pddata[curcols]',pddata[curcols].tolist())
        data_all = pddata[pddata[curcols].isin(['all', 'ALL'])]
        # print('data_all',data_all)
        # get all labels
        labels_all = list(set(data_all[colsname[cols + 1]].tolist()))
        # print('labels_all',labels_all)
        ALL_label_option = []
        for label in labels_all:
            ALL_label_option.append(
                {label: data_all[data_all[colsname[cols + 1]] == label][colsname[cols + 2]].dropna().tolist()})
        # print('ALL_label_option',ALL_label_option)

        # # get each label option
        # cates_all = categorylistres
        # # cates_all.extend(cate.split(',') for cate in categorylistres)
        # # remove 'all' and 'ALL'
        # cates_all.remove('ALL')
        # cates_all = list(set(cates_all))

        if 'ALL' in categorylistres:
            categorylistres.remove('ALL')
        # print('categorylistres2',categorylistres)

        # remove 'all' and 'ALL' from pddata
        pddata = pddata[~pddata[curcols].isin(['all', 'ALL'])]

        # print('alltops',alltops)
        # print(only_one_ele(pddata[curcols].tolist(),[]))
        print('---------------------------------------------------------')

        # pddata[curcols]=pddata[curcols].map(lambda x:x.strip().split(','))

        pddata[curcols] = pddata[curcols].map(lambda x: only_one_ele(x.strip().split(','), []))

        # print('ddddd',pddata[curcols])

        pddata = pddata.explode(curcols)

        # colsname = only_one_ele(pddata.columns.tolist(),[])
        print('------------------')
        curcols = colsname[cols]

        categorylistres = only_one_ele(pddata[curcols].tolist(), [])
        # print('categorylist1',categorylistres)

        reslist.update({'top category': categorylistres})

        for topcategory in categorylistres:
            tmpres = {topcategory: []}

            tmpdf = pddata[pddata[colsname[cols]] == topcategory]
            subtaglist = get_corr(pddata, colsname[cols], colsname[cols + 1], topcategory)
            tmpdf = pddata[pddata[colsname[cols]] == topcategory]
            if subtaglist != []:
                for subtag in subtaglist:
                    sub_subtag = get_corr(tmpdf, colsname[cols + 1], colsname[cols + 2], subtag)
                    if sub_subtag != []:
                        tmpres[topcategory].append({subtag: sub_subtag})

            tmpres[topcategory].extend(ALL_label_option)

            reslist['type'].append(tmpres)

    # if 'label' in csvpath:
    #     reslist= {'type':[]}
    #     # load label csv file
    #     print('categorylistres',categorylistres)
    #     # tt_categorylistres = list(set([ i.s]))
    #     if 'all' in categorylistres :            
    #         alltops = str(categorylistres.remove('all')).replace('[','').replace(']','')
    #         pddata = pddata.replace({curcols:{'all':alltops}})
    #     if 'ALL' in categorylistres:   
    #         # alltops = str(categorylistres.remove('ALL')).replace('[','').replace(']','')
    #         categorylistres.remove('ALL')
    #         alltops = ",".join(categorylistres)
    #         pddata = pddata.replace({curcols:{'ALL':alltops}})

    #     print('---------------------------------------------------------')

    #     print('alltops',alltops)
    #     print(only_one_ele(pddata[curcols].tolist(),[]))
    #     print('---------------------------------------------------------')

    #     pddata[curcols]=pddata[curcols].map(lambda x:x.strip().split(','))
    #     pddata=pddata.explode(curcols)

    #     # colsname = only_one_ele(pddata.columns.tolist(),[])
    #     print('------------------')
    #     curcols = colsname[cols]

    #     categorylistres = only_one_ele(pddata[curcols].tolist(),[])
    #     print('categorylist1',categorylistres)

    #     reslist.update({'top category':categorylistres})

    #     for topcategory in categorylistres:
    #         tmpres = {topcategory:[]}

    #         tmpdf = pddata[pddata[colsname[cols]] == topcategory]
    #         subtaglist = get_corr(pddata,colsname[cols],colsname[cols+1],topcategory)
    #         tmpdf = pddata[pddata[colsname[cols]] == topcategory]
    #         if subtaglist != []:
    #             for subtag in subtaglist:
    #                 sub_subtag = get_corr(tmpdf,colsname[cols+1],colsname[cols+2],subtag)
    #                 if sub_subtag != []:
    #                     tmpres[topcategory].append({subtag:sub_subtag})

    #         reslist['type'].append(tmpres)

    return reslist


def get_corr(df, colkey, colvalue, target_key):
    reslist = df[df[colkey] == target_key][colvalue].dropna().tolist()
    reslist = only_one_ele(reslist, [])

    return reslist


def only_one_ele(inputlist, outputlist):
    outputlist = []
    for ele in inputlist:
        if type(ele) == str:
            tmpres = ele.strip().split(',')
            outputlist.extend([i.strip() for i in tmpres])
        else:
            tmpres = ele
            outputlist.append(tmpres)
    outputlist = list(set(outputlist))
    return outputlist


def download_data(imgurl, outputdir):
    # download imgurl to outputdir
    imgs = []
    for img in imgurl:
        if img and type(img) == str:
            # if type(img) == str :
            imgname = img.strip(" "" ").split('/')[-1].split('.')[0] + '.jpg'
            imgpath = os.path.join(outputdir, imgname)
            if not os.path.exists(imgpath):
                try:
                    response = requests.get(img, stream=True, timeout=60)
                    # response.raise_for_status()
                    if response.status_code == 200:
                        with open(imgpath, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=1000000):
                                f.write(chunk)
                            # f.write(requests.get(img,timeout=10).iter_content)
                        f.close()
                        if check_img(imgpath):
                            imgs.append(imgpath)
                            # print(f'download success to {imgpath}')
                        # imgs.append(imgpath)
                except Exception as e:
                    print(f'download error: {e}')
                    continue
    return imgs


def check_img(imgpath):
    is_valid = False
    ifimg = imghdr.what(imgpath, h=None)

    if ifimg is not None:
        try:
            pilimg = Image.open(imgpath)
            pilres = pilimg.load()
            if pilres is not None:
                is_valid = True
        except:
            is_valid = False

    return is_valid


def load_image(image_file):
    if image_file.startswith('http') or image_file.startswith('https'):
        response = requests.get(image_file)
        image = Image.open(BytesIO(response.content)).convert('RGB')
    else:
        image = Image.open(image_file).convert('RGB')
    return image


def find_element_in_list(element: str, lst: list) -> str:
    # 将元素转换为小写
    lowercase_element = element.lower().strip("'").strip('"').strip('.')
    # 遍历列表
    for item in lst:
        # print('item',item.lower(),'lowercase_element',lowercase_element)
        if lowercase_element == item.lower():
            return item  # 如果找到了，返回原始的元素（不改变大小写）
    return None  # 如果没有找到，返回None


def res_post_process(res):
    # res: list
    # return: list
    r = '[!"#$%&\'*+,.:;<=>?@[\\]^_`{|}~\n]+'
    res = re.sub(r, ' ', str(res))
    res = res.replace('</s>', '')
    return res


def find_eles_in_list(element: str, lst: list) -> str:
    res = []
    # 将元素转换为小写
    lowercase_element = element.lower().strip("'").strip('"').strip('.')
    # 遍历列表
    for item in lst:
        if lowercase_element in item.lower():
            res.append(item)
    if res != []:
        res = list(set(res))
        res = [i for i in res if i != '']
        res = ','.join(res)
    else:
        res = None
    return res


def reload(urlfile):
    # check if urlfile is changed 
    # urlfile: url file path
    # return: True or False
    is_reload = False
    if os.path.exists(urlfile):
        with open(urlfile, 'r') as f:
            url = json.load(f)

    return url
