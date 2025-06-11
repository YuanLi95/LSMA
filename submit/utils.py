from openai import OpenAI
import json
import re
import random
import time
import os
client = OpenAI(api_key="input your api key",base_url='input your base url')
 
def getfromOpenAI(system, user,model):
  completion = client.chat.completions.create(
    model=model,
    messages=[
      {"role": "system", "content": system},
      {"role": "user", "content": user}
    ]
  )
 
  return completion.choices[0].message.content

def replace_variables(text, variables):
    for variable, value in variables.items():
        text = text.replace(variable, str(value))
    return text


def extract_prompt(file_path, variables):
    with open(file_path, 'r') as file:
        content = file.read()

    #分别是prompt中system和user的起始标记
    system_start_marker = "==== SYSTEM ===="
    user_start_marker = "==== USER ===="

    system_start = content.find(system_start_marker) + len(system_start_marker)
    system_end = content.find(user_start_marker)
    system_text = content[system_start:system_end].strip()

    user_start = content.find(user_start_marker) + len(user_start_marker)
    user_text = content[user_start:].strip()

    system_text = replace_variables(system_text, variables)
    user_text = replace_variables(user_text, variables)

    return system_text, user_text


def get_variables(data, arg):
    if arg['type']=='rephrase' or arg['type']=='extend'or arg['type']=='ai_filter':
        return{
            "<<INPUT>>":data
        }
    elif arg['type']=='generate':
        if arg['year']=="2017":
            return{
                "<<INPUT>>":data
            }
        elif arg['year']=="2015":
            data_rt=[0,1,0,1,0,1,0,1,0,1,1,1]
            random.shuffle(data_rt)
            rt='The comments you generate should not start with the "RT @Username:" format.'
            if data_rt[0]==1:
                rt='*The comments you generate start with the "RT @Username:" format, where "Username" can be a real person, an organization, or a name I invent. Additionally, there is a 10% chance that the comments you generate do not start with a retweet format.'
            
            return {
            "<<INPUT>>":data["aspects"],
            "<<RT>>":rt
            }

def getDictFromJsonl(file_path):
    if os.path.exists(file_path)==False:
        return []
    data=[]
    if file_path.endswith('.jsonl'):
        with open(file_path, 'r',encoding='utf-8') as f:
            data = [json.loads(line) for line in f]
    elif file_path.endswith('.json'):
        with open(file_path, 'r',encoding='utf-8') as f:
            data = json.load(f)
    
    return data

def safe_json_loads(json_str):
    try:
        # 尝试解析JSON字符串
        if isinstance(json_str, str):
            str_ = re.sub(r"```|json", "", json_str) 
            return json.loads(str_)
        print("输入不是字符串")
        return None
        
    except json.JSONDecodeError:
        # 如果解析失败，打印错误信息并返回None
        print("JSON解析失败，将尝试重新获取数据。")
        return None
    
def aspects_extract(input_path,output_path):
    '''将原本的数据得到句子和抽出aspect,丢弃image_id等'''
    with open(input_path, 'r') as file:
        # 加载 JSON 数据
        data = json.load(file)

    list_= []
    for item in data:
        dict_={}
        sentence = ' '.join(item['words'])
        dict_['sentence'] = sentence
        aspect_list = []
        for aspect in item['aspects']:
            term=' '.join(aspect["term"])
            sentiment = aspect["polarity"]
            aspect_list.append({"term": term, "polarity": sentiment})
        dict_['aspects'] = aspect_list
        dict_['image_id'] = item['image_id']
        list_.append(dict_)
    # 将处理后的数据写入新的 JSONL 文件

    with open(output_path, 'w',encoding='utf-8') as file:
        for item in list_:
            json.dump(item, file)
            file.write('\n')

