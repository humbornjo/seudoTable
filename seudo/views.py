import mimetypes
import copy
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from seudo.process.utils import importer,CEA,CTA
from seudo.process.utils.utils import *
from seudo.process import wikitool
import seudo.process.utils.alphaSparql as aSparql
from urllib.parse import unquote

sparql=aSparql.MySPARQL("http://dbpedia.org/sparql")

import os, csv

##################### util func ##########################

def query_direct_wiki(target_cell, history_wiki):
    try:
        res = history_wiki["direct"][target_cell]
    except:
        res = wikitool.wiki_suggest(target_cell)
        history_wiki["direct"][target_cell] = res

    return res, history_wiki

def query_seudo_wiki(target_cell, history_wiki):
    try:
        res = history_wiki["seudo"][target_cell]
    except:

        res = wikitool.wiki_search(target_cell)
        history_wiki["seudo"][target_cell] = res

    return res, history_wiki

def query_wiki2db_fullbase(wiki_url, history_dbp):
    try:
        dbp_search = history_dbp["wiki2db"][wiki_url]
        # NOTE: Cell dbpedia Exist 1. None 2. not None
    except:
        dbp_search = sparql.get_wiki2db(wiki_url)
        if dbp_search:
            history_dbp["wiki2db"][wiki_url] = dbp_search
            history_dbp["label"][dbp_search] = sparql.get_label(dbp_search)
            history_dbp["type"][dbp_search] = sparql.get_type(dbp_search)
            history_dbp["abstract"][dbp_search] = sparql.get_abstract(dbp_search)

    return dbp_search, history_dbp

def query_db_fullbase(db_url, history_dbp):
    try:
        temp = history_dbp["label"][db_url]
    except:
        history_dbp["label"][db_url] = sparql.get_label(db_url)
        history_dbp["type"][db_url] = sparql.get_type(db_url)
        history_dbp["abstract"][db_url] = sparql.get_abstract(db_url)

    return history_dbp


def cell_sidebar(row_idx,col_idx,table,table_data):
    key_coords = "row" + str(row_idx) + "col" + str(col_idx)
    return {
        "cell_title": table_data.data_original[row_idx][col_idx],
        "cell_header": table.header[col_idx],
        "cell_row_coord": row_idx + 1,
        "cell_col_coord": col_idx + 1,
    }

def header_sidebar(col_idx,table,table_search):
    if col_idx not in table.ne_cols:
        return {"type_title": table.header[col_idx]}
    history_dbp=table_search.history_dbp
    type_dict=table_search.type_dict
    col=str(col_idx)
    total_num = 0
    for type in type_dict[col].keys():
        total_num+=type_dict[col][type]
    ratio_type_list=[]
    for type in type_dict[col].keys():
        try:
            label=history_dbp["label"][type]
        except:
            label=sparql.get_label(type)
            history_dbp["label"][type]=label
        conf = type_dict[col][type]/total_num
        if not label:
            label=os.path.basename(type).lower()
        ratio_type_list.append({"label": label,"url": type, "conf": "%.4f" % conf})
    importer.update_search(table_search=table_search, history_dbp=history_dbp)
    ratio_type_list.sort(reverse=True, key = lambda x:x["conf"])
    candidate=ratio_type_list[:3]

    return {
        "type_title": table.header[col_idx],
        "candidate": candidate
    }

def direct_sidebar(right_sidebar,key_coords,table_search,cell_wiki,cell_dbp):
    if cell_dbp:
        label, url, conf = table_search.history_dbp["label"][cell_dbp["url"]], cell_dbp["url"], "%.4f" % get_finals(cell_dbp)
    else:
        label, url, conf = cell_wiki["label"], cell_wiki["url"], -1

    right_sidebar[key_coords]["direct_res"] = {"label": label, "url": url, "conf": conf}
    right_sidebar[key_coords]["step_1"] = "True"

    return right_sidebar

def seudo_sidebar(right_sidebar,key_coords,table_search,cell_dbp):
    cand_sidebar = []

    target_cand_list = cell_dbp

    for cand in target_cand_list:
        label = table_search.history_dbp["label"][cand["url"]]
        cand_sidebar.append({"label": label, "url": cand["url"], "conf": "%.4f" % get_finals(cand)})
    right_sidebar[key_coords]["step_2"] = "True"
    right_sidebar[key_coords]["candidate"] = cand_sidebar

    return right_sidebar
######################### main part ###############################
def home(request):
    return render(request, 'seudo/home.html')

