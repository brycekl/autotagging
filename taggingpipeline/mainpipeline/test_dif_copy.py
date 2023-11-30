import copy
import os

import gradio as gr
from transformers import AutoModelForCausalLM, AutoTokenizer


class InitQwen:
    def __init__(self, iftest=False):
        # 请注意：分词器默认行为已更改为默认关闭特殊token攻击防护。
        self.tokenizer = AutoTokenizer.from_pretrained("/root/autodl-tmp/autotagging/Qwen-VL-Chat",
                                                       trust_remote_code=True)

        # 默认gpu进行推理，需要约24GB显存
        # model = AutoModelForCausalLM.from_pretrained("/root/autodl-tmp/autotagging/Qwen-VL-Chat", device_map="cuda", trust_remote_code=True).eval()
        self.model = AutoModelForCausalLM.from_pretrained("/root/autodl-tmp/autotagging/Qwen-VL-Chat",
                                                          device_map="cuda", trust_remote_code=True, fp16=True).eval()
        self.history = None
        self.history_ = None
        self.iftest = iftest

    def infer(self, imagepath, qname):

        query = self.tokenizer.from_list_format([
            {'image': f'{imagepath}'},  # Either a local path or an url
            {'text': f'{qname}'},
        ])

        response, self.history = self.model.chat(self.tokenizer, query=query, history=self.history)
        print(response)

        return response

    def infer_mulimg(self, imagepath, qname):

        list_format = []
        # if  imagepath  is a dirpath,then get all imagepath in dirpath 
        if os.path.isdir(imagepath):
            for root, dirs, files in os.walk(imagepath):
                for file in files:
                    if file.endswith('.png') or file.endswith('.jpg'):
                        imgpath = os.path.join(root, file)
                        list_format.append({'image': imgpath})

        elif os.path.isfile(imagepath):
            list_format.append({'image': imagepath})

        list_format.append({'text': f'{qname}'})

        query = self.tokenizer.from_list_format(list_format)

        response, self.history = self.model.chat(self.tokenizer, query=query, history=self.history)
        self.history_ = copy.deepcopy(self.history)
        self.tmptag_ = None

        if self.iftest:
            response = f'Q:{qname} \n\n A:{response}'

        print(response)

        return response

    def infer_noimg(self, imagepath, qname):

        print('imagepath:', imagepath)
        print('qname:', qname)
        print('self.tmptag_:', self.tmptag_)
        print('self.history_ = self.history', self.history_ == self.history)
        print('idself.history_ = self.history', id(self.history_) == id(self.history))

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
        print(response)

        return response

    def detec_main(self, imagepath, qname):
        if os.path.isdir(imagepath) or os.path.isfile(imagepath):
            return self.infer_mulimg(imagepath, qname)
        else:
            return self.infer_noimg(imagepath, qname)

    def clear_history(self):
        self.history = None
        self.history_ = None
        self.tmptag_ = None
        return 'clear history'


Iqw = InitQwen(iftest=True)

outputres = gr.Textbox(lines=2, label="response")
ttq = gr.Interface(fn=Iqw.detec_main,
                   title='test——qwen',
                   inputs=[gr.Textbox(lines=2, label="imagepath"),
                           gr.Textbox(lines=2, label="query")],
                   outputs=[outputres])

ccq = gr.Interface(fn=Iqw.clear_history,
                   title='clear——qwen',
                   inputs=[],
                   outputs='text')

io = gr.TabbedInterface([ttq, ccq], ["test_qwen", "clear_qwen"])

if __name__ == '__main__':
    io.launch(server_port=6006)
