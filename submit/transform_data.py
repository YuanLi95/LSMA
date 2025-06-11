import json
from utils import *
def json_to_txt(json_file, txt_file):
    data_list=getDictFromJsonl(json_file)
    out_put_list=[]
    for data in data_list:
        if "retain" in data.keys() and data["retain"]==0:
            continue

        words = [word.lower() for word in data.get("words", [])]  # 转化为小写
        text=" ".join(words)
        tags=["O"]*len(words)
        for aspect in data.get("aspects",[]):
            term=aspect.get("term",[])
            polarity=aspect.get("polarity","O")
            start=aspect.get("from",0)
            end=aspect.get("to",0)
            if term:
                tags[start]=f"T-{polarity}-B"
                for i in range(start+1,end):
                    tags[i]=f"T-{polarity}"

        annotated_text=" ".join([f"{word}={tag}" for word,tag in zip(words,tags)])

        image_indices=[0 for i in range(16)]
        image_ids=[data.get("image_id")]
        out_put_list.append(f"{text}####{annotated_text} ____image={image_indices}____image_ids={image_ids}\n")
    with open(txt_file,'w',encoding='utf-8') as f:
        f.writelines(out_put_list)

def findAnotherRealData(input_path,set_path, output_path):
    data_list=getDictFromJsonl(input_path)
    set_list=getDictFromJsonl(set_path)
    output_list=[]
    image_list=[item['image_id'] for item in data_list]
    for item in set_list:
        if item['image_id'] not in image_list:
            output_list.append(item)

    append_to_jsonl(output_path,output_list)
    

def main():
    # json_file = "dataReal/2015/train_13.jsonl"  # Replace with your JSONL file path
    # txt_file = "dataForJML/real/2015/train_13.txt"    # Replace with your desired TXT file path
    # json_to_txt(json_file, txt_file)

    input_path1='data/twitter_2017/100/train.json'
    input_path2='data/twitter_2017/100/test.json'
    input_path3='output/twitter_2017/100/train.jsonl'

    data1=getDictFromJsonl(input_path1)
    data2=getDictFromJsonl(input_path2)
    data3=getDictFromJsonl(input_path3)
    temp_data=[]
    for item in data3:
        if 'retain' in item.keys() and item['retain']==0:
            continue
        temp_data.append(item)
    term_list1=[]
    term_list2=[]
    num=int(len(data1)*2.5)
    data1.extend(random.sample(temp_data,min(len(temp_data),num)))
    print(len(data1))
    for item in data1:
        for item1 in item['aspects']:
            term_list1.append(item1['term'])

    for item in data2:
        for item1 in item['aspects']:
            term_list2.append(item1['term'])

    num=0
    for item in term_list2:
        if item in term_list1:
            num+=1

    print(num)
    print(len(term_list2)) 
    print(len(term_list1))  




if __name__ == "__main__":
    main()