def upload(request):
    context = num_query()

    # Create your views here.
    if request.method == "POST":
        File = request.FILES.get("files", None)
        if File is None:
            context['iffile']=False
            table_list=Table.objects.order_by('pub_date')
            context['tables']=table_list

            return render(request, 'seudo/upload.html', context)
        else:
            context['iffile'] = True
            file_name = request.FILES['files'].name
            data=File.read().decode("utf-8").splitlines()
            try:
                csv_reader=list(csv.reader(data))
            except:
                context['valid'] = False
                table_list = Table.objects.order_by('pub_date')
                context['tables'] = table_list

                return render(request, 'seudo/upload.html', context)

            if importer.check_table(file_name=file_name):
                context['last_upload'] = None
                importer.load_table( file_name, csv_reader)
                table_list=Table.objects.order_by('pub_date')
                context['tables']=table_list
                context['tables_count']+=1
                return render(request, 'seudo/upload.html', context)

            else:
                context['last_upload']=file_name
                table_list=Table.objects.order_by('pub_date')
                context['tables']=table_list
                return render(request, 'seudo/upload.html', context)
    else:
        table_list = Table.objects.order_by('pub_date')
        context['tables'] = table_list

        return render(request, 'seudo/upload.html', context)

def download(request, table_id):
    table = get_object_or_404(Table, id=table_id)

    fl_path=generate_answer(table)

    fl = open(fl_path, 'r')
    mime_type, _ = mimetypes.guess_type(fl_path)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % (os.path.basename(fl_path))
    return response

def workspace(request):
    context = num_query()

    return render(request, 'seudo/base-dashboard.html', context)

def tablist(request):
    context = num_query()
    table_list = Table.objects.order_by('pub_date')
    search_filter_param = request.GET.get("search", "")

    if request.is_ajax():
        if search_filter_param != "":
            table_list = table_list.filter(file_name__icontains=search_filter_param)
            context['tables'] = table_list
        else:
            context['tables'] = table_list
        table_list_html = render_to_string(
            template_name="seudo/table_search.html",
            context=context
        )
        data = {
            "table_list_html": table_list_html,
        }

        return JsonResponse(data=data, safe=False)

    context['tables'] = table_list
    return render(request, 'seudo/table_list.html', context)

def export(request):
    context = num_query()

    table_list = Table.objects.order_by('pub_date')
    context['tables'] = table_list

    return render(request, 'seudo/export.html', context)

def aboutus(request):
    context = num_query()

    return render(request, 'seudo/aboutus.html', context)

