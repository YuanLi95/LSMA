import json
from utils import *
import random
import ast
import os
model='gpt-4o-mini'
#注意2015和2017的prompt不同
p_2015='prompt/sentence_generation_2015.txt'
p_2017='prompt/sentence_generation_2017.txt'
prompt_sentence_generation=p_2015
prompt_sentence_rephrase='prompt/sentence_rephase.txt'
prompt_aspect_extension='prompt/aspect_extension.txt'
prompt_filter='prompt/ai_filter.txt'
input_path='output/twitter_2015/13/origin_aspect.jsonl' 
arg={}
arg['year']="2017"
def ai_filter(prompt_path,input_path,output_path,type='normal'):
    '''利用大模型进行筛选生成的句子的质量'''
    data_list = []
    with open(input_path, 'r') as file:
        # 加载 JSONL 数据
        for line in file:
            data_list.append(json.loads(line))
    sentence_list=[]
    filter_num=len(data_list)
    i=0
    arg['type']='ai_filter'
    while i<len(data_list):
        chunk_size = min(8, len(data_list) - i)
        # 将'sentence'字段添加到sentence_list中
        sentence_list.extend([data['sentence'] for data in data_list[i:i+chunk_size]])
        extend_list=[]
        ppass=False
        while ppass==False:
            try:
                system_text,user_text = extract_prompt(prompt_path,get_variables(sentence_list,arg))
                str_=getfromOpenAI(system_text,user_text,model)
                extend_list=ast.literal_eval(str_)
                print(extend_list)
                ppass=True
                
            except Exception as e:
                print(e)
                ppass=False
                
        print(len(extend_list),chunk_size)
        min_=min(chunk_size,len(extend_list))
        #防止AI出现问题导致extend_list长度小于chunk_size
        for j in range(0,min_):
            data_list[i+j]['retain']=extend_list[j]
        for j in range(min_,chunk_size):
            data_list[i+j]['retain']=0

        i+=chunk_size
        sentence_list.clear()

    append_to_jsonl(output_path,data_list)

    log_str='过滤模式'+' '+'过滤数据条数：'+str(filter_num)
    record('log/run_log.txt',log_str)

def data_process(input_path,output_path):
    '''找到实体的位置和对句子划分为列表'''
    data_list = []
    with open(input_path, 'r') as file:
        # 加载 JSONL 数据
        for line in file:
            data = json.loads(line)
            data_list.append(data)
    new_data=[]
    for item in data_list:

        words=split_and_preserve_punctuation(item['sentence'])
        term_list=[]
        for term in item['aspects']:
            dict_={}
            new_term=split_and_preserve_punctuation(term['term'])
            dict_['term']=new_term
            dict_['polarity']=term['polarity']
            dict_['type']=term['type']
            term_list.append(dict_)
            
        # item['words']=words
        # item['aspects']=find_from2to(words,term_list)
        # item['aspect_num']=len(term_list)
        item['words']=words
        item['aspects']=find_from2to(words,term_list)
        if item['aspects']==[]:
            print('can not find term')
            continue
        item['opinions']=[{'term':[]}]
        #new_dict.update(item)
        item['aspects_num']=len(term_list)
        new_data.append(item)

    append_to_jsonl(output_path,new_data)
        
def sentence_generate(prompt_path,input_path,output_path,type='rephrase',test=False,extension_path=None):
    '''当type为rephase,启动改写生成,level1；当type为origin,启动原始生成,level2；当type为extension,启动扩展生成,level3'''
    data_list=[]
    image_id_list=[]
    if type=='rephrase':
        data_list = getDictFromJsonl(input_path)
        image_id_list = [data['image_id'] for data in data_list]
        #去掉data_list中image_id的元素
        for item in data_list:
            del item['image_id']
    elif type=='origin':
        data_list = reunite_set(input_path)
    elif type=='extension':
        data_list = get_aspects_from_extension(extension_path,input_path)
    
    print("生成模式：",type)
    print("数据条数：",len(data_list))
    
    #random.shuffle(data_list)
    #如果为测试模式，则只选择三条进行测试，否则至多100条数据进行测试
    if test:
        data_list=data_list[:20]
    
    arg['type']='rephrase'
    generate_sentence_list = []
    for index,item in enumerate(data_list):
        print(item)
        system_prompt,user_prompt = extract_prompt(prompt_path,get_variables(item,arg=arg))
        dict_=None
        while dict_ is None:
            #print(system_prompt)
            #print(user_prompt)
            generate_sentence=getfromOpenAI(system_prompt,user_prompt,model)
            dict_=safe_json_loads(generate_sentence)
            
        dict_['type']=type
        if type=='rephrase':
            dict_['image_id']=image_id_list[index]
        print(dict_)
        generate_sentence_list.append(dict_)
        
    
    append_to_jsonl(output_path,generate_sentence_list)
    log_str='生成模式：'+type+' '+'生成数据条数：'+str(len(generate_sentence_list))
    record('log/run_log.txt',log_str)
    
