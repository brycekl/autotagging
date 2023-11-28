import os
import requests
import multiprocessing
import argparse 

import json 
import copy
import os 
import requests
from queue import Queue
import pandas as pd
import time
import torch
# from loguru import logger
from log_config import get_logger
import traceback

logger = get_logger()

# add logger 
# logdir = '/root/autodl-tmp/autotagging/taggingpipeline/logs'
# logger.add(os.path.join(args.res_dir,'log.log'), rotation="500 MB",format="[{time:HH:mm:ss}] {level} - {message}")

 

from tagging import InitQwen
from tag_service import Service
from  get_data import read_database
from utils  import download_data



   
global RES_t
RES  = pd.DataFrame()
RES_t = pd.DataFrame()
# global MAXQSIZE
MAXQSIZE =0


def data_input(data_path, output_dir, input_data_q):
    try:
        print('output_dir',output_dir)
        logger.info(f'output_dir {output_dir}')
        # if data_path is xlsx or csv，use pandas to read,if data_path is url ,use requests to read
        if data_path.endswith('xlsx') or data_path.endswith('csv'):
            datares = pd.read_csv(data_path, encoding='latin-1',skipinitialspace=True,dtype=str).dropna(how='all')
            # datares = pd.read_csv(data_path, encoding='latin-1',header=0,skipinitialspace=True).dropna(how='all')
            # datares = datares.drop(datares.index[0,1])
            # datares = datares.drop(datares.index[0,1])
            # datares.headers = datares.iloc[0]
            print('datares.shape',datares.shape)
            print('datares.cols',datares.columns.tolist())
            datares.rename(columns={'ï»¿id':'id'},inplace=True)
            # datares.rename(columns={'product_id':'id'},inplace=True)
            # print('type',type(datares['id'].tolist()[0]),datares['id'].tolist()[0])
            # datares['id']=datares['id'].astype(int)
            datares['id']=datares['id'].astype(str)


            datares = datares[['id','title','imgs1','desc1','features1','link1']]

            # datares = datares[['id','title_x','imgs','desc','features','link']]
            datares.rename(columns={'imgs1':'imgs','desc1':'desc','features1':'features','link1':'link'},inplace=True)
            # datares = datares.sample(1)
            # datares = datares.iloc[0:3]
            for index,row in datares.iterrows():
                
                print('index',index)
                outputdir = os.path.join(output_dir,f'{str(row["id"])}_{time.strftime("%H_%M_%S")}')
                os.makedirs(outputdir)
                product_info =[]
                imgs = []
                product_id = row['id']
                # dowload  imgs
                if row['imgs'] == '':
                    imgs = []
                elif type(row['imgs']) == str:
                    imgs = json.loads(row['imgs'])[0:5]
                elif type(row['imgs']) == list:
                    imgs = row['imgs']
                print('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')
                imgs = download_data(imgs,outputdir)
                if  len(imgs) == 0:
                    logger.info(f'can not get img url :which product is {product_id}:{row["link"]}')
                    # continue
                product_info = row[['title','desc','features','link']].dropna().to_dict()
                # convert product_info to str 

                # input_data = {"id":product_id,"imgs":imgs,"info":product_info}
                input_data = {"id":product_id,"imgs":outputdir,"info":product_info,"index":index}
                # print('input_data',input_data)
                print('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')
                
                logger.info('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')
                logger.info(f'input_data {input_data}')
                logger.info('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')
                
                
                input_data_q.put(input_data)
                input_data_qsize = input_data_q.qsize()

                global MAXQSIZE
                MAXQSIZE +=1
                # if input_data_qsize > MAXQSIZE:
                #     MAXQSIZE = input_data_qsize

            # return True, imgs
    
    except Exception as e:
        logger.error(f'{traceback}')
        logger.error(f'e {e}')
        logger.error(f'{e.__traceback__.tb_frame.f_globals["__file__"]}')
        logger.error(f'{e.__traceback__.tb_lineno}')
        # raise e
        # return False, str(e)

