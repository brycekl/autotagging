import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

torch.manual_seed(1234)

# 请注意：分词器默认行为已更改为默认关闭特殊token攻击防护。
tokenizer = AutoTokenizer.from_pretrained("/root/autodl-tmp/autotagging/Qwen-VL-Chat", trust_remote_code=True)

# 默认gpu进行推理，需要约24GB显存
# model = AutoModelForCausalLM.from_pretrained("/root/autodl-tmp/autotagging/Qwen-VL-Chat", device_map="cuda", trust_remote_code=True).eval()
model = AutoModelForCausalLM.from_pretrained("/root/autodl-tmp/autotagging/Qwen-VL-Chat", device_map="cuda",
                                             trust_remote_code=True, fp16=True).eval()

# 可指定不同的生成长度、top_p等相关超参（transformers 4.32.0及以上无需执行此操作）
# model.generation_config = GenerationConfig.from_pretrained("Qwen/Qwen-VL-Chat", trust_remote_code=True)

# 第一轮对话
query = tokenizer.from_list_format([
    {'image': 'https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg'},
    # Either a local path or an url
    {'text': '这是什么?'},
])
response, history = model.chat(tokenizer, query=query, history=None)
print(response)
# 图中是一名女子在沙滩上和狗玩耍，旁边是一只拉布拉多犬，它们处于沙滩上。

# 第二轮对话
response, history = model.chat(tokenizer, '框出图中击掌的位置', history=history)
print(response)
# <ref>击掌</ref><box>(536,509),(588,602)</box>
image = tokenizer.draw_bbox_on_latest_picture(response, history)
if image:
    image.save('1.jpg')
else:
    print("no box")
