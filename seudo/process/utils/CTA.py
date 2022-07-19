from seudo.process.utils.alphaSparql import MySPARQL

def statistic_seudo_type(table, seudo_dbp , history_dbp, step_num, res_dict):
    for row in range(table.num_rows):
        for col in table.ne_cols:
            try:
                new_cand=seudo_dbp[str(row)][str(col)][step_num-1]
                for type in history_dbp["type"][new_cand["url"]]:
                    try:
                        res_dict[str(col)][type] += 1
                    except:
                        res_dict[str(col)][type] = 1
            except:
                pass

    return res_dict

def statistic_direct_type(table, direct_dbp , history_dbp, res_dict):
    for row in range(table.num_rows):
        for col in table.ne_cols:
            try:
                temp=res_dict[str(col)]
            except:
                res_dict[str(col)]={}
            cell= direct_dbp[str(row)][str(col)]
            if cell:
                for type in history_dbp["type"][cell["url"]]:
                    try:
                        res_dict[str(col)][type] += 1
                    except:
                        res_dict[str(col)][type] = 1

    return res_dict

def statistic_type(table, increment , history_dbp, res_dict):
    if not increment:
        return res_dict
    for col in table.ne_cols:
        try:
            temp = res_dict[str(col)]
        except:
            res_dict[str(col)] = {}

        for ent in increment[col]:
            for type in history_dbp["type"][ent]:
                try:
                    res_dict[str(col)][type] += 1
                except:
                    res_dict[str(col)][type] = 1

    return res_dict


def ds_cell_confidence(table, direct_dbp, history_dbp, type_dict,cands):
    cells_type=None
    for row in range(table.num_rows):
        for col in table.ne_cols:
            if direct_dbp[str(row)][str(col)]:
                if isinstance(direct_dbp[str(row)][str(col)],list):
                    cells_type='seudo'
                    break
                if isinstance(direct_dbp[str(row)][str(col)],dict):
                    cells_type='direct'
                    break

        if cells_type:
            break
    ratio_type_dict={}
    for col in type_dict.keys():
        for type in type_dict[col].keys():
            try:
                temp=ratio_type_dict[str(col)]
            except:
                ratio_type_dict[str(col)]={}

            ratio_type_dict[col][type]=type_dict[col][type]/len(cands[str(row)][str(col)])

    ## num(wiki2db) == 0

    if cells_type=='seudo':
        return ds_seudo_confidence(table, direct_dbp, history_dbp, ratio_type_dict)
    else:
        return ds_direct_confidence(table, direct_dbp, history_dbp, ratio_type_dict)

def ds_direct_confidence(table, cells, dictionary, type_dict):
    for row in range(table.num_rows):
        for col in table.ne_cols:
            cell=cells[str(row)][str(col)]
            if cell:
                cand=cell["url"]
                ds=0
                for type in dictionary["type"][cand]:
                    ds+=type_dict[str(col)][type]
                cell["ds"]=ds
    return cells

def ds_seudo_confidence(table, cells, dictionary, type_dict):

    for row in range(table.num_rows):
        for col in table.ne_cols:
            cell_list=cells[str(row)][str(col)]
            if cell_list:
                for cell in cell_list:
                    cand = cell["url"]
                    ds = 0
                    for type in dictionary["type"][cand]:
                        try:
                            ds += type_dict[str(col)][type]
                        except:
                            pass
                    cell["ds"] = ds

    return cells

def generate_miniontology(dbp_type):
    sparql=MySPARQL("http://dbpedia.org/sparql")

    tempo = dict()
    equ = dict()

    for ont in dbp_type.keys():
        parcls = sparql.get_subcls(ont)
        if not parcls:
            tempe = sparql.get_equcls(ont)
            if tempe:
                equ[ont] = tempe
            continue

        try:
            if ont not in tempo[parcls]:
                tempo[parcls].append(ont)
        except:
            tempo[parcls] = [ont]

    for o in equ.keys():
        for oo in equ[o]:
            try:
                if o not in tempo[sparql.get_subcls(oo)]:
                    tempo[sparql.get_subcls(oo)].append(o)
            except:
                tempo[sparql.get_subcls(oo)] = [o]
            break

    mid_list = ["http://www.w3.org/2002/07/owl#Thing"]
    num_layer = 0
    res=[]
    while mid_list:
        res.append([num_layer,mid_list])
        show_list = []
        num_layer += 1
        for type in mid_list:
            try:
                show_list += tempo[type]
            except:
                pass
        mid_list = show_list

    return res, equ.keys()