def auto_label(servicetag,queueimg,version,resq,resqt):
    
    print('starting label')
    canget = True
    servicetag = Service(servicetag)

    
    try:
        while canget:
            queuesize = queueimg.qsize()
            # todo get quene and  service.tag_main
            imgsinfo =  queueimg.get(block=True, timeout=120)

            if imgsinfo is None:
                canget = False
                return False, 'no data'
            else:
                # print('imgsinfo',imgsinfo)
                logger.info(f'imgsinfo {imgsinfo}')

            tag_perp = servicetag.tag_main(imgsinfo['imgs'],imgsinfo['info'],version)

            print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')

            logger.info('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
            logger.info(f'imgsinfo {imgsinfo}')
            logger.info(f'tag_perp {tag_perp}')
            logger.info('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')

            if type(tag_perp) == str:
                return False, tag_perp
            result_df = pd.DataFrame(tag_perp)

            result_df_t = result_df.T

            result_df_t.columns = result_df_t.iloc[0]
            result_df_t = result_df_t.drop(result_df_t.index[0])
            result_df_t.insert(0,'idindex',imgsinfo['index'])
            result_df_t.insert(1,"product_url",imgsinfo['info']['link'])
            result_df_t.insert(1,'product_id',imgsinfo['id'])
            global RES
             
            # RES = pd.concat([RES, result_df_t], ignore_index=True)
            # print('RES',RES)
            resqt.put(result_df_t)


            # result_df_t.insert(0,'imgs',imgsinfo['imgs'])

            # pd.merge(result_t,result_df_t,how='outer')

            result_df.insert(0,'idindex',imgsinfo['index'])
            result_df.insert(1,"product_url",imgsinfo['info']['link'])
            result_df.insert(1,'product_id',imgsinfo['id'])
            resq.put(result_df)
            # resq.put(result_df)    
        # return True, result_df

    except Exception as e:
        logger.error(f'e {e}')
        logger.info(f'{e.__traceback__.tb_frame.f_globals["__file__"]}')
        logger.info(f'{e.__traceback__.tb_lineno}')
        # raise e
        # return False, str(e)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    
    # parser.add_argument('--url', type=str, default='/root/autodl-tmp/autotagging/taggingpipeline/data/data_1/datav1_4.csv', help='url')
    parser.add_argument('--url', type=str, default='/root/autodl-tmp/autotagging/taggingpipeline/data/data_1/spu_no_top_11101705_final.csv', help='url')
    parser.add_argument('--res_dir', type=str, default='/root/autodl-tmp/tmp_res/tag_res/output', help='res_dir')
    parser.add_argument('--questionjson', type=str, default='/root/autodl-tmp/autotagging/taggingpipeline/mainpipeline/prompts/quesion.json', help='question.json path')
    parser.add_argument('--version', type=str, default='20131114_cl', help='question.json path')


    args = parser.parse_args()
    torch.multiprocessing.set_start_method('spawn')


    if not os.path.exists(args.res_dir):
        os.makedirs(args.res_dir)

    if os.path.exists(args.url):
        file_name = args.url.split('/')[-1].split('.')[0]
        args.res_dir = os.path.join(args.res_dir,f'{file_name}_{args.version}_{time.strftime("%Y%m%d_%H%M")}')
    else:
        args.res_dir = os.path.join(args.res_dir,f'{args.version}_{time.strftime("%Y%m%d_%H%M")}')
    
    os.makedirs(args.res_dir)
    # add logger 
    # logger.add(os.path.join(args.res_dir,'log.log'), rotation="500 MB",format="[{time:HH:mm:ss}] {level} - {message}")

    # make out csv and log json file 
    outcsvpath = os.path.join(args.res_dir,f'{args.version}_{time.strftime("%Y%m%d_%H%M")}_label_res.csv')
    log_path = os.path.join(args.res_dir,f'{args.version}_{time.strftime("%Y%m%d_%H%M")}_log.json')
    
    # qw_s = Service(args.questionjson)

    # 使用multiprocessing.Manager创建一个可以在进程之间共享的队列
    manager = multiprocessing.Manager()
    q = manager.Queue()
    resq = manager.Queue()
    resqt = manager.Queue()

    # 创建并启动两个进程
    imgs_res_dir = os.path.join(args.res_dir,'imgs')
    logger.info(f'imgs_res_dir {imgs_res_dir}')
    print('====================================START PROCESS====================================')
    logger.info('====================================START PROCESS====================================')
    p1 = multiprocessing.Process(target=data_input, args=(args.url, imgs_res_dir, q))
    
    # p2 = multiprocessing.Process(target=auto_label, args=(qw_s,q,args.version,resq))
    p2 = multiprocessing.Process(target=auto_label, args=(args.questionjson,q,args.version,resq,resqt))

    p1.start()
    time.sleep(60)
    p2.start()

    # 
    p1.join()
    p2.join()

    print('====================================END PROCESS====================================')
    logger.info('====================================END PROCESS====================================')

    # res_data  = pd.DataFrame(result)
    # res_data.to_csv(outcsvpath,index=False)

    # creat out csv file
    print('outcsvpath',outcsvpath)

    open(outcsvpath,'a').close()
    print('result.shape',RES.shape)
        
    # if not RES.empty:
    #     RES.to_csv(outcsvpath,index=False)
    # print('~~~~~~~~~~~~~~~~~~~~~~max input data size ',MAXQSIZE,'~~~~~~~~~~~~~~~~~~~~~~')
    # print('~~~~~~~~~~~~~~~~~~~~~~resq.qsize()',resq.qsize(),'~~~~~~~~~~~~~~~~~~~~~~')
    logger.info(f'max input data size {MAXQSIZE}')
    logger.info(f'resq.qsize() {resq.qsize()}')
    
    while  resq.qsize() >0:
        tmpres = resq.get(block=True, timeout=240)
        RES_t = pd.concat([RES_t,tmpres],axis=0)
        print('RES_t.shape',RES_t.shape)
        # print('RES_t',RES_t)
        logger.info(f'RES_t.shape {RES_t.shape}')
    RES_t.to_csv(outcsvpath,index=False)

    print('RES.shape',RES.shape)

    label_res_t= outcsvpath.replace('label_res','label_res_t')
    open(label_res_t,'a').close()

    while  resqt.qsize() >0:
        tmpres = resqt.get(block=True, timeout=240)
        RES = pd.concat([RES,tmpres],axis=0)
        print('RES.shape',RES.shape)
        # print('RES_t',RES_t)
        logger.info(f'RES.shape {RES.shape}')

    RES.to_csv(label_res_t,index=False)
    
    # if not result_t.empty:
    #     result_t.to_csv('/root/autodl-tmp/autotagging/taggingpipeline/output/data_1/tt.csv')
    logger.info('====================================END LABEL====================================')
    print('====================================END LABEL====================================')