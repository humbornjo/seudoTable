import copy

from datetime import datetime
from django.shortcuts import get_object_or_404
from seudotable.models import Table, TableData, TableSearch, GlobalStatusEnum

def check_table(file_name):
    assert (len(file_name) > 0)
    res=Table.objects.filter(file_name=file_name)
    if res:
        return False
    else:
        return True

def load_table(file_name, content):
    assert (len(file_name) > 0)
    assert (len(content) > 0)

    header = content[0]


    table = Table(
        file_name=file_name,
        header=header,
        num_cols=len(content[0]),
        num_rows=len(content)-1
        #process=process
    )
    table.save()

    datas = content[1:]

    TableData(
        table=table,
        header=header,
        data_original=datas,
        data=datas,
    ).save()

    TableSearch(table=table).save()

def update_table(table_id,
                 ne_cols=None,
                 global_status =None):
    table = get_object_or_404(Table, id=table_id)
    table.last_edit_date = datetime.now()
    if ne_cols:
        ori_ne_cols=table.ne_cols
        if ori_ne_cols!=ne_cols:
            no_ann_cols = list(set([i for i in range(len(table.header))]) - set(ne_cols))
            table.ne_cols=ne_cols
            table.no_ann_cols=no_ann_cols
            reset_search=True
    if global_status:
        table.global_status=global_status

    table.save()

def update_search(table_search, direct_res=None, direct_dbp=None, seudo_res=None, seudo_dbp=None, history_wiki=None, history_dbp=None, type_dict=None):
    if direct_res:
        table_search.direct_res=direct_res
    if direct_dbp:
        table_search.direct_dbp=direct_dbp
    if seudo_res:
        table_search.seudo_res=seudo_res
    if seudo_dbp:
        table_search.seudo_dbp=seudo_dbp
    if history_wiki:
        table_search.history_wiki=history_wiki
    if history_dbp:
        table_search.history_dbp=history_dbp
    if type_dict:
        table_search.type_dict=type_dict
    # table.last_edit_date=datetime.now()
    table_search.save()
    # table.save()

def table_reset(table_id):
    table = get_object_or_404(Table, id=table_id)
    table_search= TableSearch.objects.get(table=table)
    table_data= TableData.objects.get(table=table)

    table.global_status=GlobalStatusEnum.TODO.value
    table.ne_cols = []
    table.no_ann_cols = []
    table.last_edit_date = datetime.now()
    table.save()

    table_search.direct_res={}
    table_search.direct_dbp={}
    table_search.seudo_res={}
    table_search.seudo_dbp={}
    table_search.type_dict={}
    table_search.step_num=1
    table_search.save()

    table_data.cands={}
    table_data.data=copy.deepcopy(table_data.data_original)
    table_data.save()

