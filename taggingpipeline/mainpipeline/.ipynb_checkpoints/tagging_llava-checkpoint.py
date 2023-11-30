import argparse
import copy
import os
# from LLaVA import llava
# import LLaVA
import sys
import time

import requests
import torch
from PIL import Image

sys.path.append('/root/autodl-tmp/autotagging/LLaVA')

# from LLaVA.llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN, DEFAULT_IM_START_TOKEN, DEFAULT_IM_END_TOKEN
# from LLaVA.llava.conversation import conv_templates, SeparatorStyle
# from LLaVA.llava.model.builder import load_pretrained_model
# from LLaVA.llava.utils import disable_torch_init
# from LLaVA.llava.mm_utils import process_images, tokenizer_image_token, get_model_name_from_path, KeywordsStoppingCriteria

from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN, DEFAULT_IM_START_TOKEN, DEFAULT_IM_END_TOKEN
from llava.conversation import conv_templates, SeparatorStyle
from llava.model.builder import load_pretrained_model
from llava.utils import disable_torch_init
from llava.mm_utils import process_images, tokenizer_image_token, get_model_name_from_path, KeywordsStoppingCriteria

from io import BytesIO
from transformers import TextStreamer

from log_config import get_logger

logger = get_logger()


def load_image(image_file):
    if image_file.startswith('http://') or image_file.startswith('https://'):
        response = requests.get(image_file)
        image = Image.open(BytesIO(response.content)).convert('RGB')
    else:
        image = Image.open(image_file).convert('RGB')
    return image


