import multiprocessing
import argparse
import json
import multiprocessing
import os
import time
import traceback
import uuid

import pandas as pd
import torch

# from loguru import logger
from log_config import get_logger

logger = get_logger()

from tag_service import Service
from utils import download_data, reload
from get_info_from_url import upload_tag_res, get_products, get_total_num
import queue

global RES_t
RES = pd.DataFrame()
RES_t = pd.DataFrame()
# global MAXQSIZE
MAXQSIZE = 0

TAG_RES = queue.Queue()


def data_input(data_path, output_dir, input_data_q, get_product_skc_interface=None, spu_path=None):
    """
    get some data from data_path, use input_data_q to communicate with other process
    args:
        data_path: the interface to get data
        output_dir: output root
        input_data_q: save data to communicate with other process
        get_product_skc_interface: information of the interface while getting product skc
    return:

    """
    try:
        global MAXQSIZE
        # if data_path is xlsx or csv，use pandas to read,if data_path is url ,use requests to read
        if data_path.endswith('xlsx') or data_path.endswith('csv'):
            datares = pd.read_csv(data_path, encoding='latin-1', skipinitialspace=True, dtype=str).dropna(how='all')
            logger.info(f'datares.shape {datares.shape}', 'datares.columns', datares.columns.tolist())
            datares.rename(columns={'ï»¿id': 'id'}, inplace=True)
            datares['id'] = datares['id'].astype(str)
            datares = datares[['id', 'title', 'imgs1', 'desc1', 'features1', 'link1']]
            datares.rename(columns={'imgs1': 'imgs', 'desc1': 'desc', 'features1': 'features', 'link1': 'link'},
                           inplace=True)
            # datares = datares[['id','title_x','imgs','desc','features','link']]
            # datares = datares.iloc[0:3]
            for index, row in datares.iterrows():
                outputdir = os.path.join(output_dir, f'{str(row["id"])}_{time.strftime("%H_%M_%S")}')
                os.makedirs(outputdir)
                product_info = []
                imgs = []
                product_id = row['id']
                # dowload  imgs
                if row['imgs'] == '':
                    imgs = []
                elif type(row['imgs']) == str:
                    imgs = json.loads(row['imgs'])[0:5]
                elif type(row['imgs']) == list:
                    imgs = row['imgs']
                imgs = download_data(imgs, outputdir)
                if len(imgs) == 0:
                    logger.info(f'can not get img url :which product is {product_id}:{row["link"]}')
                product_info = row[['title', 'desc', 'features', 'link']].dropna().to_dict()
                input_data = {"id": product_id, "imgs": outputdir, "info": product_info, "index": index}

                logger.info(
                    '-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')
                logger.info(f'input_data {input_data}')
                logger.info(
                    '-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')

                input_data_q.put(input_data)
                MAXQSIZE += 1

        elif data_path.startswith('http'):
            product_url = data_path
            params = get_product_skc_interface["params"]
            device = get_product_skc_interface["device"]

            from tmp_test_xlsx import read_xlx
            to_search_ids = read_xlx(spu_path)
            logger.info(f'total spu: {len(to_search_ids)}')
            chunck_size = 10
            to_search_lists = [to_search_ids[i:i + chunck_size] for i in range(0, len(to_search_ids), chunck_size)]
            for to_search_list in to_search_lists:  # 一次取chunck_size种款式进行爬取数据
                to_search_list = to_search_list if type(to_search_list) == list else [to_search_list]
                totalnum = get_total_num(product_url, to_search_list)  # 读取chunck_size种款式的所有SKC
                if totalnum == 0:
                    logger.warning(f'failed to get info from {to_search_list}')
                logger.info(f'begin to cope with spu: {to_search_list}')
                logger.info(f'get total skc number: {totalnum}')
                toadd_infos = get_product_skc_interface["infos"]
                params = get_product_skc_interface["params"]
                params["pageSize"] = 100  # todo ？
                params["pageNo"] = 0
                pronum = 0
                while pronum < totalnum:
                    # 得到product的信息
                    product_infos, params, pronum, total_skc = get_products(product_url, params, device, to_search_list)
                    logger.info(f'get useful product num is {pronum} from {str(params)})')
                    # print('product_infos',product_infos)

                    if type(product_infos) != list or len(product_infos) <= 0:
                        continue
                    for product_info in product_infos:  # cope each product
                        # download img and cope product info to input format
                        input_data, imgs = pre_process(product_info, output_dir, toadd_infos)
                        if input_data == {}:
                            logger.info(f'tagcount >=0,do not tag, {product_info["id"]}:{product_info}')
                        elif len(imgs) == 0:
                            logger.info(f'can not get img url :which product is {product_info["id"]}:{product_info}')
                        if input_data != {}:
                            logger.info(
                                '-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
                            logger.info(f'input_data {input_data}')
                            logger.info(
                                '-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')

                            input_data_q.put(input_data)
                            # global MAXQSIZE
                            MAXQSIZE += 1
                    pronum += pronum

                # time.sleep(10)

    except Exception as e:
        logger.error(f'{traceback}')
        logger.error(f'e {e}')
        logger.error(f'{e.__traceback__.tb_frame.f_globals["__file__"]}')
        logger.error(f'{e.__traceback__.tb_lineno}')
        # raise e
        # return False, str(e)


def auto_label(question_json, queueimg, version, resqt, resq, params=None, res_dir=None, ):
    """
    args:
        question_json: question
        queueimg: the queue where data saved while getting
        version: tag url， different url present different version
        resqt:
        resq:
        params:
        res_dir:

    """
    canget = True
    servicetag = Service(question_json)
    global TAG_RES
    try:
        tagres_outdir = os.path.join(res_dir, 'tag_res')
        os.makedirs(tagres_outdir)
        while canget:
            # todo get quene and  service.tag_main
            # get qsize
            qsize = queueimg.qsize()
            if qsize == 0:
                message = 'no message'
                ifpost, num, all_left_tagres, res, message = handle_tag_res(resq, 0, tagres_outdir, if_min=False)
                logger.info(f'if post {ifpost},save all {num} tag_res to {all_left_tagres} ,messgae( {message})')
                # time.sleep(300)

            product_info = queueimg.get(block=True, timeout=300)

            if product_info is None:
                logger.info('product info is None')
                canget = False
                return False, 'there is no product in queue'
            else:
                logger.info(f'product info: {product_info}')

            tag_perp = []

            # use llova generate tag answer
            tag_perp = servicetag.tag_main(product_info['imgs'], product_info['info'], version)

            logger.info(
                '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
            logger.info(f'product info: {product_info}')
            logger.info(f'predict final result: {tag_perp}')
            logger.info(
                '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')

            if type(tag_perp) == str:
                return False, tag_perp
            # if tag_perp == []:
            #     return False, tag_perp
            # phase all tag and push it into communication queue
            if tag_perp != []:
                result_df = pd.DataFrame(tag_perp)
                result_df_t = result_df.T
                result_df_t.columns = result_df_t.iloc[0]
                result_df_t = result_df_t.drop(result_df_t.index[0])
                # result_df_t.insert(0,'idindex',imgsinfo['index'])
                # result_df_t.insert(1,"product_url",imgsinfo['info']['link'])
                result_df_t.insert(1, 'product_id', str(product_info['id']))
                global RES
                resqt.put(result_df_t)

            # tag_res = params["format"]
            tag_res = {
                "firstCategory": "",
                "skcId": "",
                "subCategory": "",
                "tags": {}
            }
            if type(tag_res) != dict:
                logger.info('tag_res is not dict,which type is {type(tag_res)}')
                tag_res = tag_res = {"firstCategory": "", "skcId": "", "subCategory": "", "tags": {}}
            tag_res["skcId"] = product_info['id']
            # tag_res["firstCategory"] =tag_perp
            if tag_perp != []:
                logger.info(f'not empty tag_perp {tag_perp}')
                for each_tagres in tag_perp:
                    if each_tagres['label'] == 'first category':
                        tag_res["firstCategory"] = each_tagres['value']
                    elif each_tagres['label'] == 'subcategory':
                        tag_res["subCategory"] = each_tagres['value']
                    else:
                        tag_res["tags"][each_tagres['label']] = each_tagres['value'] if type(
                            each_tagres['value']) == list else [each_tagres['value']]

                logger.info('=========================================================')
                logger.info(f'tag_res {tag_res}')
                logger.info('=========================================================')
                resq.put(tag_res)
            message = 'no message'
            ifpost, savenum, tmp_tagres_dir, resq, message = handle_tag_res(resq, maxlimit=20, outdir=tagres_outdir,
                                                                            if_min=True)
            logger.info(f'ifpost {ifpost},save {savenum} tag_res to {tmp_tagres_dir},messgae( {message})')
            # TODO:分批读取和传回结果

            # resq.put(result_df)
        # return True, result_df

    except Exception as e:
        logger.error(f'e {e}')
        logger.info(f'{e.__traceback__.tb_frame.f_globals["__file__"]}')
        logger.info(f'{e.__traceback__.tb_lineno}')


def handle_tag_res(resq, maxlimit, outdir, if_min=False):
    tmp_tagres_dir = ''

    ifpost = False
    # global resq
    count = 0
    topost = []
    message = 'no message to post'

    if if_min:
        if resq.qsize() >= maxlimit:
            count = maxlimit
    else:
        count = resq.qsize()

    logger.info('the number of q queue: ', resq.qsize(), '.  upload data number:', count)
    if count != 0:
        for j in range(count):
            element = resq.get()
            # print('element',element)
            if element['tags'] != {}:
                topost.append(element)

        urlfile = '/root/autodl-tmp/autotagging/taggingpipeline/mainpipeline/configs/product_urls.json'

        tagurl = reload(urlfile)['tagurl']
        # print('topost',topost)
        topost = json.loads(json.dumps(topost))

        ifpost, message = upload_tag_res(tagurl, topost)
        # if not ifpost:
        #     for element in topost:
        #         resq.put(element)

        tmp_tagres_dir = os.path.join(outdir, f'{time.strftime("%Y%m%d_%H%M")}_{uuid.uuid1()}')
        os.makedirs(tmp_tagres_dir)

        # save topost to file :
        with open(os.path.join(tmp_tagres_dir, 'tag_res.json'), 'w+') as f:
            json.dump(topost, f)

    return ifpost, len(topost), tmp_tagres_dir, resq, message


def pre_process(product_info, output_dir, infos):
    product_id = product_info['id']
    imgs = []

    # if product_info.get("tagCount"):
    # if product_info["tagCount"]>=1:
    #     return {},imgs
    outputdir = os.path.join(output_dir, f'{product_id}')
    os.makedirs(outputdir)

    # download imgs

    if product_info.get('imgs'):
        p_imgs = product_info['imgs']

        if p_imgs == '':
            imgs = []
        elif type(p_imgs) == str:
            imgs = json.loads(p_imgs)[0:5]
        elif type(p_imgs) == list:
            imgs = p_imgs
        imgs = download_data(imgs, outputdir)
    # if  len(imgs) == 0:
    #     logger.info(f'can not get img url :which product is {product_id}:{product_info["link"]}')

    info = {}
    # print('params["infos"]',infos)
    for info_name in infos:
        # print('info_name',info_name)
        if product_info.get(info_name):
            info[info_name] = product_info[info_name]
    input_data = {"id": product_id, "imgs": outputdir, "info": info}

    return input_data, imgs


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    # # parser.add_argument('--url', type=str, default='/root/autodl-tmp/autotagging/taggingpipeline/data/data_1/datav1_4.csv', help='url')
    # parser.add_argument('--url', type=str, default='http://44.213.48.82:11181/product/skc/pageSkc', help='url')
    # parser.add_argument('--res_dir', type=str, default='/root/autodl-tmp/tmp_res/tag_res/output', help='res_dir')
    # parser.add_argument('--questionjson', type=str, default='/root/autodl-tmp/autotagging/taggingpipeline/mainpipeline/prompts/quesion.json', help='question.json path')
    # # parser.add_argument('--version', type=str, default='http://44.213.48.82:11181/category/getTagsConfig', help='question.json path')
    # parser.add_argument('--version', type=str, default='20131114_cl', help='question.json path')

    parser.add_argument('--cfgpath', type=str, default='/root/autodl-tmp/autotagging/start_tag.json',
                        help='question.json path')
    parser.add_argument('--spu_path', type=str,
                        default='/root/autodl-tmp/autotagging/data_utils/spu/SPU_131204.xlsx')

    args = parser.parse_args()
    torch.multiprocessing.set_start_method('spawn')

    # load cfgpath
    with open(args.cfgpath, 'r') as f:
        cfg = json.load(f)
    f.close()
    logger.info(f'spu path: {args.spu_path}')

    res_dir = cfg['res_dir']
    gettag_url_interface = cfg['gettag_url']
    get_product_skc_interface = cfg['get_product_skc']
    product_source = cfg['get_product_skc']["product_url"]
    questionjson = cfg['questionjson']
    upload_tag_param = cfg['upload_tags']

    if not os.path.exists(res_dir):
        os.makedirs(res_dir)
    if os.path.exists(product_source):
        file_name = product_source.split('/')[-1].split('.')[0]
        res_dir = os.path.join(res_dir, f'{file_name}_{time.strftime("%Y%m%d_%H%M")}')
    else:
        res_dir = os.path.join(res_dir, f'{time.strftime("%Y%m%d_%H%M")}')
    os.makedirs(res_dir)

    # make out csv and log json file 
    outcsvpath = os.path.join(res_dir, f'{time.strftime("%Y%m%d_%H%M")}_label_res.csv')

    # 使用multiprocessing.Manager创建一个可以在进程之间共享的队列
    manager = multiprocessing.Manager()
    q = manager.Queue()  # 保存爬取到到数据
    resq = manager.Queue()  # 保存解析的结果
    resqt = manager.Queue()  # save my own result

    # 创建并启动两个进程
    imgs_res_dir = os.path.join(res_dir, 'imgs')
    os.makedirs(imgs_res_dir)
    logger.info(f'img save root: {imgs_res_dir}')
    logger.info('====================================START PROCESS====================================')
    p1 = multiprocessing.Process(target=data_input, args=(product_source, imgs_res_dir, q, get_product_skc_interface,
                                                          args.spu_path))
    p2 = multiprocessing.Process(target=auto_label,
                                 args=(questionjson, q, gettag_url_interface, resqt, resq, upload_tag_param, res_dir))

    p1.start()
    time.sleep(100)
    p2.start()
    # 
    p1.join()
    p2.join()

    logger.info('====================================END PROCESS====================================')

    # creat out csv file
    print('outcsvpath', outcsvpath)

    open(outcsvpath, 'a').close()
    print('result.shape', RES.shape)

    # if not RES.empty:
    #     RES.to_csv(outcsvpath,index=False)
    # print('~~~~~~~~~~~~~~~~~~~~~~max input data size ',MAXQSIZE,'~~~~~~~~~~~~~~~~~~~~~~')
    # print('~~~~~~~~~~~~~~~~~~~~~~resq.qsize()',resq.qsize(),'~~~~~~~~~~~~~~~~~~~~~~')
    logger.info(f'max input data size {MAXQSIZE}')
    logger.info(f'resq.qsize() {resq.qsize()}')

    # while  resq.qsize() >0:
    #     tmpres = resq.get(block=True, timeout=240)
    #     RES_t = pd.concat([RES_t.astype(str),tmpres.astype(str)],axis=0,ignore_index=True)
    #     print('RES_t.shape',RES_t.shape)
    #     # print('RES_t',RES_t)
    #     logger.info(f'RES_t.shape {RES_t.shape}')
    # RES_t.to_csv(outcsvpath,index=False)

    print('RES.shape', RES.shape)

    label_res_t = outcsvpath.replace('label_res', 'label_res_t')
    open(label_res_t, 'a').close()

    while resqt.qsize() > 0:
        tmpres = resqt.get(block=True, timeout=240)
        RES = pd.concat([RES.astype(str), tmpres.astype(str)], axis=0, ignore_index=True)
        # print('RES_t',RES_t)
        logger.info(f'RES.shape {RES.shape}')

    RES.to_csv(label_res_t, index=False)

    # if not result_t.empty:
    #     result_t.to_csv('/root/autodl-tmp/autotagging/taggingpipeline/output/data_1/tt.csv')
    logger.info('====================================END LABEL====================================')
