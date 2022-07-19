import os
import math
import json
import torch
from seudo.process.utils import CTA
from seudo.process.utils.alphaSparql import MySPARQL
from seudo.process.utils.hiercolnet import HiercolClassifier
from transformers import BertTokenizer, BertModel, BertForMaskedLM
from django.shortcuts import get_object_or_404
from seudotable.models import Table,TableData,TableSearch, GlobalStatusEnum

def scan_folder(directory, prefix=None, postfix=None):
    files_list = []
    #os.chdir(os.path.abspath(os.path.join(os.path.dirname("__file__"),os.path.pardir))) #进入上一级目录
    for root, sub_dirs, files in os.walk(directory):
        for special_file in files:
            if postfix:
                if special_file.endswith(postfix):
                    files_list.append(os.path.join(root, special_file))
            elif prefix:
                if special_file.startswith(prefix):
                    files_list.append(os.path.join(root, special_file))
            else:
                files_list.append(os.path.join(root, special_file))
    return files_list

def get_finals(cell):
    if not cell:
        return -1

    sums=(cell["bs"]+cell["ds"])/3
    return 1/(1+math.exp(-sums))

def generate_answer(table):
    bert_tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    # Load pre-trained model (weights)
    bert_model = BertModel.from_pretrained('bert-base-uncased',
                                      output_hidden_states=True,)  # Whether the model returns all hidden-states.
    # Put the model in "evaluation" mode, meaning feed-forward operation.
    bert_model.eval()

    model=HiercolClassifier()
    model.load_state_dict(torch.load("seudo/private/model/128_hcol_state.pth"))
    model.eval()

    data_ans=[]

    table_search=TableSearch.objects.get(table=table)
    for row in range(table.num_rows):
        row_ans=[]
        for col in table.ne_cols:
            direct_cell=table_search.direct_dbp[str(row)][str(col)]
            seudo_cell_list=table_search.seudo_dbp[str(row)][str(col)]

            hconf=get_finals(direct_cell)
            cell_ans = [direct_cell["url"]]

            # if direct_cell["fix"]:
            #     hconf=1
            for cell in seudo_cell_list:
                if get_finals(cell)>hconf:
                    cell_ans=[cell["url"]]
                if get_finals(cell)==hconf:
                    cell_ans.append(cell["url"])
            row_ans.append(cell_ans)
        data_ans.append(row_ans)


    type_dict=table_search.type_dict
    ratio_type_dict={}
    for col in type_dict.keys():
        for type in type_dict[col].keys():
            try:
                temp=ratio_type_dict[str(col)]
            except:
                ratio_type_dict[str(col)]={}
            ratio_type_dict[col][type]=type_dict[col][type]/table.num_rows

    col_ans={}
    for col in table.ne_cols:
        input, ans_cands=build_input(bert_tokenizer, bert_model, ratio_type_dict[str(col)])
        logits = model(input)
        squeezed_logits = torch.squeeze(logits, dim=-1)
        arg = torch.argmax(squeezed_logits, dim=-1)
        col_ans[col] = ans_cands[arg]

    filename=table.file_name
    fl_path = './seudo/private/res/'+os.path.splitext(filename)[0] +".json"

    with open(fl_path, 'w', encoding='utf-8') as json_file:
        json.dump({"col": col_ans, "data": data_ans}, json_file, ensure_ascii=False)
        print("write json file success!")

    return fl_path

def num_query():
    context={}
    tables_count = Table.objects.count()
    tables_completed_count = Table.objects.filter(global_status=GlobalStatusEnum.DONE.value).count()
    tables_in_progress_count = Table.objects.filter(global_status=GlobalStatusEnum.DOING.value).count()
    context['tables_count'] = tables_count
    context['tables_completed']= tables_completed_count
    context['tables_in_progress'] = tables_in_progress_count
    return context

def context_query(table,table_data):
    context={}
    context['table'] = table
    context['table_datas'] = table_data.data
    context['ne_cols'] = table.ne_cols
    context['no_ann_cols'] = table.no_ann_cols
    return context

