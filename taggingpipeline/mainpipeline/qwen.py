from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig
import torch


class InitQwen:
    def __init__(self):
        # 请注意：分词器默认行为已更改为默认关闭特殊token攻击防护。
        self.tokenizer = AutoTokenizer.from_pretrained("/root/autodl-tmp/autotagging/Qwen-VL-Chat", trust_remote_code=True)

        # 默认gpu进行推理，需要约24GB显存
        # model = AutoModelForCausalLM.from_pretrained("/root/autodl-tmp/autotagging/Qwen-VL-Chat", device_map="cuda", trust_remote_code=True).eval()
        self.model = AutoModelForCausalLM.from_pretrained("/root/autodl-tmp/autotagging/Qwen-VL-Chat", device_map="cuda", trust_remote_code=True, fp16=True).eval()

    def infer(self,imagepath):
        
        qname1 = 'please  describe the clothes in the picture as much detail as possible'


        query = self.tokenizer.from_list_format([
                {'image': f'{imagepath}'}, # Either a local path or an url
                {'text': f'{qname1}'},
            ])
        

        response, history = self.model.chat(self.tokenizer, query=query, history=None)
        print(response)