def aspect_extension(prompt_path,input_path,output_path,type='normal'):
    '''将原数据的实体集合作为输入，生成扩展的实体'''
    data_list=getDictFromJsonl(input_path)
    term_list=[]
    for index,item1 in enumerate(data_list):
        for item2 in item1['aspects']:
            term_list.append(item2['term'])

    random.shuffle(term_list)
    if type=='test':
        term_list=term_list[:10]
    else:
        term_list=term_list[:len(data_list)]

    print("数据条数：",len(term_list))
    arg['type']='extend'
    aspect_extension_list = []
    for index,item in enumerate(term_list):
        dict_={}
        system_text,user_text=extract_prompt(prompt_path,get_variables(item,arg=arg))
        
        str=getfromOpenAI(system_text,user_text,model)
        dict_['origin_term']=item
        print(dict_)
        
        try:
            extend_list=ast.literal_eval(str)
            dict_['aspects']=[]
            for i in extend_list:
                dict_['aspects'].append({'term':i})
            aspect_extension_list.append(dict_)
        except Exception as e:
            print(e)
            continue

    append_to_jsonl(output_path,aspect_extension_list)
        
def only_level1(input_path,output_dir):
    output_dir+='only_level1'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    before_filter_path=os.path.join(output_dir,'before_filter.jsonl')
    after_filter_path=os.path.join(output_dir,'after_filter.jsonl')
    
    #运行level1
    print("running first level1")
    sentence_generate(prompt_sentence_generation,input_path,before_filter_path,type='rephase')
    #运行level2
    print("running second level2")
    sentence_generate(prompt_sentence_generation,input_path,before_filter_path,type='rephase')
    #运行level3
    print("running third level3")
    sentence_generate(prompt_sentence_generation,input_path,before_filter_path,type='rephase')
    #filter
    ai_filter(prompt_filter,input_path=before_filter_path,output_path=after_filter_path,type='normal')
    os.remove(before_filter_path)

def only_level2(input_path,output_dir):
    output_dir+='only_level2'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    before_filter_path=os.path.join(output_dir,'before_filter.jsonl')
    after_filter_path=os.path.join(output_dir,'after_filter.jsonl')
    # #运行level2
    # print("running first level2")
    # sentence_generate(prompt_sentence_generation,input_path,before_filter_path,type='origin')
    # #运行level2
    # print("running second level2")
    # sentence_generate(prompt_sentence_generation,input_path,before_filter_path,type='origin')
    #运行level2
    print("running third level2")
    sentence_generate(prompt_sentence_generation,input_path,before_filter_path,type='origin')
    #filter
    ai_filter(prompt_filter,input_path=before_filter_path,output_path=after_filter_path,type='normal')
    os.remove(before_filter_path)

def only_level3(input_path,output_dir):
    output_dir+='only_level3'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    before_filter_path=os.path.join(output_dir,'before_filter.jsonl')
    after_filter_path=os.path.join(output_dir,'after_filter.jsonl')
    aspect_extension_path=os.path.join(output_dir,'aspect_extension.jsonl')
    #运行level3
    print("running first level3")
    aspect_extension(prompt_aspect_extension,input_path,aspect_extension_path,type='normal')
    sentence_generate(prompt_sentence_generation,input_path,before_filter_path,type='extension',test=False,
    extension_path=aspect_extension_path)
    os.remove(aspect_extension_path)
    #运行level3
    print("running second level3")
    aspect_extension(prompt_aspect_extension,input_path,aspect_extension_path,type='normal')
    sentence_generate(prompt_sentence_generation,input_path,before_filter_path,type='extension',test=False,
    extension_path=aspect_extension_path)
    os.remove(aspect_extension_path)
    #运行level3
    print("running third level3")
    aspect_extension(prompt_aspect_extension,input_path,aspect_extension_path,type='normal')
    sentence_generate(prompt_sentence_generation,input_path,before_filter_path,type='extension',test=False,
    extension_path=aspect_extension_path)
    os.remove(aspect_extension_path)
    #filter
    ai_filter(prompt_filter,input_path=before_filter_path,output_path=after_filter_path,type='normal')
    os.remove(before_filter_path)

