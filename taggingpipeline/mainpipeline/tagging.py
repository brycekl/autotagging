from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig
import torch
import gradio as gr
import pandas as pd
import os
import copy
import json 

from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig

from log_config import get_logger

logger = get_logger()



class InitQwen:
    def __init__(self,iftest=False):
        # 请注意：分词器默认行为已更改为默认关闭特殊token攻击防护。
        self.tokenizer = AutoTokenizer.from_pretrained("/root/autodl-tmp/autotagging/Qwen-VL-Chat", trust_remote_code=True)

        # 默认gpu进行推理，需要约24GB显存
        # model = AutoModelForCausalLM.from_pretrained("/root/autodl-tmp/autotagging/Qwen-VL-Chat", device_map="cuda", trust_remote_code=True).eval()
        self.model = AutoModelForCausalLM.from_pretrained("/root/autodl-tmp/autotagging/Qwen-VL-Chat", device_map="cuda", trust_remote_code=True, fp16=True).eval()
        self.history = None
        self.history_ = None
        self.iftest = iftest
        # self.tokenizer2 = AutoTokenizer.from_pretrained("/root/autodl-tmp/autotagging/Qwen-14B-Chat-Int4", trust_remote_code=True)
        self.model2 = AutoModelForCausalLM.from_pretrained("/root/autodl-tmp/autotagging/Qwen-14B-Chat-Int4", device_map="cuda", trust_remote_code=True).eval()
    
    def clear_history(self):
        self.history = None
        self.history_ = None
        self.tmptag_ = None
        return 'clear history'
    
    def infer(self,imagepath,qname):

        query = self.tokenizer.from_list_format([
                {'image': f'{imagepath}'}, # Either a local path or an url
                {'text': f'{qname}'},
            ])
        response, self.history = self.model.chat(self.tokenizer, query=query, history=self.history)
        print(response)

        return response

    def infer_mulimg(self,imagepath,qname):
        self.history = None 
        list_format =[]
        # if  imagepath  is a dirpath,then get all imagepath in dirpath 
        if os.path.isdir(imagepath):
            for root, dirs, files in os.walk(imagepath):
                for file in files:
                    if file.endswith('.png') or file.endswith('.jpg'):
                        imgpath = os.path.join(root, file)
                        list_format.append({'image':imgpath})

        elif os.path.isfile(imagepath):
            list_format.append({'image':imagepath})

        list_format.append({'text': f'{qname}'})

        query = self.tokenizer.from_list_format(list_format)

        response, self.history = self.model.chat(self.tokenizer, query=query, history=self.history)
        self.history_ = copy.deepcopy(self.history)
        self.tmptag_ = None 

        if self.iftest:
            response = f'Q:{qname} \n\n A:{response}'
        
        print(response)

        return response
    
    def infer_noimg(self,imagepath,qname):

        # print('imagepath:',imagepath)
        # print('qname:',qname)
        # print('self.tmptag_:',self.tmptag_)
        # print('self.history_ = self.history',self.history_ == self.history)
        # print('idself.history_ = self.history',id(self.history_) == id(self.history))

        logger.info(f'imagepath:{imagepath}')
        logger.info(f'qname:{qname}')
        logger.info(f'self.tmptag_:{self.tmptag_}')
        logger.info(f'self.history_ = self.history:{self.history_ == self.history}')
        logger.info(f'idself.history_ = self.history:{id(self.history_) == id(self.history)}')


        if self.tmptag_ is None:
            self.tmptag_ = imagepath
        elif self.tmptag_ != imagepath:
            self.history_ = None
            self.history_ = copy.deepcopy(self.history)
            self.tmptag_ = imagepath


        query = self.tokenizer.from_list_format([{'text': f'{qname}'}])
        response, self.history_ = self.model.chat(self.tokenizer, query=query, history=self.history_)

        if self.iftest:
            response = f'Q:{qname} \n\n A:{response}'
        logger.info(f'Q:{qname} \n\n A:{response}')

        return response
    
    def detec_main(self,imagepath,qname):
        logger.info('start qa' )
        if os.path.isdir(imagepath) or os.path.isfile(imagepath):
            return self.infer_mulimg(imagepath,qname)
        else:
            return self.infer_noimg(imagepath,qname)
    


    def tag_main(self,imagepath,qname):
        if os.path.isdir(imagepath) or os.path.isfile(imagepath):
            return self.infer_mulimg(imagepath,qname)
        else:
            return self.infer_noimg(imagepath,qname)
    
    def quick_qa(self,qustion):

        response, history_ = self.model2.chat(self.tokenizer, query=qustion, history=None)
        logger.info(f'Q:{qustion} \n\n A:{response}')
        return response