def append_to_jsonl(file_path, data):
    with open(file_path, 'a', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


def split_and_preserve_punctuation(sentence):
    # 定义需要保留的符号
    punctuations = ['@', '.', ',', '!', '?', '#','\'','\"','*','$','(',')']
    
    # 首先根据空格分割句子
    words = sentence.split(' ')
    
    # 用于存储最终结果的列表
    result = []
    
    # 遍历每个单词
    for word in words:
        # 如果单词中包含定义的符号，则进一步分割
        if any(punct in word for punct in punctuations):
            # 将单词分割成符号前的单词和符号
            for punct in punctuations:
                # 找到符号的位置
                index = word.find(punct)
                # 如果找到了符号
                while index != -1:
                    # 将符号前的单词添加到结果列表
                    result.append(word[:index])
                    # 将符号本身添加到结果列表
                    result.append(punct)
                    # 更新单词，去掉已经处理过的部分
                    word = word[index + 1:]
                    # 再次查找符号的位置
                    index = word.find(punct)
            # 如果单词中没有符号了，直接添加到结果列表
            if word and word!="":
                result.append(word)
        else:
            # 如果单词中没有符号，直接添加到结果列表
            result.append(word)
    
    return result

def find_from2to(sentence, term_list):
    '''以每个句子为单位'''
    for index,term in enumerate(term_list):
        #找到term在sentence中的位置
        from_=-1
        to_=-1
        for i,word in enumerate(sentence):
            if word == term['term'][0]:
                from_=i
            if word == term['term'][-1]:
                to_=i
                break
        
        if from_ != -1 and to_ != -1:
            term_list[index]['from'] = from_
            term_list[index]['to'] = to_+1
        else:
            return []
            # term_list[index]['from'] = -1
            # term_list[index]['to'] = -1

    return term_list

def reunite_set(input_path):
    term_list = []
    sentiment=[]
    geshu=[]
    
    with open(input_path, 'r') as file:
        # 加载 JSONL 数据
        for line in file:
            data = json.loads(line)
            for aspect in data['aspects']:
                term_list.append(aspect['term'])
                sentiment.append(aspect['polarity'])
            geshu.append(len(data['aspects']))

    random.shuffle(term_list)
    random.shuffle(sentiment)

    new_data = []
    start=0
    for i in geshu:
        aspect=[]
        for j in range(start,start+i):
            dict_={}
            dict_['term'] = term_list[j]
            dict_['sentiment'] = sentiment[j]
            aspect.append(dict_)

        new_data.append({"aspects": aspect})
        start+=i

    return new_data

def get_aspects_from_extension(extension_path,origin_path):
    '''origin_path: 原始数据集
    为了求出原数据集情感的分布情况，还有句子有多少个实体的情况，使扩展集全部保持一致'''
    term_list = []
    sentiment=[]
    geshu=[]
    
    with open(origin_path, 'r') as file:
        # 加载 JSONL 数据
        for line in file:
            data = json.loads(line)
            for aspect in data['aspects']:
                sentiment.append(aspect['polarity'])
            geshu.append(len(data['aspects']))

    with open(extension_path, 'r') as file:
        # 加载 JSONL 数据
        for line in file:
            data = json.loads(line)
            for aspect in data['aspects']:
                term_list.append(aspect['term'])

    random.shuffle(term_list)
    random.shuffle(sentiment)

    new_data = []
    start=0
    for i in geshu:
        aspect=[]
        for j in range(start,start+i):
            dict_={}
            dict_['term'] = term_list[j]
            dict_['polarity'] = sentiment[j]
            aspect.append(dict_)

        new_data.append({"aspects": aspect})
        start+=i

    return new_data
            
def record(log_file, log):
    with open(log_file, 'a') as f:
        #先记录当前时间
        f.write('==================================\n')
        f.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\n')
        f.write(log + '\n')

def delete_unretain(data):
    newdata=[]
    for item in data:
        if item['retain']==0:
            continue
        newdata.append(item)

    return newdata

def print_len_words(data_list):
    n_5_10=0
    n_10_15=0
    n_15_20=0
    n_20_25=0
    n_25_30=0
    for item in data_list:
        if len(item['words'])/5<2:
            n_5_10+=1
        elif len(item['words'])/5<3:
            n_10_15+=1
        elif len(item['words'])/5<4:
            n_15_20+=1
        elif len(item['words'])/5<5:
            n_20_25+=1
        else:
            n_25_30+=1
    print(n_5_10,n_10_15,n_15_20,n_20_25,n_25_30)

            