def muti_levels(input_path,output_dir):
    #output_dir+='muti_level'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    before_filter_path=os.path.join(output_dir,'before_filter.jsonl')
    after_filter_path=os.path.join(output_dir,'after_filter.jsonl')
    aspect_extension_path=os.path.join(output_dir,'aspect_extension.jsonl')
    
    #运行level1
    print("running level1")
    sentence_generate(prompt_sentence_rephrase,input_path,before_filter_path,type='rephrase',test=False)
    sentence_generate(prompt_sentence_rephrase,input_path,before_filter_path,type='rephrase',test=False)
    #运行level2
    print("running level2")
    sentence_generate(prompt_sentence_generation,input_path,before_filter_path,type='origin',test=False)
    sentence_generate(prompt_sentence_generation,input_path,before_filter_path,type='origin',test=False)
    sentence_generate(prompt_sentence_generation,input_path,before_filter_path,type='origin',test=False)
    #运行level3
    print("running level3")
    for i in range(1):
        aspect_extension(prompt_aspect_extension,input_path,aspect_extension_path,type='normal')
        sentence_generate(prompt_sentence_generation,input_path,before_filter_path,type='extension',test=False,
        extension_path=aspect_extension_path)
        #filter
        os.remove(aspect_extension_path)

    ai_filter(prompt_filter,input_path=before_filter_path,output_path=after_filter_path,type='normal')
    os.remove(before_filter_path)

if __name__ == '__main__':

    '''看一眼prompt的路径有没有对!!!'''
    prompt_sentence_generation=p_2015
    input_path='output/twitter_2015/13/origin_data.jsonl'
    output_dir='output/twitter_2015/13/'
    #prompt_sentence_generation='15'
    muti_levels(input_path,output_dir)
    #only_level1(input_path,output_dir)
    input_path='output/twitter_2015/13/origin_data.jsonl'
    output_path='output/twitter_2015/13/test_rephrase.jsonl'

    #sentence_generate(prompt_sentence_rephrase,input_path,output_path,type='rephrase',test=True)
    #aspects_extract(input_path,output_path)
    # input_path2='data/twitter_2017/100/origin_aspect.json'
    # output_path='output/twitter_2017/100/test_aspect.jsonl'
    # output_path='output/twitter_2017/100/before_.jsonl'
    # #sentence_generate(prompt_sentence_generation,input_path2,output_path,type='rephase')
    # input_path='output/twitter_2015/13/add_image.jsonl'
    # output_path='output/twitter_2015/13/after_filter.jsonl'
    # output_path1='output/twitter_2015/13/after_filter_w.jsonl'
    # #data_process(output_path,output_path1)
    # data=getDictFromJsonl(output_path1)
    # print_len_words(data)

    # for image in image_name_list:
    #     if image not in image_list:
    #         os.remove(os.path.join(image_folder,image))

    # data1=getDictFromJsonl('output/twitter_2017/87/origin_aspect.jsonl')
    # data2=getDictFromJsonl('output/twitter_2017/42/origin_aspect.jsonl')
    # data3=getDictFromJsonl('output/twitter_2017/100/origin_aspect.jsonl')

            
    # before_filter_path=os.path.join(output_dir,'only_level2/before_filter.jsonl')
    # after_filter_path=os.path.join(output_dir,'only_level2/after_filter.jsonl')
    #ai_filter(prompt_filter,input_path=before_filter_path,output_path=after_filter_path,type='normal')
    # input_path='data/twitter_2015/13/train.json'
    # output_path='origin_data.jsonl'
    # with open(input_path,'r') as f:
    #     data=json.load(f)

    # append_to_jsonl(output_path,data)
    


        