class InitLLA:
    def __init__(self, iftest=False):
        model_path = "/root/autodl-tmp/autotagging/llava-v1.5-13b"
        model_base = None
        self.iftest = iftest

        self.tokenizer, self.model, self.image_processor, self.context_len, conv_mode, self.model_name = self.load_model(
            model_path, model_base)
        self.conv = conv_templates[conv_mode].copy()
        self.conv_init = conv_templates[conv_mode].copy()
        # self.conv = None
        self.conv_ = None

    def load_model(self, model_path, model_base):
        disable_torch_init()

        load_8bit = False
        load_4bit = True

        model_name = get_model_name_from_path(model_path)
        tokenizer, model, image_processor, context_len = load_pretrained_model(model_path, model_base, model_name,
                                                                               load_8bit, load_4bit)

        if 'llama-2' in model_name.lower():
            conv_mode = "llava_llama_2"
        elif "v1" in model_name.lower():
            conv_mode = "llava_v1"
        elif "mpt" in model_name.lower():
            conv_mode = "mpt"
        else:
            conv_mode = "llava_v0"

        return tokenizer, model, image_processor, context_len, conv_mode, model_name

    def load_image(self, image_file, model_cfg):
        # load image
        imgs = []
        if os.path.isdir(image_file):
            print('isdir')
            for root, dirs, files in os.walk(image_file):
                for file in files:
                    if file.endswith('.jpg') or file.endswith('.png'):
                        imgs.append(load_image(os.path.join(root, file)))
            print(f'len image is {len(imgs)}')
        else:
            imgs.append(load_image(image_file))

        # Similar operation in model_worker.py
        image_tensor = process_images(imgs, self.image_processor, model_cfg)
        if type(image_tensor) is list:
            image_tensor = [image.to(self.model.device, dtype=torch.float16) for image in image_tensor]
        else:
            image_tensor = image_tensor.to(self.model.device, dtype=torch.float16)

        print(f'image tensor shape is {image_tensor.shape}')
        logger.info(f'image tensor shape is {image_tensor.shape}')

        return image_tensor, imgs

    def infer_mulimg(self, imagepath, inp):

        logger.info('start qa with images')
        self.conv = copy.deepcopy(self.conv_init)

        # process images
        model_cfg = {'image_aspect_ratio': 'pad'}
        self.image_tensor, imgs = self.load_image(imagepath, model_cfg)
        # first message
        if self.model.config.mm_use_im_start_end:
            inp = DEFAULT_IM_START_TOKEN + DEFAULT_IMAGE_TOKEN + DEFAULT_IM_END_TOKEN + '\n' + inp
        else:
            inp = DEFAULT_IMAGE_TOKEN + '\n' + inp

        self.conv.append_message(self.conv.roles[0], inp)
        image = None
        conv = copy.deepcopy(self.conv)
        response, self.conv = self.infer(conv)

        self.conv_ = copy.deepcopy(self.conv)
        self.tmptag_ = None

        logger.info(f'Q:{inp} \n\n A:{response}')

        return response

    def infer_noimg(self, imagepath, inp):
        logger.info('start qa without images')

        if self.tmptag_ is None:
            self.tmptag_ = imagepath
        elif self.tmptag_ != imagepath:
            self.conv_ = None
            self.conv_ = copy.deepcopy(self.conv)
            self.tmptag_ = imagepath

        self.conv_.append_message(self.conv_.roles[0], inp)
        conv = copy.deepcopy(self.conv_)
        response, self.conv_ = self.infer(conv)
        logger.info(f'Q:{inp} \n\n A:{response}')

        return response

    def infer(self, conv, temperature=0.9, max_new_tokens=10000):

        conv.append_message(conv.roles[1], None)
        prompt = conv.get_prompt()

        input_ids = tokenizer_image_token(prompt, self.tokenizer, IMAGE_TOKEN_INDEX, return_tensors='pt').unsqueeze(
            0).cuda()
        stop_str = conv.sep if conv.sep_style != SeparatorStyle.TWO else conv.sep2
        keywords = [stop_str]
        stopping_criteria = KeywordsStoppingCriteria(keywords, self.tokenizer, input_ids)
        streamer = TextStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
        logger.info(f'!!!!!!!start generate!!!!!!!!!!!!!!!!!')

        with torch.inference_mode():
            output_ids = self.model.generate(
                input_ids,
                images=self.image_tensor,
                do_sample=True,
                temperature=temperature,
                max_new_tokens=max_new_tokens,
                streamer=streamer,
                use_cache=True,
                stopping_criteria=[stopping_criteria])

        outputs = self.tokenizer.decode(output_ids[0, input_ids.shape[1]:]).strip()
        conv.messages[-1][-1] = outputs

        return outputs, conv

    def tag_main(self, imagepath, qname):
        logger.info('start qa')
        response = '</s>'

        if os.path.isdir(imagepath) or os.path.isfile(imagepath):

            response = self.infer_mulimg(imagepath, qname)
        else:
            response = self.infer_noimg(imagepath, qname)

        response = response.replace("</s>", "")

        # response = self.infer(imgs,qname)
        print(f'Q:{qname} \n\n A:{response}')

        return response


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--model_path", type=str, default="/root/autodl-tmp/autotagging/llava-v1.5-13b")
    parser.add_argument("--model_base", type=str, default=None)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--conv-mode", type=str, default=None)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--load-8bit", action="store_true")
    parser.add_argument("--load-4bit", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--image-aspect-ratio", type=str, default='pad')

    args = parser.parse_args()

    start_time = time.time()

    qw_s = InitLLA()

    init_time = time.time()

    imgsinfo0 = {'imgs': '/root/autodl-tmp/autotagging/taggingpipeline/test_data/test_easy_7_imgs',
                 'info': '{Color:   Green, \n Product desciption: Take your collared look up a notch. We made this notch collar blouse with a relaxed, slim fit with a clean and crisp look for an everyday appeal. Perfectly made to be layered or worn solo. Plus, silk fiber contains 18 kinds of amino acids that make it amazing for skin nourishment, hypo-allergenic, and naturally thermoregulating to help maintain body temperature., \n details: [\n Crafted from 90% mulberry silk for luxe feel, and 10% spandex for a little stretch  \t, \n 19mm fabric weight for a premium drape and hand-feel, \n This material is certified by OEKO-TEX Standard 100 (Certificate Number: SH015140381& SH050127759) which ensures that no hazardous substances are present",Made with care in China  \n ],size&fit:[Slim fit, consider sizing up for a more relaxed look]}'
                 }

    # imgsinfos = [imgsinfo2,imgsinfo3]
    qname = "you are a professional fashion consultant,you answer a series of information about clothing characteristics,follow these steps to complete \n first : observethe clothes in the pictures \n second: Take a deep breath and read the refer information carefully,refer info:{ Color:   Green, Product desciption: Take your collared look up a notch. We made this notch collar blouse with a relaxed, slim fit with a clean and crisp look for an everyday appeal. Perfectly made to be layered or worn solo. Plus, silk fiber contains 18 kinds of amino acids that make it amazing for skin nourishment, hypo-allergenic, and naturally thermoregulating to help maintain body temperature., details: [Crafted from 90% mulberry silk for luxe feel, and 10% spandex for a little stretch  \t,19mm fabric weight for a premium drape and hand-feel,This material is certified by OEKO-TEX Standard 100 (Certificate Number: SH015140381& SH050127759) which ensures that no hazardous substances are present,Made with care in China ],size&fit:[Slim fit, consider sizing up for a more relaxed look]} \n third: answer the questions \n  question: what kind of this clothed is this?Introduce it briefly"

    qname2 = "question:what is the top category  of this clothes? \n options: ['TOP', 'DRESS', 'SWEATER','JACKET', 'OUTWEAR','BOTTOMS','PANTS'],\n please select an answer from the above options,no need to answer in full sentences \n please answer your options directly and just give one option \n answer 'none' if there is no match in the options "
    # 衣服种类

    imgsinfos = [imgsinfo0]

    for imgsinfo in imgsinfos:
        tag_perp = qw_s.tag_main(imgsinfo['imgs'], qname)

        tag_perp = qw_s.tag_main(" ", qname2)

        print(
            '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
        print('imgsinfo', imgsinfo)
        print('tag_perp', tag_perp)
        print(
            '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')

        print('===============================')
        print('RESULT:')

        print(tag_perp)
        print('===============================')
