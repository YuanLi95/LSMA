import os
from PIL import Image
import numpy as np
import torch
import clip
from utils import *
# 加载 CLIP 模型
device = torch.device("cuda:4" if torch.cuda.is_available() else "cpu")
model, preprocess = clip.load("ViT-B/32",device=device)
# print(model)
model.eval()

def get_(image_list,text_list):
    '''虽未list，但实际上只有一个元素'''
    # 图像和文本预处理
    image_input = torch.tensor(np.stack(image_list)).to(device)
    text_tokens = clip.tokenize(text_list).to(device)

    # 计算特征
    with torch.no_grad():
        image_features = model.encode_image(image_input).float()
        text_features = model.encode_text(text_tokens).float()

    # 计算相似度
    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)

    similarity = (text_features.cpu().numpy() @ image_features.cpu().numpy().T)
    return similarity


def service(input_path,image_dir,output_path):
    data=getDictFromJsonl(input_path)
    similarity_list=[]
    sum=len(data)
    num_20=0
    num_25=0
    num_30=0
    output=[]
    for idx,item in enumerate(data):
        print(idx)
        texts=[item['sentence']]
        image_path=image_dir+item['image_id']
        if os.path.exists(image_path)==False:
            continue
        try:
            image=Image.open(image_path).convert("RGB")
        except:
            similarity_list.append(0)
            continue
        images=[preprocess(image)]
        similarity=get_(image_list=images,text_list=texts)
        print(item['image_id'],similarity)
        if similarity<0.2:
            item['retain']=0
        output.append(item)

    append_to_jsonl(output_path,output)




def main():
    input_path="MBASA_DE/output/twitter_2017/100/add_image.jsonl"
    output_path="MBASA_DE/output/twitter_2017/100/clip_fiter.jsonl"
    image_dir='MBASA_DE/output/twitter_2017/100/image/'
    service(input_path,image_dir,output_path)


if __name__=='__main__':
    main()