# PROCESS
def neCols_select(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    table_data = TableData.objects.get(table=table)

    context = {
        'table': table,
        'table_datas': table_data.data_original,
    }

    if table.ne_cols:
        context['ne_cols']=table.ne_cols
        context['no_ann_cols']=table.no_ann_cols

    return render(request, 'seudo/process/choose_col.html', context)

# NOTE: check the validation of selected neCols
# and store the Table info into the local database
def check_neCols(request):
    ne_cols=json.loads(request.POST.get('neCols'))
    table_id= int(request.POST.get("tableId"))
    if ne_cols:
        table = get_object_or_404(Table, id=table_id)

        table.ne_cols=ne_cols

        importer.update_table(table_id=table_id,
                              ne_cols=ne_cols,
                              global_status = GlobalStatusEnum.DOING.value)

        return JsonResponse({"res": 1})
    else:
        return JsonResponse({"res": 0})

def reset(request, table_id):
    importer.table_reset(table_id)
    table = get_object_or_404(Table, id=table_id)
    table_data = TableData.objects.get(table=table)

    context = {
        'table': table,
        'table_datas': table_data.data_original,
    }

    if table.ne_cols:
        context['ne_cols']=table.ne_cols
        context['no_ann_cols']=table.no_ann_cols

    return render(request, 'seudo/process/choose_col.html', context)

# NOTE: There might be a simpler and more efficient way to describe direct_search
# but i will stop here for now
def direct_search(request, table_id):
    table ,table_data ,table_search ,context = all_query(table_id)
    increment={}
    if not table_data.cands:
        for row in range(table.num_rows):
            table_data.cands[str(row)] = {}
            for col in table.ne_cols:
                table_data.cands[str(row)][str(col)]=[]

    search=True
    if table_search.direct_dbp:
        search=False

    if search:
        for col in table.ne_cols:
            increment[col]=[]

        direct_wiki, direct_dbp= table_search.direct_res, table_search.direct_dbp
        history_wiki, history_dbp = table_search.history_wiki, table_search.history_dbp

        for row in range(table.num_rows):
            row_direct_wiki, row_direct_dbp={},{}
            for col in table.ne_cols:
                target_cell=table_data.data_original[row][col]
                temp_wiki, history_wiki = query_direct_wiki(target_cell, history_wiki)
                print(temp_wiki)
                if temp_wiki:
                    row_direct_wiki[str(col)]= temp_wiki

                    dbp_search,history_dbp=query_wiki2db_fullbase(unquote(temp_wiki["url"]),history_dbp)
                    if dbp_search:
                        row_direct_dbp[str(col)] = {"url": dbp_search, "bs": -1, "ds": -1, "fix": 0}
                        table_data.cands[str(row)][str(col)].append(dbp_search)
                        increment[col].append(dbp_search)
                    else:
                        row_direct_dbp[str(col)] = {}

                else:
                    row_direct_wiki[str(col)], row_direct_dbp[str(col)]= {}, {}

            direct_wiki[str(row)], direct_dbp[str(row)] = row_direct_wiki, row_direct_dbp
        direct_dbp = CEA.bs_cell_confidence(table_data.data_original, table_search.direct_dbp,
                                            table_search.history_dbp,
                                            table.num_rows, table.ne_cols)
        res_dict = table_search.type_dict  ###table_search.type_dict
        type_dict = CTA.statistic_type(table, increment, table_search.history_dbp, res_dict)
        direct_dbp = CTA.ds_cell_confidence(table, direct_dbp, table_search.history_dbp, type_dict,table_data.cands)

            # importer.update_search(table_search=table_search,direct_res=direct_wiki,direct_dbp=direct_dbp,
            #                        history_wiki=history_wiki,history_dbp=history_dbp)
        table_search.type_dict=type_dict
        table_search.direct_dbp=direct_dbp
        table_search.direct_res=direct_wiki
        table_search.history_dbp=history_dbp
        table_search.history_wiki=history_wiki
        table_search.save()

    if table.global_status != GlobalStatusEnum.TODO.value:
        right_sidebar = {}
        for col_idx in range(table.num_cols):
            key_coords = "col" + str(col_idx)
            right_sidebar[key_coords] = header_sidebar(col_idx, table, table_search)
            for row_idx in range(table.num_rows):
                key_coords = "row" + str(row_idx) + "col" + str(col_idx)
                right_sidebar[key_coords] = cell_sidebar(row_idx,col_idx,table,table_data)

                if col_idx in table.ne_cols:
                    cell_wiki = table_search.direct_res[str(row_idx)][str(col_idx)]
                    cell_dbp = table_search.direct_dbp[str(row_idx)][str(col_idx)]
                    right_sidebar=direct_sidebar(right_sidebar,key_coords,table_search,cell_wiki,cell_dbp)
        context['right_sidebar'] = right_sidebar
    data=copy.deepcopy(table_data.data_original)
    data=link_query(data,table,table_search)
    table_data.data=data
    table_data.save()
    context["table_datas"]=data
    return render(request, 'seudo/process/direct_search.html', context)

def seudo_search(request, table_id):
    table ,table_data ,table_search ,context = all_query(table_id)
    right_sidebar = {}

    seudo_dbp=table_search.seudo_dbp
    if not seudo_dbp:
        for row in range(table.num_rows):
            seudo_dbp[str(row)] = {}
            for col in table.ne_cols:
                seudo_dbp[str(row)][str(col)]=[]

    increment={}

    search=True
    if table_search.step_num>2:
        search=False

    if search:
        for col in table.ne_cols:
            increment[col]=[]
        seudo_wiki = {}

        history_wiki, history_dbp, type_dict = table_search.history_wiki, table_search.history_dbp, table_search.type_dict

        layer={}
        e={}
        for col in table.ne_cols:
            layer_list, equ = CTA.generate_miniontology(table_search.type_dict[str(col)])
            layer[col]=layer_list
            e[col]=equ
        print(layer)
        for row in range(table.num_rows):
            row_seudo_wiki, row_seudo_dbp={},{}
            for col in table.ne_cols:

                target_cell=table_data.data_original[row][col]
                fix=None
                if table_search.step_num==1:
                    sub_type, sub_count = None, 0
                    for type in layer[col][-1][1]:
                        if type in e[col]:
                            continue
                        if table_search.type_dict[str(col)][type] > sub_count:
                            sub_type, sub_count = type, table_search.type_dict[str(col)][type]
                    fix=-1
                    print(sub_type)
                    cands=sparql.get_seudocand(target_cell,sub_type)
                elif  table_search.step_num==2:
                    sub_type, sub_count = None, 0
                    for type in layer[col][-1][1]:
                        if type in e[col]:
                            continue
                        if table_search.type_dict[str(col)][type] > sub_count:
                            sub_type, sub_count = type, table_search.type_dict[str(col)][type]
                    fix=1
                    print(sub_type)
                    cands=sparql.get_seudodisam(target_cell,sub_type)
                else:
                    cands, history_wiki = query_seudo_wiki(target_cell,history_wiki)
                    temp_cands=[]
                    ## cands: [{"label":page.title,"url":page.url}, {"label":page.title,"url":page.url}, ...]
                    if cands:
                        row_seudo_wiki[str(col)] = cands
                        #cell_seudo_dbp=[]

                        for cand in cands:
                            dbp_search,history_dbp=query_wiki2db_fullbase(unquote(cand["url"]),history_dbp)
                            if dbp_search:
                                temp_cands.append(dbp_search)
                                if table_search.direct_dbp[str(row)][str(col)]:
                                    if dbp_search == table_search.direct_dbp[str(row)][str(col)]["url"]:
                                        continue

                                #cell_seudo_dbp.append({"url": dbp_search, "bs": -1, "ds": -1, "fix": 0})
                        #row_seudo_dbp[str(col)] = cell_seudo_dbp
                    else:
                        row_seudo_wiki[str(col)]= []
                        #row_seudo_dbp[str(col)] = []
                    seudo_wiki[str(row)] = row_seudo_wiki
                    #seudo_dbp[str(row)] = row_seudo_dbp
                    cands=temp_cands
                print(cands)
                for cand in cands:
                    if cand in table_data.cands[str(row)][str(col)]:
                        continue
                    else:
                        seudo_dbp[str(row)][str(col)].append({"url": cand, "bs": -1, "ds": -1, "fix": fix})
                        history_dbp=query_db_fullbase(cand,history_dbp)
                        table_data.cands[str(row)][str(col)].append(cand)
                        increment[col].append(cand)
        table_search.type_dict=type_dict
        table_search.seudo_dbp=seudo_dbp
        table_search.history_dbp=history_dbp
        table_search.history_wiki=history_wiki
        table_search.save()

        table_data.save()

    table_search=TableSearch.objects.get(table=table)

    type_dict = table_search.type_dict

    type_dict = CTA.statistic_type(table, increment, table_search.history_dbp, type_dict)

    if search:
        seudo_dbp = CEA.bs_cell_confidence(table_data.data_original, table_search.seudo_dbp,
                                           table_search.history_dbp,
                                           table.num_rows, table.ne_cols)
        direct_dbp=CTA.ds_cell_confidence(table, table_search.direct_dbp,table_search.history_dbp,type_dict,table_data.cands)
        seudo_dbp=CTA.ds_cell_confidence(table, seudo_dbp,table_search.history_dbp,type_dict,table_data.cands)

        table_search.type_dict=type_dict
        table_search.seudo_dbp=seudo_dbp
        table_search.direct_dbp=direct_dbp
        table_search.save()

        # importer.update_search(table_id=table_id, direct_dbp=direct_dbp, seudo_dbp=seudo_dbp,type_dict=type_dict)
        table_search=TableSearch.objects.get(table=table)

    for col_idx in range(table.num_cols):
        key_coords = "col" + str(col_idx)
        right_sidebar[key_coords] = header_sidebar(col_idx, table, table_search)

        for row_idx in range(table.num_rows):
            key_coords = "row" + str(row_idx) + "col" + str(col_idx)
            right_sidebar[key_coords] = cell_sidebar(row_idx,col_idx,table,table_data)

            if col_idx in table.ne_cols:
                cell_wiki = table_search.direct_res[str(row_idx)][str(col_idx)]
                cell_dbp = table_search.direct_dbp[str(row_idx)][str(col_idx)]
                right_sidebar = direct_sidebar(right_sidebar, key_coords, table_search, cell_wiki, cell_dbp)
                ## seudo result
                cell_dbp=table_search.seudo_dbp[str(row_idx)][str(col_idx)]
                right_sidebar = seudo_sidebar(right_sidebar, key_coords, table_search, cell_dbp)

    context['right_sidebar'], context['step_num'] = right_sidebar, table_search.step_num

    table.global_status=GlobalStatusEnum.DONE.value
    table.save()

    if table_search.step_num>=3:
        context['finish']='True'
    else:
        table_search.step_num+=1
        table_search.save()
    data=copy.deepcopy(table_data.data_original)
    data=link_query(data,table,table_search)
    table_data.data=data
    table_data.save()
    context["table_datas"]=data
    print(table_search.seudo_dbp)
    return render(request, 'seudo/process/seudo_search.html', context)