def all_query(table_id):
    table = get_object_or_404(Table, id=table_id)
    table_data = TableData.objects.get(table=table)
    table_search = TableSearch.objects.get(table=table)
    context = context_query(table,table_data)

    return table,table_data,table_search,context

def link_query(data, table, table_search):
    for row in range(table.num_rows):
        for col in table.ne_cols:
            cell = table_search.direct_dbp[str(row)][str(col)]
            temp_target, score = None, 0
            if cell:
                if get_finals(cell)>score:
                    temp_target, score = cell, get_finals(cell)
                try:
                    cands=table_search.seudo_dbp[str(row)][str(col)]
                    if cands:
                        for cand in cands:
                            if get_finals(cand) > score:
                                temp_target, score = cand, get_finals(cand)
                except:
                    pass
            if temp_target:
                data[row][col]=data[row][col]+"<br>"+ "<a href=\"%s\" class='res_hyperlink' target='_BLANK'>%s</a>" % (temp_target["url"], temp_target["url"]) + " <em style='color: black'>%.4f</em>" % get_finals(temp_target)
    return data

def build_input(bert_tokenizer, model, type_dict):
    sparql=MySPARQL("http://dbpedia.org/sparql")

    sta_list=[]
    for type in type_dict.keys():
        try:
            sta_list.append([type, type_dict[type]])
        except:
            sta_list.append([type, 1])

    sta_list.sort(key=lambda x: x[1], reverse=True)

    res,exclu=CTA.generate_miniontology(type_dict)
    layer_dict={}
    for item in res:
        layer_dict[item[0]]=item[1]

    input = None
    ans_cands=[]
    for ele in sta_list:
        if ele[0] not in exclu:
            if ele[0] == "http://www.w3.org/2002/07/owl#Thing":
                words = "[CLS] " + "Thing" + " [SEP]"
            else:
                words = "[CLS] " + sparql.get_label(ele[0]) + " [SEP]"

            words = bert_tokenizer.tokenize(words)
            indexed_tokens = bert_tokenizer.convert_tokens_to_ids(words)
            segments_ids = [1] * len(words)
            tokens_tensor = torch.tensor([indexed_tokens])
            segments_tensors = torch.tensor([segments_ids])
            hidden_states = model(tokens_tensor, segments_tensors)[2]
            token_vecs = hidden_states[-2][0]
            semantic_embed = torch.mean(token_vecs, dim=0)
            conf = ele[1]
            layer = None
            for l in layer_dict.keys():
                if ele[0] in layer_dict[l]:
                    layer = l

            if not layer:
                continue

            embed = torch.cat((semantic_embed.unsqueeze(0), torch.tensor([conf, layer]).unsqueeze(0)), -1)

            if input == None:
                input = embed
            else:
                input = torch.cat((input, embed))

            ans_cands.append(ele[0])
        if len(ans_cands) == 8:
            break

    while len(ans_cands) < 8:
        for ele in sta_list:
            if ele[0] not in exclu:
                if ele[0] == "http://www.w3.org/2002/07/owl#Thing":
                    words = "[CLS] " + "Thing" + " [SEP]"
                else:
                    words = "[CLS] " + ele[0].split("/")[-1] + " [SEP]"

                words = bert_tokenizer.tokenize(words)
                indexed_tokens = bert_tokenizer.convert_tokens_to_ids(words)
                segments_ids = [1] * len(words)
                tokens_tensor = torch.tensor([indexed_tokens])
                segments_tensors = torch.tensor([segments_ids])
                hidden_states = model(tokens_tensor, segments_tensors)[2]
                token_vecs = hidden_states[-2][0]
                semantic_embed = torch.mean(token_vecs, dim=0)

                conf = ele[1]
                layer = None

                for l in layer_dict.keys():
                    if ele[0] in layer_dict[l]:
                        layer = l

                if not layer:
                    continue

                embed = torch.cat((semantic_embed.unsqueeze(0), torch.tensor([conf, layer]).unsqueeze(0)), -1)

                if input == None:
                    input = embed
                else:
                    input = torch.cat((input, embed))

                ans_cands.append(ele[0])
            if len(ans_cands) == 8:
                break
    return input.unsqueeze(0), ans_cands
